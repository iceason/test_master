"""
Celery tasks for the build/testing module.
Handles Jenkins build triggering, polling, log fetching, reports, and notifications.
"""
import logging
import time
import json
import hmac
import base64
import hashlib
from urllib.parse import quote_plus

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .testing_serializers import report_url_for_notification

logger = logging.getLogger(__name__)

# Try Celery import; tasks degrade to plain functions if unavailable
try:
    from celery import shared_task
except ImportError:
    def shared_task(func=None, **kwargs):
        """Fallback decorator when Celery is not installed."""
        if func is None:
            return lambda f: f
        return func


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def run_build_task(self, execution_id):
    """Main task: trigger a Jenkins build, poll until done, fetch logs/report, notify."""
    run_build_sync(execution_id)


@shared_task(bind=True, max_retries=1, default_retry_delay=5)
def run_repeated_builds_task(self, plan_id, triggered_by='system', trigger_type='manual'):
    """Orchestrate repeated builds for stop-on-first-fail policy."""
    return run_repeated_builds_sync(plan_id, triggered_by=triggered_by, trigger_type=trigger_type)


def _dispatch_build(execution):
    """
    Dispatch a build execution using Celery if available, otherwise fall back
    to a background thread. Reuses the same CELERY_AVAILABLE check as the
    manual trigger endpoint.
    """
    import threading
    from .views import CELERY_AVAILABLE

    if CELERY_AVAILABLE:
        try:
            task = run_build_task.delay(execution.id)
            execution.celery_task_id = task.id
            execution.save(update_fields=['celery_task_id'])
            return
        except Exception:
            logger.warning("Celery dispatch failed, falling back to thread")

    threading.Thread(
        target=run_build_sync, args=(execution.id,), daemon=True
    ).start()


def _create_repeat_execution(plan, trigger_type, triggered_by, idx, total):
    from .models import BuildExecution
    suffix = f"#{idx}/{total}" if total > 1 else ''
    return BuildExecution.objects.create(
        build_plan=plan,
        executor_machine=plan.executor_machine,
        trigger_type=trigger_type,
        triggered_by=f"{triggered_by}{suffix}",
        status='pending',
    )


def dispatch_repeated_builds(plan, repeat_run_times, failure_policy, triggered_by, trigger_type='manual'):
    """
    Dispatch repeated builds according to failure policy.
    - continue_all: create N executions and dispatch each asynchronously.
    - stop_on_first_fail: delegate to orchestrator task/thread and run sequentially.
    """
    import threading
    from .views import CELERY_AVAILABLE

    repeat_run_times = max(1, min(int(repeat_run_times or 1), 20))
    if failure_policy not in ('continue_all', 'stop_on_first_fail'):
        failure_policy = 'continue_all'

    if failure_policy == 'continue_all':
        execution_ids = []
        for idx in range(1, repeat_run_times + 1):
            execution = _create_repeat_execution(plan, trigger_type, triggered_by, idx, repeat_run_times)
            execution_ids.append(execution.id)
            _dispatch_build(execution)
        return {
            'execution_ids': execution_ids,
            'mode': 'parallel_dispatch',
        }

    # stop_on_first_fail: sequential orchestrator
    if CELERY_AVAILABLE:
        task = run_repeated_builds_task.delay(
            plan.id, triggered_by=triggered_by, trigger_type=trigger_type
        )
        return {
            'execution_ids': [],
            'mode': 'sequential_orchestrator_celery',
            'orchestrator_task_id': task.id,
        }

    threading.Thread(
        target=run_repeated_builds_sync,
        args=(plan.id, triggered_by, trigger_type),
        daemon=True,
    ).start()
    return {
        'execution_ids': [],
        'mode': 'sequential_orchestrator_thread',
    }


def run_repeated_builds_sync(plan_id, triggered_by='system', trigger_type='manual'):
    """Sequential repeated build runner; stops on first fail when configured."""
    from .models import BuildPlan, BuildExecution

    try:
        plan = BuildPlan.objects.select_related('executor_machine').get(id=plan_id)
    except BuildPlan.DoesNotExist:
        logger.error("BuildPlan %s not found for repeated runs", plan_id)
        return {'execution_ids': [], 'stopped_early': False}

    repeat_run_times = max(1, min(int(getattr(plan, 'repeat_run_times', 1) or 1), 20))
    failure_policy = getattr(plan, 'repeat_failure_policy', 'continue_all') or 'continue_all'

    execution_ids = []
    stopped_early = False
    for idx in range(1, repeat_run_times + 1):
        execution = _create_repeat_execution(plan, trigger_type, triggered_by, idx, repeat_run_times)
        execution_ids.append(execution.id)
        run_build_sync(execution.id)
        execution = BuildExecution.objects.get(id=execution.id)
        if failure_policy == 'stop_on_first_fail' and execution.status in ('failed', 'cancelled'):
            stopped_early = True
            break

    return {
        'execution_ids': execution_ids,
        'stopped_early': stopped_early,
    }


def run_build_sync(execution_id):
    """Synchronous build runner (used by both Celery and thread fallback)."""
    from .models import BuildExecution
    from .jenkins_client import create_jenkins_client

    try:
        execution = BuildExecution.objects.select_related(
            'build_plan', 'build_plan__executor_machine'
        ).get(id=execution_id)
    except BuildExecution.DoesNotExist:
        logger.error("BuildExecution %s not found", execution_id)
        return

    plan = execution.build_plan

    # Mark as running
    execution.status = 'running'
    execution.started_at = timezone.now()
    execution.save(update_fields=['status', 'started_at'])

    client = create_jenkins_client(plan)
    if not client:
        execution.status = 'failed'
        execution.log_text = 'ERROR: Jenkins not configured for this build plan.'
        execution.finished_at = timezone.now()
        execution.duration_ms = 0
        execution.save()
        return

    try:
        # 1. Trigger Jenkins build
        params = _build_jenkins_params(plan, execution)
        queue_id = client.trigger_build(plan.jenkins_job_name, parameters=params)
        execution.log_text = f"Jenkins job queued (queue_id={queue_id})\n"
        execution.save(update_fields=['log_text'])

        # 2. Wait for build number
        build_number = client.get_build_number_from_queue(queue_id, timeout=120)
        execution.jenkins_build_number = build_number
        machine = plan.executor_machine
        jenkins_base = machine.jenkins_url.rstrip('/') if machine and machine.jenkins_url else ''
        execution.jenkins_build_url = (
            f"{jenkins_base}/job/{plan.jenkins_job_name}/{build_number}/"
        )
        execution.log_text += f"Build started: #{build_number}\n"
        execution.save(update_fields=[
            'jenkins_build_number', 'jenkins_build_url', 'log_text',
        ])

        # 3. Poll until build completes
        _poll_build(client, execution, plan.jenkins_job_name, build_number)

        # 4. Fetch full log
        try:
            log = client.get_build_console_output(plan.jenkins_job_name, build_number)
            execution.log_text = log
            execution.save(update_fields=['log_text'])
        except Exception as e:
            logger.warning("Failed to fetch build log: %s", e)

        # 5. Fetch test report
        _fetch_report(client, execution, plan.jenkins_job_name, build_number)

        # 6. Send notification
        schedule_build_notifications(execution.id)
        _send_external_callback(execution)

    except Exception as e:
        logger.exception("Build execution %s failed", execution_id)
        execution.status = 'failed'
        execution.log_text = (execution.log_text or '') + f"\nERROR: {e}"
        execution.finished_at = timezone.now()
        if execution.started_at:
            delta = execution.finished_at - execution.started_at
            execution.duration_ms = int(delta.total_seconds() * 1000)
        execution.save()
        schedule_build_notifications(execution.id)
        _send_external_callback(execution)


def _build_jenkins_params(plan, execution):
    """Build Jenkins job parameters."""
    return {
        'EXECUTION_ID': str(execution.id),
    }


def _poll_build(client, execution, job_name, build_number, poll_interval=5, timeout=7200):
    """Poll Jenkins until the build is done."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            result = client.get_build_result(job_name, build_number)
            if result is not None:
                # Build finished
                status_map = {
                    'SUCCESS': 'success',
                    'FAILURE': 'failed',
                    'ABORTED': 'cancelled',
                    'UNSTABLE': 'failed',
                }
                execution.status = status_map.get(result, 'failed')
                execution.finished_at = timezone.now()
                if execution.started_at:
                    delta = execution.finished_at - execution.started_at
                    execution.duration_ms = int(delta.total_seconds() * 1000)
                execution.save(update_fields=['status', 'finished_at', 'duration_ms'])
                return
        except Exception as e:
            logger.warning("Poll error: %s", e)
        time.sleep(poll_interval)

    # Timeout
    execution.status = 'failed'
    execution.log_text = (execution.log_text or '') + '\nERROR: Build poll timeout.'
    execution.finished_at = timezone.now()
    if execution.started_at:
        delta = execution.finished_at - execution.started_at
        execution.duration_ms = int(delta.total_seconds() * 1000)
    execution.save()


def _fetch_report(client, execution, job_name, build_number):
    """Try to fetch a test report from Jenkins."""
    try:
        report = client.get_build_test_report(job_name, build_number)
        if report:
            execution.report_type = 'junit'
            execution.report_data = report
            execution.save(update_fields=['report_type', 'report_data'])
            return
    except Exception as e:
        logger.warning("JUnit report fetch failed: %s", e)

    # Check if Allure report URL is available
    try:
        info = client.get_build_info(job_name, build_number)
        for a in info.get('actions', []):
            url_name = a.get('urlName', '')
            if 'allure' in url_name.lower():
                execution.report_type = 'allure'
                execution.report_url = (
                    f"{execution.jenkins_build_url}{url_name}/"
                )
                execution.save(update_fields=['report_type', 'report_url'])
                return
    except Exception:
        pass


def _send_notification(execution):
    """Send build result notification based on plan config."""
    plan = execution.build_plan
    config = plan.notification_config or {}

    # Email notification
    email_cfg = config.get('email', {})
    if email_cfg.get('enabled') and email_cfg.get('recipients'):
        try:
            from .models import EmailTemplate

            status_emoji_map = {
                'success': '✅', 'failed': '❌', 'cancelled': '⚠️',
                'running': '🔄', 'pending': '⏳',
            }
            ctx = {
                'plan_name': plan.name,
                'status': execution.status,
                'status_upper': execution.status.upper(),
                'status_emoji': status_emoji_map.get(execution.status, '📋'),
                'trigger_type': execution.trigger_type or '手动',
                'triggered_by': execution.triggered_by or 'system',
                'duration': execution.duration_display,
                'jenkins_url': execution.jenkins_build_url or '-',
                'timestamp': execution.started_at.strftime('%Y-%m-%d %H:%M:%S') if execution.started_at else '-',
            }

            tpl = EmailTemplate.objects.filter(is_default=True).first()
            if tpl:
                subject, body = tpl.render(ctx)
            else:
                subject = f"[Test Master] {plan.name} - {execution.status.upper()}"
                body = "\n".join(f"{k}: {v}" for k, v in ctx.items())

            send_mail(
                subject, body,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@testmaster.local'),
                email_cfg['recipients'],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning("Email notification failed: %s", e)

    # Webhook notification (DingTalk / Feishu / WeChat Work) - legacy path
    webhook_cfg = config.get('webhook', {})
    if webhook_cfg.get('enabled') and webhook_cfg.get('url'):
        try:
            import requests
            webhook_type = webhook_cfg.get('type', 'dingtalk')
            payload = _build_webhook_payload(execution, webhook_type)
            requests.post(
                webhook_cfg['url'],
                json=payload,
                timeout=10,
            )
        except Exception as e:
            logger.warning("Webhook notification failed: %s", e)

    # DingTalk notification (new preferred path)
    dingtalk_cfg = config.get('dingtalk', {})
    if dingtalk_cfg.get('enabled'):
        _send_dingtalk_groups(execution, dingtalk_cfg)


def _send_external_callback(execution):
    """Callback build result to external URL once."""
    if not execution.callback_url or execution.callback_notified:
        return
    if execution.status not in ('success', 'failed', 'cancelled'):
        return
    try:
        import requests
        payload = {
            'execution_id': execution.id,
            'build_plan_id': execution.build_plan_id,
            'build_plan_name': execution.build_plan.name,
            'status': execution.status,
            'trigger_type': execution.trigger_type,
            'triggered_by': execution.triggered_by,
            'jenkins_build_number': execution.jenkins_build_number,
            'jenkins_build_url': execution.jenkins_build_url,
            'report_type': execution.report_type,
            'report_url': execution.report_url,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
            'duration_ms': execution.duration_ms,
        }
        response = requests.post(execution.callback_url, json=payload, timeout=10)
        execution.callback_notified = response.status_code < 400
        execution.callback_notified_at = timezone.now()
        execution.callback_last_response = f"HTTP {response.status_code}: {response.text[:300]}"
        execution.save(update_fields=['callback_notified', 'callback_notified_at', 'callback_last_response'])
    except Exception as e:
        execution.callback_notified = False
        execution.callback_notified_at = timezone.now()
        execution.callback_last_response = f"ERROR: {e}"
        execution.save(update_fields=['callback_notified', 'callback_notified_at', 'callback_last_response'])


def _build_webhook_payload(execution, webhook_type):
    """Build notification payload for different webhook types."""
    plan = execution.build_plan
    text = (
        f"**Build Notification**\n"
        f"- Plan: {plan.name}\n"
        f"- Status: {execution.status}\n"
        f"- Trigger: {execution.trigger_type} by {execution.triggered_by}\n"
        f"- Duration: {execution.duration_display}\n"
    )
    if execution.jenkins_build_url:
        text += f"- [Jenkins Link]({execution.jenkins_build_url})\n"

    if webhook_type == 'dingtalk':
        return {
            'msgtype': 'markdown',
            'markdown': {'title': f'Build {execution.status}', 'text': text},
        }
    elif webhook_type == 'feishu':
        return {
            'msg_type': 'interactive',
            'card': {
                'header': {'title': {'tag': 'plain_text', 'content': f'Build {execution.status}'}},
                'elements': [{'tag': 'markdown', 'content': text}],
            },
        }
    else:
        # WeChat Work or generic
        return {
            'msgtype': 'markdown',
            'markdown': {'content': text},
        }


def _build_notification_context(execution):
    status_emoji_map = {
        'success': '✅', 'failed': '❌', 'cancelled': '⚠️',
        'running': '🔄', 'pending': '⏳',
    }
    allure_report_url = report_url_for_notification(execution.report_url)
    allure_report_block = (
        f"- Allure 报告：[{allure_report_url}]({allure_report_url})\n"
        if allure_report_url else ""
    )
    return {
        'plan_name': execution.build_plan.name,
        'status': execution.status,
        'status_upper': execution.status.upper(),
        'status_emoji': status_emoji_map.get(execution.status, '📋'),
        'trigger_type': execution.trigger_type or 'manual',
        'triggered_by': execution.triggered_by or 'system',
        'duration': execution.duration_display,
        'jenkins_url': execution.jenkins_build_url or '-',
        'timestamp': execution.started_at.strftime('%Y-%m-%d %H:%M:%S') if execution.started_at else '-',
        'report_type': execution.report_type or '',
        'allure_report_url': allure_report_url or '',
        'allure_report_block': allure_report_block,
    }


def _should_defer_notification_for_report(plan, execution):
    if not getattr(plan, 'report_enabled', False):
        return False
    if execution.report_url:
        return False
    if execution.status not in ('success', 'failed', 'cancelled'):
        return False
    return True


def schedule_build_notifications(execution_id):
    from .models import BuildExecution
    try:
        execution = BuildExecution.objects.select_related('build_plan').get(id=execution_id)
    except BuildExecution.DoesNotExist:
        return
    if _should_defer_notification_for_report(execution.build_plan, execution):
        send_notification_when_report_ready.delay(execution.id)
    else:
        _send_notification(execution)


def _render_dingtalk_template(execution, template_id=None):
    from .models import DingTalkTemplate

    template = None
    if template_id:
        template = DingTalkTemplate.objects.filter(id=template_id, is_active=True).first()
    if not template:
        template = DingTalkTemplate.objects.filter(is_default=True, is_active=True).first()
    if not template:
        template = DingTalkTemplate.objects.filter(is_active=True).order_by('-updated_at').first()

    ctx = _build_notification_context(execution)
    if template:
        return template.render(ctx)

    # Fallback to simple built-in template
    title = f"{ctx['status_emoji']} [{ctx['status_upper']}] {ctx['plan_name']}"
    body = (
        f"### {ctx['status_emoji']} 自动化构建报告\n\n"
        f"- 构建计划：{ctx['plan_name']}\n"
        f"- 执行状态：{ctx['status_upper']}\n"
        f"- 触发方式：{ctx['trigger_type']}\n"
        f"- 触发人：{ctx['triggered_by']}\n"
        f"- 执行耗时：{ctx['duration']}\n"
        f"- 执行时间：{ctx['timestamp']}\n"
        f"- Jenkins：{ctx['jenkins_url']}\n"
        f"{ctx.get('allure_report_block', '')}"
    )
    return title, body


def _build_dingtalk_signed_url(webhook_url, secret):
    if not secret:
        raise ValueError("DingTalk secret is required")

    ts = str(int(time.time() * 1000))
    string_to_sign = f"{ts}\n{secret}"
    sign = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256,
        ).digest()
    ).decode('utf-8')
    delimiter = '&' if '?' in webhook_url else '?'
    return f"{webhook_url}{delimiter}timestamp={ts}&sign={quote_plus(sign)}"


def send_dingtalk_markdown(webhook_url, secret, title, text):
    import requests

    signed_url = _build_dingtalk_signed_url(webhook_url, secret)
    payload = {
        'msgtype': 'markdown',
        'markdown': {'title': title, 'text': text},
    }
    response = requests.post(signed_url, json=payload, timeout=10)
    response.raise_for_status()
    try:
        result = response.json()
    except Exception:
        result = {}
    if result.get('errcode', 0) != 0:
        raise ValueError(result.get('errmsg', 'Unknown DingTalk error'))


def _send_dingtalk_groups(execution, dingtalk_cfg):
    from .models import DingTalkGroup

    group_ids = dingtalk_cfg.get('group_ids') or []
    if not group_ids:
        return

    template_id = dingtalk_cfg.get('template_id')
    title, body = _render_dingtalk_template(execution, template_id=template_id)
    groups = DingTalkGroup.objects.filter(id__in=group_ids, is_active=True)
    for group in groups:
        try:
            send_dingtalk_markdown(group.webhook_url, group.secret, title, body)
            logger.info("dingtalk_notify success group=%s execution=%s", group.name, execution.id)
        except Exception as e:
            logger.warning(
                "dingtalk_notify failed group=%s execution=%s error=%s",
                group.name, execution.id, e
            )


@shared_task
def send_notification_when_report_ready(execution_id):
    from .models import BuildExecution
    wait_seconds = int(getattr(settings, 'NOTIFICATION_WAIT_FOR_REPORT_SECONDS', 240) or 240)
    poll_seconds = int(getattr(settings, 'NOTIFICATION_REPORT_POLL_SECONDS', 5) or 5)
    poll_seconds = max(1, poll_seconds)
    deadline = time.time() + wait_seconds
    last_execution = None
    while time.time() <= deadline:
        try:
            execution = BuildExecution.objects.select_related('build_plan').get(id=execution_id)
            last_execution = execution
        except BuildExecution.DoesNotExist:
            return
        if execution.report_url:
            _send_notification(execution)
            return
        if execution.status not in ('success', 'failed', 'cancelled'):
            return
        time.sleep(poll_seconds)
    if last_execution:
        _send_notification(last_execution)


@shared_task
def send_report_upload_followup_if_needed(execution_id):
    from .models import BuildExecution
    try:
        execution = BuildExecution.objects.select_related('build_plan').get(id=execution_id)
    except BuildExecution.DoesNotExist:
        return
    if not execution.report_url:
        return
    if not getattr(execution.build_plan, 'report_enabled', False):
        return
    _send_notification(execution)


@shared_task
def send_build_notification(execution_id):
    """Standalone task to send notifications."""
    from .models import BuildExecution
    try:
        execution = BuildExecution.objects.select_related('build_plan').get(id=execution_id)
        schedule_build_notifications(execution.id)
        _send_external_callback(execution)
    except BuildExecution.DoesNotExist:
        logger.error("BuildExecution %s not found for notification", execution_id)


@shared_task
def check_cron_builds():
    """
    Periodic task: scan BuildPlans with is_cron_enabled=True
    and trigger builds according to their cron_expression.
    Should be called by Celery Beat every minute.
    """
    from .models import BuildPlan, BuildExecution
    import re

    now = timezone.localtime()
    plans = BuildPlan.objects.filter(status='active', is_cron_enabled=True).exclude(cron_expression='')

    for plan in plans:
        if _cron_matches(plan.cron_expression, now):
            # Avoid duplicate triggers within the same minute
            recent = plan.executions.filter(
                trigger_type='cron',
                started_at__minute=now.minute,
                started_at__hour=now.hour,
                started_at__day=now.day,
            ).exists()
            if recent:
                continue

            logger.info("Cron trigger for plan: %s", plan.name)
            execution = BuildExecution.objects.create(
                build_plan=plan,
                executor_machine=plan.executor_machine,
                trigger_type='cron',
                triggered_by='scheduler',
                status='pending',
            )
            _dispatch_build(execution)


def _cron_matches(expression, dt):
    """
    Simple cron expression matcher (minute hour day month weekday).
    Supports: *, specific numbers, ranges (1-5), step (*/5), lists (1,3,5).
    """
    try:
        parts = expression.strip().split()
        if len(parts) != 5:
            return False
        checks = [
            (parts[0], dt.minute, 0, 59),
            (parts[1], dt.hour, 0, 23),
            (parts[2], dt.day, 1, 31),
            (parts[3], dt.month, 1, 12),
            (parts[4], dt.weekday(), 0, 6),  # Monday=0
        ]
        for field, value, vmin, vmax in checks:
            if not _cron_field_matches(field, value, vmin, vmax):
                return False
        return True
    except Exception:
        return False


def _cron_field_matches(field, value, vmin, vmax):
    """Check if a single cron field matches the value."""
    if field == '*':
        return True
    for part in field.split(','):
        if '/' in part:
            base, step = part.split('/', 1)
            step = int(step)
            if base == '*':
                if value % step == 0:
                    return True
            else:
                start = int(base)
                if value >= start and (value - start) % step == 0:
                    return True
        elif '-' in part:
            lo, hi = part.split('-', 1)
            if int(lo) <= value <= int(hi):
                return True
        else:
            if int(part) == value:
                return True
    return False

"""
Celery tasks for the build/testing module.
Handles Jenkins build triggering, polling, log fetching, reports, and notifications.
"""
import logging
import time
import json

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

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
        params = _build_jenkins_params(plan)
        queue_id = client.trigger_build(plan.jenkins_job_name, parameters=params)
        execution.log_text = f"Jenkins job queued (queue_id={queue_id})\n"
        execution.save(update_fields=['log_text'])

        # 2. Wait for build number
        build_number = client.get_build_number_from_queue(queue_id, timeout=120)
        execution.jenkins_build_number = build_number
        execution.jenkins_build_url = (
            f"{plan.jenkins_server_url}/job/{plan.jenkins_job_name}/{build_number}/"
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
        _send_notification(execution)

    except Exception as e:
        logger.exception("Build execution %s failed", execution_id)
        execution.status = 'failed'
        execution.log_text = (execution.log_text or '') + f"\nERROR: {e}"
        execution.finished_at = timezone.now()
        if execution.started_at:
            delta = execution.finished_at - execution.started_at
            execution.duration_ms = int(delta.total_seconds() * 1000)
        execution.save()
        _send_notification(execution)


def _build_jenkins_params(plan):
    """Build Jenkins job parameters from the plan's steps."""
    params = {}
    # Pass build steps as a JSON parameter if the Jenkins job accepts it
    steps = list(plan.steps.order_by('order').values('name', 'script', 'timeout'))
    if steps:
        params['BUILD_STEPS'] = json.dumps(steps)
    return params


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
            subject = f"[Test Master] Build '{plan.name}' - {execution.status.upper()}"
            body = (
                f"Build Plan: {plan.name}\n"
                f"Status: {execution.status}\n"
                f"Trigger: {execution.trigger_type}\n"
                f"Triggered by: {execution.triggered_by}\n"
                f"Duration: {execution.duration_display}\n"
            )
            if execution.jenkins_build_url:
                body += f"Jenkins: {execution.jenkins_build_url}\n"
            send_mail(
                subject, body,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@testmaster.local'),
                email_cfg['recipients'],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning("Email notification failed: %s", e)

    # Webhook notification (DingTalk / Feishu / WeChat Work)
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


@shared_task
def send_build_notification(execution_id):
    """Standalone task to send notifications."""
    from .models import BuildExecution
    try:
        execution = BuildExecution.objects.select_related('build_plan').get(id=execution_id)
        _send_notification(execution)
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
            try:
                run_build_task.delay(execution.id)
            except Exception:
                import threading
                threading.Thread(
                    target=run_build_sync, args=(execution.id,), daemon=True
                ).start()


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

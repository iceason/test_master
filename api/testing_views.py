"""
ViewSets for the Testing module: ExecutorMachine, BuildPlan, BuildExecution.
Also includes external trigger, Jenkins webhook, report upload and progressive log endpoints.
"""
import logging
import os
import zipfile
import subprocess
import socket

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser
from django.http import StreamingHttpResponse, HttpResponse
from django.utils import timezone
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import (
    ExecutorMachine, BuildPlan, BuildStep, BuildExecution, EmailTemplate,
    DingTalkGroup, DingTalkTemplate,
)
from .testing_serializers import (
    ExecutorMachineSerializer,
    BuildPlanSerializer, BuildPlanListSerializer,
    BuildExecutionSerializer, BuildExecutionListSerializer,
    EmailTemplateSerializer,
    DingTalkGroupSerializer, DingTalkTemplateSerializer,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# ExecutorMachine
# -----------------------------------------------------------------------

class ExecutorMachineViewSet(viewsets.ModelViewSet):
    queryset = ExecutorMachine.objects.all()
    serializer_class = ExecutorMachineSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'os_type']
    search_fields = ['name', 'hostname', 'ip_address', 'description']
    ordering_fields = ['id', 'name', 'status', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['post'])
    def ping(self, request, pk=None):
        """Check if the executor machine is reachable (TCP connect)."""
        machine = self.get_object()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((machine.ip_address, machine.port))
            sock.close()
            if result == 0:
                machine.status = 'online'
                machine.save(update_fields=['status', 'updated_at'])
                return Response({'status': 'online', 'message': 'Reachable'})
            else:
                machine.status = 'offline'
                machine.save(update_fields=['status', 'updated_at'])
                return Response({'status': 'offline', 'message': 'Port closed'})
        except Exception as e:
            machine.status = 'offline'
            machine.save(update_fields=['status', 'updated_at'])
            return Response(
                {'status': 'offline', 'message': str(e)},
                status=status.HTTP_200_OK,
            )

    @action(detail=True, methods=['post'], url_path='test-jenkins')
    def test_jenkins(self, request, pk=None):
        """Test Jenkins connectivity for this executor machine."""
        machine = self.get_object()
        if not machine.jenkins_url:
            return Response({'status': 'error', 'message': 'Jenkins URL not configured'})
        try:
            from .jenkins_client import JenkinsClient
            client = JenkinsClient(
                server_url=machine.jenkins_url,
                username=machine.jenkins_username or None,
                token=machine.jenkins_token or None,
            )
            version = client.ping()
            return Response({'status': 'ok', 'version': version})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)})


# -----------------------------------------------------------------------
# BuildPlan
# -----------------------------------------------------------------------

class BuildPlanViewSet(viewsets.ModelViewSet):
    queryset = BuildPlan.objects.all()
    serializer_class = BuildPlanSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_cron_enabled', 'executor_machine']
    search_fields = ['name', 'description', 'jenkins_job_name']
    ordering_fields = ['id', 'name', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return BuildPlanListSerializer
        return BuildPlanSerializer

    def _sync_jenkins_job(self, plan):
        """Try to sync the plan to Jenkins; return dict with result info."""
        machine = plan.executor_machine
        if not machine or not machine.jenkins_url:
            return None
        try:
            from .jenkins_client import sync_jenkins_job
            sync_jenkins_job(plan)
            return {'jenkins_sync': 'ok'}
        except Exception as e:
            err_msg = str(e)
            try:
                from .jenkins_client import _diagnose_jenkins_connection
                diag = _diagnose_jenkins_connection(
                    machine.jenkins_url, machine.jenkins_username, machine.jenkins_token
                )
                if diag:
                    err_msg = diag
            except Exception:
                pass
            logger.warning("Failed to sync Jenkins job for plan %s: %s", plan.id, e)
            return {'jenkins_sync': 'error', 'jenkins_error': err_msg}

    def _ensure_jenkinsfile_text(self, plan):
        """If jenkinsfile_text is empty (visual mode save), generate from steps."""
        if not plan.jenkinsfile_text:
            from .jenkins_client import build_pipeline_script
            machine = plan.executor_machine
            steps = list(
                plan.steps.order_by('order').values('name', 'script', 'timeout', 'on_failure')
            )
            plan.jenkinsfile_text = build_pipeline_script(
                steps=steps,
                os_type=getattr(machine, 'os_type', 'linux') if machine else 'linux',
                node_label=getattr(machine, 'jenkins_node_name', None) if machine else None,
                git_repo_url=plan.git_repo_url or '',
                git_branch=plan.git_branch or 'main',
                workspace_cleanup=plan.workspace_cleanup,
                report_enabled=plan.report_enabled,
                report_command=plan.report_command or '',
                environment_variables=plan.environment_variables or [],
                git_credential_id=getattr(plan, 'git_credential_id', '') or '',
            )
            plan.save(update_fields=['jenkinsfile_text'])

    def perform_create(self, serializer):
        plan = serializer.save()
        self._ensure_jenkinsfile_text(plan)
        sync_result = self._sync_jenkins_job(plan)
        if sync_result:
            plan._sync_result = sync_result

    def perform_update(self, serializer):
        plan = serializer.save()
        self._ensure_jenkinsfile_text(plan)
        sync_result = self._sync_jenkins_job(plan)
        if sync_result:
            plan._sync_result = sync_result

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        plan = BuildPlan.objects.get(id=response.data['id'])
        if hasattr(plan, '_sync_result'):
            response.data['_jenkins'] = plan._sync_result
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        plan = self.get_object()
        if hasattr(plan, '_sync_result'):
            response.data['_jenkins'] = plan._sync_result
        return response

    @action(detail=True, methods=['get'], url_path='jenkinsfile_preview')
    def jenkinsfile_preview(self, request, pk=None):
        """Return the Jenkinsfile script that would be pushed to Jenkins."""
        plan = self.get_object()
        raw_jenkinsfile = getattr(plan, 'jenkinsfile_text', '') or ''
        if raw_jenkinsfile:
            return Response({'jenkinsfile': raw_jenkinsfile})

        from .jenkins_client import build_pipeline_script
        machine = plan.executor_machine
        steps = list(
            plan.steps.order_by('order').values('name', 'script', 'timeout', 'on_failure')
        )
        script = build_pipeline_script(
            steps=steps,
            os_type=getattr(machine, 'os_type', 'linux') if machine else 'linux',
            node_label=getattr(machine, 'jenkins_node_name', None) if machine else None,
            git_repo_url=getattr(plan, 'git_repo_url', '') or '',
            git_branch=getattr(plan, 'git_branch', 'main') or 'main',
            workspace_cleanup=getattr(plan, 'workspace_cleanup', True),
            report_enabled=getattr(plan, 'report_enabled', False),
            report_command=getattr(plan, 'report_command', '') or '',
            environment_variables=getattr(plan, 'environment_variables', None) or [],
            git_credential_id=getattr(plan, 'git_credential_id', '') or '',
        )
        return Response({'jenkinsfile': script})

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """Manually trigger a build for this plan."""
        plan = self.get_object()
        if plan.status == 'disabled':
            return Response(
                {'error': 'Build plan is disabled'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        machine = plan.executor_machine
        if not machine or not machine.jenkins_url:
            return Response(
                {'error': 'No executor machine or Jenkins not configured'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not plan.jenkins_job_name:
            try:
                from .jenkins_client import sync_jenkins_job
                sync_jenkins_job(plan)
            except (ConnectionError, ValueError) as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                return Response(
                    {'error': f'Jenkins 同步失败: {e}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        triggered_by = request.user.username if request.user.is_authenticated else 'anonymous'
        repeat_run_times = max(1, min(int(getattr(plan, 'repeat_run_times', 1) or 1), 20))
        failure_policy = getattr(plan, 'repeat_failure_policy', 'continue_all') or 'continue_all'

        from .build_tasks import dispatch_repeated_builds
        result = dispatch_repeated_builds(
            plan=plan,
            repeat_run_times=repeat_run_times,
            failure_policy=failure_policy,
            triggered_by=triggered_by,
            trigger_type='manual',
        )

        return Response({
            'execution_id': result['execution_ids'][0] if result.get('execution_ids') else None,
            'execution_ids': result.get('execution_ids', []),
            'repeat_summary': {
                'repeat_run_times': repeat_run_times,
                'repeat_failure_policy': failure_policy,
                'dispatch_mode': result.get('mode'),
                'orchestrator_task_id': result.get('orchestrator_task_id', ''),
            },
            'status': 'accepted',
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop the latest running build."""
        plan = self.get_object()
        execution = plan.executions.filter(status='running').order_by('-started_at').first()
        if not execution:
            return Response({'error': 'No running build'}, status=status.HTTP_400_BAD_REQUEST)

        if execution.jenkins_build_number:
            try:
                from .jenkins_client import create_jenkins_client
                client = create_jenkins_client(plan)
                if client:
                    client.stop_build(plan.jenkins_job_name, execution.jenkins_build_number)
            except Exception as e:
                logger.warning("Failed to stop Jenkins build: %s", e)

        execution.status = 'cancelled'
        execution.finished_at = timezone.now()
        if execution.started_at:
            delta = execution.finished_at - execution.started_at
            execution.duration_ms = int(delta.total_seconds() * 1000)
        execution.save()
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['get'], url_path='refresh-status')
    def refresh_status(self, request, pk=None):
        """Refresh the status of the latest execution from Jenkins."""
        plan = self.get_object()
        execution = plan.executions.order_by('-started_at').first()
        if not execution:
            return Response({'status': 'no_executions'})
        return Response({
            'execution_id': execution.id,
            'status': execution.status,
            'started_at': execution.started_at,
            'finished_at': execution.finished_at,
            'duration_ms': execution.duration_ms,
        })

    @action(detail=True, methods=['post'], url_path='sync-jenkins')
    def sync_jenkins(self, request, pk=None):
        """Force sync the Jenkins job config."""
        plan = self.get_object()
        result = self._sync_jenkins_job(plan)
        if not result:
            return Response({'error': 'Jenkins not configured'}, status=status.HTTP_400_BAD_REQUEST)
        if result.get('jenkins_sync') == 'error':
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(result)

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """List executions for this build plan."""
        plan = self.get_object()
        qs = plan.executions.all()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = BuildExecutionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BuildExecutionListSerializer(qs, many=True)
        return Response(serializer.data)


# -----------------------------------------------------------------------
# BuildExecution
# -----------------------------------------------------------------------

class BuildExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BuildExecution.objects.all()
    serializer_class = BuildExecutionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'trigger_type', 'build_plan']
    search_fields = ['build_plan__name', 'triggered_by']
    ordering_fields = ['id', 'started_at', 'finished_at', 'duration_ms']
    ordering = ['-started_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return BuildExecutionListSerializer
        return BuildExecutionSerializer

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Return the build log text."""
        execution = self.get_object()

        # If log is stored in Jenkins and we don't have it yet, try to fetch
        if not execution.log_text and execution.jenkins_build_number:
            try:
                from .jenkins_client import create_jenkins_client
                client = create_jenkins_client(execution.build_plan)
                if client:
                    log = client.get_build_console_output(
                        execution.build_plan.jenkins_job_name,
                        execution.jenkins_build_number,
                    )
                    execution.log_text = log
                    execution.save(update_fields=['log_text'])
            except Exception as e:
                logger.warning("Failed to fetch Jenkins log: %s", e)

        return Response({
            'execution_id': execution.id,
            'log_text': execution.log_text or '',
        })

    @action(detail=True, methods=['get'])
    def log_download(self, request, pk=None):
        """Download full log as a text file."""
        execution = self.get_object()
        log_content = execution.log_text or 'No log available.'
        response = HttpResponse(log_content, content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename="build_{execution.id}_log.txt"'
        )
        return response

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Return test report data."""
        execution = self.get_object()
        return Response({
            'execution_id': execution.id,
            'report_type': execution.report_type,
            'report_url': execution.report_url,
            'report_data': execution.report_data,
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a running build."""
        execution = self.get_object()
        if execution.status not in ('pending', 'running'):
            return Response(
                {'error': 'Build is not running'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Try to stop Jenkins build
        if execution.jenkins_build_number:
            try:
                from .jenkins_client import create_jenkins_client
                client = create_jenkins_client(execution.build_plan)
                if client:
                    client.stop_build(
                        execution.build_plan.jenkins_job_name,
                        execution.jenkins_build_number,
                    )
            except Exception as e:
                logger.warning("Failed to stop Jenkins build: %s", e)

        execution.status = 'cancelled'
        execution.finished_at = timezone.now()
        if execution.started_at:
            delta = execution.finished_at - execution.started_at
            execution.duration_ms = int(delta.total_seconds() * 1000)
        execution.save()
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['get'], url_path='progressive-log')
    def progressive_log(self, request, pk=None):
        """Return incremental log content starting from a byte offset."""
        execution = self.get_object()
        start = int(request.query_params.get('start', 0))
        log_text = execution.log_text or ''
        chunk = log_text[start:]
        return Response({
            'log': chunk,
            'offset': start + len(chunk),
            'more': execution.status in ('pending', 'running'),
        })


# -----------------------------------------------------------------------
# External Trigger API (token-based, no auth required)
# -----------------------------------------------------------------------

class BuildTriggerView(APIView):
    """
    POST /api/build-trigger/<trigger_token>/
    External trigger endpoint. No auth required; validated by token.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, trigger_token):
        try:
            plan = BuildPlan.objects.select_related(
                'executor_machine'
            ).get(trigger_token=trigger_token, status='active')
        except BuildPlan.DoesNotExist:
            return Response(
                {'error': 'Invalid or disabled trigger token'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not plan.executor_machine or not plan.executor_machine.jenkins_url:
            return Response(
                {'error': 'No executor machine with Jenkins configured'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not plan.jenkins_job_name:
            try:
                from .jenkins_client import sync_jenkins_job
                sync_jenkins_job(plan)
            except Exception as e:
                return Response(
                    {'error': f'Failed to create Jenkins job: {e}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        triggered_by = request.data.get('triggered_by', 'external_api')

        execution = BuildExecution.objects.create(
            build_plan=plan,
            executor_machine=plan.executor_machine,
            trigger_type='api',
            triggered_by=triggered_by,
            status='pending',
        )

        from .build_tasks import _dispatch_build
        _dispatch_build(execution)

        return Response({
            'execution_id': execution.id,
            'build_plan': plan.name,
            'status': 'accepted',
        }, status=status.HTTP_202_ACCEPTED)


# -----------------------------------------------------------------------
# Jenkins Webhook
# -----------------------------------------------------------------------

class JenkinsWebhookView(APIView):
    """
    POST /api/jenkins-webhook/
    Receive build completion notifications from Jenkins.
    Expected payload: { "build_plan_id": ..., "build_number": ...,
                        "result": "SUCCESS"|"FAILURE", "build_url": "..." }
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        build_plan_id = request.data.get('build_plan_id')
        build_number = request.data.get('build_number')
        result = request.data.get('result', '')
        build_url = request.data.get('build_url', '')

        if not build_plan_id or not build_number:
            return Response(
                {'error': 'Missing build_plan_id or build_number'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find matching execution
        try:
            execution = BuildExecution.objects.filter(
                build_plan_id=build_plan_id,
                jenkins_build_number=build_number,
            ).latest('started_at')
        except BuildExecution.DoesNotExist:
            # Create one if webhook arrives before polling picks it up
            try:
                plan = BuildPlan.objects.get(id=build_plan_id)
            except BuildPlan.DoesNotExist:
                return Response(
                    {'error': 'Build plan not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            execution = BuildExecution.objects.create(
                build_plan=plan,
                trigger_type='jenkins_webhook',
                triggered_by='jenkins',
                jenkins_build_number=build_number,
                jenkins_build_url=build_url,
                status='pending',
            )

        # Update status
        status_map = {
            'SUCCESS': 'success',
            'FAILURE': 'failed',
            'ABORTED': 'cancelled',
        }
        execution.status = status_map.get(result.upper(), 'failed')
        execution.jenkins_build_url = build_url or execution.jenkins_build_url
        execution.finished_at = timezone.now()
        if execution.started_at:
            delta = execution.finished_at - execution.started_at
            execution.duration_ms = int(delta.total_seconds() * 1000)
        execution.save()

        # Trigger notification asynchronously
        try:
            from .build_tasks import send_build_notification
            send_build_notification.delay(execution.id)
        except Exception:
            pass

        return Response({'status': 'ok', 'execution_id': execution.id})


# -----------------------------------------------------------------------
# Report Upload (from Jenkins build scripts)
# -----------------------------------------------------------------------

class ReportUploadView(APIView):
    """
    POST /api/upload-report/<execution_id>/
    Receive a report.zip uploaded from a Jenkins build script.
    Extracts it to MEDIA_ROOT/reports/<execution_id>/.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request, execution_id):
        try:
            execution = BuildExecution.objects.get(id=execution_id)
        except BuildExecution.DoesNotExist:
            return Response(
                {'error': 'Execution not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        report_file = request.FILES.get('report')
        if not report_file:
            return Response(
                {'error': 'No report file uploaded'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report_dir = os.path.join(settings.MEDIA_ROOT, 'reports', str(execution_id))
        os.makedirs(report_dir, exist_ok=True)

        zip_path = os.path.join(report_dir, 'report.zip')
        with open(zip_path, 'wb+') as f:
            for chunk in report_file.chunks():
                f.write(chunk)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(report_dir)
        except zipfile.BadZipFile:
            return Response(
                {'error': 'Invalid zip file'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report_url = f'/media/reports/{execution_id}/index.html'
        execution.report_type = 'allure'
        execution.report_url = report_url
        execution.save(update_fields=['report_type', 'report_url'])

        return Response({
            'status': 'ok',
            'report_url': report_url,
        })


# -----------------------------------------------------------------------
# Email Template Management
# -----------------------------------------------------------------------

class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer

    @action(detail=True, methods=['post'], url_path='set_default')
    def set_default(self, request, pk=None):
        tpl = self.get_object()
        tpl.is_default = True
        tpl.save()
        return Response({'status': 'ok'})

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        tpl = self.get_object()
        sample = {
            'plan_name': '示例构建计划',
            'status': 'success',
            'status_upper': 'SUCCESS',
            'status_emoji': '✅',
            'trigger_type': '手动',
            'triggered_by': 'admin',
            'duration': '1m 23s',
            'jenkins_url': 'http://127.0.0.1:8080/job/demo/1/',
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        subject, body = tpl.render(sample)
        return Response({'subject': subject, 'body': body})

    @action(detail=False, methods=['post'], url_path='preview_custom')
    def preview_custom(self, request):
        subject_tpl = request.data.get('subject', '')
        body_tpl = request.data.get('body', '')
        sample = {
            'plan_name': '示例构建计划',
            'status': 'success',
            'status_upper': 'SUCCESS',
            'status_emoji': '✅',
            'trigger_type': '手动',
            'triggered_by': 'admin',
            'duration': '1m 23s',
            'jenkins_url': 'http://127.0.0.1:8080/job/demo/1/',
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        for key, value in sample.items():
            placeholder = '{{' + key + '}}'
            subject_tpl = subject_tpl.replace(placeholder, str(value))
            body_tpl = body_tpl.replace(placeholder, str(value))
        return Response({'subject': subject_tpl, 'body': body_tpl})


class DingTalkGroupViewSet(viewsets.ModelViewSet):
    queryset = DingTalkGroup.objects.all()
    serializer_class = DingTalkGroupSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description', 'webhook_url']
    ordering_fields = ['id', 'name', 'updated_at', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['post'], url_path='test-send')
    def test_send(self, request, pk=None):
        group = self.get_object()
        try:
            from .build_tasks import send_dingtalk_markdown
            title = request.data.get('title', 'Test Master 钉钉通知测试')
            text = request.data.get(
                'text',
                '### Test Master 通知测试\n\n- 状态：连通性测试\n- 结果：通过\n'
            )
            send_dingtalk_markdown(group.webhook_url, group.secret, title, text)
            return Response({'status': 'ok'})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DingTalkTemplateViewSet(viewsets.ModelViewSet):
    queryset = DingTalkTemplate.objects.all()
    serializer_class = DingTalkTemplateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'updated_at', 'created_at']
    ordering = ['-is_default', '-updated_at']

    @action(detail=True, methods=['post'], url_path='set_default')
    def set_default(self, request, pk=None):
        tpl = self.get_object()
        tpl.is_default = True
        tpl.save()
        return Response({'status': 'ok'})

    @action(detail=True, methods=['post'], url_path='preview')
    def preview(self, request, pk=None):
        tpl = self.get_object()
        sample = {
            'plan_name': '示例构建计划',
            'status': 'success',
            'status_upper': 'SUCCESS',
            'status_emoji': '✅',
            'trigger_type': '手动',
            'triggered_by': 'admin',
            'duration': '1m 23s',
            'jenkins_url': 'http://127.0.0.1:8080/job/demo/1/',
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        title, body = tpl.render(sample)
        return Response({'title': title, 'body': body})

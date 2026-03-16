"""
ViewSets for the Testing module: ExecutorMachine, BuildPlan, BuildExecution.
Also includes external trigger and Jenkins webhook endpoints.
"""
import logging
import subprocess
import socket

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import StreamingHttpResponse, HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import ExecutorMachine, BuildPlan, BuildStep, BuildExecution
from .testing_serializers import (
    ExecutorMachineSerializer,
    BuildPlanSerializer, BuildPlanListSerializer,
    BuildExecutionSerializer, BuildExecutionListSerializer,
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


# -----------------------------------------------------------------------
# BuildPlan
# -----------------------------------------------------------------------

class BuildPlanViewSet(viewsets.ModelViewSet):
    queryset = BuildPlan.objects.all()
    serializer_class = BuildPlanSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_cron_enabled', 'executor_machine', 'environment']
    search_fields = ['name', 'description', 'jenkins_job_name']
    ordering_fields = ['id', 'name', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return BuildPlanListSerializer
        return BuildPlanSerializer

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """Manually trigger a build for this plan."""
        plan = self.get_object()
        if plan.status == 'disabled':
            return Response(
                {'error': 'Build plan is disabled'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        triggered_by = request.user.username if request.user.is_authenticated else 'anonymous'

        # Create execution record
        execution = BuildExecution.objects.create(
            build_plan=plan,
            executor_machine=plan.executor_machine,
            trigger_type='manual',
            triggered_by=triggered_by,
            status='pending',
        )

        # Launch async build task
        try:
            from .build_tasks import run_build_task
            task = run_build_task.delay(execution.id)
            execution.celery_task_id = task.id
            execution.save(update_fields=['celery_task_id'])
            return Response({
                'execution_id': execution.id,
                'task_id': task.id,
                'status': 'accepted',
            }, status=status.HTTP_202_ACCEPTED)
        except Exception:
            # Fallback: run in thread
            import threading

            def _run():
                from .build_tasks import run_build_sync
                run_build_sync(execution.id)

            threading.Thread(target=_run, daemon=True).start()
            return Response({
                'execution_id': execution.id,
                'status': 'processing',
            }, status=status.HTTP_202_ACCEPTED)

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
            plan = BuildPlan.objects.get(
                trigger_token=trigger_token, status='active')
        except BuildPlan.DoesNotExist:
            return Response(
                {'error': 'Invalid or disabled trigger token'},
                status=status.HTTP_404_NOT_FOUND,
            )

        triggered_by = request.data.get('triggered_by', 'external_api')

        execution = BuildExecution.objects.create(
            build_plan=plan,
            executor_machine=plan.executor_machine,
            trigger_type='api',
            triggered_by=triggered_by,
            status='pending',
        )

        try:
            from .build_tasks import run_build_task
            task = run_build_task.delay(execution.id)
            execution.celery_task_id = task.id
            execution.save(update_fields=['celery_task_id'])
        except Exception:
            import threading

            def _run():
                from .build_tasks import run_build_sync
                run_build_sync(execution.id)

            threading.Thread(target=_run, daemon=True).start()

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

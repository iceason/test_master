from django.conf import settings
from rest_framework import serializers
from .models import (
    ExecutorMachine, BuildPlan, BuildStep, BuildExecution, EmailTemplate,
    DingTalkGroup, DingTalkTemplate,
)


def resolve_backend_base_url_fallback():
    explicit = getattr(settings, 'BACKEND_BASE_URL', '') or ''
    if explicit.strip():
        return explicit.strip().rstrip('/')
    # Avoid inferring from request host (can be Jenkins reverse proxy host/port).
    return 'http://127.0.0.1:8000'


def absolute_report_url(stored_url, _request=None):
    """
    Return a browser-loadable report URL.

    - Default: path-only ``/media/...`` so the iframe uses the **same origin as the SPA**
      (Vite or nginx proxies ``/media`` to Django). Avoids opening Jenkins-only IPs/ports.
    - If ``REPORT_PUBLIC_BASE_URL`` is set (public URL where /media is served), prefix with it.
      Do **not** use ``BACKEND_BASE_URL`` here—that value is for Jenkins curl, often unreachable
      from a developer browser (e.g. 192.168.x.x:8000 when Django only listens on 127.0.0.1).

    ``_request`` is accepted for call-site compatibility; host inference is intentionally not
    used here (Vite changeOrigin breaks request.build_absolute_uri for media).
    """
    u = (stored_url or '').strip()
    if not u:
        return ''
    if u.startswith('http://') or u.startswith('https://'):
        return u
    if not u.startswith('/'):
        u = '/' + u
    public = (getattr(settings, 'REPORT_PUBLIC_BASE_URL', '') or '').strip().rstrip('/')
    if public:
        return public + u
    return u


def report_url_for_notification(stored_url):
    """
    Absolute http(s) URL for DingTalk / email / webhooks.

    Relative ``/media/...`` is prefixed in order:
    ``REPORT_PUBLIC_BASE_URL`` (optional dedicated origin) →
    ``FRONTEND_BASE_URL`` (SPA + Vite/nginx 反代 /media，推荐局域网填 http://192.168.x.x:3334) →
    ``BACKEND_BASE_URL`` → dev fallback ``http://127.0.0.1:8000``.
    """
    u = (stored_url or '').strip()
    if not u:
        return ''
    if u.startswith('http://') or u.startswith('https://'):
        return u
    if not u.startswith('/'):
        u = '/' + u
    for base in (
        getattr(settings, 'REPORT_PUBLIC_BASE_URL', '') or '',
        getattr(settings, 'FRONTEND_BASE_URL', '') or '',
        getattr(settings, 'BACKEND_BASE_URL', '') or '',
        resolve_backend_base_url_fallback(),
    ):
        b = base.strip().rstrip('/')
        if b:
            return b + u
    return u


class ExecutorMachineSerializer(serializers.ModelSerializer):
    has_jenkins_token = serializers.SerializerMethodField()

    class Meta:
        model = ExecutorMachine
        fields = [
            'id', 'name', 'hostname', 'ip_address', 'port', 'os_type',
            'labels', 'status', 'description', 'jenkins_node_name',
            'jenkins_url', 'jenkins_username', 'jenkins_token',
            'has_jenkins_token',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'jenkins_token': {'write_only': True, 'required': False},
        }

    def get_has_jenkins_token(self, obj):
        return bool(obj.jenkins_token)

    def update(self, instance, validated_data):
        token = validated_data.get('jenkins_token')
        if token is not None and token.strip() == '':
            validated_data.pop('jenkins_token')
        return super().update(instance, validated_data)


class BuildStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildStep
        fields = ['id', 'order', 'name', 'script', 'timeout', 'on_failure']


class BuildPlanSerializer(serializers.ModelSerializer):
    steps = BuildStepSerializer(many=True, required=False)
    created_by_name = serializers.CharField(
        source='created_by.username', read_only=True, default='')
    executor_machine_name = serializers.CharField(
        source='executor_machine.name', read_only=True, default='')
    executor_machine_jenkins_url = serializers.CharField(
        source='executor_machine.jenkins_url', read_only=True, default='')
    environment_name = serializers.CharField(
        source='environment.name', read_only=True, default='')
    last_execution_status = serializers.SerializerMethodField()
    backend_base_url = serializers.SerializerMethodField()

    class Meta:
        model = BuildPlan
        fields = [
            'id', 'name', 'description',
            'executor_machine', 'executor_machine_name',
            'executor_machine_jenkins_url',
            'environment', 'environment_name',
            'jenkins_job_name',
            'git_repo_url', 'git_branch', 'git_credential_id',
            'workspace_cleanup',
            'report_enabled', 'report_results_dir', 'report_command',
            'environment_variables', 'jenkinsfile_text',
            'cron_expression', 'is_cron_enabled',
            'repeat_run_times', 'repeat_failure_policy',
            'notification_config', 'trigger_token',
            'status', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'steps', 'last_execution_status',
            'backend_base_url',
        ]

    def validate_repeat_run_times(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError("repeat_run_times must be between 1 and 20")
        return value
        read_only_fields = [
            'trigger_token', 'created_by', 'created_at', 'updated_at',
        ]

    def get_last_execution_status(self, obj):
        last = obj.executions.order_by('-started_at').first()
        if last:
            return {
                'id': last.id,
                'status': last.status,
                'started_at': last.started_at,
            }
        return None

    def get_backend_base_url(self, obj):
        return resolve_backend_base_url_fallback()

    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        plan = BuildPlan.objects.create(**validated_data)
        for idx, step_data in enumerate(steps_data):
            step_data.setdefault('order', idx)
            BuildStep.objects.create(build_plan=plan, **step_data)
        return plan

    def update(self, instance, validated_data):
        steps_data = validated_data.pop('steps', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if steps_data is not None:
            instance.steps.all().delete()
            for idx, step_data in enumerate(steps_data):
                step_data.setdefault('order', idx)
                step_data.pop('id', None)
                BuildStep.objects.create(build_plan=instance, **step_data)
        return instance


class BuildPlanListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.username', read_only=True, default='')
    executor_machine_name = serializers.CharField(
        source='executor_machine.name', read_only=True, default='')
    executor_machine_jenkins_url = serializers.CharField(
        source='executor_machine.jenkins_url', read_only=True, default='')
    environment_name = serializers.CharField(
        source='environment.name', read_only=True, default='')
    step_count = serializers.IntegerField(
        source='steps.count', read_only=True)
    last_execution_status = serializers.SerializerMethodField()

    class Meta:
        model = BuildPlan
        fields = [
            'id', 'name', 'description',
            'executor_machine', 'executor_machine_name',
            'executor_machine_jenkins_url',
            'environment', 'environment_name',
            'jenkins_job_name',
            'git_repo_url', 'git_branch', 'git_credential_id',
            'workspace_cleanup',
            'report_enabled', 'report_results_dir', 'report_command',
            'environment_variables', 'jenkinsfile_text',
            'cron_expression', 'is_cron_enabled',
            'repeat_run_times', 'repeat_failure_policy',
            'notification_config',
            'trigger_token', 'status',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'step_count', 'last_execution_status',
        ]

    def get_last_execution_status(self, obj):
        last = obj.executions.order_by('-started_at').first()
        if last:
            return {
                'id': last.id,
                'status': last.status,
                'started_at': last.started_at,
            }
        return None


class BuildExecutionSerializer(serializers.ModelSerializer):
    build_plan_name = serializers.CharField(
        source='build_plan.name', read_only=True)
    executor_machine_name = serializers.CharField(
        source='executor_machine.name', read_only=True, default='')
    duration_display = serializers.CharField(read_only=True)
    report_url = serializers.SerializerMethodField()

    class Meta:
        model = BuildExecution
        fields = [
            'id', 'build_plan', 'build_plan_name',
            'executor_machine', 'executor_machine_name',
            'trigger_type', 'triggered_by', 'status',
            'callback_url', 'callback_notified', 'callback_notified_at', 'callback_last_response',
            'jenkins_build_number', 'jenkins_build_url',
            'log_text', 'log_file',
            'report_type', 'report_url', 'report_data',
            'started_at', 'finished_at', 'duration_ms',
            'duration_display', 'celery_task_id',
        ]
        read_only_fields = [
            'started_at', 'finished_at', 'duration_ms', 'celery_task_id',
        ]

    def get_report_url(self, obj):
        request = self.context.get('request')
        return absolute_report_url(obj.report_url, request)


class BuildExecutionListSerializer(serializers.ModelSerializer):
    build_plan_name = serializers.CharField(
        source='build_plan.name', read_only=True)
    executor_machine_name = serializers.CharField(
        source='executor_machine.name', read_only=True, default='')
    duration_display = serializers.CharField(read_only=True)
    report_url = serializers.SerializerMethodField()

    class Meta:
        model = BuildExecution
        fields = [
            'id', 'build_plan', 'build_plan_name',
            'executor_machine', 'executor_machine_name',
            'trigger_type', 'triggered_by', 'status',
            'callback_url', 'callback_notified', 'callback_notified_at',
            'jenkins_build_number', 'jenkins_build_url',
            'report_type', 'report_url',
            'started_at', 'finished_at', 'duration_ms',
            'duration_display',
        ]

    def get_report_url(self, obj):
        request = self.context.get('request')
        return absolute_report_url(obj.report_url, request)


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'subject', 'body', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DingTalkGroupSerializer(serializers.ModelSerializer):
    has_secret = serializers.SerializerMethodField()

    class Meta:
        model = DingTalkGroup
        fields = [
            'id', 'name', 'webhook_url', 'secret', 'has_secret', 'is_active',
            'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'secret': {'write_only': True},
        }

    def get_has_secret(self, obj):
        return bool(obj.secret)

    def update(self, instance, validated_data):
        secret = validated_data.get('secret')
        if secret is not None and str(secret).strip() == '':
            validated_data.pop('secret')
        return super().update(instance, validated_data)


class DingTalkTemplateSerializer(serializers.ModelSerializer):
    variable_help = serializers.SerializerMethodField()

    class Meta:
        model = DingTalkTemplate
        fields = [
            'id', 'name', 'title_template', 'body_template',
            'is_default', 'is_active', 'description',
            'variable_help', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'variable_help']

    def get_variable_help(self, obj):
        return [{'key': key, 'desc': desc} for key, desc in DingTalkTemplate.VARIABLE_HELP]

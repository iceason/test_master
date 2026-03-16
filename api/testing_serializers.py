from rest_framework import serializers
from .models import ExecutorMachine, BuildPlan, BuildStep, BuildExecution


class ExecutorMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutorMachine
        fields = [
            'id', 'name', 'hostname', 'ip_address', 'port', 'os_type',
            'labels', 'status', 'description', 'jenkins_node_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


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
    environment_name = serializers.CharField(
        source='environment.name', read_only=True, default='')
    last_execution_status = serializers.SerializerMethodField()

    class Meta:
        model = BuildPlan
        fields = [
            'id', 'name', 'description',
            'executor_machine', 'executor_machine_name',
            'environment', 'environment_name',
            'jenkins_job_name', 'jenkins_server_url', 'jenkins_credentials',
            'cron_expression', 'is_cron_enabled',
            'notification_config', 'trigger_token',
            'status', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'steps', 'last_execution_status',
        ]
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
            'environment', 'environment_name',
            'jenkins_job_name', 'jenkins_server_url',
            'cron_expression', 'is_cron_enabled',
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

    class Meta:
        model = BuildExecution
        fields = [
            'id', 'build_plan', 'build_plan_name',
            'executor_machine', 'executor_machine_name',
            'trigger_type', 'triggered_by', 'status',
            'jenkins_build_number', 'jenkins_build_url',
            'log_text', 'log_file',
            'report_type', 'report_url', 'report_data',
            'started_at', 'finished_at', 'duration_ms',
            'duration_display', 'celery_task_id',
        ]
        read_only_fields = [
            'started_at', 'finished_at', 'duration_ms', 'celery_task_id',
        ]


class BuildExecutionListSerializer(serializers.ModelSerializer):
    build_plan_name = serializers.CharField(
        source='build_plan.name', read_only=True)
    executor_machine_name = serializers.CharField(
        source='executor_machine.name', read_only=True, default='')
    duration_display = serializers.CharField(read_only=True)

    class Meta:
        model = BuildExecution
        fields = [
            'id', 'build_plan', 'build_plan_name',
            'executor_machine', 'executor_machine_name',
            'trigger_type', 'triggered_by', 'status',
            'jenkins_build_number', 'jenkins_build_url',
            'report_type', 'report_url',
            'started_at', 'finished_at', 'duration_ms',
            'duration_display',
        ]

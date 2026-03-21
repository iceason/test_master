from rest_framework import serializers
from .models import Directory, Interface, TestCase, TestCaseCategory, Environment, TestExecutionBatch, TestExecution
import yaml
import json

class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

class DirectorySerializer(serializers.ModelSerializer):
    sub_directories = RecursiveField(many=True, read_only=True)
    
    class Meta:
        model = Directory
        fields = ['id', 'name', 'parent', 'level', 'order', 'sub_directories']
        read_only_fields = ['level']

class InterfaceSerializer(serializers.ModelSerializer):
    schema_yaml = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Interface
        fields = '__all__'
        extra_kwargs = {
            'schema': {'required': False}
        }

    def validate(self, attrs):
        schema_yaml = attrs.pop('schema_yaml', None)
        # path 校验
        path = attrs.get('path')
        if path and not str(path).startswith('/'):
            raise serializers.ValidationError({"path": "Path must start with '/'."})
        if schema_yaml:
            try:
                # Try parsing as YAML
                parsed_schema = yaml.safe_load(schema_yaml)
                if not isinstance(parsed_schema, dict):
                     raise serializers.ValidationError({"schema_yaml": "YAML content must parse to a dictionary/object"})
                attrs['schema'] = parsed_schema
            except yaml.YAMLError as e:
                raise serializers.ValidationError({"schema_yaml": f"Invalid YAML format: {str(e)}"})
        return attrs

class TestCaseCategorySerializer(serializers.ModelSerializer):
    sub_categories = RecursiveField(many=True, read_only=True)

    class Meta:
        model = TestCaseCategory
        fields = ['id', 'name', 'code', 'parent', 'description', 'sub_categories']

class TestCaseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)

    class Meta:
        model = TestCase
        fields = '__all__'


class EnvironmentSerializer(serializers.ModelSerializer):
    """环境配置序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)

    class Meta:
        model = Environment
        fields = ['id', 'name', 'code', 'project', 'project_name', 'base_url', 'token', 'description', 'config', 'is_active', 'created_at', 'updated_at']


class TestExecutionSerializer(serializers.ModelSerializer):
    """测试执行记录序列化器"""
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    test_case_interface = serializers.CharField(source='test_case.interface.name', read_only=True)
    project_name = serializers.CharField(source='test_case.project.name', read_only=True, default=None)
    project_id = serializers.IntegerField(source='test_case.project_id', read_only=True, default=None)
    interface_id = serializers.IntegerField(source='test_case.interface_id', read_only=True)
    
    class Meta:
        model = TestExecution
        fields = [
            'id', 'execution_id', 'test_case', 'test_case_name', 'test_case_interface',
            'project_name', 'project_id', 'interface_id',
            'batch', 'status', 'request_url', 'request_method', 'request_headers',
            'request_body', 'response_status', 'response_headers', 'response_body',
            'response_time_ms', 'assertions_passed', 'assertions_failed',
            'assertion_details', 'error_message', 'error_traceback', 'retry_count',
            'parent_execution', 'started_at', 'finished_at', 'duration_ms'
        ]
        read_only_fields = ['execution_id', 'started_at', 'finished_at', 'duration_ms']


class TestExecutionBatchSerializer(serializers.ModelSerializer):
    """测试执行批次序列化器"""
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    execution_records = TestExecutionSerializer(many=True, read_only=True)
    
    class Meta:
        model = TestExecutionBatch
        fields = [
            'id', 'batch_id', 'name', 'trigger_type', 'executor', 'environment',
            'environment_name', 'total_cases', 'passed_cases', 'failed_cases',
            'error_cases', 'status', 'started_at', 'finished_at', 'duration_ms',
            'celery_task_id', 'success_rate', 'execution_records'
        ]
        read_only_fields = ['batch_id', 'started_at', 'finished_at', 'duration_ms', 'success_rate']


class TestExecutionBatchListSerializer(serializers.ModelSerializer):
    """测试执行批次列表序列化器（不包含执行记录详情）"""
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = TestExecutionBatch
        fields = [
            'id', 'batch_id', 'name', 'trigger_type', 'executor', 'environment',
            'environment_name', 'total_cases', 'passed_cases', 'failed_cases',
            'error_cases', 'status', 'started_at', 'finished_at', 'duration_ms',
            'celery_task_id', 'success_rate'
        ]

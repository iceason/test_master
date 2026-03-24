from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Directory, Interface, TestCase, TestCaseCategory, Environment, TestExecutionBatch, TestExecution, ProjectMember
from .serializers import (DirectorySerializer, InterfaceSerializer, TestCaseSerializer, TestCaseCategorySerializer,
                          EnvironmentSerializer, TestExecutionBatchSerializer, TestExecutionBatchListSerializer,
                          TestExecutionSerializer,
                          ProjectSerializer, ProjectMemberSerializer, UserSimpleSerializer)
from rest_framework.permissions import IsAuthenticated, BasePermission
from .test_case_generator import TestCaseGenerator
from .exporters import TestCasesExporter
from asgiref.sync import async_to_sync
from django.contrib.auth import authenticate
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import threading

# Try to import Celery, fallback to threading if not available
import logging as _logging
_logger = _logging.getLogger(__name__)

def _check_celery_available():
    """检查 Celery 是否完全可用（模块 + Redis + Worker）"""
    try:
        from celery.result import AsyncResult  # noqa: F401
        from .tasks import generate_test_cases_task  # noqa: F401
        # 验证 Redis 连接
        import redis as _redis_lib
        _r = _redis_lib.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        _r.ping()
        _r.close()
        # 验证 Celery Worker 是否在线
        from TestCaseGenerator.celery import app as _celery_app
        inspector = _celery_app.control.inspect(timeout=2.0)
        active_workers = inspector.ping()
        if not active_workers:
            _logger.info("Celery: Redis 已连接但无 Worker 在线，降级为线程模式")
            return False
        _logger.info("Celery: 完全可用 (Workers: %s)", list(active_workers.keys()))
        return True
    except Exception as e:
        _logger.info("Celery: 不可用 (%s)，使用线程模式", e)
        return False

CELERY_AVAILABLE = _check_celery_available()

# 延迟导入（即使检查失败也确保后续引用不报错）
try:
    from celery.result import AsyncResult
    from .tasks import generate_test_cases_task
except Exception:
    pass

class DirectoryViewSet(viewsets.ModelViewSet):
    queryset = Directory.objects.filter(parent__isnull=True)  # Root directories
    serializer_class = DirectorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['id', 'name', 'order', 'level']
    ordering = ['order', 'id']
    pagination_class = None  # 禁用分页，返回完整树形结构

    def get_queryset(self):
        if self.action == 'list':
            return Directory.objects.filter(parent__isnull=True)
        return Directory.objects.all()

class InterfaceViewSet(viewsets.ModelViewSet):
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['directory', 'method']
    search_fields = ['name', 'path']
    ordering_fields = ['id', 'name', 'method', 'path', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        directory_id = self.request.query_params.get('directory')
        if directory_id:
            queryset = queryset.filter(directory_id=directory_id)
        return queryset

    @action(detail=True, methods=['post'])
    def generate_cases(self, request, pk=None):
        interface = self.get_object()
        
        # 解析参数: category_ids (list of integers)
        category_ids = request.data.get('category_ids', [])
        if not isinstance(category_ids, list):
            category_ids = []
        
        # 如果Celery可用，使用Celery；否则使用线程
        try:
            if CELERY_AVAILABLE:
                async_result = generate_test_cases_task.delay(interface.id, category_ids)
                return Response({'status': 'accepted', 'task_id': async_result.id}, status=status.HTTP_202_ACCEPTED)
        except Exception:
            # Celery 运行时失败，降级到线程
            pass
        
        # 回退到线程处理
        def run_in_thread():
            generator = TestCaseGenerator(interface)
            async_to_sync(generator.generate)(category_ids)
        
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        return Response({'status': 'processing', 'message': 'Task started in background'}, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Invalid ids'}, status=status.HTTP_400_BAD_REQUEST)
        
        count, _ = Interface.objects.filter(id__in=ids).delete()
        return Response({'status': 'success', 'deleted_count': count})

class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'test_field']
    filterset_fields = ['interface', 'test_type', 'category', 'project']
    ordering_fields = ['id', 'name', 'created_at', 'updated_at', 'test_type']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        interface_id = self.request.query_params.get('interface')
        if interface_id:
            queryset = queryset.filter(interface_id=interface_id)
        return queryset

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Invalid ids'}, status=status.HTTP_400_BAD_REQUEST)
        
        count, _ = TestCase.objects.filter(id__in=ids).delete()
        return Response({'status': 'success', 'deleted_count': count})

class TestCaseCategoryViewSet(viewsets.ModelViewSet):
    queryset = TestCaseCategory.objects.filter(parent__isnull=True)
    serializer_class = TestCaseCategorySerializer
    pagination_class = None  # 禁用分页，返回完整树形结构

class ExportTestCasesView(APIView):
    def post(self, request):
        scope = request.data.get('scope')
        ids = request.data.get('ids', [])
        fmt = request.data.get('format', 'json')
        
        if not scope or not ids:
            return Response({'error': 'Missing scope or ids'}, status=400)
            
        exporter = TestCasesExporter()
        try:
            if fmt == 'csv':
                # 流式输出CSV
                from django.http import StreamingHttpResponse
                generator = exporter.stream_csv(scope, ids)
                response = StreamingHttpResponse(generator, content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="test_cases.csv"'
                return response
            else:
                content, content_type, filename = exporter.export(scope, ids, fmt)
                response = HttpResponse(content, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class YamlExportView(APIView):
    """YAML导出API"""
    
    def post(self, request):
        """
        导出YAML配置
        
        请求体:
        {
            "scope": "testcase|interface|environment",
            "ids": [1, 2, 3]
        }
        """
        from .executor.yaml_plugin import YamlPlugin
        
        scope = request.data.get('scope')
        ids = request.data.get('ids', [])
        
        if not scope or not ids:
            return Response({'error': '缺少scope或ids参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plugin = YamlPlugin()
            yaml_content = plugin.export_to_yaml(scope, ids)
            
            response = HttpResponse(yaml_content, content_type='application/x-yaml')
            response['Content-Disposition'] = f'attachment; filename="{scope}_export.yaml"'
            return response
            
        except Exception as e:
            return Response({'error': f'导出失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class YamlImportView(APIView):
    """YAML导入API"""
    
    def post(self, request):
        """
        导入YAML配置
        
        请求体:
        {
            "yaml_content": "...",
            "mode": "merge|replace"
        }
        """
        from .executor.yaml_plugin import YamlPlugin
        
        yaml_content = request.data.get('yaml_content')
        mode = request.data.get('mode', 'merge')
        
        if not yaml_content:
            return Response({'error': '缺少yaml_content参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        if mode not in ['merge', 'replace']:
            return Response({'error': 'mode必须是merge或replace'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plugin = YamlPlugin()
            result = plugin.import_from_yaml(yaml_content, mode)
            
            return Response({
                'status': 'success',
                'message': '导入成功',
                'result': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'导入失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ImportOpenAPIView(APIView):
    """导入 OpenAPI/Swagger 文档"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        导入 OpenAPI 文档，解析并批量创建接口

        请求方式: multipart/form-data
        参数:
            - file: OpenAPI 文件 (JSON/YAML)
            - directory_id: 目标目录 ID
        """
        from .openapi_parser import OpenAPIParser

        file = request.FILES.get('file')
        directory_id = request.data.get('directory_id')

        if not file:
            return Response({'error': '请上传文件'}, status=status.HTTP_400_BAD_REQUEST)

        if not directory_id:
            return Response({'error': '请选择目标目录'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证目录是否存在
        try:
            directory = Directory.objects.get(id=directory_id)
        except Directory.DoesNotExist:
            return Response({'error': '目录不存在'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证文件大小 (10MB 上限)
        if file.size > 10 * 1024 * 1024:
            return Response({'error': '文件大小不能超过 10MB'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response({'error': '文件编码不支持，请使用 UTF-8 编码'}, status=status.HTTP_400_BAD_REQUEST)

        # 判断文件类型
        file_name = file.name.lower()
        if file_name.endswith('.json'):
            file_type = 'json'
        elif file_name.endswith(('.yaml', '.yml')):
            file_type = 'yaml'
        else:
            return Response({'error': '不支持的文件格式，请上传 JSON 或 YAML 文件'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parser = OpenAPIParser()

            # 解析文件
            spec = parser.parse_file(content, file_type)

            # 验证规范
            parser.validate_spec(spec)

            # 提取接口列表
            interfaces_data = parser.extract_interfaces(spec)

            if not interfaces_data:
                return Response({'error': '未在文档中找到任何接口定义'}, status=status.HTTP_400_BAD_REQUEST)

            # 批量创建/更新接口
            created = []
            updated = []
            errors = []

            for iface in interfaces_data:
                try:
                    obj, was_created = Interface.objects.update_or_create(
                        method=iface['method'],
                        path=iface['path'],
                        defaults={
                            'name': iface['name'],
                            'directory_id': directory_id,
                            'schema': iface['schema'],
                        }
                    )
                    entry = {'id': obj.id, 'name': obj.name, 'method': obj.method, 'path': obj.path}
                    if was_created:
                        created.append(entry)
                    else:
                        updated.append(entry)
                except Exception as e:
                    errors.append({
                        'method': iface['method'],
                        'path': iface['path'],
                        'error': str(e),
                    })

            return Response({
                'total': len(interfaces_data),
                'created': len(created),
                'updated': len(updated),
                'failed': len(errors),
                'created_items': created,
                'updated_items': updated,
                'errors': errors,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'导入失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImportOpenAPIPreviewView(APIView):
    """预览 OpenAPI 文档信息（不实际导入）"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        预览 OpenAPI 文档，返回接口统计和标签信息

        请求方式: multipart/form-data
        参数:
            - file: OpenAPI 文件 (JSON/YAML)
        """
        from .openapi_parser import OpenAPIParser

        file = request.FILES.get('file')
        if not file:
            return Response({'error': '请上传文件'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response({'error': '文件编码不支持'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = file.name.lower()
        if file_name.endswith('.json'):
            file_type = 'json'
        elif file_name.endswith(('.yaml', '.yml')):
            file_type = 'yaml'
        else:
            return Response({'error': '不支持的文件格式'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parser = OpenAPIParser()
            spec = parser.parse_file(content, file_type)
            parser.validate_spec(spec)
            info = parser.get_spec_info(spec)
            return Response(info, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'解析失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ObtainTokenView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'code': 400, 'data': None, 'message': '缺少用户名或密码'}, status=400)
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'code': 400, 'data': None, 'message': '用户名或密码错误'}, status=400)
        refresh = RefreshToken.for_user(user)
        return Response({'code': 0, 'data': {'access': str(refresh.access_token), 'refresh': str(refresh)}, 'message': 'ok'})


class RefreshTokenView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'code': 400, 'data': None, 'message': '缺少 refresh token'}, status=400)
        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)
            new_refresh = str(refresh)
            return Response({'code': 0, 'data': {'access': new_access, 'refresh': new_refresh}, 'message': 'ok'})
        except Exception:
            return Response({'code': 401, 'data': None, 'message': 'refresh token 已过期，请重新登录'}, status=401)

class CurrentUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        roles = ['admin'] if user.is_superuser else ['editor']
        data = {
            'id': user.id,
            'name': getattr(user, 'get_full_name', lambda: '')() or user.username,
            'email': getattr(user, 'email', '') or '',
            'username': user.username,
            'roles': roles,
        }
        return Response({'code': 0, 'data': data, 'message': 'ok'})


class TaskStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id: str):
        if not CELERY_AVAILABLE:
            return Response({'error': 'Celery not available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        result = AsyncResult(task_id)
        return Response({'task_id': task_id, 'state': result.state, 'result': str(result.result) if result.result else None})


class EnvironmentViewSet(viewsets.ModelViewSet):
    """测试环境管理"""
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['id']


class TestExecutionBatchViewSet(viewsets.ModelViewSet):
    """测试执行批次管理"""
    queryset = TestExecutionBatch.objects.all()
    serializer_class = TestExecutionBatchSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'trigger_type', 'environment']
    search_fields = ['name', 'executor']
    ordering_fields = ['id', 'started_at', 'finished_at', 'duration_ms']
    ordering = ['-started_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TestExecutionBatchListSerializer
        return TestExecutionBatchSerializer
    
    @action(detail=False, methods=['post'])
    def execute_cases(self, request):
        """
        批量执行测试用例
        
        请求体:
        {
            "name": "批次名称",
            "case_ids": [1, 2, 3],
            "environment": 1,  # 可选，不传则自动匹配
            "parallel": false,
            "executor": "用户名"
        }
        """
        case_ids = request.data.get('case_ids', [])
        environment_id = request.data.get('environment')
        parallel = request.data.get('parallel', False)
        batch_name = request.data.get('name', f'Batch-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        executor_name = request.data.get('executor', request.user.username)
        
        if not case_ids:
            return Response({'error': '未选择测试用例'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 自动匹配环境
        if not environment_id:
            first_case = TestCase.objects.select_related('project').filter(id__in=case_ids).first()
            if first_case and first_case.project:
                env = Environment.objects.filter(project=first_case.project, is_active=True).first()
                if env:
                    environment_id = env.id
            if not environment_id:
                return Response({'error': '未找到该项目关联的活跃环境，请先在环境管理中配置'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            environment = Environment.objects.get(id=environment_id, is_active=True)
        except Environment.DoesNotExist:
            return Response({'error': '测试环境不存在或未启用'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建批次
        batch = TestExecutionBatch.objects.create(
            name=batch_name,
            trigger_type='web',
            executor=executor_name,
            environment=environment,
            total_cases=len(case_ids),
            status='pending'
        )
        
        # 异步执行测试
        try:
            if CELERY_AVAILABLE:
                from .executor_tasks import execute_test_cases_task
                task = execute_test_cases_task.delay(case_ids, environment_id, batch.id, parallel)
                batch.celery_task_id = task.id
                batch.save()
                
                return Response({
                    'batch_id': batch.batch_id,
                    'batch_db_id': batch.id,
                    'task_id': task.id,
                    'status': 'accepted',
                    'message': '测试执行任务已提交'
                }, status=status.HTTP_202_ACCEPTED)
            else:
                # 回退到线程执行（绕过 Celery Task.__call__，直接调用底层函数）
                def run_in_thread():
                    from .executor_tasks import run_batch_execution
                    try:
                        run_batch_execution(case_ids, environment_id, batch.id, parallel)
                    except Exception as exc:
                        _logger.error("Batch %s thread execution failed: %s", batch.id, exc, exc_info=True)
                
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
                
                return Response({
                    'batch_id': batch.batch_id,
                    'batch_db_id': batch.id,
                    'status': 'processing',
                    'message': '测试执行任务已在后台启动'
                }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            batch.delete()
            return Response({'error': f'启动测试执行失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """获取批次执行状态"""
        batch = self.get_object()
        
        serializer = TestExecutionBatchListSerializer(batch)
        data = serializer.data
        
        # 如果有Celery任务ID，查询任务状态
        if batch.celery_task_id and CELERY_AVAILABLE:
            task_result = AsyncResult(batch.celery_task_id)
            data['task_state'] = task_result.state
            data['task_info'] = str(task_result.info) if task_result.info else None
        
        return Response(data)


class TestExecutionViewSet(viewsets.ModelViewSet):
    """测试执行记录管理"""
    queryset = TestExecution.objects.select_related('test_case', 'test_case__interface', 'test_case__project').all()
    serializer_class = TestExecutionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'test_case': ['exact'],
        'batch': ['exact'],
        'test_case__project': ['exact'],
        'test_case__interface': ['exact'],
        'started_at': ['gte', 'lte'],
    }
    search_fields = ['test_case__name', 'request_url']
    ordering_fields = ['id', 'started_at', 'finished_at', 'duration_ms', 'response_time_ms']
    ordering = ['-started_at']
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取执行记录统计信息（支持与列表相同的筛选参数）"""
        qs = self.filter_queryset(self.get_queryset())
        from django.db.models import Count, Avg, Q
        agg = qs.aggregate(
            total=Count('id'),
            passed=Count('id', filter=Q(status='passed')),
            failed=Count('id', filter=Q(status='failed')),
            error=Count('id', filter=Q(status='error')),
            avg_response_time=Avg('response_time_ms'),
        )
        return Response(agg)
    
    @action(detail=False, methods=['post'])
    def execute_single(self, request):
        """
        执行单个测试用例
        
        请求体:
        {
            "case_id": 1,
            "environment": 1  // 可选，不传则自动匹配项目环境
        }
        """
        case_id = request.data.get('case_id')
        environment_id = request.data.get('environment')
        
        if not case_id:
            return Response({'error': '未指定测试用例'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 自动匹配环境
        if not environment_id:
            try:
                test_case = TestCase.objects.select_related('project').get(id=case_id)
                if test_case.project:
                    env = Environment.objects.filter(project=test_case.project, is_active=True).first()
                    if env:
                        environment_id = env.id
                if not environment_id:
                    return Response({'error': '未找到该项目关联的活跃环境，请先在环境管理中配置'}, status=status.HTTP_400_BAD_REQUEST)
            except TestCase.DoesNotExist:
                return Response({'error': '测试用例不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            if CELERY_AVAILABLE:
                from .executor_tasks import execute_single_test_case_task
                task = execute_single_test_case_task.delay(case_id, environment_id)
                
                return Response({
                    'task_id': task.id,
                    'status': 'accepted',
                    'message': '测试用例执行任务已提交'
                }, status=status.HTTP_202_ACCEPTED)
            else:
                from .models import TestCase as TC, Environment as Env
                from .executor.core import TestExecutor, ExecutorConfig
                
                tc = TC.objects.get(id=case_id)
                environment = Env.objects.get(id=environment_id)
                
                extra_config = dict(environment.config) if environment.config else {}
                default_headers = extra_config.pop('default_headers', {})
                if environment.token:
                    default_headers['Authorization'] = f'Bearer {environment.token}'
                
                executor_config = ExecutorConfig(
                    environment=environment.code,
                    base_url=environment.base_url,
                    default_headers=default_headers,
                    **extra_config
                )
                executor = TestExecutor(executor_config)
                
                env_config = {
                    'base_url': environment.base_url,
                    **extra_config
                }
                result = executor.execute_test_case(tc, env_config)
                
                execution = TestExecution.objects.create(
                    test_case=tc,
                    status=result.status,
                    request_url=result.request_url,
                    request_method=result.request_method,
                    request_headers=result.request_headers,
                    request_body=result.request_body,
                    response_status=result.response_status,
                    response_headers=result.response_headers,
                    response_body=result.response_body,
                    response_time_ms=result.response_time_ms,
                    assertions_passed=result.assertions_passed,
                    assertions_failed=result.assertions_failed,
                    assertion_details=result.assertion_details,
                    error_message=result.error_message,
                    error_traceback=result.error_traceback,
                    started_at=result.started_at,
                    finished_at=result.finished_at,
                    duration_ms=result.duration_ms
                )
                
                return Response({
                    'execution_id': str(execution.execution_id),
                    'status': execution.status,
                    'result': TestExecutionSerializer(execution).data
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({'error': f'执行测试用例失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# 项目管理模块
# ---------------------------------------------------------------------------

User = get_user_model()


class IsProjectAdminOrOwner(BasePermission):
    """项目写操作权限：仅 owner / admin 可执行写操作"""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.user.is_superuser:
            return True
        project = obj if isinstance(obj, Directory) else getattr(obj, 'project', None)
        if project is None:
            return False
        return ProjectMember.objects.filter(
            project=project, user=request.user, role__in=['owner', 'admin']
        ).exists()


class ProjectViewSet(viewsets.ModelViewSet):
    """项目管理（基于根级 Directory）"""
    queryset = Directory.objects.filter(parent__isnull=True).prefetch_related('members')
    serializer_class = ProjectSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'order', 'created_at']
    ordering = ['-created_at']
    pagination_class = None

    def perform_create(self, serializer):
        project = serializer.save(parent=None, created_by=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user, role='owner')

    def perform_update(self, serializer):
        serializer.save(parent=None)

    # ----- 成员管理 actions -----

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """获取项目成员列表"""
        project = self.get_object()
        members = ProjectMember.objects.filter(project=project).select_related('user')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """添加项目成员"""
        project = self.get_object()

        if not request.user.is_superuser and not ProjectMember.objects.filter(
            project=project, user=request.user, role__in=['owner', 'admin']
        ).exists():
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')

        if not user_id:
            return Response({'error': '缺少 user_id 参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if ProjectMember.objects.filter(project=project, user=user).exists():
            return Response({'error': '该用户已是项目成员'}, status=status.HTTP_400_BAD_REQUEST)

        member = ProjectMember.objects.create(project=project, user=user, role=role)
        return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """移除项目成员"""
        project = self.get_object()

        if not request.user.is_superuser and not ProjectMember.objects.filter(
            project=project, user=request.user, role__in=['owner', 'admin']
        ).exists():
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': '缺少 user_id 参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = ProjectMember.objects.get(project=project, user_id=user_id)
        except ProjectMember.DoesNotExist:
            return Response({'error': '该用户不是项目成员'}, status=status.HTTP_404_NOT_FOUND)

        if member.role == 'owner' and ProjectMember.objects.filter(project=project, role='owner').count() <= 1:
            return Response({'error': '不能移除项目唯一的所有者'}, status=status.HTTP_400_BAD_REQUEST)

        member.delete()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def update_member_role(self, request, pk=None):
        """更新成员角色"""
        project = self.get_object()

        if not request.user.is_superuser and not ProjectMember.objects.filter(
            project=project, user=request.user, role__in=['owner', 'admin']
        ).exists():
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        new_role = request.data.get('role')

        if not user_id or not new_role:
            return Response({'error': '缺少 user_id 或 role 参数'}, status=status.HTTP_400_BAD_REQUEST)

        valid_roles = [c[0] for c in ProjectMember.ROLE_CHOICES]
        if new_role not in valid_roles:
            return Response({'error': f'无效角色，可选: {valid_roles}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = ProjectMember.objects.get(project=project, user_id=user_id)
        except ProjectMember.DoesNotExist:
            return Response({'error': '该用户不是项目成员'}, status=status.HTTP_404_NOT_FOUND)

        if member.role == 'owner' and new_role != 'owner':
            if ProjectMember.objects.filter(project=project, role='owner').count() <= 1:
                return Response({'error': '不能降级项目唯一的所有者'}, status=status.HTTP_400_BAD_REQUEST)

        member.role = new_role
        member.save()
        return Response(ProjectMemberSerializer(member).data)


class UserListView(APIView):
    """系统用户列表（用于成员选择器）"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        qs = User.objects.filter(is_active=True).order_by('username')
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))
        serializer = UserSimpleSerializer(qs[:50], many=True)
        return Response(serializer.data)

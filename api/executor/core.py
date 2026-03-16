"""
测试执行引擎核心

提供工业级的测试执行能力
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from .http_client import EnhancedHttpClient, ConnectionPoolManager, ClientConfig
from .assertion_engine import AssertionEngine, Assertion, AssertionResults

logger = logging.getLogger(__name__)


@dataclass
class ExecutorConfig:
    """执行器配置"""
    environment: str = 'test'
    base_url: Optional[str] = None
    default_headers: Dict[str, str] = field(default_factory=dict)
    default_timeout: tuple = (5, 30)
    max_retries: int = 3
    verify_ssl: bool = True
    report_dir: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutorConfig':
        """从字典创建配置"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    @classmethod
    def from_env(cls, env: str) -> 'ExecutorConfig':
        """从环境名称创建默认配置"""
        return cls(environment=env)


@dataclass
class TestResult:
    """单个测试执行结果"""
    test_case_id: Optional[int] = None
    test_case_name: str = ""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"  # pending/running/passed/failed/error
    
    # 请求信息
    request_method: str = ""
    request_url: str = ""
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: Any = None
    
    # 响应信息
    response_status: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Any = None
    response_time_ms: Optional[int] = None
    
    # 断言结果
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_details: List[Dict] = field(default_factory=list)
    
    # 错误信息
    error_message: str = ""
    error_traceback: str = ""
    
    # 时间信息
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'test_case_id': self.test_case_id,
            'test_case_name': self.test_case_name,
            'execution_id': self.execution_id,
            'status': self.status,
            'request_method': self.request_method,
            'request_url': self.request_url,
            'request_headers': self.request_headers,
            'request_body': self.request_body,
            'response_status': self.response_status,
            'response_headers': self.response_headers,
            'response_body': self.response_body,
            'response_time_ms': self.response_time_ms,
            'assertions_passed': self.assertions_passed,
            'assertions_failed': self.assertions_failed,
            'assertion_details': self.assertion_details,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration_ms': self.duration_ms,
        }


@dataclass
class BatchResult:
    """批量执行结果"""
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    error_cases: int = 0
    results: List[TestResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_cases == 0:
            return 0.0
        return (self.passed_cases / self.total_cases) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'batch_id': self.batch_id,
            'total_cases': self.total_cases,
            'passed_cases': self.passed_cases,
            'failed_cases': self.failed_cases,
            'error_cases': self.error_cases,
            'success_rate': self.success_rate,
            'results': [r.to_dict() for r in self.results],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration_ms': self.duration_ms,
        }


class TestExecutor:
    """
    工业级测试执行引擎
    
    特性:
    - 支持pytest插件机制
    - 连接池管理（requests.Session）
    - 并发执行控制（线程池/进程池）
    - 实时结果流（WebSocket/SSE）
    - 失败重试和断路器
    """
    
    def __init__(self, config: ExecutorConfig):
        self.config = config
        self.http_client = self._create_http_client()
        self.assertion_engine = AssertionEngine()
        logger.info(f"TestExecutor初始化完成 - 环境: {config.environment}")
    
    def _create_http_client(self) -> EnhancedHttpClient:
        """创建HTTP客户端"""
        client_config = ClientConfig(
            max_retries=self.config.max_retries,
            timeout=self.config.default_timeout,
            verify_ssl=self.config.verify_ssl
        )
        
        if self.config.base_url:
            return ConnectionPoolManager.get_client(self.config.base_url, client_config)
        else:
            return EnhancedHttpClient(client_config)
    
    def execute_test_case(
        self,
        test_case: Any,  # TestCase model instance or dict
        environment_config: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例对象或字典
            environment_config: 环境配置（覆盖默认配置）
            
        Returns:
            TestResult
        """
        result = TestResult()
        result.started_at = datetime.now()
        result.status = 'running'
        
        try:
            # 解析测试用例数据
            if hasattr(test_case, 'id'):
                # Django模型实例
                result.test_case_id = test_case.id
                result.test_case_name = test_case.name
                interface = test_case.interface
                method = interface.method
                path = interface.path
                request_data = test_case.request_data or {}
                expected_response = test_case.expected_response or {}
                expected_value = test_case.expected_value or {}
            else:
                # 字典格式
                result.test_case_name = test_case.get('name', 'Unknown')
                method = test_case.get('method', 'GET')
                path = test_case.get('path', '')
                request_data = test_case.get('request_data', {})
                expected_response = test_case.get('expected_response', {})
                expected_value = test_case.get('expected_value', {})
            
            # 构建完整URL
            base_url = (environment_config or {}).get('base_url', self.config.base_url or '')
            url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
            
            # 准备请求头
            headers = dict(self.config.default_headers)
            if 'headers' in request_data:
                headers.update(request_data.pop('headers'))
            
            # 记录请求信息
            result.request_method = method
            result.request_url = url
            result.request_headers = headers
            result.request_body = request_data
            
            # 发送请求
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = self.http_client.get(url, headers=headers, params=request_data)
            elif method.upper() == 'POST':
                response = self.http_client.post(url, headers=headers, json=request_data)
            elif method.upper() == 'PUT':
                response = self.http_client.put(url, headers=headers, json=request_data)
            elif method.upper() == 'DELETE':
                response = self.http_client.delete(url, headers=headers, params=request_data)
            elif method.upper() == 'PATCH':
                response = self.http_client.patch(url, headers=headers, json=request_data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 记录响应信息
            result.response_status = response.status_code
            result.response_headers = dict(response.headers)
            result.response_time_ms = response_time_ms
            
            try:
                result.response_body = response.json()
            except:
                result.response_body = response.text
            
            # 执行断言
            assertions = self._build_assertions(expected_response, expected_value)
            assertion_results = self.assertion_engine.assert_response(
                response, assertions, response_time_ms
            )
            
            result.assertions_passed = assertion_results.passed_count
            result.assertions_failed = assertion_results.failed_count
            result.assertion_details = [r.to_dict() for r in assertion_results.results]
            
            # 判断测试状态
            if assertion_results.passed:
                result.status = 'passed'
            else:
                result.status = 'failed'
                result.error_message = f"{assertion_results.failed_count} 个断言失败"
            
        except Exception as e:
            result.status = 'error'
            result.error_message = str(e)
            logger.error(f"测试用例执行异常: {e}", exc_info=True)
            import traceback
            result.error_traceback = traceback.format_exc()
        
        finally:
            result.finished_at = datetime.now()
            if result.started_at:
                result.duration_ms = int(
                    (result.finished_at - result.started_at).total_seconds() * 1000
                )
        
        return result
    
    def execute_batch(
        self,
        test_cases: List[Any],
        environment_config: Optional[Dict[str, Any]] = None
    ) -> BatchResult:
        """
        批量执行测试用例（顺序执行）
        
        Args:
            test_cases: 测试用例列表
            environment_config: 环境配置
            
        Returns:
            BatchResult
        """
        batch_result = BatchResult()
        batch_result.started_at = datetime.now()
        batch_result.total_cases = len(test_cases)
        
        logger.info(f"开始批量执行 {len(test_cases)} 个测试用例")
        
        for test_case in test_cases:
            result = self.execute_test_case(test_case, environment_config)
            batch_result.results.append(result)
            
            if result.status == 'passed':
                batch_result.passed_cases += 1
            elif result.status == 'failed':
                batch_result.failed_cases += 1
            elif result.status == 'error':
                batch_result.error_cases += 1
        
        batch_result.finished_at = datetime.now()
        batch_result.duration_ms = int(
            (batch_result.finished_at - batch_result.started_at).total_seconds() * 1000
        )
        
        logger.info(
            f"批量执行完成 - 总数: {batch_result.total_cases}, "
            f"通过: {batch_result.passed_cases}, "
            f"失败: {batch_result.failed_cases}, "
            f"错误: {batch_result.error_cases}, "
            f"耗时: {batch_result.duration_ms}ms"
        )
        
        return batch_result
    
    def _build_assertions(
        self,
        expected_response: Dict[str, Any],
        expected_value: Dict[str, Any]
    ) -> List[Assertion]:
        """
        构建断言列表
        
        Args:
            expected_response: 旧版期望响应格式
            expected_value: 新版期望值格式
            
        Returns:
            断言列表
        """
        assertions = []
        
        # 处理旧版格式（expected_response）
        if expected_response:
            if 'status' in expected_response:
                assertions.append(Assertion(
                    type='status_code',
                    expected=expected_response['status'],
                    description='HTTP状态码'
                ))
            
            if 'contains_fields' in expected_response:
                for field in expected_response['contains_fields']:
                    assertions.append(Assertion(
                        type='jsonpath',
                        actual_path=f'$.{field}',
                        expected=None,  # 只检查字段存在
                        description=f'字段 {field} 存在'
                    ))
            
            if 'field_values' in expected_response:
                for field, value in expected_response['field_values'].items():
                    assertions.append(Assertion(
                        type='equals',
                        actual_path=field,
                        expected=value,
                        description=f'字段 {field} 等于 {value}'
                    ))
        
        # 处理新版格式（expected_value）
        if expected_value:
            if 'status_code' in expected_value:
                assertions.append(Assertion(
                    type='status_code',
                    expected=expected_value['status_code'],
                    description='HTTP状态码'
                ))
            
            if 'response_time' in expected_value:
                assertions.append(Assertion(
                    type='response_time',
                    expected=expected_value['response_time'],
                    description='响应时间'
                ))
            
            if 'assertions' in expected_value:
                for assertion_data in expected_value['assertions']:
                    assertions.append(Assertion(**assertion_data))
        
        # 如果没有任何断言，至少检查状态码为2xx
        if not assertions:
            assertions.append(Assertion(
                type='status_code',
                expected=200,
                description='默认状态码200'
            ))
        
        return assertions
    
    def close(self):
        """关闭执行器"""
        if hasattr(self.http_client, 'close'):
            self.http_client.close()
        logger.info("TestExecutor已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

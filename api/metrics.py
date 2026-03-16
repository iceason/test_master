"""
Prometheus指标收集和导出
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse
from django.views import View
import logging

logger = logging.getLogger(__name__)

# 定义Prometheus指标
test_executions_total = Counter(
    'test_executions_total',
    'Total number of test executions',
    ['environment', 'status', 'trigger_type']
)

test_duration_seconds = Histogram(
    'test_duration_seconds',
    'Test execution duration in seconds',
    ['test_case_name', 'environment'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, float('inf'))
)

test_response_time_seconds = Histogram(
    'test_response_time_seconds',
    'HTTP response time in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, float('inf'))
)

active_test_executions = Gauge(
    'active_test_executions',
    'Number of currently running test executions',
    ['environment']
)

test_assertions_total = Counter(
    'test_assertions_total',
    'Total number of assertions',
    ['status']  # passed/failed
)

batch_executions_total = Counter(
    'batch_executions_total',
    'Total number of batch executions',
    ['trigger_type', 'status']
)


class MetricsCollector:
    """指标收集器"""
    
    @staticmethod
    def record_execution(execution):
        """记录测试执行指标"""
        from .models import TestExecution
        
        if not isinstance(execution, TestExecution):
            return
        
        # 执行总数
        test_executions_total.labels(
            environment=execution.batch.environment.code if execution.batch and execution.batch.environment else 'unknown',
            status=execution.status,
            trigger_type=execution.batch.trigger_type if execution.batch else 'unknown'
        ).inc()
        
        # 执行耗时
        if execution.duration_ms and execution.test_case:
            test_duration_seconds.labels(
                test_case_name=execution.test_case.name,
                environment=execution.batch.environment.code if execution.batch and execution.batch.environment else 'unknown'
            ).observe(execution.duration_ms / 1000.0)
        
        # 响应时间
        if execution.response_time_ms:
            test_response_time_seconds.labels(
                method=execution.request_method,
                endpoint=execution.request_url
            ).observe(execution.response_time_ms / 1000.0)
        
        # 断言统计
        test_assertions_total.labels(status='passed').inc(execution.assertions_passed)
        test_assertions_total.labels(status='failed').inc(execution.assertions_failed)
        
        logger.debug(f"记录执行指标: {execution.test_case.name if execution.test_case else 'unknown'}")
    
    @staticmethod
    def record_batch(batch):
        """记录批次执行指标"""
        from .models import TestExecutionBatch
        
        if not isinstance(batch, TestExecutionBatch):
            return
        
        batch_executions_total.labels(
            trigger_type=batch.trigger_type,
            status=batch.status
        ).inc()
        
        logger.debug(f"记录批次指标: {batch.batch_id}")
    
    @staticmethod
    def set_active_executions(environment: str, count: int):
        """设置活跃执行数"""
        active_test_executions.labels(environment=environment).set(count)


class PrometheusMetricsView(View):
    """Prometheus指标导出端点"""
    
    def get(self, request):
        """导出Prometheus格式指标"""
        metrics = generate_latest()
        return HttpResponse(metrics, content_type=CONTENT_TYPE_LATEST)

"""
测试执行相关的Celery任务
"""

from celery import shared_task
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def execute_test_cases_task(self, case_ids: list, environment_id: int, batch_id: int, parallel: bool = False):
    """
    异步执行测试用例任务
    
    Args:
        self: Celery任务实例
        case_ids: 测试用例ID列表
        environment_id: 环境ID
        batch_id: 批次ID
        parallel: 是否并发执行
        
    Returns:
        dict: 执行结果摘要
    """
    from .models import TestCase, Environment, TestExecutionBatch, TestExecution
    from .executor.core import TestExecutor, ExecutorConfig
    
    # 获取批次对象
    batch = TestExecutionBatch.objects.get(id=batch_id)
    batch.status = 'running'
    batch.celery_task_id = self.request.id
    batch.save()
    
    try:
        # 获取环境配置
        environment = Environment.objects.get(id=environment_id)
        env_config = {
            'base_url': environment.base_url,
            **environment.config
        }
        
        # 创建执行器
        executor_config = ExecutorConfig(
            environment=environment.code,
            base_url=environment.base_url,
            **environment.config
        )
        executor = TestExecutor(executor_config)
        
        # 获取测试用例
        test_cases = TestCase.objects.filter(id__in=case_ids)
        
        if parallel:
            # TODO: 实现并发执行
            results = []
            for test_case in test_cases:
                result = executor.execute_test_case(test_case, env_config)
                results.append(result)
        else:
            # 顺序执行
            batch_result = executor.execute_batch(list(test_cases), env_config)
            results = batch_result.results
        
        # 保存执行结果
        for result in results:
            execution = TestExecution.objects.create(
                test_case_id=result.test_case_id,
                batch=batch,
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
        
        # 更新批次统计信息
        batch.total_cases = len(results)
        batch.passed_cases = sum(1 for r in results if r.status == 'passed')
        batch.failed_cases = sum(1 for r in results if r.status == 'failed')
        batch.error_cases = sum(1 for r in results if r.status == 'error')
        batch.status = 'completed'
        batch.finished_at = timezone.now()
        
        if batch.started_at:
            batch.duration_ms = int((batch.finished_at - batch.started_at).total_seconds() * 1000)
        
        batch.save()
        
        logger.info(
            f"批次 {batch.batch_id} 执行完成 - "
            f"总数: {batch.total_cases}, 通过: {batch.passed_cases}, "
            f"失败: {batch.failed_cases}, 错误: {batch.error_cases}"
        )
        
        return {
            'batch_id': str(batch.batch_id),
            'status': 'completed',
            'total_cases': batch.total_cases,
            'passed_cases': batch.passed_cases,
            'failed_cases': batch.failed_cases,
            'error_cases': batch.error_cases,
            'success_rate': batch.success_rate
        }
        
    except Exception as e:
        logger.error(f"批次 {batch.batch_id} 执行异常: {e}", exc_info=True)
        batch.status = 'completed'  # 即使有异常也标记为完成
        batch.finished_at = timezone.now()
        if batch.started_at:
            batch.duration_ms = int((batch.finished_at - batch.started_at).total_seconds() * 1000)
        batch.save()
        
        raise


@shared_task(bind=True)
def execute_single_test_case_task(self, case_id: int, environment_id: int):
    """
    异步执行单个测试用例
    
    Args:
        self: Celery任务实例
        case_id: 测试用例ID
        environment_id: 环境ID
        
    Returns:
        dict: 执行结果
    """
    from .models import TestCase, Environment, TestExecution
    from .executor.core import TestExecutor, ExecutorConfig
    
    try:
        # 获取测试用例和环境
        test_case = TestCase.objects.get(id=case_id)
        environment = Environment.objects.get(id=environment_id)
        
        # 创建执行器
        executor_config = ExecutorConfig(
            environment=environment.code,
            base_url=environment.base_url,
            **environment.config
        )
        executor = TestExecutor(executor_config)
        
        # 执行测试用例
        env_config = {
            'base_url': environment.base_url,
            **environment.config
        }
        result = executor.execute_test_case(test_case, env_config)
        
        # 保存执行结果
        execution = TestExecution.objects.create(
            test_case=test_case,
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
        
        return {
            'execution_id': str(execution.execution_id),
            'status': execution.status,
            'response_status': execution.response_status,
            'response_time_ms': execution.response_time_ms
        }
        
    except Exception as e:
        logger.error(f"测试用例 {case_id} 执行异常: {e}", exc_info=True)
        raise

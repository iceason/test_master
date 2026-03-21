"""
测试执行相关的Celery任务
"""

from celery import shared_task
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def run_batch_execution(case_ids: list, environment_id: int, batch_id: int, parallel: bool = False, celery_task_id: str = ''):
    """
    核心批量执行逻辑 - 逐条执行并实时更新进度。
    线程模式和 Celery 模式共用此函数，避免 bind=True 的参数绑定问题。
    """
    from .models import TestCase, Environment, TestExecutionBatch, TestExecution
    from .executor.core import TestExecutor, ExecutorConfig

    batch = TestExecutionBatch.objects.get(id=batch_id)
    batch.status = 'running'
    if celery_task_id:
        batch.celery_task_id = celery_task_id
    batch.save()

    try:
        environment = Environment.objects.get(id=environment_id)
        extra_config = dict(environment.config) if environment.config else {}
        default_headers = extra_config.pop('default_headers', {})
        if environment.token:
            default_headers['Authorization'] = f'Bearer {environment.token}'

        env_config = {
            'base_url': environment.base_url,
            **extra_config
        }

        executor_config = ExecutorConfig(
            environment=environment.code,
            base_url=environment.base_url,
            default_headers=default_headers,
            **extra_config
        )
        executor = TestExecutor(executor_config)

        test_cases = list(TestCase.objects.filter(id__in=case_ids))
        passed = 0
        failed = 0
        errors = 0

        for test_case in test_cases:
            try:
                result = executor.execute_test_case(test_case, env_config)
            except Exception as exc:
                logger.error("用例 %s 执行异常: %s", test_case.id, exc, exc_info=True)
                from .executor.core import TestResult
                result = TestResult(
                    test_case_id=test_case.id,
                    status='error',
                    request_url='',
                    request_method=getattr(test_case.interface, 'method', '') if hasattr(test_case, 'interface') else '',
                    error_message=str(exc),
                )

            TestExecution.objects.create(
                test_case=test_case,
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

            if result.status == 'passed':
                passed += 1
            elif result.status == 'failed':
                failed += 1
            else:
                errors += 1

            batch.passed_cases = passed
            batch.failed_cases = failed
            batch.error_cases = errors
            batch.save(update_fields=['passed_cases', 'failed_cases', 'error_cases'])

        batch.status = 'completed'
        batch.finished_at = timezone.now()
        if batch.started_at:
            batch.duration_ms = int((batch.finished_at - batch.started_at).total_seconds() * 1000)
        batch.save()

        logger.info(
            "批次 %s 执行完成 - 总数: %s, 通过: %s, 失败: %s, 错误: %s",
            batch.batch_id, batch.total_cases, passed, failed, errors
        )

        return {
            'batch_id': str(batch.batch_id),
            'status': 'completed',
            'total_cases': batch.total_cases,
            'passed_cases': passed,
            'failed_cases': failed,
            'error_cases': errors,
            'success_rate': batch.success_rate
        }

    except Exception as e:
        logger.error("批次 %s 执行异常: %s", batch.batch_id, e, exc_info=True)
        batch.status = 'completed'
        batch.finished_at = timezone.now()
        if batch.started_at:
            batch.duration_ms = int((batch.finished_at - batch.started_at).total_seconds() * 1000)
        batch.save()
        raise


@shared_task(bind=True)
def execute_test_cases_task(self, case_ids: list, environment_id: int, batch_id: int, parallel: bool = False):
    """Celery 入口 - 委托给 run_batch_execution"""
    return run_batch_execution(
        case_ids, environment_id, batch_id, parallel,
        celery_task_id=self.request.id if self else ''
    )


def run_single_execution(case_id: int, environment_id: int):
    """
    核心单条执行逻辑。线程模式和 Celery 模式共用。
    """
    from .models import TestCase, Environment, TestExecution
    from .executor.core import TestExecutor, ExecutorConfig

    test_case = TestCase.objects.get(id=case_id)
    environment = Environment.objects.get(id=environment_id)

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
    result = executor.execute_test_case(test_case, env_config)

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


@shared_task(bind=True)
def execute_single_test_case_task(self, case_id: int, environment_id: int):
    """Celery 入口 - 委托给 run_single_execution"""
    return run_single_execution(case_id, environment_id)

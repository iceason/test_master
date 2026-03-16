"""
使用示例：集成模式
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestCaseGenerator.settings')
django.setup()

from api.models import TestCase, Environment
from api.executor.core import TestExecutor, ExecutorConfig

def example_execute_single_case():
    """示例1：执行单个测试用例"""
    print("=" * 60)
    print("示例1：执行单个测试用例")
    print("=" * 60)
    
    # 获取测试用例和环境
    test_case = TestCase.objects.first()
    environment = Environment.objects.first()
    
    if not test_case or not environment:
        print("请先创建测试用例和环境配置")
        return
    
    # 创建执行器
    config = ExecutorConfig(
        environment=environment.code,
        base_url=environment.base_url,
        **environment.config
    )
    executor = TestExecutor(config)
    
    # 执行测试
    result = executor.execute_test_case(test_case, {'base_url': environment.base_url})
    
    # 输出结果
    print(f"\n测试用例: {result.test_case_name}")
    print(f"状态: {result.status}")
    print(f"响应状态码: {result.response_status}")
    print(f"响应时间: {result.response_time_ms}ms")
    print(f"断言通过: {result.assertions_passed}")
    print(f"断言失败: {result.assertions_failed}")
    
    if result.error_message:
        print(f"错误: {result.error_message}")
    
    executor.close()


def example_execute_batch():
    """示例2：批量执行测试用例"""
    print("\n" + "=" * 60)
    print("示例2：批量执行测试用例")
    print("=" * 60)
    
    # 获取多个测试用例
    test_cases = list(TestCase.objects.all()[:5])
    environment = Environment.objects.first()
    
    if not test_cases or not environment:
        print("请先创建测试用例和环境配置")
        return
    
    # 创建执行器
    config = ExecutorConfig(
        environment=environment.code,
        base_url=environment.base_url,
        report_dir='./reports'
    )
    executor = TestExecutor(config)
    
    # 批量执行
    batch_result = executor.execute_batch(test_cases, {'base_url': environment.base_url})
    
    # 输出结果
    print(f"\n批次ID: {batch_result.batch_id}")
    print(f"总用例数: {batch_result.total_cases}")
    print(f"通过: {batch_result.passed_cases} ({batch_result.success_rate:.1f}%)")
    print(f"失败: {batch_result.failed_cases}")
    print(f"错误: {batch_result.error_cases}")
    print(f"总耗时: {batch_result.duration_ms}ms")
    
    # 生成报告
    from api.executor.reporter import TestReporter
    reporter = TestReporter('./reports')
    
    html_report = reporter.generate_html_report(batch_result)
    print(f"\nHTML报告: {html_report}")
    
    junit_report = reporter.generate_junit_xml(batch_result)
    print(f"JUnit XML报告: {junit_report}")
    
    executor.close()


def example_yaml_export():
    """示例3：导出YAML配置"""
    print("\n" + "=" * 60)
    print("示例3：导出YAML配置")
    print("=" * 60)
    
    from api.executor.yaml_plugin import YamlPlugin
    
    plugin = YamlPlugin()
    
    # 导出测试用例
    test_case_ids = list(TestCase.objects.values_list('id', flat=True)[:3])
    if test_case_ids:
        yaml_content = plugin.export_to_yaml('testcase', test_case_ids)
        print("\n测试用例YAML:")
        print(yaml_content)
    
    # 导出环境配置
    env_ids = list(Environment.objects.values_list('id', flat=True))
    if env_ids:
        yaml_content = plugin.export_to_yaml('environment', env_ids)
        print("\n环境配置YAML:")
        print(yaml_content)


if __name__ == '__main__':
    example_execute_single_case()
    example_execute_batch()
    example_yaml_export()

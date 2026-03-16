"""
使用示例：独立模式（纯YAML驱动）
"""

from pathlib import Path
import yaml

# 独立运行，无需Django
from api.executor.core import TestExecutor, ExecutorConfig

def example_standalone_yaml_execution():
    """示例：从YAML文件独立执行测试"""
    print("=" * 60)
    print("独立模式：从YAML执行API测试")
    print("=" * 60)
    
    # 加载YAML配置
    yaml_file = Path(__file__).parent / 'configs' / 'api_tests.yaml'
    if not yaml_file.exists():
        print(f"YAML文件不存在: {yaml_file}")
        return
    
    with open(yaml_file, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    if config_data.get('type') != 'testcases':
        print("此示例仅支持testcases类型的YAML")
        return
    
    # 创建执行器（使用默认配置）
    executor_config = ExecutorConfig(
        environment='test',
        base_url='http://test-api.example.com',  # 根据实际情况修改
        default_timeout=(5, 30),
        max_retries=3
    )
    
    executor = TestExecutor(executor_config)
    
    # 准备测试用例（从YAML转换为执行器格式）
    test_cases = []
    for tc in config_data.get('testcases', []):
        test_case_dict = {
            'name': tc['name'],
            'method': tc['interface']['method'],
            'path': tc['interface']['path'],
            'request_data': tc.get('request_data', {}),
            'expected_response': tc.get('expected_response', {}),
            'expected_value': tc.get('expected_value', {})
        }
        test_cases.append(test_case_dict)
    
    # 执行测试
    print(f"\n开始执行 {len(test_cases)} 个测试用例...")
    batch_result = executor.execute_batch(test_cases)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("执行结果汇总")
    print("=" * 60)
    print(f"总用例数: {batch_result.total_cases}")
    print(f"✓ 通过: {batch_result.passed_cases} ({batch_result.success_rate:.1f}%)")
    print(f"✗ 失败: {batch_result.failed_cases}")
    print(f"⚠ 错误: {batch_result.error_cases}")
    print(f"⏱ 总耗时: {batch_result.duration_ms}ms")
    
    # 详细结果
    print("\n测试用例详情:")
    for result in batch_result.results:
        status_icon = "✓" if result.status == 'passed' else "✗"
        print(f"  {status_icon} {result.test_case_name} - {result.status}")
        print(f"     {result.request_method} {result.request_url}")
        print(f"     响应: {result.response_status} | 耗时: {result.response_time_ms}ms")
        
        if result.status != 'passed':
            print(f"     错误: {result.error_message}")
        print()
    
    # 生成报告
    from api.executor.reporter import TestReporter
    reporter = TestReporter('./reports')
    
    html_report = reporter.generate_html_report(batch_result)
    print(f"✅ HTML报告已生成: {html_report}")
    
    junit_report = reporter.generate_junit_xml(batch_result)
    print(f"✅ JUnit XML报告已生成: {junit_report}")
    
    json_report = reporter.generate_json_report(batch_result)
    print(f"✅ JSON报告已生成: {json_report}")
    
    executor.close()


if __name__ == '__main__':
    example_standalone_yaml_execution()

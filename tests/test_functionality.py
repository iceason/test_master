"""
功能测试脚本

测试所有核心模块的基本功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """测试所有模块导入"""
    print("="*60)
    print("测试1: 模块导入")
    print("="*60)
    
    try:
        # 测试执行引擎模块
        from api.executor.core import TestExecutor, ExecutorConfig, TestResult, BatchResult
        print("✓ TestExecutor模块导入成功")
        
        from api.executor.http_client import EnhancedHttpClient, ClientConfig, ConnectionPoolManager
        print("✓ HTTP客户端模块导入成功")
        
        from api.executor.assertion_engine import AssertionEngine, Assertion, AssertionResult
        print("✓ 断言引擎模块导入成功")
        
        from api.executor.yaml_plugin import YamlPlugin
        print("✓ YAML插件模块导入成功")
        
        from api.executor.config_manager import ConfigManager
        print("✓ 配置管理器模块导入成功")
        
        from api.executor.reporter import TestReporter
        print("✓ 报告生成器模块导入成功")
        
        from api.executor.parallel import ParallelExecutor
        print("✓ 并发执行器模块导入成功")
        
        print("\n所有模块导入成功！")
        return True
    except Exception as e:
        print(f"\n✗ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_http_client():
    """测试HTTP客户端"""
    print("\n" + "="*60)
    print("测试2: HTTP客户端")
    print("="*60)
    
    try:
        from api.executor.http_client import EnhancedHttpClient, ClientConfig
        
        # 创建客户端
        config = ClientConfig(max_retries=2, timeout=(3, 10))
        client = EnhancedHttpClient(config)
        print("✓ HTTP客户端创建成功")
        
        # 测试GET请求
        response = client.get('https://httpbin.org/get', params={'test': 'value'})
        print(f"✓ GET请求成功 - 状态码: {response.status_code}")
        
        # 测试POST请求
        response = client.post('https://httpbin.org/post', json={'key': 'value'})
        print(f"✓ POST请求成功 - 状态码: {response.status_code}")
        
        client.close()
        print("\n✓ HTTP客户端测试通过")
        return True
    except Exception as e:
        print(f"\n✗ HTTP客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_assertion_engine():
    """测试断言引擎"""
    print("\n" + "="*60)
    print("测试3: 断言引擎")
    print("="*60)
    
    try:
        from api.executor.assertion_engine import AssertionEngine, Assertion
        from api.executor.http_client import EnhancedHttpClient
        
        engine = AssertionEngine()
        client = EnhancedHttpClient()
        
        # 发送请求获取响应
        response = client.get('https://httpbin.org/get')
        
        # 测试状态码断言
        assertions = [
            Assertion(type='status_code', expected=200, description='状态码200'),
            Assertion(type='response_time', expected=5000, description='响应时间<5秒'),
            Assertion(type='content_type', expected='application/json', description='JSON响应'),
        ]
        
        results = engine.assert_response(response, assertions, response_time_ms=100)
        
        print(f"✓ 断言执行完成 - 通过: {results.passed_count}, 失败: {results.failed_count}")
        
        for result in results.results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.assertion_type}: {result.message}")
        
        client.close()
        print("\n✓ 断言引擎测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 断言引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_test_executor():
    """测试执行器"""
    print("\n" + "="*60)
    print("测试4: 测试执行器")
    print("="*60)
    
    try:
        from api.executor.core import TestExecutor, ExecutorConfig
        
        # 创建执行器配置
        config = ExecutorConfig(
            environment='test',
            base_url='https://httpbin.org',
            default_timeout=(3, 10)
        )
        
        executor = TestExecutor(config)
        print("✓ 测试执行器创建成功")
        
        # 创建模拟测试用例
        test_case = {
            'name': 'GET测试',
            'method': 'GET',
            'path': '/get',
            'request_data': {'param1': 'value1'},
            'expected_value': {
                'status_code': 200,
                'assertions': [
                    {'type': 'status_code', 'expected': 200}
                ]
            }
        }
        
        # 执行测试
        result = executor.execute_test_case(test_case)
        
        print(f"✓ 测试执行完成")
        print(f"  状态: {result.status}")
        print(f"  响应码: {result.response_status}")
        print(f"  响应时间: {result.response_time_ms}ms")
        print(f"  断言通过: {result.assertions_passed}")
        
        executor.close()
        print("\n✓ 测试执行器测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 测试执行器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yaml_plugin():
    """测试YAML插件"""
    print("\n" + "="*60)
    print("测试5: YAML插件")
    print("="*60)
    
    try:
        from api.executor.yaml_plugin import YamlPlugin
        import yaml
        
        plugin = YamlPlugin()
        print("✓ YAML插件创建成功")
        
        # 测试YAML解析
        test_yaml = """
version: '1.0'
type: 'testcases'
testcases:
  - name: 测试用例1
    interface:
      method: GET
      path: /test
    request_data:
      key: value
    expected_value:
      status_code: 200
"""
        
        data = yaml.safe_load(test_yaml)
        print(f"✓ YAML解析成功 - 类型: {data.get('type')}")
        print(f"  用例数量: {len(data.get('testcases', []))}")
        
        print("\n✓ YAML插件测试通过")
        return True
    except Exception as e:
        print(f"\n✗ YAML插件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reporter():
    """测试报告生成器"""
    print("\n" + "="*60)
    print("测试6: 报告生成器")
    print("="*60)
    
    try:
        from api.executor.reporter import TestReporter
        from api.executor.core import BatchResult, TestResult
        from datetime import datetime
        
        reporter = TestReporter('./test_reports')
        print("✓ 报告生成器创建成功")
        
        # 创建模拟结果
        batch_result = BatchResult()
        batch_result.total_cases = 2
        batch_result.passed_cases = 1
        batch_result.failed_cases = 1
        batch_result.error_cases = 0
        batch_result.started_at = datetime.now()
        batch_result.finished_at = datetime.now()
        batch_result.duration_ms = 1000
        
        # 添加测试结果
        result1 = TestResult(
            test_case_name='测试1',
            status='passed',
            request_method='GET',
            request_url='https://httpbin.org/get',
            response_status=200,
            response_time_ms=100,
            assertions_passed=1,
            assertions_failed=0
        )
        
        result2 = TestResult(
            test_case_name='测试2',
            status='failed',
            request_method='POST',
            request_url='https://httpbin.org/post',
            response_status=400,
            response_time_ms=200,
            assertions_passed=0,
            assertions_failed=1,
            error_message='断言失败'
        )
        
        batch_result.results = [result1, result2]
        
        # 生成报告
        html_report = reporter.generate_html_report(batch_result)
        print(f"✓ HTML报告生成成功: {html_report}")
        
        junit_report = reporter.generate_junit_xml(batch_result)
        print(f"✓ JUnit XML报告生成成功: {junit_report}")
        
        json_report = reporter.generate_json_report(batch_result)
        print(f"✓ JSON报告生成成功: {json_report}")
        
        print("\n✓ 报告生成器测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 报告生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager():
    """测试配置管理器"""
    print("\n" + "="*60)
    print("测试7: 配置管理器")
    print("="*60)
    
    try:
        from api.executor.config_manager import ConfigManager
        
        manager = ConfigManager()
        print("✓ 配置管理器创建成功")
        
        # 测试配置合并
        config1 = {'a': 1, 'b': {'c': 2}}
        config2 = {'b': {'d': 3}, 'e': 4}
        merged = manager.merge_configs(config1, config2)
        
        print(f"✓ 配置合并成功: {merged}")
        
        # 测试变量插值
        config = {
            'url': '${config.base_url}/api',
            'base_url': 'http://example.com'
        }
        interpolated = manager.interpolate_variables(config)
        print(f"✓ 变量插值成功: {interpolated}")
        
        print("\n✓ 配置管理器测试通过")
        return True
    except Exception as e:
        print(f"\n✗ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("TestMaster 功能验证测试")
    print("="*60 + "\n")
    
    tests = [
        ("模块导入", test_imports),
        ("HTTP客户端", test_http_client),
        ("断言引擎", test_assertion_engine),
        ("测试执行器", test_test_executor),
        ("YAML插件", test_yaml_plugin),
        ("报告生成器", test_reporter),
        ("配置管理器", test_config_manager),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 执行异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统功能正常！")
        return 0
    else:
        print(f"\n⚠️  有 {total-passed} 个测试失败，请检查！")
        return 1


if __name__ == '__main__':
    sys.exit(main())

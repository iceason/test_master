"""
测试报告生成器

支持多种格式：HTML、JUnit XML、JSON
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

logger = logging.getLogger(__name__)


class TestReporter:
    """统一报告生成器"""
    
    def __init__(self, report_dir: str = './reports'):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, batch_result: Any) -> str:
        """
        生成HTML报告
        
        Args:
            batch_result: BatchResult对象
            
        Returns:
            HTML文件路径
        """
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {batch_result.batch_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric {{
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .metric.total {{
            background-color: #2196F3;
            color: white;
        }}
        .metric.passed {{
            background-color: #4CAF50;
            color: white;
        }}
        .metric.failed {{
            background-color: #f44336;
            color: white;
        }}
        .metric.error {{
            background-color: #FF9800;
            color: white;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .test-case {{
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 6px;
            overflow: hidden;
        }}
        .test-case-header {{
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-case-header.passed {{
            background-color: #e8f5e9;
        }}
        .test-case-header.failed {{
            background-color: #ffebee;
        }}
        .test-case-header.error {{
            background-color: #fff3e0;
        }}
        .test-case-body {{
            padding: 20px;
            background-color: #f9f9f9;
            display: none;
        }}
        .test-case-body.show {{
            display: block;
        }}
        .status-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-badge.passed {{
            background-color: #4CAF50;
            color: white;
        }}
        .status-badge.failed {{
            background-color: #f44336;
            color: white;
        }}
        .status-badge.error {{
            background-color: #FF9800;
            color: white;
        }}
        .detail-section {{
            margin: 15px 0;
        }}
        .detail-section h4 {{
            margin: 10px 0;
            color: #555;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 13px;
        }}
        .assertion {{
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #ddd;
            background-color: #fafafa;
        }}
        .assertion.passed {{
            border-left-color: #4CAF50;
        }}
        .assertion.failed {{
            border-left-color: #f44336;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 测试执行报告</h1>
        
        <div class="summary">
            <div class="metric total">
                <div class="metric-label">总用例数</div>
                <div class="metric-value">{batch_result.total_cases}</div>
            </div>
            <div class="metric passed">
                <div class="metric-label">通过</div>
                <div class="metric-value">{batch_result.passed_cases}</div>
            </div>
            <div class="metric failed">
                <div class="metric-label">失败</div>
                <div class="metric-value">{batch_result.failed_cases}</div>
            </div>
            <div class="metric error">
                <div class="metric-label">错误</div>
                <div class="metric-value">{batch_result.error_cases}</div>
            </div>
        </div>
        
        <div style="margin: 20px 0; padding: 15px; background-color: #f0f0f0; border-radius: 6px;">
            <strong>成功率:</strong> {batch_result.success_rate:.1f}% &nbsp;&nbsp;
            <strong>总耗时:</strong> {batch_result.duration_ms}ms &nbsp;&nbsp;
            <strong>开始时间:</strong> {batch_result.started_at} &nbsp;&nbsp;
            <strong>结束时间:</strong> {batch_result.finished_at}
        </div>
        
        <h2>测试用例详情</h2>
"""
        
        for result in batch_result.results:
            html_content += self._generate_test_case_html(result)
        
        html_content += """
    </div>
    <script>
        document.querySelectorAll('.test-case-header').forEach(header => {
            header.addEventListener('click', () => {
                const body = header.nextElementSibling;
                body.classList.toggle('show');
            });
        });
    </script>
</body>
</html>
"""
        
        # 保存HTML文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'test_report_{timestamp}.html'
        filepath = self.report_dir / filename
        filepath.write_text(html_content, encoding='utf-8')
        
        logger.info(f"HTML报告已生成: {filepath}")
        return str(filepath)
    
    def _generate_test_case_html(self, result: Any) -> str:
        """生成单个测试用例的HTML"""
        assertions_html = ""
        for assertion in result.assertion_details:
            status_class = 'passed' if assertion.get('passed') else 'failed'
            assertions_html += f"""
                <div class="assertion {status_class}">
                    <strong>{assertion.get('assertion_type')}</strong>: 
                    {assertion.get('message')}
                </div>
            """
        
        return f"""
        <div class="test-case">
            <div class="test-case-header {result.status}">
                <div>
                    <strong>{result.test_case_name}</strong>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        {result.request_method} {result.request_url}
                    </div>
                </div>
                <span class="status-badge {result.status}">{result.status.upper()}</span>
            </div>
            <div class="test-case-body">
                <div class="detail-section">
                    <h4>📤 请求信息</h4>
                    <p><strong>方法:</strong> {result.request_method}</p>
                    <p><strong>URL:</strong> {result.request_url}</p>
                    <p><strong>请求体:</strong></p>
                    <pre>{json.dumps(result.request_body, ensure_ascii=False, indent=2)}</pre>
                </div>
                
                <div class="detail-section">
                    <h4>📥 响应信息</h4>
                    <p><strong>状态码:</strong> {result.response_status}</p>
                    <p><strong>响应时间:</strong> {result.response_time_ms}ms</p>
                    <p><strong>响应体:</strong></p>
                    <pre>{json.dumps(result.response_body, ensure_ascii=False, indent=2) if result.response_body else 'N/A'}</pre>
                </div>
                
                <div class="detail-section">
                    <h4>✓ 断言结果</h4>
                    <p><strong>通过:</strong> {result.assertions_passed} &nbsp;&nbsp; <strong>失败:</strong> {result.assertions_failed}</p>
                    {assertions_html}
                </div>
                
                {f'<div class="detail-section"><h4>❌ 错误信息</h4><pre>{result.error_message}</pre></div>' if result.error_message else ''}
            </div>
        </div>
"""
    
    def generate_junit_xml(self, batch_result: Any) -> str:
        """
        生成JUnit XML格式报告（Jenkins/GitLab CI集成）
        
        Args:
            batch_result: BatchResult对象
            
        Returns:
            XML文件路径
        """
        testsuites = Element('testsuites')
        testsuite = SubElement(testsuites, 'testsuite', {
            'name': f'Batch-{batch_result.batch_id}',
            'tests': str(batch_result.total_cases),
            'failures': str(batch_result.failed_cases),
            'errors': str(batch_result.error_cases),
            'time': str(batch_result.duration_ms / 1000),
            'timestamp': str(batch_result.started_at)
        })
        
        for result in batch_result.results:
            testcase = SubElement(testsuite, 'testcase', {
                'name': result.test_case_name,
                'classname': f"{result.request_method}.{result.request_url.replace('/', '.')}",
                'time': str((result.duration_ms or 0) / 1000)
            })
            
            if result.status == 'failed':
                failure = SubElement(testcase, 'failure', {
                    'message': result.error_message or 'Test failed',
                    'type': 'AssertionError'
                })
                failure.text = result.error_message or str(result.assertion_details)
            
            elif result.status == 'error':
                error = SubElement(testcase, 'error', {
                    'message': result.error_message or 'Test error',
                    'type': 'Exception'
                })
                error.text = result.error_traceback or result.error_message
        
        # 格式化XML
        xml_str = minidom.parseString(tostring(testsuites)).toprettyxml(indent="  ")
        
        # 保存XML文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'junit_report_{timestamp}.xml'
        filepath = self.report_dir / filename
        filepath.write_text(xml_str, encoding='utf-8')
        
        logger.info(f"JUnit XML报告已生成: {filepath}")
        return str(filepath)
    
    def generate_json_report(self, batch_result: Any) -> str:
        """
        生成JSON格式报告
        
        Args:
            batch_result: BatchResult对象
            
        Returns:
            JSON文件路径
        """
        report_data = batch_result.to_dict()
        
        # 保存JSON文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'test_report_{timestamp}.json'
        filepath = self.report_dir / filename
        filepath.write_text(
            json.dumps(report_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        logger.info(f"JSON报告已生成: {filepath}")
        return str(filepath)
    
    def generate_markdown_summary(self, batch_result: Any) -> str:
        """
        生成Markdown摘要（用于PR评论）
        
        Args:
            batch_result: BatchResult对象
            
        Returns:
            Markdown内容
        """
        status_icon = "✅" if batch_result.success_rate == 100 else "❌"
        
        markdown = f"""
## {status_icon} 测试执行报告

### 📊 总体统计

| 指标 | 数值 |
|------|------|
| 总用例数 | {batch_result.total_cases} |
| ✅ 通过 | {batch_result.passed_cases} |
| ❌ 失败 | {batch_result.failed_cases} |
| ⚠️ 错误 | {batch_result.error_cases} |
| 📈 成功率 | {batch_result.success_rate:.1f}% |
| ⏱️ 总耗时 | {batch_result.duration_ms}ms |

### 📝 失败用例

"""
        
        failed_cases = [r for r in batch_result.results if r.status in ['failed', 'error']]
        if failed_cases:
            for result in failed_cases:
                markdown += f"""
- **{result.test_case_name}** ({result.status.upper()})
  - URL: `{result.request_method} {result.request_url}`
  - 错误: {result.error_message or '断言失败'}

"""
        else:
            markdown += "\n✅ 所有测试用例均通过！\n"
        
        return markdown

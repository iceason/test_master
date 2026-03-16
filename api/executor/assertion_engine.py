"""
多层次断言引擎

支持多种断言类型：
- 基础断言（状态码、响应时间、内容类型）
- JSONPath断言
- JSONSchema验证
- 正则表达式匹配
- 自定义脚本断言
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import jsonpath_ng
    from jsonpath_ng import parse as jsonpath_parse
    JSONPATH_AVAILABLE = True
except ImportError:
    JSONPATH_AVAILABLE = False
    
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class AssertionType(Enum):
    """断言类型"""
    STATUS_CODE = 'status_code'
    RESPONSE_TIME = 'response_time'
    CONTENT_TYPE = 'content_type'
    HEADER = 'header'
    JSONPATH = 'jsonpath'
    JSONSCHEMA = 'jsonschema'
    REGEX = 'regex'
    CONTAINS = 'contains'
    NOT_CONTAINS = 'not_contains'
    EQUALS = 'equals'
    NOT_EQUALS = 'not_equals'
    SCRIPT = 'script'


@dataclass
class Assertion:
    """断言配置"""
    type: str  # AssertionType
    expected: Any
    actual_path: Optional[str] = None  # JSONPath或字段路径
    description: Optional[str] = None
    
    def __post_init__(self):
        # 转换为枚举
        if isinstance(self.type, str):
            try:
                self.type = AssertionType(self.type)
            except ValueError:
                logger.warning(f"未知的断言类型: {self.type}")


@dataclass
class AssertionResult:
    """单个断言结果"""
    passed: bool
    assertion_type: str
    expected: Any
    actual: Any
    message: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'assertion_type': self.assertion_type,
            'expected': self.expected,
            'actual': self.actual,
            'message': self.message,
            'description': self.description
        }


@dataclass
class AssertionResults:
    """断言结果集合"""
    results: List[AssertionResult] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """所有断言是否通过"""
        return all(r.passed for r in self.results)
    
    @property
    def passed_count(self) -> int:
        """通过的断言数量"""
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed_count(self) -> int:
        """失败的断言数量"""
        return sum(1 for r in self.results if not r.passed)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'total': len(self.results),
            'passed_count': self.passed_count,
            'failed_count': self.failed_count,
            'details': [r.to_dict() for r in self.results]
        }


class AssertionEngine:
    """
    多层次断言系统
    
    支持:
    - 基础断言（状态码、响应时间、内容类型）
    - JSONPath断言（$.data.user.name）
    - JSONSchema验证（结构校验）
    - 正则表达式匹配
    - 自定义断言脚本
    """
    
    def __init__(self):
        self.results = AssertionResults()
    
    def assert_response(
        self,
        response: Any,  # requests.Response
        assertions: List[Union[Assertion, Dict]],
        response_time_ms: Optional[int] = None
    ) -> AssertionResults:
        """
        执行所有断言
        
        Args:
            response: requests.Response对象
            assertions: 断言列表
            response_time_ms: 响应时间（毫秒）
            
        Returns:
            AssertionResults
        """
        results = AssertionResults()
        
        # 转换字典为Assertion对象
        assertion_objects = []
        for assertion in assertions:
            if isinstance(assertion, dict):
                assertion_objects.append(Assertion(**assertion))
            else:
                assertion_objects.append(assertion)
        
        for assertion in assertion_objects:
            try:
                if assertion.type == AssertionType.STATUS_CODE:
                    result = self._assert_status_code(response, assertion)
                elif assertion.type == AssertionType.RESPONSE_TIME:
                    result = self._assert_response_time(response_time_ms, assertion)
                elif assertion.type == AssertionType.CONTENT_TYPE:
                    result = self._assert_content_type(response, assertion)
                elif assertion.type == AssertionType.HEADER:
                    result = self._assert_header(response, assertion)
                elif assertion.type == AssertionType.JSONPATH:
                    result = self._assert_jsonpath(response, assertion)
                elif assertion.type == AssertionType.JSONSCHEMA:
                    result = self._assert_jsonschema(response, assertion)
                elif assertion.type == AssertionType.REGEX:
                    result = self._assert_regex(response, assertion)
                elif assertion.type == AssertionType.CONTAINS:
                    result = self._assert_contains(response, assertion)
                elif assertion.type == AssertionType.NOT_CONTAINS:
                    result = self._assert_not_contains(response, assertion)
                elif assertion.type == AssertionType.EQUALS:
                    result = self._assert_equals(response, assertion)
                elif assertion.type == AssertionType.NOT_EQUALS:
                    result = self._assert_not_equals(response, assertion)
                else:
                    result = AssertionResult(
                        passed=False,
                        assertion_type=str(assertion.type),
                        expected=assertion.expected,
                        actual=None,
                        message=f"不支持的断言类型: {assertion.type}",
                        description=assertion.description
                    )
                
                results.results.append(result)
                
            except Exception as e:
                logger.error(f"断言执行异常: {e}", exc_info=True)
                results.results.append(AssertionResult(
                    passed=False,
                    assertion_type=str(assertion.type),
                    expected=assertion.expected,
                    actual=None,
                    message=f"断言执行异常: {str(e)}",
                    description=assertion.description
                ))
        
        return results
    
    def _assert_status_code(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言HTTP状态码"""
        actual = response.status_code
        expected = assertion.expected
        passed = actual == expected
        
        return AssertionResult(
            passed=passed,
            assertion_type='status_code',
            expected=expected,
            actual=actual,
            message=f"状态码 {actual} {'==' if passed else '!='} {expected}",
            description=assertion.description
        )
    
    def _assert_response_time(self, response_time_ms: Optional[int], assertion: Assertion) -> AssertionResult:
        """断言响应时间"""
        if response_time_ms is None:
            return AssertionResult(
                passed=False,
                assertion_type='response_time',
                expected=assertion.expected,
                actual=None,
                message="响应时间未提供",
                description=assertion.description
            )
        
        expected_max = assertion.expected
        passed = response_time_ms <= expected_max
        
        return AssertionResult(
            passed=passed,
            assertion_type='response_time',
            expected=f"<= {expected_max}ms",
            actual=f"{response_time_ms}ms",
            message=f"响应时间 {response_time_ms}ms {'<=' if passed else '>'} {expected_max}ms",
            description=assertion.description
        )
    
    def _assert_content_type(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言Content-Type"""
        actual = response.headers.get('Content-Type', '')
        expected = assertion.expected
        passed = expected in actual
        
        return AssertionResult(
            passed=passed,
            assertion_type='content_type',
            expected=expected,
            actual=actual,
            message=f"Content-Type '{actual}' {'包含' if passed else '不包含'} '{expected}'",
            description=assertion.description
        )
    
    def _assert_header(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言HTTP头"""
        header_name = assertion.actual_path
        actual = response.headers.get(header_name, None)
        expected = assertion.expected
        passed = actual == expected
        
        return AssertionResult(
            passed=passed,
            assertion_type='header',
            expected=expected,
            actual=actual,
            message=f"Header '{header_name}': {actual} {'==' if passed else '!='} {expected}",
            description=assertion.description
        )
    
    def _assert_jsonpath(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言JSONPath"""
        if not JSONPATH_AVAILABLE:
            return AssertionResult(
                passed=False,
                assertion_type='jsonpath',
                expected=assertion.expected,
                actual=None,
                message="jsonpath_ng库未安装",
                description=assertion.description
            )
        
        try:
            response_json = response.json()
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion_type='jsonpath',
                expected=assertion.expected,
                actual=None,
                message=f"响应不是有效的JSON: {e}",
                description=assertion.description
            )
        
        try:
            jsonpath_expr = jsonpath_parse(assertion.actual_path)
            matches = jsonpath_expr.find(response_json)
            
            if not matches:
                return AssertionResult(
                    passed=False,
                    assertion_type='jsonpath',
                    expected=assertion.expected,
                    actual=None,
                    message=f"JSONPath '{assertion.actual_path}' 未找到匹配",
                    description=assertion.description
                )
            
            actual = matches[0].value
            expected = assertion.expected
            passed = actual == expected
            
            return AssertionResult(
                passed=passed,
                assertion_type='jsonpath',
                expected=expected,
                actual=actual,
                message=f"JSONPath '{assertion.actual_path}': {actual} {'==' if passed else '!='} {expected}",
                description=assertion.description
            )
            
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion_type='jsonpath',
                expected=assertion.expected,
                actual=None,
                message=f"JSONPath解析错误: {e}",
                description=assertion.description
            )
    
    def _assert_jsonschema(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言JSONSchema"""
        if not JSONSCHEMA_AVAILABLE:
            return AssertionResult(
                passed=False,
                assertion_type='jsonschema',
                expected=assertion.expected,
                actual=None,
                message="jsonschema库未安装",
                description=assertion.description
            )
        
        try:
            response_json = response.json()
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion_type='jsonschema',
                expected=assertion.expected,
                actual=None,
                message=f"响应不是有效的JSON: {e}",
                description=assertion.description
            )
        
        try:
            schema = assertion.expected
            jsonschema.validate(instance=response_json, schema=schema)
            
            return AssertionResult(
                passed=True,
                assertion_type='jsonschema',
                expected="符合Schema",
                actual="符合Schema",
                message="响应符合JSONSchema定义",
                description=assertion.description
            )
            
        except jsonschema.ValidationError as e:
            return AssertionResult(
                passed=False,
                assertion_type='jsonschema',
                expected="符合Schema",
                actual=e.message,
                message=f"Schema验证失败: {e.message}",
                description=assertion.description
            )
    
    def _assert_regex(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言正则表达式"""
        try:
            actual = response.text
        except:
            actual = str(response.content)
        
        pattern = assertion.expected
        try:
            passed = bool(re.search(pattern, actual))
            
            return AssertionResult(
                passed=passed,
                assertion_type='regex',
                expected=f"匹配模式: {pattern}",
                actual="匹配" if passed else "不匹配",
                message=f"正则表达式 '{pattern}' {'匹配' if passed else '不匹配'}",
                description=assertion.description
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion_type='regex',
                expected=pattern,
                actual=None,
                message=f"正则表达式错误: {e}",
                description=assertion.description
            )
    
    def _assert_contains(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言包含"""
        try:
            actual = response.text
        except:
            actual = str(response.content)
        
        expected = str(assertion.expected)
        passed = expected in actual
        
        return AssertionResult(
            passed=passed,
            assertion_type='contains',
            expected=expected,
            actual="包含" if passed else "不包含",
            message=f"响应 {'包含' if passed else '不包含'} '{expected}'",
            description=assertion.description
        )
    
    def _assert_not_contains(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言不包含"""
        try:
            actual = response.text
        except:
            actual = str(response.content)
        
        expected = str(assertion.expected)
        passed = expected not in actual
        
        return AssertionResult(
            passed=passed,
            assertion_type='not_contains',
            expected=f"不包含 {expected}",
            actual="不包含" if passed else "包含",
            message=f"响应 {'不包含' if passed else '包含'} '{expected}'",
            description=assertion.description
        )
    
    def _assert_equals(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言等于"""
        try:
            response_json = response.json()
            if assertion.actual_path:
                # 简单的点符号路径解析
                actual = self._get_nested_value(response_json, assertion.actual_path)
            else:
                actual = response_json
        except:
            actual = response.text
        
        expected = assertion.expected
        passed = actual == expected
        
        return AssertionResult(
            passed=passed,
            assertion_type='equals',
            expected=expected,
            actual=actual,
            message=f"{actual} {'==' if passed else '!='} {expected}",
            description=assertion.description
        )
    
    def _assert_not_equals(self, response: Any, assertion: Assertion) -> AssertionResult:
        """断言不等于"""
        try:
            response_json = response.json()
            if assertion.actual_path:
                actual = self._get_nested_value(response_json, assertion.actual_path)
            else:
                actual = response_json
        except:
            actual = response.text
        
        expected = assertion.expected
        passed = actual != expected
        
        return AssertionResult(
            passed=passed,
            assertion_type='not_equals',
            expected=f"!= {expected}",
            actual=actual,
            message=f"{actual} {'!=' if passed else '=='} {expected}",
            description=assertion.description
        )
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """获取嵌套字段值（简单版本）"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

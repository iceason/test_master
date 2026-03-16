import re
import random
import string
import json
import logging
import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from typing import List, Dict, Any, Tuple, Optional, Set
from faker import Faker
from hypothesis import strategies as st
from hypothesis.errors import InvalidArgument

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化Faker，支持多语言
fake = Faker(["zh_CN", "en_US"])


class SchemaValidator:
    """Schema验证器，支持OpenAPI 3.0和自定义Schema"""

    def __init__(self, schema_type: str = "openapi"):
        self.schema_type = schema_type
        self.required_fields = {"type"}  # 核心必填字段

    def validate(self, schema: Dict[str, Any]) -> bool:
        """验证Schema基本合法性"""
        if not isinstance(schema, dict):
            logger.error("Schema must be a dictionary")
            return False

        # 适配OpenAPI Schema结构
        if self.schema_type == "openapi":
            schema = schema.get("properties", schema)

        for field, config in schema.items():
            if not isinstance(config, dict):
                logger.error(f"Field '{field}' config must be a dictionary")
                return False

            # 检查核心字段
            if "type" not in config:
                logger.warning(f"Field '{field}' missing 'type' field, default to 'string'")
                config["type"] = "string"

            # 验证枚举类型
            if "enum" in config and not isinstance(config["enum"], list):
                logger.error(f"Field '{field}' enum must be a list")
                return False

            # 验证正则表达式
            if "regex" in config or "pattern" in config:
                regex = config.get("regex") or config.get("pattern")
                try:
                    re.compile(regex)
                except re.error as e:
                    logger.error(f"Field '{field}' invalid regex: {e}")
                    return False

        return True


class BaseGenerator:
    """增强版基础生成器，提供通用工具方法"""

    def __init__(self):
        self.supported_types = {"string", "integer", "number", "boolean", "object", "array", "null"}
        self.format_handlers = {
            "email": fake.email,
            "uuid": fake.uuid4,
            "ipv4": fake.ipv4,
            "ipv6": fake.ipv6,
            "url": fake.url,
            "phone": fake.phone_number,
            "date": fake.date,
            "datetime": fake.date_time,
            "password": lambda: fake.password(length=12, special_chars=True, digits=True, upper_case=True,
                                              lower_case=True),
            "username": fake.user_name,
            "name": fake.name,
            "address": fake.address
        }

    def _make_case(self, api_name: str, field: str, input_val: Any,
                   pos_neg: str, expected: str, reason: str) -> dict:
        """构造标准化测试用例（兼容JSON序列化）"""

        # 处理特殊值的序列化
        def serialize_val(val):
            if isinstance(val, (dict, list, int, float, bool, str, type(None))):
                return val
            return str(val)

        case_id = f"{api_name}_{field.upper().replace('.', '_').replace('[*]', '_ITEM')}_{pos_neg.upper()}_{expected.upper()}_{random.randint(1000, 9999)}"

        return {
            "test_case_id": case_id,
            "target_field": field,
            "input_value": serialize_val(input_val),
            "test_type": pos_neg.lower(),
            "expected_outcome": expected.lower(),
            "test_rationale": reason,
            "created_at": fake.iso8601()  # 增加时间戳，便于追溯
        }

    def _safe_get(self, config: dict, key: str, default=None, type_cast=None) -> Any:
        """安全获取配置值，支持类型转换"""
        val = config.get(key, default)
        if type_cast and val is not None:
            try:
                return type_cast(val)
            except (ValueError, TypeError):
                logger.warning(f"Failed to cast {key}={val} to {type_cast}, use default {default}")
                return default
        return val

    def _generate_compliant_string(self, length: int, regex: str = None) -> str:
        """增强版合规字符串生成，支持更复杂的正则"""
        if length <= 0:
            return ""

        if not regex:
            return "".join(random.choices(string.ascii_letters + string.digits, k=length))

        # 1. 尝试使用hypothesis生成精确长度的字符串
        try:
            # 尝试过滤出指定长度的字符串
            # 注意：如果概率太低可能会抛出 Unsatisfiable，所以捕获异常
            return st.from_regex(regex, fullmatch=True).filter(lambda x: len(x) == length).example()
        except Exception:
            pass

        # 2. 如果精确生成失败，生成任意匹配串并调整长度
        try:
            base_str = st.from_regex(regex, fullmatch=True).example()
            if len(base_str) >= length:
                return base_str[:length]
            else:
                # 补全逻辑：重复最后一个字符
                if base_str:
                    padded = base_str + base_str[-1] * (length - len(base_str))
                    # 这里我们优先保证长度符合要求（用于边界测试）
                    return padded
        except (InvalidArgument, Exception) as e:
            logger.debug(f"Hypothesis regex generation failed: {e}, use fallback logic")

        # 3. 启发式生成（增强版）作为最后兜底
        use_upper = bool(re.search(r'A-Z', regex))
        use_lower = bool(re.search(r'a-z', regex))
        use_digit = bool(re.search(r'\d|0-9', regex))
        use_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?\/\\|`~]', regex))

        pool = ""
        if use_upper:
            pool += string.ascii_uppercase
        if use_lower:
            pool += string.ascii_lowercase
        if use_digit:
            pool += string.digits
        if use_special:
            pool += "!@#$%^&*()_+-="

        # 兜底字符池
        if not pool:
            pool = string.ascii_letters + string.digits

        # 生成并洗牌
        result = [random.choice(pool) for _ in range(length)]
        random.shuffle(result)

        # 确保首字符符合正则要求
        if regex.startswith('^[a-zA-Z]') and not result[0].isalpha():
            for i, c in enumerate(result):
                if c.isalpha():
                    result[0], result[i] = result[i], result[0]
                    break

        return "".join(result)


    def _generate_semantic_value(self, field_name: str, config: dict) -> Any:
        """生成语义化真实值（基于format/字段名）"""
        field_format = self._safe_get(config, "format", "")
        lower_name = field_name.lower()

        # 优先使用format匹配
        if field_format in self.format_handlers:
            return self.format_handlers[field_format]()

        # 字段名启发式匹配
        for keyword, handler in self.format_handlers.items():
            if keyword in lower_name:
                return handler()

        # 兜底使用基础合法值
        return self._generate_valid_value(field_name, config)

    def _generate_valid_value(self, field_name: str, config: dict) -> Any:
        """生成基础合法值（支持所有类型）"""
        field_type = self._safe_get(config, "type", "string")
        enum_vals = self._safe_get(config, "enum", [])

        if enum_vals:
            return random.choice(enum_vals)

        if field_type == "string":
            regex = config.get("regex") or config.get("pattern")
            return self._generate_compliant_string(10, regex)
        elif field_type == "integer":
            min_val = self._safe_get(config, "minimum", 0, int)
            max_val = self._safe_get(config, "maximum", 100, int)
            return random.randint(min_val, max_val)
        elif field_type == "number":
            min_val = self._safe_get(config, "minimum", 0.0, float)
            max_val = self._safe_get(config, "maximum", 100.0, float)
            return random.uniform(min_val, max_val)
        elif field_type == "boolean":
            return random.choice([True, False])
        elif field_type == "object":
            # 生成空对象或简单对象
            return {} if not config.get("properties") else {k: self._generate_valid_value(f"{field_name}.{k}", v) for
                                                            k, v in config["properties"].items() if
                                                            k in list(config["properties"].keys())[:2]}
        elif field_type == "array":
            # 生成简单数组
            item_config = self._safe_get(config, "items", {})
            return [self._generate_valid_value(f"{field_name}[0]", item_config)]
        elif field_type == "null":
            return None
        return "valid_value"


class TestCaseGenerator(BaseGenerator):
    """增强版测试用例生成器，支持复杂类型和自定义规则"""

    def __init__(self, disabled_categories: Set[str] = None):
        super().__init__()
        self.disabled_categories = disabled_categories or set()
        self.security_payloads = {
            "SQL Injection": ["' OR '1'='1", "1; DROP TABLE users", "' UNION SELECT * FROM users --", "admin' --"],
            "XSS": ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "javascript:alert(1)",
                    "<svg onload=alert(1)>"],
            "Command Injection": ["; ls -la", "| cat /etc/passwd", "`whoami`", "$(cat /etc/passwd)"],
            "JSON Injection": ['{"$ne": null}', '{"key": "value", "inject": true}'],
            "NoSQL Injection": ['{"$gt": ""}', '{"$where": "1==1"}'],
            "Fuzzing": ["".join([chr(random.randint(0, 255)) for _ in range(10)])]
        }

    def generate_all_cases(self, schema: Dict[str, Any], api_name: str) -> List[dict]:
        """生成所有字段的测试用例（支持嵌套）"""
        all_cases = []
        properties = schema.get("properties", schema)  # 兼容OpenAPI结构

        # 递归处理所有字段（包括嵌套对象/数组）
        def process_field(field_path: str, config: dict):
            # 生成当前字段的用例
            cases = self.generate_cases(field_path, config, api_name)
            all_cases.extend(cases)

            # 处理嵌套对象
            if config.get("type") == "object" and "properties" in config:
                for sub_field, sub_config in config["properties"].items():
                    process_field(f"{field_path}.{sub_field}", sub_config)

            # 处理数组项
            if config.get("type") == "array" and "items" in config:
                item_config = config["items"]
                if item_config.get("type") == "object" and "properties" in item_config:
                    for sub_field, sub_config in item_config["properties"].items():
                        process_field(f"{field_path}[*].{sub_field}", sub_config)
                else:
                    process_field(f"{field_path}[*]", item_config)

        # 遍历根字段
        for field, config in properties.items():
            process_field(field, config)

        return all_cases

    def generate_cases(self, field_name: str, config: dict, api_name: str) -> List[dict]:
        """生成单个字段的测试用例（过滤禁用类别）"""
        cases = []
        field_type = self._safe_get(config, "type", "string")

        # 跳过不支持的类型
        if field_type not in self.supported_types:
            logger.warning(f"Unsupported field type '{field_type}' for {field_name}, skip")
            return cases

        # 按类别生成用例
        category_handlers = {
            "Positive": self._generate_positive_cases,
            "Negative": self._generate_negative_cases,
            "Boundary": self._generate_boundary_cases,
            "Security": self._generate_security_cases
        }

        for category, handler in category_handlers.items():
            if category in self.disabled_categories:
                logger.debug(f"Skip {category} cases for {field_name}")
                continue
            try:
                cases.extend(handler(field_name, config, api_name))
            except Exception as e:
                logger.error(f"Failed to generate {category} cases for {field_name}: {e}")

        return cases

    def _generate_positive_cases(self, field_name: str, config: dict, api_name: str) -> List[dict]:
        """增强版正向用例生成"""
        cases = []
        field_type = self._safe_get(config, "type", "string")

        # 1. 基础合法值
        valid_val = self._generate_valid_value(field_name, config)
        cases.append(self._make_case(
            api_name, field_name, valid_val, "Positive", "Success",
            f"Valid basic value ({field_type})"
        ))

        # 2. 语义化合法值（基于format/字段名）
        semantic_val = self._generate_semantic_value(field_name, config)
        if semantic_val != valid_val:
            cases.append(self._make_case(
                api_name, field_name, semantic_val, "Positive", "Success",
                "Valid semantic/realistic value"
            ))

        # 3. 枚举全覆盖
        enum_vals = self._safe_get(config, "enum", [])
        if enum_vals:
            for val in enum_vals:
                cases.append(self._make_case(
                    api_name, field_name, val, "Positive", "Success",
                    f"Enum value: {val}"
                ))

        # 4. 长度/数值边界内的合法值
        if field_type == "string":
            max_len = self._safe_get(config, "max_length", 100, int)
            min_len = self._safe_get(config, "min_length", 0, int)
            if max_len < 1000 and max_len > min_len:
                # 最大长度合法值
                max_valid = self._generate_compliant_string(max_len, config.get("regex"))
                cases.append(self._make_case(
                    api_name, field_name, max_valid, "Positive", "Success",
                    f"Max length valid string ({max_len} chars)"
                ))
                # 最小长度合法值
                if min_len > 0:
                    min_valid = self._generate_compliant_string(min_len, config.get("regex"))
                    cases.append(self._make_case(
                        api_name, field_name, min_valid, "Positive", "Success",
                        f"Min length valid string ({min_len} chars)"
                    ))

        elif field_type in ["integer", "number"]:
            max_val = self._safe_get(config, "maximum", 1000, int)
            min_val = self._safe_get(config, "minimum", 0, int)
            if max_val > min_val:
                # 中间值
                mid_val = random.randint(min_val + 1, max_val - 1) if field_type == "integer" else random.uniform(
                    min_val + 1, max_val - 1)
                cases.append(self._make_case(
                    api_name, field_name, mid_val, "Positive", "Success",
                    f"Mid value between min({min_val}) and max({max_val})"
                ))

        # 5. 数组类型正向用例
        if field_type == "array":
            item_config = self._safe_get(config, "items", {})
            # 合法长度数组
            min_items = self._safe_get(config, "minItems", 1, int)
            valid_array = [self._generate_valid_value(f"{field_name}[{i}]", item_config) for i in range(min_items)]
            cases.append(self._make_case(
                api_name, field_name, valid_array, "Positive", "Success",
                f"Valid array with {min_items} items"
            ))

        return cases

    def _generate_negative_cases(self, field_name: str, config: dict, api_name: str) -> List[dict]:
        """增强版负向用例生成"""
        cases = []
        field_type = self._safe_get(config, "type", "string")

        # 1. 枚举非法值
        enum_vals = self._safe_get(config, "enum", [])
        if enum_vals:
            invalid_enum = f"{enum_vals[0]}_INVALID_{random.randint(100, 999)}"
            cases.append(self._make_case(
                api_name, field_name, invalid_enum, "Negative", "Failure",
                "Value not in enum list"
            ))

        # 2. 缺失必填字段
        if self._safe_get(config, "required", False, bool):
            cases.append(self._make_case(
                api_name, field_name, None, "Negative", "Failure",
                "Missing required field"
            ))

        # 3. 格式错误（正则不匹配）
        regex = config.get("regex") or config.get("pattern")
        if regex:
            invalid_fmt = self._generate_regex_mismatch(regex)
            cases.append(self._make_case(
                api_name, field_name, invalid_fmt, "Negative", "Failure",
                "Regex pattern mismatch"
            ))

        # 4. 类型错误
        type_errors = self._get_type_error_values(field_type)
        for val in type_errors:
            cases.append(self._make_case(
                api_name, field_name, val, "Negative", "Failure",
                f"Type error (expected {field_type}, got {type(val).__name__})"
            ))

        # 5. 格式特定错误（email/url等）
        field_format = self._safe_get(config, "format", "")
        if field_format == "email":
            invalid_emails = ["user@.com", "user@com", "@domain.com", "user@domain..com"]
            cases.append(self._make_case(
                api_name, field_name, random.choice(invalid_emails), "Negative", "Failure",
                f"Invalid {field_format} format"
            ))
        elif field_format == "url":
            invalid_urls = ["http://", "www.domain.com", "http://.com", "ftp://invalid url"]
            cases.append(self._make_case(
                api_name, field_name, random.choice(invalid_urls), "Negative", "Failure",
                f"Invalid {field_format} format"
            ))

        # 6. 保留字校验
        reserved_words = self._safe_get(config, "reserved_words", [])
        if reserved_words:
            for word in reserved_words[:3]:  # 限制数量，避免用例过多
                cases.append(self._make_case(
                    api_name, field_name, word, "Negative", "Failure",
                    f"Reserved word: {word}"
                ))

        # 7. 数组类型负向用例
        if field_type == "array":
            max_items = self._safe_get(config, "maxItems", 10, int)
            # 超出最大项数
            item_config = self._safe_get(config, "items", {})
            invalid_array = [self._generate_valid_value(f"{field_name}[{i}]", item_config) for i in
                             range(max_items + 1)]
            cases.append(self._make_case(
                api_name, field_name, invalid_array, "Negative", "Failure",
                f"Array items exceed maxItems ({max_items})"
            ))

        return cases

    def _generate_boundary_cases(self, field_name: str, config: dict, api_name: str) -> List[dict]:
        """增强版边界用例生成"""
        cases = []
        field_type = self._safe_get(config, "type", "string")

        # 1. 字符串长度边界
        if field_type == "string":
            max_len = self._safe_get(config, "max_length", 100, int)
            min_len = self._safe_get(config, "min_length", 0, int)

            # 刚好最大长度
            if max_len < 1000:
                max_val = self._generate_compliant_string(max_len, config.get("regex"))
                cases.append(self._make_case(
                    api_name, field_name, max_val, "Boundary", "Success",
                    f"String at max length ({max_len})"
                ))
                # 超出最大长度
                over_max = self._generate_compliant_string(max_len + 1, config.get("regex"))
                cases.append(self._make_case(
                    api_name, field_name, over_max, "Boundary", "Failure",
                    f"String exceeds max length ({max_len + 1} > {max_len})"
                ))

            # 刚好最小长度
            if min_len > 0:
                min_val = self._generate_compliant_string(min_len, config.get("regex"))
                cases.append(self._make_case(
                    api_name, field_name, min_val, "Boundary", "Success",
                    f"String at min length ({min_len})"
                ))
                # 低于最小长度
                under_min = self._generate_compliant_string(min_len - 1, config.get("regex"))
                cases.append(self._make_case(
                    api_name, field_name, under_min, "Boundary", "Failure",
                    f"String below min length ({min_len - 1} < {min_len})"
                ))

        # 2. 数值类型边界
        elif field_type in ["integer", "number"]:
            max_val = self._safe_get(config, "maximum", None, int)
            min_val = self._safe_get(config, "minimum", None, int)

            if max_val is not None:
                # 刚好最大值
                cases.append(self._make_case(
                    api_name, field_name, max_val, "Boundary", "Success",
                    f"Value at maximum ({max_val})"
                ))
                # 超出最大值
                over_max = max_val + 1 if field_type == "integer" else max_val + 0.1
                cases.append(self._make_case(
                    api_name, field_name, over_max, "Boundary", "Failure",
                    f"Value exceeds maximum ({over_max} > {max_val})"
                ))

            if min_val is not None:
                # 刚好最小值
                cases.append(self._make_case(
                    api_name, field_name, min_val, "Boundary", "Success",
                    f"Value at minimum ({min_val})"
                ))
                # 低于最小值
                under_min = min_val - 1 if field_type == "integer" else min_val - 0.1
                cases.append(self._make_case(
                    api_name, field_name, under_min, "Boundary", "Failure",
                    f"Value below minimum ({under_min} < {min_val})"
                ))

        # 3. 空值/零值边界
        cases.append(self._make_case(
            api_name, field_name, None, "Boundary",
            "Failure" if self._safe_get(config, "required", False) else "Success",
            "Null value"
        ))

        if field_type == "string":
            cases.append(self._make_case(
                api_name, field_name, "", "Boundary",
                "Failure" if min_len > 0 else "Success",
                "Empty string"
            ))
        elif field_type in ["integer", "number"]:
            cases.append(self._make_case(
                api_name, field_name, 0, "Boundary", "Success",
                "Zero value"
            ))

        # 4. 特殊字符边界（密码/敏感字段）
        if "password" in field_name.lower() or "secret" in field_name.lower():
            cases.extend(self._generate_boundary_special_chars(field_name, config, api_name))

        return cases

    def _generate_security_cases(self, field_name: str, config: dict, api_name: str) -> List[dict]:
        """增强版安全用例生成"""
        cases = []
        field_type = self._safe_get(config, "type", "string")

        # 仅字符串类型生成安全用例
        if field_type != "string":
            return cases

        # 跳过非输入类字段（如ID/时间戳）
        skip_security = ["id", "timestamp", "created_at", "updated_at"]
        if any(kw in field_name.lower() for kw in skip_security):
            return cases

        # 遍历所有安全类型payload
        for attack_type, payloads in self.security_payloads.items():
            for payload in payloads[:2]:  # 限制每个类型的payload数量
                cases.append(self._make_case(
                    api_name, field_name, payload, "Security", "Failure",
                    f"{attack_type} attempt"
                ))

        # 权限绕过测试（针对token/权限字段）
        if any(kw in field_name.lower() for kw in ["token", "auth", "permission", "role"]):
            cases.append(self._make_case(
                api_name, field_name, "admin_token_123456", "Security", "Failure",
                "Unauthorized role/token bypass attempt"
            ))

        return cases

    def _generate_boundary_special_chars(self, field_name: str, config: dict, api_name: str) -> List[dict]:
        """生成特殊字符边界用例"""
        cases = []
        regex = config.get("regex") or config.get("pattern")
        if not regex:
            return cases

        # 提取允许的特殊字符
        special_match = re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?\/\\|`~]', regex)
        allowed_specials = special_match.group() if special_match else "!@#$%"
        forbidden_specials = set("+-=[]{};:'\",.<>?/\\|`~") - set(allowed_specials)

        # 合法特殊字符
        for char in allowed_specials[:3]:
            valid_val = self._generate_compliant_string(10, regex)
            valid_val = valid_val[:-1] + char  # 替换最后一位为特殊字符
            cases.append(self._make_case(
                api_name, field_name, valid_val, "Boundary", "Success",
                f"Valid special character: '{char}'"
            ))

        # 非法特殊字符
        for char in list(forbidden_specials)[:3]:
            valid_val = self._generate_compliant_string(10, regex)
            valid_val = valid_val[:-1] + char  # 替换最后一位为非法特殊字符
            cases.append(self._make_case(
                api_name, field_name, valid_val, "Boundary", "Failure",
                f"Illegal special character: '{char}'"
            ))

        return cases

    def _generate_regex_mismatch(self, regex: str) -> str:
        """生成不匹配正则的字符串"""
        # 生成基础字符串后破坏正则规则
        base_str = self._generate_compliant_string(10)

        # 策略1：添加非法字符
        illegal_chars = ["@", "#", "$", "%", "^", "&", "*", "(", ")", " "]
        modified = base_str + random.choice(illegal_chars)

        # 策略2：如果正则以特定字符开头，替换开头
        if regex.startswith('^[a-zA-Z]'):
            modified = "1" + modified[1:]

        return modified

    def _get_type_error_values(self, field_type: str) -> list:
        """生成类型错误的值列表（增强版）"""
        type_map = {
            "string": [123, 123.45, True, [], {}, None],
            "integer": ["123a", 123.45, True, [], {}, None],
            "number": ["123a", True, [], {}, None],
            "boolean": ["true", 1, 0, [], {}, None],
            "object": ["{}", 123, [], True, None],
            "array": ["[]", 123, {}, True, None],
            "null": ["null", 123, "", True, []]
        }
        return type_map.get(field_type, [])[:3]  # 限制数量，避免用例过多


class LLMDataGenerator:
    """基于 LLM 的数据生成器"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model
        self.client = None

        if OpenAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            logger.warning("OpenAI client not initialized. Missing 'openai' package or API key.")

    def generate_seed_record(self, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成符合 Schema 的语义化种子数据"""
        if not self.client:
            logger.warning("LLM client not available, skipping AI generation.")
            return None

        prompt = self._construct_prompt(schema)
        try:
            logger.info("Calling LLM to generate seed data...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior QA engineer. Generate realistic JSON test data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None

    def _construct_prompt(self, schema: Dict[str, Any]) -> str:
        """构建 Prompt"""
        return f"""
        Please generate ONE valid JSON record based on the following JSON Schema.
        The data should be realistic, semantically consistent (e.g., city matches zip code), and cover all fields.
        
        Schema:
        {json.dumps(schema, indent=2)}
        
        Return ONLY the JSON object.
        """


class DatasetGenerator(BaseGenerator):
    """增强版数据集生成器，支持复杂类型和 LLM 增强"""

    def __init__(self, llm_generator: LLMDataGenerator = None):
        super().__init__()
        self.llm_generator = llm_generator

    def generate_record(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single record based on schema (Try LLM first)"""
        # 1. Try LLM generation
        if self.llm_generator:
            seed_data = self.llm_generator.generate_seed_record(schema)
            if seed_data:
                logger.info("✅ Successfully generated seed data using LLM")
                return seed_data

        # 2. Fallback to Rule-based generation
        logger.info("ℹ️ Using rule-based generation (Fallback)")
        properties = schema.get("properties", schema)
        return self._generate_record(properties, "record")

    def generate_dataset(self, schema: Dict[str, Any], count: int) -> List[dict]:
        """生成符合Schema的真实数据集（支持嵌套对象/数组）"""
        dataset = []
        properties = schema.get("properties", schema)  # 兼容OpenAPI结构

        for idx in range(count):
            try:
                record = self._generate_record(properties, f"record_{idx}")
                dataset.append(record)
            except Exception as e:
                logger.error(f"Failed to generate record {idx}: {e}")

        return dataset

    def _generate_record(self, properties: Dict[str, Any], record_id: str) -> Dict[str, Any]:
        """生成单条记录（递归处理嵌套）"""
        record = {}
        for field, config in properties.items():
            field_type = self._safe_get(config, "type", "string")
            field_path = f"{record_id}.{field}"

            # 生成字段值（支持复杂类型）
            if field_type == "object" and "properties" in config:
                record[field] = self._generate_record(config["properties"], field_path)
            elif field_type == "array" and "items" in config:
                # 随机数组长度（在minItems/maxItems范围内）
                min_items = self._safe_get(config, "minItems", 1, int)
                max_items = self._safe_get(config, "maxItems", 5, int)
                arr_length = random.randint(min_items, max_items)

                item_config = config["items"]
                if item_config.get("type") == "object" and "properties" in item_config:
                    record[field] = [self._generate_record(item_config["properties"], f"{field_path}[{i}]") for i in
                                     range(arr_length)]
                else:
                    record[field] = [self._generate_realistic_field_value(f"{field_path}[{i}]", item_config) for i in
                                     range(arr_length)]
            else:
                record[field] = self._generate_realistic_field_value(field_path, config)

        return record

    def _generate_realistic_field_value(self, field_path: str, config: dict) -> Any:
        """生成真实感强的字段值（增强版）"""
        # 优先使用枚举值
        enum_vals = self._safe_get(config, "enum", [])
        if enum_vals:
            return random.choice(enum_vals)

        # 基于format/字段名生成语义化值
        # 注意：BaseGenerator 中的 _generate_semantic_value 已实现，但为了更清晰的继承，确保 DatasetGenerator 也能正确调用
        return super()._generate_semantic_value(field_path, config)
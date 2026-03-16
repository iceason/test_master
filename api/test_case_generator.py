import random
import string
import json
import asyncio
import re
import logging
from asgiref.sync import sync_to_async
from .models import TestCase, TestCaseCategory
from .field_generators import TestCaseGenerator as LogicGenerator, DatasetGenerator

logger = logging.getLogger(__name__)

class TestCaseGenerator:
    def __init__(self, interface):
        self.interface = interface
        self.schema = interface.schema
        # Initialize advanced generators
        self.dataset_generator = DatasetGenerator()
        # LogicGenerator handles the core generation logic
        self.logic_generator = LogicGenerator()

    async def generate(self, category_ids=None):
        """
        异步生成测试用例
        """
        if not self.schema or not isinstance(self.schema, dict):
            return 0
        
        properties = self.schema.get('properties', {})
        if not properties and self.schema:
            properties = self.schema

        if not properties:
            return 0

        # 获取需要生成的分类
        categories = []
        if category_ids:
            # 异步获取分类对象
            categories = await self._get_categories(category_ids)
        else:
            # 如果没传，默认生成正向
            categories = await self._get_default_categories()

        created_count = 0
        
        for cat in categories:
            # 根据分类编码调用不同的生成策略
            case_data_list = self._generate_by_category(cat, properties)
            
            for case_data in case_data_list:
                await self._create_test_case(cat, case_data)
                created_count += 1
                
        return created_count

    @sync_to_async
    def _get_categories(self, ids):
        return list(TestCaseCategory.objects.filter(id__in=ids))

    @sync_to_async
    def _get_default_categories(self):
        # 默认只生成正向-仅传必要字段
        return list(TestCaseCategory.objects.filter(code='positive_necessary'))

    @staticmethod
    def _derive_test_type(category_code: str) -> str:
        """Derive test_type from category code prefix."""
        for prefix in ('positive', 'negative', 'boundary', 'security'):
            if category_code.startswith(prefix):
                return prefix
        return ''

    @sync_to_async
    def _create_test_case(self, category, data):
        TestCase.objects.create(
            interface=self.interface,
            category=category,
            name=data.get('name', f"{category.name} - 用例"),
            description=data.get('description', ''),
            test_field=data.get('test_field', ''),
            request_data=data.get('request_data', {}),
            expected_value=data.get('expected_value', {}),
            expected_response=data.get('expected_response', {'status': 200}),
            test_type=self._derive_test_type(category.code) if category and category.code else '',
        )

    def _generate_by_category(self, category, properties):
        """
        根据分类编码分发生成逻辑
        返回列表: [{'name':..., 'request_data':...}, ...]
        """
        code = category.code
        # 正向
        if code == 'positive_necessary':
            return self._gen_positive_necessary(properties)
        elif code == 'positive_valid':
            return self._gen_positive_valid(properties)
        elif code == 'positive_enum':
            return self._gen_positive_enum(properties)
        elif code == 'positive_other':
            return self._gen_positive_necessary(properties) # Fallback
            
        # 负向
        elif code == 'negative_missing_required':
            return self._gen_negative_missing(properties)
        elif code == 'negative_type_error':
            return self._gen_negative_type(properties)
        elif code.startswith('negative_'):
             return self._gen_negative_type(properties) # Fallback

        # 边界
        elif code == 'boundary_max_min':
            return self._gen_boundary_max_min(properties)
        elif code == 'boundary_length':
            return self._gen_boundary_length(properties)
        elif code == 'boundary_null_empty':
            return self._gen_boundary_null_empty(properties)
        elif code.startswith('boundary_'):
            return self._gen_boundary_null_empty(properties) # Fallback

        # 安全
        elif code.startswith('security_'):
            return self._gen_security(code, properties)
        
        # 默认回落
        return self._gen_positive_valid(properties)

    # --- Enhanced Logic Implementation ---

    def _get_base_record(self):
        """Generate a high-quality base record using DatasetGenerator"""
        try:
            return self.dataset_generator.generate_record(self.schema)
        except Exception as e:
            logger.error(f"Failed to generate base record: {e}")
            return {}

    def _inject_value(self, base_data, field_name, value):
        """Inject value into nested structure"""
        # Create deep copy
        data = json.loads(json.dumps(base_data))
        
        # Simple recursive injection handling both dict and list
        parts = field_name.replace("[*]", "").split(".")
        current = data
        
        try:
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
                if isinstance(current, list) and len(current) > 0:
                    current = current[0]
            
            leaf = parts[-1]
            if isinstance(current, dict):
                current[leaf] = value
            elif isinstance(current, list) and len(current) > 0:
                 # Simplified array handling: replace in first item
                 # Ideally we should handle [*] properly but for single case injection this is often enough
                 pass
        except Exception as e:
            logger.debug(f"Injection failed for {field_name}: {e}")
            
        return data

    def _map_logic_cases(self, logic_cases, base_data, category_prefix=""):
        """Map LogicGenerator cases to API format"""
        api_cases = []
        for case in logic_cases:
            target_field = case.get("target_field")
            input_val = case.get("input_value")
            rationale = case.get("test_rationale", "")
            expected_outcome = case.get("expected_outcome", "success")
            
            # Enrich payload
            request_data = self._inject_value(base_data, target_field, input_val)
            
            # Map expected value
            expected_value = {'status': 'success'} if expected_outcome == 'success' else {'error': rationale}
            
            api_cases.append({
                'name': f'{category_prefix}: {target_field} - {rationale}',
                'description': rationale,
                'test_field': target_field,
                'request_data': request_data,
                'expected_value': expected_value
            })
        return api_cases

    def _gen_positive_necessary(self, properties):
        # Use DatasetGenerator for full valid payload
        data = self._get_base_record()
        return [{
            'name': '正向-默认参数',
            'description': '传入所有字段的合法值 (基于Schema生成的完整示例)',
            'request_data': data,
            'expected_value': {'status': 'success'}
        }]

    def _gen_positive_valid(self, properties):
        return self._gen_positive_necessary(properties)

    def _gen_positive_enum(self, properties):
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            if 'enum' in v:
                for val in v['enum']:
                    data = self._inject_value(base_data, k, val)
                    cases.append({
                        'name': f'正向-枚举值: {k}={val}',
                        'test_field': k,
                        'request_data': data,
                        'expected_value': {'status': 'success'}
                    })
        return cases if cases else self._gen_positive_necessary(properties)

    def _gen_negative_missing(self, properties):
        # Use LogicGenerator to identify required fields, or just use existing logic
        # LogicGenerator._generate_negative_cases handles required check
        # But we want to be specific about "missing" category
        cases = []
        base_data = self._get_base_record()
        
        # Iterate properties to check 'required' (LogicGenerator doesn't expose a simple "get missing cases" method)
        # But wait, LogicGenerator._generate_negative_cases produces "Missing required field" cases.
        
        for k, v in properties.items():
            # Delegate to LogicGenerator
            logic_cases = self.logic_generator._generate_negative_cases(k, v, "API")
            # Filter for missing required
            filtered = [c for c in logic_cases if "Missing required field" in c.get("test_rationale", "")]
            
            # If logic generator didn't produce it (maybe field not required), skip
            # If it did, map it.
            # Note: LogicGenerator returns None for input_value for missing.
            
            for c in filtered:
                # Special handling for missing: delete field
                data = json.loads(json.dumps(base_data))
                if k in data:
                    del data[k]
                
                cases.append({
                    'name': f'负向-缺失必填: {k}',
                    'description': 'Missing required field',
                    'test_field': k,
                    'request_data': data,
                    'expected_value': {'error': f'Missing field {k}'}
                })
                
        return cases

    def _gen_negative_type(self, properties):
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            logic_cases = self.logic_generator._generate_negative_cases(k, v, "API")
            # Filter for Type error
            filtered = [c for c in logic_cases if "Type error" in c.get("test_rationale", "")]
            cases.extend(self._map_logic_cases(filtered, base_data, "负向-类型错误"))
            
        return cases

    def _gen_negative_validation(self, properties):
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            logic_cases = self.logic_generator._generate_negative_cases(k, v, "API")
            # Filter for Regex, Reserved, Format, Enum
            filtered = [c for c in logic_cases if any(x in c.get("test_rationale", "") for x in 
                       ["Regex", "Reserved", "Invalid", "not in enum"])]
            cases.extend(self._map_logic_cases(filtered, base_data, "负向-校验失败"))
            
        return cases

    def _gen_boundary_max_min(self, properties):
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            logic_cases = self.logic_generator._generate_boundary_cases(k, v, "API")
            # Filter for max/min values (numeric)
            filtered = [c for c in logic_cases if any(x in c.get("test_rationale", "") for x in ["maximum", "minimum"])]
            cases.extend(self._map_logic_cases(filtered, base_data, "边界-极值"))
            
        return cases

    def _gen_boundary_length(self, properties):
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            logic_cases = self.logic_generator._generate_boundary_cases(k, v, "API")
            # Filter for length
            filtered = [c for c in logic_cases if "length" in c.get("test_rationale", "")]
            cases.extend(self._map_logic_cases(filtered, base_data, "边界-长度"))
            
        return cases

    def _gen_boundary_null_empty(self, properties):
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            logic_cases = self.logic_generator._generate_boundary_cases(k, v, "API")
            # Filter for Null, Empty
            filtered = [c for c in logic_cases if any(x in c.get("test_rationale", "") for x in ["Null", "Empty"])]
            cases.extend(self._map_logic_cases(filtered, base_data, "边界-空/Null"))
            
        return cases

    def _gen_boundary_special_chars(self, properties):
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            logic_cases = self.logic_generator._generate_boundary_cases(k, v, "API")
            # LogicGenerator puts special chars in boundary too? 
            # Wait, _generate_boundary_cases calls _generate_boundary_special_chars internally if password/secret.
            # So yes, they are there.
            filtered = [c for c in logic_cases if "special char" in c.get("test_rationale", "")]
            cases.extend(self._map_logic_cases(filtered, base_data, "边界-特殊字符"))
            
        return cases

    def _gen_security(self, code, properties):
        # Map API code to LogicGenerator payloads or methods
        # LogicGenerator has _generate_security_cases
        cases = []
        base_data = self._get_base_record()
        
        for k, v in properties.items():
            logic_cases = self.logic_generator._generate_security_cases(k, v, "API")
            
            # LogicGenerator generates ALL security cases.
            # We need to filter based on 'code' passed from API.
            # API codes: security_sql_injection, security_xss, etc.
            # LogicGenerator rationale: "SQL Injection attempt", "XSS attempt"
            
            mapping = {
                'security_sql_injection': 'SQL Injection',
                'security_xss': 'XSS',
                'security_cmd_injection': 'Command Injection',
                'security_fuzz': 'Fuzzing'
            }
            
            target_type = mapping.get(code)
            if target_type:
                filtered = [c for c in logic_cases if target_type in c.get("test_rationale", "")]
                cases.extend(self._map_logic_cases(filtered, base_data, f"安全-{code}"))
                
        return cases

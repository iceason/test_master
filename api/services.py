import random
import string
from .models import TestCase

class TestCaseGenerator:
    def __init__(self, interface):
        self.interface = interface
        self.schema = interface.schema

    def generate(self):
        """
        Generates test cases based on the interface schema.
        Returns the number of created test cases.
        """
        if not self.schema or not isinstance(self.schema, dict):
            return 0

        # Assume standard JSON Schema structure or simple dict
        properties = self.schema.get('properties', {})
        if not properties and self.schema:
            # Maybe flat key-value
            properties = self.schema
        
        if not properties:
            return 0

        created_count = 0
        
        # 1. Happy Path Case
        happy_data = self._generate_happy_path(properties)
        TestCase.objects.create(
            interface=self.interface,
            name="正向用例 - 默认参数",
            request_data=happy_data,
            expected_response={"status": 200, "message": "success"},
            test_type='positive',
        )
        created_count += 1

        # 2. Boundary Case (for integers)
        boundary_data = self._generate_boundary_path(properties)
        if boundary_data != happy_data:
            TestCase.objects.create(
                interface=self.interface,
                name="边界测试用例",
                request_data=boundary_data,
                expected_response={"status": 200},
                test_type='boundary',
            )
            created_count += 1
            
        return created_count

    def _generate_happy_path(self, properties):
        data = {}
        for key, value in properties.items():
            field_type = value.get('type', 'string') if isinstance(value, dict) else 'string'
            
            if field_type == 'string':
                data[key] = ''.join(random.choices(string.ascii_letters, k=8))
            elif field_type == 'integer':
                data[key] = random.randint(1, 100)
            elif field_type == 'boolean':
                data[key] = True
            else:
                data[key] = "test_value"
        return data

    def _generate_boundary_path(self, properties):
        data = {}
        for key, value in properties.items():
            field_type = value.get('type', 'string') if isinstance(value, dict) else 'string'
            
            if field_type == 'integer':
                # Max integer or 0
                data[key] = 2147483647
            elif field_type == 'string':
                data[key] = "" # Empty string
            else:
                data[key] = self._generate_happy_path({key: value})[key]
        return data

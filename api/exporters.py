import json
import csv
import yaml
import io
from openpyxl import Workbook
from api.models import Directory, Interface, TestCase
from typing import Iterable

class TestCasesExporter:
    def __init__(self):
        pass

    def export(self, scope, ids, fmt):
        data = self._collect_data(scope, ids)
        
        if fmt == 'json':
            return self._to_json(data), 'application/json', 'test_cases.json'
        elif fmt == 'yaml':
            return self._to_yaml(data), 'application/x-yaml', 'test_cases.yaml'
        elif fmt == 'csv':
            return self._to_csv(data), 'text/csv', 'test_cases.csv'
        elif fmt == 'excel':
            return self._to_excel(data), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'test_cases.xlsx'
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    def _collect_data(self, scope, ids):
        if scope == 'directory':
            dirs = Directory.objects.filter(id__in=ids)
            return [self._serialize_directory(d) for d in dirs]
        elif scope == 'interface':
            interfaces = Interface.objects.filter(id__in=ids)
            return [self._serialize_interface(i) for i in interfaces]
        elif scope == 'testcase':
            cases = TestCase.objects.filter(id__in=ids).select_related('interface', 'interface__directory', 'category')
            # Group by interface for better structure in JSON/YAML
            # But for simple list of cases, we can just return the list or group them.
            # Let's group them by interface for consistency if possible, 
            # but if we select random cases, a flat list or grouped list is fine.
            # Let's return a virtual structure: List of Interfaces containing only selected cases.
            
            # Group by interface
            interface_map = {}
            for case in cases:
                if case.interface_id not in interface_map:
                    interface_map[case.interface_id] = {
                        'obj': case.interface,
                        'cases': []
                    }
                interface_map[case.interface_id]['cases'].append(case)
            
            result = []
            for item in interface_map.values():
                serialized_iface = self._serialize_interface(item['obj'], cases=item['cases'])
                result.append(serialized_iface)
            return result
        return []

    def _serialize_directory(self, directory):
        return {
            "type": "directory",
            "id": directory.id,
            "name": directory.name,
            "sub_directories": [self._serialize_directory(d) for d in directory.sub_directories.all()],
            "interfaces": [self._serialize_interface(i) for i in directory.interfaces.all()]
        }

    def _serialize_interface(self, interface, cases=None):
        if cases is None:
            cases = interface.testcases.all().select_related('category')
        
        return {
            "type": "interface",
            "id": interface.id,
            "name": interface.name,
            "method": interface.method,
            "path": interface.path,
            "directory_path": self._get_dir_path(interface.directory),
            "test_cases": [self._serialize_case(c) for c in cases]
        }

    def _serialize_case(self, case):
        return {
            "type": "testcase",
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "category": case.category.name if case.category else "",
            "test_field": case.test_field,
            "request_data": case.request_data,
            "expected_value": case.expected_value
        }

    def _get_dir_path(self, directory):
        path = [directory.name]
        parent = directory.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return "/".join(path)

    def _to_json(self, data):
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _to_yaml(self, data):
        return yaml.dump(data, allow_unicode=True, sort_keys=False)

    def _to_csv(self, data):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Directory', 'Interface Name', 'Method', 'Path', 'Case ID', 'Case Name', 'Category', 'Description', 'Test Field', 'Request Data', 'Expected Value'])

        def process_item(item, dir_path=""):
            if item.get('type') == 'directory':
                current_path = f"{dir_path}/{item['name']}" if dir_path else item['name']
                for sub in item.get('sub_directories', []):
                    process_item(sub, current_path)
                for iface in item.get('interfaces', []):
                    # interface already has directory_path computed in serialization, but for consistency in recursive walk:
                    # Actually _serialize_interface computes absolute path.
                    process_interface(iface)
            elif item.get('type') == 'interface':
                process_interface(item)

        def process_interface(iface):
            d_path = iface.get('directory_path', '')
            i_name = iface['name']
            i_method = iface['method']
            i_path = iface['path']
            
            for case in iface.get('test_cases', []):
                writer.writerow([
                    d_path,
                    i_name,
                    i_method,
                    i_path,
                    case['id'],
                    case['name'],
                    case['category'],
                    case['description'],
                    case['test_field'],
                    json.dumps(case['request_data'], ensure_ascii=False),
                    json.dumps(case['expected_value'], ensure_ascii=False)
                ])

        for item in data:
            process_item(item)
            
        return output.getvalue()
    
    def _to_excel(self, data):
        """导出为Excel格式"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Test Cases"
        
        # 写入表头
        headers = ['Directory', 'Interface Name', 'Method', 'Path', 'Case ID', 'Case Name', 'Category', 'Description', 'Test Field', 'Request Data', 'Expected Value']
        ws.append(headers)
        
        # 写入数据
        def process_item(item, dir_path=""):
            if item.get('type') == 'directory':
                current_path = f"{dir_path}/{item['name']}" if dir_path else item['name']
                for sub in item.get('sub_directories', []):
                    process_item(sub, current_path)
                for iface in item.get('interfaces', []):
                    process_interface(iface)
            elif item.get('type') == 'interface':
                process_interface(item)
        
        def process_interface(iface):
            d_path = iface.get('directory_path', '')
            i_name = iface['name']
            i_method = iface['method']
            i_path = iface['path']
            
            for case in iface.get('test_cases', []):
                ws.append([
                    d_path,
                    i_name,
                    i_method,
                    i_path,
                    case['id'],
                    case['name'],
                    case['category'],
                    case['description'],
                    case['test_field'],
                    json.dumps(case['request_data'], ensure_ascii=False),
                    json.dumps(case['expected_value'], ensure_ascii=False)
                ])
        
        for item in data:
            process_item(item)
        
        # 保存到字节流
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def stream_csv(self, scope, ids) -> Iterable[str]:
        """以流式方式导出CSV，适合大数据量"""
        data = self._collect_data(scope, ids)
        # 先写表头
        headers = ['Directory', 'Interface Name', 'Method', 'Path', 'Case ID', 'Case Name', 'Category', 'Description', 'Test Field', 'Request Data', 'Expected Value']
        yield ','.join([self._escape_csv(h) for h in headers]) + '\n'

        def process_item(item, dir_path=""):
            if item.get('type') == 'directory':
                current_path = f"{dir_path}/{item['name']}" if dir_path else item['name']
                for sub in item.get('sub_directories', []):
                    yield from process_item(sub, current_path)
                for iface in item.get('interfaces', []):
                    yield from process_interface(iface)
            elif item.get('type') == 'interface':
                yield from process_interface(item)

        def process_interface(iface):
            d_path = iface.get('directory_path', '')
            i_name = iface['name']
            i_method = iface['method']
            i_path = iface['path']
            for case in iface.get('test_cases', []):
                row = [
                    d_path,
                    i_name,
                    i_method,
                    i_path,
                    str(case['id']),
                    case['name'],
                    case['category'],
                    case['description'],
                    case['test_field'],
                    json.dumps(case['request_data'], ensure_ascii=False),
                    json.dumps(case['expected_value'], ensure_ascii=False),
                ]
                yield ','.join([self._escape_csv(str(col)) for col in row]) + '\n'

        for item in data:
            yield from process_item(item)

    @staticmethod
    def _escape_csv(value: str) -> str:
        if any(ch in value for ch in [',', '"', '\n', '\r']):
            return '"' + value.replace('"', '""') + '"'
        return value

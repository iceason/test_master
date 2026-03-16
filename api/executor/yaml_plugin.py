"""
YAML配置插件

支持数据库与YAML的双向同步
"""

import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class YamlPlugin:
    """YAML配置插件"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_to_yaml(self, scope: str, ids: List[int]) -> str:
        """
        导出到YAML格式
        
        支持:
        - 单个测试用例
        - 测试套件（多用例）
        - 完整接口（含所有用例）
        - 全局环境配置
        
        Args:
            scope: 导出范围（testcase/interface/environment）
            ids: ID列表
            
        Returns:
            YAML字符串
        """
        from django.apps import apps
        
        if scope == 'testcase':
            TestCase = apps.get_model('api', 'TestCase')
            test_cases = TestCase.objects.filter(id__in=ids).select_related('interface', 'category')
            return self._export_testcases_to_yaml(test_cases)
        
        elif scope == 'interface':
            Interface = apps.get_model('api', 'Interface')
            interfaces = Interface.objects.filter(id__in=ids).prefetch_related('testcases')
            return self._export_interfaces_to_yaml(interfaces)
        
        elif scope == 'environment':
            Environment = apps.get_model('api', 'Environment')
            environments = Environment.objects.filter(id__in=ids)
            return self._export_environments_to_yaml(environments)
        
        else:
            raise ValueError(f"不支持的导出范围: {scope}")
    
    def _export_testcases_to_yaml(self, test_cases) -> str:
        """导出测试用例到YAML"""
        data = {
            'version': '1.0',
            'type': 'testcases',
            'testcases': []
        }
        
        for tc in test_cases:
            testcase_data = {
                'name': tc.name,
                'description': tc.description,
                'interface': {
                    'method': tc.interface.method,
                    'path': tc.interface.path
                },
                'request_data': tc.request_data,
                'expected_response': tc.expected_response,
                'expected_value': tc.expected_value,
                'test_type': tc.test_type,
                'category': tc.category.code if tc.category else None
            }
            data['testcases'].append(testcase_data)
        
        return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def _export_interfaces_to_yaml(self, interfaces) -> str:
        """导出接口到YAML"""
        data = {
            'version': '1.0',
            'type': 'interfaces',
            'interfaces': []
        }
        
        for interface in interfaces:
            interface_data = {
                'name': interface.name,
                'method': interface.method,
                'path': interface.path,
                'schema': interface.schema,
                'testcases': []
            }
            
            for tc in interface.testcases.all():
                testcase_data = {
                    'name': tc.name,
                    'description': tc.description,
                    'request_data': tc.request_data,
                    'expected_response': tc.expected_response,
                    'expected_value': tc.expected_value,
                    'test_type': tc.test_type
                }
                interface_data['testcases'].append(testcase_data)
            
            data['interfaces'].append(interface_data)
        
        return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def _export_environments_to_yaml(self, environments) -> str:
        """导出环境配置到YAML"""
        data = {
            'version': '1.0',
            'type': 'environments',
            'environments': {}
        }
        
        for env in environments:
            data['environments'][env.code] = {
                'name': env.name,
                'base_url': env.base_url,
                'description': env.description,
                'config': env.config
            }
        
        return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def import_from_yaml(self, yaml_content: str, mode: str = 'merge') -> Dict[str, Any]:
        """
        从YAML导入
        
        策略:
        - merge: 增量更新（冲突时更新现有记录）
        - replace: 全量覆盖（删除后重建）
        
        Args:
            yaml_content: YAML内容
            mode: 导入模式（merge/replace）
            
        Returns:
            导入结果统计
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {e}")
        
        if not isinstance(data, dict):
            raise ValueError("YAML内容必须是字典格式")
        
        yaml_type = data.get('type')
        
        if yaml_type == 'testcases':
            return self._import_testcases_from_yaml(data, mode)
        elif yaml_type == 'interfaces':
            return self._import_interfaces_from_yaml(data, mode)
        elif yaml_type == 'environments':
            return self._import_environments_from_yaml(data, mode)
        else:
            raise ValueError(f"不支持的YAML类型: {yaml_type}")
    
    def _import_testcases_from_yaml(self, data: Dict, mode: str) -> Dict[str, Any]:
        """从YAML导入测试用例"""
        from django.apps import apps
        
        TestCase = apps.get_model('api', 'TestCase')
        Interface = apps.get_model('api', 'Interface')
        TestCaseCategory = apps.get_model('api', 'TestCaseCategory')
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        testcases = data.get('testcases', [])
        
        for tc_data in testcases:
            try:
                # 查找或创建接口
                interface_data = tc_data.get('interface', {})
                interface, _ = Interface.objects.get_or_create(
                    method=interface_data.get('method'),
                    path=interface_data.get('path'),
                    defaults={'name': f"{interface_data.get('method')} {interface_data.get('path')}"}
                )
                
                # 查找分类
                category = None
                if tc_data.get('category'):
                    try:
                        category = TestCaseCategory.objects.get(code=tc_data['category'])
                    except TestCaseCategory.DoesNotExist:
                        pass
                
                # 检查是否已存在
                existing = TestCase.objects.filter(
                    interface=interface,
                    name=tc_data['name']
                ).first()
                
                if existing:
                    if mode == 'merge':
                        # 更新现有记录
                        for field in ['description', 'request_data', 'expected_response', 
                                     'expected_value', 'test_type']:
                            if field in tc_data:
                                setattr(existing, field, tc_data[field])
                        if category:
                            existing.category = category
                        existing.save()
                        updated_count += 1
                    else:
                        # replace模式：先删除再创建
                        existing.delete()
                        TestCase.objects.create(
                            interface=interface,
                            category=category,
                            name=tc_data['name'],
                            description=tc_data.get('description', ''),
                            request_data=tc_data.get('request_data', {}),
                            expected_response=tc_data.get('expected_response', {}),
                            expected_value=tc_data.get('expected_value', {}),
                            test_type=tc_data.get('test_type')
                        )
                        created_count += 1
                else:
                    # 创建新记录
                    TestCase.objects.create(
                        interface=interface,
                        category=category,
                        name=tc_data['name'],
                        description=tc_data.get('description', ''),
                        request_data=tc_data.get('request_data', {}),
                        expected_response=tc_data.get('expected_response', {}),
                        expected_value=tc_data.get('expected_value', {}),
                        test_type=tc_data.get('test_type')
                    )
                    created_count += 1
                    
            except Exception as e:
                logger.error(f"导入测试用例失败: {tc_data.get('name')} - {e}")
                error_count += 1
        
        return {
            'created': created_count,
            'updated': updated_count,
            'errors': error_count,
            'total': len(testcases)
        }
    
    def _import_interfaces_from_yaml(self, data: Dict, mode: str) -> Dict[str, Any]:
        """从YAML导入接口"""
        from django.apps import apps
        
        Interface = apps.get_model('api', 'Interface')
        TestCase = apps.get_model('api', 'TestCase')
        
        created_interfaces = 0
        updated_interfaces = 0
        created_testcases = 0
        updated_testcases = 0
        error_count = 0
        
        interfaces = data.get('interfaces', [])
        
        for interface_data in interfaces:
            try:
                # 查找或创建接口
                interface, created = Interface.objects.get_or_create(
                    method=interface_data.get('method'),
                    path=interface_data.get('path'),
                    defaults={
                        'name': interface_data.get('name', ''),
                        'schema': interface_data.get('schema', {})
                    }
                )
                
                if created:
                    created_interfaces += 1
                else:
                    if mode == 'merge':
                        interface.name = interface_data.get('name', interface.name)
                        interface.schema = interface_data.get('schema', interface.schema)
                        interface.save()
                        updated_interfaces += 1
                
                # 导入测试用例
                for tc_data in interface_data.get('testcases', []):
                    existing_tc = TestCase.objects.filter(
                        interface=interface,
                        name=tc_data['name']
                    ).first()
                    
                    if existing_tc:
                        if mode == 'merge':
                            for field in ['description', 'request_data', 'expected_response', 
                                         'expected_value', 'test_type']:
                                if field in tc_data:
                                    setattr(existing_tc, field, tc_data[field])
                            existing_tc.save()
                            updated_testcases += 1
                    else:
                        TestCase.objects.create(
                            interface=interface,
                            name=tc_data['name'],
                            description=tc_data.get('description', ''),
                            request_data=tc_data.get('request_data', {}),
                            expected_response=tc_data.get('expected_response', {}),
                            expected_value=tc_data.get('expected_value', {}),
                            test_type=tc_data.get('test_type')
                        )
                        created_testcases += 1
                        
            except Exception as e:
                logger.error(f"导入接口失败: {interface_data.get('name')} - {e}")
                error_count += 1
        
        return {
            'created_interfaces': created_interfaces,
            'updated_interfaces': updated_interfaces,
            'created_testcases': created_testcases,
            'updated_testcases': updated_testcases,
            'errors': error_count,
            'total': len(interfaces)
        }
    
    def _import_environments_from_yaml(self, data: Dict, mode: str) -> Dict[str, Any]:
        """从YAML导入环境配置"""
        from django.apps import apps
        
        Environment = apps.get_model('api', 'Environment')
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        environments = data.get('environments', {})
        
        for code, env_data in environments.items():
            try:
                env, created = Environment.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': env_data.get('name', code),
                        'base_url': env_data.get('base_url', ''),
                        'description': env_data.get('description', ''),
                        'config': env_data.get('config', {})
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    if mode == 'merge':
                        env.name = env_data.get('name', env.name)
                        env.base_url = env_data.get('base_url', env.base_url)
                        env.description = env_data.get('description', env.description)
                        env.config = env_data.get('config', env.config)
                        env.save()
                        updated_count += 1
                        
            except Exception as e:
                logger.error(f"导入环境失败: {code} - {e}")
                error_count += 1
        
        return {
            'created': created_count,
            'updated': updated_count,
            'errors': error_count,
            'total': len(environments)
        }
    
    def sync_db_to_yaml(self, output_dir: str) -> None:
        """
        数据库同步到YAML（用于版本控制）
        
        Args:
            output_dir: 输出目录
        """
        from django.apps import apps
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 导出环境配置
        Environment = apps.get_model('api', 'Environment')
        environments = Environment.objects.filter(is_active=True)
        if environments.exists():
            yaml_content = self._export_environments_to_yaml(environments)
            (output_path / 'environments.yaml').write_text(yaml_content, encoding='utf-8')
            logger.info(f"已导出 {environments.count()} 个环境配置")
        
        # 导出接口和用例
        Interface = apps.get_model('api', 'Interface')
        interfaces = Interface.objects.all().prefetch_related('testcases')
        if interfaces.exists():
            yaml_content = self._export_interfaces_to_yaml(interfaces)
            (output_path / 'interfaces.yaml').write_text(yaml_content, encoding='utf-8')
            logger.info(f"已导出 {interfaces.count()} 个接口")
    
    def sync_yaml_to_db(self, yaml_dir: str, mode: str = 'merge') -> Dict[str, Any]:
        """
        YAML同步到数据库（部署时初始化）
        
        Args:
            yaml_dir: YAML配置目录
            mode: 导入模式
            
        Returns:
            导入结果统计
        """
        yaml_path = Path(yaml_dir)
        
        if not yaml_path.exists():
            raise ValueError(f"YAML目录不存在: {yaml_dir}")
        
        results = {}
        
        # 导入环境配置
        env_file = yaml_path / 'environments.yaml'
        if env_file.exists():
            yaml_content = env_file.read_text(encoding='utf-8')
            results['environments'] = self.import_from_yaml(yaml_content, mode)
        
        # 导入接口和用例
        interface_file = yaml_path / 'interfaces.yaml'
        if interface_file.exists():
            yaml_content = interface_file.read_text(encoding='utf-8')
            results['interfaces'] = self.import_from_yaml(yaml_content, mode)
        
        return results

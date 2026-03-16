"""
OpenAPI/Swagger 文档解析器

支持解析 OpenAPI 3.0+ 和 Swagger 2.0 格式的 JSON/YAML 文件，
将其中的接口定义提取并映射为系统内部的 Interface 数据结构。
"""

import json
import yaml
from typing import Dict, List, Any, Optional


class OpenAPIParser:
    """解析 OpenAPI/Swagger 文档并提取接口信息"""

    SUPPORTED_METHODS = {'get', 'post', 'put', 'delete', 'patch'}

    def parse_file(self, file_content: str, file_type: str) -> Dict[str, Any]:
        """
        解析文件内容为字典

        Args:
            file_content: 文件文本内容
            file_type: 文件类型 ('json' 或 'yaml')

        Returns:
            解析后的 OpenAPI 规范字典

        Raises:
            ValueError: 解析失败时抛出
        """
        try:
            if file_type == 'json':
                return json.loads(file_content)
            else:  # yaml / yml
                return yaml.safe_load(file_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {str(e)}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析失败: {str(e)}")

    def validate_spec(self, spec: Dict[str, Any]) -> None:
        """
        验证 OpenAPI 规范的基本结构

        Args:
            spec: OpenAPI 规范字典

        Raises:
            ValueError: 规范无效时抛出
        """
        if not isinstance(spec, dict):
            raise ValueError("无效的 OpenAPI 文档：根节点必须是对象")

        # 检查是否为 OpenAPI 3.x 或 Swagger 2.x
        is_openapi3 = 'openapi' in spec
        is_swagger2 = 'swagger' in spec

        if not is_openapi3 and not is_swagger2:
            raise ValueError("无效的 OpenAPI 文档：缺少 'openapi' 或 'swagger' 版本字段")

        if 'paths' not in spec or not isinstance(spec.get('paths'), dict):
            raise ValueError("无效的 OpenAPI 文档：缺少 'paths' 定义")

    def get_spec_info(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取规范的基本信息（用于前端预览）

        Args:
            spec: OpenAPI 规范字典

        Returns:
            包含 title, version, totalApis, tags 等信息的字典
        """
        info = spec.get('info', {})
        paths = spec.get('paths', {})

        # 计算接口总数
        total_apis = 0
        all_tags = set()
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, definition in methods.items():
                if method.lower() in self.SUPPORTED_METHODS:
                    total_apis += 1
                    if isinstance(definition, dict):
                        tags = definition.get('tags', [])
                        if isinstance(tags, list):
                            all_tags.update(tags)

        return {
            'title': info.get('title', '未命名'),
            'version': info.get('version', ''),
            'description': info.get('description', ''),
            'totalApis': total_apis,
            'tags': sorted(list(all_tags)),
        }

    def extract_interfaces(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 OpenAPI 规范中提取接口列表

        Args:
            spec: OpenAPI 规范字典

        Returns:
            接口信息列表，每个元素包含 path, method, name, schema
        """
        interfaces = []
        paths = spec.get('paths', {})
        is_swagger2 = 'swagger' in spec

        # Swagger 2.0 的 basePath
        base_path = ''
        if is_swagger2:
            base_path = spec.get('basePath', '').rstrip('/')

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue

            # 处理路径级别的 parameters
            path_params = methods.get('parameters', [])

            for method, definition in methods.items():
                if method.lower() not in self.SUPPORTED_METHODS:
                    continue

                if not isinstance(definition, dict):
                    continue

                # 构建完整路径
                full_path = f"{base_path}{path}" if base_path else path

                # 提取名称：优先使用 summary，其次使用 operationId
                name = (
                    definition.get('summary')
                    or definition.get('operationId')
                    or f"{method.upper()} {full_path}"
                )
                # 截断过长的名称
                if len(name) > 100:
                    name = name[:97] + '...'

                # 构建 schema
                schema = self._build_schema(definition, path_params, is_swagger2)

                interfaces.append({
                    'path': full_path,
                    'method': method.upper(),
                    'name': name,
                    'schema': schema,
                })

        return interfaces

    def _build_schema(
        self,
        definition: Dict[str, Any],
        path_params: List,
        is_swagger2: bool
    ) -> Dict[str, Any]:
        """
        构建接口的 schema 信息

        Args:
            definition: 单个接口的定义
            path_params: 路径级别的参数
            is_swagger2: 是否为 Swagger 2.0

        Returns:
            包含 description, parameters, requestBody, responses, tags 的字典
        """
        schema: Dict[str, Any] = {}

        # description
        description = definition.get('description', '')
        if description:
            schema['description'] = description

        # parameters（合并路径级和操作级参数）
        op_params = definition.get('parameters', [])
        all_params = []
        if isinstance(path_params, list):
            all_params.extend(path_params)
        if isinstance(op_params, list):
            all_params.extend(op_params)

        if is_swagger2:
            # Swagger 2.0: body 参数在 parameters 中
            body_params = [p for p in all_params if isinstance(p, dict) and p.get('in') == 'body']
            non_body_params = [p for p in all_params if isinstance(p, dict) and p.get('in') != 'body']

            if non_body_params:
                schema['parameters'] = non_body_params
            if body_params:
                schema['requestBody'] = body_params[0].get('schema', {})
        else:
            # OpenAPI 3.x
            if all_params:
                schema['parameters'] = all_params

            request_body = definition.get('requestBody')
            if request_body:
                schema['requestBody'] = request_body

        # responses
        responses = definition.get('responses')
        if responses:
            schema['responses'] = responses

        # tags
        tags = definition.get('tags', [])
        if tags:
            schema['tags'] = tags

        return schema

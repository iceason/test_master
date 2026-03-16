"""
配置管理器

支持多环境配置和变量插值
"""

import os
import re
import logging
from typing import Dict, Any, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    多环境配置管理
    
    配置层级:
    1. 全局默认配置
    2. 环境特定配置（test/staging/prod）
    3. 用户自定义配置
    4. 运行时动态参数
    """
    
    def __init__(self, global_config: Optional[Dict] = None):
        self.global_config = global_config or {}
        self.env_configs = {}
        self.logger = logging.getLogger(__name__)
    
    def load_environment(self, env: str) -> Dict[str, Any]:
        """
        加载环境配置
        
        Args:
            env: 环境名称（test/staging/prod）
            
        Returns:
            环境配置字典
        """
        if env in self.env_configs:
            return self.env_configs[env]
        
        # 从数据库加载环境配置
        from django.apps import apps
        try:
            Environment = apps.get_model('api', 'Environment')
            env_obj = Environment.objects.get(code=env, is_active=True)
            
            config = {
                'name': env_obj.name,
                'base_url': env_obj.base_url,
                'code': env_obj.code,
                **env_obj.config
            }
            
            self.env_configs[env] = config
            return config
            
        except Exception as e:
            logger.warning(f"无法加载环境配置 {env}: {e}")
            return {}
    
    def merge_configs(self, *configs: Dict) -> Dict[str, Any]:
        """
        智能合并配置（深度合并）
        
        Args:
            *configs: 配置字典列表
            
        Returns:
            合并后的配置字典
        """
        result = {}
        
        for config in configs:
            result = self._deep_merge(result, config)
        
        return result
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """
        深度合并两个字典
        
        Args:
            base: 基础字典
            update: 更新字典
            
        Returns:
            合并后的字典
        """
        result = deepcopy(base)
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    def interpolate_variables(self, config: Dict, context: Optional[Dict] = None) -> Dict:
        """
        变量插值
        
        支持:
        - 环境变量：${ENV_VAR}
        - 配置引用：${config.base_url}
        - 运行时变量：${runtime.timestamp}
        - 上下文变量：${context.user_id}
        
        Args:
            config: 配置字典
            context: 上下文变量
            
        Returns:
            插值后的配置字典
        """
        context = context or {}
        
        def interpolate_value(value):
            if isinstance(value, str):
                return self._interpolate_string(value, config, context)
            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [interpolate_value(item) for item in value]
            else:
                return value
        
        return interpolate_value(config)
    
    def _interpolate_string(self, text: str, config: Dict, context: Dict) -> str:
        """
        字符串插值
        
        Args:
            text: 原始字符串
            config: 配置字典
            context: 上下文变量
            
        Returns:
            插值后的字符串
        """
        # 环境变量：${ENV_VAR}
        env_pattern = r'\$\{ENV_([A-Z_]+)\}'
        text = re.sub(env_pattern, lambda m: os.getenv(m.group(1), ''), text)
        
        # 配置引用：${config.key}
        config_pattern = r'\$\{config\.([a-zA-Z_][a-zA-Z0-9_\.]*)\}'
        text = re.sub(config_pattern, lambda m: str(self._get_nested_value(config, m.group(1))), text)
        
        # 上下文变量：${context.key}
        context_pattern = r'\$\{context\.([a-zA-Z_][a-zA-Z0-9_\.]*)\}'
        text = re.sub(context_pattern, lambda m: str(context.get(m.group(1), '')), text)
        
        # 运行时变量
        if '${runtime.timestamp}' in text:
            from datetime import datetime
            text = text.replace('${runtime.timestamp}', str(int(datetime.now().timestamp())))
        
        return text
    
    def _get_nested_value(self, data: Dict, path: str, default: Any = '') -> Any:
        """
        获取嵌套字典的值
        
        Args:
            data: 数据字典
            path: 路径（用.分隔）
            default: 默认值
            
        Returns:
            值或默认值
        """
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_full_config(self, env: str, runtime_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        获取完整配置
        
        合并顺序：全局配置 -> 环境配置 -> 运行时参数
        
        Args:
            env: 环境名称
            runtime_params: 运行时参数
            
        Returns:
            完整配置字典
        """
        env_config = self.load_environment(env)
        runtime_params = runtime_params or {}
        
        # 合并配置
        full_config = self.merge_configs(
            self.global_config,
            env_config,
            runtime_params
        )
        
        # 变量插值
        full_config = self.interpolate_variables(full_config, runtime_params)
        
        return full_config

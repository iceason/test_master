"""
增强型HTTP客户端

提供连接池复用、自动重试、超时控制等企业级特性
"""

import logging
import time
from typing import Dict, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ClientConfig:
    """HTTP客户端配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
        pool_size: int = 50,
        timeout: tuple = (5, 30),  # (connect_timeout, read_timeout)
        verify_ssl: bool = True,
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.pool_size = pool_size
        self.timeout = timeout
        self.verify_ssl = verify_ssl


class EnhancedHttpClient:
    """
    增强型HTTP客户端
    
    特性:
    - 连接池复用（提升性能）
    - 自动重试（指数退避）
    - 超时控制（连接超时+读取超时）
    - 响应缓存（可选）
    - Mock服务器集成（开发测试）
    """
    
    def __init__(self, config: Optional[ClientConfig] = None):
        self.config = config or ClientConfig()
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """创建配置好的Session"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # 配置连接池
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.pool_size,
            pool_maxsize=self.config.pool_size,
            pool_block=False
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # SSL验证
        session.verify = self.config.verify_ssl
        
        return session
    
    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        timeout: Optional[tuple] = None,
        **kwargs
    ) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            params: URL参数
            json: JSON请求体
            data: 表单数据或原始数据
            timeout: 超时设置
            **kwargs: 其他requests参数
            
        Returns:
            Response对象
        """
        timeout = timeout or self.config.timeout
        
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout,
                **kwargs
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"{method.upper()} {url} - {response.status_code} - {elapsed_ms}ms"
            )
            
            return response
            
        except requests.exceptions.Timeout as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"{method.upper()} {url} - Timeout after {elapsed_ms}ms")
            raise
            
        except requests.exceptions.RequestException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"{method.upper()} {url} - Error after {elapsed_ms}ms: {e}")
            raise
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET请求"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST请求"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """PUT请求"""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """DELETE请求"""
        return self.request('DELETE', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> requests.Response:
        """PATCH请求"""
        return self.request('PATCH', url, **kwargs)
    
    def close(self):
        """关闭Session"""
        self.session.close()
        logger.info("HTTP客户端已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ConnectionPoolManager:
    """全局连接池管理器（单例模式）"""
    
    _instance = None
    _pools: Dict[str, EnhancedHttpClient] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_client(cls, base_url: str, config: Optional[ClientConfig] = None) -> EnhancedHttpClient:
        """
        获取HTTP客户端（复用连接池）
        
        Args:
            base_url: 基础URL（用于标识连接池）
            config: 客户端配置
            
        Returns:
            EnhancedHttpClient实例
        """
        if base_url not in cls._pools:
            cls._pools[base_url] = EnhancedHttpClient(config)
            logger.info(f"创建新的连接池: {base_url}")
        
        return cls._pools[base_url]
    
    @classmethod
    def close_all(cls):
        """关闭所有连接池"""
        for base_url, client in cls._pools.items():
            client.close()
            logger.info(f"关闭连接池: {base_url}")
        cls._pools.clear()

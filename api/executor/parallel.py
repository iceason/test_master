"""
并发执行优化

支持线程池和进程池
"""

import logging
import concurrent.futures
from typing import List, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """并发执行器"""
    
    def __init__(self, max_workers: int = 10, use_threads: bool = True):
        """
        Args:
            max_workers: 最大并发数
            use_threads: True=线程池（IO密集），False=进程池（CPU密集）
        """
        self.max_workers = max_workers
        self.use_threads = use_threads
        
        if use_threads:
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        else:
            self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
    
    def execute_parallel(
        self,
        func: Callable,
        items: List[Any],
        *args,
        **kwargs
    ) -> List[Any]:
        """
        并发执行任务
        
        Args:
            func: 执行函数
            items: 任务列表
            *args: 额外参数
            **kwargs: 额外关键字参数
            
        Returns:
            结果列表
        """
        logger.info(f"开始并发执行 {len(items)} 个任务，最大并发数: {self.max_workers}")
        start_time = datetime.now()
        
        futures = []
        for item in items:
            future = self.executor.submit(func, item, *args, **kwargs)
            futures.append(future)
        
        results = []
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=300)  # 5分钟超时
                results.append(result)
                completed += 1
                
                if completed % 10 == 0:  # 每10个任务输出一次进度
                    logger.info(f"进度: {completed}/{len(items)}")
                    
            except Exception as e:
                logger.error(f"任务执行异常: {e}", exc_info=True)
                results.append(None)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"并发执行完成，耗时: {duration:.2f}秒")
        
        return results
    
    def close(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)
        logger.info("并发执行器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

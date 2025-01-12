from abc import ABC, abstractmethod
from typing import List, Callable, Optional
import pandas as pd

class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self):
        self.subscribers = set()
        self.strategy_manager = None
        
    def register_strategy_manager(self, strategy_manager) -> None:
        """
        注册策略管理器
        
        Args:
            strategy_manager: 策略管理器实例
        """
        self.strategy_manager = strategy_manager
        
    @abstractmethod
    def subscribe(self, symbols: List[str], callback: Callable) -> None:
        """订阅标的
        
        Args:
            symbols: 标的代码列表
            callback: 数据回调函数
        """
        pass

    @abstractmethod
    def unsubscribe(self, symbols: List[str]) -> None:
        """取消订阅
        
        Args:
            symbols: 标的代码列表
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """开始推送数据"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止推送数据"""
        pass

    @abstractmethod
    def get_current_data(self) -> pd.DataFrame:
        """获取当前数据
        
        Returns:
            包含时间、买价队列、卖价队列的多维DataFrame
        """
        pass

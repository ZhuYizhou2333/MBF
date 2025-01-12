from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from .order import Order, OrderStatus, OrderDirection, OrderType, OrderTimeInForce
from .position import Position
'''
设计理念：
策略专注于下单，平仓逻辑。可获取未平仓订单，持仓信息等。
'''
class BaseStrategy(ABC):
    """策略基类，所有策略都需要继承此类"""
    
    def __init__(self, strategy_id: str, instruments: List[str], params: Optional[Dict] = None):
        """
        初始化策略
        
        Args:
            strategy_id: 策略ID
            instruments: 标的列表
            params: 策略参数
        """
        self.strategy_id = strategy_id
        self.instruments = instruments
        self.orders : List[Order] = []  # 未平仓订单
        self.positions : Dict[str, Position] = {} # 持仓信息
        self.params = params or {}
        
    @abstractmethod
    def on_data(self, data: pd.DataFrame) -> None:
        """
        接收数据回调
        
        Args:
            data: 包含多个标的的最新行情数据
        """
        pass
        
    @abstractmethod
    def on_order(self, order: Order) -> None:
        """
        发送订单回调
        
        Args:
            order: 订单信息
        """
        pass
        
    @abstractmethod
    def on_trade(self, Order: Order) -> None:
        """
        成交回调
        
        Args:
            trade: 成交信息
        """
        pass
        
    def send_order(self, Order: Order) -> None:
        """
        发送订单
        
        Args:
            order: 订单信息
        """
        # 具体实现由策略管理器处理
        pass

    def on_cancel(self, Order:Order)->None:
        """
        撤单回调
        Args:
            order: 订单信息
        """
        pass

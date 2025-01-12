from typing import Dict, List
import pandas as pd
from .base import BaseStrategy
from .order import Order, OrderDirection, OrderType, OrderTimeInForce

class ArbitrageStrategy(BaseStrategy):
    """套利策略"""
    
    def __init__(self, 
                 strategy_id: str,
                 instruments: List[str],
                 spread_threshold: float,
                 **kwargs):
        """
        初始化套利策略
        
        Args:
            strategy_id: 策略ID
            instruments: 标的列表
            spread_threshold: 价差阈值
            kwargs: 其他参数
        """
        super().__init__(strategy_id, instruments, kwargs)
        self.spread_threshold = spread_threshold
        self.spread_history = []
        
    def on_data(self, data: pd.DataFrame) -> None:
        """
        接收数据回调
        
        Args:
            data: 包含多个标的的最新行情数据
        """
        if len(self.instruments) != 2:
            return
            
        # 获取两个标的的最新价格
        instrument1 = self.instruments[0]
        instrument2 = self.instruments[1]
        
        bid1 = data.at[instrument1, 'bidp1']
        ask1 = data.at[instrument1, 'askp1']
        bid2 = data.at[instrument2, 'bidp1']
        ask2 = data.at[instrument2, 'askp1']
        
        # 计算价差
        spread = (bid1 - ask2) if bid1 > ask2 else (bid2 - ask1)
        self.spread_history.append(spread)
        
        # 生成交易指令
        if abs(spread) > self.spread_threshold:
            if spread > 0:
                # 正向套利：买入instrument1，卖出instrument2
                self._execute_positive_arbitrage(instrument1, instrument2, spread)
            else:
                # 反向套利：买入instrument2，卖出instrument1
                self._execute_negative_arbitrage(instrument2, instrument1, -spread)
                
    def _execute_positive_arbitrage(self, instrument1: str, instrument2: str, spread: float) -> None:
        """
        执行正向套利交易
        
        Args:
            instrument1: 标的1（买入）
            instrument2: 标的2（卖出）
            spread: 价差
        """
        # 创建买入订单
        buy_order = Order(
            order_id=f"{self.strategy_id}_buy_{instrument1}",
            instrument=instrument1,
            direction=OrderDirection.BUY,
            price=0,  # 市价单价格为0
            volume=1,
            order_type=OrderType.MARKET,
            time_in_force=OrderTimeInForce.GTC
        )
        
        # 创建卖出订单
        sell_order = Order(
            order_id=f"{self.strategy_id}_sell_{instrument2}",
            instrument=instrument2,
            direction=OrderDirection.SELL,
            price=0,  # 市价单价格为0
            volume=1,
            order_type=OrderType.MARKET,
            time_in_force=OrderTimeInForce.GTC
        )
        
        # 发送订单
        self.send_order(buy_order)
        self.send_order(sell_order)
        
    def _execute_negative_arbitrage(self, instrument1: str, instrument2: str, spread: float) -> None:
        """
        执行反向套利交易
        
        Args:
            instrument1: 标的1（买入）
            instrument2: 标的2（卖出）
            spread: 价差
        """
        # 创建买入订单
        buy_order = Order(
            order_id=f"{self.strategy_id}_buy_{instrument1}",
            instrument=instrument1,
            direction=OrderDirection.BUY,
            price=0,  # 市价单价格为0
            volume=1,
            order_type=OrderType.MARKET,
            time_in_force=OrderTimeInForce.GTC
        )
        
        # 创建卖出订单
        sell_order = Order(
            order_id=f"{self.strategy_id}_sell_{instrument2}",
            instrument=instrument2,
            direction=OrderDirection.SELL,
            price=0,  # 市价单价格为0
            volume=1,
            order_type=OrderType.MARKET,
            time_in_force=OrderTimeInForce.GTC
        )
        
        # 发送订单
        self.send_order(buy_order)
        self.send_order(sell_order)

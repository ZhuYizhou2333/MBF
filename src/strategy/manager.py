from typing import Dict, List, Optional
from datetime import datetime
from .base import BaseStrategy
from .order import Order, OrderDirection, OrderType
from .signal import Signal, SignalType

class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.performance_stats = {
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'max_drawdown': 0.0,
            'start_time': datetime.now()
        }
        
    def register(self, strategy: BaseStrategy) -> bool:
        """
        注册策略
        
        Args:
            strategy: 策略实例
            
        Returns:
            是否注册成功
        """
        if strategy.strategy_id in self.strategies:
            return False
            
        self.strategies[strategy.strategy_id] = strategy
        return True
        
    def unregister(self, strategy_id: str) -> bool:
        """
        注销策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否注销成功
        """
        if strategy_id not in self.strategies:
            return False
            
        del self.strategies[strategy_id]
        return True
        
    def get_strategy(self, strategy_id: str) -> Optional[BaseStrategy]:
        """
        获取策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略实例，如果不存在返回None
        """
        return self.strategies.get(strategy_id)
        
    def broadcast(self, data: Dict) -> None:
        """
        广播数据到所有策略
        
        Args:
            data: 行情数据
        """
        for strategy in self.strategies.values():
            strategy.on_data(data)
            
    def process_signal(self, signal: Signal) -> Order:
        """
        处理交易信号
        
        Args:
            signal: 交易信号
            
        Returns:
            生成的订单
        """
        # 将信号转换为订单
        order = Order(
            order_id=f"ORDER_{signal.instrument}_{signal.signal_type}",
            instrument=signal.instrument,
            direction=OrderDirection.BUY if signal.signal_type in [
                SignalType.LIMIT_BUY, SignalType.MARKET_BUY
            ] else OrderDirection.SELL,
            price=signal.price,
            volume=signal.volume,
            order_type=OrderType.LIMIT if signal.signal_type in [
                SignalType.LIMIT_BUY, SignalType.LIMIT_SELL
            ] else OrderType.MARKET
        )
        
        # 更新性能统计
        self._update_performance_stats(order)
        
        return order
        
    def _update_performance_stats(self, order: Order) -> None:
        """
        更新策略性能统计
        
        Args:
            order: 订单实例
        """
        self.performance_stats['total_trades'] += 1
        
        # 这里可以添加更多性能指标的计算逻辑
        # 例如：盈亏统计、最大回撤等
        
    def get_performance_report(self) -> Dict:
        """
        获取策略性能报告
        
        Returns:
            包含策略性能指标的字典
        """
        report = self.performance_stats.copy()
        report['running_time'] = (datetime.now() - report['start_time']).total_seconds()
        return report

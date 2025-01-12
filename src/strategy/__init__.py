from .base import BaseStrategy
from .arbitrage import ArbitrageStrategy
from .manager import StrategyManager
from .signal import Signal, SignalType
from .order import Order, OrderDirection, OrderType, OrderStatus

__all__ = [
    'BaseStrategy',
    'ArbitrageStrategy',
    'StrategyManager',
    'Signal',
    'SignalType',
    'Order',
    'OrderDirection',
    'OrderType',
    'OrderStatus'
]

def initialize_strategies(data_source):
    """
    初始化策略并注册到数据源
    
    Args:
        data_source: 数据源实例
    """
    # 创建策略管理器
    strategy_manager = StrategyManager()
    
    # 创建套利策略
    arbitrage_strategy = ArbitrageStrategy(
        strategy_id="arbitrage_1",
        instruments=["instrument1", "instrument2"],
        spread_threshold=0.5
    )
    
    # 注册策略
    strategy_manager.register(arbitrage_strategy)
    
    # 将策略管理器注册到数据源
    data_source.register_strategy_manager(strategy_manager)
    
    return strategy_manager

from enum import Enum

class SignalType(Enum):
    """交易信号类型枚举"""
    LIMIT_BUY = "LIMIT_BUY"  # 限价买入
    LIMIT_SELL = "LIMIT_SELL"  # 限价卖出
    MARKET_BUY = "MARKET_BUY"  # 市价买入
    MARKET_SELL = "MARKET_SELL"  # 市价卖出
    STOP_PROFIT = "STOP_PROFIT"  # 价格止盈
    STOP_LOSS = "STOP_LOSS"  # 价格止损
    TIME_PROFIT = "TIME_PROFIT"  # 时间止盈
    TIME_LOSS = "TIME_LOSS"  # 时间止损

class Signal:
    """交易信号类"""
    
    def __init__(self, 
                 signal_type: SignalType,
                 instrument: str,
                 price: float,
                 volume: int,
                 **kwargs):
        """
        初始化交易信号
        
        Args:
            signal_type: 信号类型
            instrument: 标的代码
            price: 价格
            volume: 数量
            kwargs: 其他参数
        """
        self.signal_type = signal_type
        self.instrument = instrument
        self.price = price
        self.volume = volume
        self.extra_params = kwargs
        
    def to_dict(self) -> dict:
        """将信号转换为字典"""
        return {
            "signal_type": self.signal_type.value,
            "instrument": self.instrument,
            "price": self.price,
            "volume": self.volume,
            **self.extra_params
        }

from datetime import datetime
from .order import OrderDirection

class Position:
    def __init__(self, symbol: str, direction: OrderDirection, 
                 volume: float, price: float, timestamp: datetime,
                 commission_rate: float = 0.0005):
        self.symbol = symbol
        self.direction = direction
        self.volume = volume
        self.open_price = price
        self.open_time = timestamp
        self.current_price = price
        self.pnl = 0.0
        self.commission_rate = commission_rate
        self.total_commission = 0.0
        
    def update(self, current_price: float) -> None:
        """更新仓位市值和盈亏"""
        self.current_price = current_price
        self.pnl = (current_price - self.open_price) * self.volume
        if self.direction == OrderDirection.SELL:
            self.pnl = -self.pnl
            
    def close(self) -> float:
        """平仓并返回盈亏"""
        # 计算平仓手续费
        commission = self.current_price * self.volume * self.commission_rate
        self.total_commission += commission
        return self.pnl - commission
    
    def add_commission(self, price: float, volume: float) -> None:
        """添加开仓手续费"""
        commission = price * volume * self.commission_rate
        self.total_commission += commission

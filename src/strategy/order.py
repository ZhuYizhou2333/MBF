from datetime import datetime
from enum import Enum
from typing import Optional

class OrderDirection(Enum):
    """订单方向枚举"""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    """订单类型枚举"""
    LIMIT = "LIMIT"  # 限价单
    MARKET = "MARKET"  # 市价单
    STOP = "STOP"  # 止损/止盈单
    TIME = "TIME"  # 时间单

class OrderTimeInForce(Enum):
    """订单时间指令类型枚举"""
    GTC = "GTC"  # 一直有效直到取消
    DAY = "DAY"  # 当日有效
    GTD = "GTD"  # 指定日期前有效

class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "PENDING"  # 等待成交
    FILLED = "FILLED"  # 完全成交
    CANCELLED = "CANCELLED"  # 已取消
    REJECTED = "REJECTED"  # 已拒绝

class Order:
    """订单类"""
    
    def __init__(self,
                 order_id: str,
                 instrument: str,
                 direction: OrderDirection,
                 price: float,
                 volume: int,
                 order_type: OrderType,
                 create_time: datetime,
                 time_in_force: OrderTimeInForce = OrderTimeInForce.GTC,
                 expire_time: Optional[datetime] = None):
        """
        初始化订单
        
        Args:
            order_id: 订单ID
            instrument: 标的代码
            direction: 买卖方向
            price: 价格
            volume: 数量
            order_type: 订单类型
            time_in_force: 订单有效期类型
            expire_time: 过期时间
            create_time: 订单创建时间
        """
        self.order_id = order_id
        self.instrument = instrument
        self.direction = direction
        self.price = price
        self.volume = volume
        self.order_type = order_type
        self.time_in_force = time_in_force
        self.expire_time = expire_time
        self.create_time = create_time
        self.filled_time: Optional[datetime] = None
        self.filled_price: Optional[float] = None
        self.status = OrderStatus.PENDING
        self.filled_volume = 0
        self.avg_price = 0.0
        
    def to_dict(self) -> dict:
        """将订单转换为字典"""
        return {
            "order_id": self.order_id,
            "instrument": self.instrument,
            "direction": self.direction.value,
            "price": self.price,
            "volume": self.volume,
            "order_type": self.order_type.value,
            "time_in_force": self.time_in_force.value,
            "stop_price": self.stop_price,
            "expire_time": self.expire_time.isoformat() if self.expire_time else None,
            "create_time": self.create_time.isoformat(),
            "filled_time": self.filled_time.isoformat() if self.filled_time else None,
            "filled_price": self.filled_price,
            "status": self.status.value,
            "filled_volume": self.filled_volume,
            "avg_price": self.avg_price
        }

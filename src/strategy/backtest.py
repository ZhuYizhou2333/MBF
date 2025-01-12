from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from .base import BaseStrategy
from .manager import StrategyManager
from .order import Order, OrderStatus, OrderDirection, OrderType, OrderTimeInForce
from .signal import Signal
from .position import Position

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, strategy: BaseStrategy, data: pd.DataFrame):
        """
        初始化回测引擎
        
        Args:
            strategy: 策略实例
            data: 历史数据
        """
        self.strategy = strategy
        self.data = data
        self.orders: List[Order] = []
        self.positions: Dict[str, Position] = {}  # 仓位管理
        self.current_idx = 0
        self.performance_stats = {
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'max_drawdown': 0.0,
            'total_commission': 0.0,  # 新增手续费统计
            'start_time': datetime.now()
        }
        
    def run(self) -> Dict:
        """
        运行回测
        
        Returns:
            回测结果
        """
        for idx in range(len(self.data)):
            self.current_idx = idx
            self._process_tick()
            
        return self._generate_report()
        
    def _process_tick(self) -> None:
        """处理每个tick数据"""
        current_data = self.data.iloc[self.current_idx].to_dict()
        
        # 更新策略
        self.strategy.on_data(current_data)
        
        # 处理订单
        self._process_orders()
        
        # 更新仓位和性能统计
        self._update_performance_stats()
        
    def _process_orders(self) -> None:
        """处理订单"""
        current_data = self.data.iloc[self.current_idx]
        ask_price = current_data['askp1']
        bid_price = current_data['bidp1']
        current_timestamp = pd.to_datetime(current_data['timestamp'])
        
        # 处理待处理订单
        for order in self.orders[:]:
            if order.status == OrderStatus.PENDING:
                # 检查订单是否过期
                if order.time_in_force == OrderTimeInForce.GTC:
                    # 永久有效订单，不检查过期
                    pass
                elif order.time_in_force == OrderTimeInForce.DAY:
                    # 检查是否超过当日有效时间
                    if current_timestamp.date() > order.create_time.date():
                        order.status = OrderStatus.CANCELLED
                        continue
                elif order.time_in_force == OrderTimeInForce.GTD:
                    # 检查是否超过指定到期时间
                    if current_timestamp > order.expire_time:
                        order.status = OrderStatus.CANCELLED
                        continue
                    
                # 处理市价单
                if order.order_type == OrderType.MARKET:
                    if order.direction == OrderDirection.BUY:
                        order.filled_price = ask_price
                    else:
                        order.filled_price = bid_price
                    order.status = OrderStatus.FILLED
                    order.filled_time = current_timestamp

                # 处理限价单
                elif order.order_type == OrderType.LIMIT:
                    if order.direction == OrderDirection.BUY and ask_price <= order.price:
                        order.filled_price = ask_price
                        order.status = OrderStatus.FILLED
                        order.filled_time = current_timestamp
                        order.create_time = current_timestamp if not order.create_time else order.create_time
                    elif order.direction == OrderDirection.SELL and bid_price >= order.price:
                        order.filled_price = bid_price
                        order.status = OrderStatus.FILLED
                        order.filled_time = current_timestamp
                        
                # 处理止盈止损单
                elif order.order_type == OrderType.STOP:
                    # 买单
                    if order.direction == OrderDirection.BUY:
                        if ask_price >= order.price:
                            order.filled_price = ask_price
                            order.status = OrderStatus.FILLED
                            order.filled_time = current_timestamp
                    # 卖单
                    else:
                        if bid_price <= order.price:
                            order.filled_price = bid_price
                            order.status = OrderStatus.FILLED
                            order.filled_time = current_timestamp

            # 处理已成交订单
            if order.status == OrderStatus.FILLED:
                # 处理仓位
                if order.symbol in self.positions:
                    # 已有仓位
                    position = self.positions[order.symbol]
                    if position.direction == order.direction:
                        # 加仓
                        total_volume = position.volume + order.volume
                        position.open_price = (position.open_price * position.volume + 
                                     order.filled_price * order.volume) / total_volume
                        position.volume = total_volume
                        # 计算开仓手续费
                        position.add_commission(order.filled_price, order.volume)
                        self.performance_stats['total_commission'] += order.filled_price * order.volume * self.strategy.commission_rate
                    else:
                        # 平仓或反向开仓
                        if order.volume >= position.volume:
                            # 完全平仓
                            pnl = position.close()
                            self.performance_stats['total_commission'] += position.total_commission
                            del self.positions[order.symbol]
                        else:
                            # 部分平仓
                            pnl = (order.filled_price - position.open_price) * order.volume
                            if position.direction == OrderDirection.SELL:
                                pnl = -pnl
                            position.volume -= order.volume
                            # 计算平仓手续费
                            commission = order.filled_price * order.volume * self.strategy.commission_rate
                            position.total_commission += commission
                            self.performance_stats['total_commission'] += commission
                else:
                    # 新开仓
                    self.positions[order.symbol] = Position(
                        symbol=order.symbol,
                        direction=order.direction,
                        volume=order.volume,
                        price=order.filled_price,
                        timestamp=current_timestamp,
                        commission_rate=self.strategy.commission_rate
                    )
                    # 计算开仓手续费
                    self.positions[order.symbol].add_commission(order.filled_price, order.volume)
                    self.performance_stats['total_commission'] += order.filled_price * order.volume * self.strategy.commission_rate
                    
                # 调用策略的成交回调
                self.strategy.on_order_filled(order)
                # 从待处理订单中移除
                self.orders.remove(order)
                    
    def _update_performance_stats(self) -> None:
        """基于仓位更新性能统计"""
        current_price = self.data.iloc[self.current_idx]['close']
        
        # 更新所有仓位的市值和盈亏
        total_pnl = 0.0
        for position in self.positions.values():
            position.update(current_price)
            total_pnl += position.pnl
            
        # 更新净值曲线
        if not hasattr(self, 'equity_curve'):
            self.equity_curve = [0.0]
        self.equity_curve.append(self.equity_curve[-1] + total_pnl)
        
        # 更新最大回撤
        peak = max(self.equity_curve)
        trough = min(self.equity_curve)
        drawdown = (peak - trough) / peak if peak != 0 else 0
        self.performance_stats['max_drawdown'] = max(
            self.performance_stats['max_drawdown'], drawdown
        )
        
    def _generate_report(self) -> Dict:
        """生成回测报告"""
        report = self.performance_stats.copy()
        
        # 计算总盈亏
        report['total_pnl'] = report.get('total_profit', 0) - report.get('total_loss', 0)
        
        # 计算胜率
        report['win_rate'] = (
            report['win_trades'] / report['total_trades'] 
            if report['total_trades'] > 0 else 0
        )
        
        # 计算盈亏比
        report['profit_factor'] = (
            report.get('total_profit', 0) / report.get('total_loss', 1)
            if report.get('total_loss', 0) > 0 else float('inf')
        )
        
        # 添加运行时间
        report['running_time'] = (datetime.now() - report['start_time']).total_seconds()
        
        return report

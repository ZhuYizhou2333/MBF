from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from ..data_source.realtime_data_source import RealTimeDataSource
from .base import BaseStrategy
from .order import Order, OrderStatus, OrderDirection, OrderType, OrderTimeInForce
from .position import Position

class BacktestEngine:
    """回测引擎"""
    def __init__(self, strategy: BaseStrategy, data_loader:RealTimeDataSource):
        """
        初始化回测引擎
        
        Args:
            strategy: 策略实例
            data: 历史数据
        """
        self.strategy = strategy
        self.current_data = None # 当前时间点的数据
        self.data_loader = data_loader # 数据加载器
        self.performance_stats = {
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'max_drawdown': 0.0,
            'total_commission': 0.0,  # 新增手续费统计
            'start_time': datetime.now()
        }
        self.commission_rate = 0.0005  # 默认手续费率
        
    def run(self) -> Dict:
        """
        运行回测
        
        Returns:
            回测结果
        """
        while True:
            self.current_data = self.data_loader.push_next_tick()
            self._process_tick()
            if self.current_data is None:
                break
        return self._generate_report()
    
    def _process_tick(self) -> None:
        """处理每个tick数据"""
        # 更新策略，生成订单信号
        self.strategy.on_data(self.current_data)
        # 处理订单
        self._process_orders()
        # 更新仓位和性能统计
        self._update_performance_stats()
        
    def _process_orders(self) -> None:
        """处理订单"""
        ask_price = self.current_data['askp1']
        bid_price = self.current_data['bidp1']
        current_timestamp = pd.to_datetime(self.current_data['timestamp'])
        
        # 处理待处理订单
        for order in self.strategy.orders:
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
                if order.instrument in self.strategy.positions:
                    # 已有仓位
                    position = self.strategy.positions[order.instrument]
                    if position.direction == order.direction:
                        # 加仓
                        total_volume = position.volume + order.volume
                        position.open_price = (position.open_price * position.volume + 
                                     order.filled_price * order.volume) / total_volume
                        position.volume = total_volume
                        # 计算开仓手续费
                        position.add_commission(order.filled_price, order.volume)
                        self.performance_stats['total_commission'] += order.filled_price * order.volume * self.commission_rate
                    else:
                        # 平仓或反向开仓
                        if order.volume >= position.volume:
                            # 完全平仓
                            pnl = position.close()
                            self.performance_stats['total_commission'] += position.total_commission
                            del self.strategy.positions[order.instrument]
                        else:
                            # 部分平仓
                            pnl = (order.filled_price - position.open_price) * order.volume
                            if position.direction == OrderDirection.SELL:
                                pnl = -pnl
                            position.volume -= order.volume
                            # 计算平仓手续费
                            commission = order.filled_price * order.volume * self.commission_rate
                            position.total_commission += commission
                            self.performance_stats['total_commission'] += commission
                else:
                    # 新开仓
                    self.strategy.positions[order.instrument] = Position(
                        symbol=order.instrument,
                        direction=order.direction,
                        volume=order.volume,
                        price=order.filled_price,
                        timestamp=current_timestamp,
                        commission_rate=self.commission_rate
                    )
                    # 计算开仓手续费
                    self.strategy.positions[order.instrument].add_commission(order.filled_price, order.volume)
                    self.performance_stats['total_commission'] += order.filled_price * order.volume * self.commission_rate
                    
                # 调用成交回调
                self.strategy.on_trade(order)
                # 从待处理订单中移除
                self.strategy.orders.remove(order)

            elif order.status == OrderStatus.CANCELLED:
                # 调用撤单回调
                self.strategy.on_cancel(order)
                # 从待处理订单中移除
                self.strategy.orders.remove(order)


    def _get_current_price(self, symbol: str) -> float:
        """获取当前标的的最新价格"""
        return (self.current_data[symbol]['askp1'] + self.current_data[symbol]['bidp1']) / 2
                    
    def _update_performance_stats(self) -> None:
        """基于仓位更新性能统计"""
        
        # 更新所有仓位的市值和盈亏
        total_pnl = 0.0
        for position in self.strategy.positions.values():
            position.update(self._get_current_price(position.symbol)) # todo: current_price
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

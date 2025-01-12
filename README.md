MBF's Backtest Framework
# 适用于套利交易策略的回测框架。
套利策略是利用价差回归赚钱的策略。希望建立一个事件驱动的流式计算回测框架，支持多标的套利策略的回测。希望实现以下功能：

1. 支持多标的套利策略回测。
2. 支持通过买卖价实现高频套利回测。
3. 需要流式计算，方便移植实盘交易。

## 框架设计

### 1. 数据源
- 可能存在不同周期的数据，支持自行配置。支持从已有数据源中降采样。
- 数据应至少包含时间列，买价队列，卖价队列。
- 数据源模块负责在指定周期下推送数据。
- 同一时间点所有标的数据同步推送，通过多维dataframe实现。

### 2. 策略
- 逐bar推送各标的买一卖一价，策略模块注册后，根据数据源推送的数据流式计算，并生成交易信号。
- 策略模块应该支持多标的套利策略。
- 策略模块支持的交易信号应该包括：限价买入，限价卖出，市价买入，市价卖出，价格止盈，价格止损，时间止盈，时间止损。
- 策略模块的核心数据类型是订单。

### 3. 回测模拟撮合
- 模拟撮合模块负责接收策略模块的交易信号，并模拟撮合，计算盈亏。
- 本模块根据后续性能瓶颈评估，可以考虑使用C++实现。
- 模拟撮合设计为单利模式，这样可以支持多策略并行回测。

## 缺陷

1. 可能无法支持动态再平衡，因为框架无法实时计算盈亏。（可以通过设置再平衡周期，实现数据播放与模拟撮合并行执行来解决。）

## 独特性

1. 支持多标的策略回测，通过回调函数实现最贴近实盘的回测。
2. 支持多周期数据回测，通过数据源模块实现数据降采样。

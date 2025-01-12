import pandas as pd
from typing import List, Callable, Dict, Tuple
import os
import toml
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from .base import DataSource

class FileDataSource(DataSource):
    """文件数据源实现类"""
    
    def __init__(self, config_path: str = "config/data_source_config.toml", interval: str = '1s'):
        """初始化文件数据源
        
        Args:
            config_path: 配置文件路径
            interval: 数据推送周期
        """
        self.config = self._load_config(config_path)
        self.interval = interval
        self.symbols = []
        self._data = {}
        self._resampled_data = None
        self.start_date = None
        self.end_date = None

    def set_time_range(self, start_date: datetime, end_date: datetime) -> None:
        """设置时间范围
        
        Args:
            start_date: 开始时间
            end_date: 结束时间
        """
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        self.start_date = start_date
        self.end_date = end_date

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")
        return toml.load(config_path)

    def _get_date_range(self) -> List[Tuple[int, int]]:
        """获取需要加载的年份和月份列表"""
        if self.start_date is None or self.end_date is None:
            logger.error("Time range not set")
            raise ValueError("Time range not set")
            
        dates = []
        current = self.start_date.replace(day=1)
        while current <= self.end_date:
            dates.append((current.year, current.month))
            # 移动到下个月
            if current.month == 12:
                current = current.replace(year=current.year+1, month=1)
            else:
                current = current.replace(month=current.month+1)
        return dates

    def _build_file_path(self, symbol: str, year: int, month: int) -> str:
        """构建h5文件路径
        
        Args:
            symbol: 标的代码
            year: 年份
            month: 月份
            
        Returns:
            完整的h5文件路径
        """
        root = self.config['data_source']['root_path']
        exchange = self.config['data_source'].get('default_exchange', 'binance')
        symbol_type = self.config['data_source'].get('default_type', 'spot')
        
        file_name = self.config['data_source']['file_name_format'].format(
            year=year,
            month=f"{month:02d}",
            symbol=symbol
        )
        
        return str(Path(root) / exchange / symbol_type / symbol / file_name)

    def subscribe(self, symbols: List[str], callback: Callable) -> None:
        """订阅标的
        
        Args:
            symbols: 标的代码列表
            callback: 数据回调函数
        """
        if self.start_date is None or self.end_date is None:
            logger.error("Time range must be set before subscribing")
            raise ValueError("Time range must be set before subscribing")
            
        self.symbols = symbols
        self._load_data()
        self._resample_data()

    def unsubscribe(self, symbols: List[str]) -> None:
        """取消订阅
        
        Args:
            symbols: 标的代码列表
        """
        self.symbols = [s for s in self.symbols if s not in symbols]
        for symbol in symbols:
            self._data.pop(symbol, None)

    def get_current_data(self) -> pd.DataFrame:
        """获取当前数据
        
        Returns:
            包含时间、买价队列、卖价队列的多维DataFrame
        """
        return self._resampled_data

    def load_data(self, symbol: str) -> pd.DataFrame:
        """加载指定标的的历史数据
        
        Args:
            symbol: 标的代码
            
        Returns:
            包含时间、买价、卖价的历史数据DataFrame
        """
        if symbol not in self._data:
            logger.warning(f"Data for {symbol} not loaded, loading now")
            self.symbols = [symbol]
            self._load_data()
            
        return self._data.get(symbol, pd.DataFrame())

    def _load_data(self) -> None:
        """加载数据文件"""
        date_ranges = self._get_date_range()
        for symbol in self.symbols:
            dfs = []
            last_month = None
            for year, month in date_ranges:
                file_path = self._build_file_path(symbol, year, month)
                if os.path.exists(file_path):
                    df = pd.read_hdf(file_path)
                    # 转换时间戳
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    # 设置时间索引
                    df.set_index('timestamp', inplace=True)
                    # 过滤时间范围
                    df = df.loc[self.start_date:self.end_date]
                    dfs.append(df)
                    
                    # 检查月份连续性
                    if last_month is not None:
                        expected_month = last_month + 1 if last_month < 12 else 1
                        if month != expected_month:
                            logger.warning(f"Non-continuous month detected for {symbol}: {last_month} -> {month}")
                    last_month = month
                    
            if dfs:
                self._data[symbol] = pd.concat(dfs)
                logger.info(f"Loaded {len(dfs)} months data for {symbol}")
            else:
                logger.warning(f"No data found for {symbol} in specified time range")

    def _resample_data(self) -> None:
        """数据降采样"""
        if self._data:
            resampled = []
            for symbol, df in self._data.items():
                resampled.append(df.resample(self.interval).last())
            self._resampled_data = pd.concat(resampled, axis=1, keys=self.symbols)
            logger.info(f"Resampled data for {len(self.symbols)} symbols")

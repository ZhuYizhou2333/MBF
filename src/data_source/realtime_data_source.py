import pandas as pd
from typing import List, Dict
from streamz import Stream
from .file_data_source import FileDataSource
from .base import DataSource

class RealTimeDataSource(DataSource):
    """实时数据源"""
    
    def __init__(self, file_ds: FileDataSource):
        super().__init__()
        self.file_ds = file_ds
        self.stream = Stream()
        self.data = {}  # 按标的存储数据
        self.current_idx = 0
        
    def load_data(self, symbols: List[str], start_time: pd.Timestamp, end_time: pd.Timestamp):
        """加载并预处理数据"""
        for symbol in symbols:
            df = self.file_ds.load_data(symbol, start_time, end_time) # 从文件数据源加载数据 #! 方法还未实现
            self.data[symbol] = df
            
        # 对齐时间戳
        self.aligned_data = self._align_timestamps()
        
    def _align_timestamps(self) -> pd.DataFrame:
        """对齐所有标的的时间戳，缺失值填充为NaN"""
        all_timestamps = set()
        for symbol, df in self.data.items():
            all_timestamps.update(df.index)
            
        aligned_df = pd.DataFrame(index=sorted(all_timestamps))
        for symbol, df in self.data.items():
            # 使用reindex填充缺失值为NaN
            aligned_df[symbol] = df.reindex(aligned_df.index)
            
        return aligned_df
        
    def start(self):
        """开始推送数据"""
        self.current_idx = 0
        self._push_next_tick()
        
    def _push_next_tick(self):
        """推送下一个tick数据"""
        if self.current_idx >= len(self.aligned_data):
            return
            
        tick_data = self.aligned_data.iloc[self.current_idx].to_dict()
        
        # 更新当前数据
        self.current_data = self._convert_to_dataframe(tick_data)
        
        # 通知订阅者
        for callback in self.subscribers:
            callback(self.current_data)
            
        # 广播数据给策略管理器
        if self.strategy_manager:
            self.strategy_manager.broadcast(self.current_data)
            
        self.stream.emit(tick_data)
        
        self.current_idx += 1
        self._push_next_tick()
        
    def _convert_to_dataframe(self, data: Dict) -> pd.DataFrame:
        """将tick数据转换为DataFrame格式"""
        return pd.DataFrame([data])
        
    def get_stream(self) -> Stream:
        """获取数据流"""
        return self.stream

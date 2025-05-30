"""
数据验证工具
Data validation utilities
"""

import pandas as pd
import numpy as np
from typing import Union, Optional
from functools import wraps
import warnings


def validate_series_input(func):
    """
    Series数据验证装饰器 - 修复类方法参数顺序问题
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 检测是否为类方法 (第一个参数是self)
        if len(args) >= 3 and hasattr(args[0], '__class__'):
            # 类方法: self, data, n, *args
            self_arg, data, n = args[0], args[1], args[2]
            remaining_args = args[3:]
        elif len(args) >= 2:
            # 普通函数: data, n, *args  
            data, n = args[0], args[1]
            remaining_args = args[2:]
        else:
            raise ValueError("函数参数不足，至少需要data和n参数")
        
        # 基础类型检查
        if not isinstance(data, pd.Series):
            raise TypeError("输入数据必须是pandas Series类型")
        
        if not isinstance(n, int) or n <= 0:
            raise ValueError("参数n必须是正整数")
        
        # 数据长度检查
        if len(data) < n:
            raise ValueError(f"数据长度({len(data)})不足，需要至少{n}个观测值")
        
        # 非空数据检查
        non_null_count = data.dropna().shape[0]
        if non_null_count < n:
            warnings.warn(f"非空数据点({non_null_count})少于窗口大小({n})，结果可能不可靠")
        
        return func(*args, **kwargs)
    
    return wrapper


def validate_dataframe_input(data: pd.DataFrame, required_columns: Optional[list] = None) -> bool:
    """
    DataFrame输入验证
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("输入数据必须是pandas DataFrame类型")
    
    if data.empty:
        raise ValueError("输入数据不能为空")
    
    if required_columns:
        missing_cols = [col for col in required_columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"缺少必要的列: {missing_cols}")
    
    return True


def validate_backtest_inputs(signals: pd.Series, 
                           price_data: pd.DataFrame,
                           signal_type: str,
                           assumed_direction: int) -> bool:
    """
    回测输入验证
    """
    # 验证信号数据
    if not isinstance(signals, pd.Series):
        raise TypeError("信号数据必须是pandas Series类型")
    
    if signals.empty:
        raise ValueError("信号数据不能为空")
    
    # 验证价格数据
    validate_dataframe_input(price_data, required_columns=['ValueR', 'GrowthR'])
    
    # 验证信号类型
    valid_signal_types = [
        'historical_high', 'marginal_improvement', 'exceed_expectation',
        'historical_new_high', 'historical_new_low'
    ]
    if signal_type not in valid_signal_types:
        raise ValueError(f"无效的信号类型: {signal_type}. 有效类型: {valid_signal_types}")
    
    # 验证方向参数
    if assumed_direction not in [1, -1]:
        raise ValueError("assumed_direction必须是1或-1")
    
    return True


def check_data_alignment(data1: Union[pd.Series, pd.DataFrame], 
                        data2: Union[pd.Series, pd.DataFrame]) -> bool:
    """
    检查两个数据集的时间索引对齐情况
    """
    if not isinstance(data1.index, pd.DatetimeIndex) or not isinstance(data2.index, pd.DatetimeIndex):
        warnings.warn("建议使用DatetimeIndex以确保正确的时间序列处理")
    
    # 检查时间范围重叠
    overlap_start = max(data1.index.min(), data2.index.min())
    overlap_end = min(data1.index.max(), data2.index.max())
    
    if overlap_start >= overlap_end:
        raise ValueError("数据时间范围无重叠")
    
    overlap_days = (overlap_end - overlap_start).days
    if overlap_days < 365:  # 少于一年的重叠
        warnings.warn(f"数据重叠时间较短: {overlap_days}天")
    
    return True


def sanitize_numeric_series(series: pd.Series, 
                          fill_method: str = 'none') -> pd.Series:
    """
    清理和标准化数值序列
    """
    # 转换为数值类型
    series = pd.to_numeric(series, errors='coerce')
    
    # 处理无穷值
    series = series.replace([np.inf, -np.inf], np.nan)
    
    # 填充缺失值
    if fill_method == 'forward':
        series = series.fillna(method='ffill')
    elif fill_method == 'backward':
        series = series.fillna(method='bfill')
    elif fill_method == 'mean':
        series = series.fillna(series.mean())
    # 'none' 则不填充
    
    return series 
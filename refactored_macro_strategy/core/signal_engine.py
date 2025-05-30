"""
信号生成引擎
Signal generation engine
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable

from ..utils.validators import validate_series_input
from ..config.signal_config import SignalConfig


class SignalEngine:
    """
    精简的信号生成引擎
    合并原有的模式识别功能，减少重复代码
    """
    
    def __init__(self, config: Optional[SignalConfig] = None):
        self.config = config or SignalConfig()
        self.signal_functions = self._register_signal_functions()
    
    def _register_signal_functions(self) -> Dict[str, Callable]:
        """注册信号生成函数"""
        return {
            'historical_high': self._historical_high,
            'marginal_improvement': self._marginal_improvement,
            'exceed_expectation': self._exceed_expectation,
            'historical_new_high': self._historical_new_high,
            'historical_new_low': self._historical_new_low
        }
    
    @validate_series_input
    def _historical_high(self, data: pd.Series, n: int = 12) -> pd.Series:
        """历史高位模式识别"""
        rolling_median = data.rolling(window=n, min_periods=n).median().shift(1)
        signal = data > rolling_median
        return self._apply_validity_mask(signal, data, n + 1)
    
    @validate_series_input
    def _marginal_improvement(self, data: pd.Series, n: int = 3) -> pd.Series:
        """边际改善模式识别"""
        past_n_months = data.rolling(window=n, min_periods=n).mean()
        past_year = data.rolling(window=12, min_periods=12).mean()
        signal = past_n_months > past_year
        return self._apply_validity_mask(signal, data, 12)
    
    @validate_series_input
    def _exceed_expectation(self, data: pd.Series, n: int = 12) -> pd.Series:
        """超预期模式识别"""
        past_mean = data.rolling(window=n, min_periods=n).mean().shift(1)
        signal = data > past_mean
        return self._apply_validity_mask(signal, data, n + 1)
    
    @validate_series_input
    def _historical_new_high(self, data: pd.Series, n: int = 12) -> pd.Series:
        """历史新高模式识别"""
        past_max = data.rolling(window=n, min_periods=n).max().shift(1)
        signal = data > past_max
        return self._apply_validity_mask(signal, data, n + 1)
    
    @validate_series_input
    def _historical_new_low(self, data: pd.Series, n: int = 12) -> pd.Series:
        """历史新低模式识别"""
        past_min = data.rolling(window=n, min_periods=n).min().shift(1)
        signal = data < past_min
        return self._apply_validity_mask(signal, data, n + 1)
    
    def _apply_validity_mask(self, signal: pd.Series, data: pd.Series, required_points: int) -> pd.Series:
        """应用有效性掩码，前面数据不足的部分设为NaN"""
        first_valid_idx = data.first_valid_index()
        if first_valid_idx is not None:
            valid_start_pos = data.index.get_loc(first_valid_idx) + required_points - 1
            if valid_start_pos < len(data):
                # 先转换为compatible类型，然后设置NaN
                signal = signal.astype('object')  # 或使用 'float64' 如果只有数值
                signal.iloc[:valid_start_pos] = np.nan
        return signal
    
    def generate_single_signal(self, data: pd.Series, signal_type: str, n: int) -> pd.Series:
        """
        为单个指标生成指定类型的信号
        """
        if signal_type not in self.signal_functions:
            raise ValueError(f"不支持的信号类型: {signal_type}")
        
        signal_func = self.signal_functions[signal_type]
        return signal_func(data, n)
    
    def generate_signals_for_indicator(self, data: pd.Series, 
                                     signal_types: Optional[List[str]] = None,
                                     custom_params: Optional[Dict[str, int]] = None) -> Dict[str, pd.Series]:
        """
        为单个指标生成多种信号
        """
        if signal_types is None:
            signal_types = self.config.SIGNAL_TYPES
        
        results = {}
        for signal_type in signal_types:
            if custom_params and signal_type in custom_params:
                n = custom_params[signal_type]
            else:
                n = self.config.DEFAULT_SIGNAL_PARAMS[signal_type]
            
            try:
                results[signal_type] = self.generate_single_signal(data, signal_type, n)
            except Exception as e:
                print(f"警告：生成 {signal_type} 信号失败: {e}")
                results[signal_type] = pd.Series(False, index=data.index)
        
        return results
    
    def generate_signals_batch(self, data: pd.DataFrame,
                             signal_types: Optional[List[str]] = None,
                             custom_params: Optional[Dict[str, int]] = None) -> Dict[str, pd.DataFrame]:
        """
        为多个指标批量生成信号
        """
        if signal_types is None:
            signal_types = self.config.SIGNAL_TYPES
        
        results = {}
        
        for signal_type in signal_types:
            signal_matrix = pd.DataFrame(index=data.index)
            
            if custom_params and signal_type in custom_params:
                n = custom_params[signal_type]
            else:
                n = self.config.DEFAULT_SIGNAL_PARAMS[signal_type]
            
            for column in data.columns:
                try:
                    signal_matrix[column] = self.generate_single_signal(data[column], signal_type, n)
                except Exception as e:
                    print(f"警告：指标 {column} 的 {signal_type} 信号生成失败: {e}")
                    signal_matrix[column] = pd.Series(False, index=data.index)
            
            results[signal_type] = signal_matrix
        
        return results
    
    def comprehensive_parameter_test(self, data: pd.DataFrame,
                                   test_params: Optional[Dict[str, List[int]]] = None,
                                   signal_types: Optional[List[str]] = None) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        全面的参数测试 - 精简版
        """
        if test_params is None:
            test_params = self.config.TEST_PARAMS
        
        if signal_types is None:
            signal_types = self.config.SIGNAL_TYPES
        
        print(f"开始全面参数测试...")
        print(f"指标数量: {len(data.columns)}")
        print(f"信号类型: {len(signal_types)}")
        
        all_results = {}
        total_combinations = sum(len(params) for signal_type, params in test_params.items() if signal_type in signal_types)
        current_combination = 0
        
        for signal_type in signal_types:
            if signal_type not in test_params:
                continue
            
            print(f"\n处理信号类型: {signal_type}")
            signal_results = {}
            
            for n in test_params[signal_type]:
                current_combination += 1
                print(f"  参数 N={n} ({current_combination}/{total_combinations})")
                
                param_results = pd.DataFrame(index=data.index)
                
                for column in data.columns:
                    try:
                        param_results[column] = self.generate_single_signal(data[column], signal_type, n)
                    except Exception as e:
                        print(f"    警告：指标 {column} 在 N={n} 时失败: {e}")
                        param_results[column] = pd.Series(False, index=data.index)
                
                signal_results[f'N_{n}'] = param_results
            
            all_results[signal_type] = signal_results
        
        print(f"\n参数测试完成！")
        return all_results
    
    def calculate_signal_strength(self, signals: Dict[str, pd.DataFrame],
                                weights: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """
        计算综合信号强度
        """
        if weights is None:
            weights = self.config.get_signal_weights()
        
        if not signals:
            return pd.DataFrame()
        
        # 获取基础信息
        index = list(signals.values())[0].index
        columns = list(signals.values())[0].columns
        
        composite_signals = pd.DataFrame(index=index, columns=columns, dtype=float)
        
        for column in columns:
            weighted_sum = pd.Series(0.0, index=index)
            
            for signal_type in self.config.SIGNAL_TYPES:
                if signal_type in signals:
                    weight = weights.get(signal_type, 0)
                    signal_values = signals[signal_type][column].astype(float)
                    weighted_sum += weight * signal_values
            
            composite_signals[column] = weighted_sum
        
        return composite_signals 
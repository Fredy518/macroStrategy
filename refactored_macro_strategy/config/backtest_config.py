"""
回测配置
Backtest configuration
"""

from typing import Optional, Literal
from dataclasses import dataclass


@dataclass
class BacktestConfig:
    """回测配置类"""
    
    # 并行处理设置
    enable_parallel: bool = True
    num_processes: Optional[int] = 16
    
    # 回测标的设置
    backtest_target: Literal['value_growth', 'big_small'] = 'value_growth'  # 回测标的选择
    
    # 回测参数
    enable_dual_direction: bool = True  # 是否启用双向测试
    significance_level: float = 0.05  # 显著性水平
    
    # 结果筛选参数
    min_t_statistic: float = 0.0  # 最小t统计量
    top_n_results: int = 3  # 每个指标保留的最佳结果数量
    
    # 滚动窗口配置
    rolling_window_years: int = 5
    rolling_step_months: int = 3
    
    # 交易规则
    signal_delay_months: int = 2  # 信号触发后延迟交易月数
    
    def __post_init__(self):
        """初始化后处理"""
        if self.num_processes is None:
            import os
            self.num_processes = min(os.cpu_count(), 16)
    
    def get_target_columns(self) -> tuple:
        """获取回测标的对应的价格列名"""
        if self.backtest_target == 'value_growth':
            return ('ValueR', 'GrowthR')
        elif self.backtest_target == 'big_small':
            return ('BigR', 'SmallR')
        else:
            raise ValueError(f"不支持的回测标的: {self.backtest_target}")
    
    def get_trading_logic_description(self) -> str:
        """获取交易逻辑说明"""
        if self.backtest_target == 'value_growth':
            return """
            价值/成长回测逻辑:
            - 方向=+1: 信号TRUE时做多ValueR做空GrowthR，信号FALSE时做空ValueR做多GrowthR
            - 方向=-1: 信号TRUE时做空ValueR做多GrowthR，信号FALSE时做多ValueR做空GrowthR
            - 信号NaN: 无仓位
            - 交易时机: 信号触发后第二个月月初
            """
        elif self.backtest_target == 'big_small':
            return """
            大小盘回测逻辑:
            - 方向=+1: 信号TRUE时做多BigR做空SmallR，信号FALSE时做空BigR做多SmallR  
            - 方向=-1: 信号TRUE时做空BigR做多SmallR，信号FALSE时做多BigR做空SmallR
            - 信号NaN: 无仓位
            - 交易时机: 信号触发后第二个月月初
            """
        else:
            return "未知的回测标的类型"
    
    def get_position_direction_rules(self) -> dict:
        """获取仓位方向规则"""
        if self.backtest_target == 'value_growth':
            return {
                'direction_1': {
                    'signal_true': '做多ValueR做空GrowthR',
                    'signal_false': '做空ValueR做多GrowthR'
                },
                'direction_-1': {
                    'signal_true': '做空ValueR做多GrowthR', 
                    'signal_false': '做多ValueR做空GrowthR'
                }
            }
        elif self.backtest_target == 'big_small':
            return {
                'direction_1': {
                    'signal_true': '做多BigR做空SmallR',
                    'signal_false': '做空BigR做多SmallR'
                },
                'direction_-1': {
                    'signal_true': '做空BigR做多SmallR', 
                    'signal_false': '做多BigR做空SmallR'
                }
            }
        else:
            return {} 
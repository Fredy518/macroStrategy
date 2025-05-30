"""
导出配置
Export configuration
"""

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
import os


@dataclass
class ExportConfig:
    """导出配置类"""
    
    # 输出目录
    output_dir: str = "signal_test_results"
    
    # Excel文件配置
    excel_engine: str = "openpyxl"
    
    # 回测标的类型 (用于文件命名)
    backtest_target: Optional[Literal['value_growth', 'big_small']] = None
    
    # 导出的列
    export_columns: List[str] = None
    
    # 聚合函数
    agg_functions: List[str] = None
    
    # 基础文件名
    base_backtest_filename: str = "backtest_results_refactored"
    base_performance_filename: str = "parameter_performance_refactored"
    base_stability_filename: str = "rolling_stability_refactored"
    
    def __post_init__(self):
        """初始化后处理"""
        if self.export_columns is None:
            self.export_columns = [
                'information_ratio', 'win_rate', 'monthly_avg_return', 
                't_statistic', 'p_value', 'df_ttest', 'is_significant_0.05',
                'total_return', 'annualized_return', 'volatility', 'max_drawdown',
                'assumed_direction', 'original_indicator_direction'
            ]
        
        if self.agg_functions is None:
            self.agg_functions = ['mean', 'std', 'max', 'min', 'count']
    
    def get_target_suffix(self) -> str:
        """获取回测标的对应的文件名后缀"""
        if self.backtest_target == 'value_growth':
            return "_value_growth"
        elif self.backtest_target == 'big_small':
            return "_big_small"
        else:
            return ""
    
    def ensure_output_dir(self) -> str:
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        return self.output_dir
    
    def get_backtest_filepath(self) -> str:
        """获取回测结果文件路径"""
        suffix = self.get_target_suffix()
        filename = f"{self.base_backtest_filename}{suffix}.xlsx"
        return os.path.join(self.ensure_output_dir(), filename)
    
    def get_performance_filepath(self) -> str:
        """获取性能分析文件路径"""
        suffix = self.get_target_suffix()
        filename = f"{self.base_performance_filename}{suffix}.xlsx"
        return os.path.join(self.ensure_output_dir(), filename)
    
    def get_stability_filepath(self) -> str:
        """获取稳定性分析文件路径"""
        suffix = self.get_target_suffix()
        filename = f"{self.base_stability_filename}{suffix}.xlsx"
        return os.path.join(self.ensure_output_dir(), filename)
    
    def get_export_sheets_config(self) -> Dict[str, Dict]:
        """获取导出工作表配置 - 精简版，移除无意义的汇总"""
        target_desc = ""
        if self.backtest_target == 'value_growth':
            target_desc = "(价值/成长)"
        elif self.backtest_target == 'big_small':
            target_desc = "(大盘/小盘)"
        
        return {
            'Full_Results': {
                'description': f'完整回测结果{target_desc}',
                'columns': self.export_columns
            },
            'Filtered_Best': {
                'description': f'筛选后的优质组合{target_desc}',
                'columns': self.export_columns
            },
            'Significant_Positive': {
                'description': f'显著且正向的组合{target_desc}',
                'filter': 'significant_positive'
            },
            'Top_Positive_IR': {
                'description': f'正向t统计量的最佳IR{target_desc}',
                'sort_by': 'information_ratio',
                'filter': 'positive_t',
                'top_n': 50
            }
        } 
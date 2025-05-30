"""
结果处理器
Result processor for backtest analysis and export
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os

from ..config.export_config import ExportConfig


class ResultProcessor:
    """
    统一的结果处理器 - 精简导出和分析流程
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
    
    def filter_best_significant_results(self, backtest_df: pd.DataFrame) -> pd.DataFrame:
        """筛选每个指标的最佳显著组合 - 精简版"""
        if backtest_df.empty:
            print("输入的回测结果为空")
            return pd.DataFrame()
        
        required_columns = ['indicator', 'is_significant_0.05', 'information_ratio', 't_statistic']
        missing_columns = [col for col in required_columns if col not in backtest_df.columns]
        if missing_columns:
            print(f"缺少必要的列: {missing_columns}")
            return pd.DataFrame()
        
        print("开始筛选最佳显著组合...")
        
        # 筛选统计显著且t>0的结果
        significant_positive_results = backtest_df[
            (backtest_df['is_significant_0.05'] == 1) & 
            (backtest_df['t_statistic'] > 0)
        ].copy()
        
        if significant_positive_results.empty:
            print("警告: 没有统计显著且t>0的结果")
            return pd.DataFrame()
        
        print(f"筛选前: {len(backtest_df)} 个组合")
        print(f"显著且t>0: {len(significant_positive_results)} 个组合")
        
        # 按指标分组，选择信息比率最高的组合
        best_combinations = []
        for indicator_name, group in significant_positive_results.groupby('indicator'):
            best_combination = group.loc[group['information_ratio'].idxmax()]
            best_combinations.append(best_combination)
        
        if not best_combinations:
            return pd.DataFrame()
        
        filtered_df = pd.DataFrame(best_combinations)
        print(f"筛选后: {len(filtered_df)} 个组合 (每个指标的最佳)")
        
        return filtered_df
    
    def analyze_results(self, backtest_df: pd.DataFrame, 
                       filtered_df: Optional[pd.DataFrame] = None) -> None:
        """分析回测结果 - 只关注显著且正向的结果"""
        if backtest_df.empty:
            print("无回测结果可分析")
            return
        
        print("="*80)
        print("回测结果分析 (显著正向结果导向)")
        print("="*80)
        
        # 基础统计
        print(f"总回测组合: {len(backtest_df)}")
        print(f"指标数量: {backtest_df['indicator'].nunique()}")
        print(f"信号类型数量: {backtest_df['signal_type'].nunique()}")
        
        if 'assumed_direction' in backtest_df.columns:
            print(f"测试方向数量: {backtest_df['assumed_direction'].nunique()}")
        
        # 核心指标统计
        if 'information_ratio' in backtest_df.columns:
            print(f"\n信息比率统计:")
            print(f"  平均值: {backtest_df['information_ratio'].mean():.4f}")
            print(f"  标准差: {backtest_df['information_ratio'].std():.4f}")
            print(f"  最大值: {backtest_df['information_ratio'].max():.4f}")
            print(f"  最小值: {backtest_df['information_ratio'].min():.4f}")
        
        # 显著性分析 - 重点关注
        if 'is_significant_0.05' in backtest_df.columns and 't_statistic' in backtest_df.columns:
            significant_positive = backtest_df[
                (backtest_df['is_significant_0.05'] == 1) & 
                (backtest_df['t_statistic'] > 0)
            ]
            print(f"\n*** 关键发现：显著且正向的宏观事件组合 ***")
            print(f"  显著且t>0的组合: {len(significant_positive)} ({len(significant_positive)/len(backtest_df)*100:.1f}%)")
            
            if len(significant_positive) > 0:
                print(f"  这些组合的平均信息比率: {significant_positive['information_ratio'].mean():.4f}")
                print(f"  涉及指标数量: {significant_positive['indicator'].nunique()}")
                
                # 按指标显示最佳组合
                print(f"\n按指标的最佳显著组合:")
                for indicator in significant_positive['indicator'].unique():
                    indicator_best = significant_positive[significant_positive['indicator'] == indicator].nlargest(1, 'information_ratio')
                    if not indicator_best.empty:
                        row = indicator_best.iloc[0]
                        print(f"  {indicator}: {row['signal_type']} (Dir:{row['assumed_direction']}, IR:{row['information_ratio']:.4f})")
        
        # Top表现者 - 只显示正向的
        if 'information_ratio' in backtest_df.columns and 't_statistic' in backtest_df.columns:
            positive_t_results = backtest_df[backtest_df['t_statistic'] > 0]
            if not positive_t_results.empty:
                print(f"\nTop 5 正向t统计量的信息比率:")
                top_5 = positive_t_results.nlargest(5, 'information_ratio')
                for i, (_, row) in enumerate(top_5.iterrows(), 1):
                    print(f"  {i}. {row.get('indicator','N/A')} - {row.get('signal_type','N/A')} "
                          f"(Dir: {row.get('assumed_direction','N/A')}, IR: {row.get('information_ratio',0):.4f})")
        
        # 筛选结果分析
        if filtered_df is not None and not filtered_df.empty:
            print(f"\n*** 筛选后的优质组合 ***")
            print(f"  筛选后组合数: {len(filtered_df)}")
            print(f"  筛选率: {len(filtered_df)/len(backtest_df)*100:.1f}%")
            if 'information_ratio' in filtered_df.columns:
                print(f"  筛选后平均信息比率: {filtered_df['information_ratio'].mean():.4f}")
            print(f"  覆盖指标数: {filtered_df['indicator'].nunique()}")
    
    def export_results(self, backtest_df: pd.DataFrame,
                      filtered_df: Optional[pd.DataFrame] = None) -> str:
        """导出结果到Excel - 精简版"""
        if backtest_df.empty:
            print("无结果可导出")
            return ""
        
        try:
            filepath = self.config.get_backtest_filepath()
            print(f"\n导出结果到: {filepath}")
            
            with pd.ExcelWriter(filepath, engine=self.config.excel_engine) as writer:
                # 完整结果
                backtest_df.to_excel(writer, sheet_name='Full_Results', index=False)
                
                # 筛选结果
                if filtered_df is not None and not filtered_df.empty:
                    filtered_df.to_excel(writer, sheet_name='Filtered_Best', index=False)
                
                # 汇总分析
                if not backtest_df.empty:
                    self._export_summary_sheets(writer, backtest_df)
                
                # 如果有筛选结果，也导出其汇总
                if filtered_df is not None and not filtered_df.empty:
                    self._export_filtered_summary_sheets(writer, filtered_df)
            
            print(f"导出完成: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"导出失败: {e}")
            return ""
    
    def _export_summary_sheets(self, writer: pd.ExcelWriter, df: pd.DataFrame) -> None:
        """导出汇总工作表 - 只保留有价值的分析"""
        
        # 只导出显著且正向的结果汇总
        if all(col in df.columns for col in ['is_significant_0.05', 't_statistic', 'information_ratio']):
            significant_positive = df[
                (df['is_significant_0.05'] == 1) & 
                (df['t_statistic'] > 0)
            ]
            if not significant_positive.empty:
                significant_positive.to_excel(writer, sheet_name='Significant_Positive', index=False)
        
        # Top表现者（只要t>0的）
        if all(col in df.columns for col in ['information_ratio', 't_statistic']):
            positive_t_results = df[df['t_statistic'] > 0]
            if not positive_t_results.empty:
                top_performers = positive_t_results.nlargest(50, 'information_ratio')
                top_performers.to_excel(writer, sheet_name='Top_Positive_IR', index=False)
    
    def _export_filtered_summary_sheets(self, writer: pd.ExcelWriter, filtered_df: pd.DataFrame) -> None:
        """导出筛选结果的汇总工作表 - 精简版"""
        
        # 筛选结果的整体统计
        if 'information_ratio' in filtered_df.columns:
            stats_data = {
                'Metric': ['Count', 'Mean_IR', 'Std_IR', 'Max_IR', 'Min_IR', 'Indicators_Count'],
                'Value': [
                    len(filtered_df),
                    filtered_df['information_ratio'].mean(),
                    filtered_df['information_ratio'].std(),
                    filtered_df['information_ratio'].max(),
                    filtered_df['information_ratio'].min(),
                    filtered_df['indicator'].nunique() if 'indicator' in filtered_df.columns else 0
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Filtered_Summary', index=False)
    
    def compare_analysis(self, original_df: pd.DataFrame, 
                        filtered_df: pd.DataFrame) -> None:
        """对比分析筛选前后的结果"""
        if original_df.empty and filtered_df.empty:
            print("原始和筛选后的结果都为空")
            return
        
        print("="*80)
        print("筛选前后对比分析")
        print("="*80)
        
        # 数量对比
        print(f"原始组合数量: {len(original_df)}")
        print(f"筛选后组合数量: {len(filtered_df)}")
        print(f"保留比例: {len(filtered_df)/len(original_df)*100:.1f}%" if len(original_df) > 0 else "保留比例: N/A")
        
        # 信息比率对比
        if 'information_ratio' in original_df.columns and 'information_ratio' in filtered_df.columns:
            print(f"\n信息比率对比:")
            print(f"原始平均: {original_df['information_ratio'].mean():.4f}")
            print(f"筛选后平均: {filtered_df['information_ratio'].mean():.4f}")
            improvement = filtered_df['information_ratio'].mean() - original_df['information_ratio'].mean()
            print(f"提升幅度: {improvement:.4f}")
        
        # 指标覆盖对比
        if 'indicator' in original_df.columns and 'indicator' in filtered_df.columns:
            print(f"\n指标覆盖对比:")
            print(f"原始涉及指标: {original_df['indicator'].nunique()}")
            print(f"筛选后保留指标: {filtered_df['indicator'].nunique()}")
            coverage = filtered_df['indicator'].nunique() / original_df['indicator'].nunique() * 100
            print(f"指标覆盖率: {coverage:.1f}%")
    
    def generate_performance_report(self, backtest_df: pd.DataFrame) -> Dict[str, any]:
        """生成性能报告摘要"""
        if backtest_df.empty:
            return {}
        
        report = {
            'basic_stats': {
                'total_combinations': len(backtest_df),
                'unique_indicators': backtest_df['indicator'].nunique() if 'indicator' in backtest_df.columns else 0,
                'unique_signal_types': backtest_df['signal_type'].nunique() if 'signal_type' in backtest_df.columns else 0
            }
        }
        
        # 信息比率统计
        if 'information_ratio' in backtest_df.columns:
            ir_stats = backtest_df['information_ratio'].describe()
            report['information_ratio_stats'] = {
                'mean': float(ir_stats['mean']),
                'std': float(ir_stats['std']),
                'min': float(ir_stats['min']),
                'max': float(ir_stats['max']),
                'median': float(ir_stats['50%'])
            }
        
        # 显著性统计
        if 'is_significant_0.05' in backtest_df.columns and 't_statistic' in backtest_df.columns:
            significant_positive = backtest_df[
                (backtest_df['is_significant_0.05'] == 1) & 
                (backtest_df['t_statistic'] > 0)
            ]
            report['significance_stats'] = {
                'significant_positive_count': len(significant_positive),
                'significant_positive_ratio': len(significant_positive) / len(backtest_df),
                'avg_t_statistic': float(significant_positive['t_statistic'].mean()) if len(significant_positive) > 0 else 0
            }
        
        return report 
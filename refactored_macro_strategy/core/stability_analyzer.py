"""
稳定性分析器

基于排名的稳定性分析，关注参数组合在不同时间窗口中的稳定表现
"""

import os
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from ..config.export_config import ExportConfig


@dataclass
class StabilityConfig:
    """稳定性分析配置"""
    top_k_per_window: int = 15  # 每个窗口保留的显著组合数量（仅当enable_top_k_limit=True时生效）
    enable_top_k_limit: bool = False  # 是否启用TopK限制，False表示保留所有显著组合
    min_appearance_windows: int = 8  # 最少出现窗口数
    significance_threshold: float = 0.05  # 显著性阈值
    high_stability_threshold: float = 0.5  # 高稳定性阈值，用于筛选和推荐组合
    ranking_weight: float = 0.2  # 表现一致性权重 (基于全窗口IR中位数稳定性)
    significance_weight: float = 0.2  # 显著性一致率权重 (显著窗口占比)
    performance_weight: float = 0.2  # 性能稳定性权重 (基于全窗口IR变异系数)
    absolute_performance_weight: float = 0.4  # 绝对表现权重 (基于全窗口IR水平)
    
    def __post_init__(self):
        """验证权重总和为1"""
        total_weight = (self.ranking_weight + self.significance_weight + 
                       self.performance_weight + self.absolute_performance_weight)
        # import pdb; pdb.set_trace()
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(f"权重总和必须为1.0，当前为: {total_weight}")
        
    def get_weights_summary(self) -> str:
        """获取权重配置摘要"""
        return (f"权重配置: 表现一致性={self.ranking_weight:.2f}, "
                f"显著性一致率={self.significance_weight:.2f}, "
                f"性能稳定性={self.performance_weight:.2f}, "
                f"绝对表现={self.absolute_performance_weight:.2f}")

    def get_selection_summary(self) -> str:
        """获取组合筛选配置摘要"""
        if self.enable_top_k_limit:
            return f"筛选策略: 每窗口保留Top {self.top_k_per_window} 显著组合"
        else:
            return "筛选策略: 保留所有显著组合（基于统计显著性筛选）"


class RankingStabilityAnalyzer:
    """
    基于排名的稳定性分析器
    
    核心思想：
    1. 关注统计显著组合的排名变化，而非绝对最优状态
    2. 评估参数组合在不同窗口中的稳定表现
    3. 识别"持续优秀"的组合，而非"偶尔最优"的组合
    """
    
    def __init__(self, config: Optional[StabilityConfig] = None, 
                 export_config: Optional[ExportConfig] = None):
        self.config = config or StabilityConfig()
        self.export_config = export_config or ExportConfig()
    
    def extract_significant_combinations_per_window(self, 
                                            rolling_results_df: pd.DataFrame) -> pd.DataFrame:
        """
        从滚动结果中提取每个窗口的显著组合
        
        参数:
            rolling_results_df: 滚动回测的原始结果
            
        返回:
            包含每个窗口显著组合的DataFrame
        """
        if rolling_results_df.empty:
            return pd.DataFrame()
        
        if self.config.enable_top_k_limit:
            print(f"开始提取每个窗口的 Top {self.config.top_k_per_window} 个显著组合...")
        else:
            print(f"开始提取每个窗口的所有显著组合...")
        
        # 确保必要的列存在
        required_cols = ['window_id', 'indicator', 'signal_type', 'parameter_n', 
                        'assumed_direction', 'is_significant_0.05', 't_statistic', 
                        'information_ratio']
        
        missing_cols = [col for col in required_cols if col not in rolling_results_df.columns]
        if missing_cols:
            raise ValueError(f"缺少必要的列: {missing_cols}")
        
        selected_results = []
        
        # 按窗口分组处理
        for window_id, window_data in rolling_results_df.groupby('window_id'):
            # 筛选显著且t>0的组合
            significant_positive = window_data[
                (window_data['is_significant_0.05'] == 1) & 
                (window_data['t_statistic'] > 0)
            ].copy()
            
            if significant_positive.empty:
                continue
            
            # 按信息比率排序
            significant_positive = significant_positive.sort_values(
                'information_ratio', ascending=False
            ).copy()
            
            # 根据配置决定是否限制数量
            if self.config.enable_top_k_limit:
                # 取前K个
                selected_in_window = significant_positive.head(self.config.top_k_per_window).copy()
            else:
                # 保留所有显著组合
                selected_in_window = significant_positive.copy()
            
            # 添加窗口内排名
            selected_in_window['rank_in_window'] = range(1, len(selected_in_window) + 1)
            
            selected_results.append(selected_in_window)
        
        if not selected_results:
            print("警告: 没有窗口包含显著的正向组合")
            return pd.DataFrame()
        
        final_results = pd.concat(selected_results, ignore_index=True)
        
        print(f"提取完成: 共 {len(final_results)} 条记录，"
              f"涉及 {final_results['window_id'].nunique()} 个窗口")
        
        return final_results
    
    def calculate_ranking_stability(self, significant_df: pd.DataFrame, 
                                   rolling_results_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算每个参数组合的排名稳定性
        
        参数:
            significant_df: 包含每个窗口显著组合的DataFrame
            rolling_results_df: 原始滚动回测结果，用于计算全窗口平均IR
            
        返回:
            包含稳定性指标的DataFrame
        """
        if significant_df.empty:
            return pd.DataFrame()
        
        print("开始计算排名稳定性...")
        
        # 创建组合唯一标识
        significant_df['combination_id'] = (
            significant_df['indicator'].astype(str) + '_' +
            significant_df['signal_type'].astype(str) + '_' +
            significant_df['parameter_n'].astype(str) + '_' +
            significant_df['assumed_direction'].astype(str)
        )
        
        # 创建原始数据的组合标识（用于计算全窗口平均IR）
        rolling_results_df['combination_id'] = (
            rolling_results_df['indicator'].astype(str) + '_' +
            rolling_results_df['signal_type'].astype(str) + '_' +
            rolling_results_df['parameter_n'].astype(str) + '_' +
            rolling_results_df['assumed_direction'].astype(str)
        )
        
        # 计算每个组合在所有窗口中的平均IR（包括不显著的窗口）
        all_window_ir_stats = rolling_results_df.groupby('combination_id').agg({
            'information_ratio': ['mean', 'std', 'count']
        }).reset_index()
        all_window_ir_stats.columns = ['combination_id', 'all_window_ir_mean', 'all_window_ir_std', 'all_window_count']
        
        print(f"计算全窗口IR统计: 涉及 {len(all_window_ir_stats)} 个组合，"
              f"平均每组合 {all_window_ir_stats['all_window_count'].mean():.1f} 个窗口")
        
        # 第一步：收集所有符合条件组合的全窗口平均IR，用于计算绝对表现得分  
        valid_combo_ids = set()
        for combo_id, combo_data in significant_df.groupby('combination_id'):
            total_windows = combo_data['window_id'].nunique()
            if total_windows >= self.config.min_appearance_windows:
                valid_combo_ids.add(combo_id)
        
        # 获取符合条件组合的全窗口IR统计
        valid_all_window_ir = all_window_ir_stats[
            all_window_ir_stats['combination_id'].isin(valid_combo_ids)
        ]['all_window_ir_mean'].values
        
        # 计算全窗口IR的分布统计，用于标准化绝对表现得分
        if len(valid_all_window_ir) > 0:
            ir_mean_global = np.mean(valid_all_window_ir)
            ir_std_global = np.std(valid_all_window_ir)
            ir_min_global = np.min(valid_all_window_ir)
            ir_max_global = np.max(valid_all_window_ir)
            print(f"全局全窗口IR统计: 均值={ir_mean_global:.3f}, 标准差={ir_std_global:.3f}, "
                  f"范围=[{ir_min_global:.3f}, {ir_max_global:.3f}]")
        else:
            ir_mean_global = ir_std_global = 0
            ir_min_global = ir_max_global = 0
        
        stability_results = []
        
        # 第二步：按组合分组分析
        for combo_id, combo_data in significant_df.groupby('combination_id'):
            combo_info = combo_data.iloc[0]  # 获取组合基本信息
            
            # 基本统计
            total_windows = combo_data['window_id'].nunique()
            total_possible_windows = significant_df['window_id'].nunique()
            
            # 如果出现窗口数太少，跳过
            if total_windows < self.config.min_appearance_windows:
                continue
            
            # 获取该组合的全窗口IR统计
            combo_all_window_stats = all_window_ir_stats[
                all_window_ir_stats['combination_id'] == combo_id
            ]
            if combo_all_window_stats.empty:
                print(f"警告: 组合 {combo_id} 在原始数据中未找到，跳过")
                continue
            
            all_window_ir_mean = combo_all_window_stats['all_window_ir_mean'].iloc[0]
            all_window_ir_std = combo_all_window_stats['all_window_ir_std'].iloc[0]
            all_window_count = combo_all_window_stats['all_window_count'].iloc[0]
            
            # 1. 表现一致性分析 (基于全窗口IR) *** 改为全窗口一致性 ***
            # 计算该组合全窗口IR相对稳定性，使用与performance_stability不同的方法
            # 这里使用基于中位数的稳定性评估，更关注极值的影响
            if all_window_count >= 3:
                # 获取该组合在所有窗口的IR值
                combo_all_window_ir = rolling_results_df[
                    rolling_results_df['combination_id'] == combo_id
                ]['information_ratio'].values
                
                if len(combo_all_window_ir) > 0:
                    ir_median = np.median(combo_all_window_ir)
                    # 计算所有窗口IR与中位数的绝对偏差的中位数 (MAD - Median Absolute Deviation)
                    mad = np.median(np.abs(combo_all_window_ir - ir_median))
                    # 标准化MAD相对于中位数的比例
                    mad_ratio = mad / abs(ir_median) if abs(ir_median) > 1e-6 else float('inf')
                    ranking_stability_score = 1 / (1 + mad_ratio) if mad_ratio != float('inf') else 0
                else:
                    ranking_stability_score = 0
            else:
                ranking_stability_score = 0
            
            # 保留显著窗口排名统计用于输出和分析
            ranks = combo_data['rank_in_window'].values
            rank_mean = np.mean(ranks)
            rank_std = np.std(ranks)
            rank_cv = rank_std / rank_mean if rank_mean > 0 else float('inf')
            
            # 2. 显著性一致率
            significance_consistency = total_windows / total_possible_windows
            
            # 3. 性能稳定性 (基于全窗口IR) *** 修改为全窗口 ***
            all_window_ir_cv = all_window_ir_std / abs(all_window_ir_mean) if abs(all_window_ir_mean) > 1e-6 else float('inf')
            
            performance_stability_score = 1 / (1 + all_window_ir_cv) if all_window_ir_cv != float('inf') else 0
            
            # 保留显著窗口IR统计用于输出和其他分析
            significant_ir_values = combo_data['information_ratio'].values
            significant_ir_mean = np.mean(significant_ir_values)
            significant_ir_std = np.std(significant_ir_values)
            significant_ir_cv = significant_ir_std / abs(significant_ir_mean) if abs(significant_ir_mean) > 1e-6 else float('inf')
            
            # 4. 绝对表现得分 (基于全窗口IR)
            if ir_std_global > 0:
                # 使用全窗口平均IR进行标准化：(全窗口IR - 全局均值) / 全局标准差
                ir_z_score = (all_window_ir_mean - ir_mean_global) / ir_std_global
                # 将z-score映射到[0,1]，使用sigmoid函数
                absolute_performance_score = 1 / (1 + np.exp(-ir_z_score))
            else:
                # 如果没有方差，使用简单的线性映射
                if ir_max_global > ir_min_global:
                    absolute_performance_score = (all_window_ir_mean - ir_min_global) / (ir_max_global - ir_min_global)
                else:
                    absolute_performance_score = 0.5  # 所有IR相同时给中等得分
            
            # 5. 综合稳定性得分 (四维加权)
            overall_stability_score = (
                self.config.ranking_weight * ranking_stability_score +
                self.config.significance_weight * significance_consistency +
                self.config.performance_weight * performance_stability_score +
                self.config.absolute_performance_weight * absolute_performance_score
            )
            
            # 6. 其他统计信息
            best_rank = np.min(ranks)
            worst_rank = np.max(ranks)
            median_rank = np.median(ranks)
            
            stability_results.append({
                'combination_id': combo_id,
                'indicator': combo_info['indicator'],
                'signal_type': combo_info['signal_type'],
                'parameter_n': combo_info['parameter_n'],
                'assumed_direction': combo_info['assumed_direction'],
                
                # 出现频率
                'appearance_windows': total_windows,
                'total_possible_windows': total_possible_windows,
                'appearance_rate': significance_consistency,
                
                # 排名统计
                'rank_mean': rank_mean,
                'rank_std': rank_std,
                'rank_cv': rank_cv,
                'best_rank': best_rank,
                'worst_rank': worst_rank,
                'median_rank': median_rank,
                
                # 性能统计
                'ir_mean': significant_ir_mean,
                'ir_std': significant_ir_std,
                'ir_cv': significant_ir_cv,
                'ir_min': np.min(significant_ir_values),
                'ir_max': np.max(significant_ir_values),
                
                # 全窗口IR统计 (新增)
                'all_window_ir_mean': all_window_ir_mean,
                'all_window_ir_std': all_window_ir_std, 
                'all_window_count': all_window_count,
                
                # 稳定性得分
                'ranking_stability_score': ranking_stability_score,
                'significance_consistency_score': significance_consistency,
                'performance_stability_score': performance_stability_score,
                'absolute_performance_score': absolute_performance_score,
                'overall_stability_score': overall_stability_score,
                
                # t统计量平均值
                't_statistic_mean': combo_data['t_statistic'].mean(),
                't_statistic_std': combo_data['t_statistic'].std(),
            })
        
        stability_df = pd.DataFrame(stability_results)
        
        if not stability_df.empty:
            # 按综合稳定性得分排序
            stability_df = stability_df.sort_values('overall_stability_score', ascending=False)
            print(f"稳定性分析完成: 共分析 {len(stability_df)} 个参数组合")
        else:
            print("警告: 没有满足条件的组合")
        
        return stability_df
    
    def generate_stability_insights(self, stability_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        生成稳定性洞察报告
        
        参数:
            stability_df: 稳定性分析结果
            
        返回:
            包含各种洞察的字典
        """
        if stability_df.empty:
            return {}
        
        print("生成稳定性洞察报告...")
        
        insights = {}
        
        # 1. 顶级稳定组合 (综合得分超过阈值的所有组合)
        high_stability_threshold = self.config.high_stability_threshold
        top_stable_combinations = stability_df[
            stability_df['overall_stability_score'] > high_stability_threshold
        ].copy()
        
        print(f"综合得分超过{high_stability_threshold}的组合数量: {len(top_stable_combinations)}")
        insights['top_stable_combinations'] = top_stable_combinations
        
        # 1.1 最佳组合 (每个指标的最高得分组合，且综合得分超过阈值)
        best_combinations_per_indicator = []
        
        # 只考虑得分超过阈值的组合
        qualified_combinations = stability_df[
            stability_df['overall_stability_score'] > high_stability_threshold
        ].copy()
        
        if not qualified_combinations.empty:
            # 按指标分组，选择每组中得分最高的
            for indicator_name, group in qualified_combinations.groupby('indicator'):
                best_combination = group.loc[group['overall_stability_score'].idxmax()]
                best_combinations_per_indicator.append(best_combination)
            
            if best_combinations_per_indicator:
                best_combinations_df = pd.DataFrame(best_combinations_per_indicator)
                best_combinations_df = best_combinations_df.sort_values(
                    'overall_stability_score', ascending=False
                )
                insights['best_combinations_per_indicator'] = best_combinations_df
                print(f"符合条件的最佳组合数量: {len(best_combinations_df)} (每个指标的最佳)")
            else:
                insights['best_combinations_per_indicator'] = pd.DataFrame()
                print("没有符合条件的最佳组合")
        else:
            insights['best_combinations_per_indicator'] = pd.DataFrame()
            print(f"没有综合得分超过{high_stability_threshold}的组合")
        
        # 2. 按指标汇总的稳定性
        indicator_stability = stability_df.groupby('indicator').agg({
            'overall_stability_score': 'mean',
            'appearance_rate': 'mean',
            'rank_mean': 'mean',
            'ir_mean': 'mean',
            'combination_id': 'count'
        }).rename(columns={'combination_id': 'combination_count'})
        indicator_stability = indicator_stability.sort_values('overall_stability_score', ascending=False)
        insights['indicator_stability_summary'] = indicator_stability
        
        # 3. 按信号类型汇总的稳定性
        signal_type_stability = stability_df.groupby('signal_type').agg({
            'overall_stability_score': 'mean',
            'appearance_rate': 'mean',
            'rank_mean': 'mean',
            'ir_mean': 'mean',
            'combination_id': 'count'
        }).rename(columns={'combination_id': 'combination_count'})
        signal_type_stability = signal_type_stability.sort_values('overall_stability_score', ascending=False)
        insights['signal_type_stability_summary'] = signal_type_stability
        
        # 4. 最稳定排名的组合 (排名方差最小)
        most_consistent_ranking = stability_df.nsmallest(10, 'rank_cv')[
            ['combination_id', 'indicator', 'signal_type', 'rank_mean', 'rank_std', 'rank_cv', 'ir_mean']
        ]
        insights['most_consistent_ranking'] = most_consistent_ranking
        
        # 5. 最高出现率的组合
        highest_appearance_rate = stability_df.nlargest(10, 'appearance_rate')[
            ['combination_id', 'indicator', 'signal_type', 'appearance_rate', 'rank_mean', 'ir_mean']
        ]
        insights['highest_appearance_rate'] = highest_appearance_rate
        
        # 6. 综合统计
        high_stability_count = len(stability_df[stability_df['overall_stability_score'] > high_stability_threshold])
        best_combinations_count = len(insights.get('best_combinations_per_indicator', pd.DataFrame()))
        
        overall_stats = pd.DataFrame({
            'Metric': [
                'Total Analyzed Combinations',
                'Average Stability Score',
                'Average Appearance Rate',
                'Average Rank Mean',
                'Average IR Mean',
                'Combinations with >50% Appearance',
                'Combinations with Avg Rank ≤3',
                f'High Stability Combinations (>{high_stability_threshold})',
                'Best Combinations per Indicator (>0.5)'
            ],
            'Value': [
                len(stability_df),
                f"{stability_df['overall_stability_score'].mean():.3f}",
                f"{stability_df['appearance_rate'].mean():.1%}",
                f"{stability_df['rank_mean'].mean():.2f}",
                f"{stability_df['ir_mean'].mean():.4f}",
                len(stability_df[stability_df['appearance_rate'] > 0.5]),
                len(stability_df[stability_df['rank_mean'] <= 3]),
                high_stability_count,
                best_combinations_count
            ]
        })
        insights['overall_statistics'] = overall_stats
        
        return insights
    
    def export_stability_analysis(self, stability_df: pd.DataFrame, 
                                insights: Dict[str, pd.DataFrame], 
                                significant_df: pd.DataFrame) -> str:
        """
        导出稳定性分析结果
        
        参数:
            stability_df: 稳定性分析结果
            insights: 洞察报告
            significant_df: 显著组合数据
            
        返回:
            导出文件路径
        """
        try:
            # 生成文件路径
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"signal_test_results/ranking_stability_analysis_{timestamp}.xlsx"
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            print(f"导出稳定性分析结果到: {filepath}")
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 主要结果
                if not stability_df.empty:
                    stability_df.to_excel(writer, sheet_name='Stability_Analysis', index=False)
                
                # 洞察报告
                for sheet_name, data_df in insights.items():
                    if not data_df.empty:
                        sheet_name_clean = sheet_name.replace('_', '_')[:31]  # Excel限制
                        data_df.to_excel(writer, sheet_name=sheet_name_clean, index=False)
                
                # 原始显著组合数据
                if not significant_df.empty:
                    significant_df.to_excel(writer, sheet_name='Raw_Significant_Data', index=False)
            
            print(f"稳定性分析结果导出完成: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"导出稳定性分析结果失败: {e}")
            return ""
    
    def run_complete_stability_analysis(self, rolling_results_df: pd.DataFrame) -> Dict[str, any]:
        """
        运行完整的稳定性分析流程
        
        参数:
            rolling_results_df: 滚动回测结果
            
        返回:
            包含所有分析结果的字典
        """
        print("="*80)
        print("基于排名的稳定性分析")
        print("="*80)
        print(f"配置: 最少窗口数={self.config.min_appearance_windows}")
        print(f"{self.config.get_selection_summary()}")
        print(f"{self.config.get_weights_summary()}")
        
        try:
            # 1. 提取显著组合
            significant_df = self.extract_significant_combinations_per_window(rolling_results_df)
            if significant_df.empty:
                print("无法提取显著组合，分析终止")
                return {}
            
            # 2. 计算稳定性
            stability_df = self.calculate_ranking_stability(significant_df, rolling_results_df)
            if stability_df.empty:
                print("无法计算稳定性，分析终止")
                return {}
            
            # 3. 生成洞察
            insights = self.generate_stability_insights(stability_df)
            
            # 4. 导出结果
            export_path = self.export_stability_analysis(stability_df, insights, significant_df)
            
            # 5. 打印关键发现
            self._print_key_findings(stability_df, insights)
            
            return {
                'stability_analysis': stability_df,
                'insights': insights,
                'significant_data': significant_df,
                'export_path': export_path
            }
            
        except Exception as e:
            print(f"稳定性分析失败: {e}")
            return {}
    
    def _print_key_findings(self, stability_df: pd.DataFrame, 
                          insights: Dict[str, pd.DataFrame]) -> None:
        """打印关键发现"""
        print("\n" + "="*50)
        print("关键发现 - 基于排名的稳定性分析 (四维评分)")
        print("="*50)
        
        # 显示权重配置
        print(f"\n>>> 评分权重配置:")
        print(f"  {self.config.get_weights_summary()}")
        
        if 'overall_statistics' in insights:
            print("\n>>> 整体统计:")
            stats_df = insights['overall_statistics']
            for _, row in stats_df.iterrows():
                print(f"  {row['Metric']}: {row['Value']}")
        
        if not stability_df.empty:
            # 展示高稳定性组合概况
            high_stability_threshold = self.config.high_stability_threshold
            high_stability_combinations = stability_df[
                stability_df['overall_stability_score'] > high_stability_threshold
            ]
            
            print(f"\n>>> 高稳定性组合概况 (综合得分 > {high_stability_threshold}):")
            print(f"  高稳定性组合数量: {len(high_stability_combinations)}")
            print(f"  占总组合比例: {len(high_stability_combinations)/len(stability_df)*100:.1f}%")
            
            if not high_stability_combinations.empty:
                print(f"  平均得分: {high_stability_combinations['overall_stability_score'].mean():.3f}")
                print(f"  最高得分: {high_stability_combinations['overall_stability_score'].max():.3f}")
                print(f"  涉及指标数: {high_stability_combinations['indicator'].nunique()}")
            
            print(f"\n>>> Top 5 最优组合 (综合评分最高):")
            top_5 = stability_df.head(5)
            for i, (_, row) in enumerate(top_5.iterrows(), 1):
                print(f"  {i}. {row['indicator']} - {row['signal_type']} "
                      f"(N={row['parameter_n']}, Dir={row['assumed_direction']})")
                print(f"     综合得分: {row['overall_stability_score']:.3f} | "
                      f"平均IR: {row['ir_mean']:.3f} | "
                      f"平均排名: {row['rank_mean']:.1f} | "
                      f"出现率: {row['appearance_rate']:.1%}")
                print(f"     分项得分: 排名稳定={row['ranking_stability_score']:.3f}, "
                      f"一致性={row['significance_consistency_score']:.3f}, "
                      f"性能稳定={row['performance_stability_score']:.3f}, "
                      f"绝对表现={row['absolute_performance_score']:.3f}")
                print()
        
        if 'indicator_stability_summary' in insights:
            print(f"\n>>> Top 5 最优指标:")
            top_indicators = insights['indicator_stability_summary'].head(5)
            for i, (indicator, row) in enumerate(top_indicators.iterrows(), 1):
                print(f"  {i}. {indicator}: 综合得分 {row['overall_stability_score']:.3f}, "
                      f"平均IR {row['ir_mean']:.3f}, 组合数量 {row['combination_count']}")
        
        # 重点展示：每个指标的最佳组合（综合得分 > 阈值）
        if 'best_combinations_per_indicator' in insights:
            best_combos = insights['best_combinations_per_indicator']
            if not best_combos.empty:
                print(f"\n>>> ★★★ 最佳组合推荐 (每个指标最佳且得分>{self.config.high_stability_threshold}) ★★★")
                print(f"共 {len(best_combos)} 个指标符合条件:")
                for i, (_, row) in enumerate(best_combos.iterrows(), 1):
                    print(f"  {i:2d}. {row['indicator']:<25} | {row['signal_type']:<20} | "
                          f"N={row['parameter_n']:<3} | Dir={row['assumed_direction']:2d}")
                    print(f"      综合得分: {row['overall_stability_score']:.3f} | "
                          f"平均IR: {row['ir_mean']:.3f} | "
                          f"出现窗口: {row['appearance_windows']:2d} | "
                          f"平均排名: {row['rank_mean']:.1f}")
                    print()
            else:
                print(f"\n>>> ★★★ 最佳组合推荐 ★★★")
                print(f"  没有指标的组合达到推荐标准 (综合得分>{self.config.high_stability_threshold})")
                print("  建议检查分析参数或数据质量")
                
        # 新增：按绝对表现排序的Top 5
        if not stability_df.empty:
            print(f"\n>>> Top 5 绝对表现最佳组合 (按平均IR排序):")
            top_ir = stability_df.nlargest(5, 'ir_mean')
            for i, (_, row) in enumerate(top_ir.iterrows(), 1):
                print(f"  {i}. {row['indicator']} - {row['signal_type']} "
                      f"(N={row['parameter_n']}, Dir={row['assumed_direction']})")
                print(f"     平均IR: {row['ir_mean']:.3f} | 综合得分: {row['overall_stability_score']:.3f} | "
                      f"绝对表现得分: {row['absolute_performance_score']:.3f}")
                print() 
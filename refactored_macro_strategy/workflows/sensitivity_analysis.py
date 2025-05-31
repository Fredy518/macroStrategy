"""
指标敏感性分析工作流
Indicator Sensitivity Analysis Workflow

测试不同宏观事件数量下的策略表现稳定性
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os
from datetime import datetime

from .multi_signal_workflow import MultiSignalVotingWorkflow
from ..config.signal_config import SignalConfig
from ..core.multi_signal_voting import MultiSignalVotingEngine, MultiSignalBacktestEngine
from ..utils.data_loader import load_all_data


class SensitivityAnalysisWorkflow:
    """指标敏感性分析工作流"""
    
    def __init__(self, signal_config: Optional[SignalConfig] = None):
        self.signal_config = signal_config or SignalConfig()
        self.voting_engine = MultiSignalVotingEngine(self.signal_config)
        self.backtest_engine = MultiSignalBacktestEngine()
    
    def run_signal_count_sensitivity_test(self,
                                          data_path: str,
                                          strategy_type: str,
                                          signal_counts: List[int] = [5, 7, 9, 11, 13],
                                          start_date: str = '2013-01-01',
                                          end_date: str = '2025-05-27') -> Dict:
        """
        运行信号数量敏感性测试
        
        参数:
            data_path: 数据文件路径
            strategy_type: 策略类型 ('value_growth' 或 'big_small')
            signal_counts: 要测试的信号数量列表
            start_date: 回测开始日期
            end_date: 回测结束日期
            
        返回:
            敏感性测试结果
        """
        print("="*100)
        print(f"{strategy_type.upper()} 策略 - 指标敏感性测试")
        print("="*100)
        print(f"测试信号数量: {signal_counts}")
        print(f"回测期间: {start_date} -> {end_date}")
        
        # 1. 加载数据
        try:
            data_dict = load_all_data(data_path)
            indicator_data = data_dict['indicator_data']
            price_data = data_dict['price_data']
            print(f"\n数据加载成功:")
            print(f"  宏观指标数据: {indicator_data.shape}")
            print(f"  价格数据: {price_data.shape}")
        except Exception as e:
            print(f"数据加载失败: {e}")
            return {}
        
        # 2. 获取信号排序信息
        ranking_info = self.signal_config.get_signal_ranking_info(strategy_type)
        total_signals = ranking_info['total_signals']
        
        print(f"\n{strategy_type} 策略信号排序:")
        for rank_info in ranking_info['signal_order'][:5]:  # 显示前5个
            print(f"  {rank_info['rank']}. {rank_info['indicator']} - {rank_info['description']}")
        if total_signals > 5:
            print(f"  ... 还有 {total_signals - 5} 个信号")
        
        # 3. 验证信号数量
        valid_counts = [n for n in signal_counts if n <= total_signals]
        if len(valid_counts) != len(signal_counts):
            invalid_counts = [n for n in signal_counts if n > total_signals]
            print(f"\n警告: 信号数量 {invalid_counts} 超过总信号数 {total_signals}，已忽略")
        
        # 4. 运行不同信号数量的测试
        sensitivity_results = {}
        
        for signal_count in valid_counts:
            print(f"\n{'='*80}")
            print(f"测试 {signal_count} 个信号的 {strategy_type} 策略")
            print(f"{'='*80}")
            
            # 获取前N个信号
            top_n_signals = self.signal_config.get_top_n_voting_signals(strategy_type, signal_count)
            
            print(f"使用的信号:")
            for i, signal in enumerate(top_n_signals, 1):
                print(f"  {i}. {signal['indicator']} - {signal.get('description', '')}")
            
            try:
                # 生成投票信号
                voting_signals = self.voting_engine.generate_voting_signals(
                    indicator_data, top_n_signals, strategy_type, signal_start_date='2012-11-01'
                )
                
                if voting_signals.empty:
                    print(f"警告: {signal_count} 个信号的投票信号生成失败")
                    continue
                
                # 计算投票决策
                voting_decisions = self.voting_engine.calculate_voting_decisions(
                    voting_signals, strategy_type
                )
                
                if voting_decisions.empty:
                    print(f"警告: {signal_count} 个信号的投票决策计算失败")
                    continue
                
                # 运行回测
                backtest_results = self.backtest_engine.run_voting_backtest(
                    voting_decisions, price_data, strategy_type, start_date, end_date
                )
                
                if not backtest_results:
                    print(f"警告: {signal_count} 个信号的回测失败")
                    continue
                
                # 保存结果
                sensitivity_results[f"{signal_count}_signals"] = {
                    'signal_count': signal_count,
                    'signals_used': top_n_signals,
                    'voting_signals': voting_signals,
                    'voting_decisions': voting_decisions,
                    **backtest_results
                }
                
                # 显示简要结果
                enhanced_metrics = backtest_results['enhanced_metrics']
                strategy_metrics = enhanced_metrics['strategy_metrics']
                excess_metrics = enhanced_metrics['excess_metrics']
                
                print(f"\n简要结果:")
                print(f"  策略年化收益: {strategy_metrics['annualized_return']:>8.2%}")
                print(f"  策略夏普比率: {strategy_metrics['sharpe_ratio']:>8.3f}")
                print(f"  策略最大回撤: {strategy_metrics['max_drawdown']:>8.2%}")
                print(f"  超额年化收益: {excess_metrics['excess_annualized_return']:>8.2%}")
                print(f"  信息比率:     {excess_metrics['information_ratio']:>8.3f}")
                print(f"  月胜率:       {enhanced_metrics['monthly_win_rate']['monthly_win_rate']:>8.1%}")
                
            except Exception as e:
                print(f"错误: {signal_count} 个信号测试失败 - {e}")
                continue
        
        # 5. 生成敏感性分析报告
        if sensitivity_results:
            sensitivity_summary = self._generate_sensitivity_summary(sensitivity_results, strategy_type)
            
            # 导出结果
            try:
                self._export_sensitivity_results(sensitivity_results, sensitivity_summary, strategy_type)
            except Exception as e:
                print(f"敏感性测试结果导出失败: {e}")
        
        print(f"\n{'='*100}")
        print(f"{strategy_type.upper()} 策略指标敏感性测试完成")
        print(f"{'='*100}")
        
        return {
            'strategy_type': strategy_type,
            'signal_counts_tested': valid_counts,
            'total_signals_available': total_signals,
            'ranking_info': ranking_info,
            'sensitivity_results': sensitivity_results,
            'sensitivity_summary': sensitivity_summary if sensitivity_results else {}
        }
    
    def run_both_strategies_sensitivity_test(self,
                                           data_path: str,
                                           signal_counts: List[int] = [5, 7, 9, 11, 13],
                                           start_date: str = '2013-01-01',
                                           end_date: str = '2025-05-27') -> Dict:
        """
        同时运行两个策略的敏感性测试
        
        参数:
            data_path: 数据文件路径
            signal_counts: 要测试的信号数量列表
            start_date: 回测开始日期
            end_date: 回测结束日期
            
        返回:
            包含两个策略敏感性测试结果的字典
        """
        print("="*100)
        print("多信号投票策略 - 指标敏感性测试 (价值成长 & 大小盘)")
        print("="*100)
        
        all_results = {}
        
        # 测试价值成长策略
        try:
            print("\n>>> 开始价值成长策略敏感性测试 <<<")
            value_growth_results = self.run_signal_count_sensitivity_test(
                data_path, 'value_growth', signal_counts, start_date, end_date
            )
            all_results['value_growth'] = value_growth_results
        except Exception as e:
            print(f"价值成长策略敏感性测试失败: {e}")
            all_results['value_growth'] = {}
        
        # 测试大小盘策略
        try:
            print("\n>>> 开始大小盘策略敏感性测试 <<<")
            big_small_results = self.run_signal_count_sensitivity_test(
                data_path, 'big_small', signal_counts, start_date, end_date
            )
            all_results['big_small'] = big_small_results
        except Exception as e:
            print(f"大小盘策略敏感性测试失败: {e}")
            all_results['big_small'] = {}
        
        # 生成综合比较报告
        try:
            self._generate_cross_strategy_sensitivity_report(all_results, signal_counts)
        except Exception as e:
            print(f"综合敏感性分析报告生成失败: {e}")
        
        return all_results
    
    def _generate_sensitivity_summary(self, sensitivity_results: Dict, strategy_type: str) -> Dict:
        """生成敏感性分析摘要"""
        
        summary_data = []
        
        for test_key, result in sensitivity_results.items():
            signal_count = result['signal_count']
            enhanced_metrics = result['enhanced_metrics']
            strategy_metrics = enhanced_metrics['strategy_metrics']
            benchmark_metrics = enhanced_metrics['benchmark_metrics']
            excess_metrics = enhanced_metrics['excess_metrics']
            monthly_win_rate = enhanced_metrics['monthly_win_rate']
            
            summary_data.append({
                'signal_count': signal_count,
                'strategy_annual_return': strategy_metrics['annualized_return'],
                'strategy_volatility': strategy_metrics['volatility'],
                'strategy_sharpe_ratio': strategy_metrics['sharpe_ratio'],
                'strategy_max_drawdown': strategy_metrics['max_drawdown'],
                'benchmark_annual_return': benchmark_metrics['annualized_return'],
                'benchmark_volatility': benchmark_metrics['volatility'],
                'benchmark_sharpe_ratio': benchmark_metrics['sharpe_ratio'],
                'benchmark_max_drawdown': benchmark_metrics['max_drawdown'],
                'excess_annual_return': excess_metrics['excess_annualized_return'],
                'information_ratio': excess_metrics['information_ratio'],
                'tracking_error': excess_metrics['tracking_error'],
                'relative_drawdown': enhanced_metrics['relative_drawdown'],
                'monthly_win_rate': monthly_win_rate['monthly_win_rate']
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # 计算稳定性指标
        stability_metrics = {
            'return_stability': summary_df['strategy_annual_return'].std(),
            'sharpe_stability': summary_df['strategy_sharpe_ratio'].std(),
            'excess_return_stability': summary_df['excess_annual_return'].std(),
            'info_ratio_stability': summary_df['information_ratio'].std(),
            'win_rate_stability': summary_df['monthly_win_rate'].std(),
            'best_signal_count': summary_df.loc[summary_df['information_ratio'].idxmax(), 'signal_count'],
            'most_stable_range': self._find_most_stable_range(summary_df)
        }
        
        return {
            'summary_table': summary_df,
            'stability_metrics': stability_metrics,
            'performance_trend': self._analyze_performance_trend(summary_df)
        }
    
    def _find_most_stable_range(self, summary_df: pd.DataFrame) -> str:
        """寻找最稳定的信号数量范围"""
        # 计算相邻信号数量间的收益率变化
        returns = summary_df['strategy_annual_return'].values
        changes = np.abs(np.diff(returns))
        
        # 找到变化最小的相邻对
        min_change_idx = np.argmin(changes)
        
        signal_counts = summary_df['signal_count'].values
        stable_range = f"{signal_counts[min_change_idx]}-{signal_counts[min_change_idx+1]}"
        
        return stable_range
    
    def _analyze_performance_trend(self, summary_df: pd.DataFrame) -> Dict:
        """分析绩效趋势"""
        signal_counts = summary_df['signal_count'].values
        returns = summary_df['strategy_annual_return'].values
        sharpe_ratios = summary_df['strategy_sharpe_ratio'].values
        info_ratios = summary_df['information_ratio'].values
        
        # 计算趋势斜率
        return_trend = np.polyfit(signal_counts, returns, 1)[0]
        sharpe_trend = np.polyfit(signal_counts, sharpe_ratios, 1)[0]
        info_ratio_trend = np.polyfit(signal_counts, info_ratios, 1)[0]
        
        # 确定趋势方向
        def trend_direction(slope):
            if abs(slope) < 0.001:
                return "稳定"
            elif slope > 0:
                return "上升"
            else:
                return "下降"
        
        return {
            'return_trend': trend_direction(return_trend),
            'return_slope': return_trend,
            'sharpe_trend': trend_direction(sharpe_trend),
            'sharpe_slope': sharpe_trend,
            'info_ratio_trend': trend_direction(info_ratio_trend),
            'info_ratio_slope': info_ratio_trend
        }
    
    def _export_sensitivity_results(self, 
                                   sensitivity_results: Dict, 
                                   sensitivity_summary: Dict, 
                                   strategy_type: str) -> None:
        """导出敏感性测试结果"""
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"signal_test_results/sensitivity_analysis_{strategy_type}_{timestamp}.xlsx"
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 1. 敏感性分析摘要
            summary_df = sensitivity_summary['summary_table']
            summary_df_export = summary_df.copy()
            
            # 格式化百分比列
            pct_columns = ['strategy_annual_return', 'strategy_volatility', 'benchmark_annual_return', 
                          'benchmark_volatility', 'excess_annual_return', 'strategy_max_drawdown', 
                          'benchmark_max_drawdown', 'tracking_error', 'relative_drawdown', 'monthly_win_rate']
            
            for col in pct_columns:
                if col in summary_df_export.columns:
                    summary_df_export[col] = summary_df_export[col].apply(lambda x: f"{x:.2%}")
            
            # 格式化比率列
            ratio_columns = ['strategy_sharpe_ratio', 'benchmark_sharpe_ratio', 'information_ratio']
            for col in ratio_columns:
                if col in summary_df_export.columns:
                    summary_df_export[col] = summary_df_export[col].apply(lambda x: f"{x:.3f}")
            
            # 重命名列为中文
            summary_df_export = summary_df_export.rename(columns={
                'signal_count': '信号数量',
                'strategy_annual_return': '策略年化收益',
                'strategy_volatility': '策略波动率',
                'strategy_sharpe_ratio': '策略夏普比率',
                'strategy_max_drawdown': '策略最大回撤',
                'benchmark_annual_return': '基准年化收益',
                'benchmark_volatility': '基准波动率',
                'benchmark_sharpe_ratio': '基准夏普比率',
                'benchmark_max_drawdown': '基准最大回撤',
                'excess_annual_return': '超额年化收益',
                'information_ratio': '信息比率',
                'tracking_error': '跟踪误差',
                'relative_drawdown': '相对回撤',
                'monthly_win_rate': '月胜率'
            })
            
            summary_df_export.to_excel(writer, sheet_name='敏感性分析摘要', index=False)
            
            # 2. 稳定性指标
            stability_metrics = sensitivity_summary['stability_metrics']
            stability_df = pd.DataFrame([{
                '指标': '年化收益率稳定性（标准差）',
                '数值': f"{stability_metrics['return_stability']:.4f}"
            }, {
                '指标': '夏普比率稳定性（标准差）',
                '数值': f"{stability_metrics['sharpe_stability']:.4f}"
            }, {
                '指标': '超额收益稳定性（标准差）',
                '数值': f"{stability_metrics['excess_return_stability']:.4f}"
            }, {
                '指标': '信息比率稳定性（标准差）',
                '数值': f"{stability_metrics['info_ratio_stability']:.4f}"
            }, {
                '指标': '月胜率稳定性（标准差）',
                '数值': f"{stability_metrics['win_rate_stability']:.4f}"
            }, {
                '指标': '最佳信号数量',
                '数值': str(stability_metrics['best_signal_count'])
            }, {
                '指标': '最稳定信号范围',
                '数值': stability_metrics['most_stable_range']
            }])
            
            stability_df.to_excel(writer, sheet_name='稳定性指标', index=False)
            
            # 3. 绩效趋势分析
            trend_analysis = sensitivity_summary['performance_trend']
            trend_df = pd.DataFrame([{
                '绩效指标': '年化收益率',
                '趋势方向': trend_analysis['return_trend'],
                '趋势斜率': f"{trend_analysis['return_slope']:.6f}"
            }, {
                '绩效指标': '夏普比率',
                '趋势方向': trend_analysis['sharpe_trend'],
                '趋势斜率': f"{trend_analysis['sharpe_slope']:.6f}"
            }, {
                '绩效指标': '信息比率',
                '趋势方向': trend_analysis['info_ratio_trend'],
                '趋势斜率': f"{trend_analysis['info_ratio_slope']:.6f}"
            }])
            
            trend_df.to_excel(writer, sheet_name='绩效趋势分析', index=False)
            
            # 4. 各测试的详细结果
            for test_key, result in sensitivity_results.items():
                signal_count = result['signal_count']
                
                # 年度绩效
                try:
                    yearly_analysis = result['enhanced_metrics']['yearly_analysis']
                    if not yearly_analysis.empty:
                        yearly_analysis.to_excel(writer, sheet_name=f'{signal_count}信号_年度绩效', index=False)
                except:
                    pass
                
                # 净值曲线
                try:
                    strategy_nav = result['strategy_nav']
                    benchmark_nav = result['benchmark_nav']
                    
                    aligned_nav_data = pd.DataFrame({
                        'strategy_nav': strategy_nav,
                        'benchmark_nav': benchmark_nav
                    }).dropna()
                    
                    relative_nav = aligned_nav_data['strategy_nav'] / aligned_nav_data['benchmark_nav']
                    
                    nav_data = pd.DataFrame({
                        '日期': aligned_nav_data.index,
                        '策略净值': aligned_nav_data['strategy_nav'].values,
                        '基准净值': aligned_nav_data['benchmark_nav'].values,
                        '相对净值': relative_nav.values
                    })
                    nav_data.to_excel(writer, sheet_name=f'{signal_count}信号_净值曲线', index=False)
                except:
                    pass
        
        print(f"\n{strategy_type} 敏感性测试结果已导出: {output_file}")
    
    def _generate_cross_strategy_sensitivity_report(self, all_results: Dict, signal_counts: List[int]) -> None:
        """生成跨策略敏感性分析报告"""
        print("\n" + "="*100)
        print("跨策略敏感性分析报告")
        print("="*100)
        
        # 收集所有结果进行比较
        comparison_data = []
        
        for strategy_name, strategy_results in all_results.items():
            if not strategy_results or 'sensitivity_results' not in strategy_results:
                continue
            
            sensitivity_results = strategy_results['sensitivity_results']
            
            for test_key, result in sensitivity_results.items():
                signal_count = result['signal_count']
                enhanced_metrics = result['enhanced_metrics']
                
                comparison_data.append({
                    'strategy': strategy_name,
                    'signal_count': signal_count,
                    'annual_return': enhanced_metrics['strategy_metrics']['annualized_return'],
                    'sharpe_ratio': enhanced_metrics['strategy_metrics']['sharpe_ratio'],
                    'max_drawdown': enhanced_metrics['strategy_metrics']['max_drawdown'],
                    'excess_return': enhanced_metrics['excess_metrics']['excess_annualized_return'],
                    'information_ratio': enhanced_metrics['excess_metrics']['information_ratio'],
                    'monthly_win_rate': enhanced_metrics['monthly_win_rate']['monthly_win_rate']
                })
        
        if not comparison_data:
            print("没有可用的比较数据")
            return
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # 按信号数量分组比较
        print(f"\n按信号数量的策略表现比较:")
        print(f"{'信号数':<8} {'策略':<15} {'年化收益':<10} {'夏普比率':<10} {'超额收益':<10} {'信息比率':<10} {'月胜率':<8}")
        print("-" * 80)
        
        for signal_count in sorted(signal_counts):
            group_data = comparison_df[comparison_df['signal_count'] == signal_count]
            
            for _, row in group_data.iterrows():
                print(f"{row['signal_count']:<8} {row['strategy']:<15} {row['annual_return']:>9.2%} "
                      f"{row['sharpe_ratio']:>9.3f} {row['excess_return']:>9.2%} {row['information_ratio']:>9.3f} "
                      f"{row['monthly_win_rate']:>7.1%}")
        
        # 导出综合比较结果
        try:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            comparison_file = f"signal_test_results/cross_strategy_sensitivity_comparison_{timestamp}.xlsx"
            
            with pd.ExcelWriter(comparison_file, engine='openpyxl') as writer:
                # 格式化比较数据
                comparison_export = comparison_df.copy()
                
                # 格式化百分比列
                pct_cols = ['annual_return', 'max_drawdown', 'excess_return', 'monthly_win_rate']
                for col in pct_cols:
                    comparison_export[col] = comparison_export[col].apply(lambda x: f"{x:.2%}")
                
                # 格式化比率列
                ratio_cols = ['sharpe_ratio', 'information_ratio']
                for col in ratio_cols:
                    comparison_export[col] = comparison_export[col].apply(lambda x: f"{x:.3f}")
                
                # 重命名列
                comparison_export = comparison_export.rename(columns={
                    'strategy': '策略类型',
                    'signal_count': '信号数量',
                    'annual_return': '年化收益',
                    'sharpe_ratio': '夏普比率',
                    'max_drawdown': '最大回撤',
                    'excess_return': '超额收益',
                    'information_ratio': '信息比率',
                    'monthly_win_rate': '月胜率'
                })
                
                comparison_export.to_excel(writer, sheet_name='跨策略敏感性比较', index=False)
                
                # 稳定性分析汇总
                stability_summary = []
                for strategy_name, strategy_results in all_results.items():
                    if strategy_results and 'sensitivity_summary' in strategy_results:
                        stability_metrics = strategy_results['sensitivity_summary']['stability_metrics']
                        stability_summary.append({
                            '策略类型': strategy_name,
                            '收益稳定性': f"{stability_metrics['return_stability']:.4f}",
                            '夏普稳定性': f"{stability_metrics['sharpe_stability']:.4f}",
                            '超额收益稳定性': f"{stability_metrics['excess_return_stability']:.4f}",
                            '信息比率稳定性': f"{stability_metrics['info_ratio_stability']:.4f}",
                            '最佳信号数量': stability_metrics['best_signal_count'],
                            '最稳定范围': stability_metrics['most_stable_range']
                        })
                
                if stability_summary:
                    stability_df = pd.DataFrame(stability_summary)
                    stability_df.to_excel(writer, sheet_name='稳定性对比', index=False)
            
            print(f"\n跨策略敏感性分析结果已导出: {comparison_file}")
            
        except Exception as e:
            print(f"跨策略敏感性分析结果导出失败: {e}")


def run_value_growth_sensitivity_test(data_path: str, 
                                     signal_counts: List[int] = [5, 7, 9, 11, 13]) -> Dict:
    """运行价值成长策略敏感性测试"""
    workflow = SensitivityAnalysisWorkflow()
    return workflow.run_signal_count_sensitivity_test(data_path, 'value_growth', signal_counts)


def run_big_small_sensitivity_test(data_path: str, 
                                  signal_counts: List[int] = [5, 7, 9, 11, 13]) -> Dict:
    """运行大小盘策略敏感性测试"""
    workflow = SensitivityAnalysisWorkflow()
    return workflow.run_signal_count_sensitivity_test(data_path, 'big_small', signal_counts)


def run_both_strategies_sensitivity_test(data_path: str, 
                                        signal_counts: List[int] = [5, 7, 9, 11, 13]) -> Dict:
    """同时运行两个策略的敏感性测试"""
    workflow = SensitivityAnalysisWorkflow()
    return workflow.run_both_strategies_sensitivity_test(data_path, signal_counts) 
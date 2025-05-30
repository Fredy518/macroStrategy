"""
多信号投票工作流程
Multi-Signal Voting Workflow

集成多信号投票策略的完整工作流程
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os

from ..core.multi_signal_voting import (
    SignalConfiguration, 
    MultiSignalVotingEngine, 
    MultiSignalBacktestEngine
)
from ..utils.data_loader import load_all_data
from ..config.signal_config import SignalConfig


class MultiSignalVotingWorkflow:
    """多信号投票策略工作流程"""
    
    def __init__(self, signal_config: Optional[SignalConfig] = None):
        self.signal_config = signal_config or SignalConfig()
        self.signal_configuration = SignalConfiguration()
        self.voting_engine = MultiSignalVotingEngine(self.signal_config)
        self.backtest_engine = MultiSignalBacktestEngine()
    
    def run_complete_voting_strategy(self, 
                                   data_path: str,
                                   strategy_type: str,
                                   start_date: str = '2013-01-01',
                                   end_date: str = '2025-05-27',
                                   custom_signals: Optional[List[Dict]] = None) -> Dict:
        """
        运行完整的多信号投票策略
        
        参数:
            data_path: 数据文件路径
            strategy_type: 策略类型 ('value_growth' 或 'big_small')
            start_date: 回测开始日期
            end_date: 回测结束日期
            custom_signals: 自定义信号配置（可选）
            
        返回:
            完整的分析结果
        """
        print("="*80)
        print(f"多信号投票策略 - {strategy_type.upper()}")
        print("="*80)
        
        # 1. 加载数据
        try:
            data_dict = load_all_data(data_path)
            indicator_data = data_dict['indicator_data']
            price_data = data_dict['price_data']
            print(f"数据加载成功:")
            print(f"  宏观指标数据: {indicator_data.shape}")
            print(f"  价格数据: {price_data.shape}")
        except Exception as e:
            print(f"数据加载失败: {e}")
            return {}
        
        # 2. 获取信号配置
        if custom_signals:
            signal_configs = custom_signals
            print(f"使用自定义信号配置: {len(signal_configs)} 个信号")
        else:
            all_configs = self.signal_configuration.load_default_configurations()
            signal_configs = all_configs.get(strategy_type, [])
            print(f"使用默认信号配置: {len(signal_configs)} 个信号")
        
        if not signal_configs:
            print(f"错误: 没有找到 {strategy_type} 策略的信号配置")
            return {}
        
        # 3. 生成投票信号
        voting_signals = self.voting_engine.generate_voting_signals(
            indicator_data, signal_configs, strategy_type, signal_start_date='2012-11-01'
        )
        
        if voting_signals.empty:
            print("错误: 投票信号生成失败")
            return {}
        
        # 4. 计算投票决策
        voting_decisions = self.voting_engine.calculate_voting_decisions(
            voting_signals, strategy_type
        )
        
        if voting_decisions.empty:
            print("错误: 投票决策计算失败")
            return {}
        
        # 5. 运行回测
        backtest_results = self.backtest_engine.run_voting_backtest(
            voting_decisions, price_data, strategy_type, start_date, end_date
        )
        
        if not backtest_results:
            print("错误: 回测运行失败")
            return {}
        
        # 6. 导出结果
        try:
            self._export_results(backtest_results, strategy_type)
        except Exception as e:
            print(f"结果导出失败: {e}")
        
        # 7. 综合结果
        complete_results = {
            'strategy_type': strategy_type,
            'signal_configs': signal_configs,
            'voting_signals': voting_signals,
            'voting_decisions': voting_decisions,
            **backtest_results
        }
        
        print(f"\n=== {strategy_type} 多信号投票策略完成 ===")
        return complete_results
    
    def run_complete_proportional_voting_strategy(self, 
                                                  data_path: str,
                                                  strategy_type: str,
                                                  start_date: str = '2013-01-01',
                                                  end_date: str = '2025-05-27',
                                                  custom_signals: Optional[List[Dict]] = None) -> Dict:
        """
        运行完整的按比例分配多信号投票策略
        
        参数:
            data_path: 数据文件路径
            strategy_type: 策略类型 ('value_growth' 或 'big_small')
            start_date: 回测开始日期
            end_date: 回测结束日期
            custom_signals: 自定义信号配置（可选）
            
        返回:
            完整的分析结果
        """
        print("="*80)
        print(f"多信号投票策略 (按比例分配) - {strategy_type.upper()}")
        print("="*80)
        
        # 1. 加载数据
        try:
            data_dict = load_all_data(data_path)
            indicator_data = data_dict['indicator_data']
            price_data = data_dict['price_data']
            print(f"数据加载成功:")
            print(f"  宏观指标数据: {indicator_data.shape}")
            print(f"  价格数据: {price_data.shape}")
        except Exception as e:
            print(f"数据加载失败: {e}")
            return {}
        
        # 2. 获取信号配置
        if custom_signals:
            signal_configs = custom_signals
            print(f"使用自定义信号配置: {len(signal_configs)} 个信号")
        else:
            all_configs = self.signal_configuration.load_default_configurations()
            signal_configs = all_configs.get(strategy_type, [])
            print(f"使用默认信号配置: {len(signal_configs)} 个信号")
        
        if not signal_configs:
            print(f"错误: 没有找到 {strategy_type} 策略的信号配置")
            return {}
        
        # 3. 生成投票信号
        voting_signals = self.voting_engine.generate_voting_signals(
            indicator_data, signal_configs, strategy_type, signal_start_date='2012-11-01'
        )
        
        if voting_signals.empty:
            print("错误: 投票信号生成失败")
            return {}
        
        # 4. 计算投票决策
        voting_decisions = self.voting_engine.calculate_voting_decisions(
            voting_signals, strategy_type
        )
        
        if voting_decisions.empty:
            print("错误: 投票决策计算失败")
            return {}
        
        # 5. 运行按比例分配回测
        backtest_results = self.backtest_engine.run_voting_backtest_proportional(
            voting_decisions, price_data, strategy_type, start_date, end_date
        )
        
        if not backtest_results:
            print("错误: 按比例回测运行失败")
            return {}
        
        # 6. 导出结果
        try:
            self._export_results(backtest_results, strategy_type, mode_suffix='proportional')
        except Exception as e:
            print(f"结果导出失败: {e}")
        
        # 7. 综合结果
        complete_results = {
            'strategy_type': strategy_type,
            'backtest_mode': 'proportional',
            'signal_configs': signal_configs,
            'voting_signals': voting_signals,
            'voting_decisions': voting_decisions,
            **backtest_results
        }
        
        print(f"\n=== {strategy_type} 按比例分配投票策略完成 ===")
        return complete_results
    
    def run_both_strategies(self, 
                           data_path: str,
                           start_date: str = '2013-01-01',
                           end_date: str = '2025-05-27') -> Dict[str, Dict]:
        """
        同时运行价值成长和大小盘两个策略
        
        参数:
            data_path: 数据文件路径
            start_date: 回测开始日期
            end_date: 回测结束日期
            
        返回:
            包含两个策略结果的字典
        """
        print("="*80)
        print("多信号投票策略 - 价值成长 & 大小盘轮动")
        print("="*80)
        
        all_results = {}
        
        # 运行价值成长策略
        try:
            print("\n>>> 开始价值成长策略分析 <<<")
            value_growth_results = self.run_complete_voting_strategy(
                data_path, 'value_growth', start_date, end_date
            )
            all_results['value_growth'] = value_growth_results
        except Exception as e:
            print(f"价值成长策略运行失败: {e}")
            all_results['value_growth'] = {}
        
        # 运行大小盘策略
        try:
            print("\n>>> 开始大小盘策略分析 <<<")
            big_small_results = self.run_complete_voting_strategy(
                data_path, 'big_small', start_date, end_date
            )
            all_results['big_small'] = big_small_results
        except Exception as e:
            print(f"大小盘策略运行失败: {e}")
            all_results['big_small'] = {}
        
        # 生成比较报告
        try:
            self._generate_comparison_report(all_results)
        except Exception as e:
            print(f"比较报告生成失败: {e}")
        
        return all_results
    
    def _export_results(self, results: Dict, strategy_type: str, mode_suffix: str = '') -> None:
        """导出分析结果到Excel"""
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"signal_test_results/multi_signal_voting_{strategy_type}_{mode_suffix}_{timestamp}.xlsx"
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 获取增强绩效指标
            enhanced_metrics = results['enhanced_metrics']
            
            try:
                # 年度绩效分析（已包含累计表现和中文表头）
                yearly_analysis = enhanced_metrics['yearly_analysis']
                if not yearly_analysis.empty:
                    yearly_analysis.to_excel(writer, sheet_name='年度绩效分析', index=False)
                    print("  ✓ 年度绩效分析导出成功")
            except Exception as e:
                print(f"  ✗ 年度绩效分析导出失败: {e}")
            
            try:
                # 交易信号（处理None值并使用中文列名）
                if 'trading_signals' in results and not results['trading_signals'].empty:
                    trading_signals_export = results['trading_signals'].copy()
                    
                    # 处理None值，转换为字符串
                    trading_signals_export['trading_date'] = trading_signals_export['trading_date'].apply(
                        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '未来信号'
                    )
                    trading_signals_export['signal_date'] = trading_signals_export['signal_date'].apply(
                        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
                    )
                    
                    # 根据回测模式决定列名映射
                    if results.get('backtest_mode') == 'proportional':
                        # 按比例分配模式的列名映射
                        trading_signals_export = trading_signals_export.rename(columns={
                            'signal_date': '信号日期',
                            'trading_date': '交易日期', 
                            'asset1_weight': '第一资产权重',
                            'asset2_weight': '第二资产权重',
                            'asset1_votes': '第一资产票数',
                            'asset2_votes': '第二资产票数',
                            'total_votes': '总票数',
                            'asset1_name': '第一资产名称',
                            'asset2_name': '第二资产名称'
                        })
                    else:
                        # 传统获胜者全拿模式的列名映射
                        trading_signals_export = trading_signals_export.rename(columns={
                            'signal_date': '信号日期',
                            'trading_date': '交易日期', 
                            'target_asset': '目标资产',
                            'winning_direction': '获胜方向',
                            'vote_confidence': '投票信心度'
                        })
                    
                    trading_signals_export.to_excel(writer, sheet_name='交易信号', index=False)
                    print("  ✓ 交易信号导出成功")
            except Exception as e:
                print(f"  ✗ 交易信号导出失败: {e}")
            
            try:
                # 投票决策
                if 'voting_decisions' in results and not results['voting_decisions'].empty:
                    results['voting_decisions'].to_excel(writer, sheet_name='投票决策')
                    print("  ✓ 投票决策导出成功")
            except Exception as e:
                print(f"  ✗ 投票决策导出失败: {e}")
            
            try:
                # 净值曲线数据（使用新计算的净值，以2013/1/4为基准）
                strategy_nav = results['strategy_nav']
                benchmark_nav = results['benchmark_nav']
                nav_base_date = results['nav_base_date']
                
                print(f"  策略净值长度: {len(strategy_nav)}, 基准净值长度: {len(benchmark_nav)}")
                
                # 确保数据对齐
                aligned_nav_data = pd.DataFrame({
                    'strategy_nav': strategy_nav,
                    'benchmark_nav': benchmark_nav
                }).dropna()
                
                print(f"  对齐后净值数据长度: {len(aligned_nav_data)}")
                
                # 计算相对净值
                relative_nav = aligned_nav_data['strategy_nav'] / aligned_nav_data['benchmark_nav']
                
                nav_data = pd.DataFrame({
                    '日期': aligned_nav_data.index,
                    '策略净值': aligned_nav_data['strategy_nav'].values,
                    '基准净值': aligned_nav_data['benchmark_nav'].values,
                    '相对净值': relative_nav.values
                })
                nav_data.to_excel(writer, sheet_name='净值曲线', index=False)
                print("  ✓ 净值曲线导出成功")
            except Exception as e:
                print(f"  ✗ 净值曲线导出失败: {e}")
            
            try:
                # 日度收益数据（确保数据对齐）
                aligned_returns = pd.DataFrame({
                    'strategy': results['strategy_returns'],
                    'benchmark': results['benchmark_returns']
                }).dropna()
                
                print(f"  对齐后收益数据长度: {len(aligned_returns)}")
                
                returns_data = pd.DataFrame({
                    '日期': aligned_returns.index,
                    '策略收益': aligned_returns['strategy'].values,
                    '基准收益': aligned_returns['benchmark'].values,
                    '超额收益': (aligned_returns['strategy'] - aligned_returns['benchmark']).values
                })
                returns_data.to_excel(writer, sheet_name='日度收益', index=False)
                print("  ✓ 日度收益导出成功")
            except Exception as e:
                print(f"  ✗ 日度收益导出失败: {e}")
            
            try:
                # 月度胜率统计
                win_rate_data = enhanced_metrics['monthly_win_rate']
                monthly_stats = pd.DataFrame([{
                    '总月份数': win_rate_data['total_months'],
                    '获胜月份': win_rate_data['winning_months'],
                    '失败月份': win_rate_data['losing_months'],
                    '月胜率': f"{win_rate_data['monthly_win_rate']:.1%}"
                }])
                monthly_stats.to_excel(writer, sheet_name='月度统计', index=False)
                print("  ✓ 月度统计导出成功")
            except Exception as e:
                print(f"  ✗ 月度统计导出失败: {e}")
        
        print(f"\n{strategy_type} 策略结果已导出: {output_file}")
    
    def _generate_comparison_report(self, all_results: Dict[str, Dict]) -> None:
        """生成策略比较报告"""
        print("\n" + "="*60)
        print("多信号投票策略比较报告")
        print("="*60)
        
        for strategy_name, results in all_results.items():
            if not results or 'enhanced_metrics' not in results:
                print(f"\n>>> {strategy_name.upper()} 策略: 数据不完整，跳过")
                continue
            
            enhanced_metrics = results['enhanced_metrics']
            strategy_metrics = enhanced_metrics['strategy_metrics']
            benchmark_metrics = enhanced_metrics['benchmark_metrics']
            excess_metrics = enhanced_metrics['excess_metrics']
            
            print(f"\n>>> {strategy_name.upper()} 策略结果:")
            print(f"  策略年化收益: {strategy_metrics['annualized_return']:.2%}")
            print(f"  策略波动率: {strategy_metrics['volatility']:.2%}")
            print(f"  策略夏普比率: {strategy_metrics['sharpe_ratio']:.3f}")
            print(f"  策略最大回撤: {strategy_metrics['max_drawdown']:.2%}")
            print(f"  基准年化收益: {benchmark_metrics['annualized_return']:.2%}")
            print(f"  基准波动率: {benchmark_metrics['volatility']:.2%}")
            print(f"  基准夏普比率: {benchmark_metrics['sharpe_ratio']:.3f}")
            print(f"  基准最大回撤: {benchmark_metrics['max_drawdown']:.2%}")
            print(f"  超额年化收益: {excess_metrics['excess_annualized_return']:.2%}")
            print(f"  信息比率: {excess_metrics['information_ratio']:.3f}")
            print(f"  月胜率: {enhanced_metrics['monthly_win_rate']['monthly_win_rate']:.1%}")
        
        # 导出综合比较结果
        try:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            comparison_file = f"signal_test_results/multi_signal_strategies_comparison_{timestamp}.xlsx"
            
            comparison_data = []
            for strategy_name, results in all_results.items():
                if results and 'enhanced_metrics' in results:
                    enhanced_metrics = results['enhanced_metrics']
                    strategy_metrics = enhanced_metrics['strategy_metrics']
                    benchmark_metrics = enhanced_metrics['benchmark_metrics']
                    excess_metrics = enhanced_metrics['excess_metrics']
                    
                    comparison_data.append({
                        'strategy': strategy_name,
                        'strategy_annualized_return': strategy_metrics['annualized_return'],
                        'strategy_volatility': strategy_metrics['volatility'],
                        'strategy_sharpe_ratio': strategy_metrics['sharpe_ratio'],
                        'strategy_max_drawdown': strategy_metrics['max_drawdown'],
                        'benchmark_annualized_return': benchmark_metrics['annualized_return'],
                        'benchmark_volatility': benchmark_metrics['volatility'],
                        'benchmark_sharpe_ratio': benchmark_metrics['sharpe_ratio'],
                        'benchmark_max_drawdown': benchmark_metrics['max_drawdown'],
                        'excess_return': excess_metrics['excess_annualized_return'],
                        'information_ratio': excess_metrics['information_ratio'],
                        'tracking_error': excess_metrics['tracking_error'],
                        'relative_drawdown': enhanced_metrics['relative_drawdown'],
                        'monthly_win_rate': enhanced_metrics['monthly_win_rate']['monthly_win_rate']
                    })
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data)
                comparison_df.to_excel(comparison_file, index=False)
                print(f"\n策略比较结果已导出: {comparison_file}")
        
        except Exception as e:
            print(f"比较结果导出失败: {e}")


def run_value_growth_voting_strategy(data_path: str) -> Dict:
    """运行价值成长多信号投票策略"""
    workflow = MultiSignalVotingWorkflow()
    return workflow.run_complete_voting_strategy(data_path, 'value_growth')


def run_big_small_voting_strategy(data_path: str) -> Dict:
    """运行大小盘多信号投票策略"""
    workflow = MultiSignalVotingWorkflow()
    return workflow.run_complete_voting_strategy(data_path, 'big_small')


def run_both_voting_strategies(data_path: str) -> Dict[str, Dict]:
    """同时运行两个投票策略"""
    workflow = MultiSignalVotingWorkflow()
    return workflow.run_both_strategies(data_path)


def run_value_growth_proportional_voting_strategy(data_path: str) -> Dict:
    """运行价值成长按比例分配多信号投票策略"""
    workflow = MultiSignalVotingWorkflow()
    return workflow.run_complete_proportional_voting_strategy(data_path, 'value_growth')


def run_big_small_proportional_voting_strategy(data_path: str) -> Dict:
    """运行大小盘按比例分配多信号投票策略"""
    workflow = MultiSignalVotingWorkflow()
    return workflow.run_complete_proportional_voting_strategy(data_path, 'big_small')


def run_both_proportional_voting_strategies(data_path: str) -> Dict[str, Dict]:
    """同时运行两个按比例分配投票策略"""
    workflow = MultiSignalVotingWorkflow()
    
    all_results = {}
    
    # 运行价值成长比例策略
    try:
        print("\n>>> 开始价值成长比例策略分析 <<<")
        value_growth_results = workflow.run_complete_proportional_voting_strategy(
            data_path, 'value_growth'
        )
        all_results['value_growth_proportional'] = value_growth_results
    except Exception as e:
        print(f"价值成长比例策略运行失败: {e}")
        all_results['value_growth_proportional'] = {}
    
    # 运行大小盘比例策略
    try:
        print("\n>>> 开始大小盘比例策略分析 <<<")
        big_small_results = workflow.run_complete_proportional_voting_strategy(
            data_path, 'big_small'
        )
        all_results['big_small_proportional'] = big_small_results
    except Exception as e:
        print(f"大小盘比例策略运行失败: {e}")
        all_results['big_small_proportional'] = {}
    
    return all_results 
"""
多信号投票回测系统
Multi-Signal Voting Backtest System

实现基于多个宏观信号投票的轮动策略回测
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os

from ..utils.data_loader import load_all_data
from .signal_engine import SignalEngine
from ..config.signal_config import SignalConfig


class SignalConfiguration:
    """信号配置管理器"""
    
    def __init__(self):
        self.value_growth_signals = []
        self.big_small_signals = []
    
    def parse_signal_config_text(self, config_text: str) -> Dict[str, List[Dict]]:
        """
        解析用户提供的信号配置文本
        
        参数:
            config_text: 包含信号配置的文本
            
        返回:
            解析后的信号配置字典
        """
        signals = {
            'value_growth': [],
            'big_small': []
        }
        
        lines = config_text.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            # 解析每行：model, combination_id, indicator, signal_type, parameter_n, assumed_direction
            parts = [part.strip() for part in line.split('\t')]
            if len(parts) != 6:
                continue
                
            model, combination_id, indicator, signal_type, parameter_n, assumed_direction = parts
            
            signal_config = {
                'indicator': indicator,
                'signal_type': signal_type,
                'parameter_n': int(parameter_n),
                'assumed_direction': int(assumed_direction),
                'combination_id': combination_id
            }
            
            if model == 'value_growth':
                signals['value_growth'].append(signal_config)
            elif model == 'big_small':
                signals['big_small'].append(signal_config)
        
        return signals
    
    def load_default_configurations(self) -> Dict[str, List[Dict]]:
        """加载默认的信号配置（您提供的配置）"""
        config_text = """value_growth	long_loan_newadded_MA12_yoy_exceed_expectation_3_-1	long_loan_newadded_MA12_yoy	exceed_expectation	3	-1
value_growth	M2_M1_historical_new_high_3_1	M2_M1	historical_new_high	3	1
value_growth	newstarts_area_yoy_historical_new_high_3_1	newstarts_area_yoy	historical_new_high	3	1
value_growth	CPI_PPI_historical_new_high_6_-1	CPI_PPI	historical_new_high	6	-1
value_growth	US_BOND_5Y_exceed_expectation_12_1	US_BOND_5Y	exceed_expectation	12	1
value_growth	TSF_newadded_MA12_yoy_historical_high_12_-1	TSF_newadded_MA12_yoy	historical_high	12	-1
value_growth	US_BOND_10Y_exceed_expectation_12_1	US_BOND_10Y	exceed_expectation	12	1
value_growth	fixedasset_investment_yoy_exceed_expectation_3_1	fixedasset_investment_yoy	exceed_expectation	3	1
value_growth	M1_exceed_expectation_9_-1	M1	exceed_expectation	9	-1
value_growth	M2_historical_high_12_-1	M2	historical_high	12	-1
value_growth	pmi_manufacturing_neworder_historical_new_low_6_1	pmi_manufacturing_neworder	historical_new_low	6	1
value_growth	pmi_nonmanufacturing_historical_new_low_3_-1	pmi_nonmanufacturing	historical_new_low	3	-1
value_growth	CREDIT_SPREAD_historical_new_low_3_1	CREDIT_SPREAD	historical_new_low	3	1
big_small	local_gov_budget_MA12_yoy_historical_high_6_1	local_gov_budget_MA12_yoy	historical_high	6	1
big_small	pmi_manufacturing_neworder_historical_new_low_6_1	pmi_manufacturing_neworder	historical_new_low	6	1
big_small	pmi_manufacturing_historical_high_6_1	pmi_manufacturing	historical_high	6	1
big_small	completed_yoy_historical_new_high_3_-1	completed_yoy	historical_new_high	3	-1
big_small	CN_BOND_1Y_historical_new_high_3_1	CN_BOND_1Y	historical_new_high	3	1
big_small	PPI_historical_new_low_9_1	PPI	historical_new_low	9	1
big_small	newstarts_area_yoy_historical_new_high_3_1	newstarts_area_yoy	historical_new_high	3	1
big_small	CPI_PPI_historical_new_high_6_-1	CPI_PPI	historical_new_high	6	-1
big_small	core_CPI_PPI_historical_new_high_9_-1	core_CPI_PPI	historical_new_high	9	-1
big_small	fixedasset_investment_ytd_yoy_historical_new_high_3_1	fixedasset_investment_ytd_yoy	historical_new_high	3	1
big_small	TSF_yoy_historical_new_high_3_-1	TSF_yoy	historical_new_high	3	-1
big_small	CN_BOND_10Y_exceed_expectation_3_1	CN_BOND_10Y	exceed_expectation	3	1
big_small	industrial_value_added_yoy_exceed_expectation_9_1	industrial_value_added_yoy	exceed_expectation	9	1"""
        
        return self.parse_signal_config_text(config_text)


class MultiSignalVotingEngine:
    """多信号投票引擎"""
    
    def __init__(self, signal_config: Optional[SignalConfig] = None):
        self.signal_config = signal_config or SignalConfig()
        self.signal_engine = SignalEngine(self.signal_config)
        self.signal_configuration = SignalConfiguration()
    
    def generate_voting_signals(self, 
                               data: pd.DataFrame,
                               signal_configs: List[Dict],
                               strategy_type: str,
                               signal_start_date: str = '2012-11-01') -> pd.DataFrame:
        """
        为指定策略生成投票信号
        
        参数:
            data: 宏观指标数据
            signal_configs: 信号配置列表
            strategy_type: 策略类型 ('value_growth' 或 'big_small')
            signal_start_date: 信号计算开始日期，默认2012-11-01
            
        返回:
            包含每个时间点投票结果的DataFrame
        """
        # 过滤数据到指定开始时间之后
        signal_start_ts = pd.Timestamp(signal_start_date)
        filtered_data = data.loc[data.index >= signal_start_ts].copy()
        
        if filtered_data.empty:
            print(f"警告: 过滤到{signal_start_date}之后无可用数据")
            return pd.DataFrame()
        
        print(f"\n=== {strategy_type} 策略信号生成 ===")
        print(f"信号计算期间: {signal_start_date} -> {filtered_data.index[-1].strftime('%Y-%m-%d')}")
        print(f"配置的信号数量: {len(signal_configs)}")
        
        voting_results = []
        
        for i, signal_config in enumerate(signal_configs, 1):
            indicator = signal_config['indicator']
            signal_type = signal_config['signal_type']
            parameter_n = signal_config['parameter_n']
            assumed_direction = signal_config['assumed_direction']
            combination_id = signal_config['combination_id']
            
            print(f"  处理信号 {i}/{len(signal_configs)}: {indicator} - {signal_type} (N={parameter_n}, Dir={assumed_direction})")
            
            if indicator not in filtered_data.columns:
                print(f"    警告: 指标 {indicator} 不存在于数据中，跳过")
                continue
            
            try:
                # 生成原始信号
                raw_signal = self.signal_engine.generate_single_signal(
                    filtered_data[indicator], signal_type, parameter_n
                )
                
                # 处理NaN值 - 将NaN填充为False（表示无信号）
                if raw_signal.isna().any():
                    print(f"    警告: 信号包含NaN值，已填充为False")
                    raw_signal = raw_signal.fillna(False).infer_objects(copy=False)
                
                # 确保raw_signal是布尔类型
                if raw_signal.dtype != bool:
                    raw_signal = raw_signal.astype(bool)
                
                # 根据假定方向调整信号
                if assumed_direction == 1:
                    # 正向：信号为True时支持对应方向
                    adjusted_signal = raw_signal
                else:
                    # 反向：信号为True时支持相反方向
                    adjusted_signal = ~raw_signal
                
                # 根据策略类型确定投票方向
                if strategy_type == 'value_growth':
                    # 对于价值成长：True=价值，False=成长
                    vote_direction = adjusted_signal.astype(int)  # 1=价值，0=成长
                elif strategy_type == 'big_small':
                    # 对于大小盘：True=大盘，False=小盘
                    vote_direction = adjusted_signal.astype(int)  # 1=大盘，0=小盘
                
                # 添加到投票结果
                vote_series = pd.DataFrame({
                    'date': filtered_data.index,
                    'signal_id': combination_id,
                    'vote': vote_direction,
                    'indicator': indicator,
                    'signal_type': signal_type
                })
                
                voting_results.append(vote_series)
                
            except Exception as e:
                print(f"    错误: 信号生成失败 - {e}")
                continue
        
        if not voting_results:
            print("警告: 没有成功生成任何信号")
            return pd.DataFrame()
        
        # 合并所有投票结果
        all_votes_df = pd.concat(voting_results, ignore_index=True)
        
        return all_votes_df
    
    def calculate_voting_decisions(self, 
                                  voting_signals: pd.DataFrame,
                                  strategy_type: str) -> pd.DataFrame:
        """
        计算每个时间点的投票决策
        
        参数:
            voting_signals: 包含所有信号投票的DataFrame
            strategy_type: 策略类型
            
        返回:
            包含投票决策的DataFrame
        """
        if voting_signals.empty:
            return pd.DataFrame()
        
        print(f"\n=== {strategy_type} 投票决策计算 ===")
        
        # 按日期分组统计投票
        voting_summary = voting_signals.groupby('date').agg({
            'vote': ['sum', 'count', lambda x: (x == 1).sum(), lambda x: (x == 0).sum()]
        }).reset_index()
        
        voting_summary.columns = ['date', 'total_score', 'total_signals', 'votes_for_first', 'votes_for_second']
        
        # 确定获胜方向
        if strategy_type == 'value_growth':
            # 1=价值，0=成长
            voting_summary['winning_direction'] = (voting_summary['votes_for_first'] > voting_summary['votes_for_second']).astype(int)
            voting_summary['winning_name'] = voting_summary['winning_direction'].map({1: 'Value', 0: 'Growth'})
            voting_summary['value_votes'] = voting_summary['votes_for_first']
            voting_summary['growth_votes'] = voting_summary['votes_for_second']
        elif strategy_type == 'big_small':
            # 1=大盘，0=小盘
            voting_summary['winning_direction'] = (voting_summary['votes_for_first'] > voting_summary['votes_for_second']).astype(int)
            voting_summary['winning_name'] = voting_summary['winning_direction'].map({1: 'Big', 0: 'Small'})
            voting_summary['big_votes'] = voting_summary['votes_for_first']
            voting_summary['small_votes'] = voting_summary['votes_for_second']
        
        # 计算投票优势度
        voting_summary['vote_margin'] = abs(voting_summary['votes_for_first'] - voting_summary['votes_for_second'])
        voting_summary['vote_confidence'] = voting_summary['vote_margin'] / voting_summary['total_signals']
        
        voting_summary = voting_summary.set_index('date')
        
        print(f"投票决策统计:")
        if strategy_type == 'value_growth':
            value_wins = (voting_summary['winning_direction'] == 1).sum()
            growth_wins = (voting_summary['winning_direction'] == 0).sum()
            print(f"  价值获胜: {value_wins} 次 ({value_wins/len(voting_summary)*100:.1f}%)")
            print(f"  成长获胜: {growth_wins} 次 ({growth_wins/len(voting_summary)*100:.1f}%)")
        else:
            big_wins = (voting_summary['winning_direction'] == 1).sum()
            small_wins = (voting_summary['winning_direction'] == 0).sum()
            print(f"  大盘获胜: {big_wins} 次 ({big_wins/len(voting_summary)*100:.1f}%)")
            print(f"  小盘获胜: {small_wins} 次 ({small_wins/len(voting_summary)*100:.1f}%)")
        
        return voting_summary


class MultiSignalBacktestEngine:
    """多信号投票回测引擎"""
    
    def __init__(self):
        pass
    
    def calculate_enhanced_performance_metrics(self, 
                                             strategy_returns: pd.Series,
                                             benchmark_returns: pd.Series) -> Dict:
        """
        计算增强的绩效指标
        
        参数:
            strategy_returns: 策略收益序列
            benchmark_returns: 基准收益序列
            
        返回:
            包含详细绩效指标的字典
        """
        # 确保数据对齐
        aligned_data = pd.DataFrame({
            'strategy': strategy_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        strategy_ret = aligned_data['strategy']
        benchmark_ret = aligned_data['benchmark']
        
        # 基础绩效指标
        def calc_basic_metrics(returns):
            total_return = (1 + returns).prod() - 1
            annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
            
            # 最大回撤
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown
            }
        
        strategy_metrics = calc_basic_metrics(strategy_ret)
        benchmark_metrics = calc_basic_metrics(benchmark_ret)
        
        # 超额收益分析
        excess_returns = strategy_ret - benchmark_ret
        excess_metrics = {
            'excess_annualized_return': strategy_metrics['annualized_return'] - benchmark_metrics['annualized_return'],
            'excess_volatility': excess_returns.std() * np.sqrt(252),
            'information_ratio': (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0,
            'tracking_error': excess_returns.std() * np.sqrt(252)
        }
        
        # 相对回撤
        strategy_nav = (1 + strategy_ret).cumprod()
        benchmark_nav = (1 + benchmark_ret).cumprod()
        relative_nav = strategy_nav / benchmark_nav
        relative_drawdown = (relative_nav / relative_nav.expanding().max() - 1).min()
        
        # 月胜率分析
        monthly_strategy = strategy_ret.resample('M').apply(lambda x: (1 + x).prod() - 1)
        monthly_benchmark = benchmark_ret.resample('M').apply(lambda x: (1 + x).prod() - 1)
        monthly_excess = monthly_strategy - monthly_benchmark
        
        win_rate = (monthly_excess > 0).mean()
        monthly_win_rate = {
            'monthly_win_rate': win_rate,
            'total_months': len(monthly_excess),
            'winning_months': (monthly_excess > 0).sum(),
            'losing_months': (monthly_excess <= 0).sum()
        }
        
        # 年度绩效分析
        yearly_analysis = self.calculate_yearly_performance(
            strategy_ret, 
            benchmark_ret, 
            {
                'strategy_metrics': strategy_metrics,
                'benchmark_metrics': benchmark_metrics,
                'excess_metrics': excess_metrics,
                'monthly_win_rate': monthly_win_rate
            }
        )
        
        return {
            'strategy_metrics': strategy_metrics,
            'benchmark_metrics': benchmark_metrics,
            'excess_metrics': excess_metrics,
            'relative_drawdown': relative_drawdown,
            'monthly_win_rate': monthly_win_rate,
            'yearly_analysis': yearly_analysis
        }
    
    def calculate_yearly_performance(self, 
                                   strategy_returns: pd.Series,
                                   benchmark_returns: pd.Series,
                                   overall_metrics: Dict = None) -> pd.DataFrame:
        """
        计算年度绩效表现（增强版）
        
        参数:
            strategy_returns: 策略收益序列
            benchmark_returns: 基准收益序列
            overall_metrics: 整体绩效指标（用于累计表现行）
            
        返回:
            增强的年度绩效DataFrame，包含中文表头和累计表现
        """
        # 确保数据对齐
        aligned_data = pd.DataFrame({
            'strategy': strategy_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        # 计算净值序列（用于准确的年度收益计算）
        strategy_nav = (1 + aligned_data['strategy']).cumprod()
        benchmark_nav = (1 + aligned_data['benchmark']).cumprod()
        
        # 按年分组计算
        yearly_data = []
        for year in range(aligned_data.index[0].year, aligned_data.index[-1].year + 1):
            year_data = aligned_data[aligned_data.index.year == year]
            year_strategy_nav = strategy_nav[strategy_nav.index.year == year]
            year_benchmark_nav = benchmark_nav[benchmark_nav.index.year == year]
            
            if len(year_data) == 0 or len(year_strategy_nav) == 0:
                continue
            
            # 计算年度收益（使用净值首尾，避免累积误差）
            strategy_annual = (year_strategy_nav.iloc[-1] / year_strategy_nav.iloc[0]) - 1
            benchmark_annual = (year_benchmark_nav.iloc[-1] / year_benchmark_nav.iloc[0]) - 1
            excess_annual = strategy_annual - benchmark_annual
            
            # 计算年度波动率
            strategy_vol = year_data['strategy'].std() * np.sqrt(252)
            benchmark_vol = year_data['benchmark'].std() * np.sqrt(252)
            
            # 计算年度年化收益（与年度收益相同，因为已经是年度数据）
            strategy_annualized = strategy_annual
            benchmark_annualized = benchmark_annual
            
            # 计算年度夏普比率
            strategy_sharpe = strategy_annualized / strategy_vol if strategy_vol > 0 else 0
            benchmark_sharpe = benchmark_annualized / benchmark_vol if benchmark_vol > 0 else 0
            
            # 计算年度最大回撤
            strategy_cum = year_strategy_nav / year_strategy_nav.iloc[0]  # 相对于年初
            strategy_dd = (strategy_cum / strategy_cum.expanding().max() - 1).min()
            
            benchmark_cum = year_benchmark_nav / year_benchmark_nav.iloc[0]  # 相对于年初
            benchmark_dd = (benchmark_cum / benchmark_cum.expanding().max() - 1).min()
            
            # 计算年度相对回撤（策略相对于基准的回撤）
            relative_nav = year_strategy_nav / year_benchmark_nav  # 策略相对基准的表现
            relative_cum = relative_nav / relative_nav.iloc[0]  # 相对于年初的相对表现
            relative_dd = (relative_cum / relative_cum.expanding().max() - 1).min()
            
            # 计算年度月胜率
            year_monthly_strategy = year_data['strategy'].resample('M').apply(lambda x: (1 + x).prod() - 1)
            year_monthly_benchmark = year_data['benchmark'].resample('M').apply(lambda x: (1 + x).prod() - 1)
            year_monthly_excess = year_monthly_strategy - year_monthly_benchmark
            year_win_rate = (year_monthly_excess > 0).mean() if len(year_monthly_excess) > 0 else 0
            
            yearly_data.append({
                '年份': str(year),
                '策略收益': strategy_annual,
                '基准收益': benchmark_annual,
                '超额收益': excess_annual,
                '策略年化收益': strategy_annualized,
                '基准年化收益': benchmark_annualized,
                '策略波动率': strategy_vol,
                '基准波动率': benchmark_vol,
                '策略夏普比率': strategy_sharpe,
                '基准夏普比率': benchmark_sharpe,
                '策略最大回撤': strategy_dd,
                '基准最大回撤': benchmark_dd,
                '相对回撤': relative_dd,
                '月胜率': year_win_rate,
                '交易天数': len(year_data)
            })
        
        # 创建年度数据DataFrame
        yearly_df = pd.DataFrame(yearly_data)
        
        # 添加累计表现行
        if overall_metrics and yearly_df is not None and len(yearly_df) > 0:
            strategy_metrics = overall_metrics['strategy_metrics']
            benchmark_metrics = overall_metrics['benchmark_metrics']
            excess_metrics = overall_metrics['excess_metrics']
            monthly_win_rate = overall_metrics['monthly_win_rate']
            
            # 计算整个期间的相对回撤（策略相对基准的最大回撤）
            overall_relative_nav = strategy_nav / benchmark_nav
            overall_relative_drawdown = (overall_relative_nav / overall_relative_nav.expanding().max() - 1).min()
            
            cumulative_row = {
                '年份': '累计表现',
                '策略收益': strategy_metrics['total_return'],
                '基准收益': benchmark_metrics['total_return'],
                '超额收益': strategy_metrics['total_return'] - benchmark_metrics['total_return'],
                '策略年化收益': strategy_metrics['annualized_return'],
                '基准年化收益': benchmark_metrics['annualized_return'],
                '策略波动率': strategy_metrics['volatility'],
                '基准波动率': benchmark_metrics['volatility'],
                '策略夏普比率': strategy_metrics['sharpe_ratio'],
                '基准夏普比率': benchmark_metrics['sharpe_ratio'],
                '策略最大回撤': strategy_metrics['max_drawdown'],
                '基准最大回撤': benchmark_metrics['max_drawdown'],
                '相对回撤': overall_relative_drawdown,
                '月胜率': monthly_win_rate['monthly_win_rate'],
                '交易天数': len(aligned_data)
            }
            
            # 使用pd.concat而不是append
            cumulative_df = pd.DataFrame([cumulative_row])
            yearly_df = pd.concat([yearly_df, cumulative_df], ignore_index=True)
        
        return yearly_df
    
    def print_enhanced_performance_report(self, enhanced_metrics: Dict, strategy_type: str) -> None:
        """
        打印增强的绩效报告
        
        参数:
            enhanced_metrics: 增强绩效指标字典
            strategy_type: 策略类型
        """
        print(f"\n{'='*80}")
        print(f"{strategy_type.upper()} 策略详细绩效报告")
        print(f"{'='*80}")
        
        # 基础绩效对比已集成到年度绩效表中，显示超额收益分析
        excess_metrics = enhanced_metrics['excess_metrics']
        
        print(f"\n【超额收益分析】")
        print(f"信息比率:        {excess_metrics['information_ratio']:>8.3f}")
        print(f"跟踪误差:        {excess_metrics['tracking_error']:>8.2%}")
        print(f"相对回撤:        {enhanced_metrics['relative_drawdown']:>8.2%}")
        
        # 月胜率分析
        win_rate_data = enhanced_metrics['monthly_win_rate']
        print(f"\n【月度胜率分析】")
        print(f"月胜率:          {win_rate_data['monthly_win_rate']:>8.1%}")
        print(f"总月份数:        {win_rate_data['total_months']:>8d}")
        print(f"获胜月份:        {win_rate_data['winning_months']:>8d}")
        print(f"失败月份:        {win_rate_data['losing_months']:>8d}")
        
        # 年度绩效分析（使用新的中文表头格式）
        yearly_df = enhanced_metrics['yearly_analysis']
        if not yearly_df.empty:
            print(f"\n【年度绩效分析】")
            # 创建动态表头，包含相对回撤
            print(f"{'年份':>8} {'策略收益':>10} {'基准收益':>10} {'超额收益':>10} {'策略夏普':>10} {'基准夏普':>10} {'相对回撤':>10} {'月胜率':>8}")
            print(f"{'-'*88}")
            for _, row in yearly_df.iterrows():
                if row['年份'] == '累计表现':
                    print(f"{'-'*88}")
                print(f"{row['年份']:>8} {row['策略收益']:>9.1%} {row['基准收益']:>9.1%} "
                      f"{row['超额收益']:>9.1%} {row['策略夏普比率']:>9.3f} {row['基准夏普比率']:>9.3f} "
                      f"{row['相对回撤']:>9.1%} {row['月胜率']:>7.1%}")
        
        print(f"\n{'='*80}")
    
    def calculate_benchmark_returns(self, 
                                   price_data: pd.DataFrame,
                                   strategy_type: str,
                                   rebalance_dates: pd.DatetimeIndex) -> pd.Series:
        """
        计算基准收益（50%+50%月度再平衡）
        
        参数:
            price_data: 价格数据
            strategy_type: 策略类型
            rebalance_dates: 再平衡日期
            
        返回:
            基准收益序列
        """
        if strategy_type == 'value_growth':
            col1, col2 = 'ValueR', 'GrowthR'
        elif strategy_type == 'big_small':
            col1, col2 = 'BigR', 'SmallR'
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
        
        # 检查所需列是否存在
        if col1 not in price_data.columns or col2 not in price_data.columns:
            raise ValueError(f"价格数据缺少必要的列: {[col1, col2]}")
        
        benchmark_returns = []
        
        for i, rebalance_date in enumerate(rebalance_dates):
            # 确定下一个再平衡日期
            if i < len(rebalance_dates) - 1:
                next_date = rebalance_dates[i + 1]
                period_data = price_data.loc[rebalance_date:next_date]
            else:
                period_data = price_data.loc[rebalance_date:]
            
            if len(period_data) <= 1:
                continue
            
            # 计算期间收益率
            period_returns = period_data.pct_change().dropna()
            
            # 50%+50%的组合收益
            portfolio_returns = 0.5 * period_returns[col1] + 0.5 * period_returns[col2]
            
            benchmark_returns.extend(portfolio_returns.tolist())
        
        # 构建完整的收益序列
        all_dates = price_data.index[1:]  # 排除第一个日期（无收益）
        benchmark_series = pd.Series(0.0, index=all_dates)
        
        # 填入基准收益
        current_idx = 0
        for i, rebalance_date in enumerate(rebalance_dates):
            if i < len(rebalance_dates) - 1:
                next_date = rebalance_dates[i + 1]
                period_mask = (all_dates >= rebalance_date) & (all_dates < next_date)
            else:
                period_mask = all_dates >= rebalance_date
            
            period_length = period_mask.sum()
            if period_length > 0 and current_idx < len(benchmark_returns):
                end_idx = min(current_idx + period_length, len(benchmark_returns))
                # 确保分配的值长度与目标索引长度匹配
                values_to_assign = benchmark_returns[current_idx:end_idx]
                target_indices = all_dates[period_mask]
                
                # 如果长度不匹配，截取或填充
                if len(values_to_assign) == len(target_indices):
                    benchmark_series.loc[target_indices] = values_to_assign
                elif len(values_to_assign) > len(target_indices):
                    # 截取多余的值
                    benchmark_series.loc[target_indices] = values_to_assign[:len(target_indices)]
                else:
                    # 填充不足的值（用最后一个值填充）
                    padded_values = values_to_assign + [values_to_assign[-1]] * (len(target_indices) - len(values_to_assign))
                    benchmark_series.loc[target_indices] = padded_values
                
                current_idx = end_idx
        
        return benchmark_series
    
    def run_voting_backtest(self,
                           voting_decisions: pd.DataFrame,
                           price_data: pd.DataFrame,
                           strategy_type: str,
                           start_date: str = '2013-01-01',
                           end_date: str = '2025-05-27') -> Dict:
        """
        运行多信号投票回测
        
        参数:
            voting_decisions: 投票决策数据
            price_data: 价格数据
            strategy_type: 策略类型
            start_date: 回测开始日期
            end_date: 回测结束日期
            
        返回:
            回测结果字典
        """
        print(f"\n=== {strategy_type} 多信号投票回测 ===")
        print(f"回测期间: {start_date} -> {end_date}")
        
        # 确定目标列
        if strategy_type == 'value_growth':
            target_col1, target_col2 = 'ValueR', 'GrowthR'
            direction_map = {1: target_col1, 0: target_col2}  # 1=Value, 0=Growth
        elif strategy_type == 'big_small':
            target_col1, target_col2 = 'BigR', 'SmallR'
            direction_map = {1: target_col1, 0: target_col2}  # 1=Big, 0=Small
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
        
        # 检查价格数据
        required_cols = [target_col1, target_col2]
        missing_cols = [col for col in required_cols if col not in price_data.columns]
        if missing_cols:
            raise ValueError(f"价格数据缺少必要的列: {missing_cols}")
        
        # 过滤时间范围
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        
        price_data_filtered = price_data.loc[start_ts:end_ts].copy()
        if price_data_filtered.empty:
            raise ValueError("指定时间范围内没有价格数据")
        
        # 生成交易信号
        trading_signals = []
        
        for decision_date, decision_data in voting_decisions.iterrows():
            # 根据T-2月的信号，在T月第一个交易日调仓
            # decision_date 是信号日期，需要找到对应的交易日期
            
            # 计算目标交易月份
            target_year = decision_date.year
            target_month = decision_date.month + 2
            
            # 处理跨年
            if target_month > 12:
                target_month -= 12
                target_year += 1
            
            # 找到目标月份的第一个交易日
            target_month_start = pd.Timestamp(target_year, target_month, 1)
            available_trading_dates = price_data_filtered.index[price_data_filtered.index >= target_month_start]
            
            # 如果没有可用的交易日期（如最新信号），设置为None
            if len(available_trading_dates) == 0:
                trading_date = None
            else:
                trading_date = available_trading_dates[0]
            
            # 确定持仓方向
            winning_direction = decision_data['winning_direction']
            target_asset = direction_map[winning_direction]
            
            trading_signals.append({
                'signal_date': decision_date,
                'trading_date': trading_date,
                'target_asset': target_asset,
                'winning_direction': winning_direction,
                'vote_confidence': decision_data.get('vote_confidence', 0)
            })
        
        if not trading_signals:
            print("警告: 没有生成任何交易信号")
            return {}
        
        trading_signals_df = pd.DataFrame(trading_signals)
        print(f"生成交易信号: {len(trading_signals_df)} 个")
        
        # 计算净值基准日期
        nav_base_date = pd.Timestamp('2013-01-04')
        
        # 如果基准日期不存在，找到最接近的交易日
        if nav_base_date not in price_data_filtered.index:
            available_dates = price_data_filtered.index[price_data_filtered.index >= nav_base_date]
            if len(available_dates) > 0:
                nav_base_date = available_dates[0]
            else:
                # 如果没有找到合适的日期，使用第一个交易日
                nav_base_date = price_data_filtered.index[0]
        
        print(f"净值基准日期: {nav_base_date.strftime('%Y-%m-%d')}")
        
        # 使用新的净值计算方法：基于持仓份额
        nav_results = self.calculate_nav_curves_by_shares(
            trading_signals_df, price_data_filtered, strategy_type, nav_base_date
        )
        
        strategy_nav = nav_results['strategy_nav']
        benchmark_nav = nav_results['benchmark_nav']
        
        # 基于净值计算收益率（用于绩效分析）
        strategy_returns_from_nav = strategy_nav.pct_change().dropna()
        benchmark_returns_from_nav = benchmark_nav.pct_change().dropna()
        
        print(f"基于净值计算的收益序列长度: 策略{len(strategy_returns_from_nav)}, 基准{len(benchmark_returns_from_nav)}")
        
        # 计算增强的绩效指标
        enhanced_metrics = self.calculate_enhanced_performance_metrics(
            strategy_returns_from_nav, benchmark_returns_from_nav
        )
        
        # 编译结果
        results = {
            'strategy_type': strategy_type,
            'trading_signals': trading_signals_df,
            'strategy_returns': strategy_returns_from_nav,
            'benchmark_returns': benchmark_returns_from_nav,
            'strategy_nav': strategy_nav,
            'benchmark_nav': benchmark_nav,
            'nav_base_date': nav_base_date,
            'enhanced_metrics': enhanced_metrics,
            'voting_decisions': voting_decisions
        }
        
        print(f"\n=== {strategy_type} 回测结果摘要 ===")
        self.print_enhanced_performance_report(enhanced_metrics, strategy_type)
        
        return results

    def calculate_nav_curves_by_shares(self,
                                      trading_signals_df: pd.DataFrame,
                                      price_data: pd.DataFrame,
                                      strategy_type: str,
                                      nav_base_date: pd.Timestamp) -> Dict:
        """
        基于持仓份额计算净值曲线
        
        参数:
            trading_signals_df: 交易信号数据
            price_data: 价格数据
            strategy_type: 策略类型
            nav_base_date: 净值基准日期（2013-01-04）
            
        返回:
            包含策略和基准净值序列的字典
        """
        # 确定资产列名
        if strategy_type == 'value_growth':
            asset1_col, asset2_col = 'ValueR', 'GrowthR'
        elif strategy_type == 'big_small':
            asset1_col, asset2_col = 'BigR', 'SmallR'
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
        
        # 获取净值计算期间的价格数据
        nav_price_data = price_data.loc[nav_base_date:].copy()
        
        if nav_price_data.empty:
            raise ValueError(f"净值基准日期 {nav_base_date} 之后没有价格数据")
        
        # 基准日期的价格（用于计算初始份额）
        base_price_asset1 = nav_price_data.iloc[0][asset1_col]
        base_price_asset2 = nav_price_data.iloc[0][asset2_col]
        
        print(f"净值基准日期: {nav_base_date.strftime('%Y-%m-%d')}")
        print(f"基准日价格: {asset1_col}={base_price_asset1:.4f}, {asset2_col}={base_price_asset2:.4f}")
        
        # 初始化净值序列
        strategy_nav = pd.Series(index=nav_price_data.index, dtype=float)
        benchmark_nav = pd.Series(index=nav_price_data.index, dtype=float)
        
        # 基准日期净值设为1.0
        strategy_nav.iloc[0] = 1.0
        benchmark_nav.iloc[0] = 1.0
        
        # 基准投资组合：始终50%+50%
        benchmark_shares_asset1 = 0.5 / base_price_asset1  # 基准50%资金购买asset1的份额
        benchmark_shares_asset2 = 0.5 / base_price_asset2  # 基准50%资金购买asset2的份额
        
        # 生成基准再平衡日期（每月第一个交易日）
        rebalance_dates = pd.date_range(start=nav_base_date, end=nav_price_data.index[-1], freq='MS')  # 每月第一天
        rebalance_dates = rebalance_dates[rebalance_dates.isin(nav_price_data.index)]  # 只保留实际交易日
        
        print(f"基准再平衡日期数量: {len(rebalance_dates)}")
        if len(rebalance_dates) > 0:
            print(f"再平衡日期范围: {rebalance_dates[0].strftime('%Y-%m-%d')} ~ {rebalance_dates[-1].strftime('%Y-%m-%d')}")
        
        # 策略初始持仓：根据第一个有效信号决定
        valid_signals = trading_signals_df[
            (trading_signals_df['trading_date'].notna()) & 
            (trading_signals_df['trading_date'] >= nav_base_date)
        ].sort_values('trading_date')
        
        # 确定策略初始持仓
        if not valid_signals.empty:
            first_signal = valid_signals.iloc[0]
            if first_signal['target_asset'] == asset1_col:
                strategy_shares_asset1 = 1.0 / base_price_asset1  # 100%资金购买asset1
                strategy_shares_asset2 = 0.0
            else:
                strategy_shares_asset1 = 0.0
                strategy_shares_asset2 = 1.0 / base_price_asset2  # 100%资金购买asset2
            
            print(f"策略初始持仓: {first_signal['target_asset']} 100%")
        else:
            # 如果没有有效信号，默认持有asset2（成长/小盘）
            strategy_shares_asset1 = 0.0
            strategy_shares_asset2 = 1.0 / base_price_asset2
            print(f"策略初始持仓: {asset2_col} 100% (无信号默认)")
        
        # 逐日计算净值
        rebalance_count = 0
        for i in range(1, len(nav_price_data)):
            current_date = nav_price_data.index[i]
            current_price_asset1 = nav_price_data.iloc[i][asset1_col]
            current_price_asset2 = nav_price_data.iloc[i][asset2_col]
            
            # 检查基准是否需要再平衡（每月第一个交易日）
            if current_date in rebalance_dates:
                # 计算再平衡前的基准净值
                current_benchmark_nav_value = (benchmark_shares_asset1 * current_price_asset1 + 
                                             benchmark_shares_asset2 * current_price_asset2)
                
                # 重新平衡为50%+50%
                benchmark_shares_asset1 = (current_benchmark_nav_value * 0.5) / current_price_asset1
                benchmark_shares_asset2 = (current_benchmark_nav_value * 0.5) / current_price_asset2
                
                rebalance_count += 1
                if rebalance_count <= 3:  # 只打印前3次再平衡详情
                    print(f"基准再平衡 {current_date.strftime('%Y-%m-%d')}: 净值={current_benchmark_nav_value:.4f}")
            
            # 检查策略是否有调仓信号
            signals_on_date = valid_signals[valid_signals['trading_date'] == current_date]
            
            if not signals_on_date.empty:
                # 有调仓信号：先计算调仓前的净值，然后调仓
                prev_strategy_nav_value = (strategy_shares_asset1 * current_price_asset1 + 
                                         strategy_shares_asset2 * current_price_asset2)
                
                # 调仓：将所有资金投入新的目标资产
                new_signal = signals_on_date.iloc[-1]  # 如果有多个信号取最后一个
                if new_signal['target_asset'] == asset1_col:
                    strategy_shares_asset1 = prev_strategy_nav_value / current_price_asset1
                    strategy_shares_asset2 = 0.0
                else:
                    strategy_shares_asset1 = 0.0
                    strategy_shares_asset2 = prev_strategy_nav_value / current_price_asset2
                
                print(f"策略调仓 {current_date.strftime('%Y-%m-%d')}: 切换至 {new_signal['target_asset']}")
            
            # 计算当日净值
            strategy_nav_value = (strategy_shares_asset1 * current_price_asset1 + 
                                strategy_shares_asset2 * current_price_asset2)
            benchmark_nav_value = (benchmark_shares_asset1 * current_price_asset1 + 
                                 benchmark_shares_asset2 * current_price_asset2)
            
            strategy_nav.iloc[i] = strategy_nav_value
            benchmark_nav.iloc[i] = benchmark_nav_value
        
        print(f"总共执行基准再平衡: {rebalance_count} 次")
        
        return {
            'strategy_nav': strategy_nav,
            'benchmark_nav': benchmark_nav,
            'strategy_shares_asset1': strategy_shares_asset1,
            'strategy_shares_asset2': strategy_shares_asset2,
            'benchmark_shares_asset1': benchmark_shares_asset1,
            'benchmark_shares_asset2': benchmark_shares_asset2
        } 
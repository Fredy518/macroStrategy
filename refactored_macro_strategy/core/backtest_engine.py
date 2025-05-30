"""
精简回测引擎
Streamlined backtest engine
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from scipy import stats
import multiprocessing
import os

from ..utils.validators import validate_backtest_inputs, check_data_alignment
from ..config.backtest_config import BacktestConfig


class BacktestEngine:
    """
    精简回测引擎 - 统一处理单向和双向测试
    """
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
    
    def calculate_trading_dates(self, signal_dates: pd.DatetimeIndex, 
                              price_data: pd.DataFrame) -> pd.DataFrame:
        """计算信号对应的交易日期"""
        trading_mapping = []
        
        for signal_date in signal_dates:
            # 计算第二个月的月初
            if signal_date.month == 11:
                target_year = signal_date.year + 1
                target_month = 1
            elif signal_date.month == 12:
                target_year = signal_date.year + 1
                target_month = 2
            else:
                target_year = signal_date.year
                target_month = signal_date.month + self.config.signal_delay_months
            
            target_month_start = pd.Timestamp(target_year, target_month, 1)
            available_dates = price_data.index[price_data.index >= target_month_start]
            
            trading_date = available_dates[0] if len(available_dates) > 0 else None
            
            trading_mapping.append({
                'signal_date': signal_date,
                'trading_date': trading_date
            })
        
        return pd.DataFrame(trading_mapping)
    
    def determine_position_direction(self, signal_value: any, 
                                   signal_type: str, 
                                   assumed_direction: int) -> int:
        """根据信号值、信号类型和假定指标方向确定仓位方向"""
        if pd.isna(signal_value):
            return 0
        
        # 基础方向：根据假定指标方向和信号值确定
        if assumed_direction == 1:
            base_direction = 1 if signal_value else -1
        else:  # assumed_direction == -1
            base_direction = -1 if signal_value else 1
        
        # 特殊处理：历史新低信号需要反向
        if signal_type == 'historical_new_low':
            base_direction = -base_direction
        
        return base_direction
    
    def calculate_portfolio_returns(self, signals: pd.Series,
                                  price_data: pd.DataFrame,
                                  signal_type: str,
                                  assumed_direction: int,
                                  effective_start_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """计算组合收益率"""
        
        # 获取回测标的对应的价格列
        target_col1, target_col2 = self.config.get_target_columns()
        
        # 检查价格数据是否包含所需列
        required_columns = [target_col1, target_col2]
        missing_cols = [col for col in required_columns if col not in price_data.columns]
        if missing_cols:
            raise ValueError(f"价格数据缺少必要的列: {missing_cols}")
        
        signals_filtered = signals.dropna()
        if signals_filtered.empty:
            return pd.DataFrame()
        
        # 计算信号对应的交易日期
        trading_mapping = self.calculate_trading_dates(signals_filtered.index, price_data)
        if trading_mapping.empty:
            return pd.DataFrame()
        
        # 生成交易
        trades = []
        current_position = 0
        
        for _, row in trading_mapping.iterrows():
            signal_date = row['signal_date']
            trading_date = row['trading_date']
            
            if trading_date is None or pd.Timestamp(trading_date) not in price_data.index:
                continue
            
            trading_date = pd.Timestamp(trading_date)
            signal_value = signals_filtered.loc[signal_date]
            target_position = self.determine_position_direction(signal_value, signal_type, assumed_direction)
            
            if target_position != current_position:
                trades.append({
                    'signal_date': signal_date,
                    'trading_date': trading_date,
                    'signal_value': signal_value,
                    'old_position': current_position,
                    'new_position': target_position,
                    f'{target_col1.lower()}_price': price_data.loc[trading_date, target_col1],
                    f'{target_col2.lower()}_price': price_data.loc[trading_date, target_col2]
                })
                current_position = target_position
        
        if not trades:
            return pd.DataFrame()
        
        # 计算收益
        trades_df = pd.DataFrame(trades)
        portfolio_returns_list = []
        
        for i in range(len(trades_df)):
            start_trade = trades_df.iloc[i]
            current_trading_date = start_trade['trading_date']
            position = start_trade['new_position']
            
            end_trading_date = trades_df.iloc[i + 1]['trading_date'] if i < len(trades_df) - 1 else price_data.index[-1]
            period_prices = price_data.loc[current_trading_date:end_trading_date]
            
            if len(period_prices) > 1:
                target1_daily_returns = period_prices[target_col1].pct_change().fillna(0)
                target2_daily_returns = period_prices[target_col2].pct_change().fillna(0)
                
                if position == 1:
                    # +1: 做多target1，做空target2 (多价值空成长 或 多大盘空小盘)
                    portfolio_daily_returns_series = target1_daily_returns - target2_daily_returns
                elif position == -1:
                    # -1: 做多target2，做空target1 (多成长空价值 或 多小盘空大盘)
                    portfolio_daily_returns_series = target2_daily_returns - target1_daily_returns
                else:
                    portfolio_daily_returns_series = pd.Series(0.0, index=period_prices.index)
                
                for date_idx, ret in portfolio_daily_returns_series.items():
                    if date_idx > current_trading_date:
                        portfolio_returns_list.append({
                            'date': date_idx,
                            'position': position,
                            'daily_return': ret,
                            'signal_date': start_trade['signal_date'],
                            'signal_value': start_trade['signal_value']
                        })
        
        return pd.DataFrame(portfolio_returns_list) if portfolio_returns_list else pd.DataFrame()
    
    def calculate_performance_metrics(self, returns_df: pd.DataFrame) -> Dict[str, float]:
        """计算回测业绩指标"""
        if returns_df.empty or 'daily_return' not in returns_df.columns:
            return {}
        
        daily_returns = returns_df['daily_return'].dropna()
        if daily_returns.empty:
            return {}
        
        # 计算月度收益
        returns_df_copy = returns_df.copy()
        returns_df_copy['date'] = pd.to_datetime(returns_df_copy['date'])
        returns_df_copy['year_month'] = returns_df_copy['date'].dt.to_period('M')
        monthly_returns = returns_df_copy.groupby('year_month')['daily_return'].apply(lambda x: (1 + x).prod() - 1).dropna()
        
        # 基础统计
        total_return_val = (1 + daily_returns).prod() - 1
        annualized_return_val = (1 + total_return_val) ** (252 / len(daily_returns)) - 1 if len(daily_returns) > 0 else 0.0
        volatility_val = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0.0
        information_ratio_val = annualized_return_val / volatility_val if volatility_val > 1e-9 else 0.0
        
        # 月度统计
        total_months = len(monthly_returns)
        win_rate_val = (monthly_returns > 0).sum() / total_months if total_months > 0 else 0.0
        monthly_avg_return_val = monthly_returns.mean() if total_months > 0 else 0.0
        
        # t检验
        t_stat_val, p_value_val = 0.0, 1.0
        df_ttest_val = 0
        if total_months > 1:
            clean_monthly_returns = monthly_returns.dropna()
            if len(clean_monthly_returns) > 1:
                t_stat_val, p_value_val = stats.ttest_1samp(clean_monthly_returns, 0, nan_policy='omit')
                df_ttest_val = len(clean_monthly_returns) - 1
        
        is_significant_val = 1 if df_ttest_val > 0 and p_value_val < self.config.significance_level else 0
        
        # 最大回撤
        cumulative_returns = (1 + daily_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown_val = drawdowns.min() if not drawdowns.empty else 0.0
        
        return {
            'total_return': float(total_return_val),
            'annualized_return': float(annualized_return_val),
            'volatility': float(volatility_val),
            'information_ratio': float(information_ratio_val),
            'win_rate': float(win_rate_val),
            'monthly_avg_return': float(monthly_avg_return_val),
            't_statistic': float(t_stat_val),
            'p_value': float(p_value_val),
            'df_ttest': int(df_ttest_val),
            'is_significant_0.05': int(is_significant_val),
            'max_drawdown': float(max_drawdown_val),
            'total_trades': len(returns_df['signal_date'].unique()) if 'signal_date' in returns_df.columns and not returns_df.empty else 0,
            'total_days': len(daily_returns),
            'total_months': total_months
        }
    
    def run_single_backtest(self, indicator_name: str,
                          signal_type: str,
                          parameter_n: int,
                          signals: pd.Series,
                          price_data: pd.DataFrame,
                          assumed_direction: int,
                          window_start_date: Optional[pd.Timestamp] = None,
                          memo_df: Optional[pd.DataFrame] = None) -> Dict[str, any]:
        """运行单个指标的回测"""
        try:
            if signals.empty:
                return {'error': f'指标 {indicator_name} 的信号序列为空'}
            
            returns_df = self.calculate_portfolio_returns(signals, price_data, signal_type, assumed_direction, window_start_date)
            
            if returns_df.empty:
                return {'error': '无有效交易数据'}
            
            performance = self.calculate_performance_metrics(returns_df)
            if not performance:
                return {'error': '无法计算业绩指标'}
            
            # 获取原始指标方向
            original_indicator_direction = None
            if memo_df is not None and 'index' in memo_df.columns and 'direction' in memo_df.columns:
                memo_df_copy = memo_df.copy()
                memo_df_copy['index'] = memo_df_copy['index'].astype(str)
                direction_series = memo_df_copy.set_index('index')['direction']
                if indicator_name in direction_series.index:
                    original_indicator_direction = int(direction_series.loc[indicator_name])
            
            result = {
                'indicator': indicator_name,
                'signal_type': signal_type,
                'parameter_n': parameter_n,
                'assumed_direction': assumed_direction,
                'original_indicator_direction': original_indicator_direction,
                'backtest_start_date': returns_df['date'].min().strftime('%Y-%m-%d') if not returns_df.empty and 'date' in returns_df.columns else None,
                'backtest_end_date': returns_df['date'].max().strftime('%Y-%m-%d') if not returns_df.empty and 'date' in returns_df.columns else None,
                'window_start_param': window_start_date.strftime('%Y-%m-%d') if window_start_date else None,
                **performance
            }
            return result
        except Exception as e:
            return {'error': f'回测过程中出现错误: {str(e)}'}
    
    def run_batch_backtest(self, test_results: Dict,
                         price_data: pd.DataFrame,
                         memo_df: Optional[pd.DataFrame] = None,
                         indicators: Optional[List[str]] = None,
                         signal_types: Optional[List[str]] = None,
                         window_start_date: Optional[pd.Timestamp] = None,
                         enable_parallel: Optional[bool] = None) -> pd.DataFrame:
        """批量运行回测 - 统一处理串行和并行"""
        
        use_parallel = enable_parallel if enable_parallel is not None else self.config.enable_parallel
        
        if use_parallel:
            return self._run_batch_backtest_parallel(test_results, price_data, memo_df, indicators, signal_types, window_start_date)
        else:
            return self._run_batch_backtest_serial(test_results, price_data, memo_df, indicators, signal_types, window_start_date)
    
    def _run_batch_backtest_serial(self, test_results: Dict, price_data: pd.DataFrame,
                                 memo_df: Optional[pd.DataFrame] = None,
                                 indicators: Optional[List[str]] = None,
                                 signal_types: Optional[List[str]] = None,
                                 window_start_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """串行批量回测"""
        print("开始串行回测...")
        backtest_results_list = []
        
        effective_signal_types = signal_types if signal_types is not None else list(test_results.keys())
        
        # 计算总任务数
        total_tasks = 0
        for st in effective_signal_types:
            if st not in test_results:
                continue
            for param_key, signal_data_for_param in test_results[st].items():
                current_indicators = indicators if indicators is not None else signal_data_for_param.columns
                for indicator_name in current_indicators:
                    if indicator_name not in signal_data_for_param.columns:
                        continue
                    signals_series = signal_data_for_param[indicator_name]
                    if not isinstance(signals_series, pd.Series) or signals_series.empty:
                        continue
                    # 双向测试
                    total_tasks += 2 if self.config.enable_dual_direction else 1
        
        if total_tasks == 0:
            print("警告: 没有有效的回测任务")
            return pd.DataFrame()
        
        print(f"共计 {total_tasks} 个回测组合")
        current_task = 0
        
        for st in effective_signal_types:
            if st not in test_results:
                continue
                
            for param_key, signal_data_for_param in test_results[st].items():
                try:
                    parameter_n = int(param_key.split('_')[1])
                except (IndexError, ValueError):
                    continue
                
                current_indicators = indicators if indicators is not None else signal_data_for_param.columns
                
                for indicator_name in current_indicators:
                    if indicator_name not in signal_data_for_param.columns:
                        continue
                    
                    signals_series = signal_data_for_param[indicator_name]
                    if not isinstance(signals_series, pd.Series) or signals_series.empty:
                        continue
                    
                    # 测试方向：根据配置确定
                    directions = [1, -1] if self.config.enable_dual_direction else [1]
                    
                    for assumed_dir in directions:
                        current_task += 1
                        if current_task % max(1, total_tasks // 20) == 0:
                            print(f"  进度: {current_task}/{total_tasks} ({(current_task/total_tasks*100):.0f}%)")
                        
                        result = self.run_single_backtest(
                            indicator_name, st, parameter_n, signals_series,
                            price_data, assumed_dir, window_start_date, memo_df
                        )
                        
                        if isinstance(result, dict) and 'error' not in result:
                            backtest_results_list.append(result)
        
        if not backtest_results_list:
            print("警告：串行回测完成，但没有成功的结果")
            return pd.DataFrame()
        
        final_results_df = pd.DataFrame(backtest_results_list)
        print(f"\n串行批量回测完成！成功回测 {len(final_results_df)} 个组合")
        return final_results_df
    
    def _run_batch_backtest_parallel(self, test_results: Dict, price_data: pd.DataFrame,
                                   memo_df: Optional[pd.DataFrame] = None,
                                   indicators: Optional[List[str]] = None,
                                   signal_types: Optional[List[str]] = None,
                                   window_start_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """并行批量回测"""
        print("开始并行回测...")
        
        # 准备并行任务
        task_args_list = self._prepare_parallel_tasks(test_results, price_data, memo_df, indicators, signal_types, window_start_date)
        
        if not task_args_list:
            print("警告: 没有有效的并行回测任务")
            return pd.DataFrame()
        
        processes = min(self.config.num_processes, os.cpu_count(), 60)
        print(f"开始并行批量回测，共 {len(task_args_list)} 个任务，使用 {processes} 个进程...")
        
        try:
            with multiprocessing.Pool(processes=processes) as pool:
                results_list = pool.starmap(self._run_single_backtest_wrapper, task_args_list)
        except Exception as e:
            print(f"并行回测过程中发生错误: {e}")
            return pd.DataFrame()
        
        # 处理结果
        successful_results = []
        error_count = 0
        for res in results_list:
            if isinstance(res, dict) and 'error' in res:
                error_count += 1
            elif isinstance(res, dict):
                successful_results.append(res)
            else:
                error_count += 1
        
        if error_count > 0:
            print(f"发现 {error_count} 个任务执行失败")
        
        if not successful_results:
            print("警告：并行回测没有成功的结果")
            return pd.DataFrame()
        
        final_results_df = pd.DataFrame(successful_results)
        print(f"\n并行批量回测完成！成功回测 {len(final_results_df)} 个组合")
        return final_results_df
    
    def _prepare_parallel_tasks(self, test_results: Dict, price_data: pd.DataFrame,
                              memo_df: Optional[pd.DataFrame] = None,
                              indicators: Optional[List[str]] = None,
                              signal_types: Optional[List[str]] = None,
                              window_start_date: Optional[pd.Timestamp] = None) -> List[Tuple]:
        """准备并行任务参数列表"""
        task_args_list = []
        effective_signal_types = signal_types if signal_types is not None else list(test_results.keys())
        
        for st in effective_signal_types:
            if st not in test_results:
                continue
                
            for param_key, signal_data_for_param in test_results[st].items():
                try:
                    parameter_n = int(param_key.split('_')[1])
                except (IndexError, ValueError):
                    continue
                
                current_indicators = indicators if indicators is not None else signal_data_for_param.columns
                
                for indicator_name in current_indicators:
                    if indicator_name not in signal_data_for_param.columns:
                        continue
                    
                    signals_series = signal_data_for_param[indicator_name]
                    if not isinstance(signals_series, pd.Series) or signals_series.empty:
                        continue
                    
                    # 测试方向
                    directions = [1, -1] if self.config.enable_dual_direction else [1]
                    
                    for assumed_dir in directions:
                        task_args_list.append((
                            indicator_name, st, parameter_n, signals_series, price_data,
                            assumed_dir, window_start_date, memo_df
                        ))
        
        return task_args_list
    
    def _run_single_backtest_wrapper(self, *args) -> Dict[str, any]:
        """并行回测的单个任务包装器"""
        return self.run_single_backtest(*args) 
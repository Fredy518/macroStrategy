"""
稳定性分析工作流
Stability Analysis Workflow
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
import concurrent.futures # 导入并行处理模块
import functools # 导入functools，用于partial函数

from ..core.stability_analyzer import RankingStabilityAnalyzer, StabilityConfig
from ..core.signal_engine import SignalEngine
from ..core.backtest_engine import BacktestEngine
from ..core.result_processor import ResultProcessor
from ..config import SignalConfig, BacktestConfig, ExportConfig
from ..utils.data_loader import load_all_data


def _run_single_window_task(
    signal_engine: SignalEngine,
    backtest_engine: BacktestEngine,
    signal_config: SignalConfig,
    window_data: Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]], # (indicator_data, price_data, memo_data)
    window_id: int,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    signal_types: Optional[List[str]] = None,
    indicators: Optional[List[str]] = None
) -> Optional[pd.DataFrame]:
    """
    辅助函数：处理单个滚动窗口的回测任务
    """
    window_indicator_data, window_price_data, memo_data = window_data

    print(f"--- 处理窗口 {window_id}: {window_start.strftime('%Y-%m-%d')} -> {window_end.strftime('%Y-%m-%d')} ---")

    # 生成信号
    print(f"窗口 {window_id}: 生成信号...")
    try:
        window_signals = signal_engine.comprehensive_parameter_test(
            data=window_indicator_data,
            test_params=signal_config.TEST_PARAMS,
            signal_types=signal_types
        )

        if not window_signals:
            print(f"窗口 {window_id}: 信号生成失败，跳过")
            return None

    except Exception as e:
        print(f"窗口 {window_id}: 信号生成异常 - {e}")
        return None

    # 执行回测
    print(f"窗口 {window_id}: 执行回测...")
    try:
        window_results = backtest_engine.run_batch_backtest(
            test_results=window_signals,
            price_data=window_price_data,
            memo_df=memo_data,
            indicators=indicators,
            signal_types=signal_types,
            enable_parallel=False  # 批量回测内部是否并行由BacktestConfig控制，这里只是单个窗口任务
        )

        if window_results.empty:
            print(f"窗口 {window_id}: 回测无结果，跳过")
            return None

        # 添加窗口信息
        window_results = window_results.copy()
        window_results['window_id'] = window_id
        window_results['window_start_date'] = window_start
        window_results['window_end_date'] = window_end

        # 筛选显著正向结果 (可选，取决于后续分析是否需要所有结果)
        # significant_positive = window_results[
        #     (window_results['is_significant_0.05'] == 1) &
        #     (window_results['t_statistic'] > 0)
        # ]

        print(f"窗口 {window_id}: 完成，共 {len(window_results)} 条结果") # 修正打印，不再只显示显著正向数量

        return window_results

    except Exception as e:
        print(f"窗口 {window_id}: 回测异常 - {e}")
        return None


class StabilityWorkflow:
    """
    稳定性分析工作流
    
    集成滚动回测和基于排名的稳定性分析
    """
    
    def __init__(self, 
                 signal_config: Optional[SignalConfig] = None,
                 backtest_config: Optional[BacktestConfig] = None,
                 stability_config: Optional[StabilityConfig] = None,
                 export_config: Optional[ExportConfig] = None):
        
        self.signal_config = signal_config or SignalConfig()
        self.backtest_config = backtest_config or BacktestConfig()
        self.stability_config = stability_config or StabilityConfig()
        self.export_config = export_config or ExportConfig()
        
        # 同步回测标的配置
        self.export_config.backtest_target = self.backtest_config.backtest_target
        
        # 初始化引擎
        self.signal_engine = SignalEngine(self.signal_config)
        self.backtest_engine = BacktestEngine(self.backtest_config)
        self.result_processor = ResultProcessor(self.export_config)
        self.stability_analyzer = RankingStabilityAnalyzer(
            self.stability_config, self.export_config
        )
    
    def run_rolling_window_backtest(self, 
                                  data_path: str,
                                  window_years: int = 3,
                                  step_months: int = 3,
                                  signal_types: Optional[List[str]] = None,
                                  indicators: Optional[List[str]] = None) -> pd.DataFrame:
        """
        运行滚动窗口回测，收集原始数据用于稳定性分析
        
        参数:
            data_path: 数据文件路径
            window_years: 滚动窗口年数
            step_months: 步进月数
            signal_types: 信号类型列表
            indicators: 指标列表
            
        返回:
            包含所有窗口回测结果的DataFrame
        """
        print("="*80)
        print("滚动窗口回测 - 为稳定性分析收集数据")
        print("="*80)
        print(f"配置: 窗口={window_years}年, 步进={step_months}月")
        
        # 加载数据
        try:
            data_dict = load_all_data(data_path)
            indicator_data = data_dict['indicator_data']
            price_data = data_dict['price_data']
            memo_data = data_dict['memo_data']
        except Exception as e:
            print(f"数据加载失败: {e}")
            return pd.DataFrame()
        
        # 获取信号类型和指标
        signal_types = signal_types or self.signal_config.SIGNAL_TYPES
        if indicators is None and memo_data is not None:
            indicators = list(memo_data['index'].values)  # 修正列名
        elif indicators is None:
            indicators = list(indicator_data.columns)
        
        print(f"回测配置: {len(signal_types)}种信号类型, {len(indicators)}个指标")
        
        # 准备滚动窗口任务列表
        min_date = indicator_data.index.min()
        max_date = indicator_data.index.max()
        
        print(f"数据时间范围: {min_date.strftime('%Y-%m-%d')} -> {max_date.strftime('%Y-%m-%d')}")
        
        # 强制设置分析起始时间为2013年1月1日（避免金融危机等特殊时期的影响）
        analysis_start_date = pd.Timestamp('2013-01-01')
        current_start = analysis_start_date
        print(f"滚动分析起始时间: {current_start.strftime('%Y-%m-%d')} (强制从2013年开始，排除2008-2012年)")
        
        # 检查起始时间是否在数据范围内
        if current_start < min_date:
            print(f"警告：起始时间 {current_start.strftime('%Y-%m-%d')} 早于数据起始时间 {min_date.strftime('%Y-%m-%d')}")
            current_start = min_date
            print(f"调整为数据起始时间: {current_start.strftime('%Y-%m-%d')}")
        elif current_start > max_date:
            print(f"错误：起始时间 {current_start.strftime('%Y-%m-%d')} 晚于数据结束时间 {max_date.strftime('%Y-%m-%d')}")
            return pd.DataFrame()
        
        window_id = 0
        
        window_tasks = []
        
        while True:
            window_id += 1
            window_end = current_start + pd.DateOffset(years=window_years)
            
            # 严格检查窗口有效性 - 确保窗口结束日期不超过数据范围
            if window_end > max_date:
                print(f"窗口 {window_id}: 结束日期 {window_end.strftime('%Y-%m-%d')} 超过数据范围 {max_date.strftime('%Y-%m-%d')}，停止滚动")
                print(f"共准备 {window_id-1} 个满足{window_years}年要求的窗口任务")
                break
            
            # 计算窗口实际年限 (更精确的计算)
            actual_window_years = (window_end - current_start).days / 365.25
            
            # 严格要求窗口必须满足指定年限 (允许小幅度偏差，如0.1年)
            if actual_window_years < window_years - 0.1:
                print(f"窗口 {window_id}: 实际年限 {actual_window_years:.2f} 不足 {window_years} 年，跳过")
                current_start += pd.DateOffset(months=step_months)
                continue
            
            # 提取窗口数据
            window_indicator_data = indicator_data.loc[current_start:window_end]
            window_price_data = price_data.loc[current_start:window_end]
            
            # 验证窗口数据充足性 (修正为月频数据逻辑)
            # 对于月频宏观数据，每年约12个数据点
            min_data_points = window_years * 12  # 月频数据：每年12个月
            min_required_points = int(min_data_points * 0.8)  # 允许20%的缺失
            
            if len(window_indicator_data) < min_required_points:
                print(f"窗口 {window_id}: 数据点不足，实际{len(window_indicator_data)}点，需要至少{min_required_points}点，跳过")
                current_start += pd.DateOffset(months=step_months)
                continue
            
            # 输出窗口详细信息用于验证
            print(f"窗口 {window_id}: {current_start.strftime('%Y-%m-%d')} -> {window_end.strftime('%Y-%m-%d')} "
                  f"({actual_window_years:.2f}年, {len(window_indicator_data)}个数据点)")

            # 将窗口任务添加到列表
            window_tasks.append((
                (window_indicator_data, window_price_data, memo_data), # window_data tuple
                window_id,
                current_start,
                window_end,
                signal_types,
                indicators
            ))
            
            # 移动到下一个窗口
            current_start += pd.DateOffset(months=step_months)

        print(f"共准备 {len(window_tasks)} 个窗口任务")

        # 使用ProcessPoolExecutor并行执行窗口任务
        all_window_results = []
        # 传递必要的配置和引擎实例到辅助函数
        _run_task_with_engines = functools.partial(
            _run_single_window_task,
            self.signal_engine,
            self.backtest_engine,
            self.signal_config
        )

        # max_workers=None 会使用机器的CPU核心数
        with concurrent.futures.ProcessPoolExecutor(max_workers=None) as executor:
            # 使用map方法并行处理任务，参数需要解包
            # 由于map只接收一个可迭代对象，我们需要重新组织window_tasks或使用starmap
            # starmap 需要一个包含参数元组的列表
            futures = [executor.submit(_run_task_with_engines, *task_args) for task_args in window_tasks]

            for future in concurrent.futures.as_completed(futures):
                try:
                    window_results = future.result()
                    if window_results is not None:
                        all_window_results.append(window_results)
                except Exception as exc:
                    print(f'单个窗口任务生成异常: {exc}')

        # 合并所有结果
        if not all_window_results:
            print("没有有效的窗口结果")
            return pd.DataFrame()

        final_results = pd.concat(all_window_results, ignore_index=True)
        print(f"\n滚动回测完成: 共 {len(final_results)} 条记录，"
              f"涉及 {final_results['window_id'].nunique()} 个窗口")

        # 导出原始结果
        try:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            target_suffix = f"_{self.backtest_config.backtest_target}"
            raw_output_path = f"signal_test_results/rolling_raw_results{target_suffix}_{timestamp}.xlsx"
            os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)
            final_results.to_excel(raw_output_path, index=False)
            print(f"原始滚动结果已导出: {raw_output_path}")
        except Exception as e:
            print(f"导出原始滚动结果失败: {e}")

        return final_results
    
    def run_complete_stability_analysis(self, 
                                      data_path: str,
                                      window_years: int = 3,
                                      step_months: int = 3,
                                      signal_types: Optional[List[str]] = None,
                                      indicators: Optional[List[str]] = None) -> Dict[str, any]:
        """
        运行完整的稳定性分析流程
        
        参数:
            data_path: 数据文件路径
            window_years: 滚动窗口年数
            step_months: 步进月数
            signal_types: 信号类型列表
            indicators: 指标列表
            
        返回:
            包含稳定性分析结果的字典
        """
        print("="*80)
        print("完整稳定性分析流程")
        print("="*80)
        
        # 1. 运行滚动窗口回测
        rolling_results = self.run_rolling_window_backtest(
            data_path, window_years, step_months, signal_types, indicators
        )
        
        if rolling_results.empty:
            print("滚动回测无结果，稳定性分析终止")
            return {}
        
        # 2. 运行基于排名的稳定性分析
        stability_results = self.stability_analyzer.run_complete_stability_analysis(
            rolling_results
        )
        
        # 3. 综合结果
        complete_results = {
            'rolling_results': rolling_results,
            **stability_results
        }
        
        print("\n" + "="*80)
        print("完整稳定性分析流程结束")
        print("="*80)
        
        return complete_results
    
    def run_stability_analysis_on_existing_data(self, 
                                              rolling_results_file: str) -> Dict[str, any]:
        """
        在已有滚动回测结果上运行稳定性分析
        
        参数:
            rolling_results_file: 滚动回测结果文件路径
            
        返回:
            稳定性分析结果
        """
        print("="*80)
        print("基于现有数据的稳定性分析")
        print("="*80)
        
        try:
            # 加载现有数据
            rolling_results = pd.read_excel(rolling_results_file)
            print(f"已加载滚动结果: {len(rolling_results)} 条记录，"
                  f"{rolling_results['window_id'].nunique()} 个窗口")
            
            # 运行稳定性分析
            stability_results = self.stability_analyzer.run_complete_stability_analysis(
                rolling_results
            )
            
            return stability_results
            
        except Exception as e:
            print(f"基于现有数据的稳定性分析失败: {e}")
            return {}
    
    def compare_stability_across_targets(self, 
                                       data_path: str,
                                       window_years: int = 3,
                                       step_months: int = 3) -> Dict[str, any]:
        """
        比较不同回测标的的稳定性
        
        参数:
            data_path: 数据文件路径
            window_years: 滚动窗口年数
            step_months: 步进月数
            
        返回:
            比较结果字典
        """
        print("="*80)
        print("跨回测标的稳定性比较")
        print("="*80)
        
        comparison_results = {}
        
        for target in ['value_growth', 'big_small']:
            print(f"\n--- 分析回测标的: {target} ---")
            
            # 更新配置
            self.backtest_config.backtest_target = target
            self.backtest_engine = BacktestEngine(self.backtest_config)
            
            # 运行分析
            target_results = self.run_complete_stability_analysis(
                data_path, window_years, step_months
            )
            
            comparison_results[target] = target_results
        
        # 生成比较报告
        try:
            self._generate_comparison_report(comparison_results)
        except Exception as e:
            print(f"生成比较报告失败: {e}")
        
        return comparison_results
    
    def _generate_comparison_report(self, comparison_results: Dict[str, any]) -> None:
        """生成跨标的比较报告"""
        print("\n" + "="*50)
        print("跨回测标的稳定性比较报告")
        print("="*50)
        
        for target, results in comparison_results.items():
            if 'stability_analysis' in results and not results['stability_analysis'].empty:
                stability_df = results['stability_analysis']
                print(f"\n>>> {target.upper()} 回测标的:")
                print(f"  分析组合数: {len(stability_df)}")
                print(f"  平均稳定性得分: {stability_df['overall_stability_score'].mean():.3f}")
                print(f"  高稳定组合数 (>0.5): {len(stability_df[stability_df['overall_stability_score'] > 0.5])}")
                
                # Top 3 最稳定组合
                top_3 = stability_df.head(3)
                print(f"  Top 3 最稳定组合:")
                for i, (_, row) in enumerate(top_3.iterrows(), 1):
                    print(f"    {i}. {row['indicator']} - {row['signal_type']} "
                          f"(得分: {row['overall_stability_score']:.3f})")
        
        # 导出比较结果
        try:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            comparison_file = f"signal_test_results/stability_comparison_{timestamp}.xlsx"
            
            with pd.ExcelWriter(comparison_file, engine='openpyxl') as writer:
                for target, results in comparison_results.items():
                    if 'stability_analysis' in results and not results['stability_analysis'].empty:
                        results['stability_analysis'].to_excel(
                            writer, sheet_name=f'{target}_stability', index=False
                        )
            
            print(f"\n比较结果已导出: {comparison_file}")
            
        except Exception as e:
            print(f"导出比较结果失败: {e}") 
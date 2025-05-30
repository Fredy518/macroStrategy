"""
主工作流程
Main workflow for refactored macro strategy system
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime

from ..config.signal_config import SignalConfig
from ..config.backtest_config import BacktestConfig
from ..config.export_config import ExportConfig

from ..core.signal_engine import SignalEngine
from ..core.backtest_engine import BacktestEngine
from ..core.result_processor import ResultProcessor

from ..utils.validators import validate_dataframe_input


class MainWorkflow:
    """
    精简主工作流程 - 整合所有功能模块
    消除原有代码的重复和冗余
    """
    
    def __init__(self,
                 signal_config: Optional[SignalConfig] = None,
                 backtest_config: Optional[BacktestConfig] = None,
                 export_config: Optional[ExportConfig] = None):
        
        # 初始化配置
        self.signal_config = signal_config or SignalConfig()
        self.backtest_config = backtest_config or BacktestConfig()
        self.export_config = export_config or ExportConfig()
        
        # 同步回测标的配置
        self.export_config.backtest_target = self.backtest_config.backtest_target
        
        # 初始化引擎
        self.signal_engine = SignalEngine(self.signal_config)
        self.backtest_engine = BacktestEngine(self.backtest_config)
        self.result_processor = ResultProcessor(self.export_config)
    
    def load_data(self, data_path: str, memo_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
        """
        加载数据 - 参考processed.py的实现方式
        """
        print(f"加载数据...")
        
        def read_clean_data(file_path: str, sheet_name: str, skiprows: int, nrows: int):
            """辅助函数：按照processed.py的方式读取和清理数据"""
            return (
                pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows, nrows=nrows)
                .rename(columns={'日期': 'Date'})
                .set_index('Date')
                .sort_index()
            )
        
        try:
            if not data_path.endswith('.xlsx'):
                raise ValueError(f"不支持的文件格式: {data_path}，请提供.xlsx文件")
            
            # 1. 读取memo数据 (指标元数据)
            memo_df = None
            try:
                memo_raw = pd.read_excel(data_path, sheet_name='Memo')
                memo_df = memo_raw.rename(columns={
                    '指标_EN': 'index', 
                    '分类': 'categories', 
                    '方向': 'direction'
                })
                idx_need = memo_df['index'].tolist()
                print(f"Memo数据加载成功: {memo_df.shape}, 需要的指标数量: {len(idx_need)}")
            except Exception as e:
                print(f"警告: 无法加载Memo数据: {e}")
                idx_need = None
            
            # 2. 读取宏观指标数据
            try:
                macro_data = read_clean_data(data_path, 'CLEAN_MACRO', skiprows=3, nrows=250)
                print(f"CLEAN_MACRO工作表加载成功: {macro_data.shape}")
            except Exception as e:
                print(f"警告: 无法加载CLEAN_MACRO工作表: {e}")
                macro_data = pd.DataFrame()
            
            # 3. 读取利率数据
            try:
                rate_data = read_clean_data(data_path, 'CLEAN_RATE', skiprows=0, nrows=250)
                print(f"CLEAN_RATE工作表加载成功: {rate_data.shape}")
            except Exception as e:
                print(f"警告: 无法加载CLEAN_RATE工作表: {e}")
                rate_data = pd.DataFrame()
            
            # 4. 合并宏观指标和利率数据
            if not macro_data.empty and not rate_data.empty:
                data_combined = pd.concat([macro_data, rate_data], axis=1)
            elif not macro_data.empty:
                data_combined = macro_data
            elif not rate_data.empty:
                data_combined = rate_data
            else:
                raise ValueError("无法加载任何宏观指标或利率数据")
            
            # 5. 根据memo筛选需要的指标
            if idx_need is not None:
                # 筛选存在于数据中的指标
                available_indicators = [idx for idx in idx_need if idx in data_combined.columns]
                if available_indicators:
                    final_macro_data = data_combined[available_indicators].ffill()
                    print(f"按memo筛选指标: {len(available_indicators)}/{len(idx_need)} 个指标可用")
                else:
                    print("警告: memo中的指标在数据中都不存在，使用所有可用指标")
                    final_macro_data = data_combined.ffill()
            else:
                final_macro_data = data_combined.ffill()
            
            # 6. 读取价格数据 (CLOSE工作表)
            try:
                price_data = (
                    pd.read_excel(data_path, sheet_name='CLOSE', skiprows=3)
                    .rename(columns={
                        '时间': 'Date',
                        '300收益': 'BigR', 
                        '中证1000全收益': 'SmallR',
                        '创成长R': 'GrowthR', 
                        '国信价值全收益': 'ValueR'
                    })
                    .set_index('Date')
                    .sort_index()
                )
                
                # 确保有ValueR和GrowthR列
                if 'ValueR' not in price_data.columns or 'GrowthR' not in price_data.columns:
                    raise ValueError("价格数据缺少必要的ValueR或GrowthR列")
                
                print(f"价格数据加载成功: {price_data.shape}")
                
            except Exception as e:
                raise ValueError(f"无法加载价格数据 (CLOSE工作表): {e}")
            
            print(f"数据加载完成:")
            print(f"  宏观指标数据: {final_macro_data.shape}")
            print(f"  价格数据: {price_data.shape}")
            print(f"  memo数据: {'可用' if memo_df is not None else '不可用'}")
            
            # 基础验证
            validate_dataframe_input(final_macro_data)
            validate_dataframe_input(price_data, required_columns=['ValueR', 'GrowthR'])
            
            return final_macro_data, price_data, memo_df
            
        except Exception as e:
            print(f"数据加载失败: {e}")
            raise
    
    def run_signal_generation(self, macro_data: pd.DataFrame,
                            signal_types: Optional[List[str]] = None,
                            custom_test_params: Optional[Dict[str, List[int]]] = None) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        运行信号生成 - 精简版
        """
        print("="*80)
        print("信号生成阶段")
        print("="*80)
        
        if signal_types is None:
            signal_types = self.signal_config.SIGNAL_TYPES
        
        if custom_test_params is None:
            custom_test_params = self.signal_config.TEST_PARAMS
        
        try:
            # 运行全面参数测试
            test_results = self.signal_engine.comprehensive_parameter_test(
                data=macro_data,
                test_params=custom_test_params,
                signal_types=signal_types
            )
            
            print(f"\n信号生成完成!")
            print(f"信号类型: {list(test_results.keys())}")
            
            return test_results
            
        except Exception as e:
            print(f"信号生成失败: {e}")
            raise
    
    def run_backtest(self, test_results: Dict,
                    price_data: pd.DataFrame,
                    memo_df: Optional[pd.DataFrame] = None,
                    indicators: Optional[List[str]] = None,
                    signal_types: Optional[List[str]] = None,
                    enable_parallel: Optional[bool] = None) -> pd.DataFrame:
        """
        运行回测 - 精简版
        """
        print("="*80)
        print("回测阶段")
        print("="*80)
        
        try:
            # 运行批量回测 (自动选择串行或并行)
            backtest_results = self.backtest_engine.run_batch_backtest(
                test_results=test_results,
                price_data=price_data,
                memo_df=memo_df,
                indicators=indicators,
                signal_types=signal_types,
                enable_parallel=enable_parallel
            )
            
            if backtest_results.empty:
                print("警告: 回测结果为空")
                return pd.DataFrame()
            
            print(f"\n回测完成!")
            print(f"成功回测组合: {len(backtest_results)}")
            
            return backtest_results
            
        except Exception as e:
            print(f"回测失败: {e}")
            raise
    
    def run_analysis_and_export(self, backtest_results: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
        """
        运行分析和导出 - 精简版
        """
        print("="*80)
        print("结果分析和导出阶段")
        print("="*80)
        
        try:
            # 结果分析
            self.result_processor.analyze_results(backtest_results)
            
            # 筛选最佳结果
            filtered_results = self.result_processor.filter_best_significant_results(backtest_results)
            
            # 对比分析
            if not filtered_results.empty:
                self.result_processor.compare_analysis(backtest_results, filtered_results)
            
            # 导出结果
            export_path = self.result_processor.export_results(backtest_results, filtered_results)
            
            print(f"\n分析和导出完成!")
            return filtered_results, export_path
            
        except Exception as e:
            print(f"分析和导出失败: {e}")
            raise
    
    def run_complete_workflow(self, data_path: str,
                            memo_path: Optional[str] = None,
                            signal_types: Optional[List[str]] = None,
                            indicators: Optional[List[str]] = None,
                            enable_parallel: Optional[bool] = None) -> Dict[str, any]:
        """
        运行完整工作流程 - 一键执行
        """
        print("="*100)
        print("宏观策略精简工作流程开始")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        try:
            # 1. 数据加载
            macro_data, price_data, memo_df = self.load_data(data_path, memo_path)
            
            # 2. 信号生成
            test_results = self.run_signal_generation(
                macro_data=macro_data,
                signal_types=signal_types
            )
            
            # 3. 回测
            backtest_results = self.run_backtest(
                test_results=test_results,
                price_data=price_data,
                memo_df=memo_df,
                indicators=indicators,
                signal_types=signal_types,
                enable_parallel=enable_parallel
            )
            
            if backtest_results.empty:
                print("工作流程提前终止: 无有效回测结果")
                return {}
            
            # 4. 分析和导出
            filtered_results, export_path = self.run_analysis_and_export(backtest_results)
            
            # 5. 生成最终报告
            performance_report = self.result_processor.generate_performance_report(backtest_results)
            
            print("="*100)
            print("工作流程完成!")
            print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"结果文件: {export_path}")
            print("="*100)
            
            return {
                'backtest_results': backtest_results,
                'filtered_results': filtered_results,
                'export_path': export_path,
                'performance_report': performance_report,
                'data_info': {
                    'macro_data_shape': macro_data.shape,
                    'price_data_shape': price_data.shape,
                    'memo_available': memo_df is not None
                }
            }
            
        except Exception as e:
            print(f"工作流程执行失败: {e}")
            raise
    
    def get_configuration_summary(self) -> Dict[str, any]:
        """获取配置摘要"""
        return {
            'signal_config': {
                'signal_types': self.signal_config.SIGNAL_TYPES,
                'default_params': self.signal_config.DEFAULT_SIGNAL_PARAMS,
                'test_params_count': {k: len(v) for k, v in self.signal_config.TEST_PARAMS.items()}
            },
            'backtest_config': {
                'enable_parallel': self.backtest_config.enable_parallel,
                'num_processes': self.backtest_config.num_processes,
                'enable_dual_direction': self.backtest_config.enable_dual_direction,
                'significance_level': self.backtest_config.significance_level
            },
            'export_config': {
                'output_dir': self.export_config.output_dir,
                'backtest_filename': self.export_config.backtest_filename
            }
        }
    
    def quick_test(self, data_path: str, 
                  sample_indicators: Optional[List[str]] = None,
                  sample_signal_types: Optional[List[str]] = None) -> Dict[str, any]:
        """
        快速测试 - 用于验证功能
        """
        print("="*80)
        print("快速测试模式")
        print("="*80)
        
        # 临时配置 - 减少测试范围
        original_test_params = self.signal_config.TEST_PARAMS.copy()
        original_enable_parallel = self.backtest_config.enable_parallel
        
        try:
            # 简化测试参数
            simplified_params = {
                'historical_high': [12],
                'marginal_improvement': [3],
                'exceed_expectation': [12],
                'historical_new_high': [12],
                'historical_new_low': [12]
            }
            self.signal_config.TEST_PARAMS = simplified_params
            self.backtest_config.enable_parallel = False  # 快速测试用串行
            
            # 运行简化流程
            result = self.run_complete_workflow(
                data_path=data_path,
                signal_types=sample_signal_types or ['historical_high', 'marginal_improvement'],
                indicators=sample_indicators,
                enable_parallel=False
            )
            
            print("快速测试完成!")
            return result
            
        finally:
            # 恢复原始配置
            self.signal_config.TEST_PARAMS = original_test_params
            self.backtest_config.enable_parallel = original_enable_parallel 
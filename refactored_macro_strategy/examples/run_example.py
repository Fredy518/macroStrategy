"""
重构后宏观策略系统使用示例
Example usage of refactored macro strategy system
"""

import sys
import os

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (macroStrategy)
project_root = os.path.dirname(os.path.dirname(current_dir))

# 添加项目根目录到路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以正常导入包
from refactored_macro_strategy import MainWorkflow, SignalConfig, BacktestConfig, ExportConfig


def basic_example():
    """
    基础使用示例 - 使用默认配置
    """
    print("="*80)
    print("基础使用示例")
    print("="*80)
    
    # 创建工作流实例 (使用默认配置)
    workflow = MainWorkflow()
    
    # 显示配置摘要
    config_summary = workflow.get_configuration_summary()
    print("当前配置摘要:")
    for category, settings in config_summary.items():
        print(f"  {category}: {settings}")
    
    # 设置数据路径 (需要根据实际情况修改)
    data_path = "宏观指标与逻辑.xlsx"  # 文件在项目根目录
    
    # 检查文件是否存在
    if not os.path.exists(data_path):
        print(f"数据文件不存在: {data_path}")
        print("请确保数据文件路径正确")
        return
    
    try:
        # 运行完整工作流程
        results = workflow.run_complete_workflow(
            data_path=data_path,
            enable_parallel=False  # 示例中使用串行处理
        )
        
        # 显示结果摘要
        if results:
            print("\n结果摘要:")
            print(f"  回测组合总数: {len(results['backtest_results'])}")
            print(f"  筛选后组合数: {len(results['filtered_results'])}")
            print(f"  导出文件: {results['export_path']}")
            print(f"  数据信息: {results['data_info']}")
        
    except Exception as e:
        print(f"执行失败: {e}")


def run_value_growth_complete_test(data_path):
    """
    运行价值成长完整回测示例
    """
    print("="*80)
    print("开始运行：价值成长完整回测")
    print("="*80)
    
    # 价值成长回测配置
    value_growth_config = BacktestConfig(
        backtest_target='value_growth',  # 设置为价值成长回测
        enable_parallel=True  # 完整回测启用并行
    )
    
    workflow_vg = MainWorkflow(backtest_config=value_growth_config)
    
    print(f"回测目标列: {value_growth_config.get_target_columns()}")
    
    try:
        # 完整测试价值成长
        results_vg = workflow_vg.run_complete_workflow(data_path)
        print(f"\n=== 价值成长完整回测完成 ===")
        print(f"输出文件: {results_vg.get('output_file', 'N/A')}")
        print(f"注意: 文件名包含'_value_growth'后缀")
        
    except Exception as e:
        print(f"价值成长完整回测失败: {e}")


def run_big_small_complete_test(data_path):
    """
    运行大小盘完整回测示例
    """
    print("="*80)
    print("开始运行：大小盘完整回测")
    print("="*80)
    
    # 自定义信号配置 - 使用所有信号类型
    signal_config = SignalConfig()
    # 不限制信号类型，使用默认的所有信号类型
    
    # 自定义回测配置 - 大小盘回测
    backtest_config = BacktestConfig(
        backtest_target='big_small',  # 设置为大小盘回测
        enable_parallel=True,  # 使用并行处理加速完整回测
        enable_dual_direction=True  # 启用双向测试
    )
    
    # 自定义导出配置
    export_config = ExportConfig()
    
    # 创建工作流
    workflow = MainWorkflow(
        signal_config=signal_config,
        backtest_config=backtest_config,
        export_config=export_config
    )
    
    # 显示配置信息 (大小盘回测特有)
    print("回测配置信息:")
    print(f"  回测标的: {backtest_config.backtest_target}")
    print(f"  目标列: {backtest_config.get_target_columns()}")
    print(f"  交易逻辑: {backtest_config.get_trading_logic_description()}")
    print(f"  使用信号类型: {signal_config.SIGNAL_TYPES} (共{len(signal_config.SIGNAL_TYPES)}种)")
    # 这里的指标数量应该根据实际加载数据后的数量来显示，
    # 但在调用load_data之前无法准确获取最终使用的指标数量。
    # 我们可以先打印配置中定义的总数，或者在回测完成后再打印实际数量。
    # 为了准确性，我们在回测完成后打印实际使用的指标数量。
    # print(f"  配置中定义的总指标数量: {len(signal_config.get_all_indicators())}个")

    # 运行工作流
    try:
        # 使用所有指标和所有信号类型进行完整回测
        test_indicators = None # 使用所有指标 (会根据load_data和run_backtest中的逻辑确定最终列表)
        all_signal_types = None # 使用所有信号类型 (从配置中读取)

        print(f"\n预计回测组合数: {len(signal_config.get_all_indicators())} 指标(配置) × {len(signal_config.SIGNAL_TYPES)} 信号类型 × 多参数 × 2方向")
        
        results = workflow.run_complete_workflow(
            data_path=data_path,
            signal_types=all_signal_types, # 使用所有信号类型
            indicators=test_indicators,     # 使用所有指标
            enable_parallel=True # 开启并行加速完整回测
        )
        
        # 获取并打印实际使用的指标数量
        data_info = results.get('data_info', {})
        macro_data_shape = data_info.get('macro_data_shape', (0, 0))
        
        # 安全地获取指标数量
        if isinstance(macro_data_shape, tuple) and len(macro_data_shape) >= 2:
            actual_indicators_count = macro_data_shape[1]
        else:
            actual_indicators_count = "未知"
        
        print(f"实际使用指标数量: {actual_indicators_count}个")

        print(f"\n=== 大小盘完整回测完成 ===")
        print(f"输出文件: {results.get('output_file', 'N/A')}")
        print(f"注意: 文件名包含'_big_small'后缀，区分回测标的")
        
    except Exception as e:
        print(f"大小盘完整回测失败: {e}")


def run_all_complete_test(data_path):
    """
    运行全部完整回测示例 (大小盘和价值成长)
    """
    print("="*80)
    print("开始运行：全部完整回测 (大小盘 + 价值成长)")
    print("="*80)
    
    # 运行大小盘完整回测
    run_big_small_complete_test(data_path)
    
    print("\n" + "="*40)
    print("==== 开始价值成长完整回测 ====")
    print("="*40)
    
    # 运行价值成长完整回测
    run_value_growth_complete_test(data_path)
    
    print("\n全部完整回测示例完成!")
    





def run_big_small_stability_analysis(data_path):
    """
    运行大小盘稳定性分析示例
    """
    print("="*80)
    print("开始运行：大小盘稳定性分析")
    print("="*80)
    
    from refactored_macro_strategy.workflows.stability_workflow import StabilityWorkflow
    from refactored_macro_strategy.core.stability_analyzer import StabilityConfig
    from refactored_macro_strategy.config import BacktestConfig
    
    # 稳定性分析配置
    stability_config = StabilityConfig(
        high_stability_threshold=0.5,  # 高稳定性阈值
        min_appearance_windows=3,      # 最少出现窗口数 
        ranking_weight=0.2,            # 排名稳定性权重
        significance_weight=0.2,       # 显著性一致率权重
        performance_weight=0.2,        # 性能稳定性权重
        absolute_performance_weight=0.4 # 绝对表现权重
    )
    
    # 回测配置 - 大小盘
    backtest_config = BacktestConfig(
        backtest_target='big_small',
        enable_parallel=True  # 启用并行
    )
    
    # 创建稳定性工作流
    stability_workflow = StabilityWorkflow(
        backtest_config=backtest_config,
        stability_config=stability_config
    )
    
    print("稳定性分析配置:")
    print(f"  每窗口Top K: {stability_config.top_k_per_window}")
    print(f"  最少出现窗口: {stability_config.min_appearance_windows}")
    print(f"  回测标的: {backtest_config.backtest_target}")
    
    try:
        # 运行完整的稳定性分析
        print(f"\n开始滚动回测和稳定性分析...")
        
        results = stability_workflow.run_complete_stability_analysis(
            data_path=data_path,
            window_years=3,  # 5年滚动窗口
            step_months=3    # 3个月步进
        )
        
        if results and 'stability_analysis' in results:
            stability_df = results['stability_analysis']
            print(f"\n=== 大小盘稳定性分析完成 ===")
            print(f"分析的组合数: {len(stability_df)}")
            print(f"输出文件: {results.get('export_path', 'N/A')}")
        else:
            print("稳定性分析未产生有效结果")
        
    except Exception as e:
        print(f"稳定性分析失败: {e}")


def run_ranking_stability_analysis(data_path):
    """
    运行价值成长稳定性分析示例
    """
    print("="*80)
    print("开始运行：价值成长稳定性分析")
    print("="*80)
    
    from refactored_macro_strategy.workflows.stability_workflow import StabilityWorkflow
    from refactored_macro_strategy.core.stability_analyzer import StabilityConfig
    from refactored_macro_strategy.config import BacktestConfig
    
    # 稳定性分析配置
    stability_config = StabilityConfig(
        high_stability_threshold=0.5,  # 高稳定性阈值
        min_appearance_windows=3,      # 最少出现窗口数 
        ranking_weight=0.2,            # 排名稳定性权重
        significance_weight=0.2,       # 显著性一致率权重
        performance_weight=0.2,        # 性能稳定性权重
        absolute_performance_weight=0.4 # 绝对表现权重
    )
    
    # 回测配置 - 价值成长
    backtest_config = BacktestConfig(
        backtest_target='value_growth',
        enable_parallel=True  # 启用并行
    )
    
    # 创建稳定性工作流
    stability_workflow = StabilityWorkflow(
        backtest_config=backtest_config,
        stability_config=stability_config
    )
    
    print("稳定性分析配置:")
    print(f"  每窗口Top K: {stability_config.top_k_per_window}")
    print(f"  最少出现窗口: {stability_config.min_appearance_windows}")
    print(f"  回测标的: {backtest_config.backtest_target}")
    
    try:
        # 运行完整的稳定性分析
        print(f"\n开始滚动回测和稳定性分析...")
        
        results = stability_workflow.run_complete_stability_analysis(
            data_path=data_path,
            window_years=3,  # 5年滚动窗口
            step_months=3    # 3个月步进
        )
        
        if results and 'stability_analysis' in results:
            stability_df = results['stability_analysis']
            print(f"\n=== 价值成长稳定性分析完成 ===")
            print(f"分析的组合数: {len(stability_df)}")
            print(f"输出文件: {results.get('export_path', 'N/A')}")
        else:
            print("稳定性分析未产生有效结果")
        
    except Exception as e:
        print(f"稳定性分析失败: {e}")


def run_stability_comparison_across_targets(data_path):
    """
    运行跨回测标的的稳定性比较分析
    """
    print("="*80)
    print("开始运行：跨回测标的稳定性比较")
    print("="*80)
    
    from refactored_macro_strategy.workflows.stability_workflow import StabilityWorkflow
    from refactored_macro_strategy.core.stability_analyzer import StabilityConfig
    
    # 稳定性分析配置
    stability_config = StabilityConfig()
    
    # 创建稳定性工作流
    stability_workflow = StabilityWorkflow(
        stability_config=stability_config
    )
    
    try:
        # 运行跨标的比较分析
        print(f"\n开始价值成长 vs 大小盘稳定性比较分析...")
        
        comparison_results = stability_workflow.compare_stability_across_targets(
            data_path=data_path,
            window_years=3,  # 5年滚动窗口
            step_months=3    # 3个月步进
        )
        
        if comparison_results:
            print(f"\n=== 跨标的稳定性比较完成 ===")
            for target in comparison_results:
                if 'stability_analysis' in comparison_results[target]:
                    count = len(comparison_results[target]['stability_analysis'])
                    print(f"{target}: {count} 个稳定组合")
        else:
            print("跨标的比较分析未产生有效结果")
        
    except Exception as e:
        print(f"跨标的比较分析失败: {e}")


def run_stability_reanalysis_on_existing_data(rolling_results_file: str):
    """
    基于现有滚动回测数据重新计算稳定性分析
    用于在修改StabilityConfig设置后重新分析，无需重新运行耗时的滚动回测
    
    参数:
        rolling_results_file: 滚动回测结果文件路径
    """
    print("="*80)
    print("基于现有数据重新计算稳定性分析")
    print("="*80)
    
    # 从文件路径中推断回测目标（big_small或value_growth）
    if 'big_small' in rolling_results_file:
        backtest_target = 'big_small'
    elif 'value_growth' in rolling_results_file:
        backtest_target = 'value_growth'
    else:
        print(f"无法从文件名推断回测目标，请确保文件名包含'big_small'或'value_growth': {rolling_results_file}")
        backtest_target = 'value_growth'  # 默认使用value_growth
    
    print(f"检测到回测目标: {backtest_target}")
    
    # 配置回测目标和稳定性分析
    from refactored_macro_strategy.core.stability_analyzer import StabilityConfig
    
    backtest_config = BacktestConfig(backtest_target=backtest_target)
    
    # 创建稳定性配置（可以根据需要调整阈值）
    stability_config = StabilityConfig(
        high_stability_threshold=0.5,  # 可以调整这个阈值
        min_appearance_windows=3       # 可以调整最少出现窗口数
    )
    
    # 创建稳定性工作流
    from refactored_macro_strategy.workflows.stability_workflow import StabilityWorkflow
    
    stability_workflow = StabilityWorkflow(
        backtest_config=backtest_config,
        stability_config=stability_config
    )
    
    # 检查文件是否存在
    if not os.path.exists(rolling_results_file):
        print(f"滚动回测结果文件不存在: {rolling_results_file}")
        print("请确保文件路径正确")
        return
    
    print(f"使用配置:")
    print(f"  高稳定性阈值: {stability_config.high_stability_threshold}")
    print(f"  最少出现窗口: {stability_config.min_appearance_windows}")
    print(f"  回测目标: {backtest_target}")
    
    try:
        # 基于现有数据运行稳定性分析
        results = stability_workflow.run_stability_analysis_on_existing_data(rolling_results_file)
        
        if results and 'stability_analysis' in results:
            stability_df = results['stability_analysis']
            insights = results.get('insights', {})
            
            print(f"\n=== 稳定性重新分析完成 ===")
            print(f"分析的组合数量: {len(stability_df)}")
            print(f"平均稳定性得分: {stability_df['overall_stability_score'].mean():.3f}")
            
            # 使用配置的阈值
            high_stability_count = len(stability_df[
                stability_df['overall_stability_score'] > stability_config.high_stability_threshold
            ])
            print(f"高稳定组合数 (>{stability_config.high_stability_threshold}): {high_stability_count}")
            
            # 显示最佳组合推荐（如果有的话）
            if 'best_combinations_per_indicator' in insights:
                best_combos = insights['best_combinations_per_indicator']
                if not best_combos.empty:
                    print(f"\n★★★ 最佳组合推荐 (共 {len(best_combos)} 个指标) ★★★")
                    for i, (_, row) in enumerate(best_combos.head(10).iterrows(), 1):  # 只显示前10个
                        print(f"  {i:2d}. {row['indicator']:<25} | {row['signal_type']:<20}")
                        print(f"      综合得分: {row['overall_stability_score']:.3f} | "
                              f"平均IR: {row['ir_mean']:.3f} | "
                              f"出现窗口: {row['appearance_windows']}")
                else:
                    print(f"\n没有指标达到推荐标准 (得分>{stability_config.high_stability_threshold})")
            
            # 显示整体Top 5
            print(f"\nTop 5 最稳定组合 (按综合得分排序):")
            top_5 = stability_df.head(5)
            for i, (_, row) in enumerate(top_5.iterrows(), 1):
                print(f"  {i}. {row['indicator']} - {row['signal_type']} "
                      f"(N={row['parameter_n']}, Dir={row['assumed_direction']})")
                print(f"     综合得分: {row['overall_stability_score']:.3f} | "
                      f"平均IR: {row['ir_mean']:.3f} | "
                      f"出现窗口: {row['appearance_windows']}")
                print()
                
            print(f"输出文件: {results.get('export_path', 'N/A')}")
        else:
            print("稳定性重新分析失败或无结果")
            
    except Exception as e:
        print(f"稳定性重新分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_big_small_stability_reanalysis(data_path):
    """
    大小盘稳定性重新分析
    基于现有的大小盘滚动回测数据进行稳定性分析
    
    参数:
        data_path: 数据路径参数（本函数中被忽略，使用硬编码的文件路径）
    """
    print("="*80)
    print("大小盘稳定性重新分析")
    print("="*80)
    
    # 注意：忽略传入的data_path参数，使用指定的大小盘数据文件路径
    # 指定大小盘数据文件路径（用户提到的文件）
    rolling_results_file = "E:/CodePrograms/macroStrategy/signal_test_results/rolling_raw_results_big_small_20250530_111547.xlsx"
    
    # 检查文件是否存在
    if not os.path.exists(rolling_results_file):
        print(f"大小盘滚动回测结果文件不存在: {rolling_results_file}")
        print("请确保文件路径正确，或先运行大小盘完整回测")
        return
    
    print(f"找到大小盘数据文件: {rolling_results_file}")
    
    # 配置大小盘回测目标和稳定性分析
    from refactored_macro_strategy.core.stability_analyzer import StabilityConfig
    
    backtest_config = BacktestConfig(backtest_target='big_small')
    
    # 创建稳定性配置（针对大小盘优化的参数）
    stability_config = StabilityConfig(
        high_stability_threshold=0.5,  # 高稳定性阈值
        min_appearance_windows=3,      # 最少出现窗口数 
        ranking_weight=0.2,            # 排名稳定性权重
        significance_weight=0.2,       # 显著性一致率权重
        performance_weight=0.2,        # 性能稳定性权重
        absolute_performance_weight=0.4 # 绝对表现权重
    )
    
    # 创建稳定性工作流
    from refactored_macro_strategy.workflows.stability_workflow import StabilityWorkflow
    
    stability_workflow = StabilityWorkflow(
        backtest_config=backtest_config,
        stability_config=stability_config
    )
    
    print(f"稳定性分析配置:")
    print(f"  回测目标: big_small (大小盘)")
    print(f"  高稳定性阈值: {stability_config.high_stability_threshold}")
    print(f"  最少出现窗口: {stability_config.min_appearance_windows}")
    print(f"  权重配置: 排名={stability_config.ranking_weight}, "
          f"一致性={stability_config.significance_weight}, "
          f"性能={stability_config.performance_weight}, "
          f"绝对表现={stability_config.absolute_performance_weight}")
    
    try:
        print(f"\n开始分析大小盘稳定性...")
        
        # 基于现有数据运行稳定性分析
        results = stability_workflow.run_stability_analysis_on_existing_data(rolling_results_file)
        
        if results and 'stability_analysis' in results:
            stability_df = results['stability_analysis']
            insights = results.get('insights', {})
            
            print(f"\n=== 大小盘稳定性分析完成 ===")
            print(f"分析的组合数量: {len(stability_df)}")
            print(f"平均稳定性得分: {stability_df['overall_stability_score'].mean():.3f}")
            
            # 统计高稳定性组合
            high_stability_count = len(stability_df[
                stability_df['overall_stability_score'] > stability_config.high_stability_threshold
            ])
            print(f"高稳定组合数 (>{stability_config.high_stability_threshold}): {high_stability_count}")
            
            # 显示大小盘最佳组合推荐
            if 'best_combinations_per_indicator' in insights:
                best_combos = insights['best_combinations_per_indicator']
                if not best_combos.empty:
                    print(f"\n★★★ 大小盘最佳组合推荐 (共 {len(best_combos)} 个指标) ★★★")
                    for i, (_, row) in enumerate(best_combos.iterrows(), 1):
                        print(f"  {i:2d}. {row['indicator']:<30} | {row['signal_type']:<20}")
                        print(f"      综合得分: {row['overall_stability_score']:.3f} | "
                              f"平均IR: {row['ir_mean']:.3f} | "
                              f"出现窗口: {row['appearance_windows']}")
                        print(f"      参数配置: N={row['parameter_n']}, Dir={row['assumed_direction']}")
                        print()
                else:
                    print(f"\n没有指标达到推荐标准 (得分>{stability_config.high_stability_threshold})")
            
            # 显示大小盘Top 10
            print(f"\nTop 10 大小盘最稳定组合:")
            top_10 = stability_df.head(10)
            for i, (_, row) in enumerate(top_10.iterrows(), 1):
                print(f"  {i:2d}. {row['indicator']:<30} | {row['signal_type']:<20}")
                print(f"      综合得分: {row['overall_stability_score']:.3f} | "
                      f"平均IR: {row['ir_mean']:.3f} | "
                      f"出现窗口: {row['appearance_windows']}")
                print()
                
            print(f"详细结果导出到: {results.get('export_path', 'N/A')}")
            
            # 提供后续建议
            print(f"\n=== 使用建议 ===")
            if high_stability_count > 0:
                print(f"✓ 发现 {high_stability_count} 个高稳定性组合，可用于大小盘轮动策略")
                print(f"✓ 建议重点关注'最佳组合推荐'中的指标配置")
                if 'best_combinations_per_indicator' in insights and not insights['best_combinations_per_indicator'].empty:
                    best_ir = insights['best_combinations_per_indicator']['ir_mean'].max()
                    print(f"✓ 最佳平均IR: {best_ir:.3f}")
            else:
                print(f"⚠ 没有发现高稳定性组合，建议:")
                print(f"  - 降低阈值到0.3重新分析")
                print(f"  - 或检查数据质量和分析参数")
                
        else:
            print("大小盘稳定性分析失败或无结果")
            
    except Exception as e:
        print(f"大小盘稳定性分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_value_growth_stability_reanalysis(data_path):
    """
    价值成长稳定性重新分析
    基于现有的价值成长滚动回测数据进行稳定性分析
    
    参数:
        data_path: 数据路径参数（本函数中被忽略，使用硬编码的文件路径）
    """
    print("="*80)
    print("价值成长稳定性重新分析")
    print("="*80)
    
    # 注意：忽略传入的data_path参数，使用指定的价值成长数据文件路径
    # 指定价值成长数据文件路径（使用最新的文件）
    rolling_results_file = "E:/CodePrograms/macroStrategy/signal_test_results/rolling_raw_results_value_growth_20250529_150227.xlsx"
    
    # 检查文件是否存在
    if not os.path.exists(rolling_results_file):
        print(f"价值成长滚动回测结果文件不存在: {rolling_results_file}")
        print("请确保文件路径正确，或先运行价值成长完整回测")
        return
    
    print(f"找到价值成长数据文件: {rolling_results_file}")
    
    # 配置价值成长回测目标和稳定性分析
    from refactored_macro_strategy.core.stability_analyzer import StabilityConfig
    
    backtest_config = BacktestConfig(backtest_target='value_growth')
    
    # 创建稳定性配置（针对价值成长优化的参数）
    stability_config = StabilityConfig(
        high_stability_threshold=0.5,  # 高稳定性阈值
        min_appearance_windows=3,      # 最少出现窗口数 
        ranking_weight=0.2,            # 排名稳定性权重
        significance_weight=0.2,       # 显著性一致率权重
        performance_weight=0.2,        # 性能稳定性权重
        absolute_performance_weight=0.4 # 绝对表现权重
    )
    
    # 创建稳定性工作流
    from refactored_macro_strategy.workflows.stability_workflow import StabilityWorkflow
    
    stability_workflow = StabilityWorkflow(
        backtest_config=backtest_config,
        stability_config=stability_config
    )
    
    print(f"稳定性分析配置:")
    print(f"  回测目标: value_growth (价值成长)")
    print(f"  高稳定性阈值: {stability_config.high_stability_threshold}")
    print(f"  最少出现窗口: {stability_config.min_appearance_windows}")
    print(f"  权重配置: 排名={stability_config.ranking_weight}, "
          f"一致性={stability_config.significance_weight}, "
          f"性能={stability_config.performance_weight}, "
          f"绝对表现={stability_config.absolute_performance_weight}")
    
    try:
        print(f"\n开始分析价值成长稳定性...")
        
        # 基于现有数据运行稳定性分析
        results = stability_workflow.run_stability_analysis_on_existing_data(rolling_results_file)
        
        if results and 'stability_analysis' in results:
            stability_df = results['stability_analysis']
            insights = results.get('insights', {})
            
            print(f"\n=== 价值成长稳定性分析完成 ===")
            print(f"分析的组合数量: {len(stability_df)}")
            print(f"平均稳定性得分: {stability_df['overall_stability_score'].mean():.3f}")
            
            # 统计高稳定性组合
            high_stability_count = len(stability_df[
                stability_df['overall_stability_score'] > stability_config.high_stability_threshold
            ])
            print(f"高稳定组合数 (>{stability_config.high_stability_threshold}): {high_stability_count}")
            
            # 显示价值成长最佳组合推荐
            if 'best_combinations_per_indicator' in insights:
                best_combos = insights['best_combinations_per_indicator']
                if not best_combos.empty:
                    print(f"\n★★★ 价值成长最佳组合推荐 (共 {len(best_combos)} 个指标) ★★★")
                    for i, (_, row) in enumerate(best_combos.iterrows(), 1):
                        print(f"  {i:2d}. {row['indicator']:<30} | {row['signal_type']:<20}")
                        print(f"      综合得分: {row['overall_stability_score']:.3f} | "
                              f"平均IR: {row['ir_mean']:.3f} | "
                              f"出现窗口: {row['appearance_windows']}")
                        print(f"      参数配置: N={row['parameter_n']}, Dir={row['assumed_direction']}")
                        print()
                else:
                    print(f"\n没有指标达到推荐标准 (得分>{stability_config.high_stability_threshold})")
            
            # 显示价值成长Top 10
            print(f"\nTop 10 价值成长最稳定组合:")
            top_10 = stability_df.head(10)
            for i, (_, row) in enumerate(top_10.iterrows(), 1):
                print(f"  {i:2d}. {row['indicator']:<30} | {row['signal_type']:<20}")
                print(f"      综合得分: {row['overall_stability_score']:.3f} | "
                      f"平均IR: {row['ir_mean']:.3f} | "
                      f"出现窗口: {row['appearance_windows']}")
                print()
                
            print(f"详细结果导出到: {results.get('export_path', 'N/A')}")
            
            # 提供后续建议
            print(f"\n=== 使用建议 ===")
            if high_stability_count > 0:
                print(f"✓ 发现 {high_stability_count} 个高稳定性组合，可用于价值成长轮动策略")
                print(f"✓ 建议重点关注'最佳组合推荐'中的指标配置")
                if 'best_combinations_per_indicator' in insights and not insights['best_combinations_per_indicator'].empty:
                    best_ir = insights['best_combinations_per_indicator']['ir_mean'].max()
                    print(f"✓ 最佳平均IR: {best_ir:.3f}")
            else:
                print(f"⚠ 没有发现高稳定性组合，建议:")
                print(f"  - 降低阈值到0.3重新分析")
                print(f"  - 或检查数据质量和分析参数")
                
        else:
            print("价值成长稳定性分析失败或无结果")
            
    except Exception as e:
        print(f"价值成长稳定性分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_both_voting_strategies(data_path):
    """运行多信号投票策略 - 价值成长 & 大小盘"""
    from refactored_macro_strategy.workflows.multi_signal_workflow import run_both_voting_strategies as run_both_strategies_impl
    
    print("="*80)
    print("多信号投票策略")
    print("="*80)
    print("基于11个宏观信号的投票决策")
    print("策略类型: 价值成长轮动 & 大小盘轮动")
    print("投票机制: 多数票决定持仓方向")
    print("回测模式: 满仓多头策略")
    print("基准: 50% + 50% 月度再平衡")
    
    try:
        results = run_both_strategies_impl(data_path)
        
        if results:
            print(f"\n=== 多信号投票策略分析完成 ===")
            for strategy_type, strategy_results in results.items():
                if strategy_results and 'enhanced_metrics' in strategy_results:
                    metrics = strategy_results['enhanced_metrics']['strategy_metrics']
                    print(f"{strategy_type.upper()} 策略年化收益: {metrics['annualized_return']:.2%}")
                    print(f"{strategy_type.upper()} 策略夏普比率: {metrics['sharpe_ratio']:.3f}")
        else:
            print("多信号投票策略分析未产生有效结果")
    
    except Exception as e:
        print(f"多信号投票策略分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_value_growth_voting_strategy(data_path):
    """运行价值成长多信号投票策略"""
    from refactored_macro_strategy.workflows.multi_signal_workflow import run_value_growth_voting_strategy as run_vg_strategy_impl
    
    print("="*80)
    print("价值成长多信号投票策略")
    print("="*80)
    print("基于11个宏观信号的价值成长轮动策略")
    print("投票机制: 多数票决定价值 vs 成长")
    print("回测标的: ValueR vs GrowthR")
    
    try:
        results = run_vg_strategy_impl(data_path)
        
        if results and 'enhanced_metrics' in results:
            metrics = results['enhanced_metrics']['strategy_metrics']
            print(f"\n=== 价值成长投票策略完成 ===")
            print(f"策略年化收益: {metrics['annualized_return']:.2%}")
            print(f"策略夏普比率: {metrics['sharpe_ratio']:.3f}")
            print(f"输出文件: 详见signal_test_results目录")
        else:
            print("价值成长投票策略分析未产生有效结果")
    
    except Exception as e:
        print(f"价值成长投票策略分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_big_small_voting_strategy(data_path):
    """运行大小盘多信号投票策略"""
    from refactored_macro_strategy.workflows.multi_signal_workflow import run_big_small_voting_strategy as run_bs_strategy_impl
    
    print("="*80)
    print("大小盘多信号投票策略")
    print("="*80)
    print("基于11个宏观信号的大小盘轮动策略")
    print("投票机制: 多数票决定大盘 vs 小盘")
    print("回测标的: BigR vs SmallR")
    
    try:
        results = run_bs_strategy_impl(data_path)
        
        if results and 'enhanced_metrics' in results:
            metrics = results['enhanced_metrics']['strategy_metrics']
            print(f"\n=== 大小盘投票策略完成 ===")
            print(f"策略年化收益: {metrics['annualized_return']:.2%}")
            print(f"策略夏普比率: {metrics['sharpe_ratio']:.3f}")
            print(f"输出文件: 详见signal_test_results目录")
        else:
            print("大小盘投票策略分析未产生有效结果")
    
    except Exception as e:
        print(f"大小盘投票策略分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_value_growth_proportional_voting_strategy(data_path):
    """运行价值成长按比例分配多信号投票策略"""
    from refactored_macro_strategy.workflows.multi_signal_workflow import run_value_growth_proportional_voting_strategy as run_vg_prop_strategy_impl
    
    print("="*80)
    print("价值成长按比例分配多信号投票策略")
    print("="*80)
    print("基于11个宏观信号的价值成长轮动策略")
    print("投票机制: 按投票比例分配持仓权重")
    print("回测标的: ValueR vs GrowthR")
    print("示例: 价值9票，成长4票 → 价值69.2%，成长30.8%")
    
    try:
        results = run_vg_prop_strategy_impl(data_path)
        
        if results and 'enhanced_metrics' in results:
            metrics = results['enhanced_metrics']['strategy_metrics']
            print(f"\n=== 价值成长按比例投票策略完成 ===")
            print(f"策略年化收益: {metrics['annualized_return']:.2%}")
            print(f"策略夏普比率: {metrics['sharpe_ratio']:.3f}")
            print(f"输出文件: 详见signal_test_results目录")
        else:
            print("价值成长按比例投票策略分析未产生有效结果")
    
    except Exception as e:
        print(f"价值成长按比例投票策略分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_big_small_proportional_voting_strategy(data_path):
    """运行大小盘按比例分配多信号投票策略"""
    from refactored_macro_strategy.workflows.multi_signal_workflow import run_big_small_proportional_voting_strategy as run_bs_prop_strategy_impl
    
    print("="*80)
    print("大小盘按比例分配多信号投票策略")
    print("="*80)
    print("基于11个宏观信号的大小盘轮动策略")
    print("投票机制: 按投票比例分配持仓权重")
    print("回测标的: BigR vs SmallR")
    print("示例: 大盘7票，小盘6票 → 大盘53.8%，小盘46.2%")
    
    try:
        results = run_bs_prop_strategy_impl(data_path)
        
        if results and 'enhanced_metrics' in results:
            metrics = results['enhanced_metrics']['strategy_metrics']
            print(f"\n=== 大小盘按比例投票策略完成 ===")
            print(f"策略年化收益: {metrics['annualized_return']:.2%}")
            print(f"策略夏普比率: {metrics['sharpe_ratio']:.3f}")
            print(f"输出文件: 详见signal_test_results目录")
        else:
            print("大小盘按比例投票策略分析未产生有效结果")
    
    except Exception as e:
        print(f"大小盘按比例投票策略分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_both_proportional_voting_strategies(data_path):
    """运行按比例分配多信号投票策略 - 价值成长 & 大小盘"""
    from refactored_macro_strategy.workflows.multi_signal_workflow import run_both_proportional_voting_strategies as run_both_prop_strategies_impl
    
    print("="*80)
    print("按比例分配多信号投票策略")
    print("="*80)
    print("基于11个宏观信号的投票决策")
    print("策略类型: 价值成长轮动 & 大小盘轮动")
    print("投票机制: 按投票比例分配持仓权重")
    print("回测模式: 按投票比例配置策略")
    print("基准: 50% + 50% 月度再平衡")
    
    try:
        results = run_both_prop_strategies_impl(data_path)
        
        if results:
            print(f"\n=== 按比例分配投票策略分析完成 ===")
            for strategy_type, strategy_results in results.items():
                if strategy_results and 'enhanced_metrics' in strategy_results:
                    metrics = strategy_results['enhanced_metrics']['strategy_metrics']
                    print(f"{strategy_type.upper()} 策略年化收益: {metrics['annualized_return']:.2%}")
                    print(f"{strategy_type.upper()} 策略夏普比率: {metrics['sharpe_ratio']:.3f}")
        else:
            print("按比例分配投票策略分析未产生有效结果")
    
    except Exception as e:
        print(f"按比例分配投票策略分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_value_growth_sensitivity_analysis(data_path):
    """运行价值成长策略敏感性分析"""
    from refactored_macro_strategy.workflows.sensitivity_analysis import run_value_growth_sensitivity_test
    
    print("="*80)
    print("价值成长策略 - 宏观事件数量敏感性测试")
    print("="*80)
    print("测试信号数量: [5, 7, 9, 11, 13]")
    print("策略类型: 价值成长轮动 (ValueR vs GrowthR)")
    print("投票机制: 多数票决定持仓方向")
    print("分析目标: 评估不同宏观事件数量下的策略稳定性")
    
    try:
        # 运行价值成长敏感性测试
        results = run_value_growth_sensitivity_test(
            data_path=data_path,
            signal_counts=[5, 7, 9, 11, 13]
        )
        
        if results and 'sensitivity_summary' in results:
            summary = results['sensitivity_summary']
            stability_metrics = summary['stability_metrics']
            
            print(f"\n=== 价值成长敏感性分析完成 ===")
            print(f"测试的信号数量: {results.get('signal_counts_tested', [])}")
            print(f"可用信号总数: {results.get('total_signals_available', 0)}")
            print(f"最佳信号数量: {stability_metrics['best_signal_count']}")
            print(f"收益稳定性: {stability_metrics['return_stability']:.4f}")
            print(f"夏普稳定性: {stability_metrics['sharpe_stability']:.4f}")
            print(f"信息比率稳定性: {stability_metrics['info_ratio_stability']:.4f}")
            print(f"最稳定信号范围: {stability_metrics['most_stable_range']}")
            
            # 显示绩效趋势
            trend = summary['performance_trend']
            print(f"\n绩效趋势分析:")
            print(f"  收益率趋势: {trend['return_trend']}")
            print(f"  夏普比率趋势: {trend['sharpe_trend']}")
            print(f"  信息比率趋势: {trend['info_ratio_trend']}")
            
            print(f"\n详细结果已导出到 signal_test_results/ 目录")
        else:
            print("价值成长敏感性分析未产生有效结果")
    
    except Exception as e:
        print(f"价值成长敏感性分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_big_small_sensitivity_analysis(data_path):
    """运行大小盘策略敏感性分析"""
    from refactored_macro_strategy.workflows.sensitivity_analysis import run_big_small_sensitivity_test
    
    print("="*80)
    print("大小盘策略 - 宏观事件数量敏感性测试")
    print("="*80)
    print("测试信号数量: [5, 7, 9, 11, 13]")
    print("策略类型: 大小盘轮动 (BigR vs SmallR)")
    print("投票机制: 多数票决定持仓方向")
    print("分析目标: 评估不同宏观事件数量下的策略稳定性")
    
    try:
        # 运行大小盘敏感性测试
        results = run_big_small_sensitivity_test(
            data_path=data_path,
            signal_counts=[5, 7, 9, 11, 13]
        )
        
        if results and 'sensitivity_summary' in results:
            summary = results['sensitivity_summary']
            stability_metrics = summary['stability_metrics']
            
            print(f"\n=== 大小盘敏感性分析完成 ===")
            print(f"测试的信号数量: {results.get('signal_counts_tested', [])}")
            print(f"可用信号总数: {results.get('total_signals_available', 0)}")
            print(f"最佳信号数量: {stability_metrics['best_signal_count']}")
            print(f"收益稳定性: {stability_metrics['return_stability']:.4f}")
            print(f"夏普稳定性: {stability_metrics['sharpe_stability']:.4f}")
            print(f"信息比率稳定性: {stability_metrics['info_ratio_stability']:.4f}")
            print(f"最稳定信号范围: {stability_metrics['most_stable_range']}")
            
            # 显示绩效趋势
            trend = summary['performance_trend']
            print(f"\n绩效趋势分析:")
            print(f"  收益率趋势: {trend['return_trend']}")
            print(f"  夏普比率趋势: {trend['sharpe_trend']}")
            print(f"  信息比率趋势: {trend['info_ratio_trend']}")
            
            print(f"\n详细结果已导出到 signal_test_results/ 目录")
        else:
            print("大小盘敏感性分析未产生有效结果")
    
    except Exception as e:
        print(f"大小盘敏感性分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_both_strategies_sensitivity_analysis(data_path):
    """运行双策略敏感性分析"""
    from refactored_macro_strategy.workflows.sensitivity_analysis import run_both_strategies_sensitivity_test
    
    print("="*80)
    print("双策略 - 宏观事件数量敏感性测试")
    print("="*80)
    print("测试信号数量: [5, 7, 9, 11, 13]")
    print("策略类型: 价值成长轮动 & 大小盘轮动")
    print("投票机制: 多数票决定持仓方向")
    print("分析目标: 对比两个策略在不同宏观事件数量下的稳定性")
    
    try:
        # 运行双策略敏感性测试
        results = run_both_strategies_sensitivity_test(
            data_path=data_path,
            signal_counts=[5, 7, 9, 11, 13]
        )
        
        if results:
            print(f"\n=== 双策略敏感性分析完成 ===")
            
            for strategy_type, strategy_results in results.items():
                if strategy_results and 'sensitivity_summary' in strategy_results:
                    summary = strategy_results['sensitivity_summary']
                    stability_metrics = summary['stability_metrics']
                    
                    print(f"\n{strategy_type.upper()} 策略:")
                    print(f"  测试信号数量: {strategy_results.get('signal_counts_tested', [])}")
                    print(f"  最佳信号数量: {stability_metrics['best_signal_count']}")
                    print(f"  收益稳定性: {stability_metrics['return_stability']:.4f}")
                    print(f"  夏普稳定性: {stability_metrics['sharpe_stability']:.4f}")
                    print(f"  信息比率稳定性: {stability_metrics['info_ratio_stability']:.4f}")
                    print(f"  最稳定信号范围: {stability_metrics['most_stable_range']}")
                    
                    # 显示绩效趋势
                    trend = summary['performance_trend']
                    print(f"  绩效趋势: 收益{trend['return_trend']}, 夏普{trend['sharpe_trend']}, IR{trend['info_ratio_trend']}")
            
            print(f"\n详细结果已导出到 signal_test_results/ 目录")
            print(f"包含跨策略敏感性比较文件")
        else:
            print("双策略敏感性分析未产生有效结果")
    
    except Exception as e:
        print(f"双策略敏感性分析失败: {e}")
        import traceback
        traceback.print_exc()


def run_custom_sensitivity_analysis(data_path):
    """运行自定义敏感性分析"""
    from refactored_macro_strategy.workflows.sensitivity_analysis import SensitivityAnalysisWorkflow
    
    print("="*80)
    print("自定义宏观事件数量敏感性测试")
    print("="*80)
    
    # 让用户选择策略类型
    print("请选择策略类型:")
    print("  1. 价值成长策略 (value_growth)")
    print("  2. 大小盘策略 (big_small)")
    
    strategy_choice = input("请输入选择 (1-2): ").strip()
    
    if strategy_choice == '1':
        strategy_type = 'value_growth'
        strategy_name = '价值成长'
    elif strategy_choice == '2':
        strategy_type = 'big_small'
        strategy_name = '大小盘'
    else:
        print("无效选择，使用默认的价值成长策略")
        strategy_type = 'value_growth'
        strategy_name = '价值成长'
    
    # 让用户自定义信号数量
    print(f"\n当前策略: {strategy_name}")
    print("请输入要测试的信号数量 (用逗号分隔，例如: 3,5,7,9,11,13)")
    print("默认: 5,7,9,11,13")
    
    signal_input = input("信号数量: ").strip()
    
    if signal_input:
        try:
            signal_counts = [int(x.strip()) for x in signal_input.split(',')]
        except ValueError:
            print("输入格式错误，使用默认值")
            signal_counts = [5, 7, 9, 11, 13]
    else:
        signal_counts = [5, 7, 9, 11, 13]
    
    print(f"\n开始 {strategy_name} 策略敏感性测试")
    print(f"测试信号数量: {signal_counts}")
    
    try:
        # 创建敏感性分析工作流
        workflow = SensitivityAnalysisWorkflow()
        
        # 运行自定义敏感性测试
        results = workflow.run_signal_count_sensitivity_test(
            data_path=data_path,
            strategy_type=strategy_type,
            signal_counts=signal_counts
        )
        
        if results and 'sensitivity_summary' in results:
            summary = results['sensitivity_summary']
            stability_metrics = summary['stability_metrics']
            
            print(f"\n=== {strategy_name} 自定义敏感性分析完成 ===")
            print(f"测试的信号数量: {results.get('signal_counts_tested', [])}")
            print(f"可用信号总数: {results.get('total_signals_available', 0)}")
            print(f"最佳信号数量: {stability_metrics['best_signal_count']}")
            print(f"收益稳定性: {stability_metrics['return_stability']:.4f}")
            print(f"夏普稳定性: {stability_metrics['sharpe_stability']:.4f}")
            print(f"信息比率稳定性: {stability_metrics['info_ratio_stability']:.4f}")
            print(f"最稳定信号范围: {stability_metrics['most_stable_range']}")
            
            # 显示绩效趋势
            trend = summary['performance_trend']
            print(f"\n绩效趋势分析:")
            print(f"  收益率趋势: {trend['return_trend']}")
            print(f"  夏普比率趋势: {trend['sharpe_trend']}")
            print(f"  信息比率趋势: {trend['info_ratio_trend']}")
            
            print(f"\n详细结果已导出到 signal_test_results/ 目录")
        else:
            print(f"{strategy_name} 自定义敏感性分析未产生有效结果")
    
    except Exception as e:
        print(f"{strategy_name} 自定义敏感性分析失败: {e}")
        import traceback
        traceback.print_exc()


def show_sensitivity_analysis_info():
    """显示敏感性分析信息"""
    from refactored_macro_strategy.config.signal_config import SignalConfig
    
    print("="*80)
    print("宏观事件数量敏感性测试 - 信息概览")
    print("="*80)
    
    signal_config = SignalConfig()
    
    print("\n【测试原理】")
    print("通过使用前5/7/9/11/13个宏观事件进行投票，")
    print("对比策略在不同信号数量下的回测表现稳定性。")
    print("回测方式使用多信号投票策略（获胜者全拿），而非按比例投票。")
    
    print("\n【信号排序】")
    for strategy_type in ['value_growth', 'big_small']:
        ranking_info = signal_config.get_signal_ranking_info(strategy_type)
        strategy_name = '价值成长' if strategy_type == 'value_growth' else '大小盘'
        
        print(f"\n{strategy_name} 策略信号排序 (总计 {ranking_info['total_signals']} 个):")
        for i, signal_info in enumerate(ranking_info['signal_order'][:5], 1):
            print(f"  {i}. {signal_info['indicator']} - {signal_info['description']}")
        
        if ranking_info['total_signals'] > 5:
            print(f"  ... 还有 {ranking_info['total_signals'] - 5} 个信号")
    
    print("\n【分析指标】")
    print("- 年化收益率稳定性（标准差）")
    print("- 夏普比率稳定性（标准差）")
    print("- 超额收益稳定性（标准差）")
    print("- 信息比率稳定性（标准差）")
    print("- 月胜率稳定性（标准差）")
    print("- 最佳信号数量（基于信息比率）")
    print("- 最稳定信号范围")
    
    print("\n【输出文件】")
    print("测试结果会自动导出到 signal_test_results/ 目录:")
    print("1. sensitivity_analysis_{strategy_type}_{timestamp}.xlsx - 单策略敏感性分析")
    print("2. cross_strategy_sensitivity_comparison_{timestamp}.xlsx - 跨策略比较")
    
    print("\n【使用建议】")
    print("- 稳定性指标越小，说明策略在不同信号数量下越稳定")
    print("- 最佳信号数量是信息比率最高的信号数量")
    print("- 可通过趋势分析了解信号数量对策略表现的影响")
    print("- 结合业务逻辑和统计结果做出决策")


def run_detailed_voting_results_analysis(data_path):
    """
    输出全部月份(2012/10至今)，Top11宏观事件（参与投票）的投票结果明细
    """
    from refactored_macro_strategy.workflows.multi_signal_workflow import MultiSignalVotingWorkflow
    from refactored_macro_strategy.config.signal_config import SignalConfig
    import pandas as pd
    import os
    
    print("="*80)
    print("Top 11 宏观事件投票结果明细分析")
    print("="*80)
    print("分析期间: 2012年10月 至今")
    print("信号数量: 每个策略Top 11个宏观事件信号")
    print("输出内容: 每月每个信号的投票明细")
    
    try:
        # 创建工作流实例
        workflow = MultiSignalVotingWorkflow()
        signal_config = SignalConfig()
        
        # 获取两个策略的Top 11信号配置
        value_growth_configs = signal_config.get_top_n_voting_signals('value_growth', n=11)
        big_small_configs = signal_config.get_top_n_voting_signals('big_small', n=11)
        
        print(f"\n价值成长策略 Top 11 信号:")
        for i, config in enumerate(value_growth_configs, 1):
            print(f"  {i}. {config['indicator']} - {config['signal_type']} (N={config['parameter_n']}, Dir={config['assumed_direction']})")
        
        print(f"\n大小盘策略 Top 11 信号:")
        for i, config in enumerate(big_small_configs, 1):
            print(f"  {i}. {config['indicator']} - {config['signal_type']} (N={config['parameter_n']}, Dir={config['assumed_direction']})")
        
        # 加载数据
        print(f"\n正在加载数据: {data_path}")
        from refactored_macro_strategy.utils.data_loader import load_all_data
        data_dict = load_all_data(data_path)
        indicator_data = data_dict['indicator_data']
        price_data = data_dict['price_data']
        
        if indicator_data.empty or price_data.empty:
            print("错误: 数据加载失败")
            return
        
        print(f"宏观指标数据: {indicator_data.shape}")
        print(f"价格数据: {price_data.shape}")
        print(f"数据时间范围: {indicator_data.index[0].strftime('%Y-%m-%d')} 到 {indicator_data.index[-1].strftime('%Y-%m-%d')}")
        
        # 分析两个策略的投票明细
        all_detailed_results = {}
        
        for strategy_type, strategy_configs in [('value_growth', value_growth_configs), ('big_small', big_small_configs)]:
            strategy_name = '价值成长' if strategy_type == 'value_growth' else '大小盘'
            print(f"\n=== 分析 {strategy_name} 策略投票明细 ===")
            
            # 生成投票信号
            voting_signals = workflow.voting_engine.generate_voting_signals(
                indicator_data, strategy_configs, strategy_type, signal_start_date='2012-10-01'
            )
            
            if voting_signals.empty:
                print(f"错误: {strategy_name} 策略投票信号生成失败")
                continue
            
            # 计算投票决策
            voting_decisions = workflow.voting_engine.calculate_voting_decisions(
                voting_signals, strategy_type
            )
            
            if voting_decisions.empty:
                print(f"错误: {strategy_name} 策略投票决策计算失败")
                continue
            
            # 创建详细的投票明细表
            detailed_voting_results = []
            
            # 按月份分组分析
            voting_signals['year_month'] = voting_signals['date'].dt.to_period('M')
            monthly_groups = voting_signals.groupby('year_month')
            
            for period, month_data in monthly_groups:
                month_str = str(period)  # 格式: 2012-10
                
                # 获取该月的投票决策
                period_timestamp = period.to_timestamp()
                if period_timestamp in voting_decisions.index:
                    decision_data = voting_decisions.loc[period_timestamp]
                    
                    if strategy_type == 'value_growth':
                        winning_direction = decision_data['winning_name']
                        value_votes = decision_data['value_votes']
                        growth_votes = decision_data['growth_votes']
                        total_votes = value_votes + growth_votes
                    else:
                        winning_direction = decision_data['winning_name']
                        big_votes = decision_data['big_votes']
                        small_votes = decision_data['small_votes']
                        total_votes = big_votes + small_votes
                    
                    vote_confidence = decision_data['vote_confidence']
                else:
                    winning_direction = 'N/A'
                    if strategy_type == 'value_growth':
                        value_votes = growth_votes = 0
                    else:
                        big_votes = small_votes = 0
                    total_votes = 0
                    vote_confidence = 0
                
                # 获取该月每个信号的投票情况
                month_signals = month_data.groupby('signal_id').first()
                
                for signal_id, signal_data in month_signals.iterrows():
                    # 获取信号配置信息
                    signal_config_info = next((cfg for cfg in strategy_configs if cfg['combination_id'] == signal_id), None)
                    
                    if signal_config_info:
                        signal_description = signal_config_info.get('description', f"{signal_config_info['indicator']} - {signal_config_info['signal_type']}")
                        
                        vote_direction_name = ''
                        if strategy_type == 'value_growth':
                            vote_direction_name = 'Value' if signal_data['vote'] == 1 else 'Growth'
                        else:
                            vote_direction_name = 'Big' if signal_data['vote'] == 1 else 'Small'
                        
                        detailed_voting_results.append({
                            '年月': month_str,
                            '信号ID': signal_id,
                            '指标名称': signal_config_info['indicator'],
                            '信号类型': signal_config_info['signal_type'],
                            '参数N': signal_config_info['parameter_n'],
                            '方向': signal_config_info['assumed_direction'],
                            '信号描述': signal_description,
                            '投票方向': vote_direction_name,
                            '投票值': signal_data['vote'],
                            '月度获胜方向': winning_direction,
                            '投票信心度': f"{vote_confidence:.2%}" if vote_confidence > 0 else 'N/A',
                            '总票数': total_votes
                        })
                        
                        # 添加策略特定的投票统计
                        if strategy_type == 'value_growth':
                            detailed_voting_results[-1].update({
                                '价值票数': value_votes,
                                '成长票数': growth_votes
                            })
                        else:
                            detailed_voting_results[-1].update({
                                '大盘票数': big_votes,
                                '小盘票数': small_votes
                            })
            
            # 转换为DataFrame
            detailed_df = pd.DataFrame(detailed_voting_results)
            
            if not detailed_df.empty:
                print(f"{strategy_name} 策略投票明细生成完成: {len(detailed_df)} 条记录")
                print(f"时间范围: {detailed_df['年月'].min()} 到 {detailed_df['年月'].max()}")
                
                # 显示统计信息
                total_months = detailed_df['年月'].nunique()
                total_signals = detailed_df['信号ID'].nunique()
                print(f"统计: {total_months} 个月份 × {total_signals} 个信号 = {len(detailed_df)} 条投票记录")
                
                all_detailed_results[strategy_type] = {
                    'detailed_voting': detailed_df,
                    'voting_decisions': voting_decisions,
                    'strategy_configs': strategy_configs
                }
            else:
                print(f"警告: {strategy_name} 策略未生成投票明细")
        
        # 导出结果到Excel
        if all_detailed_results:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"signal_test_results/detailed_voting_results_{timestamp}.xlsx"
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 导出每个策略的详细投票结果
                for strategy_type, results in all_detailed_results.items():
                    strategy_name = '价值成长' if strategy_type == 'value_growth' else '大小盘'
                    
                    # 详细投票明细
                    detailed_df = results['detailed_voting']
                    detailed_df.to_excel(writer, sheet_name=f'{strategy_name}_投票明细', index=False)
                    
                    # 月度投票决策汇总
                    voting_decisions = results['voting_decisions'].reset_index()
                    voting_decisions['年月'] = voting_decisions['date'].dt.to_period('M').astype(str)
                    
                    # 重命名列为中文
                    if strategy_type == 'value_growth':
                        voting_decisions_export = voting_decisions[['年月', 'winning_name', 'value_votes', 'growth_votes', 'total_signals', 'vote_confidence']].copy()
                        voting_decisions_export.columns = ['年月', '获胜方向', '价值票数', '成长票数', '总信号数', '投票信心度']
                    else:
                        voting_decisions_export = voting_decisions[['年月', 'winning_name', 'big_votes', 'small_votes', 'total_signals', 'vote_confidence']].copy()
                        voting_decisions_export.columns = ['年月', '获胜方向', '大盘票数', '小盘票数', '总信号数', '投票信心度']
                    
                    voting_decisions_export.to_excel(writer, sheet_name=f'{strategy_name}_月度决策', index=False)
                    
                    # 信号配置表
                    configs_df = pd.DataFrame(results['strategy_configs'])
                    configs_df_export = configs_df[['combination_id', 'indicator', 'signal_type', 'parameter_n', 'assumed_direction', 'description']].copy()
                    configs_df_export.columns = ['信号ID', '指标名称', '信号类型', '参数N', '方向', '描述']
                    configs_df_export.to_excel(writer, sheet_name=f'{strategy_name}_信号配置', index=False)
                
                # 创建综合统计表
                summary_data = []
                for strategy_type, results in all_detailed_results.items():
                    strategy_name = '价值成长' if strategy_type == 'value_growth' else '大小盘'
                    detailed_df = results['detailed_voting']
                    voting_decisions = results['voting_decisions']
                    
                    if strategy_type == 'value_growth':
                        value_wins = (voting_decisions['winning_name'] == 'Value').sum()
                        growth_wins = (voting_decisions['winning_name'] == 'Growth').sum()
                        win_distribution = f"价值: {value_wins} ({value_wins/len(voting_decisions)*100:.1f}%), 成长: {growth_wins} ({growth_wins/len(voting_decisions)*100:.1f}%)"
                    else:
                        big_wins = (voting_decisions['winning_name'] == 'Big').sum()
                        small_wins = (voting_decisions['winning_name'] == 'Small').sum()
                        win_distribution = f"大盘: {big_wins} ({big_wins/len(voting_decisions)*100:.1f}%), 小盘: {small_wins} ({small_wins/len(voting_decisions)*100:.1f}%)"
                    
                    summary_data.append({
                        '策略类型': strategy_name,
                        '信号数量': detailed_df['信号ID'].nunique(),
                        '月份数量': detailed_df['年月'].nunique(),
                        '投票记录总数': len(detailed_df),
                        '时间范围': f"{detailed_df['年月'].min()} 到 {detailed_df['年月'].max()}",
                        '获胜分布': win_distribution,
                        '平均投票信心度': f"{voting_decisions['vote_confidence'].mean():.2%}"
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='综合统计', index=False)
            
            print(f"\n=== 投票明细分析完成 ===")
            print(f"详细结果已导出到: {output_file}")
            print(f"包含工作表:")
            for strategy_type in all_detailed_results.keys():
                strategy_name = '价值成长' if strategy_type == 'value_growth' else '大小盘'
                print(f"  - {strategy_name}_投票明细: 每月每个信号的投票详情")
                print(f"  - {strategy_name}_月度决策: 每月的投票决策汇总")
                print(f"  - {strategy_name}_信号配置: Top 11信号的配置信息")
            print(f"  - 综合统计: 两个策略的整体统计信息")
            
            # 显示一些关键统计
            print(f"\n关键统计信息:")
            for strategy_type, results in all_detailed_results.items():
                strategy_name = '价值成长' if strategy_type == 'value_growth' else '大小盘'
                detailed_df = results['detailed_voting']
                voting_decisions = results['voting_decisions']
                
                print(f"\n{strategy_name} 策略:")
                print(f"  分析月份: {detailed_df['年月'].nunique()} 个月")
                print(f"  投票记录: {len(detailed_df)} 条")
                print(f"  平均月投票信心度: {voting_decisions['vote_confidence'].mean():.2%}")
                
                if strategy_type == 'value_growth':
                    value_wins = (voting_decisions['winning_name'] == 'Value').sum()
                    growth_wins = (voting_decisions['winning_name'] == 'Growth').sum()
                    print(f"  价值获胜: {value_wins} 次 ({value_wins/len(voting_decisions)*100:.1f}%)")
                    print(f"  成长获胜: {growth_wins} 次 ({growth_wins/len(voting_decisions)*100:.1f}%)")
                else:
                    big_wins = (voting_decisions['winning_name'] == 'Big').sum()
                    small_wins = (voting_decisions['winning_name'] == 'Small').sum()
                    print(f"  大盘获胜: {big_wins} 次 ({big_wins/len(voting_decisions)*100:.1f}%)")
                    print(f"  小盘获胜: {small_wins} 次 ({small_wins/len(voting_decisions)*100:.1f}%)")
        else:
            print("错误: 未能生成任何投票明细结果")
    
    except Exception as e:
        print(f"投票明细分析失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    data_path = "宏观指标与逻辑.xlsx"
    
    # 选择要运行的示例
    examples = {
        '1': ('价值成长完整回测', run_value_growth_complete_test),
        '2': ('大小盘完整回测', run_big_small_complete_test),
        '3': ('全部完整回测', run_all_complete_test),
        '4': ('大小盘稳定性分析', run_big_small_stability_analysis),
        '5': ('价值成长稳定性分析', run_ranking_stability_analysis),
        '6': ('跨标的稳定性比较', run_stability_comparison_across_targets),
        '7': ('基于现有数据的稳定性重新分析', None),  # 特殊处理：通用重新分析
        '8': ('大小盘稳定性重新分析', run_big_small_stability_reanalysis),
        '9': ('价值成长稳定性重新分析', run_value_growth_stability_reanalysis),
        '10': ('多信号投票策略', run_both_voting_strategies),
        '11': ('价值成长多信号投票策略', run_value_growth_voting_strategy),
        '12': ('大小盘多信号投票策略', run_big_small_voting_strategy),
        '13': ('按比例分配多信号投票策略', run_both_proportional_voting_strategies),
        '14': ('价值成长按比例投票策略', run_value_growth_proportional_voting_strategy),
        '15': ('大小盘按比例投票策略', run_big_small_proportional_voting_strategy),
        '16': ('价值成长敏感性分析', run_value_growth_sensitivity_analysis),
        '17': ('大小盘敏感性分析', run_big_small_sensitivity_analysis),
        '18': ('双策略敏感性分析', run_both_strategies_sensitivity_analysis),
        '19': ('自定义敏感性分析', run_custom_sensitivity_analysis),
        '20': ('敏感性分析信息概览', show_sensitivity_analysis_info),
        '21': ('Top 11 宏观事件投票结果明细分析', run_detailed_voting_results_analysis)
    }
    
    print("可用示例:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    choice = input(f"\n请选择示例编号 (1-{len(examples)}): ").strip()
    
    # 特殊处理选项7
    if choice == '7':
        print(f"\n运行: 基于现有数据的稳定性重新分析")
        
        # 提示用户输入文件路径
        print("\n注意: 这个选项需要已有的滚动回测结果文件")
        print("示例文件名: rolling_raw_results_value_growth_20250529_140924.xlsx")
        
        # 可以提供一些常见的文件路径建议
        import glob
        possible_files = glob.glob("signal_test_results/rolling_raw_results_*.xlsx")
        if possible_files:
            print("\n在signal_test_results目录中找到以下可能的文件:")
            for i, file in enumerate(possible_files, 1):
                print(f"  {i}. {file}")
            
            file_choice = input(f"\n请选择文件编号 (1-{len(possible_files)}) 或输入完整文件路径: ").strip()
            
            # 如果是数字，选择对应文件
            if file_choice.isdigit() and 1 <= int(file_choice) <= len(possible_files):
                selected_file = possible_files[int(file_choice) - 1]
            else:
                selected_file = file_choice
        else:
            selected_file = input("请输入滚动回测结果文件的完整路径: ").strip()
        
        # 运行稳定性重新分析
        run_stability_reanalysis_on_existing_data(selected_file)
        return
    
    # 特殊处理选项20（信息概览）
    if choice == '20':
        show_sensitivity_analysis_info()
        return
    
    # 特殊处理选项21（投票明细分析）
    if choice == '21':
        print(f"\n运行: Top 11 宏观事件投票结果明细分析")
        run_detailed_voting_results_analysis(data_path)
        return
    
    selected_example = examples.get(choice)

    if selected_example:
        name, func = selected_example
        if func:  # 确保函数不为None
            print(f"\n运行: {name}")
            # Pass data_path to the selected example function
            func(data_path)
        else:
            print("功能函数未定义")
    else:
        print("无效选择，请重新运行脚本并输入有效编号。")
        # Optionally, you could default to a specific example or exit
        # print("运行: 快速测试示例")
        # quick_test_example(data_path) 


if __name__ == "__main__":
    print("重构后的宏观策略系统使用示例")
    print("="*80)
    
    # 设置数据路径 (需要根据实际情况修改)
    data_path = "宏观指标与逻辑.xlsx"  # 文件在项目根目录

    # 检查文件是否存在
    if not os.path.exists(data_path):
        print(f"数据文件不存在: {data_path}")
        print("请确保数据文件路径正确，或者在data_path变量中指定正确路径。")
        # 可以选择退出或者提示用户创建文件等
        # sys.exit(1) # 如果需要严格退出
        # 或者只返回，让用户手动解决
    
    main() 
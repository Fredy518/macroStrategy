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
    


def quick_test_example(data_path):
    """
    快速测试示例
    """
    print("="*80)
    print("快速测试示例")
    print("="*80)
    
    workflow = MainWorkflow()
    
    if not os.path.exists(data_path):
        print(f"数据文件不存在: {data_path}")
        return
    
    try:
        # 快速测试 - 只测试部分指标和信号类型
        results = workflow.quick_test(
            data_path=data_path,
            sample_indicators=['CPI_yoy', 'M1_yoy', 'electricity_yoy'],  # 只测试3个指标
            sample_signal_types=['historical_high', 'marginal_improvement']  # 只测试2种信号
        )
        
        if results:
            print(f"快速测试完成！回测组合数: {len(results['backtest_results'])}")
        
    except Exception as e:
        print(f"快速测试失败: {e}")


def step_by_step_example(data_path):
    """
    分步执行示例
    """
    print("="*80)
    print("分步执行示例")
    print("="*80)
    
    workflow = MainWorkflow()
    
    if not os.path.exists(data_path):
        print(f"数据文件不存在: {data_path}")
        return
    
    try:
        # 步骤1: 加载数据
        print("步骤1: 加载数据")
        macro_data, price_data, memo_df = workflow.load_data(data_path)
        
        # 步骤2: 生成信号 (只测试部分信号类型)
        print("\n步骤2: 生成信号")
        test_results = workflow.run_signal_generation(
            macro_data=macro_data,
            signal_types=['historical_high', 'exceed_expectation']
        )
        
        # 步骤3: 运行回测 (只测试部分指标)
        print("\n步骤3: 运行回测")
        sample_indicators = list(macro_data.columns)[:5]  # 只测试前5个指标
        backtest_results = workflow.run_backtest(
            test_results=test_results,
            price_data=price_data,
            memo_df=memo_df,
            indicators=sample_indicators,
            enable_parallel=False
        )
        
        # 步骤4: 分析和导出
        print("\n步骤4: 分析和导出")
        if not backtest_results.empty:
            filtered_results, export_path = workflow.run_analysis_and_export(backtest_results)
            print(f"分步执行完成！结果文件: {export_path}")
        else:
            print("无有效回测结果")
        
    except Exception as e:
        print(f"分步执行失败: {e}")


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
    print("基于13个宏观信号的投票决策")
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
    print("基于13个宏观信号的价值成长轮动策略")
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
    print("基于13个宏观信号的大小盘轮动策略")
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
    print("基于13个宏观信号的价值成长轮动策略")
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
    print("基于13个宏观信号的大小盘轮动策略")
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
    print("基于13个宏观信号的投票决策")
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
        '6': ('快速测试示例', quick_test_example),
        '7': ('分步执行示例', step_by_step_example),
        '8': ('跨标的稳定性比较', run_stability_comparison_across_targets),
        '9': ('基于现有数据的稳定性重新分析', None),  # 特殊处理：通用重新分析
        '10': ('大小盘稳定性重新分析', run_big_small_stability_reanalysis),  # 专门的大小盘重新分析
        '11': ('价值成长稳定性重新分析', run_value_growth_stability_reanalysis),  # 专门的价值成长重新分析
        '12': ('多信号投票策略', run_both_voting_strategies),
        '13': ('价值成长多信号投票策略', run_value_growth_voting_strategy),
        '14': ('大小盘多信号投票策略', run_big_small_voting_strategy),
        '15': ('按比例分配多信号投票策略', run_both_proportional_voting_strategies),
        '16': ('价值成长按比例投票策略', run_value_growth_proportional_voting_strategy),
        '17': ('大小盘按比例投票策略', run_big_small_proportional_voting_strategy)
    }
    
    print("可用示例:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    choice = input(f"\n请选择示例编号 (1-{len(examples)}): ").strip()
    
    # 特殊处理选项9
    if choice == '9':
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
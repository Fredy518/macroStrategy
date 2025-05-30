"""
独立稳定性重新分析脚本
基于现有的滚动回测数据重新计算稳定性分析结果
用于在修改StabilityConfig设置后快速重新分析，无需重新运行耗时的滚动回测
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

# 导入必要的模块
from refactored_macro_strategy.workflows.stability_workflow import StabilityWorkflow
from refactored_macro_strategy.config.backtest_config import BacktestConfig
from refactored_macro_strategy.core.stability_analyzer import StabilityConfig


def reanalyze_stability(rolling_results_file: str, custom_stability_config: StabilityConfig = None):
    """
    基于现有滚动回测数据重新计算稳定性分析
    
    参数:
        rolling_results_file: 滚动回测结果文件路径
        custom_stability_config: 自定义稳定性配置 (可选)
    """
    print("="*80)
    print("稳定性重新分析")
    print("="*80)
    
    # 从文件路径中推断回测目标
    if 'big_small' in rolling_results_file:
        backtest_target = 'big_small'
    elif 'value_growth' in rolling_results_file:
        backtest_target = 'value_growth'
    else:
        print(f"警告: 无法从文件名推断回测目标，默认使用value_growth")
        backtest_target = 'value_growth'
    
    print(f"检测到回测目标: {backtest_target}")
    print(f"滚动回测文件: {rolling_results_file}")
    
    # 检查文件是否存在
    if not os.path.exists(rolling_results_file):
        print(f"错误: 文件不存在 - {rolling_results_file}")
        return None
    
    # 配置
    backtest_config = BacktestConfig(backtest_target=backtest_target)
    
    # 如果提供了自定义稳定性配置，使用它，否则使用默认配置
    if custom_stability_config is None:
        # 使用您可能调整过的默认配置
        stability_config = StabilityConfig()
        print(f"使用默认稳定性配置")
    else:
        stability_config = custom_stability_config
        print(f"使用自定义稳定性配置")
    
    print(f"稳定性配置:")
    print(f"  每窗口Top K: {stability_config.top_k_per_window} (仅当启用TopK限制时生效)")
    print(f"  启用TopK限制: {stability_config.enable_top_k_limit}")
    print(f"  最少出现窗口: {stability_config.min_appearance_windows}")
    print(f"  排名权重: {stability_config.ranking_weight}")
    print(f"  显著性权重: {stability_config.significance_weight}")
    print(f"  表现权重: {stability_config.performance_weight}")
    print(f"  绝对表现权重: {stability_config.absolute_performance_weight}")
    print(f"  {stability_config.get_selection_summary()}")
    
    # 创建稳定性工作流
    stability_workflow = StabilityWorkflow(
        backtest_config=backtest_config,
        stability_config=stability_config
    )
    
    try:
        # 运行稳定性分析
        print(f"\n开始重新分析...")
        results = stability_workflow.run_stability_analysis_on_existing_data(rolling_results_file)
        
        if results and 'stability_analysis' in results:
            stability_df = results['stability_analysis']
            
            # 添加稳定性排名列（基于overall_stability_score的排名）
            stability_df['stability_rank'] = range(1, len(stability_df) + 1)
            
            print(f"\n" + "="*60)
            print(f"稳定性重新分析完成")
            print(f"="*60)
            print(f"分析的组合数量: {len(stability_df)}")
            print(f"平均稳定性得分: {stability_df['overall_stability_score'].mean():.3f}")
            print(f"高稳定组合数 (>0.5): {len(stability_df[stability_df['overall_stability_score'] > 0.5])}")
            print(f"非常高稳定组合数 (>0.7): {len(stability_df[stability_df['overall_stability_score'] > 0.7])}")
            
            # 显示Top 10最稳定组合
            print(f"\nTop 10 最稳定组合:")
            print("-" * 100)
            top_10 = stability_df.head(10)
            for i, (_, row) in enumerate(top_10.iterrows(), 1):
                print(f"{i:2d}. {row['indicator']:<20} | {row['signal_type']:<15} | {row['parameter_n']:<10}")
                print(f"     稳定性得分: {row['overall_stability_score']:.3f} | 排名: {row['stability_rank']:3d} | "
                      f"出现窗口: {row['appearance_windows']:2d} | 总窗口: {row['total_possible_windows']:2d}")
                print(f"     平均表现: {row['ir_mean']:.3f} | 平均排名: {row['rank_mean']:.1f} | "
                      f"显著性一致性: {row['significance_consistency_score']:.2f}")
                print("")
                
            # 导出路径信息
            if 'export_path' in results:
                print(f"结果已导出至: {results['export_path']}")
            
            return results
        else:
            print("错误: 稳定性重新分析失败或无结果")
            return None
            
    except Exception as e:
        print(f"错误: 稳定性重新分析失败 - {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    # 默认的滚动回测结果文件 (您可以修改这个路径)
    default_file = "signal_test_results/rolling_raw_results_value_growth_20250529_140924.xlsx"
    
    # 如果命令行提供了文件路径参数，使用它
    if len(sys.argv) > 1:
        rolling_results_file = sys.argv[1]
    else:
        rolling_results_file = default_file
    
    # 创建自定义稳定性配置 (您可以在这里修改参数)
    custom_config = StabilityConfig(
        top_k_per_window=15,          # 每窗口Top K (仅当enable_top_k_limit=True时生效)
        enable_top_k_limit=False,     # 启用纯显著性筛选，不限制数量
        min_appearance_windows=10,     # 最少出现5个窗口 (您可以调整)
        ranking_weight=0.2,          # 排名稳定性权重 (您可以调整)
        significance_weight=0.2,     # 显著性一致率权重 (您可以调整)
        performance_weight=0.2,      # 性能稳定性权重 (您可以调整)
        absolute_performance_weight=0.40,  # 绝对表现权重 (新增，重点关注IR水平)
    )
    
    # 运行重新分析
    print(f"使用文件: {rolling_results_file}")
    results = reanalyze_stability(rolling_results_file, custom_config)
    
    if results:
        print(f"\n重新分析成功完成!")
    else:
        print(f"\n重新分析失败!")


if __name__ == "__main__":
    main() 
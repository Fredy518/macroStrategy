"""
统一配置系统使用示例
Unified Configuration System Example

展示如何使用重构后的统一配置管理系统
"""

import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from config.signal_config import SignalConfig


def demonstrate_unified_config():
    """演示统一配置系统的使用"""
    
    print("="*80)
    print("统一配置系统使用示例")
    print("="*80)
    
    # 1. 创建配置实例
    signal_config = SignalConfig()
    
    # 2. 查看传统信号配置
    print("\n【传统信号配置】")
    print(f"配置的指标分类数量: {len(signal_config.INDICATOR_CATEGORIES)}")
    for category, indicators in signal_config.INDICATOR_CATEGORIES.items():
        print(f"  {category}: {len(indicators)} 个指标")
    
    print(f"\n总计传统指标数量: {len(signal_config.get_all_indicators())}")
    print(f"信号类型: {signal_config.SIGNAL_TYPES}")
    
    # 3. 查看投票策略配置
    print("\n【投票策略配置】")
    print(f"投票策略数量: {len(signal_config.VOTING_STRATEGIES)}")
    
    for strategy_type, signals in signal_config.VOTING_STRATEGIES.items():
        print(f"\n{strategy_type} 策略:")
        print(f"  信号数量: {len(signals)}")
        print(f"  使用的指标: {len(signal_config.get_voting_strategy_indicators(strategy_type))} 个")
        
        # 显示前3个信号配置示例
        print(f"  前3个信号示例:")
        for i, signal in enumerate(signals[:3]):
            print(f"    {i+1}. {signal['indicator']} - {signal['signal_type']} (N={signal['parameter_n']}, Dir={signal['assumed_direction']})")
        
        if len(signals) > 3:
            print(f"    ... 还有 {len(signals)-3} 个信号")
    
    print(f"\n投票策略总计指标数量: {len(signal_config.get_all_voting_indicators())}")
    
    # 4. 演示配置的动态修改
    print("\n【配置动态修改示例】")
    
    # 添加新的投票信号
    new_signal = {
        'indicator': 'test_indicator',
        'signal_type': 'historical_high',
        'parameter_n': 6,
        'assumed_direction': 1,
        'description': '测试指标历史高位6月1方向'
    }
    
    signal_config.add_voting_signal('value_growth', new_signal)
    print(f"添加新信号后 value_growth 策略信号数量: {len(signal_config.get_voting_strategy_signals('value_growth'))}")
    
    # 移除刚添加的信号
    combination_id = new_signal.get('combination_id', 'test_indicator_historical_high_6_1')
    removed = signal_config.remove_voting_signal('value_growth', combination_id)
    print(f"移除测试信号成功: {removed}")
    print(f"移除后 value_growth 策略信号数量: {len(signal_config.get_voting_strategy_signals('value_growth'))}")
    
    # 5. 演示工作流程使用新配置
    print("\n【工作流程配置使用】")
    
    try:
        from workflows.multi_signal_workflow import MultiSignalVotingWorkflow
        
        # 创建工作流实例（使用自定义配置）
        workflow = MultiSignalVotingWorkflow(signal_config=signal_config)
        
        print("工作流程成功创建，使用统一配置系统")
        print(f"工作流中的投票配置已加载: value_growth={len(workflow.signal_config.get_voting_strategy_signals('value_growth'))} 个信号")
        print(f"工作流中的投票配置已加载: big_small={len(workflow.signal_config.get_voting_strategy_signals('big_small'))} 个信号")
        
        # 6. 对比新旧配置系统
        print("\n【新旧配置系统对比】")
        
        # 使用新配置系统
        new_configs = workflow.signal_configuration.load_default_configurations()
        
        # 使用旧配置系统（向后兼容）
        old_configs = workflow.signal_configuration.load_legacy_configurations()
        
        print("\n配置对比结果:")
        for strategy_type in ['value_growth', 'big_small']:
            new_count = len(new_configs.get(strategy_type, []))
            old_count = len(old_configs.get(strategy_type, []))
            print(f"  {strategy_type}: 新配置={new_count} vs 旧配置={old_count}")
            
            # 检查配置是否一致
            if new_count == old_count:
                print(f"    ✅ 配置数量一致")
            else:
                print(f"    ⚠️  配置数量不同")
    
    except ImportError as e:
        print(f"工作流程导入失败 (这是正常的，因为可能缺少依赖): {e}")
        print("但统一配置系统本身工作正常")
        
        # 直接测试配置系统
        from core.multi_signal_voting import SignalConfiguration
        signal_configuration = SignalConfiguration(signal_config)
        
        print("\n【直接配置系统对比】")
        new_configs = signal_configuration.load_default_configurations()
        old_configs = signal_configuration.load_legacy_configurations()
        
        print("\n配置对比结果:")
        for strategy_type in ['value_growth', 'big_small']:
            new_count = len(new_configs.get(strategy_type, []))
            old_count = len(old_configs.get(strategy_type, []))
            print(f"  {strategy_type}: 新配置={new_count} vs 旧配置={old_count}")
            
            # 检查配置是否一致
            if new_count == old_count:
                print(f"    ✅ 配置数量一致")
            else:
                print(f"    ⚠️  配置数量不同")
    
    print("\n="*80)
    print("统一配置系统演示完成")
    print("="*80)


def show_voting_indicators_details():
    """显示投票策略中所有指标的详细信息"""
    
    print("\n" + "="*80)
    print("投票策略指标详细信息")
    print("="*80)
    
    signal_config = SignalConfig()
    
    # 按策略类型显示指标
    for strategy_type, signals in signal_config.VOTING_STRATEGIES.items():
        print(f"\n【{strategy_type.upper()} 策略】")
        print(f"{'序号':<4} {'指标名称':<35} {'信号类型':<20} {'参数':<6} {'方向':<6} {'描述'}")
        print("-" * 120)
        
        for i, signal in enumerate(signals, 1):
            indicator = signal['indicator']
            signal_type = signal['signal_type']
            param_n = signal['parameter_n']
            direction = signal['assumed_direction']
            description = signal.get('description', '')
            
            print(f"{i:<4} {indicator:<35} {signal_type:<20} {param_n:<6} {direction:<6} {description}")
    
    # 显示所有唯一指标
    all_indicators = signal_config.get_all_voting_indicators()
    print(f"\n【所有唯一指标】")
    print(f"总计: {len(all_indicators)} 个指标")
    print("-" * 80)
    
    for i, indicator in enumerate(sorted(all_indicators), 1):
        print(f"{i:2d}. {indicator}")


if __name__ == "__main__":
    # 运行演示
    demonstrate_unified_config()
    
    # 显示详细的指标信息
    show_voting_indicators_details() 
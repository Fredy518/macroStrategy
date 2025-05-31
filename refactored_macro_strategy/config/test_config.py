from signal_config import SignalConfig

# 测试统一配置系统
sc = SignalConfig()

print("✅ Config loaded successfully")
print(f"✅ Traditional indicators: {len(sc.get_all_indicators())}")
print(f"✅ Voting strategies: {len(sc.VOTING_STRATEGIES)}")
print(f"✅ Value-Growth signals: {len(sc.get_voting_strategy_signals('value_growth'))}")
print(f"✅ Big-Small signals: {len(sc.get_voting_strategy_signals('big_small'))}")
print(f"✅ All voting indicators: {len(sc.get_all_voting_indicators())}")

print("\n=== 详细配置信息 ===")
for strategy_type, signals in sc.VOTING_STRATEGIES.items():
    print(f"\n{strategy_type} 策略:")
    print(f"  信号数量: {len(signals)}")
    indicators = sc.get_voting_strategy_indicators(strategy_type)
    print(f"  指标数量: {len(indicators)}")
    print(f"  前5个指标: {', '.join(indicators[:5])}")

print("\n🎉 配置系统重构成功！") 
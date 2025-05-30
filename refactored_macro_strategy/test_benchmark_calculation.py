"""
测试基准收益计算的准确性
"""

import pandas as pd
import numpy as np
from utils.data_loader import load_all_data

def test_benchmark_calculation():
    """测试基准收益计算"""
    
    # 加载数据
    data_dict = load_all_data('../宏观指标与逻辑.xlsx')
    price_data = data_dict['price_data']
    
    # 获取2021年数据
    year_2021 = price_data[price_data.index.year == 2021]
    
    print("=== 2021年基准收益验证 ===")
    print(f"2021年数据范围: {year_2021.index[0].strftime('%Y-%m-%d')} 到 {year_2021.index[-1].strftime('%Y-%m-%d')}")
    
    # 计算个别资产年度收益
    start_value = year_2021.iloc[0]['ValueR']
    end_value = year_2021.iloc[-1]['ValueR']
    start_growth = year_2021.iloc[0]['GrowthR']
    end_growth = year_2021.iloc[-1]['GrowthR']
    
    value_return = (end_value / start_value) - 1
    growth_return = (end_growth / start_growth) - 1
    
    print(f"\n个别资产收益:")
    print(f"ValueR: {start_value:.4f} -> {end_value:.4f}, 收益: {value_return:.2%}")
    print(f"GrowthR: {start_growth:.4f} -> {end_growth:.4f}, 收益: {growth_return:.2%}")
    print(f"简单平均收益: {(value_return + growth_return)/2:.2%}")
    
    # 模拟50%+50%无再平衡
    no_rebalance_return = 0.5 * value_return + 0.5 * growth_return
    print(f"50%+50%无再平衡收益: {no_rebalance_return:.2%}")
    
    # 模拟月度再平衡
    monthly_rebalance_nav = simulate_monthly_rebalance(year_2021)
    monthly_rebalance_return = monthly_rebalance_nav - 1
    print(f"50%+50%月度再平衡收益: {monthly_rebalance_return:.2%}")
    
    return {
        'value_return': value_return,
        'growth_return': growth_return,
        'no_rebalance_return': no_rebalance_return,
        'monthly_rebalance_return': monthly_rebalance_return
    }

def simulate_monthly_rebalance(price_data):
    """模拟月度再平衡的基准组合"""
    
    # 获取每月第一个交易日
    monthly_starts = price_data.resample('MS').first()
    print(f"\n月度再平衡日期数量: {len(monthly_starts)}")
    
    # 初始净值和份额
    nav = 1.0
    initial_price_value = price_data.iloc[0]['ValueR']
    initial_price_growth = price_data.iloc[0]['GrowthR']
    
    shares_value = 0.5 / initial_price_value  # 50%资金买ValueR
    shares_growth = 0.5 / initial_price_growth  # 50%资金买GrowthR
    
    print(f"初始设置: ValueR份额={shares_value:.6f}, GrowthR份额={shares_growth:.6f}")
    
    for i, (date, row) in enumerate(price_data.iterrows()):
        current_price_value = row['ValueR']
        current_price_growth = row['GrowthR']
        
        # 检查是否需要再平衡（每月第一个交易日）
        if date in monthly_starts.index and i > 0:
            # 计算再平衡前的净值
            current_nav = shares_value * current_price_value + shares_growth * current_price_growth
            
            # 重新平衡为50%+50%
            shares_value = (current_nav * 0.5) / current_price_value
            shares_growth = (current_nav * 0.5) / current_price_growth
            
            if date <= pd.Timestamp('2021-03-01'):  # 只打印前几次再平衡
                print(f"再平衡 {date.strftime('%Y-%m-%d')}: 净值={current_nav:.4f}, 新份额: ValueR={shares_value:.6f}, GrowthR={shares_growth:.6f}")
    
    # 计算最终净值
    final_nav = shares_value * price_data.iloc[-1]['ValueR'] + shares_growth * price_data.iloc[-1]['GrowthR']
    print(f"最终净值: {final_nav:.4f}")
    
    return final_nav

if __name__ == "__main__":
    test_benchmark_calculation() 
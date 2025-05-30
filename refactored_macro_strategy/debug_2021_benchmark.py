"""
调试2021年基准收益计算问题
"""

import pandas as pd
import numpy as np
from utils.data_loader import load_all_data

def debug_2021_benchmark():
    """专门调试2021年基准收益问题"""
    
    # 加载数据
    data_dict = load_all_data('../宏观指标与逻辑.xlsx')
    price_data = data_dict['price_data']
    
    # 获取2021年数据
    year_2021 = price_data[price_data.index.year == 2021]
    
    print("=== 2021年基准收益调试 ===")
    print(f"2021年数据范围: {year_2021.index[0].strftime('%Y-%m-%d')} 到 {year_2021.index[-1].strftime('%Y-%m-%d')}")
    print(f"2021年交易日数: {len(year_2021)}")
    
    # 测试净值计算方法（模拟多信号系统从2013年开始）
    nav_base_date = pd.Timestamp('2013-01-04')
    full_nav_results = test_nav_calculation_full_period(price_data, nav_base_date)
    
    # 提取2021年的净值和收益
    extract_2021_performance(full_nav_results)

def test_nav_calculation_full_period(price_data, nav_base_date):
    """测试完整期间的净值计算（模拟多信号系统的逻辑）"""
    
    print(f"\n=== 测试完整期间净值计算 ===")
    
    # 获取从基准日期开始的所有数据
    nav_price_data = price_data.loc[nav_base_date:].copy()
    
    if nav_price_data.empty:
        return None
    
    # 基准日期的价格
    base_price_value = nav_price_data.iloc[0]['ValueR']
    base_price_growth = nav_price_data.iloc[0]['GrowthR']
    
    print(f"基准日期: {nav_base_date.strftime('%Y-%m-%d')}")
    print(f"基准日价格: ValueR={base_price_value:.4f}, GrowthR={base_price_growth:.4f}")
    
    # 初始化净值序列
    benchmark_nav = pd.Series(index=nav_price_data.index, dtype=float)
    benchmark_nav.iloc[0] = 1.0
    
    # 基准投资组合：始终50%+50%
    benchmark_shares_value = 0.5 / base_price_value
    benchmark_shares_growth = 0.5 / base_price_growth
    
    print(f"初始份额: ValueR={benchmark_shares_value:.6f}, GrowthR={benchmark_shares_growth:.6f}")
    
    # 生成再平衡日期
    rebalance_dates = pd.date_range(start=nav_base_date, end=nav_price_data.index[-1], freq='MS')
    rebalance_dates = rebalance_dates[rebalance_dates.isin(nav_price_data.index)]
    
    print(f"总再平衡日期数量: {len(rebalance_dates)}")
    rebalance_count = 0
    
    # 逐日计算净值
    for i in range(1, len(nav_price_data)):
        current_date = nav_price_data.index[i]
        current_price_value = nav_price_data.iloc[i]['ValueR']
        current_price_growth = nav_price_data.iloc[i]['GrowthR']
        
        # 检查基准是否需要再平衡
        if current_date in rebalance_dates:
            # 计算再平衡前的基准净值
            current_benchmark_nav_value = (benchmark_shares_value * current_price_value + 
                                         benchmark_shares_growth * current_price_growth)
            
            # 重新平衡为50%+50%
            benchmark_shares_value = (current_benchmark_nav_value * 0.5) / current_price_value
            benchmark_shares_growth = (current_benchmark_nav_value * 0.5) / current_price_growth
            
            rebalance_count += 1
        
        # 计算当日净值
        benchmark_nav_value = (benchmark_shares_value * current_price_value + 
                             benchmark_shares_growth * current_price_growth)
        
        benchmark_nav.iloc[i] = benchmark_nav_value
    
    print(f"总再平衡次数: {rebalance_count}")
    
    # 计算收益率
    benchmark_returns = benchmark_nav.pct_change().dropna()
    
    return {
        'nav': benchmark_nav,
        'returns': benchmark_returns
    }

def extract_2021_performance(nav_results):
    """提取2021年的绩效数据"""
    
    if not nav_results:
        return
    
    print(f"\n=== 提取2021年绩效 ===")
    
    nav = nav_results['nav']
    returns = nav_results['returns']
    
    # 筛选2021年数据
    year_2021_nav = nav[nav.index.year == 2021]
    year_2021_returns = returns[returns.index.year == 2021]
    
    if year_2021_nav.empty:
        print("2021年净值数据为空")
        return
    
    print(f"2021年净值数据点数: {len(year_2021_nav)}")
    print(f"2021年收益率数据点数: {len(year_2021_returns)}")
    
    # 计算2021年收益率
    start_nav_2021 = year_2021_nav.iloc[0]
    end_nav_2021 = year_2021_nav.iloc[-1]
    
    # 方法1：基于净值计算
    method1_return = (end_nav_2021 / start_nav_2021) - 1
    print(f"方法1 (净值首尾): {method1_return:.2%}")
    
    # 方法2：基于收益率累积
    method2_return = (1 + year_2021_returns).prod() - 1
    print(f"方法2 (收益率累积): {method2_return:.2%}")
    
    # 分析年度绩效计算逻辑
    analyze_annual_performance_logic(nav, 2021)

def analyze_annual_performance_logic(nav, target_year):
    """分析年度绩效计算逻辑（模拟多信号系统的计算方式）"""
    
    print(f"\n=== 分析{target_year}年度绩效计算逻辑 ===")
    
    # 模拟多信号系统的年度绩效计算
    yearly_data = []
    
    # 获取目标年份的数据
    year_data_nav = nav[nav.index.year == target_year]
    
    if year_data_nav.empty:
        print(f"{target_year}年数据为空")
        return
    
    # 计算收益率
    year_returns = year_data_nav.pct_change().dropna()
    
    # 计算年度收益（基于净值首尾）
    annual_return_nav = (year_data_nav.iloc[-1] / year_data_nav.iloc[0]) - 1
    
    # 计算年度收益（基于收益率累积）
    annual_return_cum = (1 + year_returns).prod() - 1
    
    print(f"净值首日: {year_data_nav.iloc[0]:.4f} ({year_data_nav.index[0].strftime('%Y-%m-%d')})")
    print(f"净值末日: {year_data_nav.iloc[-1]:.4f} ({year_data_nav.index[-1].strftime('%Y-%m-%d')})")
    print(f"年度收益(净值): {annual_return_nav:.2%}")
    print(f"年度收益(累积): {annual_return_cum:.2%}")
    
    # 检查是否有异常的收益率
    extreme_returns = year_returns[abs(year_returns) > 0.05]  # 绝对值大于5%的收益
    if not extreme_returns.empty:
        print(f"\n发现大幅收益率 (>5%):")
        for date, ret in extreme_returns.items():
            print(f"  {date.strftime('%Y-%m-%d')}: {ret:.2%}")
    
    return annual_return_nav

if __name__ == "__main__":
    debug_2021_benchmark() 
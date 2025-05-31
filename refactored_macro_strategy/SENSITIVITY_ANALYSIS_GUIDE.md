# 指标敏感性分析指南

## 概述

指标敏感性分析工具用于测试不同宏观事件数量下的策略表现稳定性。通过使用前5/7/9/11/13个事件进行投票，可以对比策略在不同信号数量下的回测表现。

## 功能特点

### 🎯 核心功能
- **信号数量敏感性测试**: 测试使用前N个信号的策略表现
- **稳定性分析**: 评估策略在不同信号数量下的稳定性
- **趋势分析**: 分析信号数量对策略绩效的影响趋势
- **跨策略比较**: 同时分析价值成长和大小盘两个策略

### 📊 分析指标
- 年化收益率稳定性（标准差）
- 夏普比率稳定性（标准差）
- 超额收益稳定性（标准差）
- 信息比率稳定性（标准差）
- 月胜率稳定性（标准差）
- 最佳信号数量（基于信息比率）
- 最稳定信号范围

## 信号排序

### Value Growth 策略信号排序
1. **long_loan_newadded_MA12_yoy** - 中长期贷款增量(MA12)当月同比超预期3月-1方向
2. **M2_M1** - M2-M1历史新高3月1方向
3. **newstarts_area_yoy** - 房屋新开工面积当月同比历史新高3月1方向
4. **CPI_PPI** - CPI-PPI历史新高6月-1方向
5. **US_BOND_5Y** - 美国5年期国债收益率超预期12月1方向
6. **TSF_newadded_MA12_yoy** - 社融规模增量(MA12)当月同比历史高位12月-1方向
7. **US_BOND_10Y** - 美国10年期国债收益率超预期12月1方向
8. **fixedasset_investment_yoy** - 固定资产投资完成额当月同比超预期3月1方向
9. **M1** - M1超预期9月-1方向
10. **M2** - M2历史高位12月-1方向
11. **pmi_manufacturing_neworder** - 制造业PMI新订单历史新低6月1方向
12. **pmi_nonmanufacturing** - 非制造业PMI历史新低3月-1方向
13. **CREDIT_SPREAD** - 信用利差历史新低3月1方向

### Big Small 策略信号排序
1. **local_gov_budget_MA12_yoy** - 地方政府预算收入(MA12)当月同比历史高位6月1方向
2. **pmi_manufacturing_neworder** - 制造业PMI新订单历史新低6月1方向
3. **pmi_manufacturing** - 制造业PMI历史高位6月1方向
4. **completed_yoy** - 房屋竣工面积当月同比历史新高3月-1方向
5. **CN_BOND_1Y** - 中国1年期国债收益率历史新高3月1方向
6. **PPI** - PPI历史新低9月1方向
7. **newstarts_area_yoy** - 房屋新开工面积当月同比历史新高3月1方向
8. **CPI_PPI** - CPI-PPI历史新高6月-1方向
9. **core_CPI_PPI** - 核心CPI-PPI历史新高9月-1方向
10. **fixedasset_investment_ytd_yoy** - 固定资产投资累计同比历史新高3月1方向
11. **TSF_yoy** - 社融存量同比历史新高3月-1方向
12. **CN_BOND_10Y** - 中国10年期国债收益率超预期3月1方向
13. **industrial_value_added_yoy** - 工业增加值当月同比超预期9月1方向

## 使用方法

### 1. 基本用法

```python
from workflows.sensitivity_analysis import SensitivityAnalysisWorkflow

# 创建工作流实例
workflow = SensitivityAnalysisWorkflow()

# 运行单个策略敏感性测试
results = workflow.run_signal_count_sensitivity_test(
    data_path='your_data_file.xlsx',
    strategy_type='value_growth',  # 或 'big_small'
    signal_counts=[5, 7, 9, 11, 13],
    start_date='2013-01-01',
    end_date='2025-05-27'
)
```

### 2. 两个策略同时测试

```python
# 同时测试两个策略
all_results = workflow.run_both_strategies_sensitivity_test(
    data_path='your_data_file.xlsx',
    signal_counts=[5, 7, 9, 11, 13],
    start_date='2013-01-01',
    end_date='2025-05-27'
)
```

### 3. 便捷函数

```python
from workflows.sensitivity_analysis import (
    run_value_growth_sensitivity_test,
    run_big_small_sensitivity_test,
    run_both_strategies_sensitivity_test
)

# 价值成长策略敏感性测试
vg_results = run_value_growth_sensitivity_test('your_data_file.xlsx')

# 大小盘策略敏感性测试
bs_results = run_big_small_sensitivity_test('your_data_file.xlsx')

# 两个策略同时测试
both_results = run_both_strategies_sensitivity_test('your_data_file.xlsx')
```

## 结果解释

### 敏感性测试结果结构

```python
{
    'strategy_type': 'value_growth',
    'signal_counts_tested': [5, 7, 9, 11, 13],
    'total_signals_available': 13,
    'ranking_info': {
        'total_signals': 13,
        'signal_order': [...],  # 详细信号排序
        'indicator_order': [...]  # 指标顺序
    },
    'sensitivity_results': {
        '5_signals': {...},   # 5个信号的回测结果
        '7_signals': {...},   # 7个信号的回测结果
        '9_signals': {...},   # 9个信号的回测结果
        '11_signals': {...},  # 11个信号的回测结果
        '13_signals': {...}   # 13个信号的回测结果
    },
    'sensitivity_summary': {
        'summary_table': DataFrame,  # 摘要表
        'stability_metrics': {...},  # 稳定性指标
        'performance_trend': {...}   # 绩效趋势
    }
}
```

### 稳定性指标解释

- **return_stability**: 年化收益率的标准差，越小越稳定
- **sharpe_stability**: 夏普比率的标准差，越小越稳定
- **excess_return_stability**: 超额收益的标准差，越小越稳定
- **info_ratio_stability**: 信息比率的标准差，越小越稳定
- **win_rate_stability**: 月胜率的标准差，越小越稳定
- **best_signal_count**: 信息比率最高的信号数量
- **most_stable_range**: 相邻信号数量间变化最小的范围

### 趋势分析

- **return_trend**: 收益率随信号数量的变化趋势（上升/下降/稳定）
- **sharpe_trend**: 夏普比率随信号数量的变化趋势
- **info_ratio_trend**: 信息比率随信号数量的变化趋势

## 输出文件

敏感性测试会自动生成以下Excel文件：

### 1. 单策略敏感性分析
文件名: `sensitivity_analysis_{strategy_type}_{timestamp}.xlsx`

包含以下工作表：
- **敏感性分析摘要**: 不同信号数量的绩效对比
- **稳定性指标**: 各项稳定性指标统计
- **绩效趋势分析**: 趋势方向和斜率分析
- **N信号_年度绩效**: 各信号数量的年度绩效表现
- **N信号_净值曲线**: 各信号数量的净值曲线数据

### 2. 跨策略敏感性比较
文件名: `cross_strategy_sensitivity_comparison_{timestamp}.xlsx`

包含以下工作表：
- **跨策略敏感性比较**: 两个策略在不同信号数量下的表现对比
- **稳定性对比**: 两个策略的稳定性指标对比

## 测试验证

运行以下命令验证敏感性分析功能：

```bash
# 验证配置功能
python test_sensitivity.py

# 运行完整测试（需要数据文件）
python -c "from workflows.sensitivity_analysis import run_both_strategies_sensitivity_test; run_both_strategies_sensitivity_test('your_data_file.xlsx')"
```

## 最佳实践

### 1. 数据准备
- 确保数据文件包含所有必需的宏观指标
- 检查数据完整性和时间范围覆盖
- 验证价格数据的正确性

### 2. 信号数量选择
- 默认测试 [5, 7, 9, 11, 13] 个信号
- 可根据实际需求调整测试范围
- 建议包含奇数个信号避免平票

### 3. 结果分析
- 重点关注稳定性指标，选择变化较小的信号数量
- 结合趋势分析了解信号增减的影响
- 比较最佳信号数量与稳定信号范围

### 4. 策略优化
- 如果前N个信号已达到最佳表现，可考虑精简策略
- 如果稳定性较差，可能需要重新排序或筛选信号
- 结合业务逻辑和统计结果做出决策

## 注意事项

1. **信号排序的重要性**: 信号在配置中的顺序决定了敏感性测试的结果
2. **回测方式**: 使用多信号投票策略（获胜者全拿），而非按比例投票
3. **基准设置**: 使用50%+50%月度再平衡作为基准
4. **数据依赖**: 测试结果高度依赖于输入数据的质量和完整性
5. **计算时间**: 完整的敏感性测试需要较长时间，建议耐心等待

## 技术支持

如有问题，请参考：
- `test_sensitivity.py` - 配置功能验证
- `examples/sensitivity_test_example.py` - 使用示例
- `workflows/sensitivity_analysis.py` - 核心实现代码 
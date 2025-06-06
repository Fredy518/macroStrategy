# Top 11 宏观事件投票结果明细分析指南

## 功能概述

这个功能提供了全部月份（2012年10月至今）Top 11宏观事件信号的详细投票结果分析，帮助用户深入了解每个信号在每个月份的投票行为和决策过程。

## 使用方法

### 运行分析

```bash
cd refactored_macro_strategy
python examples/run_example.py
# 选择选项 21: Top 11 宏观事件投票结果明细分析
```

### 输出文件

分析完成后会在 `signal_test_results/` 目录下生成一个Excel文件：
- 文件名格式：`detailed_voting_results_YYYYMMDD_HHMMSS.xlsx`

## 输出内容详解

### 工作表结构

#### 1. 价值成长_投票明细
- **内容**：价值成长策略每月每个信号的详细投票记录
- **列说明**：
  - `年月`：投票月份（格式：2012-10）
  - `信号ID`：信号的唯一标识符
  - `指标名称`：宏观指标名称
  - `信号类型`：信号类型（超预期、历史新高等）
  - `参数N`：信号参数（时间窗口）
  - `方向`：投票方向（1或-1）
  - `信号描述`：信号的中文业务描述
  - `投票方向`：该信号的投票选择（Value/Growth）
  - `投票值`：数值化的投票（1=价值，0=成长）
  - `月度获胜方向`：该月最终获胜的方向
  - `投票信心度`：投票的信心度百分比
  - `价值票数`：价值方向获得的票数
  - `成长票数`：成长方向获得的票数
  - `总票数`：参与投票的总信号数

#### 2. 大小盘_投票明细
- **内容**：大小盘策略每月每个信号的详细投票记录
- **列说明**：类似价值成长，但投票方向为Big/Small，票数统计为大盘票数/小盘票数

#### 3. 价值成长_月度决策
- **内容**：价值成长策略每月的投票决策汇总
- **列说明**：
  - `年月`：决策月份
  - `获胜方向`：最终获胜方向（Value/Growth）
  - `价值票数`：价值获得的总票数
  - `成长票数`：成长获得的总票数
  - `总信号数`：参与投票的信号总数
  - `投票信心度`：决策的信心度

#### 4. 大小盘_月度决策
- **内容**：大小盘策略每月的投票决策汇总
- **列说明**：类似价值成长月度决策，但针对大盘vs小盘

#### 5. 价值成长_信号配置 / 大小盘_信号配置
- **内容**：Top 11信号的详细配置信息
- **列说明**：
  - `信号ID`：信号唯一标识
  - `指标名称`：宏观指标名称
  - `信号类型`：信号类型
  - `参数N`：时间窗口参数
  - `方向`：假定方向
  - `描述`：业务描述

#### 6. 综合统计
- **内容**：两个策略的整体统计信息
- **列说明**：
  - `策略类型`：价值成长/大小盘
  - `信号数量`：使用的信号数量（11个）
  - `月份数量`：分析的月份数量
  - `投票记录总数`：总投票记录数
  - `时间范围`：分析的时间范围
  - `获胜分布`：各方向获胜的次数和比例
  - `平均投票信心度`：平均信心度

## 关键统计信息

### 价值成长策略
- **分析期间**：2012年10月 - 2025年5月（152个月）
- **投票记录**：1,672条（152月 × 11信号）
- **获胜分布**：
  - 价值获胜：约46.7%
  - 成长获胜：约53.3%
- **平均投票信心度**：约39.83%

### 大小盘策略
- **分析期间**：2012年10月 - 2025年5月（152个月）
- **投票记录**：1,672条（152月 × 11信号）
- **获胜分布**：
  - 大盘获胜：约35.5%
  - 小盘获胜：约64.5%
- **平均投票信心度**：约22.97%

## Top 11 信号列表

### 价值成长策略信号
1. `long_loan_newadded_MA12_yoy` - 中长期贷款增量(MA12)当月同比超预期3月-1方向
2. `M2_M1` - M2-M1历史新高3月1方向
3. `newstarts_area_yoy` - 房屋新开工面积当月同比历史新高3月1方向
4. `CPI_PPI` - CPI-PPI历史新高6月-1方向
5. `US_BOND_5Y` - 美国5年期国债收益率超预期12月1方向
6. `TSF_newadded_MA12_yoy` - 社融规模增量(MA12)当月同比历史高位12月-1方向
7. `US_BOND_10Y` - 美国10年期国债收益率超预期12月1方向
8. `fixedasset_investment_yoy` - 固定资产投资完成额当月同比超预期3月1方向
9. `M1` - M1超预期9月-1方向
10. `M2` - M2历史高位12月-1方向
11. `pmi_manufacturing_neworder` - 制造业PMI新订单历史新低6月1方向

### 大小盘策略信号
1. `local_gov_budget_MA12_yoy` - 地方政府预算收入(MA12)当月同比历史高位6月1方向
2. `pmi_manufacturing_neworder` - 制造业PMI新订单历史新低6月1方向
3. `pmi_manufacturing` - 制造业PMI历史高位6月1方向
4. `completed_yoy` - 房屋竣工面积当月同比历史新高3月-1方向
5. `CN_BOND_1Y` - 中国1年期国债收益率历史新高3月1方向
6. `PPI` - PPI历史新低9月1方向
7. `newstarts_area_yoy` - 房屋新开工面积当月同比历史新高3月1方向
8. `CPI_PPI` - CPI-PPI历史新高6月-1方向
9. `core_CPI_PPI` - 核心CPI-PPI历史新高9月-1方向
10. `fixedasset_investment_ytd_yoy` - 固定资产投资累计同比历史新高3月1方向
11. `TSF_yoy` - 社融存量同比历史新高3月-1方向

## 投票机制说明

### 投票规则
1. **多数票胜出**：每月各信号投票，获得多数票的方向获胜
2. **信号权重**：所有信号权重相等（每个信号1票）
3. **投票方向**：
   - 价值成长：Value（价值）vs Growth（成长）
   - 大小盘：Big（大盘）vs Small（小盘）

### 信心度计算
```
投票信心度 = |获胜票数 - 失败票数| / 总票数
```

### 应用场景
- **策略研究**：分析各信号的历史投票行为
- **信号评估**：评估单个信号的有效性
- **时间序列分析**：观察投票模式的时间变化
- **策略优化**：基于历史投票结果优化信号权重

## 注意事项

1. **数据完整性**：分析基于2012年10月开始的完整数据
2. **信号排序**：信号按照历史回测表现排序，前11个为最优信号
3. **投票延迟**：投票基于T-2月的信号，在T月执行交易
4. **缺失数据**：部分早期数据可能存在NaN值，已自动处理为无信号状态

## 相关功能

- **多信号投票策略**：选项10-15
- **敏感性分析**：选项16-19
- **策略回测**：选项1-3
- **HTML仪表板**：`macro_signals_dashboard.html` 
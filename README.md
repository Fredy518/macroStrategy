# 宏观策略系统 (Macro Strategy System)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

## 📋 项目概述

这是一个基于宏观经济指标的量化投资策略系统，专注于通过宏观数据分析来指导风格轮动投资决策。系统能够自动化处理宏观经济数据，生成交易信号，并进行回测分析。

## 🎯 核心功能

- **📊 宏观指标分析**: 支持多种宏观经济指标的数据处理和分析
- **🔄 风格轮动策略**: 基于价值/成长风格的轮动投资策略
- **⚡ 信号生成**: 多种信号生成算法（历史高点、边际改善等）
- **🔬 回测引擎**: 完整的策略回测和性能评估系统
- **📈 结果分析**: 自动化的结果分析和可视化输出
- **⚙️ 配置管理**: 灵活的参数配置和策略定制
- **🎯 多信号投票**: 基于11个宏观事件的投票决策系统
- **📊 敏感性分析**: 测试不同宏观事件数量下的策略稳定性
- **🔍 稳定性评估**: 滚动回测和稳定性指标分析

## 🏗️ 项目结构

```
macroStrategy/
├── refactored_macro_strategy/     # 重构后的核心系统
│   ├── config/                    # 配置模块
│   │   ├── signal_config.py       # 信号生成配置
│   │   ├── backtest_config.py     # 回测配置
│   │   └── export_config.py       # 导出配置
│   ├── core/                      # 核心引擎
│   │   ├── signal_engine.py       # 信号生成引擎
│   │   ├── backtest_engine.py     # 回测引擎
│   │   └── result_processor.py    # 结果处理器
│   ├── utils/                     # 工具模块
│   │   └── validators.py          # 数据验证工具
│   ├── workflows/                 # 工作流程
│   │   └── main_workflow.py       # 主工作流程
│   ├── examples/                  # 使用示例
│   │   └── run_example.py         # 示例代码
│   └── tests/                     # 测试模块
├── signal_test_results/           # 历史测试结果
├── 宏观指标与逻辑.xlsx            # 宏观数据文件
└── 基金专题报告_ETF系列报告（三）.pptx  # 研究报告
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pandas, numpy, openpyxl 等依赖包

### 安装依赖

```bash
cd refactored_macro_strategy
pip install -r requirements.txt
```

### 基础使用

```python
from refactored_macro_strategy.workflows import MainWorkflow

# 创建工作流实例
workflow = MainWorkflow()

# 一键运行完整流程
results = workflow.run_complete_workflow(
    data_path="宏观指标与逻辑.xlsx"
)
```

### 快速测试

```python
# 快速测试部分指标和信号
results = workflow.quick_test(
    data_path="宏观指标与逻辑.xlsx",
    sample_indicators=['CPI_yoy', 'M1_yoy'],
    sample_signal_types=['historical_high']
)
```

### 敏感性测试

```python
# 运行宏观事件数量敏感性测试
from refactored_macro_strategy.workflows.sensitivity_analysis import run_both_strategies_sensitivity_test

# 测试不同信号数量下的策略表现
results = run_both_strategies_sensitivity_test(
    data_path="宏观指标与逻辑.xlsx",
    signal_counts=[5, 7, 9, 11, 13]  # 测试前5/7/9/11/13个宏观事件
)
```

### 多信号投票策略

```python
# 运行多信号投票策略
from refactored_macro_strategy.workflows.multi_signal_workflow import run_both_voting_strategies

# 基于11个宏观事件的投票决策
results = run_both_voting_strategies("宏观指标与逻辑.xlsx")
```

## 📈 使用示例

详细的使用示例请参考：
- [基础示例](refactored_macro_strategy/examples/run_example.py)
- [稳定性分析](refactored_macro_strategy/examples/reanalyze_stability.py)
- [配置指南](refactored_macro_strategy/VALUE_GROWTH_vs_BIG_SMALL_GUIDE.md)
- [敏感性测试快速入门](refactored_macro_strategy/SENSITIVITY_QUICK_START.md)
- [敏感性分析详细指南](refactored_macro_strategy/SENSITIVITY_ANALYSIS_GUIDE.md)
- [多信号投票策略示例](refactored_macro_strategy/examples/sensitivity_test_example.py)

## 📋 数据格式

系统支持Excel格式的宏观数据，要求包含以下列：
- `ValueR`: 价值风格收益率
- `GrowthR`: 成长风格收益率
- 各类宏观经济指标列

## 🔍 结果分析

系统自动生成：
- 📊 最佳信号组合筛选
- 📈 策略性能对比分析
- 📋 标准化Excel报告
- 🎯 显著性统计检验

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 [Issue](../../issues)
- 发起 [Discussion](../../discussions)

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和研究人员。

---

**⭐ 如果这个项目对你有帮助，请给它一个星标！** 
# 上下文
文件名：TASK_MacroCycle_R_to_Python.md
创建于：[当前日期时间]
创建者：AI
关联协议：RIPER-5 + Multidimensional + Agent Protocol 

# 任务描述
将R脚本 `Calc_MacroEcoCycle_v3.R` 及其依赖 `Pkg_RiskBudget.R` 中的宏观经济周期计算逻辑迁移到Python。

# 项目概述
该项目通过分析宏观经济指标（如CMI, FIN, PMI, CPI, M1, M2等）来确定当前的宏观经济周期阶段（如复苏、繁荣、衰退、滞胀）。
主要步骤包括数据加载、数据清洗与转换、HP滤波、指标方向判断、周期概率计算和周期映射。
最终结果输出到Excel文件。

---
*以下部分由 AI 在协议执行过程中维护*
---

# 分析 (由 RESEARCH 模式填充)
R脚本 `Calc_MacroEcoCycle_v3.R` 和 `Pkg_RiskBudget.R` 已被分析。
关键功能包括：
- 从Excel加载数据。
- `info` DataFrame/tibble 作为元数据存储。
- 特定指标的合并逻辑（CMI, FIN）。
- 数据填充（`downFill`），0值转NA。
- HP滤波（`hpFilter`）。
- 指标方向计算（`getDirection`）。
- 基于映射表填充NA方向（`fillDrNaByidx2`）。
- 计算增长、通胀、流动性的上行概率（`udCycleProb`）。
- 将概率或方向组合映射到具体经济周期名称（`udCycleMap`, `hpCycleMap`）。
- 动态周期计算（`getDynamicUDCycle`）和历史周期计算（`hist_ud_cycle`）。
- 辅助日期处理函数（`preFriday`, `getPosChgDts`）。
- 结果输出到Excel。

核心R包依赖：`xts`, `openxlsx`, `mFilter`, `lubridate`, `tidyverse`, `roll`。

# 提议的解决方案 (由 INNOVATE 模式填充)
方案是创建一个Python项目，包含两个主要文件：
1. `pkg_risk_budget.py`: 包含从 `Pkg_RiskBudget.R` 迁移过来的辅助函数。
2. `macro_eco_cycle_v3.py`: 包含从 `Calc_MacroEcoCycle_v3.R` 迁移过来的主执行逻辑。

核心Python库：
- `pandas` 用于数据结构和操作 (替代 `xts`, `data.frame`)。
- `numpy` 用于数值计算。
- `statsmodels.tsa.filters.hpfilter` 用于HP滤波 (替代 `mFilter::hpfilter`)。
- `openpyxl` (通过pandas) 用于Excel读写 (替代 `openxlsx`)。
- Python内置 `datetime` 和 `dateutil` (如果需要) (替代 `lubridate`)。
- 自定义函数实现 `tidyverse` 和 `roll` 包中的部分功能逻辑。

# 实施计划 (由 PLAN 模式生成)
**目标Python文件名**: `macro_eco_cycle_v3.py` (主逻辑), `pkg_risk_budget.py` (辅助函数)

**实施检查清单**:

1.  **项目结构设置**:
    1.  创建 `pkg_risk_budget.py` 文件。
    2.  创建 `macro_eco_cycle_v3.py` 文件。
    3.  在两个Python文件的开头添加必要的导入语句:
        *   `pkg_risk_budget.py`: `import pandas as pd`, `import numpy as np`, `from statsmodels.tsa.filters import hpfilter as sm_hpfilter`, `from datetime import datetime, timedelta`
        *   `macro_eco_cycle_v3.py`: `import pandas as pd`, `import numpy as np`, `from datetime import datetime, timedelta`, `import pkg_risk_budget as prb`

2.  **`pkg_risk_budget.py` - 辅助函数实现**:
    *   注意：`info` DataFrame 在R中是全局的，但在Python中，我们将把它作为参数传递给需要它的函数。
    1.  实现 `get_beg(info_df, name)` -> `pd.Timestamp`
    2.  实现 `get_update(info_df, name)` -> `pd.Timestamp`
    3.  实现 `get_yoy(series)` -> `pd.Series`
    4.  实现 `combine_cmi(cmib_series, cmie_series, beg_date, update_date)` -> `pd.Series`
    5.  实现 `combine_fin(fin_series, finc_series, fino_series, beg_date)` -> `pd.Series`
    6.  实现 `zero_to_na(df)` -> `pd.DataFrame`
    7.  实现 `down_fill(df, zero_adj=True)` -> `pd.DataFrame`
    8.  实现 `hp_filter_df(df, lambda_val)` -> `pd.DataFrame` (trends)
    9.  实现 `get_direction(df, calc_dt, std_tv, smp_num=12)` -> `pd.DataFrame`
    10. 实现 `fill_dr_na_by_idx2(df, idx_map_df)` -> `pd.DataFrame`
    11. 实现 `ud_cycle_prob(df, idx_map_df)` -> `pd.DataFrame` ('growth', 'inflation', 'liquid')
    12. 实现 `ud_cycle_map(ud_prob_df, cyc_map_df, width=1)` -> `pd.DataFrame` (8 cycle types probabilities)
    13. 实现 `hp_cycle_map(hp_df, cyc_map_df)` -> `pd.Series` (cycle names)
    14. 实现 `pre_friday(d_date)` -> `pd.Timestamp`
    15. 实现 `get_pos_chg_dts(dts_series, beg_date, end_date, freq='W')` -> `pd.Series` of Timestamps
    16. 实现 `hist_ud_cycle(raw_factor_df, idx_map_df, cyc_map_df, lambda_val, hp_filter_func, get_direction_func, fill_dr_na_func, ud_cycle_prob_func, ud_cycle_map_func, backtest_beg='2012-01')` -> `pd.DataFrame` or `pd.Series` (cycle names)

3.  **`macro_eco_cycle_v3.py` - Main Script Logic**:
    1.  定义文件路径和全局常量 (e.g., `hp_lambda`).
    2.  加载 `Eg_MacroEcoCycle.xlsx` (sheets 'EDB', 'INFO').
    3.  数据准备 (R代码 `Calc_MacroEcoCycle_v3.R` 第60-118行):
        *   Melt, merge, type conversions, filtering.
        *   `combine_input_df` and `noneed_combine_df` creation.
        *   CMI 指标合成 (调用 `prb.combine_cmi`).
        *   FIN 指标合成 (调用 `prb.combine_fin`).
        *   构建 `growth_df`, `inflation_df`, `liquid_df`.
        *   构建 `raw_factor` (调用 `prb.down_fill`).
    4.  动态 UD 周期计算 (R代码 第127-162行):
        *   创建 `idx_map` 和 `cyc_map` DataFrames.
        *   定义 `beg_dt_dyn`, `end_dt_dyn` (调用 `prb.pre_friday`).
        *   生成 `dts_for_loop` (调用 `prb.get_pos_chg_dts`).
        *   循环计算每日动态概率:
            *   数据切片和预处理 (0值基于update_day).
            *   调用 `prb.hp_filter_df`, `prb.get_direction`, `prb.fill_dr_na_by_idx2`, `prb.ud_cycle_prob`.
            *   处理特殊日逻辑 (day_num < 10).
        *   合并 `dynamic_prob_df`, 调用 `prb.down_fill`.
        *   调用 `prb.ud_cycle_map` 得到 `dynamic_cycle_probs`.
        *   从概率确定 `dynamic_cycle` (e.g., `idxmax`).
    5.  静态宏观周期计算 (R代码 第167-192行):
        *   调用 `prb.hp_filter_df` on `raw_factor` -> `hp_factor`.
        *   调用 `prb.get_direction` on `hp_factor` -> `dr_factor`.
        *   处理 `dr_factor_ud`, 调用 `prb.ud_cycle_prob` -> `ud_prob_static`.
        *   调用 `prb.ud_cycle_map` -> `ud_cycle_probs_static`, then `ud_cycle_static` (`idxmax`).
        *   处理 `hp_model_idx`, 调用 `prb.hp_cycle_map` -> `hp_cycle_static`.
        *   调用 `prb.hist_ud_cycle` -> `ud_cycle_hist` (final version of ud_cycle).
    6.  输出结果到Excel (R代码 第196-207行) using `pd.ExcelWriter`.

4.  **Review and Refine**:
    1.  单元测试 `pkg_risk_budget.py` 中的各函数。
    2.  集成测试 `macro_eco_cycle_v3.py`。
    3.  输出结果与R版本对比验证。
    4.  代码清理、优化和文档添加。

# 当前执行步骤 (由 EXECUTE 模式在开始执行某步骤时更新)
> 正在执行: "[步骤编号和名称]"

# 任务进度 (由 EXECUTE 模式在每步完成后追加)
*   2025-05-15 17:08:58
    *   步骤：1. Project structure settings (Create files, Add imports)
    *   修改：
        *   `pkg_risk_budget.py`: Created and added imports (pandas, numpy, statsmodels.tsa.filters.hpfilter, datetime).
        *   `macro_eco_cycle_v3.py`: Created and added imports (pandas, numpy, datetime, pkg_risk_budget).
    *   更改摘要：项目文件结构和基本导入已设置完毕。
    *   原因：执行计划步骤 1。
    *   阻碍：无。
    *   用户确认状态：成功
*   2025-05-15 17:18:07
    *   步骤：2. `pkg_risk_budget.py` - 辅助函数实现 (所有16个函数)
    *   修改：
        *   `pkg_risk_budget.py`: Implemented all 16 helper functions:
            - `get_beg`, `get_update`, `get_yoy`
            - `combine_cmi`, `combine_fin`
            - `zero_to_na`, `down_fill`
            - `hp_filter_df`, `get_direction`
            - `fill_dr_na_by_idx2`, `ud_cycle_prob`
            - `ud_cycle_map`, `hp_cycle_map`
            - `pre_friday`, `get_pos_chg_dts`
            - `hist_ud_cycle` (updated to return DataFrame of probabilities)
    *   更改摘要：辅助函数模块 `pkg_risk_budget.py` 已完成所有函数的初步实现。
    *   原因：执行计划步骤 2。
    *   阻碍：`edit_file` tool had difficulties with full-file updates, requiring careful use of `reapply` or providing full content. Some R logic (e.g., in `combine_cmi`, `fill_dr_na_by_idx2`, `get_pos_chg_dts`) was complex to translate directly and may need further review/testing for exact equivalence.
    *   用户确认状态：成功
*   2025-05-15 17:25:28
    *   步骤：3.1, 3.2, 3.3 (Data Loading and Preparation up to raw_factor_df)
    *   修改：
        *   `macro_eco_cycle_v3.py`: 
            - Added constants and file paths.
            - Implemented loading of EDB, INFO, IDX_MAP, CYC_MAP, HP_CYC_MAP sheets.
            - Implemented data preparation: 
                - EDB melt, merge with INFO, date conversions, and filtering.
                - Creation of `raw_tso_pivot`.
                - Identification of `combine_input_abbrs` and `noneed_combine_abbrs`.
                - Creation of `combine_input_df` and `noneed_combine_df`.
                - Synthesis of `cmi_series` and `fin_series` using `prb` functions.
                - Construction of `growth_df`, `inflation_df`, `liquid_df` (incorporating CMI/FIN into liquid).
                - Creation of `raw_factor_df` by concatenating factor groups, dropping rows with all-NA in a group, and `prb.down_fill(zero_adj=False)`.
    *   更改摘要：主脚本加载了所有必需的数据，并完成了核心数据准备阶段，生成了 `raw_factor_df`。
    *   原因：执行计划步骤 3.1, 3.2, 3.3。
    *   阻碍：Linter error with multi-line if statement required a quick fix. Careful handling of column names during merges for `raw_factor_df` and subsequent `dropna` was needed.
    *   用户确认状态：成功
*   2025-05-15 17:30:23
    *   步骤：3.4 Dynamic UD Cycle Calculation
    *   修改：
        *   `macro_eco_cycle_v3.py` (in `main()`):
            - Calculated `beg_dt_dyn` and `end_dt_dyn` using `prb.pre_friday`.
            - Generated `dts_for_loop` using `pd.date_range` and `prb.get_pos_chg_dts`.
            - Implemented the main loop iterating through `dts_for_loop`:
                - Sliced `raw_factor_df` up to the current loop date (`tso_sub`).
                - Applied zero-value adjustment to `tso_sub` based on indicator update dates from `info_df`.
                - Called `prb.hp_filter_df`, `prb.get_direction`, `prb.fill_dr_na_by_idx2` (with `.dropna()`).
                - Called `prb.ud_cycle_prob` on the processed direction data.
                - Averaged the last `min(n_rows, 10)` rows of these probabilities.
                - Appended the averaged probability row (indexed by current loop date) to `dynamic_prob_list`.
            - Concatenated `dynamic_prob_list` into `dynamic_prob_df_raw`.
            - Applied `prb.down_fill(zero_adj=False)` to `dynamic_prob_df_raw` -> `dynamic_prob_df_filled`.
            - Called `prb.ud_cycle_map` (with `UD_ROLLING_WIDTH`) on `dynamic_prob_df_filled` -> `dynamic_cycle_probs`.
            - Determined `dynamic_cycle` using `idxmax()` on `dynamic_cycle_probs`.
    *   更改摘要：动态宏观经济周期概率和最终周期状态已计算完毕。
    *   原因：执行计划步骤 3.4。
    *   阻碍：无。
    *   用户确认状态：成功
*   2025-05-15 17:32:55
    *   步骤：3.5 Static Macro Cycle Calculation
    *   修改：
        *   `macro_eco_cycle_v3.py` (in `main()`):
            - Calculated `hp_factor_df` using `prb.hp_filter_df` on `raw_factor_df`.
            - Calculated `dr_factor_df` using `prb.get_direction` on `hp_factor_df`.
            - UD Static Cycle:
                - Called `prb.fill_dr_na_by_idx2` and `.dropna()` on `dr_factor_df` -> `dr_factor_ud_df`.
                - Called `prb.ud_cycle_prob` -> `ud_prob_static_df`.
                - Called `prb.ud_cycle_map` -> `ud_cycle_probs_static` (DataFrame of probabilities).
                - Determined `ud_cycle_static` as the cycle name with max probability for the last date from `ud_cycle_probs_static` (Series with one value).
            - HP Static Cycle:
                - Selected relevant indicators from `info_df` (where `usehp==1`).
                - Filtered `dr_factor_df` for these indicators and `.dropna()` -> `hp_model_idx_df`.
                - Called `prb.hp_cycle_map` -> `hp_cycle_static` (Series of cycle names).
            - Historical UD Cycle:
                - Called `prb.hist_ud_cycle` with `raw_factor_df` -> `ud_cycle_hist_probs_df` (DataFrame of probabilities).
                - Derived `ud_cycle_hist` (Series of cycle names) using `idxmax()` on `ud_cycle_hist_probs_df`.
    *   更改摘要：静态宏观经济周期（UD模型、HP模型）和历史UD周期已计算完毕。
    *   原因：执行计划步骤 3.5。
    *   阻碍：无。
    *   用户确认状态：[待确认]

# 最终审查 (由 REVIEW 模式填充)
[实施与最终计划的符合性评估总结，是否发现未报告偏差] 
# R Third-Drill Acceptance (v0.2 P1)

第三次 Drill（Drill 3）必须包含至少一个真实子问题由 R 承担，且 R 相对 Python 有真实方法学优势。
本任务不选择 Drill 3 题目；本文只定义验收标准。

## 首选类别

- 面板数据（panel data）
- 计量经济学（econometrics：固定效应/聚类标准误/IV）
- 因果推断（DiD、staggered adoption、匹配）
- 高级统计（分位数回归、生存分析）
- 经典时间序列（ARIMA/ETS）

## 验收标准（全部满足）

1. Python 预处理：数据清洗/构造/审计在 Python 完成，冻结输入（可哈希）。
2. Rscript 模型执行：通过 Rscript <model.R> --input ... --outdir ... 调用（无 rpy2）。
3. OUTPUT_CONTRACT 输出：coefficients.csv / metrics.csv / predictions.csv（适用时）/ model_summary.txt / run_metadata.json 齐全。
4. run metadata：R 版本、包版本、输入 hash、参数、时间戳、退出状态（见 r_toolbox/io_contract.R）。
5. 可复现包环境：renv.lock 或等价冻结；CORE 包可用，SPECIALIZED 包按任务安装并记录。
6. 论文解释：结论必须在论文中解释并追溯到输出文件（CLAIM_EVIDENCE）。
7. 至少一个独立交叉检验：例如 Python statsmodels/自编实现，或 MATLAB/Mathematica 独立实现，结果数值一致。
8. 方法路由记录：按 config/method_router.yaml 记录 use_when/avoid_when/crosscheck。

## 选择原则

- 不为了用 R 而用 R：必须说明 R 相对 Python 的优势（如 fixest 多维 FE、did 特定估计量）。
- 若某子问题两种语言都可行且 R 无差异化收益，则该子问题不算满足验收。
- 选择题目由 SOL/人工在 Drill 3 规划时确定（本任务不选择）。

# MMKit R Output Contract (v0.2 P0)

标准 R 输出契约。任何 R 模型/分析脚本必须把标准输出写入**一次运行一个独立输出目录**，文件名固定，字段固定。

## Standard outputs

| 文件 | 必填 | 内容 |
| --- | --- | --- |
| [coefficients.csv] | YES | 每行一个参数。MANDATORY 列：term、estimate、std_error、statistic、p_value。term 必须与设计矩阵列一一对应（含 (Intercept)）。 |
| [predictions.csv] | YES | 每行一个观测。MANDATORY 列：index、observed、predicted、residual。index 为输入数据的行号（1-based），保证与输入可对齐。 |
| [metrics.csv] | YES | MANDATORY 列：metric、value。命名约定：n_obs、r_squared、adj_r_squared、rmse、mae、aic、bic、loglik 等。 |
| [model_summary.txt] | YES | 人读模型摘要（R summary() 输出或等价物），必须包含模型调用/公式与估计参数。 |
| [run_metadata.json] | YES | 运行元数据（见下）。 |

## run_metadata.json — MANDATORY fields

| 字段 | 含义 | 要求 |
| --- | --- | --- |
| r_version | R 版本字符串 | 取自 R.version.string |
| input_sha256 | 输入文件 SHA256 | 为空时必须写 null 并在 stderr 警告（不可伪造） |
| arguments | 完整命令行参数 | commandArgs(TRUE) 空格拼接 |
| timestamp | UTC ISO-8601 运行时刻 | 如 2026-01-01T08:00:00Z |
| exit_status | R 进程退出码 | 0 = 成功 |
| package_status | 已安装包清单 | 用于复现 |
| session_info | sessionInfo() 摘要 | 用于复现 |

建议字段：contract_version、script、input_file、model_type。

## 论文主张如何追溯 (claim to evidence)

1. 论文中的任何系数/显著性 → coefficients.csv 的 term/estimate/p_value。
2. 论文中的任何拟合优度/误差度量 → metrics.csv，并用 run_metadata.json 的 input_sha256 + timestamp 锁定输入与运行。
3. 论文中的任何预测效果/样本内拟合 → predictions.csv。
4. 论文图表的数值必须能由 predictions.csv / coefficients.csv + 代码重建；不得使用未被记录数值的手绘数值。
5. 每个引用的数字都要能写出一条链：运行命令 + 输入哈希 + 输出文件 + 字段值。该链在 CLAIM_EVIDENCE.csv 登记。

## 硬性规则

- 不得写入未实际运行的数值（无手工回填）。
- 输出目录内不得混入其他模型的输出；一次运行一个 run id。
- 缺失输入或失败运行时：写 exit_status != 0 且输出目录内不得出现伪造的完整结果；只允许 run_metadata.json（记录失败）与错误信息。
- 数值精度：CSV 使用 >=15 有效数字（options(digits=17)），保证跨工具比对。

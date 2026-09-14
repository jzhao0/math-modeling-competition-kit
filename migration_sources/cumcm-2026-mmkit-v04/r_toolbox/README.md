# MMKit R Toolbox

R 在 MMKit 中不是 Python 的替代品，而是**专业统计 / 计量后端**。
本目录是 v0.2 P0 已落地的实现；底层原则见 docs/MMKIT_V02_SYSTEM_UPGRADE.md。

## 1. 使用原则

- Python 继续负责数据工程、总流程、优化、机器学习、图论、仿真和论文自动化（总控层）。
- 当面板数据、固定效应、DiD、匹配、分位数回归、生存分析或经典统计推断在 R 中更成熟可靠时，优先调用 R。
- 不为了“多语言”而使用 R；必须有明确方法收益。
- R 结果必须通过文件协议返回（CSV/JSON），不靠人工复制终端输出进入论文。
- Python 保持默认总控；R 作为专业统计后端被调用，两者通过 Rscript 子进程 + 文件 I/O 通信。

## 2. 目标包路由（共 14 个）

基础（7）：

- readr / readxl：读写
- dplyr / tidyr：清洗与整形
- ggplot2：数据图
- broom：模型输出转 tidy 表，便于回传 Python/LaTeX
- renv：冻结 R 包版本，保证可复现

统计/计量（7）：

- fixest：多维固定效应、OLS/GLM/IV、聚类标准误等（面板/FE 首选）
- plm：经典面板 FE/RE/FD/GMM
- did：多期、多组处理时点 DiD
- MatchIt：匹配 / 倾向得分预处理
- quantreg：分位数回归
- survival：生存分析
- forecast：经典 ARIMA / ETS 等时间序列

按题目需要安装/启用，不要求每题全量加载。包缺失是可报告状态（bootstrap 输出列出），
不是 agent 循环理由；安装由人工决定。

## 3. 标准调用方式

```text
Python preprocess
  -> input.csv / input.parquet
  -> metadata.json
  -> Rscript model.R --input ... --outdir ...
  -> coefficients.csv
  -> metrics.csv
  -> predictions.csv
  -> model_summary.txt
  -> run_metadata.json
  -> Python / LaTeX
```

不把 rpy2 设为正式比赛关键依赖；优先使用 Rscript + 文件 I/O，以降低跨环境故障面。

## 4. 输出契约

每个正式 R 模型脚本至少输出：coefficients.csv、metrics.csv、predictions.csv（需要预测时）、
model_summary.txt（辅助）、run_metadata.json（R 版本、包版本、输入 hash、参数、运行时间、退出状态）。
字段细节、必填规则与论文主张追溯见 OUTPUT_CONTRACT.md；任何论文主张不得只引用 summary(model) 的终端文本。

## 5. 本地 P0 实现

| 文件 | 用途 |
| --- | --- |
| bootstrap.R | 环境报告：R 版本、renv 状态、14 个目标包可用性；默认不安装任何包；--smoke 轻量模式；--json 机器报告。 |
| io_contract.R | 标准输出写入助手（coefficients/metrics/predictions/summary/metadata；仅 base R；SHA256 用 digest 或 certutil）。 |
| ols_smoke.R | 确定性 OLS 契约冒烟：Rscript ols_smoke.R <input.csv> <outdir>。 |
| OUTPUT_CONTRACT.md | 输出契约与论文主张追溯规则。 |
| scripts/setup_windows_r.ps1 | R 运行时发现（只读、幂等、不安装、不改全局环境变量）。 |
| scripts/smoke_python_r.py | Python 生成确定性数据 → 调 Rscript → R 拟合 lm() → 双端比对（1e-10 容差）。 |

使用：

```powershell
.\scripts\setup_windows_r.ps1                          # 发现 R（只读，不安装）
Rscript r_toolbox\bootstrap.R --smoke                  # 轻量可用性报告
Rscript r_toolbox\bootstrap.R --json reports\r_bootstrap.json
.\.venv\Scripts\python.exe scripts\smoke_python_r.py   # Python<->R OLS 契约冒烟
```

## 5b. renv 可复现性（P1 状态）

**renv 已初始化成功：RENV_INITIALIZED = TRUE（R 4.6.1，bare init，exit 0）。**
追踪文件：.Rprofile、renv/activate.R、renv/settings.json、renv/.gitignore、renv.lock（bare 初始化为空文件，如实保留）；
忽略：renv/library/、local/、cellar/、lock/、python/、sandbox/、staging/（由 renv/.gitignore 管理）。
CORE=renv,readr,dplyr,broom,ggplot2；SPECIALIZED=fixest,plm,did,MatchIt,quantreg,survival,forecast —— 均按需安装，**当前未安装**。
若在全新机器恢复：

```powershell
& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" -e "renv::restore(project='r_toolbox')"
```

（此前安装步骤备份，正常环境下无需重复：若在**普通 PowerShell（管理员或可写用户库）**中安装 renv，可执行：

```powershell
$ulib = "$env:USERPROFILE\Documents\R\win-library\4.6"
New-Item -ItemType Directory -Force $ulib | Out-Null
& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" -e "options(repos=c(CRAN='https://cloud.r-project.org')); .libPaths(c('$ulib', .libPaths())); install.packages('renv', lib='$ulib')"
# 然后：Init 项目级 renv（bare：不自动安装 14 包栈）
& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" -e "renv::init(project='r_toolbox', bare=TRUE)"
```）

包分级（不自动全量安装）：CORE = renv, readr, dplyr, broom, ggplot2；SPECIALIZED = fixest, plm, did, MatchIt, quantreg, survival, forecast（仅真实任务需要时安装并记录版本）。

## 5c. Windows R 执行规则（已验证，基于本机行为观察）

- **Rscript 路径发现**：优先 `scripts/setup_windows_r.ps1` 探测 PATH 与常见安装路径，或使用绝对路径 `C:\Program Files\R\R-4.6.1\bin\Rscript.exe`。
- **实质/多行 R 逻辑一律写在 .R 文件**（如 ols_smoke.R，经 Rscript <file.R> 执行），Windows 前端的复杂/多行 `Rscript -e` 调用在本机观察会导致 R 前端崩溃（RENV_INIT 亦通过 .R 等价方式成功）。
- `Rscript -e` 仅允许用于**单表达式探针**（如查询版本、requireNamespace 布尔检查）。
- 竞赛期间不依赖多行 `-e`；所有正式 R 运行必须走 .R 文件 + 参数（见 ols_smoke.R 的 argv 模式）。
- rpy2 不是关键依赖：Python↔R 仅经 Rscript 子进程 + 文件协议。
- **不安装 Rtools**：除非某个包明确需要源码编译且无兼容二进制。

## 6. 验收标准

R backend 标记 READY 前必须：

1. Windows 可发现 Rscript。
2. renv 可恢复冻结环境。
3. Python 能调用一个最小 R 回归并读取 CSV 输出。
4. R 与 Python 对同一 OLS 小样本的系数/预测结果在数值容差内一致。
5. sessionInfo() 与输入 hash 被记录。
6. 至少第三次 Drill 实际用 R 解决一个统计/面板/时间序列子问题。

## 7. 后续建议脚本

```text
r_toolbox/
├── bootstrap.R
├── io_contract.R
├── panel_fixed_effects.R
├── panel_random_effects.R
├── did_event_study.R
├── matching.R
├── quantile_regression.R
├── survival_analysis.R
├── time_series.R
└── statistical_tests.R
```

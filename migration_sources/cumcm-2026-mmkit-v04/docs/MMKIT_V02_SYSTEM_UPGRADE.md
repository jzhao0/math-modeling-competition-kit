# MMKit v0.2 系统升级规范

> 目标：把两次 Drill 中验证有效的流程固化为**整个 CUMCM 数学建模体系**，而不是为某一道 B 题继续堆补丁。
>
> 核心原则：模型正确性与证据链优先；Python 继续做总控；R 作为专业统计/计量后端；外部 Skills 只吸收有增益的能力，不允许多个框架同时接管工作流。

## 1. v0.2 的系统定位

MMKit v0.2 采用五层架构：

1. **Sol / 人工中央决策层**：题意、模型路线、假设、G2/G3、论文科学裁决。
2. **执行层**：Python / R / MATLAB / Mathematica + DSH / Codex 等执行器。
3. **专业 Skill 层**：文献、统计、科研图、论文审稿、CUMCM 合规等可插拔能力。
4. **证据层**：结果 CSV/JSON、CLAIM_EVIDENCE、ASSUMPTION_LEDGER、AI logs、运行日志。
5. **论文与提交层**：LaTeX、图表、引用、AI 声明、PDF/支撑材料、G4。

任何 Skill 都不得越过中央决策层自行改变已经冻结的数学模型。

---

## 2. Agent / Skill 路由

### Tier A：建议冻结到赛前本地的核心能力

- `cumcm-live-workflow-skill`
  - 用途：CUMCM 赛程/合规/终审检查、论文密度与交付流程参考。
  - 角色：**QA 与 workflow advisor**，不接管核心建模。

- `Supervisor-Skills`
  - 首选子技能：`deep-research`、`figure-designer`、`drawio-reconstruction`、`paper-writer`、`paper-polish`、`pre-submission-reviewer`。
  - 用途：文献深研、claim-first 图设计、证据门控写作、审稿人视角终审。

- `nature-skills`
  - 首选子技能：`nature-figure`、`nature-academic-search`、`nature-statistics`、`nature-reviewer`。
  - 用途：科研图、文献交叉核验、统计口径、严格审稿。

- `google-deepmind/science-skills`
  - 仅优先吸收：OpenAlex 文献检索能力、workflow-skill-creator。
  - 生命科学数据库类 Skill 不作为 CUMCM 通用依赖。

### Tier B：图表/论文专用增强

- `PaperBanana`：概念图/方法图参考生成，输出后必须转 SVG/Draw.io 并人工核对科学逻辑。
- `research-drawio-skill`：可编辑科研流程图、模型结构图、图形摘要。
- `figures4papers` / `Scientific-Figure-Design`：学习发表级 Python 图样式与多 panel 组织。
- `math-modeling-skill` / CUMCM paper-hand 类项目：只吸收质检、图文密度、获奖论文结构规律，不允许覆盖 MMKit 的 G1–G4 与证据链。

### 禁止事项

- 不允许同时启动多个“全流程总控 Skill”。
- 不允许为了“高级”而重复实现同类 checker / runner / review framework。
- 不允许 AI 生成图承担数值真实性；数据图必须由可复现代码从冻结结果生成。
- 比赛开始后遵守离线纪律，不在线搜索赛题答案、讨论、GitHub 解法。

---

## 3. Python + R 多语言建模架构

### 3.1 总原则

Python 保持默认总控，不迁移现有主系统。

R 定位为：

> **Python 建模体系中的专业统计/计量后端。**

选择语言的标准不是“更高级”，而是：**某个方法在哪个生态里实现最快、最可靠、最容易验证。**

### 3.2 任务路由

| 任务 | 首选 |
|---|---|
| 数据读取/清洗/工程管线 | Python |
| 普通描述统计/回归 | Python 或 R |
| 面板数据 | R 优先 |
| 多维固定效应 | R `fixest` 优先 |
| 经典面板 FE/RE/GMM | R `plm` |
| DiD / staggered adoption | R `did` / `fixest` |
| 匹配/倾向得分 | R `MatchIt` |
| 分位数回归 | R `quantreg` |
| 生存分析 | R `survival` |
| 时间序列 | Python / R；经典 ARIMA/ETS 可用 R `forecast` |
| 优化/运筹 | Python |
| 机器学习/深度学习 | Python |
| 图论/网络 | Python |
| 数值仿真/Monte Carlo | Python |
| 符号推导 | Mathematica / SymPy |
| MATLAB 交叉验证 | MATLAB |
| 统计论文图 | R/ggplot2 或 Python，按成图质量选择 |

### 3.3 R 最小依赖集合

基础：

- `readr`, `readxl`, `dplyr`, `tidyr`, `ggplot2`
- `broom`：把模型输出转成 tidy 表，便于回传 Python/LaTeX
- `modelsummary`（若赛前验证通过）：统一回归表输出
- `renv`：冻结 R 包版本，保证可复现

统计/计量：

- `fixest`
- `plm`
- `did`
- `MatchIt`
- `quantreg`
- `survival`
- `forecast`

按题目按需加载，不要求全量使用。

### 3.4 目录约定

建议新增：

```text
r_toolbox/
├── README.md
├── renv.lock
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

正式题目工作区可使用：

```text
04_models/
├── python/
└── r/
```

### 3.5 Python ↔ R I/O contract

优先采用**文件协议 + `Rscript` 子进程**，不把 `rpy2` 设为核心依赖。

标准流程：

```text
Python preprocess
  ↓
CSV/Parquet + metadata.json
  ↓
Rscript model.R --input ... --output ...
  ↓
coefficients.csv
model_metrics.csv
predictions.csv
model_summary.txt
run_metadata.json
  ↓
Python/LaTeX consume
```

每次 R 运行必须记录：

- `R.version.string`
- `sessionInfo()` / package versions
- 输入文件 hash
- 参数
- 输出路径
- exit code

---

## 4. 文献真实性流水线

文献流程升级为：

```text
SciSpace / deep-research / OpenAlex 发现
        ↓
Crossref / OpenAlex 元数据核验
        ↓
出版社页面 / DOI 最终确认
        ↓
BibTeX
        ↓
正文真实 cite
```

规则：

1. 不追求引用数量；优先 8–15 篇真正支撑模型与方法的高相关文献。
2. 任何 DOI、作者、年份、期刊必须由真实来源核验。
3. 不允许“主题条目”进入最终论文。
4. 赛题高度相似的赛后论文只可谨慎作为背景，不作为核心解题依据。
5. 参考文献必须与正文 claim 有绑定，不允许“列了但不 cite”。

建议新增 `references/REFERENCE_LEDGER.csv`：

```text
key,title,authors,year,venue,doi,url,verified_by,relevance,used_in_claims
```

---

## 5. 论文图表与公式密度标准

### 5.1 图表

不机械执行“每页必须一图”，采用**信息密度标准**：

- 建模/结果主体：原则上每 1–1.5 页至少有一个视觉锚点（图、表或关键公式组）。
- 每个子问题至少应有：模型/机制图 + 核心结果图或表；数据题额外要求数据审计/分布图。
- 一张图必须承担明确 claim，不做装饰图。
- 数据图只允许从冻结数据/结果程序化生成。
- AI 图只用于方法结构、流程、概念示意；生成后必须核对文本、箭头、变量与层级，并尽量保留 SVG/Draw.io 可编辑源。

### 5.2 公式

论文不是公式越多越好，但必须形成完整推导链：

```text
定义 → 目标函数/概率模型 → 约束/状态转移 → 求解准则 → 评价指标
```

每个问题至少包含能独立说明模型机制的核心公式组；避免只展示最终数值。

### 5.3 模型评价

正文模型评价建议：

- **约 2/3–3/4 为优点与可迁移价值**；
- **约 1/4–1/3 为局限与改进方向**。

优点必须具体，例如：

- 题意结构忠实；
- 概率/统计口径精确；
- baseline 与复杂模型增益清楚；
- proper/improper 或可行性处理严格；
- 不确定性传播；
- 可解释性；
- 可复现性；
- 独立交叉验证。

不得用空泛的“准确率高、适用性强、鲁棒性好”。

---

## 6. Skill 使用模式

Skill 不直接等于 Agent 权限。

建议路由：

```text
题意 / G2 / G3
  → Sol

文献深研
  → Supervisor deep-research
  → nature-academic-search / OpenAlex
  → 人工/出版社核验

统计题
  → Sol 选模型
  → Python preprocess
  → R bounded backend
  → Sol 解释与 G3

数据图
  → Python/R deterministic renderer

方法图
  → figure-designer
  → PaperBanana / research-drawio
  → 人工科学 QA

正文
  → evidence pack
  → bounded writer
  → Sol central review
  → pre-submission reviewer
```

---

## 7. 赛前本地冻结要求

正式比赛开始前完成：

1. 所需 Skill 仓库 clone/vendor 到本地，只保留明确需要的版本。
2. 记录 commit SHA / release tag / license。
3. R 安装并完成 smoke tests，生成 `renv.lock`。
4. Python/R 跨语言 smoke test。
5. OpenAlex/Crossref/SciSpace 等联网文献流程只在赛前准备/允许阶段使用；比赛时按官方联网纪律执行。
6. 图表工具和模板本地化，避免比赛时依赖在线 Midjourney/PaperBanana 等外部服务作为关键路径。

---

## 8. v0.2 实施优先级

### P0 — 立即做

- Python/R 版本与 README/pyproject 一致性审计。
- 新建 `r_toolbox/` 和 R smoke test。
- 加入 Rscript I/O contract。
- 新建 `REFERENCE_LEDGER.csv` 模板与 DOI 核验规范。
- 建立 Skill router：只登记允许的 Skill、用途、版本和禁止越权范围。

### P1 — Drill 2 后做

- 把两次 Drill 的成功/失败经验蒸馏为本项目自己的 `cumcm-live-v1` Skill。
- 接入 `nature-figure` / draw.io 科研图工作流。
- 建立 paper density audit：公式/图/表/claim coverage，而不是简单页数计数。

### P2 — 第三次 Drill 验证

- 选择一个统计/面板/时间序列型题目，强制真实使用 R backend。
- 验证 Python→R→CSV→LaTeX 全链路。
- 验证断网/无 Codex/无 DSH 情况下仍可完成。

---

## 9. v0.2 验收条件

达到以下条件才允许标记 `MMKIT_V02_READY`：

- Python 与 R 环境均可一键 smoke test。
- R 模型输出可由 Python/LaTeX 无人工复制消费。
- 至少一个 Drill 实际使用 R 并有独立交叉验证。
- Skill router 能阻止全流程 Skill 覆盖 G1–G4。
- 文献从发现到 DOI/出版社核验可追踪。
- 数据图与方法图有不同真实性规则。
- paper audit 能检查公式/图表/claim 分布，而不是鼓励装饰性密度。
- 比赛离线条件下主流程无关键在线单点依赖。

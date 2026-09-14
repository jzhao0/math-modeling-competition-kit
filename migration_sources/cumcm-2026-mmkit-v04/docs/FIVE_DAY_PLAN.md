# 5-Day Build & Validation Plan

目标：5 天完成可用工具链，并完成 3 次实操。每一天都必须有可验证产物，不以“装好了很多软件”作为完成标准。

## Day 1 — Environment discovery and freeze

任务：
- 探测 Windows 11：WSL2、Python、Git、Node/npm、LaTeX、MATLAB、Mathematica、WPS/Office、WinRAR、Agent CLI。
- 探测 macOS：Python、Git、LaTeX、Agent CLI，作为灾备基线。
- 确认 GitHub 私有仓库、克隆/拉取路径与本地项目目录。
- 接入 DeepSeek API；验证 Claude Code / OpenCode 至少一个能真实读写仓库。
- 建立 `.env`/credential 隔离，任何 Key 不进入 Git。

验收：`doctor` 报告落盘；新建测试项目；运行 Python；编译最小中文 PDF；Agent 可读写测试文件。

## Day 2 — Modeling pipeline

任务：
- 题面与附件清单、哈希、数据字典。
- EDA 模板和数据质量检查。
- 每问“目标/输入/输出/约束/评价指标”结构化。
- baseline -> 主模型 -> 诊断/稳健性流程。
- 结果统一输出为 CSV/JSON；图表从结果自动生成。
- 建立 `CLAIM_EVIDENCE.csv`。

验收：选一道往年数据/预测类题，跑到可复现结果和图。

## Day 3 — Paper, figures, compliance

任务：
- 2026 电子版 LaTeX 模板。
- 中文字体和跨 Windows/macOS/WSL 编译验证。
- 图表统一规范：尺寸、字体、单位、题注、位图/矢量导出。
- AI 使用 JSONL 审计日志 -> `AI工具使用详情.pdf`。
- Finalizer：匿名、文件大小、目录、声明、附录、支撑文件列表、关键数字一致性。

验收：一条命令生成可人工审阅的 `paper.pdf` 和支撑材料目录；人工门禁未批准时自动阻断最终提交。

## Day 4 — Drill 1 + Drill 2

### Drill 1: data / prediction / evaluation

重点测试：
- Excel/CSV 数据
- EDA
- 统计 / 时间序列 / ML
- 指标与数据泄漏
- 可解释性
- 高质量图表

### Drill 2: optimization / mechanism / simulation

重点测试：
- 目标函数与约束
- LP/MILP/NLP/启发式优化或机理模型
- MATLAB / Mathematica 交叉验证价值
- 敏感性、边界、可行性

强制故障：Codex 不可用，只用 DeepSeek API + 可用 Agent 完成闭环。

每次记录：总耗时、API 成本、人工返工次数、最严重错误、自动质检发现的问题和未发现的问题。

## Day 5 — Drill 3 + release candidate

完整模拟：
- 多题快速对比
- G1 选题
- G2 路线
- 正式计算
- G3 结果确认
- 论文
- AI 详情
- 支撑材料
- G4
- 最终冻结

额外故障测试：
- 比赛期间完全不访问 GitHub。
- Codex=0。
- 原生 Claude API=0。
- 一个免费 Agent/模型不可用。

封版：
- 锁依赖版本。
- 锁 vendor commit SHA。
- 生成离线恢复说明。
- 冻结 `RUNBOOK.md`。
- 标记 release candidate。

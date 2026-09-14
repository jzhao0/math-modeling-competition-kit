# Architecture

## Design goal

把“某个 Agent 会不会用、某个额度还有没有”从比赛成败因素里移除。任何执行器都只能通过同一套项目文件推进状态。

## Host layout

### Windows 11 — primary compute / agent / submission host

Windows 原生现在是正式比赛主环境，负责：
- Python 3.13 项目环境（由 `uv` 管理）与科学计算栈
- Git 与仓库状态管理
- OpenCode / Claude Code / Codex / DSH 等 Agent CLI
- MATLAB R2024b 数值计算、优化和交叉验证
- Mathematica 14 符号推导与公式核验
- TeX Live / XeLaTeX / latexmk 论文构建
- WPS / Office 最终人工审阅
- WinRAR、文件名、最终提交与人工视觉检查

项目由 `.python-version`（3.13）与 `pyproject.toml`（`requires-python >=3.13,<3.14`）锁定 CPython 3.13；竞赛仓库固定使用隔离的 `.venv`，避免污染全局环境。

已观察到但暂不作为核心依赖：AxMath、Mathcad 15。具体许可证和 MATLAB Toolboxes 待环境探测确认。

### WSL2 Ubuntu — optional compatibility layer

WSL 不进入正式比赛关键路径。仅当某个高价值第三方工具只能在 Linux/bash 下稳定运行时再启用，用于：
- Linux-only GitHub 项目
- bash/make/apt 工作流
- 与服务器/Docker 环境的兼容性测试

不得为了使用 WSL 复制第二份业务状态或维护第二套独立 Python/Agent 主环境。

### macOS — disaster recovery / independent build

现有 LaTeX 环境可用于独立编译和最终交叉检查。赛前不维护第二套独立业务状态；仓库仍是唯一真源。

## Control plane

OpenCode / Claude Code / Codex / DSH 等均为可替换执行器。

任何执行器只通过以下状态文件协作：
- `docs/context/PROJECT_STATE.md`
- `docs/context/DECISION_LOG.md`
- `docs/context/AGENT_HANDOFF.md`
- 正式题目中的 `STATUS.yaml`
- `ASSUMPTION_LEDGER.md`
- `CLAIM_EVIDENCE.csv`
- `08_ai_logs/ai_usage.jsonl`

## Modeling layer

默认 Python 3.13。按题目需要启用：
- 数值线性代数 / 统计 / ML / 时间序列
- 运筹优化 / 整数规划 / 启发式优化
- 图网络 / 仿真 / 微分方程
- MATLAB 交叉验证
- Mathematica 符号验证

原则：先 baseline，后主模型；复杂度必须由增益证据支持。

## Evidence layer

正式论文不可直接读取 Agent 自述的结果。关键数值必须落盘为 CSV/JSON/可重建图表，并建立 `claim -> evidence` 映射。

## Document layer

- Windows TeX Live/XeLaTeX：权威 PDF 生成路径。
- macOS LaTeX：独立灾备编译。
- WPS/Office：最终人工审阅和兼容性检查。
- 图表由代码生成，至少保留高分辨率位图和适合时的矢量版本。
- 电子论文与纸质版的专用页逻辑分开构建。

## Compliance layer

- AI 使用日志
- `AI工具使用详情.pdf`
- 匿名信息扫描
- 页数/文件大小检查
- 支撑材料清单
- 代码可运行性检查
- 论文关键数字与结果文件一致性检查
- 四道人类门禁

## Failure strategy

正式验收必须通过以下降级场景：
- Codex 额度为 0
- 原生 Claude API 不可用
- 某一个免费模型/Agent 不可用
- WSL 完全不可用
- 比赛期间不访问 GitHub
- Windows 临时故障时，macOS 至少能够完成必要的论文构建/检查与关键 Python 任务恢复

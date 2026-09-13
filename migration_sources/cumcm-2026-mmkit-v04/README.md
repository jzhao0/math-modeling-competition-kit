# CUMCM 2026 MMKit

赛前本地化的全国大学生数学建模竞赛工作台。目标不是让 AI 无人值守“自动交卷”，而是把选题、题意拆解、数据审计、建模、代码执行、图表、论文、AI 使用留痕和最终提交质检做成一套**可复现、可切换 Agent、证据可追踪、必须人工审核**的流水线。

> 当前状态：**PRECONTEST_FREEZE_READY / v0.4 EVIDENCE GOVERNANCE + EXACT G4 LOCK**。
>
> - v0.3 的 claim/evidence-first 写作、human-style review、competition visual 和唯一 `09_submission/` 仍为基础。
> - v0.4 已加入 evidence credential、gate hash invalidation、real-pilot comparison、review independence、clean-room support test 和 G4 exact-file lock。
> - 教师 `cumcm-step-review`、2026 Word/PPT/LaTeX 要求和教师 `mathmodels` R 包已经审计/固化；教师要求优先于第三方通用 skill。
> - 赛前最后一次 GitHub 数模生态 harvest 已完成并关闭；第三方项目只蒸馏有价值机制，不新增比赛时网络依赖。
> - Drill-03 已作为赛前演练归档在 `G4_PREVIEW_PACKAGING_FIXED_AWAITING_HUMAN_LOCK`。论文、AI 详情与支撑包的 packaging/clean-room 已闭环，但演练不再继续做人工 G4，也不写入 `09_submission/`。
> - 当前直到官方 2026 赛题发布：**本地无需任何操作**。

## 2026 关键纪律

- 2026 规则允许 AI 辅助，但论文的建模、分析和结论仍由参赛队负责，AI 生成内容必须人工核验。
- 使用 AI 时，论文参考文献前保留简短 AI 声明，支撑材料提供按教师/官方模板填写的 AI 使用详情。
- **从正式比赛第一条 AI 交互开始记录 `08_ai_logs/ai_calls.jsonl`**；不要赛后凭记忆补造型号、时间戳、提示词或采用决定。
- 比赛期间不得在 GitHub 等交流平台浏览、发布或讨论赛题相关内容；赛前完成依赖、模板、参考仓库与 skill 的本地冻结。
- 比赛开始后不联网搜索赛题实现，不拉取新 skill，不升级已冻结 pin，不临时迁移 Agent 平台。

官方规则以全国大学生数学建模竞赛官网和赛区/学校最新通知为准。

## 主环境

**Windows 11 原生为正式比赛主环境；WSL2 仅作为可选 Linux 兼容层。**

Windows 原生负责：

- `uv` 管理的 Python 3.13 科学计算环境
- Git
- OpenCode / Claude Code / Codex / DSH 等 CLI Agent
- MATLAB R2024b
- Mathematica
- TeX Live / XeLaTeX / latexmk
- R 4.6.1
- WPS / Office、压缩工具与最终提交检查

macOS 作为灾备和独立编译/复核环境。

教师 `mathmodels` 已完成固定版本资格验证：

```text
mathmodels 0.0.13
RemoteSha = 13adbe0ac1716c4f07c841f45040010e71109540
AHP / ETS_FORECAST / STAT_INFER / MV_PCA = PASS
```

它是可选预装 R backend，不是自动数值真相来源。

## Agent 原则

Agent 不绑定单一厂商或额度。项目文件系统才是跨 Agent 的长期状态。

- **Sol + 人**：题意、模型路线、数学形式化、主张边界、G2/G3 科学裁定。
- **Codex / DeepSeek / OpenCode / Claude Code**：按明确范围执行实现、验证、审计和有限写作任务。
- **本地程序**：承担长 CPU 计算与确定性 verifier。
- **G1–G4**：人工门禁；Agent 无权代替参赛者写 `APPROVED: YES`。

接手前必须读：

- `AGENTS.md`
- `docs/context/PROJECT_STATE.md`
- `docs/context/DECISION_LOG.md`
- `docs/context/AGENT_HANDOFF.md`

## v0.4 证据治理

机器可读规则：`config/evidence_governance.yaml`。

正式报告不能只写无来源 `PASS`，应区分：

- `MACHINE_VERIFIED`
- `HUMAN_CONFIRMED`
- `SNAPSHOT_ONLY`
- `UNVERIFIED`

上游代码/结果/claim/最终文件发生实质变化时，依赖 gate 变为 `STALE`，不得沿用旧批准。

正式论文 writer 只从 approved evidence 取事实；Agent 自报、聊天记忆、未运行代码和失败候选不是正式数值来源。

## 论文质量链

```text
G3 冻结结果
  ↓
claim register / evidence bank
  ↓
论证与章节蓝图
  ↓
真实模型比选与求解过程
  ↓
初稿 + 图表 + 中间证据
  ↓
claim-preserving polish
  ↓
human-style / teacher-step review
  ↓
评委视角 PDF 人工通读
  ↓
G4 submission engineering
```

教师核心标准：

```text
动机 → 比选 → 建模/参数依据 → 求解/中间证据 → 验证 → 解读
```

不以固定页数替代论证完整性，也不把真正推理压进附录来“控制正文”。

## G4：exact-file human lock

见 `docs/G4_EXACT_FILE_LOCK.md`。

正式比赛最终 canonical artifacts：

```text
competition_paper.pdf
AI工具使用详情.pdf
supporting_material.zip
```

G4 前必须：

1. 参赛者连续通读最终候选；
2. 支撑 ZIP 在项目树外 fresh extract；
3. clean-room 运行/验证声明的可复现链；
4. 匿名、metadata、secret、路径、清单检查；
5. standalone AI PDF 与 ZIP 内副本 exact-byte identical；
6. 所有最后修改结束后再生成 MD5/SHA-256；
7. 参赛者明确 `APPROVED: YES`；
8. 将完全相同字节复制到唯一 `09_submission/`，锁后不再重编译/重压缩。

辅助脚本：

```powershell
python scripts\g4_bundle_audit.py --help
```

它验证提交工程，不证明数学正确。

## Drill-03 演练归档

完整记录：

`docs/context/DRILL03_ARCHIVE_20260910.md`

最终演练指纹：

```text
paper  SHA256 = 9AA4FAD7619F79F82BE2329AE53C483D6BFDB9D5ECC0EE50722D2A56BB1B4B3C
AI PDF SHA256 = D4D08DFEDE705A4BB6D6D77EEF5AD77F647215A919A01225A3BBD397FFA46E8D
support ZIP SHA256 = CFE13C34A1FEE713CF560EBA288EB535A13367CC87847AB4FC032132A8B2F6AB
```

演练支撑包 clean-room 8/8 命令通过、AI PDF exact-byte identity PASS、匿名/metadata/secret/path 检查通过。演练没有执行 participant human G4，`09_submission/` 保持空，这是有意的归档边界。

## 外部 skill / Agent 策略

完整审计：

- `docs/GITHUB_FINAL_MATHMODELING_STACK_AUDIT_20260909.md`
- `docs/ACADEMIC_SKILL_STACK_V04.md`
- `vendor/CANDIDATE_SKILLS_V04.yaml`
- `vendor/SKILLS_MANIFEST_V04.yaml`
- `config/skill_registry_v04.yaml`

最终取舍：

- Paper Workbench / MathModel-Skill / Remit / Anti-Autoresearch：蒸馏治理机制；
- MathModelAgent / sci-box / ARIS / Mrite / ModexAgent：reference-only 或局部参考；
- `cumcm-live-workflow-skill`：保持已测试 vendored runtime pin，只吸收不冲突的新策略；
- `meta-model-skills-max`：未找到可信公开匹配，不虚构；
- `ai-use-statement`：截图确认真实存在但来源未定位，可能私有/未索引/私下分发。MMKit 不接入未知运行时，仅保留“local trace → evidence → human-confirmed disclosure”设计，见 `docs/AI_TRACE_DISCLOSURE_RECOVERY.md`；
- 大型自治 research / one-shot paper generator 默认关闭。

比赛开始后 supply chain 冻结。

## 目录

```text
.
├── AGENTS.md
├── RUNBOOK.md
├── config/
├── docs/
├── prompts/
├── scripts/
├── templates/
├── tests/
├── examples/
└── vendor/
```

正式问题工作区的唯一最终提交目录：

```text
09_submission/
```

`FINAL/` 仅为旧兼容占位，不再保存第二份“最终稿”。

## 当前工作顺序

当前状态文件：

`docs/context/PRECONTEST_FREEZE_20260910.md`

现在：

```text
NO LOCAL ACTION
↓
等待官方 2026 赛题发布
↓
使用 prompts/CUMCM_2026_LIVE_START.md
↓
保存官方材料 + 新建正式 workspace
↓
从第一条 AI 交互开始真实留痕
↓
完成赛题/附件盘点
↓
G1 人工选题
```

正式比赛开始后不再做外部 GitHub / skill harvest。
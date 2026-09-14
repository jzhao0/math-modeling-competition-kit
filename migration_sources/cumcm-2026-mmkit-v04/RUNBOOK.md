# CUMCM 2026 Competition Day Runbook

> 本文件在赛前演练后封版。比赛当天只执行，不临时发明流程，不联网寻找新 skill/赛题实现。

## 0. 启动

1. 用 `scripts/new_problem.ps1` 创建新工作区。
2. 运行 `scripts/workspace_preflight.py`，确认目录、门禁、证据文件、配置快照和论文骨架存在。
3. 保存官方赛题和附件原文件，保留原始文件名与哈希，不覆盖。
4. 立即开始 `08_ai_logs/ai_calls.jsonl`；不要等论文完成后再回忆补日志。

## 1. G1 — 选题

对每道候选题独立形成：

- 题型；
- 数据结构与质量；
- 主要输出；
- 可验证性；
- 预计建模/编程/写作工作量；
- 主要失败风险。

三名队员人工完成 G1。

## 2. G2 — 模型路线

Sol + 队员主导。

### 2.1 重大歧义先处理

若一种题意解释会实质改变模型：

1. 至少列出两个合理解释；
2. 用最小例/边界检查；
3. 检查与后问递进性是否冲突；
4. 记录采用解释与拒绝理由；
5. 不能裁决则停在人工 gate，不由 Agent 静默选择。

### 2.2 候选模型真实 Pilot

每问至少一个可解释 baseline。

要写进论文的候选比较，应尽量满足：

- 同一训练/验证划分；
- 同一信息可见性；
- 同一主要评价指标；
- 真实执行；
- 失败候选记录失败原因。

复杂模型必须用真实样本外增益证明必要性，不为了“高级”选模型。

三名队员人工完成 G2。

## 3. G3 — 正式计算和结果冻结

1. 先 baseline，再主模型。
2. 所有正式数值必须来自真实运行并落盘。
3. 原始数据只读；转换/清洗通过脚本产生。
4. 记录随机种子、版本、命令、参数、输入 hash 和结果文件。
5. 每完成一问更新 `CLAIM_EVIDENCE.csv`、假设账本和决策记录。
6. 做与题目相适应的样本外误差、基线比较、灵敏度、稳健性、可行性、反事实或独立求解核验。
7. G3 报告标明证明力，不允许只有无来源的 `PASS`：
   - `MACHINE_VERIFIED`
   - `HUMAN_CONFIRMED`
   - `SNAPSHOT_ONLY`
   - `UNVERIFIED`
8. 任何上游关键 hash 变化后，依赖 gate 视为 `STALE`。

三名队员人工完成 G3。

## 4. G3 后论文生产

论文不是一键生成。

### 4.1 Argument pass

从批准证据建立 claim/evidence 和章节蓝图。每一问检查：

`动机 → 比选 → 建模/参数依据 → 求解过程 → 中间证据 → 验证 → 解读`。

不得为了固定页数删除真正推理，也不得用教材背景凑页。

### 4.2 Draft pass

正式 writer 只允许从：

- approved result tables；
- `CLAIM_EVIDENCE.csv`；
- verified citations；
- approved assumptions/definitions；
- selected figures + source data；
- verified program outputs

取事实。

聊天记忆、Agent 自报、未执行代码、失败候选不是数值真相来源。

### 4.3 Figure integration

- 图服务论证，不凑数量；
- 数值几何由源结果决定；
- 可用 Python/R/MATLAB/Origin/其他已冻结工具优化表现；
- 黑白打印可区分；
- 图/表首次出现前有引入，之后有解读；
- 评审实际 A4 页面，不只看单独 PNG/PDF。

### 4.4 Human-quality / teacher-step review

按教师 `cumcm-step-review` 和最新教师要求检查：

- 算法依据、步骤、参数、结果衔接；
- 模型比选是否真实；
- 中间结果是否足够；
- 公式与代码口径；
- 图文衔接；
- AI/工程内部话术；
- 防御式模板句；
- 机器浮点数；
- 结论强度与适用边界。

运行 `scripts/audit_human_paper.py` 后仍必须真人从第一页连续阅读最终 PDF。

## 5. AI 使用详情

1. 以当届官方/教师模板字段为唯一结构。
2. 由真实 AI 日志、可核验记录和队员确认填写。
3. 缺失的历史型号/时间/逐字交互不得补造；只说明一次“未完整留存”。
4. 代表性交互优先采用：
   `AI建议 → 团队采用/修改/拒绝 → 实际验证`。
5. 主论文 AI 声明保持简洁，但范围不要与详情矛盾。
6. 最终详情人工逐条确认。

详见 `docs/AI_DISCLOSURE_STYLE.md`。

## 6. 支撑材料从第一天维护

不要等 G4 才补。

支撑材料应包含当年规则/老师要求允许且必要的：

- 完整实际使用程序；
- 必要中间/结果表；
- 图源或最终图；
- AI 工具详情；
- README / 运行说明；
- 必要时 `RUN_MANIFEST.json`。

论文附录按教师最新要求放少量真实关键代码节选 + 支撑材料文件列表，不把完整代码库或中间大表塞进正文附录。

支撑代码不得保留 Agent handoff、内部 audit 状态、作者本机绝对路径、账号密钥等。

## 7. G4 — exact-file human lock

G4 不是“编译 PASS”。详细规则见 `docs/G4_EXACT_FILE_LOCK.md`。

### 7.1 最终 canonical artifacts

```text
competition_paper.pdf
AI工具使用详情.pdf
supporting_material.zip
```

### 7.2 Clean-room support test

把最终 ZIP 解压到项目树外的新空目录。

要求：

- 不回落到原项目绝对路径；
- README 写清软件、依赖、官方附件位置、运行顺序和命令；
- 声称“完整可运行”的程序必须有 clean-room 执行证据；
- 未随包提供的官方附件依赖必须明确说明；
- 匿名、metadata、secret、路径、ZIP traversal/duplicate 全部检查。

推荐运行：

```powershell
python scripts\g4_bundle_audit.py `
  --paper <competition_paper.pdf> `
  --ai <AI工具使用详情.pdf> `
  --support <supporting_material.zip> `
  --extract-dir <fresh-clean-room> `
  --json-out <audit.json>
```

若已检查 `RUN_MANIFEST.json`，再显式加入：

```text
--execute-manifest
```

### 7.3 AI PDF exact identity

ZIP 内 `AI工具使用详情.pdf` 必须直接复制 canonical standalone PDF：

```text
SHA256(standalone) == SHA256(zip-entry)
```

“看起来一样”不等于 exact-file lock。

### 7.4 最终 hash

**所有人工修改结束后**才生成 MD5/SHA-256。

任何一个 canonical artifact 字节改变：旧 G4 自动 `STALE`，重新检查、重新批准。

### 7.5 人工批准

三名队员完成最终检查；只有参赛者明确在 `human_gates/G4_submission.md` 写 `APPROVED: YES` 后才过 G4。

Agent 不能代写批准。

### 7.6 推广

G4 通过后，只把完全相同字节复制到唯一：

```text
09_submission/
```

复制后再次核对 hash。此后禁止重编译、重压缩或改字。

`FINAL/` 不再作为第二套最终目录。

## 8. R 执行纪律

- 正式 R 运行写入 `.R` 文件后以 `Rscript <file.R>` 执行；复杂多行逻辑不依赖 `Rscript -e`。
- 教师 `mathmodels 0.0.13` 已按 pin 预安装资格验证，只在适合的未来模型路线中使用；不得因为包存在而改写已冻结结果。
- 比赛期间不联网升级/安装外部 R 包，除非规则允许且队员明确批准非赛题解决方案依赖。

## 9. Agent 时间纪律

- 每个 Agent 任务必须有 Expected / Hard stop / Non-goals。
- 预算 70%–80% 时先落盘证据和剩余项；hard stop 到达必须停。
- objective/invariant mismatch 第一次超容差就保留冲突证据并停止，不在同一个 pass 边调试边重新设计。
- 长计算在本地确定性运行。
- 没有隔离上下文/独立实现时，不把角色扮演叫“独立审稿/独立复算”。

## 10. 外部 skill / Agent 冻结

赛前最后 harvest 记录在：

- `vendor/CANDIDATE_SKILLS_V04.yaml`
- `vendor/SKILLS_MANIFEST_V04.yaml`
- `config/skill_registry_v04.yaml`
- `docs/ACADEMIC_SKILL_STACK_V04.md`

比赛开始后：

- 不通过 GitHub/CSDN/知乎/社区搜索赛题、代码、讨论、他人方案；
- 不拉取新 skill；
- 不升级外部 pin；
- 不迁移到新的 Agent 平台；
- 使用本地冻结的 MMKit、教师材料和预装运行时。

外部项目只提供赛前蒸馏的机制，不是比赛时的在线依赖。

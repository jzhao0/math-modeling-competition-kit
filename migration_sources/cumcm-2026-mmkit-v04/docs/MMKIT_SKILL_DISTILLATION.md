# MMKit Skill Distillation Plan (v0.2 P1)

目标（Drill 3 之后执行）：把经过 Drill 1-3 验证的 MMKit 工作流蒸馏成可复用 Skill。
候选名：cumcm-mmkit-live-v1。

## 必须编码的内容

1. 人工门禁（G1-G4）：门禁点、审批状态机、APPROVED: YES 检查。
2. 模型归属（Model ownership）：SOL/人工裁决模型路线，Skill 不得越过。
3. 证据账本（Evidence ledger）：CLAIM_EVIDENCE、结果文件、输入哈希、依赖冻结。
4. 快速失败执行（Fail-fast）：先 baseline，再主模型；失败即回到上游修正。
5. R/Python 方法路由：config/method_router.yaml 的 use_when/avoid_when/crosscheck。
6. 文献验证：references/REFERENCE_LEDGER + scripts/reference_audit.py 工作流。
7. 科学图工作流：docs/FIGURE_PIPELINE.md（A/B/C 三类 + QA 清单）。
8. 论文质量审计：scripts/audit_paper_density.py + config/paper_quality.yaml（GUIDANCE 模式）。
9. AI 合规：ai_usage.jsonl 日志、AI工具使用声明、AI工具使用详情.pdf。
10. 最终提交 QA：终检清单、匿名性、页数/大小、关键数字追溯。

## 分阶段

- Phase 1（当前）：本计划 + 路由/审计/冻结基础设施就位（P1）。
- Phase 2（Drill 3）：在真实 Drill 3 中验证 R 验收与图/密度审计，采集证据。
- Phase 3（Drill 3 之后）：基于证据蒸馏 Skill 草案，人工评审后冻结。

## 纪律

- 不得在 Drill 3 提供证据之前生成最终 Skill：避免把未经实战的流程固化。
- Skill 只封装事实与门禁，不创造新的总控层级；不引入第二个 workflow 框架。
- 任何蒸馏内容必须对应真实运行记录，禁止凭记忆捏造流程。

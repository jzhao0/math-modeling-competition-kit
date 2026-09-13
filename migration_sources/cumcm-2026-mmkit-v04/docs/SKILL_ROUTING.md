# MMKit Skill Routing (v0.3)

用途：定义已登记外部 Skill / distilled policy / optional runtime 在 CUMCM 流程中的触发边界。
权威归属不变：Sol/人工对题意理解、模型路线、G2、G3、主张边界和最终科学裁决负责。外部项目提供局部能力，不拥有工作流。

## 路由总表

| 阶段/任务 | 路由 | 主执行 | 边界 |
| --- | --- | --- | --- |
| 文献深研 | Supervisor deep-research + nature search + GDM/OpenAlex | Sol/人工定题 | 不得联网搜现场赛题解法；元数据仍需验证 |
| 元数据核验 | OpenAlex/Crossref/出版方 | 脚本 + 人工 | 禁止虚构 DOI/页码；搜索摘要不是最终证据 |
| 统计口径 | nature-statistics + Python/R | Sol + 真实运行 | Skill 文本不能替代计算结果 |
| 模型路线 | Sol | Sol | 所有 skill 均不得覆盖 G2 |
| 论证架构 | PaperSpine distilled policy + claim register/evidence bank | Sol + bounded writer | 冻结结果后才进入；不得按项目开发时间线写论文 |
| 初稿 | evidence pack + section blueprint + bounded writer | 人工 + writer | 不得重新发明数值、模型、范围或引用 |
| Claim-preserving polish | Horizon distilled policy + Supervisor polish | bounded writer + 人工 | 数字/公式/引用/模态/范围锁定 |
| Human-style review | humanize-paper distilled rules + `audit_human_paper.py` + SCI-polish reference | 人工 | 不是 AI 检测规避；不能为了自然改科学意义 |
| 数值证据图 | Python/R/可选 Origin | 数据脚本/Origin + 人工 QA | 数值来自冻结结果 |
| 展示型图 | Origin/Python/R + contest visual policy | 绘图执行器 + 人工 | 允许 PRESENTATION_3D；装饰深度不得冒充量轴 |
| 结构/状态图 | Draw.io/SVG/figure-designer/PaperBanana 草稿 | 人工科学 QA | 变量、箭头、方向和公式必须一致 |
| Figure contract | Nature-figure distilled policy + `FIGURE_PLAN.md` | Sol/人工 | claim/页面作用、源数据、编码、backend、展示层都要记录 |
| Submission artifacts | CUMCM workflow + academic-research-skills distilled package/manage patterns | 人工 + bounded finalizer | `09_submission/` 唯一 final dir；官方规则优先 |
| 最终科学审阅 | Sol + reviewer skills | Sol/队伍 | reviewer 给建议，不自动改 frozen math |
| 最终成品审阅 | `PAPER_HUMAN_REVIEW.md` + 真人逐页 PDF | 队伍 | 自动 geometry/AIGC/查重不能替代 |
| OpenScience / 大型 SCI pipeline | reference only | disabled by default | 不启用长自治研究/多 Agent 讨论链 |

## v0.3 外部来源模式

- `VENDORED_SKILL`：v0.2 已冻结的可用 skill。
- `DISTILLED_POLICY`：只吸收规则并写成本仓库原生策略/脚本，不依赖上游 runtime。
- `REFERENCE_ONLY`：只参考，不复制、不执行、不作为比赛时依赖。
- `OPTIONAL_RUNTIME`：可选本地后端；必须赛前安装/测试，并有 fallback。

精确 pin/license/mode 见 `vendor/SKILLS_MANIFEST.yaml`。

## 写作触发条件

1. G3 未完成、关键数字未冻结时，禁止全文写作/润色进入“成稿”状态。
2. 先完成 `CLAIM_REGISTER.md` + `PAPER_PLAN.md`，再生成完整正文。
3. 润色默认 claim lock；任何会改变否定、模态、适用范围、公式、数值、引用身份的修改必须回到 Sol。
4. `audit_human_paper.py` 只是风险定位器，不判定 AI 概率，也不代替人工阅读。
5. 论文必须删除内部 Agent/audit/pipeline/handoff 叙述，只保留科学上必要的方法/验证信息。

## 绘图触发条件

1. 数值真相来自冻结数据，renderer 不能成为真值源。
2. CUMCM 允许“为了好看而好看”的展示层。`PRESENTATION_3D` 可用于 3D 柱、立体折线/带状图、空间构图；不需要硬造第三变量。
3. 装饰深度不显示虚假量轴；值接近时配直接标签或邻近表格。
4. 双参数/敏感性/响应面优先考虑真正 DATA_3D surface/mesh/contour。
5. Origin MCP 是 `OPTIONAL_RUNTIME`。未在实际 Windows 赛机完成 doctor/smoke 前，不允许把它设为单点依赖。
6. 图必须就近服务于正文论证，禁止把所有图集中到后面满足“密度”。

## 明确不得做的事

- 所有写作/figure skills：不得改变冻结数学结论或发明结果。
- SCI-Skills：无明确 license，保持 REFERENCE_ONLY。
- SCI-polish：license/套件体量不适合作为 vendored 主流程，保持 REFERENCE_ONLY；38-agent 类自治编排禁用。
- OpenScience：只参考 local-first/provenance/skill-catalog 架构，不接管比赛流程。
- qcmuu AI-Research-Skills：只参考 selected plotting/writing ideas，不启用 99-skill lifecycle。
- humanize-paper：不得用于 detector gaming；只做 reader/writing quality。
- Nature figure：其 figure-contract/QA 原则可吸收，但不得强行用期刊极简主义覆盖 CUMCM 展示目标。
- Origin MCP：不得从图形反推/修改模型结果；不得在比赛开始后首次联网安装。

## 证据与门禁

- 所有正式结果/图表必须能追溯到冻结结果或验证模型。
- G2/G3/G4 `APPROVED: YES` 必须由队伍完成，Skill 输出不能替代审批。
- 比赛期间只使用赛前已冻结的材料、本地 distilled policy 和已验证 runtime；不联网抓新 skill。

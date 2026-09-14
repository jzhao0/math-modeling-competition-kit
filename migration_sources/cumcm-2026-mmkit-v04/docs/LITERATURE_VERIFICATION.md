# Literature Verification System (MMKit v0.2 P0)

目标：论文中的每一篇引用都必须真实、可核对、支撑具体主张。不虚构 DOI，不填占位引用。

## 数据源

- Ledger（唯一事实源）：references/REFERENCE_LEDGER.csv
- BibTeX（验证后生成，供论文使用）：references/references.bib（仅收录通过验证的条目）
- 主张登记：CLAIM_EVIDENCE.csv 的 used_in_claims 字段

## 工作流

1. 发现 (discovery)：仅允许可信来源（出版社官网、作者主页、OpenAlex/Crossref API、已核验教材/官方文档）。竞赛期间不得在 GitHub 等平台检索赛题相关内容（见 AGENTS.md 网络纪律）。
2. 元数据验证 (metadata validation)：通过 OpenAlex（api.openalex.org）与 Crossref（api.crossref.org/works/DOI）比对标题、作者、年份、venue。两源一致才可 metadata_verified = TRUE。
3. DOI/出版社验证 (publisher verification)：
   - doi 字段必须是可解析的 DOI：https://doi.org/<doi> 能 302 到出版社页面；Crossref API 返回该 DOI 记录。
   - 无 DOI 的出版物：url 必须直接命中出版社/作者官方页面，且 publisher_verified = TRUE 仅在人工点击确认后填写。
   - 禁止：编造 DOI、把搜索结果标题当作 DOI、把 URL 填进 doi 字段。
4. BibTeX：验证通过条目才写 references/references.bib；BibTeX 的 title/author/year/doi 必须与 Ledger 一致。
5. 主张链接 (CLAIM_EVIDENCE linkage)：
   - 论文每处引用必须支撑一个具体主张；used_in_claims 填写主张 ID 或对应证据行 ID。
   - 引用不支撑任何具体主张时，不得出现在最终论文中（used_in_claims 为空 = 未使用）。

## 字段语义

| 字段 | 说明 |
| --- | --- |
| key | 稳定引用键（如 author2020method） |
| title / authors / year / venue | 从验证源取得，非 AI 记忆 |
| doi / url | 二者至少一个且可解析；doi 禁止虚构 |
| discovered_via | 发现途径（API/官网/教材/期刊库） |
| metadata_verified | TRUE/FALSE：OpenAlex+Crossref 双源一致 |
| publisher_verified | TRUE/FALSE：人工确认出版社页面可访问 |
| relevance | 支持的具体主题/方法，一句话 |
| used_in_claims | CLAIM_EVIDENCE 主张 ID 列表（分号分隔）；空 = 未使用 |
| notes | 验证过程/版本/复核备注 |

## 规则

1. 不得虚构 DOI：任何 DOI 必须先经 Crossref 解析确认，doi 字段禁止猜测。
2. 不得使用主题占位引用：最终论文禁止 [待补]/[?]/（占位）类引用；无可用真实引用时，宁可少引用，不引用。
3. 引用必须支撑真实主张：每条引用在论文中必须有具体用途（方法依据/数据来源/对比基线/限制说明）。
4. 高度相似的竞赛获奖论文不属于主要方法学证据：它们可作为写作/结构参考，但不得作为方法正确性、数值或结论的主要依据；如需引用需在 notes 标注“仅写作参考”。
5. 验证是双向的：metadata_verified 与 publisher_verified 均为 TRUE 的条目才进入 references.bib 并允许出现在最终论文中。
6. Ledger 只追加修正，不静默删除；错误条目以 notes 标注废弃。

## 验证命令示例（赛前预验证/赛后复核）

```powershell
Invoke-RestMethod https://api.crossref.org/works/<DOI>
Invoke-RestMethod "https://api.openalex.org/works/https://doi.org/<DOI>"
```

> 注意：竞赛期间（2026-09-10 后）按规则不进行赛题相关联网检索；本系统在赛前完成参考资料的冻结与验证。

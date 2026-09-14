# References (MMKit v0.2 P1)

参考文献唯一事实源：REFERENCE_LEDGER.csv。工作流：

DISCOVERY -> METADATA VALIDATION -> DOI/PUBLISHER VALIDATION -> CLAIM LINKAGE -> BIBTEX -> PAPER

## 状态区分（重要）

| 状态 | 含义 | 允许进入论文？ |
| --- | --- | --- |
| discovered | 仅被检索发现，未验证 | 否 |
| metadata_verified | OpenAlex+Crossref 双源元数据一致 | 否 |
| publisher_verified | DOI/出版社页面人工确认可访问且记录匹配 | 是（需 claim_verified） |
| claim_verified | 有具体 claim 链接 (used_in_claims 非空) | 是 |

## 来源路由

- SciSpace：仅 discovery/relevance assistance（不付费依赖；无 API 真理地位）。
- OpenAlex：广泛文献 + 元数据发现（离线：仅用赛前冻结的 JSON 缓存）。
- Crossref：DOI 元数据验证（输入必须为真实 DOI）。
- 出版社/DOI landing page：最终文献学验证（标题/作者/年/卷/页）。
- Google Scholar：可选发现；仅在竞赛网络规则允许时使用。
- 高度相似 CUMCM 赛后论文：不得作为主要方法学证据（可作背景，需在 notes 标注）。

## 工具

powershell 执行：.venv\Scripts\python.exe scripts\reference_audit.py（可加 -j reports\ref_audit.json）

竞赛期间：遵守 MMKit 竞赛网络纪律（AGENTS.md 第 6 节）；不联网搜赛题相关内容。

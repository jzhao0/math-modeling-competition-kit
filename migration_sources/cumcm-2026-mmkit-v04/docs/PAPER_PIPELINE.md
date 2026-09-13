# CUMCM Paper Quality Gate

本质量门把论文检查固化为可重复执行的合同。它只发现问题、生成报告，不替作者改写论文，也不改变模型、数值或图表结论。

## 职责边界

- Sol / 人工作者负责研究判断、最终数值确认、论证取舍与措辞。
- DSH / Codex 等执行器负责按已确认合同实现确定性检查。
- Linter 负责定位可能的问题；不得自动重写论文正文。
- 任一 AI 都不得绕过 `paper_facts.yaml` 改写已经冻结的结果。事实变更必须先由人工确认，再修改 single source of truth，最后同步正文。

## 一条命令

从本仓库运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Workspace D:\path\to\problem-workspace
```

默认入口为 `<Workspace>\06_paper\main.tex`。候选稿不是 `main.tex` 时必须显式指定，报告和终端都会打印最终解析后的绝对路径：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 `
  -Workspace D:\path\to\problem-workspace `
  -MainTex 06_paper\paper_v5_sol_revised.tex
```

需要同时生成确定性的 Sol 中央审稿材料时，增加 `-BuildSolReviewPacket`：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 `
  -Workspace D:\Projects\CUMCM-DRILL-01 `
  -MainTex 06_paper\paper_v5_sol_revised.tex `
  -BuildSolReviewPacket
```

该开关把当前明确选定的 source graph、Gate findings、frozen facts、章节、
图、表、编号公式、结论、AI 声明及参考文献元数据收集到
`<Workspace>\reports\sol_review_packet.md`，并生成 JSON companion。
Packet 是 deterministic review material，不是新 Gate；它不调用 LLM，
不重写正文，不改变 frozen facts，也不判断科学质量。即使 Gate 为
`FAIL`，仍会生成 Packet。若编译 PDF 不存在，source-only Packet 会明确
记录 `PAPER_PDF_UNAVAILABLE`，PDF-only 定位统一写 `UNKNOWN`，不做猜测。

最终 PDF 为 `<Workspace>\09_submission\paper.pdf`，报告为：

- `<Workspace>\reports\paper_gate.json`
- `<Workspace>\reports\paper_gate.md`

如某题有独立事实配置，可显式传入，不要复制后静默分叉：

```powershell
.\scripts\build_paper.ps1 `
  -Workspace D:\path\to\problem-workspace `
  -FactsConfig D:\path\to\problem-workspace\config\paper_facts.yaml
```

## 执行顺序与状态

Gate 固定执行：PRECHECK → XeLaTeX 两遍 → `pdfinfo` → `pdftotext` / `pdftotext -bbox` → facts → structure → language → 可选外部 linter → layout → 汇总报告。

最终状态只有：

- `PASS`：无 ERROR、无 WARNING。
- `PASS_WITH_WARNINGS`：无 ERROR，但存在 WARNING。
- `FAIL`：至少一个 ERROR。

脚本在 `FAIL` 时返回退出码 1，其余状态返回 0。JSON 是机器接口，Markdown 供人工审阅。

## 配置合同

四份 `.yaml` 使用 JSON-compatible YAML（JSON 是 YAML 1.2 的严格子集），因此 Windows 基线不依赖全局 PyYAML：

- `config/paper_facts.yaml`：只写最终决策数字。每项至少包含 `fact_id`、`canonical_value`、`allowed_renderings`、`required`、`description`；可增加 `forbidden_values`、`wrong_roundings`、`conflicting_renderings` 和 `context_pattern`。
- `config/paper_sections.yaml`：硬检查 section、逐问 subsection、最低正文长度和明确 frozen forbidden patterns；背景矛盾、数据特点、任务/难点/方案等语义动作只生成 `SECTION_MANUAL_REVIEW` WARNING。
- `config/paper_language_rules.yaml`：定义 ERROR / WARNING 词项和密度阈值。检查只报告，不改写。
- `config/figure_contracts.yaml`：定义空白页、孤标题、异常留白、图表编号与 LaTeX 图引用合同。

仓库级 `paper_facts.yaml` 初始为空，因为赛前框架不能虚构某道题的最终数值。每次演练或正式比赛应在人工冻结结果后填入，或通过 `-FactsConfig` 指向该题唯一的受控配置。

示例事实：

```yaml
{
  "facts": [
    {
      "fact_id": "recommended_count",
      "canonical_value": "19",
      "allowed_renderings": ["19", "19 个"],
      "forbidden_values": ["18"],
      "wrong_roundings": ["20"],
      "required": true,
      "description": "人工确认的最终推荐数量"
    }
  ]
}
```

## 外部工具复用

必需基线：Python、XeLaTeX、`pdfinfo`、`pdftotext`。可选工具在运行时逐个探测：

- zhlint：对编译后的纯文本做中文标点与空格检查。
- Vale：加载 `styles/cumcm/` 的 CUMCM prose rules；不使用自动修复。
- TeXtidote：对 LaTeX 源做 sanity 检查。
- latexindent：只生成临时格式化版本并比较哈希，从不覆盖 `main.tex`。

未安装的可选工具在报告中显示 `OPTIONAL_MISSING` 与安装建议，不阻塞主 Gate，也不会被脚本自动安装。

## 确定性检查范围

- LaTeX 日志：undefined reference、undefined citation、overfull hbox、missing character。
- Facts：必需事实缺失、显式禁止值、错误取整和矛盾 rendering。
- Sections：同级 section、section*、bibliography、appendix 与文档末尾边界；subsection 不终止父 section。结论数值不再做全量前文比对，冻结结果由 facts checker 负责。
- Language：内部执行术语、模板套话、括号/破折号密度、连续起句、连接词连用、长段、长句和机械三段式；长度检查排除参考文献、caption、table、equation 和 code/listings。
- Layout：空白页、页底 section/subsection 孤标题、页顶/页底图题风险、异常留白、图表编号、LaTeX 图片 label 与正文 `ref`/`autoref`/`cref`、PDF 页数。源码模式只从真实 table/figure environment 判断；PDF fallback 只逐行识别明确图题/表题。

## 当前边界

- `pdftotext -bbox` 不提供可靠的位图几何边界，因此图像与图题是否真正跨页只能用图题页边缘位置作 WARNING，最终仍需人工看 PDF。
- 字体视觉一致性、公式美观、图内文字可读性、颜色和打印效果不由文本/bbox Gate 判断。
- 跨多个 `\input` / `\include` 文件的检查从实际 `MainTex` 沿依赖图收集源码，不再盲目合并同目录的旧稿或模板。宏动态生成的 label/ref 无法静态确定时只报 WARNING。
- section 合同基于编译后标题文本；高度定制或纯图片标题需要在配置中补充可识别 heading。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试覆盖每个 checker，并固定以下回归行为：`本文需要回答四个问题` 为 ERROR，`这些结构直接决定了` 为 WARNING，`G3 FINAL PASS` 为 ERROR，16/17/19 通过、18 替代 19 失败，以及页底无正文标题为 orphan ERROR。

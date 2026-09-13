from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_sol_review_packet import PDF_UNAVAILABLE, build_packet, render_markdown  # noqa: E402


class SolReviewPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sol-packet-test-")
        self.workspace = Path(self.temporary.name)
        paper_dir = self.workspace / "06_paper"
        reports = self.workspace / "reports"
        config = self.workspace / "config"
        figures = paper_dir / "figures"
        for path in (paper_dir, reports, config, figures):
            path.mkdir(parents=True, exist_ok=True)
        (figures / "current.png").write_bytes(b"fixture")
        self.main_tex = paper_dir / "candidate.tex"
        self.old_tex = paper_dir / "main.tex"
        self.pdf = paper_dir / "candidate.pdf"
        self.gate_json = reports / "paper_gate.json"
        self.gate_md = reports / "paper_gate.md"
        self.facts = config / "paper_facts.yaml"
        self.sections_config = config / "paper_sections.yaml"
        self.main_tex.write_text(
            r"""\documentclass{article}
\begin{document}
\begin{center}\bfseries 摘要\end{center}
这是当前候选稿摘要，保留数字 19 和术语 AFT。

关键词：测试
\section{问题重述}
当前候选稿唯一标记 CURRENT_ONLY。
\section{问题分析}
\subsection{第一问}
第一问正文内容足够明确。
\subsection{第二问}
第二问正文内容足够明确。
\section{结果}
正文引用图\ref{fig:current}与缺失图\cref{fig:missing}，并引用表\autoref{tab:values}。
\begin{figure}
\includegraphics{figures/current.png}
\caption{当前候选图}
\label{fig:current}
\end{figure}
\begin{figure}
\includegraphics{figures/missing.png}
\caption{缺失源图}
\label{fig:missing}
\end{figure}
\begin{table}
\caption{关键数值}
\label{tab:values}
\begin{tabular}{cc}
组别 & 数值 \\
Q1 & 19 \\
\end{tabular}
\end{table}
\begin{equation}
y = 19x
\end{equation}
\section{结论与建议}
结论只包含当前结果 19，并在下一标题处确定结束。
\section*{AI 工具使用声明}
本队使用 AI 工具辅助代码检查，最终科学判断由作者完成。
\begin{thebibliography}{9}
\bibitem{ref:a} BIB_ONLY Author. Title. 2020. doi:10.2307/example.
\bibitem{ref:b} Second reference.
\end{thebibliography}
\end{document}
""",
            encoding="utf-8",
        )
        self.old_tex.write_text("OLD_DRAFT_SENTINEL", encoding="utf-8")
        self.pdf.write_bytes(b"%PDF fixture")
        self.facts.write_text(json.dumps({
            "schema_version": 1,
            "facts": [{
                "fact_id": "result_q1_final", "canonical_value": 19,
                "allowed_renderings": ["19", "19.0"], "required": True,
                "description": "原样冻结结果",
            }],
        }, ensure_ascii=False), encoding="utf-8")
        self.sections_config.write_text(json.dumps({"schema_version": 1, "sections": []}), encoding="utf-8")
        gate = {
            "status": "FAIL", "errors": 1, "warnings": 4,
            "main_tex": str(self.main_tex), "pdf": str(self.pdf),
            "checker_reports": [{"checker": "paper_layout", "page_count": 12}],
            "findings": [
                {"level": "ERROR", "code": "TEST_ERROR", "message": "real error", "location": "page:2"},
                {"level": "WARNING", "code": "SECTION_MANUAL_REVIEW", "message": "review section", "location": "q1"},
                {"level": "WARNING", "code": "FIGURE_CAPTION_AT_PAGE_BOTTOM", "message": "inspect caption", "location": "page:3"},
                {"level": "WARNING", "code": "FIGURE_DYNAMIC_MACRO", "message": "inspect macro", "location": "figure:3"},
                {"level": "WARNING", "code": "CONSECUTIVE_CONNECTOR_SENTENCES", "message": "inspect prose", "location": "sentence:4"},
            ],
        }
        self.gate_json.write_text(json.dumps(gate, ensure_ascii=False), encoding="utf-8")
        self.gate_md.write_text("# gate\n", encoding="utf-8")
        self.packet = self._build()
        self.markdown = render_markdown(self.packet)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _build(self, *, pdf: Path | None = None):
        return build_packet(
            workspace=self.workspace.resolve(), main_tex=self.main_tex.resolve(),
            paper_pdf=(pdf or self.pdf).resolve(), gate_json=self.gate_json.resolve(),
            gate_md=self.gate_md.resolve(), facts_config=self.facts.resolve(),
            sections_config=self.sections_config.resolve(),
        )

    def test_01_only_selected_main_tex_is_read(self) -> None:
        self.assertEqual(self.packet["metadata"]["main_tex"], str(self.main_tex.resolve()))
        self.assertIn("CURRENT_ONLY", self.markdown)

    def test_02_section_extraction_is_bounded_and_ordered(self) -> None:
        titles = [item["title"] for item in self.packet["sections"]]
        self.assertEqual(titles[:4], ["问题重述", "问题分析", "第一问", "第二问"])
        self.assertIn("结论与建议", titles)

    def test_03_bibliography_is_not_in_conclusion(self) -> None:
        self.assertIn("当前结果 19", self.packet["conclusion"])
        self.assertNotIn("BIB_ONLY", self.packet["conclusion"])

    def test_04_frozen_facts_are_rendered_without_value_changes(self) -> None:
        self.assertIn('"canonical_value": 19', self.markdown)
        self.assertIn('"allowed_renderings": [', self.markdown)
        self.assertEqual(self.packet["frozen_facts"][0]["description"], "原样冻结结果")

    def test_05_gate_errors_and_warnings_are_copied(self) -> None:
        self.assertIn("TEST_ERROR", self.markdown)
        self.assertIn("CONSECUTIVE_CONNECTOR_SENTENCES", self.markdown)
        self.assertEqual(len(self.packet["gate"]["errors"]), 1)
        self.assertEqual(len(self.packet["gate"]["warnings"]), 4)

    def test_06_figure_labels_and_references_are_related(self) -> None:
        current = self.packet["figures"][0]
        self.assertEqual(current["label"], "fig:current")
        self.assertTrue(current["referenced"])
        self.assertIsNotNone(current["first_reference"])

    def test_07_table_content_label_and_reference_are_extracted(self) -> None:
        table = self.packet["tables"][0]
        self.assertEqual(table["label"], "tab:values")
        self.assertTrue(table["referenced"])
        self.assertIn("| Q1 | 19 |", table["content_markdown"])

    def test_08_missing_figure_source_is_marked_missing(self) -> None:
        missing = self.packet["figures"][1]
        self.assertEqual(missing["source_status"], "MISSING")
        self.assertIn("MISSING", self.markdown)

    def test_09_figure_page_is_unknown_not_guessed(self) -> None:
        self.assertTrue(all(item["page"] == "UNKNOWN" for item in self.packet["figures"]))

    def test_10_source_only_packet_is_generated(self) -> None:
        absent = self.workspace / "no-paper.pdf"
        packet = self._build(pdf=absent)
        rendered = render_markdown(packet)
        self.assertEqual(packet["metadata"]["paper_pdf_status"], PDF_UNAVAILABLE)
        self.assertEqual(packet["metadata"]["paper_page_count"], "UNKNOWN")
        self.assertIn("CURRENT_ONLY", rendered)

    def test_11_old_main_tex_content_is_absent(self) -> None:
        self.assertNotIn("OLD_DRAFT_SENTINEL", self.markdown)

    def test_12_build_does_not_modify_input_files(self) -> None:
        paths = [self.main_tex, self.old_tex, self.gate_json, self.gate_md, self.facts, self.sections_config]
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        self._build()
        after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        self.assertEqual(before, after)

    def test_13_ai_declaration_is_extracted(self) -> None:
        self.assertIn("最终科学判断由作者完成", self.packet["ai_declaration"])
        self.assertIn("## 12. AI Declaration", self.markdown)

    def test_14_references_are_counted_with_doi(self) -> None:
        self.assertEqual(len(self.packet["references"]), 2)
        self.assertEqual(self.packet["references"][0]["dois"], ["10.2307/example"])
        self.assertIn("reference count: 2", self.markdown)

    def test_15_manual_review_queue_uses_fixed_mapping(self) -> None:
        priorities = {item["source"]: item["priority"] for item in self.packet["manual_review_queue"]}
        self.assertEqual(priorities["SECTION_MANUAL_REVIEW"], "HIGH")
        self.assertEqual(priorities["FIGURE_CAPTION_AT_PAGE_BOTTOM"], "MEDIUM")
        self.assertEqual(priorities["FIGURE_DYNAMIC_MACRO"], "MEDIUM")
        self.assertEqual(priorities["CONSECUTIVE_CONNECTOR_SENTENCES"], "LOW")


if __name__ == "__main__":
    unittest.main()

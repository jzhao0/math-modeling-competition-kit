from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_paper_intelligence import build_intelligence, render_markdown  # noqa: E402


class PaperIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="paper-intelligence-")
        self.root = Path(self.tmp.name)
        self.tex = self.root / "paper.tex"
        self.facts = self.root / "facts.yaml"
        self.tex.write_text(
            r"""\documentclass{article}
\begin{document}
\section{问题分析}
\subsection{男胎浓度变化}
同一孕妇存在重复测量。
\subsection{BMI 分组与检测时点}
达标时间存在删失。
\subsection{多因素情况下的检测时点}
BMI 与身高体重存在结构相关。
\subsection{女胎异常判定}
异常判定需要孕妇级验证。
\section{第一问模型与结果}
模型建立后，由图\ref{fig:q1}可知最优值达到19.5%。
另一方案结果为8。
\subsection{敏感性分析}
参数提高10%后结果保持稳定。
\section{第二问求解}
比较结果见表\ref{tab:q2}。方案一最优值为42。
方案二最优值为43。
方案三最优值为44。
方案四最优值为45。
方案五最优值为46。
\section{结论与建议}
因此建议采用第一问方案。
\end{document}
""",
            encoding="utf-8",
        )
        self.facts.write_text(json.dumps({
            "facts": [{"fact_id": "result_q1", "question": "Q1", "canonical_value": 19.5, "allowed_renderings": ["19.5%"]}]
        }, ensure_ascii=False), encoding="utf-8")
        self.report = build_intelligence(self.tex, self.facts)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_q1_and_q2_are_mapped(self) -> None:
        questions = {item["title"]: item["question"] for item in self.report["section_index"]}
        self.assertEqual(questions["第一问模型与结果"], "Q1")
        self.assertEqual(questions["第二问求解"], "Q2")

    def test_problem_analysis_subsections_map_to_q1_q4(self) -> None:
        questions = {item["number"]: item["question"] for item in self.report["section_index"] if item["level"] == 2}
        self.assertEqual(questions["1.1"], "Q1")
        self.assertEqual(questions["1.2"], "Q2")
        self.assertEqual(questions["1.3"], "Q3")
        self.assertEqual(questions["1.4"], "Q4")

    def test_semantic_roles_are_extracted(self) -> None:
        q1 = next(item for item in self.report["section_index"] if item["title"] == "第一问模型与结果")
        self.assertIn("MODEL", q1["roles"])
        self.assertIn("RESULTS", q1["roles"])

    def test_explicit_reference_is_traceable(self) -> None:
        claim = next(item for item in self.report["claims"] if "19.5" in item["text"])
        self.assertEqual(claim["evidence_status"], "TRACEABLE_REFERENCE")
        self.assertEqual(claim["references"], ["fig:q1"])

    def test_previous_sentence_reference_is_local_context(self) -> None:
        claim = next(item for item in self.report["claims"] if "42" in item["text"])
        self.assertEqual(claim["evidence_status"], "TRACEABLE_LOCAL_CONTEXT")
        self.assertEqual(claim["references"], ["tab:q2"])

    def test_frozen_fact_hit_is_preserved(self) -> None:
        claim = next(item for item in self.report["claims"] if "19.5" in item["text"])
        self.assertEqual(claim["frozen_fact_hits"], ["result_q1"])

    def test_frozen_fact_does_not_create_manual_work(self) -> None:
        self.assertFalse(any("19.5" in item["claim"] for item in self.report["manual_review_queue"]))

    def test_manual_queue_is_bounded_per_question(self) -> None:
        q2_items = [item for item in self.report["manual_review_queue"] if item.get("question_id") == "Q2"]
        self.assertLessEqual(len(q2_items), 4)

    def test_question_coverage_has_review_claim_counts(self) -> None:
        self.assertGreaterEqual(self.report["question_coverage"]["Q1"]["claim_count"], 2)
        self.assertLessEqual(self.report["question_coverage"]["Q2"]["review_claim_count"], 8)

    def test_conclusion_is_global_not_q2(self) -> None:
        conclusion = next(item for item in self.report["section_index"] if item["title"] == "结论与建议")
        self.assertEqual(conclusion["question"], "GLOBAL")

    def test_markdown_marks_triage_as_informational(self) -> None:
        text = render_markdown(self.report)
        self.assertIn("informational triage", text)
        self.assertIn("Bounded Manual Review Queue", text)
        self.assertIn("TRACEABLE_REFERENCE", text)


if __name__ == "__main__":
    unittest.main()

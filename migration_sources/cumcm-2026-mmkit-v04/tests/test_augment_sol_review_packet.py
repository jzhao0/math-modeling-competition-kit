from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from augment_sol_review_packet import augment_packet, render_augmented_markdown  # noqa: E402


class AugmentSolReviewPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = {
            "metadata": {key: "x" for key in ("generated_at", "workspace", "main_tex", "paper_pdf", "paper_pdf_status", "gate_json", "gate_md", "facts_config", "sections_config", "git_commit", "paper_page_count", "gate_status", "error_count", "warning_count")},
            "gate": {"errors": [], "warnings": []}, "frozen_facts": [], "sections": [],
            "abstract": "a", "figures": [], "tables": [], "equations": [],
            "claims": {"Q1": "NOT DETERMINISTICALLY EXTRACTABLE", "Q2": "x", "Q3": "x", "Q4": "x", "final_conclusion": "c"},
            "conclusion": "c", "ai_declaration": "ai", "references": [], "manual_review_queue": [],
        }
        self.intelligence = {
            "section_index": [{"number": "3.1", "title": "第一问", "question": "Q1", "roles": ["RESULTS"], "source_file": "paper.tex", "source_line": 10, "source_end_line": 20}],
            "review_claims_by_question": {"Q1": [{"evidence_status": "TRACEABLE_REFERENCE", "text": "最优值为19", "numbers": ["19"], "references": ["tab:q1"], "frozen_fact_hits": [], "section": "第一问"}]},
            "manual_review_queue": [{"priority": "MEDIUM", "source": "CLAIM_EVIDENCE_TRIAGE", "location": "paper.tex:10#1", "question": "verify"}],
        }
        self.visual = {
            "page_count": 10,
            "warning_count": 2,
            "render": {"status": "OK"},
            "pages": [
                {"page": 2, "word_count": 100, "line_count": 20, "image_count": 1, "flags": ["SMALL_RENDERED_IMAGE"]},
                {"page": 3, "word_count": 100, "line_count": 20, "image_count": 1, "flags": ["SMALL_RENDERED_IMAGE"]},
            ],
            "findings": [
                {"code": "SMALL_RENDERED_IMAGE", "page": 2, "location": "page:2", "message": "inspect"},
                {"code": "SMALL_RENDERED_IMAGE", "page": 3, "location": "page:3", "message": "inspect"},
            ],
        }
        self.augmented = augment_packet(self.packet, self.intelligence, self.visual)

    def test_q1_claim_is_replaced_from_review_claims(self) -> None:
        self.assertIn("最优值为19", self.augmented["claims"]["Q1"])

    def test_manual_queues_are_merged(self) -> None:
        sources = [item["source"] for item in self.augmented["manual_review_queue"]]
        self.assertIn("CLAIM_EVIDENCE_TRIAGE", sources)
        self.assertIn("SMALL_RENDERED_IMAGE", sources)

    def test_visual_findings_are_grouped_by_code(self) -> None:
        items = [item for item in self.augmented["manual_review_queue"] if item["source"] == "SMALL_RENDERED_IMAGE"]
        self.assertEqual(len(items), 1)
        self.assertIn("page:2", items[0]["location"])
        self.assertIn("page:3", items[0]["location"])

    def test_section_index_is_embedded_in_markdown(self) -> None:
        text = render_augmented_markdown(self.augmented)
        self.assertIn("Deterministic Section / Question Index", text)
        self.assertIn("第一问", text)

    def test_visual_summary_is_embedded_in_markdown(self) -> None:
        text = render_augmented_markdown(self.augmented)
        self.assertIn("PDF Visual Review Summary", text)
        self.assertIn("SMALL_RENDERED_IMAGE", text)


if __name__ == "__main__":
    unittest.main()

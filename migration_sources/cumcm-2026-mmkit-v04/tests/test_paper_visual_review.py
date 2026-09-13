from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from paper_visual_review import analyze_pages, extract_pages, render_markdown  # noqa: E402


BBOX = """<doc><page width="600" height="800">
<word xMin="1" yMin="100" xMax="40" yMax="112">Edge</word>
</page>
<page width="600" height="800">
<word xMin="100" yMin="100" xMax="130" yMax="112">Sparse</word>
</page>
<page width="600" height="800">
<word xMin="100" yMin="100" xMax="140" yMax="112">Image</word>
<image xMin="100" yMin="200" xMax="180" yMax="250" />
</page></doc>"""


class PaperVisualReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="paper-visual-")
        self.path = Path(self.tmp.name) / "paper.bbox.html"
        self.path.write_text(BBOX, encoding="utf-8")
        self.report = analyze_pages(extract_pages(self.path))
        self.report["render"] = {"status": "UNAVAILABLE", "pages": []}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_page_count(self) -> None:
        self.assertEqual(self.report["page_count"], 3)

    def test_edge_collision_is_detected(self) -> None:
        self.assertTrue(any(item["code"] == "CONTENT_NEAR_PAGE_EDGE" for item in self.report["findings"]))

    def test_sparse_second_page_is_detected(self) -> None:
        self.assertIn("VERY_SPARSE_PAGE", self.report["pages"][1]["flags"])

    def test_small_image_is_detected(self) -> None:
        self.assertIn("SMALL_RENDERED_IMAGE", self.report["pages"][2]["flags"])

    def test_markdown_contains_page_table(self) -> None:
        text = render_markdown(self.report)
        self.assertIn("PAPER PDF VISUAL REVIEW", text)
        self.assertIn("SMALL_RENDERED_IMAGE", text)

    def test_zero_padded_rendered_page_is_matched(self) -> None:
        self.report["render"] = {"status": "OK", "pages": [str(self.path.parent / "page-01.png")]}
        text = render_markdown(self.report)
        self.assertIn("page-01.png", text)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_paper_layout import check_layout


class PaperLayoutTests(unittest.TestCase):
    @staticmethod
    def _config() -> dict:
        return {
            "page": {"blank_page_is_error": True, "abnormal_blank_ratio_warning": 1.1, "expected_body_pages_min": 1, "expected_body_pages_max": 40},
            "orphan_heading": {"bottom_ratio": 0.78, "minimum_following_words": 8},
            "captions": {"figure_pattern": r"图\s*(\d+)", "table_pattern": r"表\s*(\d+)", "top_ratio_warning": 0.0, "bottom_ratio_warning": 1.1},
            "latex": {"require_figure_labels": True, "require_figure_references": True},
        }

    @staticmethod
    def _check(bbox: str, source: str = "") -> dict:
        with tempfile.TemporaryDirectory() as directory:
            bbox_path = Path(directory) / "bbox.xml"
            bbox_path.write_text(bbox, encoding="utf-8")
            return check_layout(bbox_path, PaperLayoutTests._config(), {"sections": []}, source_text=source)

    def test_heading_at_page_bottom_is_error(self) -> None:
        bbox = """<?xml version="1.0" encoding="UTF-8"?>
<doc><page width="600" height="800">
<word xMin="50" yMin="700" xMax="130" yMax="720">问题分析</word>
</page></doc>"""
        config = self._config()
        sections = {"sections": [{"headings": ["问题分析"]}]}
        with tempfile.TemporaryDirectory() as directory:
            bbox_path = Path(directory) / "bbox.xml"
            bbox_path.write_text(bbox, encoding="utf-8")
            report = check_layout(bbox_path, config, sections)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("ORPHAN_HEADING", {item["code"] for item in report["findings"]})

    def test_data_values_are_not_table_numbers(self) -> None:
        bbox = """<?xml version="1.0" encoding="UTF-8"?>
<doc><page width="600" height="800">
<word xMin="50" yMin="100" xMax="70" yMax="120">表</word>
<word xMin="72" yMin="100" xMax="130" yMax="120">8:结果</word>
<word xMin="50" yMin="200" xMax="90" yMax="220">605</word>
<word xMin="100" yMin="200" xMax="150" yMax="220">1082</word>
</page></doc>"""
        report = self._check(bbox)
        self.assertNotIn("TABLE_NUMBERING_GAP", {item["code"] for item in report["findings"]})

    def test_real_unreferenced_figure_is_error(self) -> None:
        bbox = """<doc><page width="600" height="800"><word xMin="50" yMin="100" xMax="90" yMax="120">正文</word></page></doc>"""
        source = r"\begin{figure}\includegraphics{real.pdf}\caption{结果}\label{fig:real}\end{figure}"
        report = self._check(bbox, source)
        self.assertIn("FIGURE_UNREFERENCED", {item["code"] for item in report["findings"] if item["level"] == "ERROR"})

    def test_ref_autoref_and_cref_are_accepted(self) -> None:
        bbox = """<doc><page width="600" height="800"><word xMin="50" yMin="100" xMax="90" yMax="120">正文</word></page></doc>"""
        for command in ("ref", "autoref", "cref"):
            with self.subTest(command=command):
                source = rf"正文见\{command}{{fig:real}}。\begin{{figure}}\includegraphics{{real.pdf}}\caption{{结果}}\label{{fig:real}}\end{{figure}}"
                report = self._check(bbox, source)
                self.assertNotIn("FIGURE_UNREFERENCED", {item["code"] for item in report["findings"]})

    def test_dynamic_figure_macro_is_warning_not_error(self) -> None:
        bbox = """<doc><page width="600" height="800"><word xMin="50" yMin="100" xMax="90" yMax="120">正文</word></page></doc>"""
        source = r"\newcommand{\makefigure}[4]{\begin{figure}\includegraphics{#1}\caption{#2}\label{#4}\end{figure}}"
        report = self._check(bbox, source)
        self.assertIn("FIGURE_DYNAMIC_MACRO", {item["code"] for item in report["findings"] if item["level"] == "WARNING"})
        self.assertNotIn("FIGURE_UNREFERENCED", {item["code"] for item in report["findings"]})


if __name__ == "__main__":
    unittest.main()

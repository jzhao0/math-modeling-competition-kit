from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_paper_structure import check_structure
from paper_gate_common import load_yaml_compatible


CONFIG = load_yaml_compatible(Path(__file__).resolve().parents[1] / "config" / "paper_sections.yaml")


def _long_body(seed: str) -> str:
    return (seed + "本段说明数据关系与处理思路，并给出相应限制和验证安排。") * 4


class PaperStructureTests(unittest.TestCase):
    def test_section_then_subsection_is_valid_and_bibliography_is_excluded(self) -> None:
        text = "\n".join([
            "1 问题重述", "这里只陈述研究范围和资料特点，不使用固定模板关键词。",
            "2 问题分析",
            "2.1 男胎浓度变化", _long_body("第一部分。"),
            "2.2 分组及时点", _long_body("第二部分。"),
            "2.3 多因素扩展", _long_body("第三部分。"),
            "2.4 女胎异常判定", _long_body("第四部分。"),
            "3 模型假设与基本约定", "观测口径一致，边界条件可检查。",
            "4 符号说明", "后续正文。",
            "11 结论与建议", "冻结建议为 16、17、19 周。",
            "AI 工具使用声明", "说明文字。",
            "参考文献", "[2] DOI: 10.2307/2529876. 1982, 38(4): 963-974.",
            "A 附录 A", "附录内容。",
        ])
        report = check_structure(text, CONFIG)
        self.assertEqual(report["errors"], 0)
        inspected = {item["section"]: item for item in report["inspected_sections"]}
        self.assertLess(inspected["model_assumptions"]["chinese_characters"], 30)
        self.assertLess(inspected["conclusion"]["body_end"], text.index("10.2307"))
        self.assertNotIn("SECTION_HEADING_ORPHAN_TEXT", {item["code"] for item in report["findings"]})

    def test_each_problem_analysis_subsection_has_minimum_body(self) -> None:
        text = "\n".join([
            "2 问题分析",
            "2.1 第一部分", "太短。",
            "2.2 第二部分", _long_body("第二部分。"),
            "2.3 第三部分", _long_body("第三部分。"),
            "2.4 第四部分", _long_body("第四部分。"),
            "3 下一章节",
        ])
        config = {"sections": [next(item for item in CONFIG["sections"] if item["section"] == "problem_analysis")]}
        config["section_boundaries"] = CONFIG["section_boundaries"]
        report = check_structure(text, config)
        q1_errors = [item for item in report["findings"] if item.get("location") == "problem_analysis:q1" and item["level"] == "ERROR"]
        self.assertEqual([item["code"] for item in q1_errors], ["SECTION_QUESTION_TOO_SHORT"])

    def test_explicit_frozen_result_in_analysis_is_error(self) -> None:
        text = "\n".join([
            "2 问题分析",
            "2.1 第一部分", _long_body("最终推荐为 19，"),
            "2.2 第二部分", _long_body("第二部分。"),
            "2.3 第三部分", _long_body("第三部分。"),
            "2.4 第四部分", _long_body("第四部分。"),
            "3 下一章节",
        ])
        config = {"sections": [next(item for item in CONFIG["sections"] if item["section"] == "problem_analysis")]}
        config["section_boundaries"] = CONFIG["section_boundaries"]
        report = check_structure(text, config)
        self.assertIn("SECTION_FORBIDDEN_MOVE", {item["code"] for item in report["findings"]})


if __name__ == "__main__":
    unittest.main()

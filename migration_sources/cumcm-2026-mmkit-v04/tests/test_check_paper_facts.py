from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_paper_facts import check_facts


class PaperFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "facts": [
                {
                    "fact_id": "f16", "canonical_value": "16", "allowed_renderings": ["16"],
                    "required": True, "description": "first frozen result",
                },
                {
                    "fact_id": "f17", "canonical_value": "17", "allowed_renderings": ["17"],
                    "required": True, "description": "second frozen result",
                },
                {
                    "fact_id": "f19", "canonical_value": "19", "allowed_renderings": ["19"],
                    "forbidden_values": ["18"], "required": True, "description": "final frozen result",
                },
            ]
        }

    def test_16_17_19_pass(self) -> None:
        report = check_facts("三个冻结结果依次为 16、17 和 19。", self.config)
        self.assertEqual(report["status"], "PASS")

    def test_18_instead_of_19_fails(self) -> None:
        report = check_facts("三个结果依次为 16、17 和 18。", self.config)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual({item["code"] for item in report["findings"]}, {"FACT_MISSING", "FACT_FORBIDDEN_VALUE"})


if __name__ == "__main__":
    unittest.main()

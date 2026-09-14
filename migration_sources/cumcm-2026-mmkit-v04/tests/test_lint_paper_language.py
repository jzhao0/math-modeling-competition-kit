from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lint_paper_language import lint_language
from paper_gate_common import load_yaml_compatible


CONFIG = load_yaml_compatible(Path(__file__).resolve().parents[1] / "config" / "paper_language_rules.yaml")


class PaperLanguageTests(unittest.TestCase):
    def test_meta_phrase_is_error(self) -> None:
        report = lint_language("本文需要回答四个问题。", CONFIG)
        self.assertIn("META_NEEDS_ANSWER", {item["code"] for item in report["findings"] if item["level"] == "ERROR"})

    def test_directly_determines_is_warning(self) -> None:
        report = lint_language("这些结构直接决定了后续估计方法。", CONFIG)
        self.assertEqual(report["status"], "PASS_WITH_WARNINGS")
        self.assertIn("DIRECTLY_DETERMINES", {item["code"] for item in report["findings"]})

    def test_gate_tokens_are_errors(self) -> None:
        report = lint_language("G3 FINAL PASS", CONFIG)
        codes = {item["code"] for item in report["findings"] if item["level"] == "ERROR"}
        self.assertIn("INTERNAL_GATE_TOKEN", codes)

    def test_bare_group_labels_are_allowed(self) -> None:
        report = lint_language("G1/G2/G3/G4 分别表示四个实验组。", CONFIG)
        self.assertEqual(report["errors"], 0)
        self.assertNotIn("INTERNAL_GATE_TOKEN", {item["code"] for item in report["findings"]})

    def test_windows_path_is_error(self) -> None:
        report = lint_language(r"内部文件位于 D:\Projects\demo\main.tex。", CONFIG)
        self.assertIn("WINDOWS_PATH", {item["code"] for item in report["findings"] if item["level"] == "ERROR"})

    def test_internal_ledger_and_agent_tokens_are_errors(self) -> None:
        report = lint_language("agent_latest CLAIM_EVIDENCE ASSUMPTION_LEDGER", CONFIG)
        codes = {item["code"] for item in report["findings"] if item["level"] == "ERROR"}
        self.assertEqual(codes, {"AGENT_LATEST_TOKEN", "CLAIM_EVIDENCE_TOKEN", "ASSUMPTION_LEDGER_TOKEN"})

    def test_bibliography_and_non_prose_do_not_trigger_length_warnings(self) -> None:
        long_reference = "Reference " + "x" * 900 + " DOI: 10.2307/2529876."
        text = "正常正文。\n\n参考文献\n" + long_reference
        source = r"""
\begin{document}
正常正文。
\begin{figure}\caption{""" + "图题" * 500 + r"""}\end{figure}
\begin{table}\caption{""" + "表题" * 500 + r"""}\end{table}
\begin{equation}""" + "x" * 900 + r"""\end{equation}
\begin{lstlisting}""" + "code" * 400 + r"""\end{lstlisting}
\begin{thebibliography}{9}
""" + long_reference + r"""
\end{thebibliography}
\end{document}
"""
        report = lint_language(text, CONFIG, source)
        length_codes = {item["code"] for item in report["findings"] if "TOO_LONG" in item["code"]}
        self.assertEqual(length_codes, set())

    def test_sentence_warning_thresholds(self) -> None:
        warning = lint_language("中" * 181 + "。", CONFIG)
        strong = lint_language("中" * 261 + "。", CONFIG)
        self.assertIn("SENTENCE_TOO_LONG", {item["code"] for item in warning["findings"]})
        self.assertIn("SENTENCE_TOO_LONG_STRONG_WARNING", {item["code"] for item in strong["findings"]})


if __name__ == "__main__":
    unittest.main()

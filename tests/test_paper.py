from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mmkit.paper import audit_paper, build_paper, init_paper


class PaperTests(unittest.TestCase):
    def _workspace(self, temp: str) -> Path:
        root = Path(temp) / "workspace"
        (root / "paper" / "sections").mkdir(parents=True)
        (root / "results" / "figures").mkdir(parents=True)
        (root / "references").mkdir(parents=True)
        (root / "scripts").mkdir(parents=True)
        (root / "paper" / "main.tex").write_text(
            "\\documentclass{article}\n\\usepackage{graphicx}\n\\begin{document}\n"
            "\\input{sections/results}\n\\bibliography{../references/references}\n\\end{document}\n",
            encoding="utf-8",
        )
        (root / "paper" / "sections" / "results.tex").write_text(
            "\\section{Results}\\label{sec:results}\n"
            "See Figure~\\ref{fig:demo}. Prior work \\cite{demo2026}.\n"
            "\\begin{figure}\\includegraphics{../../results/figures/demo}"
            "\\caption{Demo}\\label{fig:demo}\\end{figure}\n",
            encoding="utf-8",
        )
        (root / "results" / "figures" / "demo.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
        (root / "references" / "references.bib").write_text(
            "@article{demo2026,\n title={Demo},\n author={A},\n year={2026}\n}\n",
            encoding="utf-8",
        )
        return root

    def test_audit_valid_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._workspace(temp)
            report = audit_paper(root, "paper/main.tex")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["source_file_count"], 2)
            self.assertEqual(report["figure_count"], 1)
            self.assertEqual(report["citation_count"], 1)

    def test_missing_citation_and_figure_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._workspace(temp)
            section = root / "paper" / "sections" / "results.tex"
            section.write_text(
                section.read_text(encoding="utf-8").replace("demo2026", "missing"),
                encoding="utf-8",
            )
            (root / "results" / "figures" / "demo.png").unlink()
            report = audit_paper(root, "paper/main.tex")
            self.assertEqual(report["status"], "FAIL")
            kinds = {x["kind"] for x in report["findings"]}
            self.assertIn("citation_key_missing", kinds)
            self.assertIn("figure_invalid", kinds)

    def test_static_missing_ref_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._workspace(temp)
            section = root / "paper" / "sections" / "results.tex"
            section.write_text(
                section.read_text(encoding="utf-8").replace("fig:demo}.", "dynamic}."),
                encoding="utf-8",
            )
            self.assertEqual(audit_paper(root, "paper/main.tex")["status"], "PASS_WITH_WARNINGS")

    def test_parent_escape_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._workspace(temp)
            (root / "paper" / "main.tex").write_text(
                "\\documentclass{article}\n\\begin{document}\\input{../../escape}\\end{document}\n",
                encoding="utf-8",
            )
            self.assertEqual(audit_paper(root, "paper/main.tex")["status"], "FAIL")

    def test_init_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            init_paper(root)
            main = root / "paper" / "main.tex"
            main.write_text("custom\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                init_paper(root)
            report = init_paper(root, force=True)
            self.assertIn("paper/main.tex", report["existing_files"])
            self.assertEqual(main.read_text(encoding="utf-8"), "custom\n")

    def test_build_fake_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._workspace(temp)
            builder = root / "scripts" / "build.py"
            builder.write_text(
                "from pathlib import Path\nPath('main.pdf').write_bytes(b'%PDF-1.4\\n% fake\\n')\n",
                encoding="utf-8",
            )
            report = build_paper(
                root,
                {
                    "schema_version": 1,
                    "main_tex": "paper/main.tex",
                    "cwd": "paper",
                    "argv": ["${PYTHON}", "../scripts/build.py"],
                    "expected_pdf": "paper/main.pdf",
                    "timeout_seconds": 30,
                },
            )
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["pdf"]["path"], "paper/main.pdf")
            self.assertEqual(len(report["pdf"]["sha256"]), 64)

    def test_build_skips_on_audit_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._workspace(temp)
            (root / "results" / "figures" / "demo.png").unlink()
            report = build_paper(
                root,
                {
                    "schema_version": 1,
                    "main_tex": "paper/main.tex",
                    "cwd": "paper",
                    "argv": ["${PYTHON}", "../scripts/nope.py"],
                    "expected_pdf": "paper/main.pdf",
                },
            )
            self.assertTrue(report["build_skipped"])
            self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()

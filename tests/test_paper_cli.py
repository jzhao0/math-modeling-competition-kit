from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mmkit.cli import main


class PaperCliTests(unittest.TestCase):
    def test_init_and_audit_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            init_json = root / "coordination" / "paper_init.json"
            audit_json = root / "coordination" / "paper_audit.json"

            self.assertEqual(main(["paper", "init", str(root), "--json", str(init_json)]), 0)
            self.assertEqual(
                main(["paper", "audit", str(root), "paper/main.tex", "--json", str(audit_json)]),
                0,
            )
            report = json.loads(audit_json.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["blocker_count"], 0)

    def test_build_cli_with_fake_builder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            self.assertEqual(main(["paper", "init", str(root)]), 0)
            script = root / "scripts" / "fake_build.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(
                "from pathlib import Path\nPath('main.pdf').write_bytes(b'%PDF-1.4\\n% fake\\n')\n",
                encoding="utf-8",
            )
            manifest = root / "config" / "paper_build_test.json"
            manifest.write_text(
                json.dumps({
                    "schema_version": 1,
                    "main_tex": "paper/main.tex",
                    "cwd": "paper",
                    "argv": ["${PYTHON}", "../scripts/fake_build.py"],
                    "expected_pdf": "paper/main.pdf",
                    "timeout_seconds": 30,
                }),
                encoding="utf-8",
            )
            report_json = root / "coordination" / "paper_build.json"
            self.assertEqual(
                main(["paper", "build", str(root), str(manifest), "--json", str(report_json)]),
                0,
            )
            report = json.loads(report_json.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["pdf"]["path"], "paper/main.pdf")


if __name__ == "__main__":
    unittest.main()

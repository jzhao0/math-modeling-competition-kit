from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from mmkit.cli import main


class CliTests(unittest.TestCase):
    def test_manifest_command_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "input.txt").write_text("x", encoding="utf-8")
            output = root / "manifest.json"
            code = main(["manifest", str(workspace), "--output", str(output)])
            self.assertEqual(code, 0)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["file_count"], 1)

    def test_audit_command_returns_nonzero_on_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = main(["audit", str(root), "--require", "paper.pdf", "--json", str(root / "report.json")])
            self.assertEqual(code, 2)

    def test_audit_command_passes_valid_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "paper.pdf").write_bytes(b"%PDF-demo")
            with zipfile.ZipFile(root / "support.zip", "w") as archive:
                archive.writestr("code/main.py", "print('ok')\n")
            code = main(["audit", str(root), "--require", "paper.pdf", "--require", "support.zip"])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

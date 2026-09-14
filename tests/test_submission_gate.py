from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from mmkit.submission.gate import audit_submission


class SubmissionGateTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "paper.pdf").write_bytes(b"%PDF-demo")
            with zipfile.ZipFile(root / "support.zip", "w") as archive:
                archive.writestr("code/main.py", "print('ok')\n")

            report = audit_submission(root, required=["paper.pdf", "support.zip"])
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["proof_level"], "MACHINE_VERIFIED")

    def test_secret_and_missing_required_file_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "notes.txt").write_text("api_key = 'abcdefghijklmnop'\n", encoding="utf-8")

            report = audit_submission(root, required=["paper.pdf"])
            kinds = {item["kind"] for item in report["findings"]}
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("missing_required_file", kinds)
            self.assertIn("secret_or_credential", kinds)

    def test_zip_traversal_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(root / "bad.zip", "w") as archive:
                archive.writestr("../escape.txt", "bad")
            report = audit_submission(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("zip_unsafe_path", {item["kind"] for item in report["findings"]})


if __name__ == "__main__":
    unittest.main()

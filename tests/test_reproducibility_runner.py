from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mmkit.reproducibility.runner import run_clean_room, validate_run_manifest


class RunnerTests(unittest.TestCase):
    def test_clean_room_executes_without_shell_and_checks_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "make_output.py").write_text(
                "from pathlib import Path\nPath('result.txt').write_text('ok', encoding='utf-8')\n",
                encoding="utf-8",
            )
            manifest = {
                "schema_version": 1,
                "commands": [
                    {
                        "name": "make-output",
                        "argv": ["${PYTHON}", "make_output.py"],
                        "cwd": ".",
                        "timeout_seconds": 30,
                        "expected_outputs": ["result.txt"],
                    }
                ],
            }
            report = run_clean_room(root, manifest)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["commands"][0]["returncode"], 0)
            self.assertEqual(report["commands"][0]["missing_outputs"], [])

    def test_manifest_rejects_windows_drive_paths_on_any_host(self) -> None:
        with self.assertRaises(ValueError):
            validate_run_manifest({
                "schema_version": 1,
                "commands": [{
                    "argv": ["echo", "x"],
                    "cwd": "C:\\outside",
                    "expected_outputs": ["result.txt"],
                }],
            })
        with self.assertRaises(ValueError):
            validate_run_manifest({
                "schema_version": 1,
                "commands": [{
                    "argv": ["echo", "x"],
                    "cwd": ".",
                    "expected_outputs": [r"D:\\private\\file.txt"],
                }],
            })

    def test_clean_room_rejects_output_symlink_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            outside = Path(tmp) / "outside.txt"
            outside.write_text("private", encoding="utf-8")
            script = root / "make_link.py"
            script.write_text(
                "from pathlib import Path\n"
                "Path('result.txt').symlink_to(" + repr(str(outside)) + ")\n",
                encoding="utf-8",
            )
            manifest = {
                "schema_version": 1,
                "commands": [{
                    "argv": ["${PYTHON}", "make_link.py"],
                    "cwd": ".",
                    "expected_outputs": ["result.txt"],
                }],
            }
            with self.assertRaisesRegex(ValueError, "expected output escaped workspace"):
                run_clean_room(root, manifest)

    def test_manifest_rejects_parent_escape(self) -> None:
        with self.assertRaises(ValueError):
            validate_run_manifest(
                {
                    "schema_version": 1,
                    "commands": [{"argv": ["echo", "x"], "cwd": "../outside"}],
                }
            )


if __name__ == "__main__":
    unittest.main()

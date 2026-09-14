from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mmkit.cli import main


class ScaffoldCliTests(unittest.TestCase):
    def test_init_then_clean_room_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "contest"
            init_report = Path(temp) / "init.json"
            reproduce_report = Path(temp) / "reproduce.json"

            code = main(
                [
                    "init",
                    str(root),
                    "--competition",
                    "CUMCM",
                    "--year",
                    "2027",
                    "--name",
                    "CUMCM-2027",
                    "--json",
                    str(init_report),
                ]
            )
            self.assertEqual(code, 0)
            init_data = json.loads(init_report.read_text(encoding="utf-8"))
            self.assertEqual(init_data["status"], "PASS")
            self.assertEqual(init_data["competition"], "CUMCM")

            code = main(
                [
                    "reproduce",
                    str(root),
                    str(root / "config" / "run_manifest.json"),
                    "--json",
                    str(reproduce_report),
                ]
            )
            self.assertEqual(code, 0)
            reproduce_data = json.loads(reproduce_report.read_text(encoding="utf-8"))
            self.assertEqual(reproduce_data["status"], "PASS")
            self.assertEqual(
                reproduce_data["commands"][0]["output_artifacts"][0]["path"],
                "results/smoke.txt",
            )

    def test_init_force_preserves_user_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "contest"
            root.mkdir()
            sentinel = root / "notes.txt"
            sentinel.write_text("user", encoding="utf-8")

            code = main(
                [
                    "init",
                    str(root),
                    "--competition",
                    "CUSTOM",
                    "--year",
                    "2027",
                    "--force",
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "user")


if __name__ == "__main__":
    unittest.main()

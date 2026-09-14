from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mmkit.reproducibility.runner import validate_run_manifest
from mmkit.scaffold import WORKSPACE_DIRS, init_project


class ScaffoldTests(unittest.TestCase):
    def test_creates_generic_workspace_and_valid_seed_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "team-workspace"
            report = init_project(
                root,
                competition="mcm",
                year=2027,
                project_name="MCM-2027-A",
            )

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["competition"], "MCM")
            self.assertEqual(report["year"], 2027)
            self.assertEqual(report["project_name"], "MCM-2027-A")

            for relpath in WORKSPACE_DIRS:
                self.assertTrue(root.joinpath(*relpath.split("/")).is_dir(), relpath)

            metadata = json.loads((root / "competition.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["competition"], "MCM")
            self.assertEqual(metadata["canonical_submission_dir"], "submission")

            headers = (root / "coordination" / "CLAIM_REGISTRY.csv").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                headers,
                "claim_id,paper_location,producer,input,artifact,value,precision,status\n",
            )

            run_manifest = json.loads(
                (root / "config" / "run_manifest.json").read_text(encoding="utf-8")
            )
            validate_run_manifest(run_manifest)
            self.assertEqual(
                run_manifest["commands"][0]["expected_outputs"],
                ["results/smoke.txt"],
            )

    def test_nonempty_destination_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "existing"
            root.mkdir()
            (root / "user.txt").write_text("keep", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                init_project(root, competition="CUMCM", year=2027)

            report = init_project(root, competition="CUMCM", year=2027, force=True)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual((root / "user.txt").read_text(encoding="utf-8"), "keep")
            self.assertTrue((root / "README_WORKSPACE.md").exists())

    def test_force_never_overwrites_existing_scaffold_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "existing"
            root.mkdir()
            readme = root / "README_WORKSPACE.md"
            readme.write_text("custom user content\n", encoding="utf-8")

            report = init_project(
                root,
                competition="ICM",
                year=2028,
                project_name="ICM-Custom",
                force=True,
            )

            self.assertIn("README_WORKSPACE.md", report["existing_files"])
            self.assertEqual(readme.read_text(encoding="utf-8"), "custom user content\n")

    def test_rejects_unsafe_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            with self.assertRaises(ValueError):
                init_project(root, competition="../MCM", year=2027)
            with self.assertRaises(ValueError):
                init_project(root, competition="MCM", year=1999)
            with self.assertRaises(ValueError):
                init_project(
                    root,
                    competition="MCM",
                    year=2027,
                    project_name="../escape",
                )


if __name__ == "__main__":
    unittest.main()

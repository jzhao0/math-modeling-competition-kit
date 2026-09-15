from __future__ import annotations

import io
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.audit_distribution import audit_archive


class DistributionAuditTests(unittest.TestCase):
    def test_wheel_passes_with_required_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            wheel = Path(temp) / "pkg.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("mmkit/__init__.py", "")
                archive.writestr("mmkit/cli.py", "")
            report = audit_archive(wheel)
            self.assertEqual(report["status"], "PASS")

    def test_sdist_blocks_migration_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sdist = Path(temp) / "pkg.tar.gz"
            with tarfile.open(sdist, "w:gz") as archive:
                for name in (
                    "pkg/pyproject.toml",
                    "pkg/README.md",
                    "pkg/LICENSE",
                    "pkg/src/mmkit/__init__.py",
                    "pkg/src/mmkit/cli.py",
                    "pkg/migration_sources/private.txt",
                ):
                    payload = b"x"
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))
            report = audit_archive(sdist)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(
                any(item["kind"] == "forbidden_distribution_component" for item in report["findings"])
            )

    def test_sdist_near_match_names_do_not_satisfy_required_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sdist = Path(temp) / "pkg.tar.gz"
            with tarfile.open(sdist, "w:gz") as archive:
                for name in (
                    "pkg/not-pyproject.toml",
                    "pkg/README.md",
                    "pkg/LICENSE",
                    "pkg/src/mmkit/__init__.py",
                    "pkg/not-src/mmkit/cli.py",
                ):
                    payload = b"x"
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))

            report = audit_archive(sdist)
            self.assertEqual(report["status"], "FAIL")
            missing = {
                item["member"]
                for item in report["findings"]
                if item["kind"] == "required_distribution_member_missing"
            }
            self.assertIn("pyproject.toml", missing)
            self.assertIn("src/mmkit/cli.py", missing)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import mmkit


class ReleaseMetadataTests(unittest.TestCase):
    def test_package_version_matches_pyproject(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(mmkit.__version__, data["project"]["version"])

    def test_v01_candidate_is_explicit_alpha(self) -> None:
        self.assertEqual(mmkit.__version__, "0.1.0a1")


if __name__ == "__main__":
    unittest.main()

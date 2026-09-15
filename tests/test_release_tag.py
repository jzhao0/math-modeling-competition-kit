from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.check_release_tag import expected_tag, validate_tag


class ReleaseTagTests(unittest.TestCase):
    def _write_pyproject(self, root: Path, version: str) -> Path:
        path = root / "pyproject.toml"
        path.write_text(
            "[project]\n"
            'name = "example"\n'
            f'version = "{version}"\n',
            encoding="utf-8",
        )
        return path

    def test_expected_tag_is_derived_from_project_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pyproject = self._write_pyproject(Path(temp), "1.2.3a4")
            self.assertEqual(expected_tag(pyproject), "v1.2.3a4")

    def test_matching_tag_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pyproject = self._write_pyproject(Path(temp), "0.1.0a1")
            ok, expected = validate_tag("v0.1.0a1", pyproject)
            self.assertTrue(ok)
            self.assertEqual(expected, "v0.1.0a1")

    def test_mismatched_tag_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pyproject = self._write_pyproject(Path(temp), "0.1.0a1")
            ok, expected = validate_tag("v0.2.0", pyproject)
            self.assertFalse(ok)
            self.assertEqual(expected, "v0.1.0a1")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mmkit.reproducibility.manifest import build_manifest


class ManifestTests(unittest.TestCase):
    def test_manifest_is_stable_and_host_path_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.txt").write_text("b\n", encoding="utf-8")
            (root / "a.txt").write_text("a\n", encoding="utf-8")

            first = build_manifest(root)
            second = build_manifest(root)

            self.assertEqual(first, second)
            self.assertEqual([item["path"] for item in first["files"]], ["a.txt", "b.txt"])
            self.assertNotIn(str(root), str(first))
            self.assertEqual(first["file_count"], 2)

    def test_manifest_hash_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "x.txt"
            path.write_text("one", encoding="utf-8")
            before = build_manifest(root)["files"][0]["sha256"]
            path.write_text("two", encoding="utf-8")
            after = build_manifest(root)["files"][0]["sha256"]
            self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()

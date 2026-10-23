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


    def test_symlink_directory_is_recorded_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source").mkdir()
            (root / "source" / "inside.txt").write_text("content", encoding="utf-8")
            try:
                (root / "alias").symlink_to(root / "source", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are not available on this host")

            entries = build_manifest(root, include_symlinks=True)["files"]
            self.assertEqual([item["path"] for item in entries], ["alias", "source/inside.txt"])
            self.assertEqual(entries[0]["type"], "symlink")
            self.assertEqual(
                [item["path"] for item in build_manifest(root)["files"]],
                ["source/inside.txt"],
            )


if __name__ == "__main__":
    unittest.main()

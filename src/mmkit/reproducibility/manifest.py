"""Deterministic file manifests for reproducible modeling workspaces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

DEFAULT_IGNORED_DIRS = frozenset({".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})


def hash_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return a lowercase SHA-256 digest for *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalise_relative(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return PurePosixPath(*rel.parts).as_posix()


def build_manifest(
    root: Path | str,
    *,
    ignored_dirs: Iterable[str] = DEFAULT_IGNORED_DIRS,
    include_symlinks: bool = False,
) -> dict[str, Any]:
    """Build a stable, machine-independent manifest for files below *root*.

    Absolute host paths are intentionally excluded from the returned structure.
    By default symlinks are recorded as non-regular entries instead of followed.
    """
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"manifest root must be a directory: {root_path}")

    ignored = set(ignored_dirs)
    records: list[dict[str, Any]] = []
    total_bytes = 0

    for path in sorted(root_path.rglob("*"), key=lambda p: _normalise_relative(p, root_path)):
        rel_parts = path.relative_to(root_path).parts
        if any(part in ignored for part in rel_parts[:-1]):
            continue
        if path.is_dir():
            continue

        rel = _normalise_relative(path, root_path)
        if path.is_symlink():
            if include_symlinks:
                records.append({"path": rel, "type": "symlink", "target": path.readlink().as_posix()})
            continue

        if not path.is_file():
            continue

        size = path.stat().st_size
        total_bytes += size
        records.append(
            {
                "path": rel,
                "type": "file",
                "size": size,
                "sha256": hash_file(path),
            }
        )

    return {
        "schema_version": 1,
        "algorithm": "sha256",
        "file_count": sum(1 for item in records if item["type"] == "file"),
        "total_bytes": total_bytes,
        "files": records,
    }


def write_manifest(manifest: dict[str, Any], path: Path | str) -> Path:
    """Write *manifest* as stable UTF-8 JSON and return the output path."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output

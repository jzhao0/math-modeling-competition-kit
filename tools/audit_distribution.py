"""Audit built distribution archives before a public release."""

from __future__ import annotations

import argparse
import json
import tarfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable

FORBIDDEN_COMPONENTS = {
    ".git",
    "__pycache__",
    "migration_sources",
}


def _members(path: Path) -> list[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            return archive.getnames()
    raise ValueError(f"unsupported distribution archive: {path}")


def _normalized_parts(value: str) -> tuple[str, ...]:
    return PurePosixPath(value.replace("\\", "/")).parts


def _contains_forbidden_component(name: str) -> str | None:
    parts = _normalized_parts(name)
    for part in parts:
        if part in FORBIDDEN_COMPONENTS:
            return part
    return None


def _has_suffix_member(members: Iterable[str], suffix: str) -> bool:
    """Match a required archive member by whole path components.

    Source distributions normally prepend one generated root directory, so an
    exact string equality check is too strict. Raw ``str.endswith`` is too
    permissive because names such as ``not-pyproject.toml`` can impersonate a
    required member. Comparing complete trailing path components permits the
    sdist root prefix while rejecting near-match filenames and directories.
    """

    suffix_parts = _normalized_parts(suffix)
    if not suffix_parts:
        return False

    for name in members:
        member_parts = _normalized_parts(name)
        if len(member_parts) >= len(suffix_parts) and member_parts[-len(suffix_parts) :] == suffix_parts:
            return True
    return False


def audit_archive(path: Path) -> dict:
    members = _members(path)
    findings: list[dict[str, str]] = []

    for member in members:
        forbidden = _contains_forbidden_component(member)
        if forbidden:
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "forbidden_distribution_component",
                    "member": member,
                    "detail": f"distribution contains forbidden component: {forbidden}",
                }
            )

    if path.suffix == ".whl":
        required = ["mmkit/__init__.py", "mmkit/cli.py"]
    else:
        required = ["pyproject.toml", "README.md", "LICENSE", "src/mmkit/__init__.py", "src/mmkit/cli.py"]

    for suffix in required:
        if not _has_suffix_member(members, suffix):
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "required_distribution_member_missing",
                    "member": suffix,
                    "detail": f"required release member is missing: {suffix}",
                }
            )

    return {
        "archive": path.name,
        "member_count": len(members),
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }


def audit_path(path: Path) -> dict:
    if path.is_dir():
        archives = sorted(
            item for item in path.iterdir() if item.suffix == ".whl" or item.name.endswith(".tar.gz")
        )
    elif path.is_file():
        archives = [path]
    else:
        raise ValueError(f"distribution path does not exist: {path}")

    if not archives:
        raise ValueError(f"no wheel or sdist archives found under: {path}")

    reports = [audit_archive(archive) for archive in archives]
    return {
        "schema_version": 1,
        "status": "PASS" if all(report["status"] == "PASS" for report in reports) else "FAIL",
        "archives": reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit MMKit public distribution archives")
    parser.add_argument("path", nargs="?", default="dist")
    parser.add_argument("--json", dest="json_path")
    args = parser.parse_args(argv)

    try:
        report = audit_path(Path(args.path))
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        print(f"DIST AUDIT: FAIL {exc}")
        return 2

    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")

    print(f"DIST AUDIT: {report['status']} archives={len(report['archives'])}")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

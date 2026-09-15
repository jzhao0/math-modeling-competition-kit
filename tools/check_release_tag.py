"""Fail closed when a release tag does not match project.version."""

from __future__ import annotations

import argparse
import os
import tomllib
from pathlib import Path


def project_version(pyproject: Path = Path("pyproject.toml")) -> str:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml does not contain a non-empty [project].version")
    return version.strip()


def expected_tag(pyproject: Path = Path("pyproject.toml")) -> str:
    return f"v{project_version(pyproject)}"


def validate_tag(tag: str, pyproject: Path = Path("pyproject.toml")) -> tuple[bool, str]:
    expected = expected_tag(pyproject)
    return tag == expected, expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Git release tag against pyproject project.version")
    parser.add_argument("tag", nargs="?", help="tag name; defaults to GITHUB_REF_NAME")
    parser.add_argument("--pyproject", default="pyproject.toml")
    args = parser.parse_args(argv)

    tag = args.tag or os.environ.get("GITHUB_REF_NAME")
    if not tag:
        print("RELEASE TAG CHECK: FAIL tag is missing and GITHUB_REF_NAME is unset")
        return 2

    try:
        ok, expected = validate_tag(tag, Path(args.pyproject))
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"RELEASE TAG CHECK: FAIL {exc}")
        return 2

    if not ok:
        print(f"RELEASE TAG CHECK: FAIL actual={tag} expected={expected}")
        return 2

    print(f"RELEASE TAG CHECK: PASS tag={tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

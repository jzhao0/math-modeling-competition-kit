"""Generic final-submission engineering gate.

This module validates packaging hygiene and reproducibility-facing invariants.
It does not certify scientific correctness, model quality, or contest eligibility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

TEXT_EXTENSIONS = {
    ".py", ".r", ".m", ".tex", ".md", ".txt", ".csv", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".ps1", ".bat", ".cmd", ".sh", ".xml", ".bib", ".sty", ".cls",
}

WINDOWS_ABS_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])[A-Z]:[\\/](?:[^\s\"'<>|]+[\\/]?)+")
UNIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])(?:/Users/[^/\s]+|/home/[^/\s]+)(?:/[^\s\"']*)?")

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "explicit_secret_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)\b\s*[:=]\s*[\"']?"
            r"(?!REDACTED\b|PLACEHOLDER\b|YOUR[_-]?|<)[A-Za-z0-9+/=_-]{12,}"
        ),
    ),
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decode_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > 8 * 1024 * 1024 or b"\x00" in data[:4096]:
        return None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def _safe_zip_member(name: str) -> tuple[bool, str | None]:
    normalized = name.replace("\\", "/")
    if normalized.startswith("/"):
        return False, "absolute POSIX path"
    if re.match(r"^[A-Za-z]:/", normalized):
        return False, "absolute Windows path"
    parts = PurePosixPath(normalized).parts
    if any(part == ".." for part in parts):
        return False, "path traversal"
    if "\x00" in name:
        return False, "NUL byte"
    return True, None


def _is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return (mode & 0o170000) == 0o120000


def _finding(severity: str, kind: str, location: str, detail: str) -> dict[str, str]:
    return {"severity": severity, "kind": kind, "location": location, "detail": detail}


def audit_submission(
    root: Path | str,
    *,
    required: list[str] | None = None,
    scan_text: bool = True,
    inspect_zips: bool = True,
) -> dict[str, Any]:
    submission = Path(root).resolve()
    findings: list[dict[str, str]] = []
    artifacts: list[dict[str, Any]] = []

    if not submission.is_dir():
        return {
            "schema_version": 1,
            "status": "FAIL",
            "proof_level": "MACHINE_VERIFIED",
            "artifacts": [],
            "findings": [_finding("BLOCKER", "submission_root", str(root), "directory does not exist")],
        }

    required = required or []
    for value in required:
        rel = PurePosixPath(value.replace("\\", "/"))
        if rel.is_absolute() or any(part == ".." for part in rel.parts):
            findings.append(_finding("BLOCKER", "required_path", value, "required path escapes submission root"))
            continue
        if not submission.joinpath(*rel.parts).is_file():
            findings.append(_finding("BLOCKER", "missing_required_file", rel.as_posix(), "required file is missing"))

    files: list[Path] = []
    for path in sorted(submission.rglob("*"), key=lambda p: p.relative_to(submission).as_posix()):
        if path.is_symlink():
            findings.append(
                _finding("BLOCKER", "filesystem_symlink", path.relative_to(submission).as_posix(), "symlink is not allowed")
            )
            continue
        if path.is_file():
            files.append(path)

    for path in files:
        rel = path.relative_to(submission).as_posix()
        artifacts.append({"path": rel, "size": path.stat().st_size, "sha256": _sha256(path)})

        if scan_text and path.suffix.lower() in TEXT_EXTENSIONS:
            text = _decode_text(path)
            if text is not None:
                for label, pattern in SECRET_PATTERNS:
                    for match in pattern.finditer(text):
                        sample = match.group(0)
                        redacted = sample[:6] + "..." if len(sample) > 6 else "[redacted]"
                        findings.append(_finding("BLOCKER", "secret_or_credential", rel, f"{label}: {redacted}"))
                for label, pattern in (
                    ("windows_absolute_path", WINDOWS_ABS_RE),
                    ("unix_home_path", UNIX_HOME_RE),
                ):
                    for match in pattern.finditer(text):
                        findings.append(
                            _finding("BLOCKER", "absolute_local_path", rel, f"{label}: {match.group(0)[:160]}")
                        )

        if inspect_zips and path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(path, "r") as archive:
                    seen: set[str] = set()
                    for info in archive.infolist():
                        canonical = info.filename.replace("\\", "/")
                        if canonical in seen:
                            findings.append(_finding("BLOCKER", "zip_duplicate_entry", f"{rel}:{canonical}", "duplicate entry"))
                        seen.add(canonical)
                        safe, reason = _safe_zip_member(info.filename)
                        if not safe:
                            findings.append(_finding("BLOCKER", "zip_unsafe_path", f"{rel}:{canonical}", reason or "unsafe path"))
                        if _is_zip_symlink(info):
                            findings.append(_finding("BLOCKER", "zip_symlink", f"{rel}:{canonical}", "symlink entry"))
                    bad_crc = archive.testzip()
                    if bad_crc:
                        findings.append(_finding("BLOCKER", "zip_crc", f"{rel}:{bad_crc}", "CRC check failed"))
            except zipfile.BadZipFile as exc:
                findings.append(_finding("BLOCKER", "invalid_zip", rel, str(exc)))

    blockers = [item for item in findings if item["severity"] == "BLOCKER"]
    return {
        "schema_version": 1,
        "status": "PASS" if not blockers else "FAIL",
        "proof_level": "MACHINE_VERIFIED",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "findings": findings,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MMKit generic final-submission engineering gate")
    parser.add_argument("submission_dir")
    parser.add_argument("--require", action="append", default=[], help="required relative file; repeatable")
    parser.add_argument("--json", dest="json_path", help="write full JSON report")
    parser.add_argument("--no-text-scan", action="store_true")
    parser.add_argument("--no-zip-scan", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = audit_submission(
        args.submission_dir,
        required=args.require,
        scan_text=not args.no_text_scan,
        inspect_zips=not args.no_zip_scan,
    )

    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    blockers = sum(1 for item in report["findings"] if item["severity"] == "BLOCKER")
    print(f"FINAL_GATE: {report['status']} blockers={blockers} artifacts={report.get('artifact_count', 0)}")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

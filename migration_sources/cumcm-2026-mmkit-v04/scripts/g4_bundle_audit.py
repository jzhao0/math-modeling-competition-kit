#!/usr/bin/env python3
"""MMKit G4 submission-engineering audit.

This script verifies exact-file identity, ZIP hygiene, clean-room extraction,
text-file secret/path leakage, Python syntax, and (optionally) a declared
RUN_MANIFEST.json command list. It does NOT certify scientific correctness.

Designed to use the Python standard library. `pdfinfo` is used when available
for PDF document-info checks; absence of pdfinfo is reported as UNVERIFIED
rather than silently treated as PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

TEXT_EXTENSIONS = {
    ".py", ".r", ".m", ".tex", ".md", ".txt", ".csv", ".json", ".yaml",
    ".yml", ".toml", ".ini", ".cfg", ".ps1", ".bat", ".cmd", ".sh",
    ".xml", ".bib", ".sty", ".cls",
}

WINDOWS_ABS_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])[A-Z]:[\\/](?:[^\s\"'<>|]+[\\/]?)+")
UNIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])(?:/Users/[^/\s]+|/home/[^/\s]+)(?:/[^\s\"']*)?")

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "explicit_api_key",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)\b\s*[:=]\s*[\"']?"
            r"(?!REDACTED\b|PLACEHOLDER\b|YOUR[_-]?|<)[A-Za-z0-9+/=_-]{12,}"
        ),
    ),
]

INTERNAL_TERMS = [
    "visual pass",
    "g4_preview",
    "mmkit",
    "handoff",
    "frozen science",
    "review-fixed candidate",
    "project_root_required",
]

PDFINFO_FIELDS = {
    "Title",
    "Subject",
    "Keywords",
    "Author",
    "Creator",
    "Producer",
    "CreationDate",
    "ModDate",
}


@dataclass
class Finding:
    severity: str  # BLOCKER / WARNING / INFO
    kind: str
    location: str
    detail: str


@dataclass
class ArtifactHash:
    path: str
    size: int
    md5: str
    sha256: str


@dataclass
class CommandResult:
    name: str
    argv: list[str]
    cwd: str
    returncode: int | None
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""
    error: str | None = None


@dataclass
class AuditReport:
    status: str = "UNVERIFIED"
    proof_level: str = "UNVERIFIED"
    artifacts: dict[str, ArtifactHash] = field(default_factory=dict)
    zip_file_count: int = 0
    extracted_root: str | None = None
    ai_zip_entry: str | None = None
    ai_byte_identity: bool | None = None
    pdfinfo_available: bool = False
    pdf_metadata: dict[str, dict[str, str]] = field(default_factory=dict)
    python_files_checked: int = 0
    command_results: list[CommandResult] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, kind: str, location: str, detail: str) -> None:
        self.findings.append(Finding(severity, kind, location, detail))

    @property
    def blockers(self) -> list[Finding]:
        return [x for x in self.findings if x.severity == "BLOCKER"]

    @property
    def warnings(self) -> list[Finding]:
        return [x for x in self.findings if x.severity == "WARNING"]


def file_hash(path: Path) -> ArtifactHash:
    md5 = hashlib.md5()  # nosec - contest checksum requirement, not security use
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            size += len(chunk)
            md5.update(chunk)
            sha256.update(chunk)
    return ArtifactHash(str(path), size, md5.hexdigest().upper(), sha256.hexdigest().upper())


def safe_zip_member(name: str) -> tuple[bool, str | None]:
    normalized = name.replace("\\", "/")
    if normalized.startswith("/"):
        return False, "absolute POSIX path"
    if re.match(r"^[A-Za-z]:/", normalized):
        return False, "absolute Windows path"
    p = PurePosixPath(normalized)
    if any(part == ".." for part in p.parts):
        return False, "path traversal '..'"
    if "\x00" in name:
        return False, "NUL byte"
    return True, None


def is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    # Unix file type bits live in the upper 16 bits of external_attr.
    mode = (info.external_attr >> 16) & 0xFFFF
    return (mode & 0o170000) == 0o120000


def prepare_extract_dir(requested: Path | None) -> tuple[Path, bool]:
    if requested is None:
        return Path(tempfile.mkdtemp(prefix="mmkit-g4-cleanroom-")), True
    requested = requested.resolve()
    requested.mkdir(parents=True, exist_ok=True)
    if any(requested.iterdir()):
        raise RuntimeError(f"extract directory must be empty: {requested}")
    return requested, False


def decode_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > 8 * 1024 * 1024:
        return None
    if b"\x00" in data[:4096]:
        return None
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def scan_text_file(path: Path, root: Path, report: AuditReport) -> None:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return
    text = decode_text(path)
    if text is None:
        return
    rel = str(path.relative_to(root))

    for label, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            sample = match.group(0)
            # Never echo the full possible secret into the audit output.
            redacted = sample[:6] + "..." if len(sample) > 6 else "[redacted]"
            report.add("BLOCKER", "secret_or_credential", rel, f"{label}: {redacted}")

    for pattern_name, pattern in (("windows_absolute_path", WINDOWS_ABS_RE), ("unix_home_path", UNIX_HOME_RE)):
        for match in pattern.finditer(text):
            report.add("BLOCKER", "absolute_local_path", rel, f"{pattern_name}: {match.group(0)[:160]}")

    lowered = text.lower()
    for term in INTERNAL_TERMS:
        if term in lowered:
            report.add("WARNING", "internal_workflow_term", rel, term)


def run_pdfinfo(path: Path, report: AuditReport, label: str, require: bool) -> None:
    exe = shutil.which("pdfinfo")
    if not exe:
        if require:
            report.add("BLOCKER", "pdf_metadata", label, "pdfinfo not available; required metadata check not executed")
        else:
            report.add("WARNING", "pdf_metadata", label, "pdfinfo not available; metadata check UNVERIFIED")
        return

    report.pdfinfo_available = True
    try:
        cp = subprocess.run([exe, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except Exception as exc:  # noqa: BLE001
        report.add("BLOCKER" if require else "WARNING", "pdf_metadata", label, f"pdfinfo failed: {exc}")
        return
    if cp.returncode != 0:
        report.add("BLOCKER" if require else "WARNING", "pdf_metadata", label, f"pdfinfo exit {cp.returncode}: {cp.stderr[-500:]}")
        return

    fields: dict[str, str] = {}
    for line in cp.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key in PDFINFO_FIELDS:
            fields[key] = value
    report.pdf_metadata[label] = fields
    nonempty = {k: v for k, v in fields.items() if v}
    if nonempty:
        report.add("BLOCKER", "pdf_metadata", label, f"non-empty document-info fields: {sorted(nonempty)}")


def inspect_zip(support: Path, ai: Path, extract_root: Path, report: AuditReport) -> None:
    seen: set[str] = set()
    ai_candidates: list[str] = []

    with zipfile.ZipFile(support, "r") as zf:
        infos = zf.infolist()
        report.zip_file_count = sum(not i.is_dir() for i in infos)
        for info in infos:
            name = info.filename
            canonical = name.replace("\\", "/")
            if canonical in seen:
                report.add("BLOCKER", "zip_duplicate_entry", canonical, "duplicate archive entry")
            seen.add(canonical)

            ok, why = safe_zip_member(name)
            if not ok:
                report.add("BLOCKER", "zip_unsafe_path", canonical, why or "unsafe path")
                continue
            if is_zip_symlink(info):
                report.add("BLOCKER", "zip_symlink", canonical, "symlink entries are not accepted in canonical support ZIP")
            if not info.is_dir() and PurePosixPath(canonical).name == "AI工具使用详情.pdf":
                ai_candidates.append(canonical)

        if report.blockers:
            return

        zf.extractall(extract_root)

        if len(ai_candidates) != 1:
            report.add("BLOCKER", "ai_pdf_identity", "supporting_material.zip", f"expected exactly one AI工具使用详情.pdf, found {len(ai_candidates)}")
        else:
            report.ai_zip_entry = ai_candidates[0]
            extracted_ai = extract_root / Path(*PurePosixPath(ai_candidates[0]).parts)
            report.ai_byte_identity = extracted_ai.read_bytes() == ai.read_bytes()
            if not report.ai_byte_identity:
                report.add("BLOCKER", "ai_pdf_identity", ai_candidates[0], "ZIP entry bytes differ from canonical standalone AI PDF")


def compile_python_files(root: Path, report: AuditReport) -> None:
    import py_compile

    for path in root.rglob("*.py"):
        if any(part in {"__pycache__", ".venv", "venv"} for part in path.parts):
            continue
        report.python_files_checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # noqa: BLE001
            report.add("BLOCKER", "python_syntax", str(path.relative_to(root)), str(exc))


def resolve_manifest_argv(argv: Iterable[Any], root: Path) -> list[str]:
    out: list[str] = []
    for raw in argv:
        value = str(raw)
        value = value.replace("{root}", str(root))
        if value == "{python}":
            value = sys.executable
        out.append(value)
    return out


def execute_manifest(root: Path, report: AuditReport, manifest_name: str, default_timeout: int) -> None:
    manifest_path = root / manifest_name
    if not manifest_path.is_file():
        report.add("BLOCKER", "run_manifest", manifest_name, "--execute-manifest requested but manifest is missing")
        return
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        report.add("BLOCKER", "run_manifest", manifest_name, f"invalid JSON: {exc}")
        return

    if payload.get("version") != 1 or not isinstance(payload.get("commands"), list):
        report.add("BLOCKER", "run_manifest", manifest_name, "expected version=1 and commands=[]")
        return

    for i, spec in enumerate(payload["commands"], start=1):
        if not isinstance(spec, dict) or not isinstance(spec.get("argv"), list) or not spec["argv"]:
            report.add("BLOCKER", "run_manifest", manifest_name, f"command #{i} has invalid argv")
            continue
        name = str(spec.get("name") or f"command-{i}")
        argv = resolve_manifest_argv(spec["argv"], root)
        cwd_rel = Path(str(spec.get("cwd", ".")))
        if cwd_rel.is_absolute() or ".." in cwd_rel.parts:
            report.add("BLOCKER", "run_manifest", name, f"unsafe cwd: {cwd_rel}")
            continue
        cwd = (root / cwd_rel).resolve()
        try:
            cwd.relative_to(root.resolve())
        except ValueError:
            report.add("BLOCKER", "run_manifest", name, f"cwd escapes clean room: {cwd}")
            continue
        timeout = int(spec.get("timeout_seconds", default_timeout))
        expected = int(spec.get("expected_exit", 0))
        started = time.monotonic()
        try:
            cp = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=os.environ.copy(),
                shell=False,
            )
            result = CommandResult(
                name=name,
                argv=argv,
                cwd=str(cwd.relative_to(root)),
                returncode=cp.returncode,
                duration_seconds=round(time.monotonic() - started, 3),
                stdout_tail=cp.stdout[-4000:],
                stderr_tail=cp.stderr[-4000:],
            )
            report.command_results.append(result)
            if cp.returncode != expected:
                report.add("BLOCKER", "clean_room_command", name, f"exit={cp.returncode}, expected={expected}")
        except Exception as exc:  # noqa: BLE001
            report.command_results.append(
                CommandResult(name, argv, str(cwd.relative_to(root)), None, round(time.monotonic() - started, 3), error=str(exc))
            )
            report.add("BLOCKER", "clean_room_command", name, str(exc))


def serialize_report(report: AuditReport) -> dict[str, Any]:
    return {
        "status": report.status,
        "proof_level": report.proof_level,
        "artifacts": {k: asdict(v) for k, v in report.artifacts.items()},
        "zip_file_count": report.zip_file_count,
        "extracted_root": report.extracted_root,
        "ai_zip_entry": report.ai_zip_entry,
        "ai_byte_identity": report.ai_byte_identity,
        "pdfinfo_available": report.pdfinfo_available,
        "pdf_metadata": report.pdf_metadata,
        "python_files_checked": report.python_files_checked,
        "command_results": [asdict(v) for v in report.command_results],
        "findings": [asdict(v) for v in report.findings],
        "blocker_count": len(report.blockers),
        "warning_count": len(report.warnings),
    }


def print_report(report: AuditReport) -> None:
    print("=== MMKIT G4 BUNDLE AUDIT ===")
    print(f"STATUS={report.status}")
    print(f"PROOF_LEVEL={report.proof_level}")
    for label, info in report.artifacts.items():
        print(f"{label.upper()}_SIZE={info.size}")
        print(f"{label.upper()}_MD5={info.md5}")
        print(f"{label.upper()}_SHA256={info.sha256}")
    print(f"ZIP_FILE_COUNT={report.zip_file_count}")
    print(f"EXTRACTED_ROOT={report.extracted_root}")
    print(f"AI_ZIP_ENTRY={report.ai_zip_entry}")
    print(f"AI_BYTE_IDENTITY={'PASS' if report.ai_byte_identity else 'FAIL' if report.ai_byte_identity is False else 'UNVERIFIED'}")
    print(f"PDFINFO_AVAILABLE={'YES' if report.pdfinfo_available else 'NO'}")
    print(f"PYTHON_FILES_CHECKED={report.python_files_checked}")
    print(f"COMMANDS_EXECUTED={len(report.command_results)}")
    print(f"BLOCKERS={len(report.blockers)}")
    print(f"WARNINGS={len(report.warnings)}")
    for finding in report.findings:
        print(f"[{finding.severity}] {finding.kind} :: {finding.location} :: {finding.detail}")
    print("NOTE=This audit covers submission engineering, not mathematical/scientific correctness.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit canonical CUMCM G4 paper/AI/support artifacts")
    p.add_argument("--paper", type=Path, required=True)
    p.add_argument("--ai", type=Path, required=True)
    p.add_argument("--support", type=Path, required=True)
    p.add_argument("--extract-dir", type=Path)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--execute-manifest", action="store_true")
    p.add_argument("--manifest-name", default="RUN_MANIFEST.json")
    p.add_argument("--command-timeout", type=int, default=180)
    p.add_argument("--require-pdfinfo", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    report = AuditReport()

    for label, path in (("paper", args.paper), ("ai", args.ai), ("support", args.support)):
        if not path.is_file():
            report.add("BLOCKER", "missing_artifact", label, str(path))
        else:
            report.artifacts[label] = file_hash(path)
    if report.blockers:
        report.status = "FAIL"
        report.proof_level = "MACHINE_VERIFIED"
        print_report(report)
        return 2

    try:
        extract_root, temporary = prepare_extract_dir(args.extract_dir)
    except Exception as exc:  # noqa: BLE001
        report.add("BLOCKER", "clean_room", "extract-dir", str(exc))
        report.status = "FAIL"
        report.proof_level = "MACHINE_VERIFIED"
        print_report(report)
        return 2

    report.extracted_root = str(extract_root)
    try:
        inspect_zip(args.support, args.ai, extract_root, report)
        if not report.blockers:
            for path in extract_root.rglob("*"):
                if path.is_file():
                    scan_text_file(path, extract_root, report)
            compile_python_files(extract_root, report)
            if args.execute_manifest:
                execute_manifest(extract_root, report, args.manifest_name, args.command_timeout)

        run_pdfinfo(args.paper, report, "paper", args.require_pdfinfo)
        run_pdfinfo(args.ai, report, "ai", args.require_pdfinfo)
        if report.ai_zip_entry:
            zip_ai = extract_root / Path(*PurePosixPath(report.ai_zip_entry).parts)
            if zip_ai.is_file():
                run_pdfinfo(zip_ai, report, "zip_ai", args.require_pdfinfo)

        report.status = "PASS" if not report.blockers else "FAIL"
        report.proof_level = "MACHINE_VERIFIED"
        print_report(report)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(serialize_report(report), ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if not report.blockers else 2
    finally:
        # Keep an explicitly requested clean room for human inspection. Temporary
        # directories are removed automatically to avoid leaving hidden artifacts.
        if temporary:
            shutil.rmtree(extract_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

"""Claim/evidence provenance for MMKit.

This module binds human-readable claim rows to exact evidence file bytes. It
does not certify scientific correctness; it detects whether previously bound
claim evidence is still current.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

REQUIRED_COLUMNS = (
    "claim_id",
    "paper_location",
    "producer",
    "input",
    "artifact",
    "value",
    "precision",
    "status",
)

CLAIM_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def _normalized_relpath(raw: str, *, field: str, claim_id: str, required: bool = False) -> str | None:
    value = raw.strip()
    if not value:
        if required:
            raise ValueError(f"{claim_id}: {field} is required")
        return None

    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or WINDOWS_DRIVE_RE.match(value):
        raise ValueError(f"{claim_id}: {field} must be workspace-relative: {value}")

    path = PurePosixPath(normalized)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{claim_id}: {field} contains unsafe path components: {value}")
    return path.as_posix()


def load_claim_registry(path: str | Path) -> list[dict[str, str]]:
    """Load and validate the human-editable CSV claim registry."""

    registry = Path(path)
    with registry.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        missing = [name for name in REQUIRED_COLUMNS if name not in headers]
        if missing:
            raise ValueError(f"claim registry missing required columns: {missing}")

        rows: list[dict[str, str]] = []
        seen: set[str] = set()
        for line_no, raw in enumerate(reader, start=2):
            row = {str(k): (v or "").strip() for k, v in raw.items() if k is not None}
            claim_id = row["claim_id"]
            if not claim_id:
                raise ValueError(f"line {line_no}: claim_id is required")
            if not CLAIM_ID_RE.fullmatch(claim_id):
                raise ValueError(f"line {line_no}: invalid claim_id {claim_id!r}")
            if claim_id in seen:
                raise ValueError(f"line {line_no}: duplicate claim_id {claim_id!r}")
            seen.add(claim_id)

            if not row["paper_location"]:
                raise ValueError(f"{claim_id}: paper_location is required")
            if not row["value"]:
                raise ValueError(f"{claim_id}: value is required")
            if not row["status"]:
                raise ValueError(f"{claim_id}: status is required")
            if row["status"].upper() == "PASS":
                raise ValueError(f"{claim_id}: generic status PASS is forbidden; use an explicit claim state")

            for field in ("producer", "input"):
                normalized = _normalized_relpath(row[field], field=field, claim_id=claim_id)
                row[field] = normalized or ""
            row["artifact"] = _normalized_relpath(
                row["artifact"], field="artifact", claim_id=claim_id, required=True
            ) or ""

            rows.append(row)

    return rows


def _resolve_evidence_file(root: Path, relpath: str, *, claim_id: str, role: str) -> Path:
    candidate = root / Path(*PurePosixPath(relpath).parts)
    if candidate.is_symlink():
        raise ValueError(f"{claim_id}: {role} may not be a symlink: {relpath}")

    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{claim_id}: {role} escaped workspace: {relpath}")
    if not resolved.exists():
        raise FileNotFoundError(f"{claim_id}: {role} missing: {relpath}")
    if not resolved.is_file():
        raise ValueError(f"{claim_id}: {role} must be a regular file: {relpath}")
    return resolved


def _fingerprint_file(root: Path, relpath: str, *, claim_id: str, role: str) -> dict[str, Any]:
    path = _resolve_evidence_file(root, relpath, claim_id=claim_id, role=role)
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return {
        "path": relpath,
        "sha256": digest.hexdigest(),
        "size": size,
    }


def _claim_semantics(row: dict[str, str]) -> dict[str, str]:
    return {key: row.get(key, "").strip() for key in sorted(row)}


def build_claim_lock(root: str | Path, registry_path: str | Path) -> dict[str, Any]:
    """Create an exact-byte evidence lock for all claims in a CSV registry."""

    workspace = Path(root).resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace root must be a directory: {workspace}")

    registry_file = Path(registry_path)
    rows = load_claim_registry(registry_file)

    claims: list[dict[str, Any]] = []
    for row in rows:
        claim_id = row["claim_id"]
        evidence: dict[str, Any] = {}
        for role in ("producer", "input", "artifact"):
            relpath = row[role]
            evidence[role] = (
                _fingerprint_file(workspace, relpath, claim_id=claim_id, role=role)
                if relpath
                else None
            )

        claims.append(
            {
                "claim_id": claim_id,
                "row_sha256": _canonical_hash(_claim_semantics(row)),
                "claim": _claim_semantics(row),
                "evidence": evidence,
            }
        )

    semantic_registry = [
        {"claim_id": item["claim_id"], "row_sha256": item["row_sha256"]}
        for item in sorted(claims, key=lambda x: x["claim_id"])
    ]

    return {
        "schema_version": 1,
        "status": "LOCKED",
        "proof_level": "MACHINE_VERIFIED",
        "scope": "claim/evidence identity only; scientific correctness is not certified",
        "registry_semantic_sha256": _canonical_hash(semantic_registry),
        "claim_count": len(claims),
        "claims": sorted(claims, key=lambda x: x["claim_id"]),
    }


def write_claim_lock(lock: dict[str, Any], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_lock(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported claim lock schema_version")
    if not isinstance(data.get("claims"), list):
        raise ValueError("claim lock is missing claims")
    return data


def verify_claim_lock(
    root: str | Path,
    registry_path: str | Path,
    lock_path: str | Path,
) -> dict[str, Any]:
    """Verify that claim semantics and bound evidence bytes still match a lock."""

    workspace = Path(root).resolve()
    rows = load_claim_registry(registry_path)
    lock = _load_lock(lock_path)

    current = {row["claim_id"]: row for row in rows}
    locked = {item["claim_id"]: item for item in lock["claims"]}

    findings: list[dict[str, str]] = []
    claim_reports: list[dict[str, Any]] = []

    for claim_id in sorted(current.keys() | locked.keys()):
        if claim_id not in locked:
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "claim_unbound",
                    "claim_id": claim_id,
                    "detail": "claim exists in registry but not in evidence lock",
                }
            )
            claim_reports.append(
                {"claim_id": claim_id, "status": "STALE", "stale_reasons": ["claim is unbound"], "evidence": {}}
            )
            continue

        if claim_id not in current:
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "claim_removed",
                    "claim_id": claim_id,
                    "detail": "claim exists in evidence lock but not in registry",
                }
            )
            claim_reports.append(
                {"claim_id": claim_id, "status": "STALE", "stale_reasons": ["claim was removed"], "evidence": {}}
            )
            continue

        row = current[claim_id]
        locked_claim = locked[claim_id]
        stale_reasons: list[str] = []
        evidence_report: dict[str, Any] = {}

        row_sha = _canonical_hash(_claim_semantics(row))
        if row_sha != locked_claim.get("row_sha256"):
            stale_reasons.append("claim semantics changed")
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "claim_semantics_changed",
                    "claim_id": claim_id,
                    "detail": "claim row no longer matches locked row fingerprint",
                }
            )

        for role in ("producer", "input", "artifact"):
            expected = locked_claim.get("evidence", {}).get(role)
            relpath = row[role]

            if expected is None:
                if relpath:
                    stale_reasons.append(f"{role} added")
                    findings.append(
                        {
                            "severity": "BLOCKER",
                            "kind": "evidence_path_changed",
                            "claim_id": claim_id,
                            "detail": f"{role} was added after lock",
                        }
                    )
                    try:
                        actual = _fingerprint_file(workspace, relpath, claim_id=claim_id, role=role)
                    except (FileNotFoundError, ValueError) as exc:
                        actual = {"path": relpath, "error": str(exc)}
                    evidence_report[role] = {"status": "STALE", "expected": None, "actual": actual}
                else:
                    evidence_report[role] = {"status": "CURRENT", "expected": None, "actual": None}
                continue

            if not relpath:
                stale_reasons.append(f"{role} removed")
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "kind": "evidence_path_changed",
                        "claim_id": claim_id,
                        "detail": f"{role} was removed after lock",
                    }
                )
                evidence_report[role] = {"status": "STALE", "expected": expected, "actual": None}
                continue

            try:
                actual = _fingerprint_file(workspace, relpath, claim_id=claim_id, role=role)
            except (FileNotFoundError, ValueError) as exc:
                stale_reasons.append(f"{role} unavailable")
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "kind": "evidence_unavailable",
                        "claim_id": claim_id,
                        "detail": str(exc),
                    }
                )
                evidence_report[role] = {
                    "status": "STALE",
                    "expected": expected,
                    "actual": {"path": relpath, "error": str(exc)},
                }
                continue

            role_status = "CURRENT"
            if (
                actual["path"] != expected.get("path")
                or actual["sha256"] != expected.get("sha256")
                or actual["size"] != expected.get("size")
            ):
                role_status = "STALE"
                stale_reasons.append(f"{role} fingerprint changed")
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "kind": "evidence_fingerprint_changed",
                        "claim_id": claim_id,
                        "detail": f"{role} no longer matches locked path/size/SHA-256",
                    }
                )

            evidence_report[role] = {
                "status": role_status,
                "expected": expected,
                "actual": actual,
            }

        claim_reports.append(
            {
                "claim_id": claim_id,
                "status": "STALE" if stale_reasons else "CURRENT",
                "stale_reasons": stale_reasons,
                "row_sha256": row_sha,
                "locked_row_sha256": locked_claim.get("row_sha256"),
                "evidence": evidence_report,
            }
        )

    semantic_registry = [
        {
            "claim_id": claim_id,
            "row_sha256": _canonical_hash(_claim_semantics(current[claim_id])),
        }
        for claim_id in sorted(current)
    ]
    registry_semantic_sha = _canonical_hash(semantic_registry)
    if registry_semantic_sha != lock.get("registry_semantic_sha256"):
        findings.append(
            {
                "severity": "INFO",
                "kind": "registry_semantic_fingerprint_changed",
                "claim_id": "",
                "detail": "registry semantic fingerprint differs from the lock",
            }
        )

    stale_count = sum(1 for item in claim_reports if item["status"] == "STALE")
    status = "PASS" if stale_count == 0 else "STALE"
    return {
        "schema_version": 1,
        "status": status,
        "proof_level": "MACHINE_VERIFIED",
        "scope": "claim/evidence identity only; scientific correctness is not certified",
        "claim_count": len(current),
        "stale_claim_count": stale_count,
        "registry_semantic_sha256": registry_semantic_sha,
        "claims": claim_reports,
        "findings": findings,
    }

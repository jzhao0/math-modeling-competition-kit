"""Shared, dependency-free helpers for the deterministic paper quality gate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


VALID_LEVELS = {"ERROR", "WARNING", "INFO"}


def load_yaml_compatible(path: str | Path) -> dict[str, Any]:
    """Load JSON-compatible YAML without requiring a global Python package.

    JSON is a strict subset of YAML 1.2. Keeping gate configuration in that
    subset makes the Windows baseline deterministic while remaining readable by
    normal YAML tooling.
    """

    config_path = Path(path)
    try:
        data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{config_path} must be JSON-compatible YAML: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a top-level mapping")
    return data


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def finding(
    level: str,
    code: str,
    message: str,
    *,
    location: str | None = None,
    evidence: str | None = None,
) -> dict[str, str]:
    normalized = level.upper()
    if normalized not in VALID_LEVELS:
        raise ValueError(f"Unsupported finding level: {level}")
    result = {"level": normalized, "code": code, "message": message}
    if location:
        result["location"] = location
    if evidence:
        result["evidence"] = evidence[:240]
    return result


def summarize(checker: str, findings: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    errors = sum(item.get("level") == "ERROR" for item in findings)
    warnings = sum(item.get("level") == "WARNING" for item in findings)
    status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {
        "checker": checker,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "findings": findings,
        **extra,
    }


def write_report(report: dict[str, Any], output: str | Path | None) -> None:
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def chinese_char_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def compact_evidence(text: str, start: int, end: int, radius: int = 32) -> str:
    snippet = text[max(0, start - radius) : min(len(text), end + radius)]
    return re.sub(r"\s+", " ", snippet).strip()

"""Check frozen decision facts against text extracted from the compiled PDF."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from paper_gate_common import compact_evidence, finding, load_yaml_compatible, read_text, summarize, write_report


def _rendering_pattern(rendering: Any) -> tuple[str, str]:
    if isinstance(rendering, dict):
        value = str(rendering.get("value", ""))
        if rendering.get("regex"):
            return value, value
    else:
        value = str(rendering)
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value):
        return value, rf"(?<![\d.]){re.escape(value)}(?![\d.])"
    return value, re.escape(value)


def _matches(text: str, rendering: Any, context_pattern: str | None = None) -> list[re.Match[str]]:
    _, pattern = _rendering_pattern(rendering)
    if context_pattern:
        pattern = rf"(?:{context_pattern}).{{0,80}}(?:{pattern})|(?:{pattern}).{{0,80}}(?:{context_pattern})"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL))


def check_facts(text: str, config: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    checked: list[dict[str, Any]] = []
    facts = config.get("facts", [])
    if not isinstance(facts, list):
        raise ValueError("paper_facts.yaml: 'facts' must be a list")

    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            raise ValueError(f"paper_facts.yaml: facts[{index}] must be a mapping")
        missing = [key for key in ("fact_id", "canonical_value", "allowed_renderings", "required", "description") if key not in fact]
        if missing:
            raise ValueError(f"paper_facts.yaml: facts[{index}] missing {', '.join(missing)}")
        fact_id = str(fact["fact_id"])
        canonical = str(fact["canonical_value"])
        allowed = list(fact.get("allowed_renderings") or [])
        if canonical not in [str(item) for item in allowed]:
            allowed.insert(0, canonical)
        context = fact.get("context_pattern")
        allowed_hits: list[tuple[Any, re.Match[str]]] = []
        for rendering in allowed:
            allowed_hits.extend((rendering, hit) for hit in _matches(text, rendering, context))

        if bool(fact["required"]) and not allowed_hits:
            findings.append(finding(
                "ERROR", "FACT_MISSING", f"Required fact '{fact_id}' is absent: {fact['description']}", location=fact_id
            ))

        forbidden = list(fact.get("forbidden_values") or [])
        wrong_roundings = list(fact.get("wrong_roundings") or [])
        for category, renderings, code in (
            ("forbidden", forbidden, "FACT_FORBIDDEN_VALUE"),
            ("wrong rounding", wrong_roundings, "FACT_WRONG_ROUNDING"),
        ):
            for rendering in renderings:
                for hit in _matches(text, rendering, context):
                    label, _ = _rendering_pattern(rendering)
                    findings.append(finding(
                        "ERROR",
                        code,
                        f"Fact '{fact_id}' contains {category} '{label}' instead of canonical '{canonical}'.",
                        location=fact_id,
                        evidence=compact_evidence(text, hit.start(), hit.end()),
                    ))

        conflicting = list(fact.get("conflicting_renderings") or [])
        for rendering in conflicting:
            for hit in _matches(text, rendering, context):
                label, _ = _rendering_pattern(rendering)
                findings.append(finding(
                    "ERROR",
                    "FACT_CONTRADICTORY_RENDERING",
                    f"Fact '{fact_id}' contains contradictory rendering '{label}'.",
                    location=fact_id,
                    evidence=compact_evidence(text, hit.start(), hit.end()),
                ))

        checked.append({
            "fact_id": fact_id,
            "canonical_value": canonical,
            "required": bool(fact["required"]),
            "allowed_occurrences": len(allowed_hits),
        })

    return summarize("paper_facts", findings, checked_facts=checked)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="UTF-8 pdftotext output")
    parser.add_argument("--config", default=str(repo_root / "config" / "paper_facts.yaml"))
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        report = check_facts(read_text(args.text), load_yaml_compatible(args.config))
    except (OSError, ValueError) as exc:
        report = summarize("paper_facts", [finding("ERROR", "FACT_CHECKER_CONFIGURATION", str(exc))])
    write_report(report, args.output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

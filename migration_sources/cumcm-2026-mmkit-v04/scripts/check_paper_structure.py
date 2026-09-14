"""Check deterministic section boundaries and structural paper contracts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from paper_gate_common import chinese_char_count, compact_evidence, finding, load_yaml_compatible, read_text, summarize, write_report
from paper_tex_extract import extract_section_titles


def _heading_matches(text: str, headings: list[str]) -> list[re.Match[str]]:
    alternatives = "|".join(re.escape(item) for item in headings)
    if not alternatives:
        return []
    return list(re.finditer(rf"(?m)^[ \t\f]*(?:\d+[ \t]+)?(?:{alternatives})[ \t]*$", text))


def _section_boundaries(text: str, config: dict[str, Any], source_text: str) -> list[int]:
    """Return same-level section, section*, bibliography, appendix, and EOF starts."""

    positions: set[int] = {len(text)}
    boundary_config = config.get("section_boundaries", {})
    exact_titles = {
        str(item).strip()
        for item in boundary_config.get("unnumbered_headings", [])
    }
    exact_titles.update(
        str(heading).strip()
        for contract in config.get("sections", [])
        for heading in contract.get("headings", [])
    )
    exact_titles.update(
        title for title in extract_section_titles(source_text)
        if title not in {"参考文献", "References", "Bibliography"}
    )

    if exact_titles:
        alternatives = "|".join(re.escape(item) for item in sorted(exact_titles, key=len, reverse=True))
        for match in re.finditer(rf"(?m)^[ \t\f]*(?:\d+[ \t]+)?(?:{alternatives})[ \t]*$", text):
            positions.add(match.start())

    # Same-level numbered sections use an integer prefix. Decimal prefixes are subsections.
    # Requiring the line to end in a letter/CJK character rejects running headers such as
    # "3 模型假设 3", whose trailing page number otherwise creates a premature boundary.
    for match in re.finditer(r"(?m)^[ \t\f]*\d+[ \t]+[^\n]{0,78}[A-Za-z\u3400-\u9fff][ \t]*$", text):
        positions.add(match.start())

    for pattern in boundary_config.get("bibliography_patterns", []):
        pattern = str(pattern).replace("(?i)", "")
        for match in re.finditer(rf"^[ \t\f]*(?:{pattern})[ \t]*$", text, flags=re.MULTILINE | re.IGNORECASE):
            positions.add(match.start())
    for pattern in boundary_config.get("appendix_patterns", []):
        pattern = str(pattern).replace("(?i)", "")
        for match in re.finditer(rf"^[ \t\f]*(?:[A-Z][ \t]+)?(?:{pattern})(?:[ \t]+[^\n]*)?[ \t]*$", text, flags=re.MULTILINE | re.IGNORECASE):
            positions.add(match.start())
    return sorted(positions)


def _manual_review_finding(section_id: str, moves: list[Any], location: str) -> dict[str, str] | None:
    if not moves:
        return None
    return finding(
        "WARNING",
        "SECTION_MANUAL_REVIEW",
        f"Manual review required for '{section_id}': {', '.join(str(item) for item in moves)}.",
        location=location,
    )


def check_structure(text: str, config: dict[str, Any], source_text: str = "") -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    sections = config.get("sections", [])
    if not isinstance(sections, list):
        raise ValueError("paper_sections.yaml: 'sections' must be a list")
    boundaries = _section_boundaries(text, config, source_text)
    inspected: list[dict[str, Any]] = []

    for contract in sections:
        section_id = str(contract.get("section"))
        matches = _heading_matches(text, [str(item) for item in contract.get("headings", [])])
        if not matches:
            findings.append(finding(
                "ERROR", "SECTION_MISSING", f"Required section '{section_id}' was not found.", location=section_id
            ))
            continue

        heading = matches[0]
        body_end = next((position for position in boundaries if position >= heading.end()), len(text))
        body = text[heading.end():body_end].strip()
        char_count = chinese_char_count(body)

        if "min_chars" in contract and char_count < int(contract["min_chars"]):
            findings.append(finding(
                "ERROR", "SECTION_TOO_SHORT", f"Section '{section_id}' has {char_count} Chinese characters; minimum is {contract['min_chars']}.", location=section_id
            ))
        if "max_chars" in contract and char_count > int(contract["max_chars"]):
            findings.append(finding(
                "ERROR", "SECTION_TOO_LONG", f"Section '{section_id}' has {char_count} Chinese characters; maximum is {contract['max_chars']}.", location=section_id
            ))

        review = _manual_review_finding(section_id, list(contract.get("manual_review_moves", [])), section_id)
        if review:
            findings.append(review)

        per_question = contract.get("per_question")
        question_summary: list[dict[str, Any]] = []
        if per_question:
            question_locations: list[tuple[int, int, str]] = []
            for marker in per_question.get("markers", []):
                marker_match = re.search(str(marker["pattern"]), body, flags=re.IGNORECASE)
                if marker_match:
                    question_locations.append((marker_match.start(), marker_match.end(), str(marker["id"])))
                else:
                    findings.append(finding(
                        "ERROR", "SECTION_QUESTION_MISSING", f"Section '{section_id}' has no subsection for '{marker['id']}'.", location=f"{section_id}:{marker['id']}"
                    ))
            question_locations.sort()
            minimum = int(per_question.get("minimum_body_chars", 0))
            for index, (question_start, question_heading_end, question_id) in enumerate(question_locations):
                question_end = question_locations[index + 1][0] if index + 1 < len(question_locations) else len(body)
                question_body = body[question_heading_end:question_end].strip()
                question_chars = chinese_char_count(question_body)
                if question_chars < minimum:
                    findings.append(finding(
                        "ERROR", "SECTION_QUESTION_TOO_SHORT",
                        f"Section '{section_id}' subsection '{question_id}' has {question_chars} Chinese characters; minimum is {minimum}.",
                        location=f"{section_id}:{question_id}",
                    ))
                question_review = _manual_review_finding(
                    section_id,
                    list(per_question.get("manual_review_moves", [])),
                    f"{section_id}:{question_id}",
                )
                if question_review:
                    findings.append(question_review)
                question_summary.append({"question": question_id, "chinese_characters": question_chars})

        for move in contract.get("forbidden_moves", []):
            for hit in re.finditer(str(move["pattern"]), body, flags=re.IGNORECASE | re.DOTALL):
                findings.append(finding(
                    "ERROR", "SECTION_FORBIDDEN_MOVE", f"Section '{section_id}' contains forbidden frozen pattern '{move['name']}'.", location=section_id,
                    evidence=compact_evidence(body, hit.start(), hit.end()),
                ))

        inspected.append({
            "section": section_id,
            "chinese_characters": char_count,
            "body_start": heading.end(),
            "body_end": body_end,
            "questions": question_summary,
        })

    return summarize("paper_structure", findings, inspected_sections=inspected)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--source")
    parser.add_argument("--config", default=str(repo_root / "config" / "paper_sections.yaml"))
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        report = check_structure(
            read_text(args.text),
            load_yaml_compatible(args.config),
            read_text(args.source) if args.source else "",
        )
    except (OSError, ValueError, re.error) as exc:
        report = summarize("paper_structure", [finding("ERROR", "STRUCTURE_CHECKER_CONFIGURATION", str(exc))])
    write_report(report, args.output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

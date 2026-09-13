"""Augment the deterministic Sol packet with bounded review-index and visual triage material."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_sol_review_packet import NOT_EXTRACTABLE, render_markdown


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def _claims_text(items: list[dict[str, Any]]) -> str:
    if not items:
        return NOT_EXTRACTABLE
    lines: list[str] = []
    for item in items:
        numbers = ", ".join(item.get("numbers", [])) or "NONE"
        refs = ", ".join(item.get("references", [])) or "NONE"
        facts = ", ".join(item.get("frozen_fact_hits", [])) or "NONE"
        lines.append(
            f"- [{item.get('evidence_status', 'UNKNOWN')}] {item.get('text', '')} "
            f"(numbers={numbers}; refs={refs}; facts={facts}; section={item.get('section', 'UNKNOWN')})"
        )
    return "\n".join(lines)


def _group_visual_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in findings:
        grouped[str(item.get("code", "VISUAL_REVIEW"))].append(item)

    output: list[dict[str, Any]] = []
    for code, items in sorted(grouped.items()):
        pages = sorted({int(item.get("page")) for item in items if str(item.get("page", "")).isdigit()})
        locations = ", ".join(f"page:{page}" for page in pages) or "UNKNOWN"
        message = str(items[0].get("message", "Inspect the rendered pages visually."))
        priority = "HIGH" if code in {"CONTENT_NEAR_PAGE_EDGE", "OVERSIZED_RENDERED_IMAGE"} else "MEDIUM"
        output.append({
            "priority": priority,
            "source": code,
            "location": locations,
            "question": f"{message} Flagged pages: {', '.join(map(str, pages)) or 'UNKNOWN'}. Inspect once; do not tune the paper merely to clear a heuristic.",
        })
    return output


def _dedupe_queue(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        key = (
            str(item.get("source", "")),
            str(item.get("location", "")),
            str(item.get("question", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def augment_packet(packet: dict[str, Any], intelligence: dict[str, Any], visual: dict[str, Any]) -> dict[str, Any]:
    packet = dict(packet)
    packet["paper_intelligence"] = intelligence
    packet["visual_review"] = visual

    claims = dict(packet.get("claims", {}))
    claims_by_question = (
        intelligence.get("review_claims_by_question")
        or intelligence.get("claims_by_question")
        or {}
    ) if isinstance(intelligence, dict) else {}
    for question in ("Q1", "Q2", "Q3", "Q4"):
        items = claims_by_question.get(question, []) if isinstance(claims_by_question, dict) else []
        if items:
            claims[question] = _claims_text(items)
    packet["claims"] = claims

    queue = list(packet.get("manual_review_queue", []))
    for item in intelligence.get("manual_review_queue", []) if isinstance(intelligence, dict) else []:
        queue.append({
            "priority": item.get("priority", "MEDIUM"),
            "source": item.get("source", "CLAIM_EVIDENCE_TRIAGE"),
            "location": item.get("location", "UNKNOWN"),
            "question": item.get("question", "Review claim/evidence alignment."),
        })
    queue.extend(_group_visual_findings(visual.get("findings", []) if isinstance(visual, dict) else []))
    packet["manual_review_queue"] = _dedupe_queue(queue)
    return packet


def _section_index_block(intelligence: dict[str, Any]) -> str:
    lines = ["### Deterministic Section / Question Index", "", "| Section | Question | Roles | Source |", "|---|---|---|---|"]
    items = (
        intelligence.get("section_index")
        or intelligence.get("semantic_map")
        or []
    ) if isinstance(intelligence, dict) else []
    if not items:
        return "### Deterministic Section / Question Index\n\nUNAVAILABLE\n"
    for item in items:
        lines.append(
            f"| {item.get('number', '')} {item.get('title', '')} | {item.get('question', 'GLOBAL')} | "
            f"{', '.join(item.get('roles', [])) or 'GENERAL'} | "
            f"`{item.get('source_file', 'UNKNOWN')}:{item.get('source_line', 'UNKNOWN')}-{item.get('source_end_line', 'UNKNOWN')}` |"
        )
    return "\n".join(lines) + "\n"


def _visual_block(visual: dict[str, Any]) -> str:
    if not visual:
        return "### PDF Visual Review Summary\n\nUNAVAILABLE\n"
    lines = [
        "### PDF Visual Review Summary", "",
        f"- page_count: {visual.get('page_count', 'UNKNOWN')}",
        f"- render_status: {visual.get('render', {}).get('status', 'UNKNOWN')}",
        f"- deterministic_warnings: {visual.get('warning_count', 0)}", "",
        "| Page | Words | Lines | Images | Flags |", "|---:|---:|---:|---:|---|",
    ]
    for item in visual.get("pages", []):
        lines.append(
            f"| {item.get('page')} | {item.get('word_count')} | {item.get('line_count')} | "
            f"{item.get('image_count')} | {', '.join(item.get('flags', [])) or 'PASS'} |"
        )
    return "\n".join(lines) + "\n"


def render_augmented_markdown(packet: dict[str, Any]) -> str:
    text = render_markdown(packet)
    section_index = _section_index_block(packet.get("paper_intelligence", {}))
    visual = _visual_block(packet.get("visual_review", {}))
    marker5 = "## 5. Abstract"
    marker15 = "## 15. Known Automation Limits"
    if marker5 in text:
        text = text.replace(marker5, section_index + "\n" + marker5, 1)
    if marker15 in text:
        text = text.replace(marker15, visual + "\n" + marker15, 1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--packet-json")
    parser.add_argument("--packet-md")
    parser.add_argument("--intelligence-json")
    parser.add_argument("--visual-json")
    args = parser.parse_args()
    try:
        workspace = Path(args.workspace).resolve()
        packet_json = Path(args.packet_json).resolve() if args.packet_json else workspace / "reports" / "sol_review_packet.json"
        packet_md = Path(args.packet_md).resolve() if args.packet_md else workspace / "reports" / "sol_review_packet.md"
        intelligence_json = Path(args.intelligence_json).resolve() if args.intelligence_json else workspace / "reports" / "paper_intelligence.json"
        visual_json = Path(args.visual_json).resolve() if args.visual_json else workspace / "reports" / "paper_visual_review.json"
        packet = _read_json(packet_json)
        if not packet:
            raise ValueError(f"Sol packet JSON missing or invalid: {packet_json}")
        augmented = augment_packet(packet, _read_json(intelligence_json), _read_json(visual_json))
        packet_json.write_text(json.dumps(augmented, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
        packet_md.write_text(render_augmented_markdown(augmented), encoding="utf-8")
        print(str(packet_md))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SOL_REVIEW_AUGMENT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

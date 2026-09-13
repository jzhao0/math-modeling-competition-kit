"""Build deterministic review material from one explicitly selected paper source."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paper_gate_common import load_yaml_compatible
from paper_tex_extract import (
    TexDocument,
    expand_tex_document,
    extract_abstract,
    extract_equations,
    extract_figures,
    extract_references,
    extract_sections,
    extract_tables,
)


PACKET_TITLE = "# SOL CENTRAL REVIEW PACKET"
NOT_EXTRACTABLE = "NOT DETERMINISTICALLY EXTRACTABLE"
PDF_UNAVAILABLE = "PAPER_PDF_UNAVAILABLE"
REVIEW_SCOPE = (
    "scientific/modeling logic",
    "completeness of answers",
    "naturalness of Chinese academic writing",
    "claim/evidence alignment",
    "whether figures/tables support nearby claims",
    "limitation wording",
    "abstract/conclusion quality",
    "whether Gate warnings are real problems",
)
AUTOMATION_LIMITS = (
    "wording naturalness",
    "scientific correctness",
    "appropriateness of modeling choices",
    "whether a figure is visually readable",
    "whether a figure deserves to remain in main text",
    "whether conclusions overclaim evidence",
    "semantic completeness",
    "clinical/scientific interpretation",
    "color/print quality",
    "equation visual aesthetics",
)


def _absolute(path: str | Path, base: Path) -> Path:
    candidate = Path(path)
    return (candidate if candidate.is_absolute() else base / candidate).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def _gate_from_markdown(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    status = re.search(r"(?mi)^- Status:\s*\*\*(\S+)\*\*", text)
    errors = re.search(r"(?mi)^- Errors:\s*(\d+)", text)
    warnings = re.search(r"(?mi)^- Warnings:\s*(\d+)", text)
    findings: list[dict[str, str]] = []
    for match in re.finditer(r"(?m)^\|\s*(ERROR|WARNING)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]*)\|", text):
        findings.append({
            "level": match.group(1).strip(), "code": match.group(2).strip(),
            "message": match.group(3).strip(), "location": match.group(4).strip(),
        })
    return {
        "status": status.group(1) if status else "UNKNOWN",
        "errors": int(errors.group(1)) if errors else sum(item["level"] == "ERROR" for item in findings),
        "warnings": int(warnings.group(1)) if warnings else sum(item["level"] == "WARNING" for item in findings),
        "findings": findings,
    }


def _git_commit(workspace: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() or "UNKNOWN"
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"


def _page_count(gate: dict[str, Any], paper_pdf: Path) -> int | str:
    if not paper_pdf.is_file():
        return "UNKNOWN"
    for report in gate.get("checker_reports", []):
        if report.get("checker") == "paper_layout" and isinstance(report.get("page_count"), int):
            return report["page_count"]
    return "UNKNOWN"


def _facts(config: dict[str, Any]) -> list[dict[str, Any]]:
    facts = config.get("facts", [])
    return facts if isinstance(facts, list) else []


def _fact_group(fact: dict[str, Any]) -> str:
    explicit = str(fact.get("question", "")).upper()
    if explicit in {"Q1", "Q2", "Q3", "Q4"}:
        return explicit
    fact_id = str(fact.get("fact_id", ""))
    match = re.search(r"(?i)(?:^|[_-])q([1-4])(?:[_-]|$)", fact_id)
    return f"Q{match.group(1)}" if match else "UNGROUPED"


def _finding_location(item: dict[str, Any]) -> str:
    pieces = []
    for key in ("location", "section", "source_line", "page"):
        if item.get(key) not in (None, ""):
            pieces.append(f"{key}={item[key]}")
    return "; ".join(pieces) or "UNKNOWN"


def _review_priority(code: str) -> str:
    if code == "SECTION_MANUAL_REVIEW":
        return "HIGH"
    if code in {"FIGURE_CAPTION_AT_PAGE_BOTTOM", "FIGURE_CAPTION_AT_PAGE_TOP"} or "DYNAMIC" in code:
        return "MEDIUM"
    return "LOW"


def _queue_question(code: str) -> str:
    fixed = {
        "SECTION_MANUAL_REVIEW": "Does the section satisfy the stated semantic writing contract?",
        "FIGURE_CAPTION_AT_PAGE_BOTTOM": "Are the figure and caption visually continuous across this page boundary?",
        "FIGURE_CAPTION_AT_PAGE_TOP": "Did the figure remain with its caption on the intended page?",
        "CONSECUTIVE_CONNECTOR_SENTENCES": "Does the repeated connector usage make the prose mechanical?",
    }
    if code in fixed:
        return fixed[code]
    if "DYNAMIC" in code:
        return "Can the dynamic LaTeX construct be verified manually in the rendered paper?"
    return "Is this Gate warning a real paper issue?"


def _section_is(title: str, term: str) -> bool:
    return term.lower() in re.sub(r"\s+", "", title).lower()


def build_packet(
    *, workspace: Path, main_tex: Path, paper_pdf: Path, gate_json: Path,
    gate_md: Path, facts_config: Path, sections_config: Path,
) -> dict[str, Any]:
    gate = _read_json(gate_json)
    if not gate:
        gate = _gate_from_markdown(gate_md)
    document = expand_tex_document(main_tex)
    sections = extract_sections(document)
    figures = extract_figures(document)
    tables = extract_tables(document)
    equations = extract_equations(document, sections)
    references = extract_references(document)
    facts_data = load_yaml_compatible(facts_config) if facts_config.is_file() else {"facts": []}
    findings = gate.get("findings", []) if isinstance(gate.get("findings", []), list) else []
    errors = [item for item in findings if item.get("level") == "ERROR"]
    warnings = [item for item in findings if item.get("level") == "WARNING"]
    conclusion = next((item for item in sections if _section_is(item["title"], "结论")), None)
    ai_declaration = next((item for item in sections if "AI" in item["title"].upper() and "工具" in item["title"]), None)
    pdf_available = paper_pdf.is_file()
    return {
        "schema_version": 1,
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(workspace), "main_tex": str(main_tex),
            "paper_pdf": str(paper_pdf), "paper_pdf_status": "AVAILABLE" if pdf_available else PDF_UNAVAILABLE,
            "gate_json": str(gate_json), "gate_md": str(gate_md),
            "facts_config": str(facts_config), "sections_config": str(sections_config),
            "git_commit": _git_commit(workspace), "paper_page_count": _page_count(gate, paper_pdf),
            "gate_status": gate.get("status", "UNKNOWN"),
            "error_count": int(gate.get("errors", len(errors))),
            "warning_count": int(gate.get("warnings", len(warnings))),
        },
        "gate": {"errors": errors, "warnings": warnings},
        "frozen_facts": _facts(facts_data),
        "sections": sections,
        "abstract": extract_abstract(document, sections),
        "figures": figures, "tables": tables, "equations": equations,
        "claims": {
            "Q1": NOT_EXTRACTABLE, "Q2": NOT_EXTRACTABLE,
            "Q3": NOT_EXTRACTABLE, "Q4": NOT_EXTRACTABLE,
            "final_conclusion": conclusion["text"] if conclusion else NOT_EXTRACTABLE,
        },
        "conclusion": conclusion["text"] if conclusion else NOT_EXTRACTABLE,
        "ai_declaration": ai_declaration["text"] if ai_declaration else NOT_EXTRACTABLE,
        "references": references,
        "manual_review_queue": [
            {
                "priority": _review_priority(str(item.get("code", ""))),
                "source": str(item.get("code", "UNKNOWN")),
                "location": _finding_location(item),
                "question": _queue_question(str(item.get("code", ""))),
            }
            for item in warnings
        ],
    }


def _line(lines: list[str], value: str = "") -> None:
    lines.append(value)


def _location(item: dict[str, Any]) -> str:
    return f"{item.get('source_file', item.get('source_tex', 'UNKNOWN'))}:{item.get('source_line', 'UNKNOWN')}"


def render_markdown(packet: dict[str, Any]) -> str:
    lines: list[str] = [PACKET_TITLE, ""]
    meta = packet["metadata"]
    _line(lines, "## 0. Run Metadata")
    _line(lines)
    for key in ("generated_at", "workspace", "main_tex", "paper_pdf", "paper_pdf_status", "gate_json", "gate_md", "facts_config", "sections_config", "git_commit", "paper_page_count", "gate_status", "error_count", "warning_count"):
        _line(lines, f"- {key}: `{meta[key]}`")
    _line(lines)
    _line(lines, "## 1. Review Scope")
    _line(lines)
    _line(lines, "This packet is deterministic review material.")
    _line(lines, "It does not judge scientific quality and does not rewrite the paper.")
    _line(lines)
    for item in REVIEW_SCOPE:
        _line(lines, f"- {item}")
    _line(lines)
    _line(lines, "## 2. Gate Summary")
    for level, heading in (("errors", "Errors"), ("warnings", "Warnings")):
        _line(lines)
        _line(lines, f"### {heading}")
        _line(lines)
        items = packet["gate"][level]
        if not items:
            _line(lines, f"No Gate {level}.")
        for item in items:
            _line(lines, f"- `{item.get('code', 'UNKNOWN')}`: {item.get('message', '')}")
            _line(lines, f"  - location: {_finding_location(item)}")
    _line(lines)
    _line(lines, "## 3. Frozen Facts")
    grouped = {name: [] for name in ("Q1", "Q2", "Q3", "Q4", "UNGROUPED")}
    for fact in packet["frozen_facts"]:
        grouped[_fact_group(fact)].append(fact)
    for group, facts in grouped.items():
        if facts:
            _line(lines)
            _line(lines, f"### {group}")
            _line(lines)
            for fact in facts:
                _line(lines, "```json")
                _line(lines, json.dumps(fact, ensure_ascii=False, indent=2))
                _line(lines, "```")
    if not packet["frozen_facts"]:
        _line(lines)
        _line(lines, "No frozen facts are configured.")
    _line(lines)
    _line(lines, "## 4. Paper Outline")
    _line(lines)
    for item in packet["sections"]:
        indent = "  " if item["level"] == 2 else ""
        number = f"{item['number']} " if item["number"] else ""
        _line(lines, f"{indent}- {number}{item['title']} — source `{_location(item)}-{item['source_end_line']}`; Chinese characters: {item['chinese_characters']}")
    _line(lines)
    _line(lines, "## 5. Abstract")
    _line(lines)
    _line(lines, packet["abstract"])
    _line(lines)
    _line(lines, "## 6. Main Text by Section")
    for item in packet["sections"]:
        prefix = "###" if item["level"] == 1 else "####"
        number = f"{item['number']} " if item["number"] else ""
        _line(lines)
        _line(lines, f"{prefix} {number}{item['title']}")
        _line(lines)
        _line(lines, f"[source: {_location(item)}-{item['source_end_line']}]")
        _line(lines)
        _line(lines, item["text"] or "(No prose before the next subsection.)")
    _line(lines)
    _line(lines, "## 7. Figures")
    for item in packet["figures"]:
        _line(lines)
        _line(lines, f"### Figure {item['number']}")
        _line(lines)
        _line(lines, f"- label: `{item['label']}`")
        _line(lines, f"- caption: {item['caption']}")
        _line(lines, f"- source file: `{item['source_file']}` ({item['source_status']})")
        _line(lines, f"- source tex location: `{item['source_tex']}:{item['source_line']}-{item['source_end_line']}`")
        ref = item["first_reference"]
        _line(lines, f"- first body reference location: `{ref['source_file']}:{ref['source_line']}`" if ref else "- first body reference location: `UNKNOWN`")
        _line(lines, f"- page number: `{item['page']}`")
        _line(lines, f"- referenced: {'YES' if item['referenced'] else 'NO'}")
    if not packet["figures"]:
        _line(lines, "\nNo figures found in the selected source graph.")
    _line(lines)
    _line(lines, "## 8. Tables")
    for item in packet["tables"]:
        _line(lines)
        _line(lines, f"### Table {item['number']}")
        _line(lines)
        _line(lines, f"- label: `{item['label']}`")
        _line(lines, f"- caption: {item['caption']}")
        _line(lines, f"- source location: `{item['source_tex']}:{item['source_line']}-{item['source_end_line']}`")
        ref = item["first_reference"]
        _line(lines, f"- first body reference location: `{ref['source_file']}:{ref['source_line']}`" if ref else "- first body reference location: `UNKNOWN`")
        _line(lines, f"- referenced: {'YES' if item['referenced'] else 'NO'}")
        _line(lines)
        _line(lines, item["content_markdown"])
    if not packet["tables"]:
        _line(lines, "\nNo tables found in the selected source graph.")
    _line(lines)
    _line(lines, "## 9. Equations / Model Definitions")
    for item in packet["equations"]:
        _line(lines)
        _line(lines, f"### Equation {item['number']}")
        _line(lines)
        _line(lines, f"- source section: {item['source_section']}")
        _line(lines, f"- source location: `{_location(item)}`")
        _line(lines, "```latex")
        _line(lines, item["latex"])
        _line(lines, "```")
    if not packet["equations"]:
        _line(lines, "\nNo numbered equation environments found.")
    _line(lines)
    _line(lines, "## 10. Claims and Result Numbers")
    for key in ("Q1", "Q2", "Q3", "Q4", "final_conclusion"):
        _line(lines)
        _line(lines, f"### {key}")
        _line(lines)
        _line(lines, packet["claims"][key])
    _line(lines)
    _line(lines, "## 11. Conclusion")
    _line(lines)
    _line(lines, packet["conclusion"])
    _line(lines)
    _line(lines, "## 12. AI Declaration")
    _line(lines)
    _line(lines, packet["ai_declaration"])
    _line(lines)
    _line(lines, "## 13. References Metadata")
    _line(lines)
    _line(lines, f"- reference count: {len(packet['references'])}")
    for item in packet["references"]:
        _line(lines, f"- [{item['number']}] {item['summary']}")
        _line(lines, f"  - DOI: {', '.join(item['dois']) if item['dois'] else 'NONE'}")
    _line(lines)
    _line(lines, "## 14. Manual Review Queue")
    _line(lines)
    _line(lines, "| Priority | Source | Location | Question for reviewer |")
    _line(lines, "|---|---|---|---|")
    for item in packet["manual_review_queue"]:
        values = [str(item[key]).replace("|", "\\|") for key in ("priority", "source", "location", "question")]
        _line(lines, "| " + " | ".join(values) + " |")
    _line(lines)
    _line(lines, "## 15. Known Automation Limits")
    _line(lines)
    for item in AUTOMATION_LIMITS:
        _line(lines, f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--main-tex")
    parser.add_argument("--paper-pdf")
    parser.add_argument("--gate-json")
    parser.add_argument("--gate-md")
    parser.add_argument("--facts-config")
    parser.add_argument("--sections-config")
    parser.add_argument("--output-md")
    parser.add_argument("--output-json")
    args = parser.parse_args()
    try:
        workspace = Path(args.workspace).resolve()
        gate_json = _absolute(args.gate_json or "reports/paper_gate.json", workspace)
        gate_md = _absolute(args.gate_md or "reports/paper_gate.md", workspace)
        gate = _read_json(gate_json)
        main_tex = _absolute(args.main_tex or gate.get("main_tex") or "06_paper/main.tex", workspace)
        paper_pdf = _absolute(args.paper_pdf or gate.get("pdf") or "09_submission/paper.pdf", workspace)
        workspace_facts = workspace / "config" / "paper_facts.yaml"
        facts_config = _absolute(args.facts_config, workspace) if args.facts_config else (workspace_facts.resolve() if workspace_facts.is_file() else (repo_root / "config" / "paper_facts.yaml").resolve())
        sections_config = _absolute(args.sections_config, workspace) if args.sections_config else (repo_root / "config" / "paper_sections.yaml").resolve()
        output_md = _absolute(args.output_md or "reports/sol_review_packet.md", workspace)
        output_json = _absolute(args.output_json or "reports/sol_review_packet.json", workspace)
        packet = build_packet(
            workspace=workspace, main_tex=main_tex, paper_pdf=paper_pdf,
            gate_json=gate_json, gate_md=gate_md, facts_config=facts_config,
            sections_config=sections_config,
        )
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(packet), encoding="utf-8")
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(packet, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
        print(str(output_md))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SOL_REVIEW_PACKET_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""Build a deterministic paper-review index and bounded claim/evidence triage queue."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from paper_gate_common import load_yaml_compatible
from paper_tex_extract import expand_tex_document, extract_sections


QUESTION_PATTERNS = {
    "Q1": (r"(?i)\bq\s*1\b", r"第一问", r"问题[一1]", r"任务[一1]"),
    "Q2": (r"(?i)\bq\s*2\b", r"第二问", r"问题[二2]", r"任务[二2]"),
    "Q3": (r"(?i)\bq\s*3\b", r"第三问", r"问题[三3]", r"任务[三3]"),
    "Q4": (r"(?i)\bq\s*4\b", r"第四问", r"问题[四4]", r"任务[四4]"),
}
ROLE_PATTERNS = {
    "ASSUMPTIONS": (r"假设", r"前提"),
    "VARIABLES": (r"符号", r"变量", r"参数定义"),
    "MODEL": (r"模型", r"建模", r"目标函数", r"约束"),
    "SOLUTION": (r"求解", r"算法", r"计算方法", r"优化"),
    "RESULTS": (r"结果", r"结果分析", r"计算结果", r"参数估计"),
    "ROBUSTNESS": (r"敏感性", r"稳健", r"鲁棒", r"误差分析"),
    "STRENGTHS_LIMITS": (r"优缺点", r"优点", r"缺点", r"局限", r"限制"),
    "CONCLUSION": (r"结论", r"建议"),
}
CLAIM_MARKERS = re.compile(
    r"(表明|说明|可知|得到|结果为|结果显示|最优|优于|劣于|提高|提升|降低|下降|"
    r"达到|分别为|最大|最小|显著|验证|证明|因此|由此|采用|选择)"
)
STRONG_CLAIM_MARKERS = re.compile(
    r"(最优|最大|最小|显著|优于|劣于|提高|提升|降低|下降|达到|推荐|最终|采用)"
)
NUMBER_PATTERN = re.compile(r"(?<![\d.])[-+]?\d+(?:\.\d+)?(?:%|‰)?(?![\d.])")
REF_PATTERN = re.compile(r"ref\(([^)]+)\)")
REVIEW_QUEUE_LIMIT_PER_QUESTION = 4
REVIEW_CLAIM_LIMIT_PER_QUESTION = 8


def _question_from_title(title: str) -> str | None:
    compact = re.sub(r"\s+", "", title)
    for question, patterns in QUESTION_PATTERNS.items():
        if any(re.search(pattern, compact) for pattern in patterns):
            return question
    return None


def _problem_analysis_question(number: str) -> str | None:
    """Map numbered 2.1-2.4 style analysis subsections to Q1-Q4 without semantic guessing."""
    match = re.fullmatch(r"\s*\d+\.(\d+)\s*", str(number or ""))
    if not match:
        return None
    ordinal = int(match.group(1))
    return f"Q{ordinal}" if 1 <= ordinal <= 4 else None


def _is_problem_analysis_title(title: str) -> bool:
    compact = re.sub(r"\s+", "", title)
    return bool(re.search(r"问题分析|任务分析|题目分析", compact))


def _roles(title: str, text: str) -> list[str]:
    sample = f"{title}\n{text[:800]}"
    roles = [
        role for role, patterns in ROLE_PATTERNS.items()
        if any(re.search(pattern, sample, flags=re.IGNORECASE) for pattern in patterns)
    ]
    return roles or ["GENERAL"]


def _split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[。！？!?；;])\s*|\n+", text)
    return [re.sub(r"\s+", " ", item).strip() for item in pieces if item.strip()]


def _fact_renderings(facts: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for fact in facts.get("facts", []):
        if not isinstance(fact, dict):
            continue
        renderings = [str(value) for value in fact.get("allowed_renderings", [])]
        canonical = fact.get("canonical_value")
        if canonical is not None:
            renderings.append(str(canonical))
        output.append({
            "fact_id": str(fact.get("fact_id", "UNKNOWN")),
            "question": str(fact.get("question", "")).upper(),
            "renderings": sorted(set(item for item in renderings if item)),
        })
    return output


def _rendering_in_sentence(value: str, sentence: str) -> bool:
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:%|‰)?", value):
        return bool(re.search(rf"(?<![\d.]){re.escape(value)}(?![\d.])", sentence))
    return value in sentence


def _fact_hits(sentence: str, facts: list[dict[str, Any]]) -> list[str]:
    return [
        fact["fact_id"]
        for fact in facts
        if any(_rendering_in_sentence(value, sentence) for value in fact["renderings"])
    ]


def _bounded_queue(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the queue useful for contest-time review instead of turning every number into work."""
    selected: list[dict[str, Any]] = []
    for question in ("Q1", "Q2", "Q3", "Q4"):
        items = [item for item in candidates if item.get("question_id") == question]
        items.sort(key=lambda item: (
            0 if item.get("priority") == "HIGH" else 1,
            int(item.get("source_line", 10**9)),
            int(item.get("sentence_index", 10**9)),
        ))
        selected.extend(items[:REVIEW_QUEUE_LIMIT_PER_QUESTION])
    return selected


def _representative_claims(claims_by_question: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for question in ("Q1", "Q2", "Q3", "Q4"):
        items = claims_by_question.get(question, [])
        high_value = [item for item in items if item.get("high_value")]
        if len(high_value) < REVIEW_CLAIM_LIMIT_PER_QUESTION:
            seen = {id(item) for item in high_value}
            high_value.extend(item for item in items if id(item) not in seen)
        output[question] = high_value[:REVIEW_CLAIM_LIMIT_PER_QUESTION]
    return output


def build_intelligence(main_tex: str | Path, facts_config: str | Path | None = None) -> dict[str, Any]:
    document = expand_tex_document(main_tex)
    sections = extract_sections(document)
    facts_data = load_yaml_compatible(facts_config) if facts_config and Path(facts_config).is_file() else {"facts": []}
    facts = _fact_renderings(facts_data)

    section_index: list[dict[str, Any]] = []
    active_question: str | None = None
    in_problem_analysis = False
    section_question: dict[tuple[str, int], str] = {}

    for item in sections:
        detected = _question_from_title(item["title"])
        if item["level"] == 1:
            in_problem_analysis = _is_problem_analysis_title(item["title"])
            if detected:
                active_question = detected
            elif in_problem_analysis:
                active_question = None
            elif any(role in _roles(item["title"], "") for role in ("CONCLUSION", "STRENGTHS_LIMITS")):
                active_question = None
            else:
                active_question = None

        analysis_question = (
            _problem_analysis_question(item.get("number", ""))
            if item["level"] > 1 and in_problem_analysis and not detected
            else None
        )
        question = detected or analysis_question or active_question or "GLOBAL"
        roles = _roles(item["title"], item["text"])
        entry = {
            "number": item["number"],
            "title": item["title"],
            "level": item["level"],
            "question": question,
            "roles": roles,
            "source_file": item["source_file"],
            "source_line": item["source_line"],
            "source_end_line": item["source_end_line"],
            "chinese_characters": item["chinese_characters"],
        }
        section_index.append(entry)
        section_question[(item["source_file"], item["source_line"])] = question

    claims: list[dict[str, Any]] = []
    claims_by_question: dict[str, list[dict[str, Any]]] = {"Q1": [], "Q2": [], "Q3": [], "Q4": [], "GLOBAL": []}
    queue_candidates: list[dict[str, Any]] = []

    for item in sections:
        question = section_question.get((item["source_file"], item["source_line"]), "GLOBAL")
        roles = _roles(item["title"], item["text"])
        sentences = _split_sentences(item["text"])
        previous_refs: list[str] = []

        for sentence_index, sentence in enumerate(sentences, start=1):
            numbers = NUMBER_PATTERN.findall(sentence)
            own_refs = REF_PATTERN.findall(sentence)
            if not (CLAIM_MARKERS.search(sentence) or numbers):
                previous_refs = own_refs
                continue

            local_refs = own_refs or previous_refs
            reference_scope = "sentence" if own_refs else ("previous_sentence" if previous_refs else "none")
            fact_hits = _fact_hits(sentence, facts)
            strong = bool(STRONG_CLAIM_MARKERS.search(sentence))
            high_value = bool(strong or any(role in roles for role in ("RESULTS", "ROBUSTNESS", "CONCLUSION")))

            if own_refs:
                status = "TRACEABLE_REFERENCE"
            elif previous_refs:
                status = "TRACEABLE_LOCAL_CONTEXT"
            elif fact_hits:
                status = "TRACEABLE_FROZEN_FACT"
            elif numbers:
                status = "NUMERIC_CLAIM_REVIEW_CANDIDATE"
            else:
                status = "CLAIM_REVIEW_CANDIDATE"

            claim = {
                "question": question,
                "section": item["title"],
                "section_roles": roles,
                "sentence_index": sentence_index,
                "text": sentence,
                "numbers": numbers,
                "references": local_refs,
                "reference_scope": reference_scope,
                "frozen_fact_hits": fact_hits,
                "evidence_status": status,
                "high_value": high_value,
                "source_file": item["source_file"],
                "source_line": item["source_line"],
            }
            claims.append(claim)
            claims_by_question.setdefault(question, []).append(claim)

            needs_review = (
                question in {"Q1", "Q2", "Q3", "Q4"}
                and high_value
                and not local_refs
                and not fact_hits
                and (numbers or strong)
            )
            if needs_review:
                queue_candidates.append({
                    "priority": "HIGH" if strong and numbers else "MEDIUM",
                    "source": "CLAIM_EVIDENCE_TRIAGE",
                    "location": f"{item['source_file']}:{item['source_line']}#{sentence_index}",
                    "question": (
                        f"Check whether this {question} high-value claim is already supported by a nearby table, figure, "
                        "equation, frozen fact, or reproducible model output. Do not rewrite merely to clear the queue."
                    ),
                    "claim": sentence,
                    "numbers": numbers,
                    "frozen_fact_hits": fact_hits,
                    "question_id": question,
                    "source_line": item["source_line"],
                    "sentence_index": sentence_index,
                })
            previous_refs = own_refs

    manual_queue = _bounded_queue(queue_candidates)
    review_claims_by_question = _representative_claims(claims_by_question)
    coverage = {
        question: {
            "section_count": sum(item["question"] == question for item in section_index),
            "claim_count": len(claims_by_question.get(question, [])),
            "review_claim_count": len(review_claims_by_question.get(question, [])),
            "roles": sorted({role for item in section_index if item["question"] == question for role in item["roles"]}),
        }
        for question in ("Q1", "Q2", "Q3", "Q4")
    }
    queue_summary = {
        question: sum(item.get("question_id") == question for item in manual_queue)
        for question in ("Q1", "Q2", "Q3", "Q4")
    }

    return {
        "schema_version": 2,
        "main_tex": str(Path(main_tex).resolve()),
        "section_index": section_index,
        "semantic_map": section_index,
        "question_coverage": coverage,
        "claims": claims,
        "claims_by_question": claims_by_question,
        "review_claims_by_question": review_claims_by_question,
        "manual_review_queue": manual_queue,
        "manual_review_queue_summary": queue_summary,
        "facts_configured": len(facts),
        "automation_limits": [
            "Section/question assignment is a deterministic index, not scientific understanding.",
            "Problem-analysis subsections numbered x.1-x.4 are mapped to Q1-Q4 only while inside a problem-analysis section.",
            "TRACEABLE_REFERENCE/LOCAL_CONTEXT/FROZEN_FACT means a trace exists; it does not prove evidentiary sufficiency.",
            "The manual claim queue is deliberately bounded to four items per question to avoid contest-time review overload.",
            "The full machine-readable claim list remains available even when an item is omitted from the bounded queue.",
            "Scientific correctness, causal validity, modeling appropriateness, and Chinese naturalness remain Sol/human responsibilities.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# PAPER REVIEW INDEX / CLAIM-EVIDENCE TRIAGE",
        "",
        "This report is informational triage. It is not a Gate and its queue is not a checklist to clear.",
        "",
        "## 1. Question Coverage",
        "",
        "| Question | Sections | Claims | Review Claims | Roles |",
        "|---|---:|---:|---:|---|",
    ]
    for question in ("Q1", "Q2", "Q3", "Q4"):
        item = report["question_coverage"][question]
        lines.append(
            f"| {question} | {item['section_count']} | {item['claim_count']} | {item['review_claim_count']} | "
            f"{', '.join(item['roles']) or 'NONE'} |"
        )
    lines += ["", "## 2. Deterministic Section / Question Index", "", "| Section | Question | Roles | Source |", "|---|---|---|---|"]
    for item in report["section_index"]:
        lines.append(
            f"| {item['number']} {item['title']} | {item['question']} | {', '.join(item['roles'])} | "
            f"`{item['source_file']}:{item['source_line']}-{item['source_end_line']}` |"
        )
    lines += ["", "## 3. Claim / Evidence Inventory", "", "| Q | Section | Status | Numbers | Refs | Claim |", "|---|---|---|---|---|---|"]
    for item in report["claims"]:
        claim = item["text"].replace("|", "\\|")
        lines.append(
            f"| {item['question']} | {item['section']} | {item['evidence_status']} | "
            f"{', '.join(item['numbers']) or '-'} | {', '.join(item['references']) or '-'} | {claim} |"
        )
    lines += ["", "## 4. Bounded Manual Review Queue", ""]
    if not report["manual_review_queue"]:
        lines.append("No high-value claim/evidence triage candidates.")
    else:
        for item in report["manual_review_queue"]:
            lines.append(f"- **{item['priority']}** `{item['location']}` — {item['question']}")
            lines.append(f"  - claim: {item['claim']}")
    lines += ["", "## 5. Automation Limits", ""]
    lines.extend(f"- {item}" for item in report["automation_limits"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--main-tex", required=True)
    parser.add_argument("--facts-config")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()
    try:
        workspace = Path(args.workspace).resolve()
        output_json = Path(args.output_json).resolve() if args.output_json else workspace / "reports" / "paper_intelligence.json"
        output_md = Path(args.output_md).resolve() if args.output_md else workspace / "reports" / "paper_intelligence.md"
        report = build_intelligence(args.main_tex, args.facts_config)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(report), encoding="utf-8")
        print(str(output_json))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"PAPER_INTELLIGENCE_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""Deterministic Chinese prose lint with bibliography and non-prose exclusions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from paper_gate_common import chinese_char_count, compact_evidence, finding, load_yaml_compatible, read_text, summarize, write_report
from paper_tex_extract import extract_readable_prose_document


NON_BODY_LINE = re.compile(
    r"(?mi)^\s*(?:AI\s*工具使用声明|参考文献|References|Bibliography|(?:[A-Z]\s+)?附录(?:\s+[^\n]*)?|Appendix(?:\s+[^\n]*)?)\s*$"
)


def _body_only(text: str) -> str:
    boundary = NON_BODY_LINE.search(text)
    return text[: boundary.start()] if boundary else text


def _pdf_length_prose(text: str) -> str:
    lines: list[str] = []
    for line in _body_only(text).splitlines():
        stripped = line.strip()
        if re.match(r"^(?:图|表|Figure|Table)\s*\d+\s*[:：.]", stripped, flags=re.IGNORECASE):
            continue
        number_tokens = re.findall(r"[-+]?\d+(?:\.\d+)?", stripped)
        if len(number_tokens) >= 4 and chinese_char_count(stripped) < 8:
            continue
        lines.append(line)
    return "\n".join(lines)


def _paragraphs(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", item).strip() for item in re.split(r"(?:\r?\n\s*){2,}", text) if item.strip()]


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[。！？!?；;])\s*", re.sub(r"\s+", " ", text)) if item.strip()]


def lint_language(text: str, config: dict[str, Any], source_text: str = "") -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    body_text = _body_only(text)
    for rule in config.get("literal_rules", []):
        pattern = str(rule["pattern"]) if rule.get("regex") else re.escape(str(rule["pattern"]))
        for hit in re.finditer(pattern, body_text, flags=re.MULTILINE | re.DOTALL):
            findings.append(finding(
                str(rule["level"]), str(rule["id"]), str(rule["message"]),
                evidence=compact_evidence(body_text, hit.start(), hit.end()),
            ))

    prose = extract_readable_prose_document(source_text) if source_text else _pdf_length_prose(body_text)
    metrics = config.get("metrics", {})
    han_count = chinese_char_count(prose)
    units = max(han_count / 500.0, 1.0)
    opening_parentheses = len(re.findall(r"[（(]", prose))
    parentheses_limit = float(metrics.get("parentheses_per_500_chinese_warning", 12)) * units
    if opening_parentheses > parentheses_limit:
        findings.append(finding(
            "WARNING", "PARENTHESES_DENSITY",
            f"Parentheses density is {opening_parentheses / units:.1f} per 500 Chinese characters (limit {metrics.get('parentheses_per_500_chinese_warning', 12)})."
        ))
    dash_count = len(re.findall(r"——|—", prose))
    dash_limit = float(metrics.get("dashes_per_500_chinese_warning", 4)) * units
    if dash_count > dash_limit:
        findings.append(finding(
            "WARNING", "DASH_DENSITY",
            f"Dash density is {dash_count / units:.1f} per 500 Chinese characters (limit {metrics.get('dashes_per_500_chinese_warning', 4)})."
        ))

    paragraphs = _paragraphs(prose)
    paragraph_limit = int(metrics.get("paragraph_max_chars_warning", 800))
    for index, paragraph in enumerate(paragraphs, start=1):
        if len(paragraph) > paragraph_limit:
            findings.append(finding(
                "WARNING", "PARAGRAPH_TOO_LONG", f"Paragraph {index} has {len(paragraph)} characters (limit {paragraph_limit}).", location=f"paragraph:{index}"
            ))
    benwen_limit = int(metrics.get("consecutive_benwen_paragraphs_warning", 3))
    for index in range(max(0, len(paragraphs) - benwen_limit + 1)):
        window = paragraphs[index:index + benwen_limit]
        if len(window) == benwen_limit and all(item.startswith("本文") for item in window):
            findings.append(finding(
                "WARNING", "CONSECUTIVE_BENWEN_OPENINGS", f"Paragraphs {index + 1}-{index + benwen_limit} all begin with '本文'.", location=f"paragraph:{index + 1}"
            ))

    sentences = _sentences(prose)
    sentence_limit = int(metrics.get("sentence_max_chars_warning", 180))
    strong_limit = int(metrics.get("sentence_max_chars_strong_warning", 260))
    for index, sentence in enumerate(sentences, start=1):
        if len(sentence) > strong_limit:
            findings.append(finding(
                "WARNING", "SENTENCE_TOO_LONG_STRONG_WARNING",
                f"STRONG WARNING: sentence {index} has {len(sentence)} characters (strong limit {strong_limit}).",
                location=f"sentence:{index}",
            ))
        elif len(sentence) > sentence_limit:
            findings.append(finding(
                "WARNING", "SENTENCE_TOO_LONG", f"Sentence {index} has {len(sentence)} characters (limit {sentence_limit}).", location=f"sentence:{index}"
            ))
    connectors = tuple(str(item) for item in metrics.get("connectors", ["因此", "说明", "表明"]))
    connector_limit = int(metrics.get("consecutive_connector_sentences_warning", 3))
    for index in range(max(0, len(sentences) - connector_limit + 1)):
        window = sentences[index:index + connector_limit]
        if len(window) == connector_limit and all(any(token in sentence for token in connectors) for sentence in window):
            findings.append(finding(
                "WARNING", "CONSECUTIVE_CONNECTOR_SENTENCES",
                f"Sentences {index + 1}-{index + connector_limit} repeatedly use therefore/indicates connectors.",
                location=f"sentence:{index + 1}",
            ))

    return summarize(
        "paper_language", findings,
        metrics={"chinese_characters": han_count, "paragraphs": len(paragraphs), "sentences": len(sentences), "length_source": "latex_source" if source_text else "pdf_text"},
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--source")
    parser.add_argument("--config", default=str(repo_root / "config" / "paper_language_rules.yaml"))
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        report = lint_language(
            read_text(args.text), load_yaml_compatible(args.config), read_text(args.source) if args.source else ""
        )
    except (OSError, ValueError, re.error) as exc:
        report = summarize("paper_language", [finding("ERROR", "LANGUAGE_CHECKER_CONFIGURATION", str(exc))])
    write_report(report, args.output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

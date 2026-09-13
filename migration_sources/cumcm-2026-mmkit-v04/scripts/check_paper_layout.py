"""Inspect Poppler bbox output and LaTeX source for deterministic layout defects."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from paper_gate_common import finding, load_yaml_compatible, read_text, summarize, write_report
from paper_tex_extract import TexDocument, extract_figures, extract_section_titles, extract_tables


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _float(element: ET.Element, name: str, default: float = 0.0) -> float:
    try:
        return float(element.attrib.get(name, default))
    except ValueError:
        return default


def _extract_pages(bbox_path: str | Path) -> list[dict[str, Any]]:
    root = ET.parse(bbox_path).getroot()
    pages: list[dict[str, Any]] = []
    for page_no, page in enumerate((item for item in root.iter() if _tag(item) == "page"), start=1):
        words = []
        images = []
        for item in page.iter():
            tag = _tag(item)
            if tag == "word":
                words.append({
                    "text": "".join(item.itertext()).strip(),
                    "x_min": _float(item, "xMin"),
                    "y_min": _float(item, "yMin"),
                    "x_max": _float(item, "xMax"),
                    "y_max": _float(item, "yMax"),
                })
            elif tag == "image":
                images.append({
                    "x_min": _float(item, "xMin"), "y_min": _float(item, "yMin"),
                    "x_max": _float(item, "xMax"), "y_max": _float(item, "yMax"),
                })
        lines: list[dict[str, Any]] = []
        for word in sorted(words, key=lambda item: (item["y_min"], item["x_min"])):
            line = next((candidate for candidate in reversed(lines[-3:]) if abs(candidate["y_min"] - word["y_min"]) <= 2.5), None)
            if line is None:
                line = {"words": [], "y_min": word["y_min"], "y_max": word["y_max"]}
                lines.append(line)
            line["words"].append(word)
            line["y_max"] = max(line["y_max"], word["y_max"])
        for line in lines:
            line["words"].sort(key=lambda item: item["x_min"])
            line["text"] = "".join(item["text"] for item in line["words"])
        pages.append({
            "page": page_no,
            "width": _float(page, "width"),
            "height": _float(page, "height"),
            "words": words,
            "images": images,
            "lines": lines,
        })
    return pages


def _heading_names(section_config: dict[str, Any]) -> set[str]:
    return {re.sub(r"\s+", "", str(name)) for section in section_config.get("sections", []) for name in section.get("headings", [])}


def _looks_like_heading(text: str, known: set[str]) -> bool:
    compact = re.sub(r"\s+", "", text)
    without_number = re.sub(r"^\d+(?:\.\d+)*", "", compact)
    if without_number in known:
        return True
    return bool(
        re.fullmatch(r"第[一二三四五六七八九十0-9]+[章节]\S{0,24}", compact)
        or re.fullmatch(r"\d+(?:\.\d+)+[\u3400-\u9fffA-Za-z]\S{0,24}", compact)
    )


def _number_gaps(numbers: list[int]) -> list[tuple[int, int]]:
    numbers = sorted(set(numbers))
    return [(left, right) for left, right in zip(numbers, numbers[1:]) if right != left + 1]


def _check_latex_figures(source: str, config: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    latex_config = config.get("latex", {})
    document = TexDocument.from_text(source)
    figures = extract_figures(document)
    for item in figures:
        index = item["number"]
        if item["dynamic"]:
            findings.append(finding(
                "WARNING", "FIGURE_DYNAMIC_MACRO", f"Figure environment {index} contains dynamic macro arguments; label/reference coverage cannot be determined statically.", location=f"figure:{index}"
            ))
            continue
        label = item["label"]
        if latex_config.get("require_figure_labels", True) and label == "UNKNOWN":
            findings.append(finding("ERROR", "FIGURE_LABEL_MISSING", f"Figure environment {index} has an image but no label.", location=f"figure:{index}"))
        elif latex_config.get("require_figure_references", True) and not item["referenced"]:
            findings.append(finding("ERROR", "FIGURE_UNREFERENCED", f"Figure label '{label}' is never referenced in the paper body.", location=f"figure:{index}"))
    source_without_figures = re.sub(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", " ", source, flags=re.DOTALL)
    outside_count = len(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{[^}]+\}", source_without_figures))
    if outside_count > 0:
        findings.append(finding("WARNING", "IMAGE_OUTSIDE_FIGURE", f"Found {outside_count} includegraphics command(s) outside a figure environment; reference coverage cannot be proven."))
    return findings


def _check_latex_tables(source: str) -> tuple[list[dict[str, str]], int]:
    """Use only real table environments; LaTeX numbering itself is contiguous."""

    findings: list[dict[str, str]] = []
    environments = extract_tables(TexDocument.from_text(source))
    count = 0
    for item in environments:
        index = item["number"]
        if item["dynamic"]:
            findings.append(finding(
                "WARNING", "TABLE_DYNAMIC_MACRO", f"Table environment {index} contains dynamic macro arguments; numbering cannot be determined statically.", location=f"table:{index}"
            ))
            continue
        if item["caption"] != "UNKNOWN":
            count += 1
        else:
            findings.append(finding("WARNING", "TABLE_CAPTION_MISSING", f"Table environment {index} has no static caption.", location=f"table:{index}"))
        if item["label"] == "UNKNOWN":
            findings.append(finding("WARNING", "TABLE_LABEL_MISSING", f"Table environment {index} has no static label.", location=f"table:{index}"))
    return findings, count


def _fallback_caption_numbers(pages: list[dict[str, Any]], kind: str) -> list[int]:
    prefix = r"表" if kind == "TABLE" else r"图"
    english = r"Table" if kind == "TABLE" else r"Figure"
    pattern = re.compile(rf"^\s*(?:{prefix}|{english})\s*(\d+)(?=\s*[:：.]|\s+\D|[^\d])", flags=re.IGNORECASE)
    numbers: list[int] = []
    for page in pages:
        for line in page["lines"]:
            match = pattern.match(line["text"])
            if match:
                numbers.append(int(match.group(1)))
    return numbers


def check_layout(
    bbox_path: str | Path,
    config: dict[str, Any],
    section_config: dict[str, Any],
    *,
    pdfinfo_text: str = "",
    source_text: str = "",
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    pages = _extract_pages(bbox_path)
    page_config = config.get("page", {})
    orphan = config.get("orphan_heading", {})
    captions = config.get("captions", {})
    known_headings = _heading_names(section_config)
    if source_text:
        known_headings.update(re.sub(r"\s+", "", item) for item in extract_section_titles(source_text))

    for page in pages:
        words = page["words"]
        if not words and not page["images"]:
            level = "ERROR" if page_config.get("blank_page_is_error", True) else "WARNING"
            findings.append(finding(level, "BLANK_PAGE", f"Page {page['page']} contains no text or image objects.", location=f"page:{page['page']}"))
            continue
        if words and page["height"] > 0:
            top = min(word["y_min"] for word in words)
            bottom = max(word["y_max"] for word in words)
            blank_ratio = max(0.0, 1.0 - ((bottom - top) / page["height"]))
            if blank_ratio > float(page_config.get("abnormal_blank_ratio_warning", 0.72)):
                findings.append(finding("WARNING", "ABNORMAL_PAGE_WHITESPACE", f"Page {page['page']} estimated blank vertical ratio is {blank_ratio:.2f}.", location=f"page:{page['page']}"))

        for line_index, line in enumerate(page["lines"]):
            if _looks_like_heading(line["text"], known_headings) and page["height"] > 0:
                ratio = line["y_min"] / page["height"]
                following = sum(len(candidate["words"]) for candidate in page["lines"][line_index + 1 :])
                if ratio >= float(orphan.get("bottom_ratio", 0.78)) and following < int(orphan.get("minimum_following_words", 8)):
                    findings.append(finding(
                        "ERROR", "ORPHAN_HEADING", f"Heading '{line['text']}' is orphaned at the bottom of page {page['page']} ({following} following words).", location=f"page:{page['page']}"
                    ))
            if re.search(str(captions.get("figure_pattern", r"图\s*(\d+)")), line["text"]) and page["height"] > 0:
                caption_ratio = line["y_min"] / page["height"]
                if caption_ratio >= float(captions.get("bottom_ratio_warning", 0.90)):
                    findings.append(finding("WARNING", "FIGURE_CAPTION_AT_PAGE_BOTTOM", f"Figure caption '{line['text']}' is at the page bottom; inspect image/caption continuity.", location=f"page:{page['page']}"))
                elif caption_ratio <= float(captions.get("top_ratio_warning", 0.08)):
                    findings.append(finding("WARNING", "FIGURE_CAPTION_AT_PAGE_TOP", f"Figure caption '{line['text']}' is at the page top; inspect whether its image stayed on the previous page.", location=f"page:{page['page']}"))

    if source_text:
        table_findings, source_table_count = _check_latex_tables(source_text)
        findings.extend(table_findings)
    else:
        source_table_count = 0
        for kind in ("FIGURE", "TABLE"):
            for left, right in _number_gaps(_fallback_caption_numbers(pages, kind)):
                findings.append(finding("ERROR", f"{kind}_NUMBERING_GAP", f"{kind.title()} numbering jumps from {left} to {right}."))

    page_count = len(pages)
    pdfinfo_match = re.search(r"(?mi)^Pages:\s*(\d+)\s*$", pdfinfo_text)
    if pdfinfo_match and int(pdfinfo_match.group(1)) != page_count:
        findings.append(finding("ERROR", "PAGE_COUNT_MISMATCH", f"pdfinfo reports {pdfinfo_match.group(1)} pages but bbox contains {page_count}."))
    minimum = int(page_config.get("expected_body_pages_min", 1))
    maximum = int(page_config.get("expected_body_pages_max", 40))
    if not minimum <= page_count <= maximum:
        findings.append(finding("WARNING", "BODY_PAGE_COUNT_OUTSIDE_EXPECTED", f"PDF contains {page_count} pages; expected range is {minimum}-{maximum}."))

    if source_text:
        findings.extend(_check_latex_figures(source_text, config))
    return summarize("paper_layout", findings, page_count=page_count, source_table_count=source_table_count)


def _generate_poppler_inputs(pdf: Path, pdfinfo: str, pdftotext: str) -> tuple[Path, str, tempfile.TemporaryDirectory[str]]:
    temporary = tempfile.TemporaryDirectory(prefix="paper-gate-layout-")
    bbox = Path(temporary.name) / "paper.bbox.html"
    info_result = subprocess.run([pdfinfo, str(pdf)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if info_result.returncode != 0:
        temporary.cleanup()
        raise OSError(f"pdfinfo failed with exit code {info_result.returncode}: {info_result.stderr.strip()}")
    bbox_result = subprocess.run([pdftotext, "-bbox", str(pdf), str(bbox)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if bbox_result.returncode != 0:
        temporary.cleanup()
        raise OSError(f"pdftotext -bbox failed with exit code {bbox_result.returncode}: {bbox_result.stderr.strip()}")
    return bbox, info_result.stdout, temporary


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--pdf")
    source_group.add_argument("--bbox")
    parser.add_argument("--pdfinfo-text")
    parser.add_argument("--source")
    parser.add_argument("--config", default=str(repo_root / "config" / "figure_contracts.yaml"))
    parser.add_argument("--sections-config", default=str(repo_root / "config" / "paper_sections.yaml"))
    parser.add_argument("--pdfinfo-command", default="pdfinfo")
    parser.add_argument("--pdftotext-command", default="pdftotext")
    parser.add_argument("--output")
    args = parser.parse_args()
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.pdf:
            bbox_path, pdfinfo_text, temporary = _generate_poppler_inputs(Path(args.pdf), args.pdfinfo_command, args.pdftotext_command)
        else:
            bbox_path = Path(args.bbox)
            pdfinfo_text = read_text(args.pdfinfo_text) if args.pdfinfo_text else ""
        report = check_layout(
            bbox_path,
            load_yaml_compatible(args.config),
            load_yaml_compatible(args.sections_config),
            pdfinfo_text=pdfinfo_text,
            source_text=read_text(args.source) if args.source else "",
        )
    except (OSError, ValueError, ET.ParseError, re.error) as exc:
        report = summarize("paper_layout", [finding("ERROR", "LAYOUT_CHECKER_INPUT", str(exc))])
    finally:
        if temporary is not None:
            temporary.cleanup()
    write_report(report, args.output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

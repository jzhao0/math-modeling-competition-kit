"""Render paper pages and produce deterministic page-level visual-review heuristics."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _float(element: ET.Element, name: str, default: float = 0.0) -> float:
    try:
        return float(element.attrib.get(name, default))
    except ValueError:
        return default


def extract_pages(bbox_path: str | Path) -> list[dict[str, Any]]:
    root = ET.parse(bbox_path).getroot()
    pages: list[dict[str, Any]] = []
    for page_no, page in enumerate((x for x in root.iter() if _tag(x) == "page"), start=1):
        words: list[dict[str, float | str]] = []
        images: list[dict[str, float]] = []
        for item in page.iter():
            if _tag(item) == "word":
                words.append({
                    "text": "".join(item.itertext()).strip(),
                    "x_min": _float(item, "xMin"), "y_min": _float(item, "yMin"),
                    "x_max": _float(item, "xMax"), "y_max": _float(item, "yMax"),
                })
            elif _tag(item) == "image":
                images.append({
                    "x_min": _float(item, "xMin"), "y_min": _float(item, "yMin"),
                    "x_max": _float(item, "xMax"), "y_max": _float(item, "yMax"),
                })
        lines: list[float] = []
        for word in sorted(words, key=lambda x: (float(x["y_min"]), float(x["x_min"]))):
            y = float(word["y_min"])
            if not lines or min(abs(y - old) for old in lines[-3:]) > 2.5:
                lines.append(y)
        pages.append({"page": page_no, "width": _float(page, "width"), "height": _float(page, "height"), "words": words, "images": images, "line_count": len(lines)})
    return pages


def analyze_pages(pages: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    page_reports: list[dict[str, Any]] = []
    for page in pages:
        width = page["width"] or 1.0
        height = page["height"] or 1.0
        words = page["words"]
        images = page["images"]
        word_count = len(words)
        line_count = page["line_count"]
        if words:
            left = min(float(item["x_min"]) for item in words)
            right = max(float(item["x_max"]) for item in words)
            top = min(float(item["y_min"]) for item in words)
            bottom = max(float(item["y_max"]) for item in words)
            horizontal_span = (right - left) / width
            vertical_span = (bottom - top) / height
            edge_min = min(left / width, (width - right) / width, top / height, (height - bottom) / height)
        else:
            horizontal_span = vertical_span = edge_min = 0.0
        image_metrics = []
        for image in images:
            iw = max(0.0, image["x_max"] - image["x_min"]) / width
            ih = max(0.0, image["y_max"] - image["y_min"]) / height
            image_metrics.append({"width_ratio": round(iw, 4), "height_ratio": round(ih, 4), "area_ratio": round(iw * ih, 4)})
        flags: list[str] = []
        if page["page"] > 1 and word_count < 35 and not images:
            flags.append("VERY_SPARSE_PAGE")
        if word_count > 850 or line_count > 72:
            flags.append("DENSE_PAGE")
        if words and edge_min < 0.01:
            flags.append("CONTENT_NEAR_PAGE_EDGE")
        if any(item["width_ratio"] < 0.25 or item["area_ratio"] < 0.025 for item in image_metrics):
            flags.append("SMALL_RENDERED_IMAGE")
        if any(item["width_ratio"] > 0.96 or item["height_ratio"] > 0.90 for item in image_metrics):
            flags.append("OVERSIZED_RENDERED_IMAGE")
        messages = {
            "VERY_SPARSE_PAGE": "Page has very little text and no image; inspect unintended whitespace or pagination.",
            "DENSE_PAGE": "Page is unusually dense; inspect font size, readability, and crowding.",
            "CONTENT_NEAR_PAGE_EDGE": "Rendered content approaches a page edge; inspect clipping/margin violations.",
            "SMALL_RENDERED_IMAGE": "At least one rendered image occupies a small fraction of the page; inspect readability.",
            "OVERSIZED_RENDERED_IMAGE": "At least one rendered image nearly fills the page; inspect clipping and caption continuity.",
        }
        for code in flags:
            findings.append({"level": "WARNING", "code": code, "page": page["page"], "location": f"page:{page['page']}", "message": messages[code]})
        page_reports.append({
            "page": page["page"], "word_count": word_count, "line_count": line_count,
            "image_count": len(images), "horizontal_text_span_ratio": round(horizontal_span, 4),
            "vertical_text_span_ratio": round(vertical_span, 4), "minimum_edge_margin_ratio": round(edge_min, 4),
            "images": image_metrics, "flags": flags,
        })
    return {
        "schema_version": 1, "page_count": len(pages), "pages": page_reports,
        "findings": findings, "warning_count": len(findings),
        "automation_limits": [
            "Heuristics detect geometry anomalies, not visual aesthetics.",
            "Rendered PNGs are for human/Sol inspection; no OCR or image-quality model is used.",
            "Color, typography harmony, chart semantics, and scientific adequacy remain manual-review tasks.",
        ],
    }


def render_pages(pdf: Path, render_dir: Path, command: str = "pdftoppm") -> dict[str, Any]:
    executable = shutil.which(command) or (command if Path(command).is_file() else None)
    if not executable or not pdf.is_file():
        return {"status": "UNAVAILABLE", "pages": []}
    render_dir.mkdir(parents=True, exist_ok=True)
    prefix = render_dir / "page"
    result = subprocess.run([str(executable), "-png", "-r", "120", str(pdf), str(prefix)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    page_paths = list(render_dir.glob("page-*.png"))
    page_paths.sort(key=lambda path: int(re.search(r"-(\d+)$", path.stem).group(1)) if re.search(r"-(\d+)$", path.stem) else 10**9)
    pages = [str(path) for path in page_paths]
    return {"status": "OK" if result.returncode == 0 else "FAILED", "exit_code": result.returncode, "stderr": result.stderr.strip()[:500], "pages": pages}


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# PAPER PDF VISUAL REVIEW", "", f"- page_count: {report['page_count']}", f"- render_status: {report['render']['status']}", f"- warning_count: {report['warning_count']}", "", "## Page Review", "", "| Page | Words | Lines | Images | Flags | Render |", "|---:|---:|---:|---:|---|---|"]
    render_pages_list = report["render"].get("pages", [])
    for item in report["pages"]:
        render_path = next((path for path in render_pages_list if (m := re.search(r"-(\d+)$", Path(path).stem)) and int(m.group(1)) == item["page"]), "")
        render_cell = f"`{render_path}`" if render_path else "UNAVAILABLE"
        lines.append(f"| {item['page']} | {item['word_count']} | {item['line_count']} | {item['image_count']} | {', '.join(item['flags']) or 'PASS'} | {render_cell} |")
    lines += ["", "## Findings", ""]
    if not report["findings"]:
        lines.append("No deterministic geometry warnings.")
    else:
        for item in report["findings"]:
            lines.append(f"- **{item['code']}** `{item['location']}` — {item['message']}")
    lines += ["", "## Automation Limits", ""]
    lines.extend(f"- {item}" for item in report["automation_limits"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--bbox", required=True)
    parser.add_argument("--pdf")
    parser.add_argument("--render-dir")
    parser.add_argument("--pdftoppm-command", default="pdftoppm")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()
    try:
        workspace = Path(args.workspace).resolve()
        report = analyze_pages(extract_pages(args.bbox))
        render_dir = Path(args.render_dir).resolve() if args.render_dir else workspace / "reports" / "visual_review" / "pages"
        report["render"] = render_pages(Path(args.pdf).resolve(), render_dir, args.pdftoppm_command) if args.pdf else {"status": "UNAVAILABLE", "pages": []}
        output_json = Path(args.output_json).resolve() if args.output_json else workspace / "reports" / "paper_visual_review.json"
        output_md = Path(args.output_md).resolve() if args.output_md else workspace / "reports" / "paper_visual_review.md"
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(report), encoding="utf-8")
        print(str(output_json))
        return 0
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"PAPER_VISUAL_REVIEW_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

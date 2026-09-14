#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_paper_density.py - GUIDANCE density audit for a LaTeX paper (MMKit v0.2 P1).

Reports per section (approximate): equation count, figure count, table count,
visual-anchor density, long text-only spans, model-evaluation balance,
placeholder citations, engineering-identifier leakage. Uses config/paper_quality.yaml
targets via a minimal key extraction (no PyYAML dependency).
Exit 0 always (guidance report); no hard-fail by design.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / "config" / "paper_quality.yaml"

def read_policy() -> dict:
    out = {"anchor_range": "1.0-1.5", "adv": "0.67-0.75", "lim": "0.25-0.33"}
    if not POLICY.exists(): return out
    for line in POLICY.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("target_visual_anchor_every_pages:") and "\"" in s:
            out["anchor_range"] = s.split("\"")[1]
        if s.startswith("advantages_share_target:") and "\"" in s:
            out["adv"] = s.split("\"")[1]
        if s.startswith("limitations_share_target:") and "\"" in s:
            out["lim"] = s.split("\"")[1]
    return out

SEC_RE = re.compile(r"\\(?:sub)*section\\{(.*?)\\}")
EQ_ENV = ("equation", "align", "eqnarray", "gather", "multline")

def parse_sections(text: str):
    """Split into sections [(name, body)]; first unnamed = Preamble/root."""
    marks = [(m.start(), m.group(1)) for m in SEC_RE.finditer(text)]
    secs = []
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        secs.append((name, text[pos:end]))
    if not secs: secs = [("root", text)]
    return secs

def count_eq(body: str) -> int:
    n = 0
    for env in EQ_ENV: n += len(re.findall(r"\\begin\{" + env + r"\}", body))
    n += len(re.findall(r"\$\$", body)) // 2
    n += len(re.findall(r"\\\[[^\n]+\\\]", body))
    return n

def count_figs(body: str) -> int:
    return len(re.findall(r"\\begin\{figure(?:\*)?\}", body)) + len(re.findall(r"\\includegraphics", body))

def count_tables(body: str) -> int:
    return len(re.findall(r"\\begin\{table(?:\*)?\}", body)) + len(re.findall(r"\\begin\{tabular(?:\*)?\}", body))

def long_spans(body: str, min_lines: int = 12) -> int:
    """Count runs of >= min_lines consecutive text lines without an anchor."""
    run = 0; spans = 0
    anchor = re.compile(r"(?:\\includegraphics|\\begin\{figure|\\begin\{table|\\begin\{equation|\\begin\{align)")
    for line in body.splitlines():
        if anchor.search(line):
            if run >= min_lines: spans += 1
            run = 0
        else:
            s = line.strip()
            if s and not s.startswith("%"): run += 1
    if run >= min_lines: spans += 1
    return spans

def eval_balance(body: str) -> dict:
    """Heuristic: count advantage vs limitation keyword sentences in eval regions."""
    adv_kw = ("优点","优势","忠实","可解释","可复现","稳健","不确定性","增益","baseline","提升")
    lim_kw = ("局限","不足","假设","边界","数据限制","样本","风险","难以","无法验证","成本","缺点")
    sentences = [s for s in re.split(r"(?<=[。；;.!?])\s*", body) if len(s.strip()) > 20]
    adv = sum(1 for s in sentences if any(k in s for k in adv_kw))
    lim = sum(1 for s in sentences if any(k in s for k in lim_kw))
    total = adv + lim
    return {"advantage_sentences": adv, "limitation_sentences": lim,
            "adv_share": round(adv / total, 3) if total else None}

def audit(tex: Path) -> dict:
    text = tex.read_text(encoding="utf-8", errors="replace")
    policy = read_policy()
    secs = parse_sections(text)
    report = {"file": str(tex), "policy": policy, "sections": []}
    total_anchor = 0
    for name, body in secs:
        figs = count_figs(body); tbs = count_tables(body); eqs = count_eq(body)
        anchors = figs + tbs + eqs
        total_anchor += anchors
        report["sections"].append({
            "section": name[:60], "equations": eqs, "figures": figs,
            "tables": tbs, "anchors": anchors,
            "long_text_spans": long_spans(body),
            "eval_balance": eval_balance(body) if any(k in name for k in ("评价","模型评价","优缺","evaluation","结果分析","discussion")) else None,
        })
    # global checks
    placeholders = re.findall(r"(?:\\cite\{[^}]*\\?[^}]*\}|\[\?\]|待[补填]|\?\?)", text)
    leak = [m for m in re.findall(r"[A-Z]:\\\\|/home/|\\.venv|vendor/|r_toolbox|reports/|tmp", text) if m]
    report["global"] = {
        "placeholder_references": placeholders[:20],
        "engineering_identifier_hits": leak[:20],
        "anchor_note": "TARGET (modeling/result regions only): about 1 meaningful visual anchor per 1.0-1.5 pages; abstract/references/assumptions/conclusion may deviate (see docs/PAPER_SCIENTIFIC_DENSITY.md)",
    }
    return report

def main() -> int:
    ap = argparse.ArgumentParser(description="Paper density audit (guidance)")
    ap.add_argument("tex", help="LaTeX main.tex path")
    ap.add_argument("-j", "--json", help="write report JSON to path")
    a = ap.parse_args()
    rep = audit(Path(a.tex))
    print("DENSITY_AUDIT guidance report for:", rep["file"])
    for s in rep["sections"]:
        print(f"  [{s['section']}] eq={s['equations']} fig={s['figures']} tab={s['tables']} anchors={s['anchors']} long_spans={s['long_text_spans']}")
    g = rep["global"]
    print("  placeholder refs:", len(g["placeholder_references"]), "| identifier leaks:", len(g["engineering_identifier_hits"]))
    print("  TARGET:", g["anchor_note"])
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    sys.exit(main())

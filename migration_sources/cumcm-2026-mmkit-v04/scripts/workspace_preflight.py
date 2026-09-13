#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify an MMKit v0.3 workspace scaffold.

Checks scaffold/inheritance state only; does not run solvers or render figures.
Exit 0 = pass, 1 = fail. -j writes JSON report.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REQUIRED_DIRS = [
    "00_problem", "01_data_raw", "02_data_processed", "03_analysis",
    "04_models", "04_models/r", "05_results", "05_results/tables",
    "05_results/figures", "06_paper", "07_scripts", "07_supporting",
    "08_ai_logs", "09_references", "09_submission", "human_gates",
    "config", "FINAL",
]
REQUIRED_FILES = [
    "STATUS.yaml", "ASSUMPTION_LEDGER.md", "DECISION_LOG.md",
    "CLAIM_EVIDENCE.csv", "README_WORKSPACE.md",
    "03_analysis/METHOD_ROUTE.md", "03_analysis/FIGURE_PLAN.md",
    "03_analysis/CLAIM_REGISTER.md", "03_analysis/PAPER_PLAN.md",
    "03_analysis/PAPER_HUMAN_REVIEW.md",
    "09_references/REFERENCE_LEDGER.csv", "09_references/references.bib",
    "09_references/README.md",
    "08_ai_logs/ai_calls.jsonl", "08_ai_logs/README.md",
    "07_scripts/run_r_model.ps1", "07_scripts/README.md",
    "04_models/r/README.md",
    "config/method_router.yaml", "config/paper_quality.yaml",
    "config/figure_quality.yaml", "config/contest_visual.yaml",
    "config/skill_routing_snapshot.yaml",
    "06_paper/main.tex",
    "09_submission/README.md", "09_submission/SUBMISSION_MANIFEST.md",
    "FINAL/README_DEPRECATED.md",
]
GATE_NAMES = ["G1_problem_choice", "G2_model_route", "G3_results", "G4_submission"]
CLAIM_HEADER = ["claim_id", "claim", "evidence_path", "code_or_method", "status"]
LEDGER_HEADER = [
    "key", "title", "authors", "year", "venue", "doi", "url",
    "discovered_via", "metadata_verified", "publisher_verified",
    "relevance", "used_in_claims", "notes",
]
LEAK_PATTERNS = [
    r"7\s*\+\s*3\s*=\s*10", r"drill\s*0?2",
    r"cameroon|开普敦|pollutant|臭氧|湖泊水|垃圾量",
]


def check(ws: Path) -> dict:
    ok = True
    issues: list[str] = []

    def fail(msg: str) -> None:
        nonlocal ok
        ok = False
        issues.append(msg)

    for d in REQUIRED_DIRS:
        if not (ws / d).is_dir():
            fail(f"missing dir: {d}")
    for f in REQUIRED_FILES:
        if not (ws / f).is_file():
            fail(f"missing file: {f}")

    for g in GATE_NAMES:
        p = ws / f"human_gates/{g}.md"
        if p.is_file() and "APPROVED: NO" not in p.read_text(encoding="utf-8", errors="replace"):
            fail(f"gate {g} not default APPROVED: NO")

    claim = ws / "CLAIM_EVIDENCE.csv"
    if claim.is_file():
        with open(claim, encoding="utf-8") as fh:
            header = next(csv.reader(fh))
        if header != CLAIM_HEADER:
            fail(f"CLAIM_EVIDENCE header mismatch: {header}")
        else:
            with open(claim, encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            if rows:
                fail(f"CLAIM_EVIDENCE not empty ({len(rows)} rows) - fabricated content not allowed")

    led = ws / "09_references/REFERENCE_LEDGER.csv"
    if led.is_file():
        with open(led, encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            hdr = rd.fieldnames
            rows = list(rd)
        if hdr != LEDGER_HEADER:
            fail(f"REFERENCE_LEDGER header mismatch: {hdr}")
        elif rows:
            fail(f"REFERENCE_LEDGER not empty ({len(rows)} rows) - no fake references")

    ai = ws / "08_ai_logs/ai_calls.jsonl"
    if ai.is_file() and ai.read_text(encoding="utf-8", errors="replace").strip():
        fail("AI log not empty")

    mr = ws / "03_analysis/METHOD_ROUTE.md"
    if mr.is_file() and "NOT_DECIDED" not in mr.read_text(encoding="utf-8"):
        fail("METHOD_ROUTE not NOT_DECIDED")

    status = ws / "STATUS.yaml"
    if status.is_file():
        txt = status.read_text(encoding="utf-8", errors="replace")
        if "canonical_submission_dir: 09_submission" not in txt:
            fail("STATUS missing canonical_submission_dir: 09_submission")

    paper = ws / "06_paper/main.tex"
    if paper.is_file():
        txt = paper.read_text(encoding="utf-8", errors="replace")
        if "\\hypersetup{hidelinks}" not in txt:
            fail("paper skeleton missing hidden hyperlink-border default")
        if "\\pagestyle{plain}" not in txt:
            fail("paper skeleton missing plain/footer page style")

    visual = ws / "config/contest_visual.yaml"
    if visual.is_file():
        txt = visual.read_text(encoding="utf-8", errors="replace")
        for marker in (
            "competition_visual_impact: optimize",
            "PRESENTATION_3D:",
            "do_not_label_visual_depth_as_measured_variable",
        ):
            if marker not in txt:
                fail(f"contest visual policy missing marker: {marker}")

    fig_plan = ws / "03_analysis/FIGURE_PLAN.md"
    if fig_plan.is_file():
        txt = fig_plan.read_text(encoding="utf-8", errors="replace")
        if "SHOWCASE_PRESENTATION" not in txt or "PRESENTATION_3D" not in txt:
            fail("FIGURE_PLAN missing showcase/presentation-3D contract")

    human_review = ws / "03_analysis/PAPER_HUMAN_REVIEW.md"
    if human_review.is_file():
        txt = human_review.read_text(encoding="utf-8", errors="replace")
        if "audit_human_paper.py" not in txt:
            fail("PAPER_HUMAN_REVIEW missing central human-paper audit step")

    dep = ws / "FINAL/README_DEPRECATED.md"
    if dep.is_file() and "DEPRECATED" not in dep.read_text(encoding="utf-8", errors="replace"):
        fail("FINAL compatibility directory is not clearly deprecated")

    sub = ws / "09_submission/README.md"
    if sub.is_file() and "ONLY final submission directory" not in sub.read_text(encoding="utf-8", errors="replace"):
        fail("09_submission README does not identify the canonical final directory")

    for p in sorted(ws.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".md", ".tex", ".yaml", ".csv", ".txt", ".jsonl"):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pat in LEAK_PATTERNS:
            if re.search(pat, txt, re.IGNORECASE):
                fail(f"drill-specific leakage pattern '{pat}' in {p.relative_to(ws)}")

    return {"workspace": str(ws), "pass": ok, "issues": issues}


def main() -> int:
    ap = argparse.ArgumentParser(description="MMKit v0.3 workspace preflight")
    ap.add_argument("workspace")
    ap.add_argument("-j", "--json", help="write report JSON")
    a = ap.parse_args()
    rep = check(Path(a.workspace))
    print(f"WORKSPACE_PREFLIGHT: {'PASS' if rep['pass'] else 'FAIL'}")
    for i in rep["issues"]:
        print(f"  - {i}")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reference_audit.py - audit references/REFERENCE_LEDGER.csv (MMKit v0.2 P1).

Checks: DOI syntax, duplicate DOI/title/key, missing authors/year/venue,
metadata_verified / publisher_verified / relevance / used_in_claims linkage.
Truth sources: the ledger itself + real registry files (no citation generators).
Exit 0 regardless of findings (guidance); exit 1 only on structural errors.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "references" / "REFERENCE_LEDGER.csv"

DOI_RE = re.compile(r"^10\.\d{4,9}/[^\s]+$")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Reference ledger auditor")
    p.add_argument("ledger", nargs="?", default=str(LEDGER))
    p.add_argument("-j", "--json", help="write report JSON to path")
    return p.parse_args()

def audit(path: Path) -> dict:
    findings: list[dict] = []
    if not path.exists():
        return {"status": "EMPTY_OR_MISSING", "rows": 0, "findings": [
            {"level": "info", "code": "ledger_missing", "detail": str(path)}]}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"key","title","authors","year","venue","doi","url",
                    "discovered_via","metadata_verified","publisher_verified",
                    "relevance","used_in_claims","notes"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            return {"status": "FAIL_STRUCTURE", "rows": 0,
                    "findings": [{"level": "error","code": "bad_header",
                                    "detail": "missing: " + ",".join(sorted(required - set(reader.fieldnames or [])))}]}
        rows = list(reader)
    keys: set[str] = set(); titles: set[str] = set(); dois: set[str] = set()
    for i, row in enumerate(rows, start=2):
        k = (row.get("key") or "").strip(); t = (row.get("title") or "").strip()
        d = (row.get("doi") or "").strip(); a = (row.get("authors") or "").strip()
        y = (row.get("year") or "").strip(); v = (row.get("venue") or "").strip()
        if not k: findings.append({"level":"warn","code":"missing_key","row":i})
        elif k in keys: findings.append({"level":"error","code":"duplicate_key","row":i,"value":k})
        else: keys.add(k)
        tl = t.lower() if t else ""
        if not t: findings.append({"level":"warn","code":"missing_title","row":i})
        elif tl in titles: findings.append({"level":"error","code":"duplicate_title","row":i,"value":t[:60]})
        else: titles.add(tl)
        if d:
            if not DOI_RE.match(d): findings.append({"level":"error","code":"doi_syntax","row":i,"value":d})
            elif d.lower() in dois: findings.append({"level":"error","code":"duplicate_doi","row":i,"value":d})
            else: dois.add(d.lower())
        else: findings.append({"level":"info","code":"no_doi","row":i,"value":"url-only"})
        if not a: findings.append({"level":"warn","code":"missing_authors","row":i})
        if not y: findings.append({"level":"warn","code":"missing_year","row":i})
        if not v: findings.append({"level":"warn","code":"missing_venue","row":i})
        mv = (row.get("metadata_verified") or "").strip().upper()
        pv = (row.get("publisher_verified") or "").strip().upper()
        if mv not in ("","TRUE","FALSE"): findings.append({"level":"warn","code":"metadata_verified_invalid","row":i,"value":mv})
        if pv not in ("","TRUE","FALSE"): findings.append({"level":"warn","code":"publisher_verified_invalid","row":i,"value":pv})
        if not (row.get("relevance") or "").strip(): findings.append({"level":"warn","code":"missing_relevance","row":i})
        claims = (row.get("used_in_claims") or "").strip()
        if not claims: findings.append({"level":"info","code":"no_claim_linkage","row":i,"detail":"not used in any claim yet"})
        elif claims in ("NONE","-"): findings.append({"level":"info","code":"no_claim_linkage","row":i})
        if pv == "TRUE" and claims and claims not in ("NONE","-"):
            findings.append({"level":"info","code":"claim_ready","row":i})
    n_pub = sum(1 for r in rows if (r.get("publisher_verified") or "").strip().upper() == "TRUE")
    n_meta = sum(1 for r in rows if (r.get("metadata_verified") or "").strip().upper() == "TRUE")
    errors = [f for f in findings if f["level"] in ("error",)]
    status = "PASS" if not errors else "WARN"
    if not rows: status = "PASS_EMPTY_LEDGER"
    return {"status": status, "rows": len(rows),
            "counts": {"metadata_verified": n_meta, "publisher_verified": n_pub},
            "findings": findings}

def main() -> int:
    args = parse_args()
    rep = audit(Path(args.ledger))
    print("REFERENCE_AUDIT:", rep["status"], "| rows:", rep["rows"])
    for f in rep["findings"]:
        print(f"  [{f['level']}] {f['code']} row={f.get('row','-')} {f.get('value',f.get('detail',''))}")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    return 0 if rep["status"] not in ("FAIL_STRUCTURE",) else 1

if __name__ == "__main__":
    sys.exit(main())

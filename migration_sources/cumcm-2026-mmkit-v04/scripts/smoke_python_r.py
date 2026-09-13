#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMKit Python <-> R OLS contract smoke test (v0.2 P0).

Pipeline (no rpy2, deterministic):
  1. Python generates a tiny deterministic synthetic dataset  -> reports/r_ols/smoke_input.csv
  2. Python locates Rscript.exe (PATH + common Windows install dirs)
     - if absent: writes smoke_report.json with status R_RUNTIME_MISSING and exits 0
       (graceful degradation path; absence of R is a reportable state)
  3. Python calls:  Rscript r_toolbox/ols_smoke.R <input.csv> <outdir>
  4. R fits lm(y ~ x1 + x2) and writes the standard outputs:
       coefficients.csv predictions.csv metrics.csv model_summary.txt run_metadata.json
  5. Python refits the same OLS with numpy.linalg.lstsq
  6. Python compares coefficients and predictions (max abs diff)
Numerical tolerance: 1e-10.

Exit codes: 0 = PASS or R_RUNTIME_MISSING; 1 = FAIL; 2 = usage error.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports" / "r_ols"
TOLERANCE = 1e-10

R_DISCOVERY_ROOTS = [
    r"C:\Program Files\R",
    r"C:\Program Files (x86)\R",
    r"C:\R",
]


def find_rscript() -> str | None:
    for name in ("Rscript.exe", "Rscript"):
        exe = shutil.which(name)
        if exe:
            return exe
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs"
    roots = [Path(p) for p in R_DISCOVERY_ROOTS]
    for cand in (local / "R", local / "RStudio"):
        roots.append(cand)
    for root in roots:
        if not root.is_dir():
            continue
        for base, dirs, files in os.walk(root):
            depth = base[len(str(root)):].count(os.sep)
            if depth > 2:
                dirs[:] = []
                continue
            if "Rscript.exe" in files:
                return os.path.join(base, "Rscript.exe")
    return None


def r_version(rscript: str) -> str:
    try:
        p = subprocess.run([rscript, "--version"], capture_output=True, text=True,
                           timeout=60, encoding="utf-8", errors="replace")
        txt = (p.stdout or "") + (p.stderr or "")
        for line in txt.splitlines():
            if "version" in line:
                return line.strip()
        return txt.strip() or "(unknown)"
    except Exception:
        return "(unknown)"


def generate_dataset(path: Path) -> dict:
    rng = np.random.default_rng(20260910)  # deterministic, version-stable generator
    n = 80
    x1 = np.linspace(-3.0, 3.0, n)
    x2 = np.sin(x1 * 1.7) * 1.2 + 0.35 * rng.standard_normal(n)
    eps = 0.10 * rng.standard_normal(n)
    beta = np.array([2.5, 1.25, -0.75])
    y = beta[0] + beta[1] * x1 + beta[2] * x2 + eps
    header = "y,x1,x2"
    np.savetxt(path, np.column_stack([y, x1, x2]), delimiter=",",
               header=header, comments="", fmt="%.17g")
    return {"y": y, "x1": x1, "x2": x2, "n": n}


def py_ols(data: dict) -> dict:
    y = data["y"]
    X = np.column_stack([np.ones(data["n"]), data["x1"], data["x2"]])
    beta_hat, resid, rank, sv = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta_hat
    return {"beta": beta_hat, "pred": pred}


def read_r_outputs(outdir: Path) -> dict:
    import csv as _csv

    def read_csv(name: str) -> list[dict]:
        with open(outdir / name, newline="", encoding="utf-8") as fh:
            return list(_csv.DictReader(fh))

    coefs = read_csv("coefficients.csv")
    preds = read_csv("predictions.csv")
    with open(outdir / "run_metadata.json", encoding="utf-8") as fh:
        meta = json.load(fh)
    return {"coefs": coefs, "preds": preds, "meta": meta}


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    rscript = find_rscript()
    if not rscript:
        report = {
            "status": "R_RUNTIME_MISSING",
            "note": "Rscript.exe not found on PATH or in common Windows install dirs. "
                    "Run scripts/setup_windows_r.ps1 for discovery guidance.",
            "timestamp": started,
        }
        (REPORTS / "smoke_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8")
        print("MMKIT_OLS_SMOKE: R_RUNTIME_MISSING")
        print("Rscript not found on PATH / common Windows locations. Graceful degrade.")
        print(f"report: {REPORTS / 'smoke_report.json'}")
        return 0

    input_csv = REPORTS / "smoke_input.csv"
    outdir = REPORTS / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    data = generate_dataset(input_csv)
    sha256 = hashlib.sha256(input_csv.read_bytes()).hexdigest()

    rver = r_version(rscript)
    print(f"[R] using Rscript: {rscript}")
    print(f"[R] version line: {rver}")

    proc = subprocess.run(
        [rscript, str(ROOT / "r_toolbox" / "ols_smoke.R"), str(input_csv), str(outdir)],
        capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        print("MMKIT_OLS_SMOKE: FAIL (R exit code != 0)")
        return 1

    r_out = read_r_outputs(outdir)
    meta = r_out["meta"]

    # required metadata keys
    for key in ("r_version", "input_sha256", "arguments", "timestamp", "exit_status"):
        if key not in meta:
            print(f"MMKIT_OLS_SMOKE: FAIL (run_metadata.json missing key {key})")
            return 1
    if meta.get("input_sha256") != sha256:
        print(f"MMKIT_OLS_SMOKE: FAIL (input SHA256 mismatch: R={meta.get('input_sha256')} py={sha256})")
        return 1

    # Python reference OLS
    ref = py_ols(data)

    # map R terms (Intercept, x1, x2) to numpy order [1, x1, x2]
    order = {"(Intercept)": 0, "x1": 1, "x2": 2}
    r_beta = np.zeros(3)
    for row in r_out["coefs"]:
        term = row["term"]
        if term in order:
            r_beta[order[term]] = float(row["estimate"])
        elif term not in ("", "(Intercept)") or order.get(term) is not None:
            continue

    coef_diff = float(np.max(np.abs(r_beta - ref["beta"])))

    r_pred = np.array([float(r["predicted"]) for r in r_out["preds"]])
    pred_diff = float(np.max(np.abs(r_pred - ref["pred"])))

    ok = coef_diff <= TOLERANCE and pred_diff <= TOLERANCE
    report = {
        "status": "PASS" if ok else "FAIL",
        "tolerance": TOLERANCE,
        "coef_max_diff": coef_diff,
        "pred_max_diff": pred_diff,
        "rscript": rscript,
        "r_version": meta.get("r_version"),
        "input_sha256": sha256,
        "n_obs": data["n"],
        "r_exit_status": meta.get("exit_status"),
        "outputs": {
            "coefficients.csv": str(outdir / "coefficients.csv"),
            "predictions.csv": str(outdir / "predictions.csv"),
            "metrics.csv": str(outdir / "metrics.csv"),
            "model_summary.txt": str(outdir / "model_summary.txt"),
            "run_metadata.json": str(outdir / "run_metadata.json"),
        },
        "timestamp": started,
    }
    (REPORTS / "smoke_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print(f"coeff max |diff| = {coef_diff:.3e}  (tol {TOLERANCE:g})")
    print(f"pred  max |diff| = {pred_diff:.3e}  (tol {TOLERANCE:g})")
    print(f"MMKIT_OLS_SMOKE: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

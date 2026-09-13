from __future__ import annotations

import json
import platform
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pyarrow as pa
import pulp
import scipy
import scipy.optimize as opt
import sklearn
import statsmodels.api as sm
import sympy as sp
from openpyxl import Workbook
from ortools.sat.python import cp_model
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

checks: dict[str, object] = {}

# Numerical linear algebra
A = np.array([[3.0, 1.0], [1.0, 2.0]])
b = np.array([9.0, 8.0])
x = np.linalg.solve(A, b)
checks["numpy_linear_solve"] = bool(np.allclose(A @ x, b))

# SciPy optimization
res = opt.minimize(lambda z: (z[0] - 2.0) ** 2 + (z[1] + 1.0) ** 2, x0=[0.0, 0.0])
checks["scipy_optimize"] = bool(res.success and np.allclose(res.x, [2.0, -1.0], atol=1e-5))

# pandas
frame = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0, 6.0]})
checks["pandas"] = bool(frame["y"].mean() == 4.0)

# scikit-learn
from sklearn.linear_model import LinearRegression
reg = LinearRegression().fit(frame[["x"]], frame["y"])
checks["sklearn"] = bool(abs(float(reg.coef_[0]) - 2.0) < 1e-9)

# statsmodels
X = sm.add_constant(frame["x"])
ols = sm.OLS(frame["y"], X).fit()
checks["statsmodels"] = bool(abs(float(ols.params["x"]) - 2.0) < 1e-9)

# sympy
symbol = sp.symbols("x")
checks["sympy"] = bool(sp.solve(sp.Eq(symbol**2 - 4, 0), symbol) == [-2, 2])

# networkx
graph = nx.Graph()
graph.add_weighted_edges_from([("A", "B", 1), ("B", "C", 2), ("A", "C", 5)])
checks["networkx"] = nx.shortest_path(graph, "A", "C", weight="weight") == ["A", "B", "C"]

# PuLP linear program
lp = pulp.LpProblem("smoke", pulp.LpMaximize)
px = pulp.LpVariable("x", lowBound=0)
py = pulp.LpVariable("y", lowBound=0)
lp += 3 * px + 2 * py
lp += px + py <= 4
lp += px <= 2
lp_status = lp.solve(pulp.PULP_CBC_CMD(msg=False))
checks["pulp"] = pulp.LpStatus[lp_status] == "Optimal"

# OR-Tools CP-SAT
cp = cp_model.CpModel()
cx = cp.new_int_var(0, 10, "x")
cy = cp.new_int_var(0, 10, "y")
cp.add(cx + cy <= 7)
cp.maximize(2 * cx + cy)
solver = cp_model.CpSolver()
cp_status = solver.solve(cp)
checks["ortools"] = cp_status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

# pyarrow
arrow_table = pa.Table.from_pandas(frame)
checks["pyarrow"] = arrow_table.num_rows == 3

# openpyxl
with tempfile.TemporaryDirectory() as td:
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "CUMCM"
    xlsx_path = Path(td) / "smoke.xlsx"
    workbook.save(xlsx_path)
    checks["openpyxl"] = xlsx_path.exists() and xlsx_path.stat().st_size > 0

# matplotlib headless render
with tempfile.TemporaryDirectory() as td:
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.tight_layout()
    image_path = Path(td) / "smoke.png"
    fig.savefig(image_path, dpi=150)
    plt.close(fig)
    checks["matplotlib"] = image_path.exists() and image_path.stat().st_size > 0

class SmokeModel(BaseModel):
    name: str
    score: float

checks["pydantic"] = SmokeModel(name="baseline", score=1.0).score == 1.0

versions = {
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "numpy": np.__version__,
    "scipy": scipy.__version__,
    "pandas": pd.__version__,
    "sklearn": sklearn.__version__,
}

all_passed = all(bool(v) for v in checks.values())
report = {
    "all_passed": all_passed,
    "versions": versions,
    "checks": checks,
}

out = REPORT_DIR / "python_smoke.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
print(f"Report: {out}")

if not all_passed:
    raise SystemExit(1)

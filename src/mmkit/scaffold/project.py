"""Cross-platform competition-project scaffolding for MMKit."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMPETITION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
PROJECT_NAME_RE = re.compile(r"^[^/\\\x00-\x1f]+$")

WORKSPACE_DIRS = (
    "problem",
    "data/raw",
    "data/processed",
    "analysis",
    "models",
    "results/tables",
    "results/figures",
    "paper",
    "scripts",
    "supporting",
    "ai_logs",
    "references",
    "submission",
    "coordination",
    "config",
    "gates",
)


def _normalize_competition(value: str) -> str:
    competition = value.strip()
    if not competition or not COMPETITION_RE.fullmatch(competition):
        raise ValueError(
            "competition must be 1-32 characters using letters, digits, '.', '_' or '-'"
        )
    return competition.upper()


def _normalize_year(value: int | str) -> int:
    try:
        year = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("year must be an integer") from exc
    if year < 2000 or year > 2200:
        raise ValueError("year must be between 2000 and 2200")
    return year


def _normalize_project_name(value: str) -> str:
    name = value.strip()
    if not name or name in {".", ".."} or not PROJECT_NAME_RE.fullmatch(name):
        raise ValueError("project name must be non-empty and may not contain path separators")
    return name


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _seed_files(metadata: dict[str, Any]) -> dict[str, str]:
    project_name = metadata["project_name"]
    competition = metadata["competition"]
    year = metadata["year"]

    competition_json = {
        "schema_version": 1,
        "project_name": project_name,
        "competition": competition,
        "year": year,
        "created_at": metadata["created_at"],
        "workflow_stage": "problem_intake",
        "canonical_submission_dir": "submission",
        "mmkit_workspace_schema": 1,
    }

    run_manifest = {
        "schema_version": 1,
        "stop_on_failure": True,
        "commands": [
            {
                "name": "scaffold_smoke",
                "argv": ["${PYTHON}", "scripts/smoke.py"],
                "cwd": ".",
                "timeout_seconds": 60,
                "expected_outputs": ["results/smoke.txt"],
            }
        ],
    }

    submission_requirements = {
        "schema_version": 1,
        "required_artifacts": [],
        "note": (
            "Populate required_artifacts with official submission filenames, then pass "
            "them to `mmkit audit submission --require <name>`."
        ),
    }

    provenance_config = {
        "schema_version": 1,
        "registry": "coordination/CLAIM_REGISTRY.csv",
        "lock": "coordination/CLAIM_PROVENANCE.lock.json",
        "verification_report": "coordination/CLAIM_PROVENANCE.verify.json",
    }

    seeds: dict[str, str] = {
        ".gitignore": (
            ".venv/\n"
            "__pycache__/\n"
            "*.py[cod]\n"
            ".pytest_cache/\n"
            ".mypy_cache/\n"
            ".ruff_cache/\n"
            ".DS_Store\n"
            "Thumbs.db\n"
        ),
        "competition.json": _json_text(competition_json),
        "README_WORKSPACE.md": f"""# {project_name}

Competition: **{competition} {year}**

This workspace was created by MMKit. It keeps competition-specific work here
while reusable engineering remains in `math-modeling-competition-kit`.

## Canonical workflow

1. Preserve official statements and attachments under `problem/`.
2. Keep `data/raw/` immutable; write transformations to code and derived data to `data/processed/`.
3. Choose and validate the model before long implementation work.
4. After the model is correct, optimize algorithms/runtime before replacing the model.
5. Write reproducible outputs under `results/`.
6. Register important paper claims in `coordination/CLAIM_REGISTRY.csv`.
7. Lock claim/evidence identity before formal writing or final review.
8. Put only official final artifacts in `submission/`.

## First commands

```text
mmkit reproduce . config/run_manifest.json --json coordination/reproduction.json
mmkit manifest . --output coordination/workspace.manifest.json
mmkit provenance lock . coordination/CLAIM_REGISTRY.csv --output coordination/CLAIM_PROVENANCE.lock.json
mmkit provenance verify . coordination/CLAIM_REGISTRY.csv coordination/CLAIM_PROVENANCE.lock.json --json coordination/CLAIM_PROVENANCE.verify.json
mmkit audit submission --json coordination/submission_audit.json
```

`mmkit provenance` verifies evidence identity/freshness, not scientific truth.
Human gates in `gates/` remain human decisions.
""",
        "AGENTS.md": """# Workspace agent instructions

Read `README_WORKSPACE.md`, `competition.json`, `coordination/ACTIVE_TASK.md`,
and `coordination/HANDOFF.md` before making material changes.

Rules:

- Do not invent problem facts, assumptions, numerical results, citations, or verification evidence.
- Treat `data/raw/` and official problem files as immutable source evidence.
- Record important paper claims in `coordination/CLAIM_REGISTRY.csv`.
- If an upstream evidence file changes after a provenance lock, re-run provenance verification.
- Do not write final artifacts outside `submission/`.
- Do not approve human gates on behalf of the team.
- Keep the handoff/current-task files short enough for a new AI agent to resume without chat history.
""",
        "analysis/MODEL_ROUTE.md": """# Model route

Status: NOT_DECIDED

| Field | Decision |
| --- | --- |
| problem structure | |
| candidate models | |
| selected model | |
| why selected | |
| assumptions | |
| baseline | |
| verification plan | |
| rejected alternatives | |
| runtime/algorithm optimization plan after correctness | |
""",
        "coordination/CLAIM_REGISTRY.csv": (
            "claim_id,paper_location,producer,input,artifact,value,precision,status\n"
        ),
        "coordination/ACTIVE_TASK.md": """# Active task

Status: PROBLEM_INTAKE

## Objective

Read and preserve the official problem package, identify candidate questions,
and record the next concrete modeling decision.

## Next action

Replace this section with one bounded next action before handing the workspace
to another human or AI agent.
""",
        "coordination/HANDOFF.md": """# Handoff

This file is the short recovery point for a new human or AI agent.

## Read first

1. `competition.json`
2. `README_WORKSPACE.md`
3. `coordination/ACTIVE_TASK.md`
4. `coordination/CLAIM_REGISTRY.csv`
5. only the files explicitly required by the active task

Do not reconstruct state from chat history when repository evidence is available.

## Current phase

PROBLEM_INTAKE

## Verified facts

- Workspace scaffold exists.
- No scientific/model claim is verified merely because the scaffold was created.

## Next action

See `coordination/ACTIVE_TASK.md`.
""",
        "coordination/PROVENANCE.md": """# Claim/evidence provenance

The editable registry is `CLAIM_REGISTRY.csv`.

After important claims have evidence files:

```text
mmkit provenance lock . coordination/CLAIM_REGISTRY.csv --output coordination/CLAIM_PROVENANCE.lock.json
```

After any upstream change:

```text
mmkit provenance verify . coordination/CLAIM_REGISTRY.csv coordination/CLAIM_PROVENANCE.lock.json --json coordination/CLAIM_PROVENANCE.verify.json
```

A PASS means the locked claim rows and evidence bytes are current. It does not
certify scientific correctness.
""",
        "config/run_manifest.json": _json_text(run_manifest),
        "config/submission_requirements.json": _json_text(submission_requirements),
        "config/provenance.json": _json_text(provenance_config),
        "scripts/smoke.py": """from pathlib import Path

output = Path("results/smoke.txt")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("MMKIT_SCAFFOLD_SMOKE_OK\\n", encoding="utf-8")
print("MMKIT_SCAFFOLD_SMOKE_OK")
""",
        "references/REFERENCE_LEDGER.csv": (
            "key,title,authors,year,venue,doi,url,metadata_verified,used_in_claims,notes\n"
        ),
        "ai_logs/ai_calls.jsonl": "",
        "paper/README.md": """# Paper

P5 will provide reusable paper-pipeline tooling. Until then, keep editable paper
sources here and derive factual claims only from verified workspace evidence.
""",
        "supporting/README.md": """# Supporting material

Keep source code, data maps, run instructions, and supporting artifacts required
by the competition here before packaging them for submission.
""",
        "submission/README.md": """# Final submission directory

This is the only canonical final-submission directory for this workspace.

Before submission, run the MMKit submission audit with every officially required
filename passed through `--require`. Do not keep competing final copies elsewhere.
""",
        "gates/G1_problem_choice.md": """# G1 — Problem choice

APPROVED: NO

- [ ] Official problem files are preserved.
- [ ] Candidate problems/questions were compared.
- [ ] Team selected the target problem/question.
""",
        "gates/G2_model_route.md": """# G2 — Model route

APPROVED: NO

- [ ] Assumptions are explicit.
- [ ] Baseline is defined.
- [ ] Selected model fits the problem structure.
- [ ] Alternatives and rejection reasons are recorded.
- [ ] Verification plan exists before long solves.
""",
        "gates/G3_results.md": """# G3 — Results

APPROVED: NO

- [ ] Key numerical claims trace to reproducible result artifacts.
- [ ] Units and precision are checked.
- [ ] Robustness/sensitivity/error checks are adequate for the problem.
- [ ] Claim registry is ready for provenance locking.
""",
        "gates/G4_submission.md": """# G4 — Submission

APPROVED: NO

- [ ] Paper and supporting files satisfy official rules.
- [ ] Claim/evidence provenance is current.
- [ ] Final human paper review is complete.
- [ ] Submission audit reports no blocker.
- [ ] Only intended final artifacts remain in `submission/`.
""",
        "gates/GATE_STATUS.md": """# Human gates

- [ ] G1 — problem choice
- [ ] G2 — model route
- [ ] G3 — results
- [ ] G4 — submission

Only the human team may approve these gates.
""",
    }

    for relpath in (
        "problem/.gitkeep",
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "models/.gitkeep",
        "results/tables/.gitkeep",
        "results/figures/.gitkeep",
    ):
        seeds[relpath] = ""

    return seeds


def init_project(
    destination: str | Path,
    *,
    competition: str,
    year: int | str,
    project_name: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Create a generic competition workspace without overwriting user files.

    ``force=True`` permits filling missing scaffold files into a non-empty
    destination. Existing files are never overwritten.
    """

    root = Path(destination).expanduser()

    if root.exists() and not root.is_dir():
        raise ValueError(f"destination exists and is not a directory: {root}")

    if root.exists() and any(root.iterdir()) and not force:
        raise FileExistsError(
            f"destination is not empty: {root}; use force=True only to fill missing scaffold files"
        )

    root.mkdir(parents=True, exist_ok=True)

    normalized_competition = _normalize_competition(competition)
    normalized_year = _normalize_year(year)
    normalized_name = _normalize_project_name(project_name or root.name)

    metadata = {
        "project_name": normalized_name,
        "competition": normalized_competition,
        "year": normalized_year,
        "created_at": _utc_now(),
    }

    created_dirs: list[str] = []
    for relpath in WORKSPACE_DIRS:
        directory = root / Path(*relpath.split("/"))
        existed = directory.exists()
        directory.mkdir(parents=True, exist_ok=True)
        if not existed:
            created_dirs.append(relpath)

    created_files: list[str] = []
    existing_files: list[str] = []

    for relpath, content in _seed_files(metadata).items():
        target = root / Path(*relpath.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not target.is_file():
                raise ValueError(f"scaffold file path exists but is not a file: {target}")
            existing_files.append(relpath)
            continue
        target.write_text(content, encoding="utf-8", newline="\n")
        created_files.append(relpath)

    return {
        "schema_version": 1,
        "status": "PASS",
        "root": str(root.resolve()),
        "project_name": normalized_name,
        "competition": normalized_competition,
        "year": normalized_year,
        "created_directory_count": len(created_dirs),
        "created_file_count": len(created_files),
        "existing_file_count": len(existing_files),
        "created_directories": created_dirs,
        "created_files": created_files,
        "existing_files": existing_files,
        "overwrite_policy": "existing files are never overwritten",
    }

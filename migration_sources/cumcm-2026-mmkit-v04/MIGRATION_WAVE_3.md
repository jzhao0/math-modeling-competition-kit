# Migration Wave 3

Mode: **snapshot-only**

Source repository: $SourceRepo  
Source ref: $SourceRef

This wave captures additional reusable source history without promoting any
snapshot into the active public toolkit.

## Rules

- no development;
- no refactor;
- no content rewrite;
- exact Git blob bytes only;
- prompts/history/context records are excluded;
- teacher/drill/CUMCM-specific review records are excluded;
- third-party/contest template trees are deferred;
- personal-path or credential-like files are skipped instead of edited.

## Counts

- Candidates: 36
- Newly copied exact: 5
- Resumed partial exact: 30
- Already present exact: 1
- Skipped public-safety: 0
- Fetch failed: 0

## Snapshot areas

- `.python-version`: 1
- `docs`: 21
- `pyproject.toml`: 1
- `r_toolbox`: 8
- `README.md`: 1
- `references`: 2
- `requirements-win-py313.lock.txt`: 1
- `RUNBOOK.md`: 1

## Newly copied

- `README.md`
- `references/README.md`
- `references/REFERENCE_LEDGER.csv`
- `requirements-win-py313.lock.txt`
- `RUNBOOK.md`


## Resumed partial exact

- `.python-version`
- `docs/ACADEMIC_SKILL_STACK_V03.md`
- `docs/ACADEMIC_SKILL_STACK_V04.md`
- `docs/AI_DISCLOSURE_STYLE.md`
- `docs/AI_TRACE_DISCLOSURE_RECOVERY.md`
- `docs/ARCHITECTURE.md`
- `docs/COMPLIANCE_2026.md`
- `docs/FIGURE_PIPELINE.md`
- `docs/FIVE_DAY_PLAN.md`
- `docs/LITERATURE_VERIFICATION.md`
- `docs/MMKIT_SKILL_DISTILLATION.md`
- `docs/MMKIT_V02_SYSTEM_UPGRADE.md`
- `docs/MMKIT_V04_HARVEST_CANDIDATES.md`
- `docs/ORIGIN_MCP_BACKEND.md`
- `docs/PAPER_INTELLIGENCE_PIPELINE.md`
- `docs/PAPER_PIPELINE.md`
- `docs/PAPER_SCIENTIFIC_DENSITY.md`
- `docs/R_DRILL_ACCEPTANCE.md`
- `docs/SKILL_ROUTING.md`
- `docs/SKILL_SUPPLY_CHAIN.md`
- `docs/WORKSPACE_SCHEMA.md`
- `pyproject.toml`
- `r_toolbox/.Rprofile`
- `r_toolbox/bootstrap.R`
- `r_toolbox/io_contract.R`
- `r_toolbox/ols_smoke.R`
- `r_toolbox/OUTPUT_CONTRACT.md`
- `r_toolbox/README.md`
- `r_toolbox/renv/activate.R`
- `r_toolbox/renv/settings.json`


## Already present exact

- `docs/G4_EXACT_FILE_LOCK.md`


## Skipped public-safety



## Fetch failed



See MIGRATION_WAVE_3.csv for original Git blob SHAs and sizes.

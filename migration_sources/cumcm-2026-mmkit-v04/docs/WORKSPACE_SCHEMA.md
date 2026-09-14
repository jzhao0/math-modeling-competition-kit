# MMKit Workspace Schema (v0.3)

`scripts/new_problem.ps1 -Name <Workspace> [-DestinationRoot <dir>] [-Force]` creates a competition workspace that inherits the frozen runtime/policy infrastructure. Creation is offline: local files only.

## Directory schema

| dir | role |
| --- | --- |
| 00_problem/ | official statement + attachments; keep original hash and read-only copy |
| 01_data_raw/ | raw data, never overwritten |
| 02_data_processed/ | cleaned/derived data + transformation scripts |
| 03_analysis/ | method route, figure plan, claim register, paper plan, human paper review, exploratory analysis |
| 04_models/ | Python/R/model code; R models under 04_models/r/ |
| 05_results/ | reproducible tables/figures/result artifacts |
| 06_paper/ | editable paper source (`main.tex`) |
| 07_scripts/ | workspace execution adapters/helpers |
| 07_supporting/ | editable source for supporting material/package |
| 08_ai_logs/ | append-only AI-use records; export official detail PDF before G4 |
| 09_references/ | reference ledger + verified BibTeX |
| 09_submission/ | **only canonical final-submission directory** |
| human_gates/ | G1..G4 (`APPROVED: NO` by default) |
| config/ | offline snapshots of method/paper/figure/competition-visual policies |
| FINAL/ | deprecated compatibility marker only; never store competing final artifacts |

## v0.3 paper / visual control files

`03_analysis/CLAIM_REGISTER.md` is completed after G3 and before full drafting. It records central claims, scope and evidence so writing starts from scientific argument rather than a generic template.

`03_analysis/FIGURE_PLAN.md` uses a figure contract: figure intent, claim/page role, reader question, source data, visual encoding, backend, dimensions/units, presentation layer, paper location, editable source and QA owner. Figure type can be `EVIDENCE_NUMERICAL`, `STRUCTURAL_SCIENTIFIC` or `SHOWCASE_PRESENTATION`.

`03_analysis/PAPER_PLAN.md` stores section-level argument structure before prose.

`03_analysis/PAPER_HUMAN_REVIEW.md` is the manual judge-view checklist for AI-style phrasing, parentheses, numeric precision, figure-text integration, formulas/symbol grammar, visual rhythm and PDF presentation.

`config/contest_visual.yaml` is the CUMCM-specific presentation layer. It explicitly allows `PRESENTATION_3D`: decorative perspective/depth may be used for better competition appearance without pretending that depth is a measured variable.

`09_submission/SUBMISSION_MANIFEST.md` exists from workspace creation. The submission package is therefore maintained as an explicit artifact from the beginning rather than discovered during G4.

## Normal path

```text
new workspace
  → preflight
  → G1 problem choice
  → G2 model route + state/reduction closure check
  → deterministic execution
  → G3 frozen results
  → claim register / evidence bank
  → paper argument blueprint
  → draft
  → formula + figure integration
  → claim-preserving polish
  → deterministic human-paper risk audit
  → human-style review
  → judge-view PDF review (science + presentation)
  → G4 submission engineering
  → 09_submission/
```

## Submission layout

After G4, `09_submission/` should contain only the files intended for the official platform plus explicit checksum/receipt records, for example:

```text
09_submission/
├── competition_paper.pdf
├── supporting_material.zip
├── SUBMISSION_MANIFEST.md
└── checksums.txt          # when needed
```

`FINAL/` remains only to avoid breaking older P2 assumptions and is seeded with `README_DEPRECATED.md`. It must not contain a second copy of the final paper/package.

## Verification

```powershell
.venv\Scripts\python.exe scripts\workspace_preflight.py <workspace>
.venv\Scripts\python.exe scripts\reference_audit.py <workspace>\09_references\REFERENCE_LEDGER.csv
.venv\Scripts\python.exe scripts\audit_paper_density.py <workspace>\06_paper\main.tex
.venv\Scripts\python.exe scripts\audit_human_paper.py <workspace>\06_paper\main.tex --code-dir <workspace>\04_models
```

`audit_human_paper.py` is advisory by default. It locates raw precision, defensive/internal-process wording, long parentheses, informal range notation, link-border risks and code presentation artifacts. It does not assign an AI probability and does not replace human review.

Preflight verifies the canonical submission marker, human-paper control files, competition visual policy, showcase/presentation-3D figure contract, hidden hyperlink-border default, footer/plain page style and the deprecation marker for `FINAL/`.

## Figure backends

- Python/matplotlib: deterministic default.
- R/ggplot2: statistical/grammar-of-graphics route.
- Origin MCP: optional high-presentation backend for 3D columns, surfaces, contours, fitting plots and polished layouts; requires pre-contest installation/host validation. See `docs/ORIGIN_MCP_BACKEND.md`.
- Draw.io/SVG: editable structural/state diagrams.

Figure values always come from frozen model/result artifacts. Aesthetic depth may be decorative, but it cannot invent a quantitative axis, change ordering or conceal uncertainty.

## R backend defaults

- Default: central MMKit `r_toolbox` renv environment; no per-workspace renv unless a materially different package set is required.
- Workspace R model files: `04_models/r/*.R`, executed through `07_scripts/run_r_model.ps1`.
- Substantive/multiline R runs through real `.R` files, not multiline `Rscript -e`.
- No automatic package installs during a competition run.

## Skill/runtime policy

- `vendor/SKILLS_MANIFEST.yaml` is the contest-authoritative supply-chain record.
- v0.3 sources are classified as `DISTILLED_POLICY`, `REFERENCE_ONLY` or `OPTIONAL_RUNTIME`; exact audited pins are recorded in the manifest and `vendor/CANDIDATE_SKILLS_V03.yaml`.
- `DISTILLED_POLICY` means MMKit-native rules are available offline without the upstream runtime.
- `REFERENCE_ONLY` sources are not copied or executed during the contest.
- Optional runtimes such as Origin MCP must be installed and validated before the contest; otherwise the fallback path is used.
- No external skill fetch/install is allowed during the competition.

## Rules

- No fabricated assumptions, claims, references, visualized values or AI-use records.
- G1-G4 can only be approved by the team.
- Numerical/model claims remain under Sol + deterministic evidence authority.
- Human-style polish cannot alter frozen numbers, formulas, citations, scope or modality without Sol review.
- Competition visual polish is encouraged after truth/readability are protected.
- Automated plagiarism/AIGC or PDF-geometry checks never replace the final human judge-view review.

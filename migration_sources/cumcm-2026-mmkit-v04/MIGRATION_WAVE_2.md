# Migration Wave 2

Mode: **snapshot-only**

Source repository: $SourceRepo  
Source ref: $SourceRef

Rules:

- no refactor;
- no feature development;
- no semantic edits;
- copied files are byte-identical source snapshots;
- personal-path / credential-like candidates are skipped rather than edited;
- all migrated assets remain isolated under migration_sources/.

## Counts

- Candidates: 22
- Newly copied exact: 22
- Already present exact: 0
- Skipped public-safety: 0
- Missing/non-file: 0

## Newly copied

- `scripts/paper_gate_common.py`
- `scripts/paper_tex_extract.py`
- `scripts/check_paper_facts.py`
- `scripts/check_paper_structure.py`
- `scripts/check_paper_layout.py`
- `scripts/reference_audit.py`
- `scripts/workspace_preflight.py`
- `scripts/paper_visual_review.py`
- `scripts/lint_paper_language.py`
- `scripts/build_paper.ps1`
- `scripts/build_paper_intelligence.py`
- `scripts/build_paper_review_bundle.ps1`
- `scripts/build_sol_review_packet.py`
- `scripts/build_workspace_paper.ps1`
- `scripts/new_problem.ps1`
- `config/figure_contracts.yaml`
- `config/figure_quality.yaml`
- `config/contest_visual.yaml`
- `config/method_router.yaml`
- `config/paper_facts.yaml`
- `config/paper_language_rules.yaml`
- `config/paper_sections.yaml`


## Already present exact



## Skipped for public-safety review



## Missing/non-file



See MIGRATION_WAVE_2.csv for source blob SHAs and byte sizes.

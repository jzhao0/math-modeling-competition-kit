# Migration source snapshot: cumcm-2026-mmkit v0.4

This directory contains **verbatim source snapshots** copied from the private `jzhao0/cumcm-2026-mmkit` workbench for later public-toolkit extraction.

This is a migration/archive layer, not the public API and not a claim that every source file is already contest-agnostic.

## Rules for this snapshot

- Source files are copied without feature development.
- Source paths are preserved below this snapshot root.
- No CUMCM problem-specific solution/results/workbooks are included.
- No worker outputs, private prompts, frozen submission hashes, official attachments, or local competition artifacts are included.
- Files that contain provider-specific/local launcher assumptions are deferred instead of copied.
- Later refactoring/generalization must happen outside `migration_sources/`.

## Migrated files

| Source path | Source blob SHA | Status |
|---|---|---|
| `config/evidence_governance.yaml` | `2bc9371300c88bdf00ba737ae325c0e3220d7637` | verbatim snapshot |
| `config/paper_quality.yaml` | `d27080a6e6631fdd54b3e1738a11b0c01b4f2e95` | verbatim snapshot |
| `docs/G4_EXACT_FILE_LOCK.md` | `047e8c38b1a8a981f034265bfaa3753dfd474b2b` | verbatim snapshot |
| `scripts/g4_bundle_audit.py` | `ead2bb923cf9ef3b170c26d82672ca534e06ad6e` | verbatim snapshot |
| `scripts/audit_human_paper.py` | `d79bd6d7d40a394b602373971120bcafea1fdfb4` | verbatim snapshot |
| `scripts/audit_paper_density.py` | `c58fbf5f2aedcc5a6dd84817a82c853e83ea4ca8` | verbatim snapshot |
| `templates/FIGURE_MANIFEST.md` | `e7dceae5169f4950cddfba36013bb2f25ff5bfc7` | verbatim snapshot |
| `templates/PAPER_VISUAL_STYLE.md` | `3370de9b886bfdf99e0414d24f08088264bda71d` | verbatim snapshot |
| `templates/plot_style.py` | `4b7cf1857306c08213b78eafea536b308992142b` | verbatim snapshot |
| `templates/tex_smoke/main.tex` | `ec18ef80d65d2a8ba2326b44d829a4ab0405cce9` | verbatim snapshot |

## Explicitly deferred

Examples of files intentionally not copied in this migration wave:

- `scripts/agent_handoff.ps1` — contains local/provider-specific launcher assumptions;
- private `prompts/` — many contain local absolute paths and drill-specific state;
- `AGENTS.md` / `RUNBOOK.md` — tightly coupled to the private CUMCM workbench lifecycle;
- problem-specific code/results/workbooks and historical worker evidence.

The private repository remains the historical source of truth.
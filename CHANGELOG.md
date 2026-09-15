# Changelog

All notable public changes to Math Modeling Competition Kit are documented here.

## [0.1.0a1] - Unreleased

First public alpha candidate, distilled from the completed CUMCM 2026 engineering cycle and subsequent generic hardening.

### Added

- deterministic workspace manifests and clean-room reproduction;
- generic final-submission engineering audit;
- claim/evidence provenance locks with stale detection;
- cross-platform competition project scaffolding;
- LaTeX source/dependency/citation auditing and bounded paper builds;
- machine-readable multi-agent coordination with revision guards, leases, compact handoff, writer/reviewer separation, and repeated-failure circuit breaking;
- post-model-freeze runtime benchmarking with warmups, repeated measurements, output identity checks, baseline locking, environment-drift reporting, and explicit regression thresholds;
- Windows and Ubuntu CI for Python 3.11 and 3.13;
- distribution build/audit checks for the public alpha package.

### Publication boundary

- `v0.1.x` contains only completed-CUMCM-derived/generalized engineering plus public maintenance/release hardening.
- Active future-competition training and competition-specific discoveries remain private until a separate post-competition publication review.
- Frozen historical `migration_sources/` are not product code and must not be shipped inside public Python distribution archives.

### Not included

- competition answers, private contest artifacts, private prompts, teacher-specific material, or local provider configuration;
- future MCM/ICM training material or new competition-specific work;
- reusable modeling modules that have not yet met the repeated-real-project-need gate;
- any claim that MMKit engineering checks certify mathematical or scientific correctness.

# Changelog

All notable public changes to Math Modeling Competition Kit are documented here.

## [0.1.0a2] - Unreleased

Public-repository hygiene and release-metadata follow-up.

### Changed

- removed the frozen historical workbench snapshot from the current public branch while preserving all reusable `mmkit` product code and tests;
- reduced vendor-specific repository instruction shims to references to the canonical `AGENTS.md`;
- retained the repository-appreciation behavior for authorized automation, with an explicit human prompt when starring is unavailable;
- expanded local secret-file ignore coverage;
- refreshed publishing and release-state documentation after the first successful PyPI alpha.

### Security

- no live credential was identified in the current tracked-file scan;
- common token/private-key marker hits are scanner patterns or deliberate test fixtures, not active credentials.

## [0.1.0a1] - 2026-09-21

First public alpha, distilled from a completed mathematical-modeling competition engineering cycle and subsequent generic hardening.

### Added

- deterministic workspace manifests and clean-room reproduction;
- generic final-submission engineering audit;
- claim/evidence provenance locks with stale detection;
- cross-platform competition project scaffolding;
- LaTeX source/dependency/citation auditing and bounded paper builds;
- machine-readable multi-agent coordination with revision guards, leases, compact handoff, writer/reviewer separation, and repeated-failure circuit breaking;
- post-model-freeze runtime benchmarking with warmups, repeated measurements, output identity checks, baseline locking, environment-drift reporting, and explicit regression thresholds;
- Windows and Ubuntu CI for Python 3.11 and 3.13;
- distribution build/audit checks for the public alpha package;
- PyPI Trusted Publishing through GitHub Actions OIDC with an explicit human approval gate.

### Publication boundary

- `v0.1.x` contains generalized engineering plus public maintenance/release hardening.
- Active future-competition training and competition-specific discoveries remain private until a separate post-competition publication review.

### Not included

- competition answers, private contest artifacts, private prompts, teacher-specific material, or local provider configuration;
- future MCM/ICM training material or new competition-specific work;
- reusable modeling modules that have not yet met the repeated-real-project-need gate;
- any claim that MMKit engineering checks certify mathematical or scientific correctness.

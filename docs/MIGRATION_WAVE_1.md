# Migration Wave 1 — Governance and Final Submission Engineering

This document tracks the first extraction from the private competition workbench into the public, contest-agnostic toolkit.

## Source concepts

The private workbench contains several proven mechanisms worth preserving:

- explicit proof levels for verification evidence;
- stale-evidence invalidation when upstream artifacts change;
- exact-byte final submission locking;
- clean-room support-package extraction and execution;
- local-path and credential leakage scans;
- deterministic hashing and archive integrity checks;
- agent handoff contracts and bounded scopes.

The public toolkit should preserve these mechanisms while removing competition-specific rules, frozen hashes, private prompts, local absolute paths, teacher-specific constraints, and historical submission artifacts.

## Migration rule

Do not copy the private repository wholesale.

Every migrated component must be:

1. contest-agnostic;
2. path-configurable;
3. free of private data and frozen competition results;
4. independently documented;
5. covered by tests where practical;
6. explicit about what it proves and what it does not prove.

## Wave 1 deliverables

### Evidence governance

Target:

`coordination/EVIDENCE_GOVERNANCE.yaml`

Must preserve:

- `MACHINE_VERIFIED`;
- `HUMAN_CONFIRMED`;
- `SNAPSHOT_ONLY`;
- `UNVERIFIED`;
- upstream fingerprint invalidation;
- writer evidence contracts;
- exact-byte final lock semantics.

### Submission audit

Planned target:

`tools/submission_audit.py`

Responsibilities:

- MD5/SHA256 hashes;
- ZIP traversal and unsafe-path detection;
- duplicate archive member detection;
- symlink detection;
- clean extraction;
- absolute local-path scans;
- credential/secret scans;
- Python syntax checks;
- optional run-manifest execution;
- optional PDF metadata checks;
- JSON reports.

It validates submission engineering only. It does not establish scientific correctness.

### Final freeze protocol

Planned target:

`docs/FINAL_FREEZE_PROTOCOL.md`

The final artifact directory must have one writer, exact hashes generated after all edits, and no writes after approval/freeze.

## Explicit exclusions

Wave 1 does not migrate:

- CUMCM problem-specific implementations;
- official problem files or result workbooks;
- historical worker outputs;
- competition-specific frozen hashes;
- private AI logs/prompts;
- teacher-specific local requirements;
- provider-specific agent runtime assumptions;
- research branches not required by the public tooling.

## Next waves

1. clean-room reproduction;
2. claim provenance and orphan-claim detection;
3. paper build/audit automation;
4. reusable competition project template;
5. algorithm/runtime benchmarking;
6. multi-agent orchestration.

## Optimization doctrine

The toolkit treats model selection and implementation optimization as separate phases.

Once a model is correct, stable, explainable, and reproducible, the default next step is to improve the implementation — runtime, memory, solver calls, I/O, reuse, parallelism and production-DAG size — rather than repeatedly searching for a different model.

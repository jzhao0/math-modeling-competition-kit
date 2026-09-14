# Math Modeling Competition Kit

A reusable engineering toolkit for mathematical modeling competitions, including CUMCM, MCM/ICM and related contests.

## Core principle

> Choose and validate the model early. Once the model is correct, optimize the algorithm and engineering implementation instead of endlessly replacing the model.

## Goals

This repository turns one-off modeling competition work into reusable infrastructure:

- mathematical optimization utilities;
- rolling-horizon optimization;
- scenario generation and reduction;
- reproducible experiment pipelines;
- clean-room reproduction;
- result/workbook generation;
- paper automation;
- claim-to-code provenance;
- final submission validation;
- multi-agent collaboration protocols.

## Workflow

Problem understanding
-> Model design
-> Model validation
-> MODEL_FROZEN
-> Correct implementation
-> Clean-room reproduction
-> Algorithm/runtime optimization
-> Production core
-> Paper/figures/tables
-> Final submission gate
-> Hash/freeze/submit

## Repository structure

- `src/mmkit/` - reusable Python package
- `templates/` - paper/project/submission templates
- `tools/` - clean-room, final-gate and provenance tools
- `coordination/` - multi-agent coordination contracts
- `examples/` - public examples
- `tests/` - automated tests
- `docs/` - architecture, roadmap and postmortems

## Design principles

1. Model selection happens early.
2. Correctness comes before performance.
3. After correctness, optimize algorithms and implementation before changing models.
4. Research pipelines and production pipelines must be separated.
5. Every important paper claim should have a traceable producer.
6. Final results must be reproducible from a clean environment.
7. Only one final integrator may write to the final submission directory.
8. New research routes stop before the submission deadline.
9. Submission artifacts are validated, hashed and frozen.
10. Postmortems are converted into reusable tooling.

## MVP commands

```bash
mmkit manifest WORKSPACE --output workspace-manifest.json

mmkit reproduce WORKSPACE run-manifest.json --json reproduce-report.json

mmkit audit SUBMISSION_DIR --require paper.pdf --require support.zip --json audit-report.json

mmkit provenance lock WORKSPACE coordination/CLAIM_REGISTRY.csv \
  --output coordination/CLAIM_EVIDENCE.lock.json

mmkit provenance verify WORKSPACE coordination/CLAIM_REGISTRY.csv \
  coordination/CLAIM_EVIDENCE.lock.json --json provenance-report.json
```

The provenance lock detects stale claim/evidence relationships; it does **not**
certify scientific correctness. See `docs/PROVENANCE_MVP.md`.

## Initial priorities

- reproducibility and clean-room execution
- final-submission gate
- claim/evidence provenance
- competition project template
- LaTeX paper template
- multi-agent coordination protocol
- algorithm/runtime benchmarking

## License

MIT

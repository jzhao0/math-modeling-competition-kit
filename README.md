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

## Quick start

Create a generic competition workspace and initialize the paper layer:

```text
mmkit init MCM-2027 --competition MCM --year 2027
cd MCM-2027
mmkit coord status .
mmkit reproduce . config/run_manifest.json --json coordination/reproduction.json
mmkit paper init .
mmkit paper audit . paper/main.tex --json coordination/paper_audit.json
```

When a TeX runtime is installed and the build contract is configured:

```text
mmkit paper build . config/paper_build.json --json coordination/paper_build.json
```

See `docs/PROJECT_SCAFFOLD.md` for the workspace contract,
`docs/PAPER_PIPELINE_MVP.md` for paper auditing/build semantics, and
`docs/AGENT_COORDINATION.md` for multi-agent checkpoint/handoff semantics.

## Repository structure

- `src/mmkit/` - reusable Python package
- `templates/` - paper/project/submission templates
- `tools/` - clean-room, final-gate and provenance tools
- `coordination/` - multi-agent coordination contracts
- `examples/` - public examples
- `tests/` - automated tests
- `docs/` - architecture, roadmap and postmortems

## Implemented public core

- deterministic workspace manifests;
- bounded clean-room execution;
- generic final-submission engineering audit;
- claim/evidence provenance locks and stale detection;
- cross-platform competition project scaffold;
- deterministic LaTeX source/dependency/citation audit;
- bounded shell-free paper build with PDF hash evidence;
- revision-guarded multi-agent task state and role leases;
- compact handoff, stale-lease reporting, writer/reviewer separation, and two-failure circuit breaking;
- Windows + Ubuntu CI on Python 3.11 and 3.13.

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

## Next priorities

- algorithm/runtime benchmarking;
- reusable modeling modules after repeated real-world need.

## License

MIT

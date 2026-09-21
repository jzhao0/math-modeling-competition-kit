# Math Modeling Competition Kit

[![PyPI](https://img.shields.io/pypi/v/math-modeling-competition-kit?label=PyPI)](https://pypi.org/project/math-modeling-competition-kit/)
[![Python](https://img.shields.io/pypi/pyversions/math-modeling-competition-kit)](https://pypi.org/project/math-modeling-competition-kit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reusable engineering toolkit for mathematical modeling competitions.

## Release status

The current public alpha line is **`v0.1.0a2`**.

This release is intentionally an **engineering core**, not an algorithm encyclopedia. It exposes reusable competition-engineering capabilities while excluding private contest artifacts, raw interaction histories, local provider configuration, and active future-competition training.

> Core principle: **Choose and validate the model early. Once the model is correct, optimize the algorithm and engineering implementation instead of endlessly replacing the model.**

## What v0.1 provides

- deterministic workspace manifests;
- bounded clean-room execution;
- generic final-submission engineering audit;
- claim/evidence provenance locks and stale detection;
- cross-platform competition project scaffold;
- deterministic LaTeX source/dependency/citation audit;
- bounded shell-free paper build with PDF hash evidence;
- revision-guarded multi-agent task state and role leases;
- compact handoff, stale-lease reporting, writer/reviewer separation, and two-failure circuit breaking;
- post-model-freeze warmup/repeated-run runtime benchmarking;
- explicit runtime regression thresholds, environment-drift reporting, and output-identity locks;
- Windows + Ubuntu CI on Python 3.11 and 3.13.

Reusable modeling modules such as rolling-horizon engines, scenario reduction, or solver abstractions are **not part of v0.1 unless repeated real-project need has been established and the module has separately passed public-release review**.

## Installation

Install the current public alpha from PyPI:

```text
python -m pip install --pre math-modeling-competition-kit==0.1.0a2
```

For the newest available release line:

```text
python -m pip install --pre math-modeling-competition-kit
```

From a source checkout:

```text
python -m pip install .
```

Verify the installation:

```text
mmkit --help
mmkit-final-gate --help
python -c "import mmkit; print(mmkit.__version__)"
```

## Workflow

```text
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
```

## Quick start

Create a generic workspace without assuming a specific future contest:

```text
mmkit init demo-project --competition CUSTOM --year 2027
cd demo-project
mmkit coord status .
mmkit reproduce . config/run_manifest.json --json coordination/reproduction.json
mmkit benchmark run . config/benchmark.json --json coordination/benchmark.json
mmkit paper init .
mmkit paper audit . paper/main.tex --json coordination/paper_audit.json
```

After a correct implementation is selected, lock an explicit runtime/output baseline before optimizing it:

```text
mmkit benchmark lock coordination/benchmark.json \
  --output coordination/benchmark.baseline.json \
  --max-regression-percent 15

mmkit benchmark compare \
  coordination/benchmark.json \
  coordination/benchmark.baseline.json \
  --json coordination/benchmark.compare.json
```

When a TeX runtime is installed and the build contract is configured:

```text
mmkit paper build . config/paper_build.json --json coordination/paper_build.json
```

## Documentation

See:

- `docs/PROJECT_SCAFFOLD.md` — workspace contract;
- `docs/MVP_REPRODUCIBILITY_FINAL_GATE.md` — clean-room and final-gate semantics;
- `docs/PROVENANCE_MVP.md` — claim/evidence locking;
- `docs/PAPER_PIPELINE_MVP.md` — paper auditing/build semantics;
- `docs/AGENT_COORDINATION.md` — multi-agent checkpoint/handoff semantics;
- `docs/ALGORITHM_RUNTIME_BENCHMARKING.md` — post-model-freeze performance measurement;
- `docs/HISTORY.md` — concise public project lineage;
- `docs/RELEASE_SCOPE_V0.1.md` — public release boundary;
- `docs/PUBLISHING.md` — Trusted Publishing release procedure.

## Repository structure

- `src/mmkit/` — reusable Python package;
- `tools/` — release/final-gate and audit utilities;
- `coordination/` — public coordination contracts;
- `tests/` — automated tests;
- `docs/` — architecture, contracts, roadmap and release documents.

Historical private-workbench snapshots are intentionally not retained on the current public branch.

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
10. Postmortems are converted into reusable tooling only after privacy/provenance/reuse review.

## Publication boundary

Future competition training and new competition-specific work are private by default. They are not copied into this public repository during active preparation or competition. Any later publication requires a separate post-competition distillation, provenance/license review, tests, PR, and explicit human publication decision.

## Security

Do not commit credentials, tokens, private keys, raw account data, or local secret files. See `SECURITY.md`.

## License

MIT

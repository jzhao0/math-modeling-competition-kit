# Architecture Principles

## Research vs production

Research may contain:
- alternative models;
- ablation studies;
- sensitivity analysis;
- experimental solvers;
- diagnostics;
- historical experiments.

Production must contain only the minimal complete path required to regenerate formal outputs.

A formal submission must never depend on historical research artifacts.

## Model lifecycle

MODEL_PROPOSED
-> MODEL_VALIDATED
-> MODEL_FROZEN
-> IMPLEMENTATION_VALIDATED
-> PRODUCTION_READY

After `MODEL_FROZEN`, changes should primarily target implementation efficiency unless a conceptual defect is discovered.

## Optimization hierarchy

After correctness:
1. eliminate redundant solves;
2. reuse mathematical structure;
3. reduce Python overhead;
4. reduce I/O;
5. exploit sparse representations;
6. tune the solver;
7. parallelize truly independent tasks;
8. reduce the production DAG.

Changing the mathematical model is not the default optimization strategy.

## Reproducibility levels

Report separately:
1. scientific equivalence;
2. reporting-precision equivalence;
3. bit-exact equivalence.

Do not confuse serialization-level differences with scientific differences.

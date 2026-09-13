# Roadmap

## Phase 0 - Foundation
- [x] Repository skeleton
- [ ] Python package metadata
- [ ] Minimal CI
- [ ] Contribution rules

## Phase 1 - Competition project template
Create a reusable scaffold with:
- inputs
- research
- production
- validation
- paper
- submission
- coordination
- tools

Rule: production must not depend on research artifacts.

## Phase 2 - Clean-room reproduction
Build `tools/cleanroom_reproduce.py` to:
- create a fresh workspace;
- copy only production sources;
- copy declared inputs;
- detect hidden dependencies;
- detect source-tree writes;
- execute the formal pipeline;
- compare outputs at scientific/reporting precision;
- generate a machine-readable report.

## Phase 3 - Final submission gate
Build `tools/final_gate.py` to check:
- paper build;
- page limits;
- citations/references;
- expected workbooks;
- support archive;
- appendix/support consistency;
- absolute path leaks;
- archive integrity;
- file-size limits;
- MD5/SHA256.

## Phase 4 - Claim provenance
Track:
- claim_id
- paper_location
- producer
- input
- artifact
- value
- precision
- status

Goal:
CLAIM -> DATA -> CODE -> OUTPUT -> PAPER

## Phase 5 - Algorithm optimization
Once the formal model is frozen and correct, benchmark:
- runtime;
- peak memory;
- solver calls;
- I/O count;
- model rebuild count;
- scenario count;
- clean-room reproducibility.

Optimization topics:
- warm start;
- model reuse;
- sparse matrix construction;
- vectorization;
- rolling-horizon state reuse;
- scenario reduction;
- solver tuning;
- parallel execution;
- I/O reduction.

## Phase 6 - Paper automation
Reusable LaTeX support for CUMCM and MCM/ICM:
- abstract formatting;
- Chinese section numbering;
- superscript numeric citations;
- booktabs tables;
- appendix formatting;
- source-code appendix;
- figure registry;
- AI usage declaration.

## Phase 7 - Multi-agent orchestration
Formalize:
- authoritative facts;
- worker isolation;
- READY/BLOCKED contracts;
- runtime budgets;
- scope boundaries;
- final integrator;
- freeze protocol.

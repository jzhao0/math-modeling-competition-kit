# v0.1 public release scope

Status: ALPHA CANDIDATE  
Target: `v0.1.0a1`

## Source lineage

The `v0.1.x` public line is limited to generic engineering capabilities distilled from the completed CUMCM 2026 development cycle and the public hardening work that followed it.

This release line is intentionally **not** a publication of the original competition solution, private competition artifacts, private prompts, teacher-specific material, local provider configuration, or historical internal state.

## Included public capabilities

- reproducibility manifests and bounded clean-room execution;
- final-submission engineering audit;
- claim/evidence provenance locking and stale detection;
- generic project scaffolding;
- paper source/dependency/citation audit and bounded build contract;
- context-resilient agent coordination primitives;
- post-model-freeze runtime/output benchmarking;
- CI, packaging, release metadata, and distribution safety checks needed to ship those capabilities.

## Explicitly excluded from v0.1

- active or future MCM/ICM training material;
- competition-specific modeling ideas, tactics, prompts, examples, adapters, experiments, or failure records from an unfinished future competition cycle;
- newly discovered reusable techniques that have not passed post-competition distillation;
- private controller state;
- frozen competition answer artifacts;
- deferred-license/provenance third-party templates or vendor assets;
- placeholder modeling namespaces as a promise of implemented modeling APIs.

## Embargo rule for future competitions

Future competition work is private by default. During training and competition, public maintenance may continue only for already-released capabilities, packaging, CI, documentation, bug fixes, and security/reliability work that does not expose embargoed competition material.

After the relevant future competition ends, candidate material may be considered through a new publication gate:

```text
private evidence
-> repeated-need review
-> de-competition/generalization
-> privacy/provenance/license review
-> tests
-> public PR
-> explicit human publication decision
```

There is no automatic private-to-public synchronization.

## Scientific boundary

MMKit machine checks establish engineering properties such as identity, freshness, declared reproducibility, packaging safety, dependency relationships, and runtime/output regression against explicit contracts. They do not certify model validity, mathematical correctness, scientific truth, global optimality, or contest-rule compliance for an arbitrary event.

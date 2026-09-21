# v0.1 public release scope

Status: ALPHA  
Current candidate: `v0.1.0a2`

## Public boundary

The `v0.1.x` line contains reusable engineering capabilities and the release/security infrastructure needed to ship them as a standalone public package.

It is intentionally **not** a publication of competition answers, private competition artifacts, raw interaction histories, private prompts, teacher-specific material, local provider configuration, personal paths, or historical private-workbench snapshots.

## Included public capabilities

- reproducibility manifests and bounded clean-room execution;
- final-submission engineering audit;
- claim/evidence provenance locking and stale detection;
- generic project scaffolding;
- paper source/dependency/citation audit and bounded build contract;
- context-resilient agent coordination primitives;
- post-model-freeze runtime/output benchmarking;
- CI, packaging, release metadata, and distribution safety checks.

## Explicitly excluded

- active or future competition training material;
- competition-specific modeling ideas, tactics, prompts, examples, adapters, experiments, or failure records from unfinished future work;
- newly discovered reusable techniques that have not passed a separate publication review;
- private controller state and provider-local configuration;
- frozen competition answer artifacts;
- raw chats or interaction logs;
- deferred-license/provenance third-party templates or vendor assets.

## Future publication gate

Future private work remains private by default. Candidate material may be considered later through:

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

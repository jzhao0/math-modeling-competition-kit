# Competition project scaffold

P4 adds a cross-platform workspace initializer:

```text
mmkit init <destination> --competition <CUMCM|MCM|ICM|CUSTOM> --year <YYYY>
```

Example:

```text
mmkit init MCM-2027 --competition MCM --year 2027 --name MCM-2027
```

The scaffold is intentionally generic. It does not copy private prompts,
teacher-specific rules, competition-specific solution code, or historical
migration snapshots.

## Workspace layout

```text
<workspace>/
├── problem/
├── data/
│   ├── raw/
│   └── processed/
├── analysis/
├── models/
├── results/
│   ├── tables/
│   └── figures/
├── paper/
├── scripts/
├── supporting/
├── ai_logs/
├── references/
├── submission/
├── coordination/
├── config/
├── gates/
├── AGENTS.md
├── competition.json
└── README_WORKSPACE.md
```

`submission/` is the only canonical final-submission directory.

## Immediate smoke

The generated `config/run_manifest.json` and `scripts/smoke.py` are valid P1
clean-room inputs, so a newly created workspace can immediately run:

```text
mmkit reproduce . config/run_manifest.json --json coordination/reproduction.json
```

The expected output is `results/smoke.txt`.

## Claim/evidence provenance

The scaffold writes a P3-compatible registry at:

```text
coordination/CLAIM_REGISTRY.csv
```

Once important claims have real evidence:

```text
mmkit provenance lock . coordination/CLAIM_REGISTRY.csv --output coordination/CLAIM_PROVENANCE.lock.json
mmkit provenance verify . coordination/CLAIM_REGISTRY.csv coordination/CLAIM_PROVENANCE.lock.json --json coordination/CLAIM_PROVENANCE.verify.json
```

A provenance PASS means the locked claim rows and evidence bytes remain current.
It does not certify scientific correctness.

## Safe force behavior

By default `mmkit init` refuses to operate in a non-empty destination.

`--force` means **fill missing scaffold files only**. Existing files are never
overwritten. This makes it possible to add the MMKit control structure to an
existing competition workspace without silently replacing user work.

## Human gates

The generated `gates/` directory seeds four human decisions:

- G1 problem choice
- G2 model route
- G3 results
- G4 submission

Agents may assist with evidence and checklists but must not approve these gates
on behalf of the human team.

# Claim / Evidence Provenance MVP

MMKit P3 binds important paper claims to exact evidence bytes.

The goal is not to prove that a mathematical result is scientifically correct.
The goal is to make stale evidence mechanically visible when a paper claim,
producer script, input file, or result artifact changes.

## Human-editable registry

Use a CSV with these required columns:

```csv
claim_id,paper_location,producer,input,artifact,value,precision,status
Q1.OBJ,Sec. 4.1,src/q1.py,data/input.csv,results/q1.json,12.34,0.01,APPROVED
```

Rules:

- `claim_id` must be unique.
- `paper_location`, `artifact`, `value`, and `status` are required.
- `producer`, `input`, and `artifact` are workspace-relative file paths.
- absolute paths, `..` escapes, symlinks, missing evidence files, and non-files are rejected.
- generic claim state `PASS` is rejected because evidence strength must be explicit.

The repository seed is `coordination/CLAIM_REGISTRY.csv`.

## Lock evidence

```bash
mmkit provenance lock . coordination/CLAIM_REGISTRY.csv \
  --output coordination/CLAIM_EVIDENCE.lock.json
```

The lock stores:

- canonical claim-row fingerprints;
- SHA-256 and size for the producer, input, and artifact files;
- the registry semantic fingerprint;
- `proof_level = MACHINE_VERIFIED`;
- an explicit scope note that scientific correctness is not certified.

## Verify evidence

```bash
mmkit provenance verify . coordination/CLAIM_REGISTRY.csv \
  coordination/CLAIM_EVIDENCE.lock.json \
  --json provenance-report.json
```

A clean verification returns exit code `0` and `status = PASS`.

If a claim row changes, evidence bytes change, a path changes, a file disappears,
or a new unbound claim is added, verification returns exit code `2` and
`status = STALE`.

The JSON report includes per-claim status plus expected and current evidence
fingerprints, so an integrator can see exactly which upstream dependency changed.

## Intended workflow

1. compute or regenerate results;
2. review the scientific result;
3. record the paper-facing claim in the registry;
4. create or refresh the evidence lock;
5. write the paper from approved evidence;
6. run `mmkit provenance verify` before paper/final-gate approval;
7. if evidence becomes stale, rerun only the dependent downstream checks.

The lock is a provenance boundary, not a substitute for human model validation,
domain judgment, citation verification, or final human review.

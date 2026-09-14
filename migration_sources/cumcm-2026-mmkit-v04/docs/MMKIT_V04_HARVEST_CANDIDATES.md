# MMKit v0.4 — External Harvest Integration Record

Updated: 2026-09-09

This document began as the backlog distilled from `GITHUB_FINAL_MATHMODELING_STACK_AUDIT_20260909.md`. The high-value governance items have now been integrated into MMKit-native policy **without making the external repositories runtime dependencies**.

Canonical implementation surfaces:

- source/pin record: `vendor/CANDIDATE_SKILLS_V04.yaml`
- reviewed-source manifest overlay: `vendor/SKILLS_MANIFEST_V04.yaml`
- capability routing overlay: `config/skill_registry_v04.yaml`
- evidence/gate policy: `config/evidence_governance.yaml`
- consolidated stack: `docs/ACADEMIC_SKILL_STACK_V04.md`
- exact G4 policy: `docs/G4_EXACT_FILE_LOCK.md`
- AI disclosure policy: `docs/AI_DISCLOSURE_STYLE.md`
- G4 machine helper: `scripts/g4_bundle_audit.py`
- G4 packaging execution prompt: `prompts/CUMCM_G4_PACKAGING_FIX.md`

## Integrated P0 core

### 1. Gate hash invalidation — INTEGRATED

Approvals bind upstream fingerprints. Material upstream change makes dependent gate `STALE`.

For G4, the binding includes the exact paper, support archive and AI-detail hashes. Any byte change requires new checksums and new human approval.

### 2. Evidence credential levels — INTEGRATED

Formal reports distinguish:

- `MACHINE_VERIFIED`
- `HUMAN_CONFIRMED`
- `SNAPSHOT_ONLY`
- `UNVERIFIED`

An Agent's prose `PASS` is not evidence by itself.

### 3. Writer evidence-only contract — INTEGRATED

Formal paper facts may come from approved result tables, claim/evidence, verified citations, approved assumptions/definitions and selected figures/source data. Chat memory, Agent self-report, rejected outputs and unexecuted code are excluded as truth sources.

### 4. Assumption sensitivity precheck — INTEGRATED

Material ambiguity requires competing interpretations, boundary/small-case checks, downstream consistency and a recorded decision. Unresolved material ambiguity goes to a human gate.

### 5. Pilot comparison contract — INTEGRATED

A candidate model comparison requires the same split, information visibility and primary metric, at least one interpretable baseline, and real execution. Failed candidates are recorded as failures rather than assigned invented metrics.

## Integrated P1 review/recovery

### 6. Reviewer independence declaration — INTEGRATED

Review reports distinguish context isolation, implementation independence and model/provider independence. Shared-context role play cannot be called independent recalculation.

### 7. Checkpoint rollback — POLICY INTEGRATED

A human rejection should return to the precise upstream stage, preserve verified predecessors and invalidate dependent downstream status, not restart the entire project by default.

### 8. Process bypass ledger — POLICY INTEGRATED

Formal-artifact edits should record edit origin, new fingerprint, verifier to rerun and dependent gate status. This prevents a changed file from retaining a stale green PASS.

### 9. Integrity forensics — INTEGRATED FOR G4

Bounded G4 review now covers claim/table/figure/appendix consistency, claimed files/experiments, internal workflow leakage and support-package dependency consistency.

Anti-Autoresearch-style AI-writing impressions have **zero verdict weight** and only trigger human reading.

## Integrated P2 AI disclosure

### 10. Evidence-style AI disclosure — INTEGRATED

Official/teacher fields remain authoritative. Representative interactions should show:

`AI suggestion → team adoption/modification/rejection → real verification`.

Unavailable history is stated truthfully once, not mechanically repeated throughout the attachment.

## G4 clean-room capability added

The harvest exposed a missing MMKit capability: a package could pass in the author's full workspace while failing when a reviewer extracted the actual submission ZIP.

v0.4 therefore adds an explicit clean-room contract and `scripts/g4_bundle_audit.py` to check exact-file hashes, ZIP path safety, local-path/secret leakage, AI-PDF byte identity, Python syntax and optional declared `RUN_MANIFEST.json` commands.

This tool verifies submission engineering; it never certifies mathematical correctness.

## Explicit non-goals retained

v0.4 still does **not** do:

- default multi-Agent debate;
- autonomous one-prompt final submission;
- fixed figure count;
- fixed paper page target;
- complete-source dump in the paper appendix by default;
- AI-text-classifier compliance verdicts;
- autonomous resolution of material uncertainty;
- wholesale migration to ModexAgent, Mrite, ARIS, Remit or another third-party platform;
- contest-time GitHub search/fetch of new modeling skills.

The core remains:

**filesystem state + deterministic evidence + evidence-bound writing + bounded Agent + human decision**.

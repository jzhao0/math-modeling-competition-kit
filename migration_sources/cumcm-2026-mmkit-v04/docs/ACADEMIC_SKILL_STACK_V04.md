# MMKit v0.4 Academic / Mathematical-Modeling Stack

Updated: 2026-09-09

## 1. Why v0.4 exists

v0.4 does **not** add another autonomous Agent platform. It consolidates the useful mechanisms found in the final pre-contest GitHub scan into MMKit-native policy while preserving the architecture already validated by three drills:

`filesystem state + deterministic computation + evidence-bound writing + bounded Agent + human gates`.

The final external-source audit is recorded in:

- `docs/GITHUB_FINAL_MATHMODELING_STACK_AUDIT_20260909.md`
- `vendor/CANDIDATE_SKILLS_V04.yaml`
- `docs/MMKIT_V04_HARVEST_CANDIDATES.md`

The machine-readable governance layer is `config/evidence_governance.yaml`.

## 2. Authority order

For CUMCM work, use the following order when rules conflict:

1. official current-year competition rules;
2. latest explicit teacher instruction for the current deliverable;
3. teacher-provided `cumcm-step-review` and teacher template materials;
4. Sol/human scientific decisions and frozen project evidence;
5. MMKit native governance and quality policy;
6. selectively distilled third-party sources;
7. reference-only external repositories.

A third-party skill can never silently override the teacher, a human gate, or verified numerical evidence.

## 3. Active native capabilities

### A. Problem / modeling route

Owner: Sol + human.

Required behavior:

- identify material ambiguities before model selection;
- test at least two plausible interpretations when the ambiguity changes the solution;
- establish an interpretable baseline;
- compare candidates on the same data split, information set and primary metric;
- record failed candidates honestly rather than inventing comparison numbers;
- require a real gain before accepting unnecessary complexity.

Sources distilled from MathModel-Skill, Remit and MathModelAgent.

### B. Deterministic evidence

Owner: local Python/R/MATLAB/Mathematica programs.

Every important result should have an identifiable evidence level:

- `MACHINE_VERIFIED`
- `HUMAN_CONFIRMED`
- `SNAPSHOT_ONLY`
- `UNVERIFIED`

Agent prose such as “PASS” is not itself evidence. Paper Workbench is the main external inspiration for this distinction.

### C. Formal writing

The formal writer may use only approved evidence:

- verified result tables;
- claim/evidence register;
- verified references;
- approved assumptions/definitions;
- selected figures and their source data.

Conversation memory and Agent summaries can help navigation but are not numerical truth sources.

Teacher `cumcm-step-review` remains the primary CUMCM exposition authority. Each substantive question should expose the real chain:

`动机 → 比选 → 建模/参数依据 → 求解过程 → 中间证据 → 验证 → 解读`.

### D. Figures

Numerical truth stays with frozen data/results. Figure tools may change presentation only.

Current references include Nature figure rules, MMKit figure contracts and optionally `sci-box` archetypes. No figure is redrawn merely because a new template repository exists.

### E. Review / integrity

Before G4:

- science review;
- human-style / judge-view PDF read;
- deterministic consistency checks;
- bounded integrity forensics;
- support-package clean-room test.

ARIS and Anti-Autoresearch contribute the principle that a generator's self-reported PASS is not independent proof. Anti-Autoresearch-style AI-writing impressions have zero verdict weight and are only prompts for human inspection.

### F. Submission engineering

G4 is an **exact-file human lock**, not a generic status string.

Canonical files:

- `competition_paper.pdf`
- `AI工具使用详情.pdf`
- `supporting_material.zip`

The support ZIP must be tested after extraction outside the project tree. If the paper says the code is complete/runnable, that statement needs clean-room execution evidence. The AI-detail PDF inside the ZIP must be the exact same bytes as the standalone canonical AI-detail PDF.

See `docs/G4_EXACT_FILE_LOCK.md`.

## 4. External-source dispositions

### High-value distilled policy

**Paper Workbench** — evidence credentials, deterministic checkpoints, gate invalidation, process ledger.

**MathModel-Skill Standard/Pro** — compute first, evidence hashes, evidence-only writer, real independence declarations.

**Remit** — same-protocol pilot comparison, checked-results-only writing, precise rollback/resume.

**Anti-Autoresearch** — bounded integrity forensics and distrust of unsupported self-attestation.

### Reference-only

**MathModelAgent** — assumption precheck and modeling-to-code handoff. Repository license metadata was not clear enough for vendoring.

**Mrite** — useful input inventory / compute-then-plot ideas, but its explicit unattended/no-confirmation policy conflicts with MMKit G1–G4 and is rejected.

**ModexAgent** — useful generic architecture ideas (persistent workspace, approvals, skill supply, trace), but it is not a math-modeling-specific solution and MMKit does not migrate to it.

**ARIS** — useful adversarial-review/persistence methodology; full autonomous research loop is disabled for CUMCM.

**sci-box** — figure/diagram archetype reference; no vendoring without license clarity.

### Existing vendored source held stable

`cumcm-live-workflow-skill` remains on the already-tested MMKit vendored pin. Its newer v5.1 was reviewed as a **policy delta source**, not automatically promoted as runtime. Useful newer details may be re-expressed natively, while conflicting fixed figure/page/appendix rules are rejected.

### Not found / not claimed

`meta-model-skills-max`: no trustworthy public match identified.

`ai-use-statement`: no unique relevant public repository identified. MMKit therefore implements only the disclosure pattern, not a fictional source.

## 5. Teacher extensions

### `cumcm-step-review`

The participant-supplied teacher archive is frozen by archive SHA-256 and its inspected rules are already integrated. It remains more authoritative than generic public CUMCM skills for paper structure/review.

### `mathmodels`

Teacher package `zhjx19/mathmodels@13adbe0...` version 0.0.13 is a prequalified optional R runtime. It can support future method routes after review, but it is not retrofitted into an already-frozen scientific result merely because it is available.

## 6. Competition-day freeze

Once the live problem is released:

- no GitHub/CSDN/community solution search;
- no fetching new external skills;
- no upgrading external skill pins;
- no new platform migration;
- use locally frozen MMKit policy/templates/dependencies only.

External sources are a **pre-contest knowledge supply chain**, not a live contest dependency.

## 7. v0.4 non-goals

- no default multi-Agent debate;
- no autonomous “one prompt → final submission” mode;
- no fixed figure count;
- no fixed paper page target;
- no full-code dump into the paper appendix by default;
- no AI-detector gaming;
- no replacing human G4 with automated PASS;
- no treating repository popularity as scientific evidence.

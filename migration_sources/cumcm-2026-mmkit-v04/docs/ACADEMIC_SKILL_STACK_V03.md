# MMKit v0.3 Academic + Competition Visual Stack

Updated: 2026-09-04  
Status: **SELECTED / DISTILLED; NO WHOLE-SUITE AUTONOMOUS PIPELINE**

## Why this layer exists

Drill-02 passed scientific checks, plagiarism checks, AIGC checks, compilation, reproducibility, anonymity and a 140-page visual audit. Manual reading still exposed defects that the automated gates missed: raw floating-point precision, visible hyperlink boxes, inconsistent page-number placement, figures separated from their explanatory text, insufficient state diagrams, excessive parenthetical asides, internal audit language and recognisable LLM-style defensive phrasing.

A second lesson came from the visual review: CUMCM is a judged modeling competition, not a journal production exercise. A technically correct but visually flat paper can underperform. MMKit therefore treats **human manuscript quality** and **competition visual impact** as separate first-class layers after scientific truth and evidence traceability.

External projects provide patterns or optional capabilities; they do not own the workflow and cannot override Sol or the G1–G4 human gates.

## Integration modes

- **VENDORED_SKILL** — already frozen locally under the v0.2 P1 supply chain.
- **DISTILLED_POLICY** — upstream was audited; MMKit stores adapted native rules/checklists. The upstream runtime is not needed during the contest.
- **REFERENCE_ONLY** — useful ideas only; no code is redistributed or relied upon at contest runtime.
- **OPTIONAL_RUNTIME** — an optional locally installed backend; must be installed and validated before the contest, with a deterministic fallback.

## Selected v0.3 sources

| Source | Pinned review commit | License status | MMKit role | Integration |
|---|---|---|---|---|
| `DT-wanf/SCI-Skills` | `b403d661…` | no clear repo license metadata | stage/evidence workflow reference | REFERENCE_ONLY |
| `WUBING2023/PaperSpine` | `1fe46f0e…` | MIT | contribution-first argument architecture, evidence bank, claim register | DISTILLED_POLICY |
| `yujie-jason-zhang/horizon-academic-writing` | `87c2ca65…` | MIT | claim-forward, claim/TeX-preserving polish | DISTILLED_POLICY |
| `SyntaxSmith/humanize-paper` | `ba796b08…` | MIT | Chinese human-style review, defensive/repeated/internal-artifact signals | DISTILLED_POLICY |
| `JilinMen/SCI-polish-skill` | `56222b0a…` | ambiguous repo metadata; bundled metadata references CC-BY-NC-4.0 | writing/LaTeX/figure review ideas only | REFERENCE_ONLY |
| `VincenzoImp/academic-research-skills` | `28a4f18e…` | MIT | package/submission/reproducibility patterns | DISTILLED_POLICY |
| `jjfroehlich/agent-skills-for-academic-research` | `9b1b256e…` | MIT | secondary writing/dataviz checklist source, >290 curated resources claimed upstream | REFERENCE_ONLY |
| `qcmuu/AI-Research-Skills` | `7678a703…` | MIT | selected academic plotting/paper-writing ideas | REFERENCE_ONLY |
| `jing1312/nature-figure-skill` | `d881e2ea…` | MIT | figure contract and visual/export QA | DISTILLED_POLICY |
| `synthetic-sciences/openscience` | `3b979e85…` | Apache-2.0 | local-first/provenance/skill-catalog architecture | REFERENCE_ONLY |
| `Ge-Shun/origin-mcp` | `fecb7226…` | MIT | optional Origin 2D/3D/contour/fitting/showcase backend | OPTIONAL_RUNTIME |
| `Yike-Ye/OriginLab-MCP` | `6e39f88c…` | MIT | verify-actual-Origin-action pattern | REFERENCE_ONLY |

The exact full SHAs and decisions are recorded in `vendor/CANDIDATE_SKILLS_V03.yaml` and the authoritative `vendor/SKILLS_MANIFEST.yaml`.

## What was actually integrated

### 1. Argument architecture

PaperSpine-style contribution/evidence thinking is implemented as MMKit-native artifacts:

```text
CLAIM_EVIDENCE.csv
        ↓
03_analysis/CLAIM_REGISTER.md
        ↓
03_analysis/PAPER_PLAN.md
        ↓
section-level draft from frozen evidence
```

This prevents the paper from becoming a chronology of implementation and debugging.

### 2. Claim-preserving polish

Horizon-style fidelity and claim-forward ideas are now policy:

- preserve numbers, formulas, citations, TeX, modality, negation and scope;
- state supported claims directly instead of burying them under redundant disclaimers;
- rewrite only after the scientific claim is frozen;
- any requested change to scientific meaning routes back to Sol.

### 3. Human-style review

The humanize-paper / SCI writing-quality ideas are adapted into `config/paper_quality.yaml` and `scripts/audit_human_paper.py`.

The review specifically looks for:

- repeated “仅 / 绝不 / 不构成 / 本文不报告 / 不在本文范围” frames;
- long parenthetical arguments;
- repeated problem–method–benefit templates;
- internal Agent/audit/pipeline/handoff language;
- implementation history presented as scientific organization;
- raw machine precision;
- slash-separated tuple dumps and informal numeric ranges;
- generated-looking code comments and private absolute paths.

This is **not** an AI-detector-evasion layer. It is a scientific-writing and reader-quality layer; the official AI disclosure remains truthful and complete.

### 4. Competition visual layer

Nature-figure/data-visualization principles are adapted, but journal minimalism is not treated as the CUMCM objective.

`config/figure_quality.yaml` and `config/contest_visual.yaml` define three figure intents:

- `EVIDENCE_NUMERICAL` — accurate result reading;
- `STRUCTURAL_SCIENTIFIC` — model/state/process explanation;
- `SHOWCASE_PRESENTATION` — visual impact and memory value while remaining grounded in verified content.

The figure path is:

```text
frozen result/model
      ↓
figure contract
      ↓
renderer (Python / R / optional Origin)
      ↓
scientific QA + visual QA
      ↓
figure placed near the argument it supports
```

## 3D policy: scientific 3D + presentation 3D

MMKit no longer bans 3D unless a real third variable exists.

### DATA_3D

The third axis is quantitative. Examples:

- two-parameter response surfaces;
- sensitivity surfaces/meshes;
- 3D scatter;
- contour + surface/projected slice combinations.

### PRESENTATION_3D

Depth/perspective is deliberately decorative. Examples:

- 3D columns for categorical comparisons;
- beveled/extruded bars;
- ribbon/extruded trend lines;
- spatial composition that improves page hierarchy.

This is explicitly allowed because visual presentation matters in a modeling competition. Constraints are narrow and scientific:

- decorative depth is not labeled as a measured variable;
- values, ordering, intervals and units remain unchanged;
- perspective cannot make the reader infer a false ranking;
- direct value labels or a nearby table are preferred when exact reading matters;
- no synthetic surface interpolation is presented as computed evidence without disclosure.

## Origin MCP route

`Ge-Shun/origin-mcp` is integrated as an **optional** showcase backend, not as a required dependency. The reviewed project documents Origin/OriginPro automation for 2D, 3D, contour, statistical/specialized plots, fitting and publication-style export.

Use Origin when it materially improves visual quality, especially for:

- 3D columns;
- response/sensitivity surfaces;
- contour projections;
- fitting visualizations;
- polished multi-layer graph composition.

Python/R remain deterministic fallback and data source. The actual Windows contest host still needs a pre-contest installation/doctor smoke before Origin can be relied upon. See `docs/ORIGIN_MCP_BACKEND.md`.

## Competition-paper pipeline after G3

```text
frozen numerical evidence
        ↓
claim register + evidence bank
        ↓
argument / section blueprint
        ↓
first draft from evidence
        ↓
formula + figure integration pass
        ↓
claim-preserving academic polish
        ↓
deterministic human-paper risk audit
        ↓
human-style review
        ↓
judge-view PDF review: science + presentation
        ↓
G4 submission engineering
```

### Formula + figure integration

A formula is not a substitute for a state/process diagram, and a diagram is not a substitute for a derivation. State-space, belief-update, rework and multistage models should combine both when that reduces cognitive load. Figures belong near the first explanation of their role, not collected later to satisfy a density target.

### Numerical presentation

Use decision-relevant precision:

- abstract/prose: normally 2 decimals;
- result tables: normally 2–4 decimals;
- figures: normally 2–3 decimals;
- full machine precision only where reproducibility or a close decision boundary requires it.

Parallel mappings should be stated explicitly or shown in a compact table rather than `/`-separated tuples. Numeric ranges should use ordinary prose or interval notation, not informal `~`/`～` output style.

### PDF presentation

Drill-02 defects are now explicit G4 checks:

- page numbers in the official location;
- running header off by default;
- `hyperref` borders hidden (`\\hypersetup{hidelinks}`) while links remain functional;
- no red/green boxes around figure/table/equation/reference numbers;
- readable figures/tables/equations at 100% PDF and A4 print;
- visual rhythm assessed by a human judge-view pass, not only page-geometry automation.

## Submission/code engineering

`09_submission/` is the one canonical final directory. `FINAL/` remains only as a deprecated compatibility marker for older workspaces.

Support code should read like ordinary scientific source code: concise names/comments explaining mathematics, I/O, units, seeds and non-obvious logic. Remove Agent handoff history, internal audit labels, generated Step 1/2/3 narration and verbose docstrings that merely restate code. This is readability cleanup, not concealment; AI use remains declared in the official AI materials.

## Disabled by design

The following are not enabled as the default CUMCM path:

- OpenScience autonomous long-horizon orchestration;
- the large SCI-polish multi-agent ensemble;
- the full 99-skill AI-Research-Skills lifecycle;
- multi-agent debate/voting as a normal paper writer;
- contest-time GitHub or external skill installation.

Drill-02 showed that open-ended Agent work can cost more time than the scientific task. MMKit uses selected local rules and bounded tasks instead.

## Remaining host-level item

The **system integration is complete**, but Origin MCP is intentionally marked optional until it is installed and smoke-tested on the actual Windows contest host. Failure of that optional backend must never block a problem: Python/R remain available.

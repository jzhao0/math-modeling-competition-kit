param(
    [Parameter(Mandatory=$true)][string]$Name,
    [string]$DestinationRoot = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
    $DestinationRoot = Split-Path -Parent $RepoRoot
}
$Workspace = Join-Path $DestinationRoot $Name

if ((Test-Path $Workspace) -and -not $Force) {
    Write-Host "Workspace already exists: $Workspace" -ForegroundColor Yellow
    Write-Host "Use -Force only if you intentionally want to fill missing scaffold files."
} else {
    New-Item -ItemType Directory -Force $Workspace | Out-Null
}

# v0.3 keeps FINAL only as a compatibility/deprecation marker so older tooling
# does not break. 09_submission is the ONLY canonical submission directory.
$dirs = @(
    '00_problem','01_data_raw','02_data_processed','03_analysis','04_models',
    '04_models\r','05_results','05_results\tables','05_results\figures',
    '06_paper','07_scripts','07_supporting','08_ai_logs','09_references',
    '09_submission','human_gates','config','FINAL'
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Force (Join-Path $Workspace $d) | Out-Null }

function Write-Seed([string]$Relative,[string]$Content) {
    $path = Join-Path $Workspace $Relative
    if (-not (Test-Path $path)) {
        $parent = Split-Path -Parent $path
        if ($parent) { New-Item -ItemType Directory -Force $parent | Out-Null }
        Set-Content -Path $path -Value $Content -Encoding UTF8
    }
}

function Write-SeedRaw([string]$Relative,[string]$Content) {
    $path = Join-Path $Workspace $Relative
    if (-not (Test-Path $path)) {
        $parent = Split-Path -Parent $path
        if ($parent) { New-Item -ItemType Directory -Force $parent | Out-Null }
        [System.IO.File]::WriteAllText($path, $Content, (New-Object System.Text.UTF8Encoding $false))
    }
}

$now = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')

Write-Seed 'STATUS.yaml' @"
project: $Name
created_at: $now
infra_version: mmkit-v0.3-P3
infra_inherited: true
stage: problem_intake
problem_choice: undecided
model_route: undecided
results_confirmed: false
paper_build: pending
submission_ready: false
canonical_submission_dir: 09_submission
current_gate: G1_problem_choice
"@

Write-Seed 'ASSUMPTION_LEDGER.md' @"
# Assumption Ledger

| ID | Assumption | Why needed | Evidence / test | Status |
|---|---|---|---|---|
| A001 |  |  |  | OPEN |
"@
Write-SeedRaw 'CLAIM_EVIDENCE.csv' "claim_id,claim,evidence_path,code_or_method,status"
Write-Seed 'DECISION_LOG.md' @"
# Decision Log

- $now — Workspace created (MMKit v0.3 scaffold).
"@

# Human gates
Write-Seed 'human_gates\G1_problem_choice.md' @"
# G1 — Problem Choice

APPROVED: NO

- [ ] Statement + attachments stored read-only in 00_problem/ with original hash.
- [ ] Candidate problems compared (structure, data, workload, risk, verifiability).
- [ ] Team confirms final choice.
- [ ] Record choice in STATUS.yaml and DECISION_LOG.md.
"@

Write-Seed 'human_gates\G2_model_route.md' @"
# G2 — Model Route

APPROVED: NO

Requires 03_analysis/METHOD_ROUTE.md.

- [ ] Route decided (Python / R / MATLAB / Mathematica) with reasons.
- [ ] Assumptions explicit.
- [ ] Baseline defined.
- [ ] State representation / reduction closure checked before long solves when applicable.
- [ ] Alternatives considered and why rejected.
- [ ] Crosscheck plan defined.
- [ ] Independent review attack checklist run (objectives, constraints, units, leakage, overfitting, feasibility).
"@

Write-Seed 'human_gates\G3_results.md' @"
# G3 — Results

APPROVED: NO

- [ ] Key numbers trace to result CSVs/JSONs/figures (CLAIM_EVIDENCE).
- [ ] Units and scale checked.
- [ ] Robustness / sensitivity / ablation / error / counterfactual checks done as appropriate.
- [ ] Interpretation checked (no over-claiming).
- [ ] Figures rebuildable from frozen results.
- [ ] Central claims are ready to enter 03_analysis/CLAIM_REGISTER.md.
"@

Write-Seed 'human_gates\G4_submission.md' @"
# G4 — Submission

APPROVED: NO

- [ ] Paper complete, compiles, official page-number/format rules satisfied.
- [ ] Human judge-view PDF review complete (not only automated geometry checks).
- [ ] Hyperlink/reference boxes visually hidden; no accidental running headers unless official template requires them.
- [ ] Figure presentation quality checked: page rhythm, labels, perspective, 3D honesty and overall competition impact.
- [ ] Supporting-file list and complete runnable source-code appendix/package are consistent.
- [ ] AI tool usage declaration present; detailed AI usage PDF generated from real logs.
- [ ] Anonymity: no team member names, school info, or identifying leaks.
- [ ] Submission code human-readable and free of agent/audit boilerplate.
- [ ] 09_submission/ contains the unique final paper + support archive (+ checksum/receipt records if needed).
- [ ] No competing final artifacts are stored in FINAL/.
"@

Write-Seed 'human_gates\GATE_STATUS.md' @"
# Human Gates

- [ ] G1 — choose problem
- [ ] G2 — approve modeling route
- [ ] G3 — confirm numerical results
- [ ] G4 — final three-person review
"@

# Analysis / planning seeds
Write-Seed '03_analysis\METHOD_ROUTE.md' @"
# METHOD_ROUTE — NOT_DECIDED

State: NOT_DECIDED

Complete this file before G2. Consider Python, R, MATLAB, Mathematica explicitly.

| Field | Value |
|---|---|
| problem structure |  |
| candidate route |  |
| selected method |  |
| why selected |  |
| state/reduction closure check |  |
| why alternatives rejected |  |
| crosscheck plan |  |
"@

Write-Seed '03_analysis\FIGURE_PLAN.md' @"
# FIGURE PLAN

One row per formal figure. type = EVIDENCE_NUMERICAL | STRUCTURAL_SCIENTIFIC | SHOWCASE_PRESENTATION.

| id | type | intent | paper claim/page role | reader question | source data | visual encoding | backend | dimensions/units | presentation layer | paper section | editable source | QA owner | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F001 |  |  |  |  |  |  |  |  |  |  |  |  | planned |

Rules:
- all values/order/intervals must trace to frozen evidence;
- structural/state diagrams need scientific QA and editable source;
- place figures near the first explanation of their evidence;
- aesthetics are a legitimate competition objective after truth/readability;
- 3D may be DATA_3D or PRESENTATION_3D; decorative depth is allowed but must not masquerade as a quantitative axis;
- 3D columns, extruded/ribbon trends and perspective composition may be used when visually stronger;
- two-parameter/sensitivity results should consider surface/mesh/contour views;
- Origin is an optional showcase backend; Python/R remain deterministic fallback/data source.
"@

Write-Seed '03_analysis\CLAIM_REGISTER.md' @"
# CLAIM REGISTER

Complete after G3 and before full-paper drafting.

| claim id | problem/question | central claim | exact scope | evidence | figure/table/equation | wording risk | frozen |
|---|---|---|---|---|---|---|---|
| C001 |  |  |  |  |  |  | NO |
"@

Write-Seed '03_analysis\PAPER_PLAN.md' @"
# PAPER PLAN

Draft only from frozen evidence.

For each section record the argument before writing prose:

| section | reader question | central claim | mathematical object/derivation | evidence | figure/table | interpretation | status |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  | planned |

Human-quality rules are inherited from config/paper_quality.yaml:
- contribution/evidence first, not generic template first;
- formulas read as derivations, not dumps;
- figures integrated near explanatory text;
- long parenthetical arguments rewritten as normal sentences;
- no defensive/internal audit language in scientific body;
- raw machine precision does not enter abstract/prose;
- competition visual impact is first-class after truth/readability; showcase 3D is allowed;
- final claim-preserving polish + human-style pass required.
"@

Write-Seed '03_analysis\PAPER_HUMAN_REVIEW.md' @"
# PAPER HUMAN REVIEW

Reviewer perspective: competition judge, not build-system auditor.

- [ ] Abstract communicates method/result/meaning without raw float precision or slash-separated output dumps.
- [ ] First five pages clearly expose the paper's strongest mathematical contributions.
- [ ] Parenthetical explanations are short and genuinely secondary.
- [ ] Defensive LLM frames (仅/绝不/不构成/本文不报告/不在声明范围) are absent unless indispensable.
- [ ] Formula explanations use consistent symbol grammar.
- [ ] State/transition diagrams appear where they reduce cognitive load.
- [ ] Figures and tables are near the claims they support.
- [ ] Page rhythm avoids long stretches of visually exhausting text.
- [ ] 3D figures declare DATA_3D or PRESENTATION_3D semantics; decorative depth does not pretend to be data.
- [ ] Showcase plots are visually strong at 100% PDF/A4 size without harming exact reading.
- [ ] Decimal precision is decision-relevant and consistent.
- [ ] Page numbers/headers/link borders follow official format.
- [ ] AI declaration is concise; detailed orchestration remains in supporting material.
- [ ] Submitted source code reads like normal scientific code, not an Agent transcript.
- [ ] Run central scripts/audit_human_paper.py before G4 and review every finding manually.
"@

# Literature system
Write-SeedRaw '09_references\REFERENCE_LEDGER.csv' "key,title,authors,year,venue,doi,url,discovered_via,metadata_verified,publisher_verified,relevance,used_in_claims,notes"
Write-SeedRaw '09_references\references.bib' "% mmkit references.bib - only verified entries"
Write-Seed '09_references\README.md' @"
# Workspace References

Stages: discovered -> metadata_verified -> publisher_verified -> claim_verified.
Only publisher_verified=TRUE AND used_in_claims non-empty entries may reach the paper.
No fabricated DOI; no topic-placeholder citations; highly similar contest solution papers are not primary methodological evidence.
"@

# AI logging
Write-SeedRaw '08_ai_logs\ai_calls.jsonl' ""
Write-Seed '08_ai_logs\README.md' @"
# AI Usage Log

Append one JSON line per AI usage. Schema:
timestamp, tool/model, phase, purpose, prompt_summary, output_used, human_review, verification.

No credentials/secrets. Export to the required detailed AI-usage PDF before G4.
Paper declaration stays concise; detailed model/role/prompt/verification records stay here and in supporting material.
"@

# Workspace-local config snapshots
foreach ($cfg in @('method_router.yaml','paper_quality.yaml','figure_quality.yaml','contest_visual.yaml')) {
    $src = Join-Path $RepoRoot "config\$cfg"
    $dst = Join-Path $Workspace ("config\" + $cfg)
    if (Test-Path $src) { Copy-Item -Path $src -Destination $dst -Force }
    else { Write-Warning ("Config snapshot source missing: " + $src) }
}

# Frozen skill routing snapshot: only vendor/SKILLS_MANIFEST.yaml is contest-authoritative.
$snapshot = Join-Path $Workspace ("config\" + 'skill_routing_snapshot.yaml')
if (-not (Test-Path $snapshot)) {
    $srcCommit = "LOCAL_UNKNOWN"
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $c = (& git rev-parse --short HEAD 2>$null | Select-Object -First 1)
        if ($c) { $srcCommit = $c }
    }
    $lines = @(
        '# skill_routing_snapshot.yaml - frozen skill/policy facts at workspace creation',
        '# contest-time use follows vendor/SKILLS_MANIFEST.yaml; no network fetches',
        ('mmkit_source_commit: ' + $srcCommit),
        'policy: use_only_frozen_verified_skills_and_distilled_policies',
        'skills:'
    )
    $manifest = Join-Path $RepoRoot ("vendor\" + 'SKILLS_MANIFEST.yaml')
    if (Test-Path $manifest) {
        $key = $null; $source = ''; $pin = ''; $lic = ''; $mode = ''; $caps = ''
        foreach ($line in (Get-Content $manifest)) {
            if ($line -match '^\s*- key:\s*(\S+)\s*$') {
                if ($key) {
                    $lines += @("  - name: $key","    source: $source","    pin: $pin","    license: $lic","    integration_mode: $mode","    allowed_capabilities: $caps")
                }
                $key = $Matches[1]; $source = ''; $pin = ''; $lic = ''; $mode = ''; $caps = ''
            } elseif ($key) {
                if ($line -match '^\s+source:\s*"?(.+?)"?\s*$') { $source = $Matches[1] }
                elseif ($line -match '^\s+pin:\s*(\S+)\s*$') { $pin = $Matches[1] }
                elseif ($line -match '^\s+license:\s*(.+?)\s*$') { $lic = $Matches[1] }
                elseif ($line -match '^\s+integration_mode:\s*(\S+)\s*$') { $mode = $Matches[1] }
                elseif ($line -match '^\s+selected_capabilities:\s*\[(.*)\]$') { $caps = $Matches[1] }
            }
        }
        if ($key) {
            $lines += @("  - name: $key","    source: $source","    pin: $pin","    license: $lic","    integration_mode: $mode","    allowed_capabilities: $caps")
        }
    }
    Set-Content -Path $snapshot -Value $lines -Encoding UTF8
}

# R workspace adapter
$adapter = @'
param(
    [Parameter(Mandatory=$true)][string]$ModelFile,
    [string[]]$RArgs = @(),
    [string]$OutDir = ""
)
$ErrorActionPreference = "Stop"
function Find-Rscript {
    $cmd = Get-Command Rscript.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $roots = @("C:\Program Files\R","C:\Program Files (x86)\R",(Join-Path $env:LOCALAPPDATA 'Programs\R'),"C:\R")
    foreach ($root in $roots) {
        if (Test-Path $root) {
            $found = Get-ChildItem $root -Recurse -Depth 3 -Filter "Rscript.exe" -File -ErrorAction SilentlyContinue |
                Sort-Object FullName -Descending | Select-Object -First 1
            if ($found) { return $found.FullName }
        }
    }
    return $null
}
$rscript = Find-Rscript
if (-not $rscript) { Write-Host "R_RUNTIME_MISSING" -ForegroundColor Red; exit 3 }
if (-not (Test-Path $ModelFile)) { Write-Host ("MODEL_FILE_MISSING: " + $ModelFile) -ForegroundColor Red; exit 2 }
if (-not $OutDir) { $OutDir = Join-Path (Split-Path -Parent $ModelFile) "..\..\05_results\r_runs" }
New-Item -ItemType Directory -Force $OutDir | Out-Null
& $rscript $ModelFile -OutDir $OutDir @RArgs
$code = $LASTEXITCODE
if ($code -ne 0) { exit $code }
foreach ($f in @('coefficients.csv','metrics.csv','model_summary.txt','run_metadata.json')) {
    if (-not (Test-Path (Join-Path $OutDir $f))) { Write-Host ("OUTPUT_CONTRACT_MISSING: " + $f) -ForegroundColor Red; exit 4 }
}
Write-Host ("R RUN OK | outputs=" + $OutDir)
'@
Write-Seed '07_scripts\run_r_model.ps1' $adapter

Write-Seed '07_scripts\README.md' @"
# Workspace Scripts

- run_r_model.ps1 — execute a real .R model file and verify the standard output contract.
- Central auditors live in MMKit; do not copy them into each workspace.
- Before G4 run MMKit scripts/audit_human_paper.py against 06_paper/main.tex (and submitted code when useful).
- Substantive/multiline R uses real .R files, not multiline Rscript -e.
- No automatic package installs during a run.
"@

Write-Seed '04_models\r\README.md' @"
# R workspace models

Place workspace .R model files here. The central MMKit r_toolbox renv environment is the default backend.
Create a separate renv project only when the problem requires a materially different package set.
"@

# Paper skeleton: clean competition-paper defaults.
Write-Seed '06_paper\main.tex' @'
\documentclass[UTF8,a4paper,12pt]{ctexart}
\usepackage[margin=2.5cm]{geometry}
\usepackage{amsmath,amssymb,booktabs,graphicx,xcolor,hyperref,siunitx}
\hypersetup{hidelinks}
\graphicspath{{../05_results/figures/}}
\pagestyle{plain}
\begin{document}
\begin{center}\LARGE 数学建模论文题目\end{center}
\begin{abstract}
摘要待完成。
\par\textbf{关键词：}待定
\end{abstract}
\section{问题重述}
\section{问题分析}
\section{模型假设}
\section{符号说明}
\section{模型建立与求解}
\section{结果分析与检验}
\section{模型评价与改进}
\section{结论}
\section*{AI工具使用声明}
按当届官方要求用简洁正文声明填写；详细工具/模型/提示与核验信息见支撑材料。
\begin{thebibliography}{9}
\end{thebibliography}
\end{document}
'@

# Canonical submission area + deprecated compatibility marker.
Write-Seed '09_submission\README.md' @"
# Canonical Submission Directory

This is the ONLY final submission directory.
Expected final artifacts after G4:
- competition_paper.pdf
- supporting_material.zip (or official allowed archive format)
- optional checksum/receipt records

Do not keep competing final versions elsewhere.
After official MD5 generation/submission, do not write/resave the submitted files.
"@

Write-Seed '09_submission\SUBMISSION_MANIFEST.md' @"
# Submission Manifest

Status: NOT_READY

| artifact | source | size | checksum/MD5 | frozen | notes |
|---|---|---:|---|---|---|
| competition_paper.pdf | 06_paper |  |  | NO |  |
| supporting_material.zip | 07_supporting |  |  | NO |  |
"@

Write-Seed 'FINAL\README_DEPRECATED.md' @"
# DEPRECATED COMPATIBILITY DIRECTORY

Do not place final submission artifacts here.
MMKit v0.3 uses 09_submission/ as the unique canonical submission directory.
This directory remains temporarily so older P2 tooling/workspaces do not fail.
"@

Write-Seed 'README_WORKSPACE.md' @"
# $Name

MMKit v0.3 competition workspace.

Critical path:
1. Official statement/materials -> 00_problem/ (read-only + hash).
2. Raw data -> 01_data_raw/; derived data -> 02_data_processed/.
3. Method/figure/paper planning -> 03_analysis/.
4. Models -> 04_models/; reproducible outputs -> 05_results/.
5. Paper source -> 06_paper/.
6. Supporting source -> 07_supporting/; AI logs -> 08_ai_logs/; references -> 09_references/.
7. G3 -> claim register/evidence bank -> paper -> figure integration -> human-quality review -> G4.
8. Figure policy distinguishes scientific truth from presentation layer; attractive showcase 3D is allowed under config/contest_visual.yaml.
9. 09_submission/ is the ONLY canonical final-submission directory.
10. FINAL/ is deprecated compatibility only; never store competing final artifacts there.

Human gates G1-G4 remain mandatory.
See MMKit docs/WORKSPACE_SCHEMA.md and docs/ACADEMIC_SKILL_STACK_V03.md.
"@

Write-Host "Workspace ready: $Workspace" -ForegroundColor Green
Write-Host "Canonical submission directory: $(Join-Path $Workspace '09_submission')" -ForegroundColor Cyan
Write-Host "Next: G1, then G2 via 03_analysis/METHOD_ROUTE.md."

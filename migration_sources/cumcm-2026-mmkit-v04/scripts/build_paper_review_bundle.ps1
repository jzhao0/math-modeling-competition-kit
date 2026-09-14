[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Workspace,
    [string]$MainTex = '06_paper\main.tex',
    [string]$FactsConfig,
    [string]$SectionsConfig,
    [string]$LanguageConfig,
    [string]$FigureConfig
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = (Resolve-Path -LiteralPath $Workspace).Path
$mainCandidate = if ([IO.Path]::IsPathRooted($MainTex)) { $MainTex } else { Join-Path $workspaceRoot $MainTex }
$mainPath = [IO.Path]::GetFullPath($mainCandidate)
$reportsDir = Join-Path $workspaceRoot 'reports'
$bboxPath = Join-Path $workspaceRoot '09_submission\build\paper_gate\paper.bbox.html'
$paperPdf = Join-Path $workspaceRoot '09_submission\paper.pdf'
$packetJson = Join-Path $reportsDir 'sol_review_packet.json'
$packetMd = Join-Path $reportsDir 'sol_review_packet.md'
$intelligenceJson = Join-Path $reportsDir 'paper_intelligence.json'
$visualJson = Join-Path $reportsDir 'paper_visual_review.json'
$renderDir = Join-Path $reportsDir 'visual_review\pages'

if (-not $FactsConfig) {
    $workspaceFacts = Join-Path $workspaceRoot 'config\paper_facts.yaml'
    $FactsConfig = if (Test-Path -LiteralPath $workspaceFacts) {
        $workspaceFacts
    } else {
        Join-Path $repoRoot 'config\paper_facts.yaml'
    }
}

$builderArgs = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'build_paper.ps1'),
    '-Workspace', $workspaceRoot, '-MainTex', $MainTex, '-BuildSolReviewPacket'
)
if ($FactsConfig) { $builderArgs += @('-FactsConfig', $FactsConfig) }
if ($SectionsConfig) { $builderArgs += @('-SectionsConfig', $SectionsConfig) }
if ($LanguageConfig) { $builderArgs += @('-LanguageConfig', $LanguageConfig) }
if ($FigureConfig) { $builderArgs += @('-FigureConfig', $FigureConfig) }

Write-Host '=== BASE PAPER GATE + SOL PACKET ===' -ForegroundColor Cyan
$texHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $mainPath).Hash
$oldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& powershell.exe @builderArgs
$gateExit = $LASTEXITCODE
$ErrorActionPreference = $oldErrorActionPreference

$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$pythonCommand = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$python = if (Test-Path -LiteralPath $venvPython) {
    $venvPython
} elseif ($pythonCommand) {
    $pythonCommand.Path
} else {
    $null
}
if (-not $python) {
    Write-Error 'Python runtime unavailable.'
    exit 2
}

Write-Host '=== REVIEW INDEX + CLAIM/EVIDENCE TRIAGE ===' -ForegroundColor Cyan
Write-Host "FACTS CONFIG: $FactsConfig"
& $python (Join-Path $PSScriptRoot 'build_paper_intelligence.py') `
    --workspace $workspaceRoot `
    --main-tex $mainPath `
    --facts-config $FactsConfig `
    --output-json $intelligenceJson `
    --output-md (Join-Path $reportsDir 'paper_intelligence.md') | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Paper review-index generation failed with exit code $LASTEXITCODE."
}

if ((Test-Path -LiteralPath $bboxPath) -and (Test-Path -LiteralPath $paperPdf)) {
    Write-Host '=== PDF PAGE RENDER + VISUAL GEOMETRY REVIEW ===' -ForegroundColor Cyan
    $pdftoppmCommand = Get-Command pdftoppm -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    $pdftoppm = if ($pdftoppmCommand) { $pdftoppmCommand.Path } elseif (Test-Path -LiteralPath 'D:\texlive\2026\bin\windows\pdftoppm.exe') { 'D:\texlive\2026\bin\windows\pdftoppm.exe' } else { 'pdftoppm' }
    & $python (Join-Path $PSScriptRoot 'paper_visual_review.py') `
        --workspace $workspaceRoot `
        --bbox $bboxPath `
        --pdf $paperPdf `
        --render-dir $renderDir `
        --pdftoppm-command $pdftoppm `
        --output-json $visualJson `
        --output-md (Join-Path $reportsDir 'paper_visual_review.md') | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Paper visual review failed with exit code $LASTEXITCODE."
    }
} else {
    Write-Warning 'PDF/bbox unavailable; visual review was skipped.'
}

if ((Test-Path -LiteralPath $packetJson) -and (Test-Path -LiteralPath $intelligenceJson)) {
    Write-Host '=== AUGMENT SOL REVIEW PACKET ===' -ForegroundColor Cyan
    $augmentArgs = @(
        (Join-Path $PSScriptRoot 'augment_sol_review_packet.py'),
        '--workspace', $workspaceRoot,
        '--packet-json', $packetJson,
        '--packet-md', $packetMd,
        '--intelligence-json', $intelligenceJson
    )
    if (Test-Path -LiteralPath $visualJson) { $augmentArgs += @('--visual-json', $visualJson) }
    & $python @augmentArgs | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Sol review packet augmentation failed with exit code $LASTEXITCODE."
    }
}

$texHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $mainPath).Hash
if ($texHashAfter -ne $texHashBefore) {
    Write-Error 'READ-ONLY CONTRACT VIOLATION: selected candidate TeX changed during review-bundle generation.'
    exit 3
}
Write-Host "CANDIDATE TEX SHA256: $texHashAfter (UNCHANGED)" -ForegroundColor Green

Write-Host "BASE GATE EXIT: $gateExit" -ForegroundColor Cyan
Write-Host "INTELLIGENCE: $intelligenceJson"
Write-Host "VISUAL REVIEW: $visualJson"
Write-Host "SOL PACKET: $packetMd"
exit $gateExit

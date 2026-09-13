param(
    [Parameter(Mandatory=$true)][string]$Workspace
)

$ErrorActionPreference = 'Stop'
$Workspace = (Resolve-Path $Workspace).Path
$paperDir = Join-Path $Workspace '06_paper'
$main = Join-Path $paperDir 'main.tex'
$outDir = Join-Path $Workspace '09_submission\build'
$finalPdf = Join-Path $Workspace '09_submission\paper.pdf'

if (-not (Test-Path $main)) { throw "Paper source not found: $main" }
New-Item -ItemType Directory -Force $outDir | Out-Null

$latexmk = Get-Command latexmk -ErrorAction SilentlyContinue
if (-not $latexmk) {
    $fallback = 'D:\texlive\2026\bin\windows\latexmk.exe'
    if (Test-Path $fallback) { $latexmk = [pscustomobject]@{ Source = $fallback } }
}
if (-not $latexmk) { throw 'latexmk not found.' }

Push-Location $paperDir
try {
    & $latexmk.Source -xelatex -interaction=nonstopmode -halt-on-error "-outdir=$outDir" $main
    if ($LASTEXITCODE -ne 0) { throw "latexmk failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

$built = Join-Path $outDir 'main.pdf'
if (-not (Test-Path $built)) { throw "Expected PDF not found: $built" }
Copy-Item -Force $built $finalPdf
Write-Host "Paper built: $finalPdf" -ForegroundColor Green

param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SourceDir = [System.IO.Path]::GetFullPath((Join-Path $Root "templates\tex_smoke"))
$BuildDir = [System.IO.Path]::GetFullPath((Join-Path $Root "reports\tex_smoke"))

New-Item -ItemType Directory -Force $BuildDir | Out-Null

# A previous version passed -outdir=$BuildDir through the Windows latexmk wrapper
# in a form that was preserved literally, creating templates\tex_smoke\$BuildDir.
# That directory is bootstrap debris and is safe to remove here.
$LiteralBuildDir = Join-Path $SourceDir '$BuildDir'
if (Test-Path $LiteralBuildDir) {
    Write-Host "Removing stale literal `$BuildDir smoke directory: $LiteralBuildDir" -ForegroundColor Yellow
    Remove-Item -Recurse -Force $LiteralBuildDir
}

$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
$latexmk = Get-Command latexmk -ErrorAction SilentlyContinue

if (-not $xelatex) {
    throw "xelatex is not available on PATH. Install/activate TeX Live first."
}

Write-Host "XeLaTeX: $($xelatex.Source)" -ForegroundColor Green
& $xelatex.Source --version | Select-Object -First 1

if ($latexmk) {
    Write-Host "latexmk: $($latexmk.Source)" -ForegroundColor Green
    $latexmkArgs = @(
        "-xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        ("-outdir={0}" -f $BuildDir),
        "main.tex"
    )
    Push-Location $SourceDir
    try {
        & $latexmk.Source @latexmkArgs
        if ($LASTEXITCODE -ne 0) { throw "latexmk XeLaTeX smoke build failed." }
    } finally {
        Pop-Location
    }
} else {
    Write-Warning "latexmk not found; falling back to two direct XeLaTeX passes."
    $xelatexArgs = @(
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        ("-output-directory={0}" -f $BuildDir),
        "main.tex"
    )
    Push-Location $SourceDir
    try {
        for ($i = 1; $i -le 2; $i++) {
            & $xelatex.Source @xelatexArgs
            if ($LASTEXITCODE -ne 0) { throw "XeLaTeX smoke build failed on pass $i." }
        }
    } finally {
        Pop-Location
    }
}

$pdf = Join-Path $BuildDir "main.pdf"
if (-not (Test-Path $pdf)) { throw "Expected smoke PDF was not created: $pdf" }

$size = (Get-Item $pdf).Length
Write-Host "`nWindows XeLaTeX smoke test PASSED." -ForegroundColor Green
Write-Host "PDF:  $pdf"
Write-Host "Bytes: $size"

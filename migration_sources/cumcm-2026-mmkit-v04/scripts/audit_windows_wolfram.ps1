param(
    [string]$WolframScriptExe = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Find-WolframScript {
    param([string]$Explicit)

    if ($Explicit -and (Test-Path $Explicit)) {
        return (Resolve-Path $Explicit).Path
    }

    $cmd = Get-Command wolframscript -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $roots = @(
        "C:\Program Files\Wolfram Research",
        "C:\Program Files (x86)\Wolfram Research",
        "D:\Program Files\Wolfram Research",
        "D:\Wolfram Research"
    ) | Where-Object { Test-Path $_ }

    foreach ($searchRoot in $roots) {
        $found = Get-ChildItem -Path $searchRoot -Filter wolframscript.exe -File -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }

    return $null
}

function Find-WolframKernels {
    $roots = @(
        "C:\Program Files\Wolfram Research",
        "C:\Program Files (x86)\Wolfram Research",
        "D:\Program Files\Wolfram Research",
        "D:\Wolfram Research"
    ) | Where-Object { Test-Path $_ }

    $hits = @()
    foreach ($searchRoot in $roots) {
        $hits += Get-ChildItem -Path $searchRoot -Include WolframKernel.exe,MathKernel.exe,Mathematica.exe -File -Recurse -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName
    }
    return @($hits | Sort-Object -Unique)
}

$reportDir = Join-Path $Root "reports"
New-Item -ItemType Directory -Force $reportDir | Out-Null
$reportPath = Join-Path $reportDir "wolfram_environment.json"

$exe = Find-WolframScript $WolframScriptExe
$kernelCandidates = Find-WolframKernels

$report = [ordered]@{
    timestamp_local = (Get-Date).ToString("o")
    wolframscript_found = [bool]$exe
    wolframscript_path = $exe
    kernel_candidates = @($kernelCandidates)
    version_output = @()
    symbolic_smoke_pass = $false
    exit_code = $null
}

if (-not $exe) {
    $report | ConvertTo-Json -Depth 5 | Set-Content -Path $reportPath -Encoding UTF8
    Write-Warning "wolframscript.exe was not found on PATH or under the common Wolfram Research install roots."
    if ($kernelCandidates.Count -gt 0) {
        Write-Host "Wolfram/Mathematica executables detected:" -ForegroundColor Cyan
        $kernelCandidates | ForEach-Object { Write-Host "  $_" }
    }
    Write-Host "Report: $reportPath"
    exit 2
}

Write-Host "WolframScript executable: $exe" -ForegroundColor Green

$code = 'Print[$Version]; Print[FullSimplify[Expand[(x - 1) (x + 1) (x^2 + 1)] == x^4 - 1]]'
$output = @(& $exe -code $code 2>&1)
$exitCode = $LASTEXITCODE

$report.exit_code = $exitCode
$report.version_output = @($output | ForEach-Object { [string]$_ })
$report.symbolic_smoke_pass = ($exitCode -eq 0 -and ($report.version_output -contains "True"))
$report | ConvertTo-Json -Depth 5 | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "`nWolframScript output:" -ForegroundColor Cyan
$output | ForEach-Object { Write-Host $_ }
Write-Host "`nSymbolic smoke: $($report.symbolic_smoke_pass)"
Write-Host "Report: $reportPath"

if (-not $report.symbolic_smoke_pass) {
    throw "WolframScript was found but the symbolic smoke test did not pass. Inspect the output and report; this may be a kernel/licensing/configuration issue."
}

Write-Host "`nWindows Wolfram CLI audit PASSED." -ForegroundColor Green

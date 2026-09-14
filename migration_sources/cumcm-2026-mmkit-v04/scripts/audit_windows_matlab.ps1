param(
    [string]$MatlabExe = "D:\MATLAB\bin\matlab.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path $MatlabExe)) {
    $cmd = Get-Command matlab -ErrorAction SilentlyContinue
    if ($cmd) {
        $MatlabExe = $cmd.Source
    } else {
        $candidate = Get-ChildItem -Path "D:\MATLAB","C:\Program Files\MATLAB" -Filter matlab.exe -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($candidate) {
            $MatlabExe = $candidate.FullName
        } else {
            throw "MATLAB executable not found. Pass -MatlabExe explicitly."
        }
    }
}

$env:CUMCM_REPO_ROOT = $Root
$scriptDir = Join-Path $Root "scripts"
$scriptPath = Join-Path $scriptDir "matlab_audit.m"
if (-not (Test-Path $scriptPath)) { throw "Missing MATLAB audit script: $scriptPath" }

Write-Host "MATLAB executable: $MatlabExe" -ForegroundColor Green
Write-Host "Repository root:  $Root"
Write-Host "Running toolbox/license audit..." -ForegroundColor Yellow

$escapedDir = $scriptDir.Replace("'", "''")
& $MatlabExe -batch "addpath('$escapedDir'); matlab_audit"
if ($LASTEXITCODE -ne 0) {
    throw "MATLAB audit failed with exit code $LASTEXITCODE. Capture the terminal output."
}

$report = Join-Path $Root "reports\matlab_environment.json"
if (-not (Test-Path $report)) {
    throw "MATLAB audit finished but report was not created: $report"
}

Write-Host "`nWindows MATLAB audit PASSED." -ForegroundColor Green
Write-Host "Report: $report"

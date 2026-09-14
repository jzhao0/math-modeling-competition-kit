# -*- coding: utf-8 -*-
# setup_windows_r.ps1 — R runtime DISCOVERY only.
#
# Purpose :
#   * discover Rscript.exe on PATH and in common Windows R install locations
#   * print the exact detected R version and full Rscript.exe path
#   * NEVER installs R, NEVER modifies global environment variables
#   * idempotent / safe to re-run (read-only)
#
# Exit codes :
#   0  -> R found (prints R_FOUND and R_VERSION / RSCRIPT_PATH)
#   3  -> R not found (prints R_RUNTIME_MISSING + actionable guidance)
#   4  -> script error (e.g. Rscript.exe found but version query failed)

param(
    [string]$ExtraSearchDir = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

function Write-Status([string]$Message, [string]$Color = "Gray") {
    if (-not $Quiet) { Write-Host $Message -ForegroundColor $Color }
}

function Get-CandidateRscriptPaths {
    $candidates = [System.Collections.Generic.List[string]]::new()

    # 1) PATH lookup
    $cmd = Get-Command "Rscript.exe" -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { $candidates.Add($cmd.Source) }
    # also accept Rscript without extension (Unix-style / R term launcher)
    $cmd2 = Get-Command "Rscript" -ErrorAction SilentlyContinue
    if ($cmd2 -and $cmd2.Source) { $candidates.Add($cmd2.Source) }

    $envHints = @()
    if ($env:R_HOME) { $envHints += (Join-Path $env:R_HOME "binRscript.exe") }
    if ($env:R_LIBS_USER) { $envHints += $env:R_LIBS_USER }

    # 2) common Windows R installation roots (registry-independent discovery)
    $roots = @(
        "C:\Program Files\R",
        "C:\Program Files (x86)\R",
        (Join-Path $env:LOCALAPPDATA "Programs\R"),
        (Join-Path $env:LOCALAPPDATA "Programs\RStudio"),
        (Join-Path $env:USERPROFILE "AppData\Local\Programs\R"),
        "C:\R"
    )
    if ($ExtraSearchDir -and (Test-Path (Split-Path $ExtraSearchDir -Parent))) {
        $roots += $ExtraSearchDir
    }

    foreach ($root in $roots) {
        if (-not $root -or -not (Test-Path $root)) { continue }
        try {
            $found = Get-ChildItem -Path $root -Recurse -Depth 4 -Filter "Rscript.exe" -File -ErrorAction SilentlyContinue |
                ForEach-Object { $_.FullName }
            foreach ($f in $found) { $candidates.Add($f) }
        } catch {
            # permission / long-path errors on some roots are non-fatal
        }
    }

    return ($candidates | Where-Object { $_ } | Select-Object -Unique)
}

function Test-RscriptUsable([string]$ExePath) {
    try {
        $spec = & $ExePath "--version" 2>&1
        if ($LASTEXITCODE -ne 0) { return $null }
        $raw = ($spec | Out-String).Trim()
        # Rscript --version prints "Rscript (R) version 4.3.2 ..." (stderr on some builds)
        $ver = $null
        if ($raw -match "version\s+([0-9]+\.[0-9]+\.[0-9]+)") { $ver = $Matches[1] }
        if (-not $ver) {
            $verQ = & $ExePath -e "cat(as.character(getRversion()))" 2>$null
            if ($LASTEXITCODE -eq 0 -and $verQ) { $ver = ($verQ | Select-Object -Last 1).Trim() }
        }
        if (-not $ver) { return $null }
        return [PSCustomObject]@{ Path = $ExePath; Version = $ver; Raw = $raw }
    } catch {
        return $null
    }
}

Write-Status "== MMKit R runtime discovery =="
Write-Status "Scanning PATH and common Windows R locations..." "Cyan"
$candidates = @(Get-CandidateRscriptPaths)
Write-Status ("Candidate Rscript.exe locations found: {0}" -f $candidates.Count)

$best = $null
foreach ($cand in $candidates) {
    $info = Test-RscriptUsable $cand
    if ($info) {
        Write-Status ("  checked: {0} -> R {1}" -f $info.Path, $info.Version)
        if (-not $best -or ([version]$info.Version -gt [version]$best.Version)) { $best = $info }
    }
}

if (-not $best) {
    Write-Status "" 
    Write-Host "R_RUNTIME_MISSING" -ForegroundColor Red
    Write-Host ""
    Write-Host "No usable Rscript.exe was detected." -ForegroundColor Yellow
    Write-Host "Actionable options (this script will NOT install anything):" -ForegroundColor Yellow
    Write-Host "  1. Install R for Windows from CRAN  : https://cran.r-project.org/bin/windows/base/"
    Write-Host "     Default install creates C:\Program Files\R\R-<ver>\bin\Rscript.exe"
    Write-Host "  2. Or install through a package manager you trust, e.g.:"
    Write-Host "       winget install --id RProject.R" -ForegroundColor Yellow
    Write-Host "       (verify the exact winget id / channel before use; then re-run this script)"
    Write-Host "  3. Or point this script at an existing install:"
    Write-Host "       .\scripts\setup_windows_r.ps1 -ExtraSearchDir 'D:\R\R-4.3.2\bin'" -ForegroundColor Yellow
    Write-Host "  4. Re-run this script after installing R to confirm discovery:"
    Write-Host "       .\scripts\setup_windows_r.ps1" -ForegroundColor Yellow
    Write-Host "Note: MMKit never modifies global PATH/R_HOME. If you want R on PATH, do that yourself." -ForegroundColor DarkGray
    exit 3
}

Write-Status ""
Write-Host "R_FOUND" -ForegroundColor Green
Write-Host ("RSCRIPT_PATH = {0}" -f $best.Path)
Write-Host ("R_VERSION    = {0}" -f $best.Version)
Write-Host ("R_HOME-env   = {0}" -f $(if ($env:R_HOME) { $env:R_HOME } else { "(not set)" }))
Write-Host ("R_LIBS_USER-env = {0}" -f $(if ($env:R_LIBS_USER) { $env:R_LIBS_USER } else { "(not set)" }))
Write-Status ""
Write-Status "Discovery complete. No environment variables were modified." "Cyan"
exit 0

[CmdletBinding()]
param(
    [switch]$ForceReinstall,
    [string]$RscriptPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ExpectedVersion = '0.0.13'
$ExpectedSha = '13adbe0ac1716c4f07c841f45040010e71109540'
$Repo = 'zhjx19/mathmodels'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Smoke = Join-Path $Here 'mathmodels_smoke.R'

function Resolve-RscriptPath {
    param([string]$ExplicitPath)

    $candidates = [System.Collections.Generic.List[string]]::new()

    if ($ExplicitPath) {
        $candidates.Add($ExplicitPath)
    }

    $cmd = Get-Command Rscript -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        $candidates.Add($cmd.Source)
    }

    if ($env:R_HOME) {
        $candidates.Add((Join-Path $env:R_HOME 'bin\Rscript.exe'))
        $candidates.Add((Join-Path $env:R_HOME 'bin\x64\Rscript.exe'))
    }

    $registryPaths = @(
        'HKLM:\SOFTWARE\R-core\R',
        'HKLM:\SOFTWARE\WOW6432Node\R-core\R',
        'HKCU:\SOFTWARE\R-core\R'
    )
    foreach ($rp in $registryPaths) {
        try {
            $item = Get-ItemProperty -LiteralPath $rp -ErrorAction Stop
            if ($item.InstallPath) {
                $candidates.Add((Join-Path $item.InstallPath 'bin\Rscript.exe'))
                $candidates.Add((Join-Path $item.InstallPath 'bin\x64\Rscript.exe'))
            }
        } catch {
            # Registry entry is optional.
        }
    }

    $roots = @(
        (Join-Path $env:ProgramFiles 'R'),
        $(if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} 'R' } else { $null }),
        $(if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'Programs\R' } else { $null }),
        'D:\Program Files\R',
        'D:\R',
        'C:\R'
    ) | Where-Object { $_ }

    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        $dirs = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending
        foreach ($dir in $dirs) {
            $candidates.Add((Join-Path $dir.FullName 'bin\Rscript.exe'))
            $candidates.Add((Join-Path $dir.FullName 'bin\x64\Rscript.exe'))
        }
        $candidates.Add((Join-Path $root 'bin\Rscript.exe'))
        $candidates.Add((Join-Path $root 'bin\x64\Rscript.exe'))
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

$RscriptExe = Resolve-RscriptPath -ExplicitPath $RscriptPath
if (-not $RscriptExe) {
    throw @'
Rscript.exe could not be located automatically.
This does not prove that R is absent; it may be installed in a non-standard directory.
Re-run with an explicit path, for example:
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_mathmodels.ps1 -RscriptPath "C:\Program Files\R\R-4.6.1\bin\Rscript.exe"
'@
}

if (-not (Test-Path -LiteralPath $Smoke -PathType Leaf)) {
    throw "Missing smoke script: $Smoke"
}

$RBin = Split-Path -Parent $RscriptExe
if (($env:Path -split ';') -notcontains $RBin) {
    $env:Path = "$RBin;$env:Path"
}

Write-Host '=== MMKIT MATHMODELS SETUP ==='
Write-Host "Rscript=$RscriptExe"
Write-Host "SOURCE=$Repo"
Write-Host "EXPECTED_VERSION=$ExpectedVersion"
Write-Host "EXPECTED_PIN=$ExpectedSha"

$Probe = @'
pkg <- "mathmodels"
cat("R_VERSION=", as.character(getRversion()), "\n", sep="")
cat("R_HOME=", R.home(), "\n", sep="")
if (!requireNamespace(pkg, quietly = TRUE)) {
  cat("INSTALLED=NO\n")
  quit(status = 0)
}
pd <- utils::packageDescription(pkg)
cat("INSTALLED=YES\n")
cat("VERSION=", as.character(utils::packageVersion(pkg)), "\n", sep="")
cat("REMOTE_SHA=", if (!is.null(pd$RemoteSha)) as.character(pd$RemoteSha) else "UNRECORDED", "\n", sep="")
'@

$probeFile = Join-Path $env:TEMP 'mmkit-mathmodels-probe.R'
Set-Content -LiteralPath $probeFile -Value $Probe -Encoding utf8
$probeOutput = & $RscriptExe $probeFile 2>&1
$probeExit = $LASTEXITCODE
$probeOutput | ForEach-Object { Write-Host $_ }
if ($probeExit -ne 0) {
    throw "Initial mathmodels probe failed with exit code $probeExit"
}

$installed = ($probeOutput -match '^INSTALLED=YES$').Count -gt 0
$versionLine = $probeOutput | Where-Object { $_ -match '^VERSION=' } | Select-Object -First 1
$shaLine = $probeOutput | Where-Object { $_ -match '^REMOTE_SHA=' } | Select-Object -First 1
$currentVersion = if ($versionLine) { ($versionLine -replace '^VERSION=', '').Trim() } else { '' }
$currentSha = if ($shaLine) { ($shaLine -replace '^REMOTE_SHA=', '').Trim() } else { '' }

$needInstall = $ForceReinstall -or (-not $installed) -or ($currentVersion -ne $ExpectedVersion) -or ($currentSha -ne $ExpectedSha)

if ($needInstall) {
    Write-Host 'ACTION=INSTALL_EXACT_PIN'
    Write-Host 'NOTE=This step uses the network and is intended for pre-contest qualification only.'

    $Install = @'
options(repos = c(CRAN = "https://cloud.r-project.org"))
if (!requireNamespace("remotes", quietly = TRUE)) {
  install.packages("remotes")
}
remotes::install_github(
  "__REPO__",
  ref = "__SHA__",
  upgrade = "never",
  dependencies = c("Depends", "Imports", "LinkingTo"),
  build_vignettes = FALSE
)
pd <- utils::packageDescription("mathmodels")
ver <- as.character(utils::packageVersion("mathmodels"))
sha <- if (!is.null(pd$RemoteSha)) as.character(pd$RemoteSha) else ""
cat("INSTALLED_VERSION=", ver, "\n", sep="")
cat("INSTALLED_REMOTE_SHA=", if (nzchar(sha)) sha else "UNRECORDED", "\n", sep="")
if (!identical(ver, "__VERSION__")) stop("Installed version mismatch")
if (!identical(sha, "__SHA__")) stop("Installed RemoteSha mismatch")
'@
    $Install = $Install.Replace('__REPO__', $Repo).Replace('__SHA__', $ExpectedSha).Replace('__VERSION__', $ExpectedVersion)

    $installFile = Join-Path $env:TEMP 'mmkit-mathmodels-install.R'
    Set-Content -LiteralPath $installFile -Value $Install -Encoding utf8
    & $RscriptExe $installFile
    if ($LASTEXITCODE -ne 0) {
        throw "Exact-pin mathmodels install failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Host 'ACTION=KEEP_EXISTING_EXACT_PIN'
}

Write-Host ''
Write-Host 'Running bounded mathmodels smoke...'
& $RscriptExe $Smoke
if ($LASTEXITCODE -ne 0) {
    throw "mathmodels smoke failed with exit code $LASTEXITCODE"
}

Write-Host ''
Write-Host '=== MMKIT MATHMODELS SETUP RESULT ==='
Write-Host 'STATUS=PASS'
Write-Host "RSCRIPT=$RscriptExe"
Write-Host "MATHMODELS_VERSION=$ExpectedVersion"
Write-Host "MATHMODELS_PIN=$ExpectedSha"
Write-Host 'ROLE=OPTIONAL_PREINSTALLED_RUNTIME'
Write-Host 'DRILL03_SCIENCE_MUTATION=NO'
Write-Host 'NEXT=SAFE_TO_USE_AS_BOUNDED_OPTIONAL_R_BACKEND'

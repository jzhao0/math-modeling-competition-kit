param(
    [switch]$SkipWinget,
    [switch]$OfficialPyPIOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Refresh-ProcessPath {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = (($machine, $user) -join ";")
}

function Add-UserPathIfMissing([string]$Dir) {
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @($current -split ";" | Where-Object { $_ })
    if ($parts -notcontains $Dir) {
        [Environment]::SetEnvironmentVariable("Path", (($parts + $Dir) -join ";"), "User")
    }
    Refresh-ProcessPath
}

function Find-UvExecutable {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }

    $wingetPackages = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $wingetPackages) {
        $found = Get-ChildItem -Path $wingetPackages -Filter uv.exe -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "astral-sh\.uv" } |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }

    return $null
}

function Install-UvStandalone {
    $installDir = Join-Path $env:USERPROFILE ".local\bin"
    New-Item -ItemType Directory -Force $installDir | Out-Null
    Write-Host "Falling back to Astral's official standalone installer..." -ForegroundColor Yellow
    Write-Host "Target: $installDir"

    $oldInstallDir = $env:UV_INSTALL_DIR
    try {
        $env:UV_INSTALL_DIR = $installDir
        $scriptText = Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing
        Invoke-Expression $scriptText
    } finally {
        $env:UV_INSTALL_DIR = $oldInstallDir
    }

    Add-UserPathIfMissing $installDir
    $candidate = Join-Path $installDir "uv.exe"
    if (-not (Test-Path $candidate)) {
        throw "Astral standalone installer completed but uv.exe was not found at $candidate."
    }
    return $candidate
}

function Resolve-Uv {
    Refresh-ProcessPath
    $uv = Find-UvExecutable
    if ($uv) { return $uv }

    if (-not $SkipWinget -and (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "uv command not found. Checking/installing Astral uv with winget..." -ForegroundColor Yellow
        & winget install --id astral-sh.uv --exact --source winget --accept-package-agreements --accept-source-agreements
        $wingetExit = $LASTEXITCODE
        if ($wingetExit -ne 0 -and $wingetExit -ne -1978335189) {
            Write-Warning "winget returned exit code $wingetExit. Will try to locate an existing portable install before using the official standalone installer."
        }

        Refresh-ProcessPath
        $uv = Find-UvExecutable
        if ($uv) {
            Add-UserPathIfMissing (Split-Path -Parent $uv)
            return $uv
        }
    }

    return Install-UvStandalone
}

function Test-PythonInterpreter([string]$Exe, [string]$ExpectedMinor) {
    if (-not (Test-Path $Exe) -and -not (Get-Command $Exe -ErrorAction SilentlyContinue)) { return $null }
    try {
        $json = & $Exe -c "import json,sys; print(json.dumps({'exe':sys.executable,'major':sys.version_info.major,'minor':sys.version_info.minor,'version':sys.version.split()[0]}))" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $json) { return $null }
        $info = $json | ConvertFrom-Json
        if ($info.major -eq 3 -and [string]$info.minor -eq $ExpectedMinor) { return $info }
    } catch {}
    return $null
}

function Resolve-SystemPython {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($minor in @("13")) {
            try {
                $exe = (& py "-3.$minor" -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
                if ($LASTEXITCODE -eq 0 -and $exe) {
                    $info = Test-PythonInterpreter $exe $minor
                    if ($info) { return $info }
                }
            } catch {}
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        foreach ($minor in @("13")) {
            $info = Test-PythonInterpreter $pythonCmd.Source $minor
            if ($info) { return $info }
        }
    }

    return $null
}

function Set-UvNetworkProfile([switch]$OfficialOnly) {
    Remove-Item Env:UV_INDEX_URL -ErrorAction SilentlyContinue
    Remove-Item Env:UV_EXTRA_INDEX_URL -ErrorAction SilentlyContinue
    Remove-Item Env:UV_INDEX -ErrorAction SilentlyContinue

    $env:UV_DEFAULT_INDEX = "https://pypi.org/simple"
    if ($OfficialOnly) {
        $indexLabel = "official PyPI only"
    } else {
        $env:UV_INDEX = "https://mirrors.ustc.edu.cn/pypi/simple/"
        $indexLabel = "USTC first; official PyPI fallback"
    }
    $env:UV_INDEX_STRATEGY = "first-index"
    $env:UV_HTTP_TIMEOUT = "120"
    $env:UV_HTTP_CONNECT_TIMEOUT = "20"
    $env:UV_HTTP_RETRIES = "5"
    $env:UV_CONCURRENT_DOWNLOADS = "4"
    $env:UV_CONCURRENT_INSTALLS = "4"

    Write-Host "`nuv network/index profile:" -ForegroundColor Yellow
    Write-Host "  Index policy        : $indexLabel"
    if (-not $OfficialOnly) { Write-Host "  Preferred index     : $env:UV_INDEX" }
    Write-Host "  Fallback/default    : $env:UV_DEFAULT_INDEX"
    Write-Host "  Index strategy      : $env:UV_INDEX_STRATEGY"
    Write-Host "  HTTP read timeout   : $env:UV_HTTP_TIMEOUT s"
    Write-Host "  Connect timeout     : $env:UV_HTTP_CONNECT_TIMEOUT s"
    Write-Host "  HTTP retries        : $env:UV_HTTP_RETRIES"
    Write-Host "  Concurrent downloads: $env:UV_CONCURRENT_DOWNLOADS"
    Write-Host "  Concurrent installs : $env:UV_CONCURRENT_INSTALLS"
}

function Remove-UntrackedUniversalLock {
    $lockPath = Join-Path $Root "uv.lock"
    if (-not (Test-Path $lockPath)) { return }

    $isTracked = $false
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $trackedMatch = (& git ls-files -- uv.lock | Select-Object -First 1)
        $isTracked = -not [string]::IsNullOrWhiteSpace([string]$trackedMatch)
    }

    if ($isTracked) {
        Write-Warning "A tracked uv.lock exists. The Windows bootstrap will not modify it; current-platform installation will use uv pip instead."
    } else {
        Write-Host "`nRemoving untracked bootstrap uv.lock." -ForegroundColor Yellow
        Write-Host "Reason: uv's universal lock may fetch metadata from wheels for other platforms; the USTC route currently redirects some such files to TUNA and returns HTTP 403."
        Remove-Item -Force $lockPath
    }
}

function Invoke-CurrentPlatformInstall([string]$UvExe, [string]$VenvPython, [switch]$OfficialOnly) {
    Set-UvNetworkProfile -OfficialOnly:$OfficialOnly

    $args = @(
        "pip", "install",
        "--python", $VenvPython,
        "-r", (Join-Path $Root "pyproject.toml"),
        "--default-index", $env:UV_DEFAULT_INDEX,
        "--index-strategy", "first-index"
    )
    if (-not $OfficialOnly) {
        $args += @("--index", $env:UV_INDEX)
    }

    & $UvExe @args
    return $LASTEXITCODE
}

$uv = Resolve-Uv
Write-Host "Using uv: $uv" -ForegroundColor Green
& $uv --version
if ($LASTEXITCODE -ne 0) { throw "uv executable failed." }

$python = Resolve-SystemPython
if (-not $python) {
    throw "No suitable existing system Python 3.13 was found (project requires-python >=3.13,<3.14). Automatic Python downloads remain disabled."
}

Write-Host "`nUsing existing system Python:" -ForegroundColor Green
Write-Host ("Python {0}" -f $python.version)
Write-Host ("Interpreter: {0}" -f $python.exe)
Write-Host "Managed-Python downloads are disabled for this setup run." -ForegroundColor Cyan

Remove-UntrackedUniversalLock

$venvPath = Join-Path $Root ".venv"
if (Test-Path $venvPath) {
    Write-Host "`nRemoving existing .venv for a clean current-platform rebuild..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvPath
}

Write-Host "`nCreating Windows virtual environment..." -ForegroundColor Yellow
& $uv venv --python $python.exe --no-managed-python --no-python-downloads $venvPath
if ($LASTEXITCODE -ne 0) { throw "uv venv failed." }

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) { throw "Virtual-environment Python was not created at $venvPython" }

Write-Host "`nInstalling project dependencies for the CURRENT Windows environment only..." -ForegroundColor Yellow
Write-Host "This intentionally bypasses uv's universal project lock during bootstrap." -ForegroundColor Cyan

$installExit = Invoke-CurrentPlatformInstall $uv $venvPython -OfficialOnly:$OfficialPyPIOnly
if ($installExit -ne 0 -and -not $OfficialPyPIOnly) {
    Write-Warning "USTC-first install failed. Keeping successfully installed/cached packages and retrying unresolved work against official PyPI only."
    $installExit = Invoke-CurrentPlatformInstall $uv $venvPython -OfficialOnly
}
if ($installExit -ne 0) {
    throw "Current-platform dependency installation failed. Capture the final package/error; do not install packages globally."
}

Write-Host "`nChecking dependency consistency..." -ForegroundColor Yellow
& $uv pip check --python $venvPython
if ($LASTEXITCODE -ne 0) { throw "uv pip check reported an inconsistent environment." }

$platformLock = Join-Path $Root "requirements-win-py313.lock.txt"
Write-Host "`nFreezing the successful Windows environment to:" -ForegroundColor Yellow
Write-Host "  $platformLock"
$freezeLines = & $uv pip freeze --python $venvPython
if ($LASTEXITCODE -ne 0) { throw "uv pip freeze failed." }
$freezeLines | Set-Content -Path $platformLock -Encoding UTF8

Write-Host "`nPython selected for this project:" -ForegroundColor Yellow
& $venvPython --version
if ($LASTEXITCODE -ne 0) { throw "Project Python failed to launch." }

Write-Host "`nRunning scientific-stack smoke test..." -ForegroundColor Yellow
& $venvPython .\scripts\python_smoke.py
if ($LASTEXITCODE -ne 0) { throw "Scientific-stack smoke test failed. Inspect reports/python_smoke.json and terminal output." }

Write-Host "`nWindows Python baseline is ready." -ForegroundColor Green
Write-Host "Environment:    $Root\.venv"
Write-Host "Platform lock:  $platformLock"
Write-Host "Smoke:          $Root\reports\python_smoke.json"
Write-Host "Universal uv.lock: deferred until it can be generated from a registry path that does not fail on unrelated platform metadata." -ForegroundColor Cyan
Write-Host "Do not install competition packages globally into the system Python installation." -ForegroundColor Cyan

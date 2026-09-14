param(
    [string]$TexDir = "D:\texlive\2026",
    [switch]$UseOfficialCTAN
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Work = Join-Path $Root ".bootstrap\texlive"
$SjtugRepo = "https://mirrors.sjtug.sjtu.edu.cn/ctan/systems/texlive/tlnet"
$OfficialRepo = "https://tug.ctan.org/systems/texlive/tlnet"
$Repo = if ($UseOfficialCTAN) { $OfficialRepo } else { $SjtugRepo }

function Add-UserPathIfMissing([string]$Dir) {
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @($current -split ";" | Where-Object { $_ })
    if ($parts -notcontains $Dir) {
        [Environment]::SetEnvironmentVariable("Path", (($parts + $Dir) -join ";"), "User")
    }
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = (($machine, $user) -join ";")
}

function Download-FileResumable([string]$Url, [string]$OutFile) {
    New-Item -ItemType Directory -Force (Split-Path -Parent $OutFile) | Out-Null
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curl) {
        throw "curl.exe is required for the resumable TeX Live bootstrap."
    }

    $part = "$OutFile.part"
    Write-Host "Download URL: $Url"
    if (Test-Path $part) {
        Write-Host ("Resuming partial download: {0:N2} MiB already present" -f ((Get-Item $part).Length / 1MB)) -ForegroundColor Cyan
    }

    & $curl.Source -4 -L --fail --retry 20 --retry-all-errors --retry-delay 2 --connect-timeout 20 --speed-time 30 --speed-limit 1024 -C - -o $part $Url
    if ($LASTEXITCODE -ne 0) {
        throw "curl failed downloading $Url. Partial file is retained at $part for the next retry."
    }

    if (-not (Test-Path $part) -or (Get-Item $part).Length -lt 10MB) {
        throw "Downloaded installer is unexpectedly small. Partial file retained for inspection: $part"
    }

    Move-Item -Force $part $OutFile
}

$driveName = ([System.IO.Path]::GetPathRoot($TexDir)).TrimEnd('\').TrimEnd(':')
$drive = Get-PSDrive -Name $driveName -ErrorAction SilentlyContinue
if (-not $drive) { throw "Drive for TeX Live destination does not exist: $TexDir" }
if ($drive.Free -lt 6GB) {
    throw ("TeX Live bootstrap requires at least 6 GB free on {0}:; available {1:N2} GB." -f $driveName, ($drive.Free / 1GB))
}

$existing = Join-Path $TexDir "bin\windows\xelatex.exe"
if (Test-Path $existing) {
    Write-Host "Existing TeX Live detected: $existing" -ForegroundColor Green
    Add-UserPathIfMissing (Split-Path -Parent $existing)
    & (Join-Path $Root "scripts\tex_smoke.ps1")
    exit $LASTEXITCODE
}

Write-Host "TeX Live 2026 Windows bootstrap" -ForegroundColor Cyan
Write-Host "Repository: $Repo"
Write-Host "Target:     $TexDir"
Write-Host "Scheme:     small + modeling/paper collections"
Write-Host "Docs/src:   disabled to reduce download size and time"
Write-Host "Download:   resumable curl with retry-all-errors"

New-Item -ItemType Directory -Force $Work | Out-Null
$zip = Join-Path $Work "install-tl.zip"
$extract = Join-Path $Work "installer"

# A previous failed mirror/redirector attempt may have left a truncated final file.
# Only .part files are considered resumable; remove suspicious final ZIPs before retrying.
if (Test-Path $zip) {
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $testZip = [System.IO.Compression.ZipFile]::OpenRead($zip)
        $entryCount = $testZip.Entries.Count
        $testZip.Dispose()
        if ($entryCount -lt 10) { throw "too few entries" }
        Write-Host "Existing installer ZIP passed integrity check; reusing it." -ForegroundColor Green
    } catch {
        Write-Warning "Existing install-tl.zip is incomplete/corrupt; removing it before the resumable SJTUG download."
        Remove-Item -Force $zip
    }
}

if (-not (Test-Path $zip)) {
    Write-Host "`nDownloading TeX Live network installer..." -ForegroundColor Yellow
    try {
        Download-FileResumable "$Repo/install-tl.zip" $zip
    } catch {
        if (-not $UseOfficialCTAN) {
            Write-Warning "SJTUG installer download did not complete. The partial SJTUG file is retained; not switching mirrors automatically because cross-mirror resume can corrupt an archive."
            Write-Warning "Re-run the same command to resume from SJTUG. Use -UseOfficialCTAN only if SJTUG repeatedly fails from zero progress."
            throw
        }
        throw
    }
}

if (Test-Path $extract) { Remove-Item -Recurse -Force $extract }
Expand-Archive -Path $zip -DestinationPath $extract -Force
$installer = Get-ChildItem -Path $extract -Filter install-tl-windows.bat -Recurse -File | Select-Object -First 1
if (-not $installer) { throw "install-tl-windows.bat was not found after extracting $zip" }

Write-Host "`nInstalling TeX Live base scheme..." -ForegroundColor Yellow
& $installer.FullName -no-gui -no-interaction -repository $Repo -scheme small -no-doc-install -no-src-install -texdir $TexDir
if ($LASTEXITCODE -ne 0) {
    throw "TeX Live installer failed with exit code $LASTEXITCODE. Do not delete installer logs; capture the final output."
}

$bin = Join-Path $TexDir "bin\windows"
$tlmgr = Join-Path $bin "tlmgr.bat"
if (-not (Test-Path $tlmgr)) { throw "tlmgr was not found at expected path: $tlmgr" }
Add-UserPathIfMissing $bin

Write-Host "`nInstalling competition paper collections..." -ForegroundColor Yellow
$packages = @(
    "collection-langchinese",
    "collection-latexrecommended",
    "collection-latexextra",
    "collection-mathscience",
    "collection-fontsrecommended",
    "latexmk"
)
& $tlmgr option repository $Repo
if ($LASTEXITCODE -ne 0) { throw "tlmgr failed to select repository $Repo" }
& $tlmgr install @packages
if ($LASTEXITCODE -ne 0) { throw "tlmgr failed while installing required paper collections." }

Write-Host "`nTeX executables:" -ForegroundColor Cyan
& (Join-Path $bin "xelatex.exe") --version | Select-Object -First 1
& (Join-Path $bin "latexmk.exe") -v | Select-Object -First 1

Write-Host "`nRunning Chinese XeLaTeX smoke build..." -ForegroundColor Yellow
& (Join-Path $Root "scripts\tex_smoke.ps1")
if ($LASTEXITCODE -ne 0) { throw "Windows TeX smoke build failed." }

Write-Host "`nWindows TeX Live baseline is ready." -ForegroundColor Green
Write-Host "TeX Live: $TexDir"
Write-Host "PATH:     $bin"
Write-Host "Smoke:    $Root\reports\tex_smoke\main.pdf"

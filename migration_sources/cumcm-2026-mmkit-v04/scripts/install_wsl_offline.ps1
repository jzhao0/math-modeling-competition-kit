param(
    [ValidateSet("Runtime", "Ubuntu", "Verify")]
    [string]$Phase,
    [string]$WslMsiPath,
    [string]$UbuntuWslPath
)

$ErrorActionPreference = "Stop"

$ExpectedWslSha256 = "a460d4560215f2efe003c136244b78ea3415d773824d7a688ea9ded36dbe9145"
$ExpectedUbuntuSha256 = "9b2f7730dc68227dd04a9f3e5eab86ad85caf556b8606ad94f1f29ff5c4fd3f5"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an elevated PowerShell/Windows Terminal."
    }
}

function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "$Label file not found: $Path" }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Host "$Label SHA256: $actual"
    if ($actual -ne $Expected.ToLowerInvariant()) {
        throw "$Label SHA256 mismatch. Do not install this file. Expected: $Expected"
    }
    Write-Host "$Label hash verified." -ForegroundColor Green
}

switch ($Phase) {
    "Runtime" {
        Assert-Administrator
        if (-not $WslMsiPath) { throw "Pass -WslMsiPath with the official x64 WSL 2.7.12 MSI." }
        Assert-Hash $WslMsiPath $ExpectedWslSha256 "WSL MSI"
        Write-Host "Installing WSL runtime..." -ForegroundColor Yellow
        $p = Start-Process -FilePath "msiexec.exe" -ArgumentList @("/i", "`"$WslMsiPath`"", "/passive", "/norestart") -Wait -PassThru
        if ($p.ExitCode -notin @(0, 3010)) { throw "WSL MSI installation failed with exit code $($p.ExitCode)." }
        Write-Host "WSL runtime installed. If Windows requests a restart, restart before installing Ubuntu." -ForegroundColor Green
        & wsl.exe --version
    }
    "Ubuntu" {
        Assert-Administrator
        if (-not $UbuntuWslPath) { throw "Pass -UbuntuWslPath with the official Ubuntu 24.04.4 amd64 .wsl file." }
        Assert-Hash $UbuntuWslPath $ExpectedUbuntuSha256 "Ubuntu WSL"
        & wsl.exe --set-default-version 2
        if ($LASTEXITCODE -ne 0) { throw "Could not set WSL 2 as default. Run -Phase Verify before changing firmware settings." }
        Write-Host "Installing Ubuntu from local .wsl file..." -ForegroundColor Yellow
        & wsl.exe --install --from-file $UbuntuWslPath
        if ($LASTEXITCODE -ne 0) { throw "Ubuntu offline installation failed with exit code $LASTEXITCODE." }
        Write-Host "Ubuntu file installed. Launch the new Ubuntu distro once to complete OOBE/user creation." -ForegroundColor Green
    }
    "Verify" {
        Write-Host "WSL runtime:" -ForegroundColor Yellow
        & wsl.exe --version
        Write-Host "`nWSL status:" -ForegroundColor Yellow
        & wsl.exe --status
        Write-Host "`nDistributions:" -ForegroundColor Yellow
        & wsl.exe --list --verbose
        Write-Host "`nWindows optional features:" -ForegroundColor Yellow
        foreach ($name in @("Microsoft-Windows-Subsystem-Linux", "VirtualMachinePlatform")) {
            $f = Get-WindowsOptionalFeature -Online -FeatureName $name -ErrorAction SilentlyContinue
            if ($f) { Write-Host ("{0}: {1}" -f $name, $f.State) }
        }
        Write-Host "`nFirmware virtualization:" -ForegroundColor Yellow
        Get-CimInstance Win32_Processor | Select-Object -First 1 VirtualizationFirmwareEnabled, VMMonitorModeExtensions | Format-List
    }
}

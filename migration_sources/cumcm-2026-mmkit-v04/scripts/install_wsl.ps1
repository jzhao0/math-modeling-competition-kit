param(
    [ValidateSet("Enable", "Ubuntu", "Verify")]
    [string]$Phase = "Enable"
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This phase requires an elevated PowerShell/Windows Terminal. Reopen the terminal with 'Run as administrator'."
    }
}

function Get-FeatureState([string]$Name) {
    $feature = Get-WindowsOptionalFeature -Online -FeatureName $Name -ErrorAction SilentlyContinue
    if (-not $feature) { return "Unknown" }
    return [string]$feature.State
}

function Show-FeatureState {
    foreach ($name in @("Microsoft-Windows-Subsystem-Linux", "VirtualMachinePlatform")) {
        Write-Host ("{0}: {1}" -f $name, (Get-FeatureState $name))
    }
}

function Test-WslFeatureReady {
    $state = Get-FeatureState "Microsoft-Windows-Subsystem-Linux"
    return ($state -eq "Enabled" -or $state -eq "EnablePending")
}

function Enable-RequiredFeature([string]$Name) {
    $before = Get-FeatureState $Name
    Write-Host ("> Enable-WindowsOptionalFeature -Online -FeatureName {0} -All -NoRestart  (current: {1})" -f $Name, $before) -ForegroundColor Cyan

    if ($before -eq "Enabled" -or $before -eq "EnablePending") {
        return
    }

    Enable-WindowsOptionalFeature -Online -FeatureName $Name -All -NoRestart -ErrorAction Stop | Out-Null

    $after = Get-FeatureState $Name
    if ($after -ne "Enabled" -and $after -ne "EnablePending") {
        throw "$Name did not enter Enabled/EnablePending state after Enable-WindowsOptionalFeature. Current state: $after"
    }
}

switch ($Phase) {
    "Enable" {
        Assert-Administrator
        Write-Host "Current Windows feature state:" -ForegroundColor Yellow
        Show-FeatureState

        Write-Host "`nEnabling Windows Subsystem for Linux and Virtual Machine Platform..." -ForegroundColor Yellow
        Enable-RequiredFeature "Microsoft-Windows-Subsystem-Linux"
        Enable-RequiredFeature "VirtualMachinePlatform"

        Write-Host "`nFeature state after enable commands:" -ForegroundColor Yellow
        Show-FeatureState

        if (-not (Test-WslFeatureReady)) {
            throw "Microsoft-Windows-Subsystem-Linux is still not Enabled/EnablePending. Do not continue to runtime installation."
        }

        Write-Host "Feature enablement is staged successfully. RESTART WINDOWS, then run -Phase Verify before installing the WSL runtime." -ForegroundColor Green
    }

    "Ubuntu" {
        Assert-Administrator
        if (-not (Test-WslFeatureReady)) {
            throw "Microsoft-Windows-Subsystem-Linux is not Enabled. Run -Phase Enable from an elevated terminal and restart Windows before installing the runtime or Ubuntu."
        }

        Write-Host "Checking Windows feature state..." -ForegroundColor Yellow
        Show-FeatureState
        Write-Host "Installing/updating the packaged WSL runtime. Store-independent download is requested where supported." -ForegroundColor Yellow

        & wsl.exe --update --web-download
        if ($LASTEXITCODE -ne 0) {
            throw "The packaged WSL runtime download failed. This is a download/network-path failure; do NOT infer a BIOS virtualization problem from it. Use scripts/install_wsl_offline.ps1 instead of repeatedly retrying."
        }

        & wsl.exe --set-default-version 2
        if ($LASTEXITCODE -ne 0) {
            throw "The WSL runtime is present but WSL 2 could not be selected. Run -Phase Verify and inspect feature/firmware virtualization state before changing BIOS settings."
        }

        & wsl.exe --install -d Ubuntu-24.04 --web-download
        if ($LASTEXITCODE -ne 0) {
            throw "Ubuntu 24.04 online installation failed. Use scripts/install_wsl_offline.ps1 rather than repeatedly retrying the same download path."
        }

        Write-Host "Ubuntu installation command completed. Launch Ubuntu once to create the Linux user, then run -Phase Verify." -ForegroundColor Green
    }

    "Verify" {
        Write-Host "Windows feature state:" -ForegroundColor Yellow
        Show-FeatureState

        $wslFeatureState = Get-FeatureState "Microsoft-Windows-Subsystem-Linux"
        if ($wslFeatureState -ne "Enabled") {
            Write-Warning "WSL optional feature is '$wslFeatureState'. Runtime/distro checks are skipped to avoid triggering Windows' interactive WSL install prompt."
        } else {
            Write-Host "`nWSL status:" -ForegroundColor Yellow
            & wsl.exe --status
            Write-Host "`nWSL runtime version:" -ForegroundColor Yellow
            & wsl.exe --version
            Write-Host "`nInstalled distributions:" -ForegroundColor Yellow
            & wsl.exe --list --verbose
        }

        Write-Host "`nVirtualization firmware flags:" -ForegroundColor Yellow
        $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
        [pscustomobject]@{
            VirtualizationFirmwareEnabled = $cpu.VirtualizationFirmwareEnabled
            VMMonitorModeExtensions = $cpu.VMMonitorModeExtensions
        } | Format-List
    }
}

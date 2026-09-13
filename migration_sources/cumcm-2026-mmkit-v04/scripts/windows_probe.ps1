$ErrorActionPreference = "SilentlyContinue"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ReportDir = Join-Path $Root "reports"
New-Item -ItemType Directory -Force $ReportDir | Out-Null
$OutFile = Join-Path $ReportDir "windows_environment.json"

function Get-CmdInfo([string]$Name, [string[]]$VersionArgs = @("--version")) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        return [ordered]@{ installed = $false; in_path = $false; version = $null; path = $null }
    }
    $version = $null
    try {
        $raw = & $Name @VersionArgs 2>&1 | Select-Object -First 1
        if ($raw) { $version = "$raw".Trim() }
    } catch {}
    return [ordered]@{ installed = $true; in_path = $true; version = $version; path = $cmd.Source }
}

function Get-InstalledApps {
    $roots = @(
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    $pattern = "MATLAB|Mathematica|Wolfram|Mathcad|AxMath|WinRAR|WPS|Microsoft 365|Microsoft Office|MiKTeX|TeX Live"
    $items = foreach ($r in $roots) {
        Get-ItemProperty $r -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -and $_.DisplayName -match $pattern } |
            ForEach-Object {
                [ordered]@{
                    name = $_.DisplayName
                    version = $_.DisplayVersion
                    publisher = $_.Publisher
                    install_location = if ($_.InstallLocation) { $_.InstallLocation } else { $null }
                }
            }
    }
    return ,@($items | Sort-Object name, version -Unique)
}

function Get-WslInfo {
    $installed = [bool](Get-Command wsl.exe -ErrorAction SilentlyContinue)
    $distros = @()
    $defaultGuid = $null

    if ($installed) {
        try {
            $lxss = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss"
            if (Test-Path $lxss) {
                $rootProps = Get-ItemProperty $lxss -ErrorAction SilentlyContinue
                $defaultGuid = $rootProps.DefaultDistribution
                $distros = @(
                    Get-ChildItem $lxss -ErrorAction SilentlyContinue | ForEach-Object {
                        $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
                        if ($p.DistributionName) {
                            [ordered]@{
                                name = $p.DistributionName
                                version = $p.Version
                                default = ($_.PSChildName -eq $defaultGuid)
                            }
                        }
                    }
                )
            }
        } catch {}
    }

    return [ordered]@{
        installed = $installed
        distributions = @($distros)
    }
}

$ghAuth = $false
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh auth status *> $null
    $ghAuth = ($LASTEXITCODE -eq 0)
}

$installedApps = @(Get-InstalledApps)

$report = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    os = [ordered]@{
        caption = (Get-CimInstance Win32_OperatingSystem).Caption
        version = (Get-CimInstance Win32_OperatingSystem).Version
        architecture = $env:PROCESSOR_ARCHITECTURE
    }
    wsl = Get-WslInfo
    cli = [ordered]@{
        powershell = [ordered]@{ installed = $true; in_path = $true; version = $PSVersionTable.PSVersion.ToString(); path = $PSHOME }
        git = Get-CmdInfo "git"
        gh = Get-CmdInfo "gh"
        gh_authenticated = $ghAuth
        python = Get-CmdInfo "python"
        py_launcher = Get-CmdInfo "py" @("--version")
        node = Get-CmdInfo "node"
        npm = Get-CmdInfo "npm"
        uv = Get-CmdInfo "uv"
        xelatex = Get-CmdInfo "xelatex"
        latexmk = Get-CmdInfo "latexmk" @("-v")
        rar = Get-CmdInfo "rar"
        matlab = Get-CmdInfo "matlab" @("-batch", "disp(version)")
        wolframscript = Get-CmdInfo "wolframscript" @("-version")
        opencode = Get-CmdInfo "opencode"
        claude = Get-CmdInfo "claude"
        codex = Get-CmdInfo "codex"
        dsh = Get-CmdInfo "dsh"
    }
    installed_apps = @($installedApps)
}

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $OutFile -Encoding UTF8
Write-Host "Environment report written to: $OutFile"
Write-Host "This report intentionally excludes API keys, tokens, usernames and home-directory paths."
$report | ConvertTo-Json -Depth 8

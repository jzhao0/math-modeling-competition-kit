[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Workspace,
    [string]$MainTex = '06_paper\main.tex',
    [string]$FactsConfig,
    [string]$SectionsConfig,
    [string]$LanguageConfig,
    [string]$FigureConfig,
    [switch]$BuildSolReviewPacket
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = (Resolve-Path -LiteralPath $Workspace).Path
$mainCandidate = if ([IO.Path]::IsPathRooted($MainTex)) { $MainTex } else { Join-Path $workspaceRoot $MainTex }
$mainPath = [IO.Path]::GetFullPath($mainCandidate)
$paperDir = Split-Path -Parent $mainPath
$submissionDir = Join-Path $workspaceRoot '09_submission'
$buildDir = Join-Path $submissionDir 'build\paper_gate'
$reportsDir = Join-Path $workspaceRoot 'reports'
$partsDir = Join-Path $reportsDir 'paper_gate_parts'
$finalPdf = Join-Path $submissionDir 'paper.pdf'
$textPath = Join-Path $buildDir 'paper.txt'
$bboxPath = Join-Path $buildDir 'paper.bbox.html'
$pdfInfoPath = Join-Path $buildDir 'pdfinfo.txt'
$sourceBundle = Join-Path $buildDir 'paper_sources.tex.txt'
$jsonReport = Join-Path $reportsDir 'paper_gate.json'
$markdownReport = Join-Path $reportsDir 'paper_gate.md'

if (-not $FactsConfig) { $FactsConfig = Join-Path $repoRoot 'config\paper_facts.yaml' }
if (-not $SectionsConfig) { $SectionsConfig = Join-Path $repoRoot 'config\paper_sections.yaml' }
if (-not $LanguageConfig) { $LanguageConfig = Join-Path $repoRoot 'config\paper_language_rules.yaml' }
if (-not $FigureConfig) { $FigureConfig = Join-Path $repoRoot 'config\figure_contracts.yaml' }

$findings = [System.Collections.Generic.List[object]]::new()
$checkerReports = [System.Collections.Generic.List[object]]::new()
$toolResults = [ordered]@{}

function Add-Finding {
    param([string]$Level, [string]$Code, [string]$Message, [string]$Location = '', [string]$Evidence = '')
    $entry = [ordered]@{ level = $Level; code = $Code; message = $Message }
    if ($Location) { $entry.location = $Location }
    if ($Evidence) { $entry.evidence = $Evidence.Substring(0, [Math]::Min(240, $Evidence.Length)) }
    $findings.Add([pscustomobject]$entry)
}

function Resolve-Tool {
    param([string]$Name, [string[]]$Candidates = @())
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in $Candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Set-ToolResult {
    param([string]$Name, [string]$Path, [bool]$Required, [string]$Suggestion)
    if ($Path) {
        $toolResults[$Name] = [ordered]@{ status = 'AVAILABLE'; path = $Path; required = $Required }
    } else {
        $toolResults[$Name] = [ordered]@{ status = 'OPTIONAL_MISSING'; required = $Required; install_suggestion = $Suggestion }
        if ($Required) {
            $toolResults[$Name].status = 'MISSING'
            Add-Finding 'ERROR' 'REQUIRED_TOOL_MISSING' "Required tool '$Name' is unavailable." $Name
        }
    }
}

function Invoke-Checker {
    param([string]$Name, [string]$Script, [string[]]$Arguments, [string]$Output)
    & $python $Script @Arguments --output $Output | Out-Null
    $exitCode = $LASTEXITCODE
    if (-not (Test-Path -LiteralPath $Output)) {
        Add-Finding 'ERROR' 'CHECKER_REPORT_MISSING' "Checker '$Name' did not produce a report (exit $exitCode)." $Name
        return
    }
    try {
        $report = Get-Content -LiteralPath $Output -Raw -Encoding UTF8 | ConvertFrom-Json
        $checkerReports.Add($report)
        foreach ($item in $report.findings) { $findings.Add($item) }
    } catch {
        Add-Finding 'ERROR' 'CHECKER_REPORT_INVALID' "Checker '$Name' produced invalid JSON: $($_.Exception.Message)" $Name
    }
}

function Invoke-OptionalTextTool {
    param([string]$Name, [string]$Path, [string[]]$Arguments, [string]$FailureLevel = 'ERROR')
    if (-not $Path) { return }
    $output = & $Path @Arguments 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Add-Finding $FailureLevel ($Name.ToUpperInvariant() + '_FAILED') "$Name reported findings or failed with exit code $exitCode." $Name $output.Trim()
    } elseif ($output.Trim()) {
        Add-Finding 'WARNING' ($Name.ToUpperInvariant() + '_OUTPUT') "$Name produced advisory output." $Name $output.Trim()
    }
}

function Get-TeXSourceGraph {
    param([string]$RootTex)
    $pending = [System.Collections.Generic.Queue[string]]::new()
    $visited = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $ordered = [System.Collections.Generic.List[string]]::new()
    $pending.Enqueue([IO.Path]::GetFullPath($RootTex))
    while ($pending.Count -gt 0) {
        $current = $pending.Dequeue()
        if (-not $visited.Add($current)) { continue }
        if (-not (Test-Path -LiteralPath $current -PathType Leaf)) {
            Add-Finding 'ERROR' 'TEX_DEPENDENCY_MISSING' "Referenced TeX source not found: $current" $current
            continue
        }
        $ordered.Add($current)
        $content = Get-Content -LiteralPath $current -Raw -Encoding UTF8
        foreach ($match in [regex]::Matches($content, '\\(?:input|include)\{([^}]+)\}')) {
            $reference = $match.Groups[1].Value.Trim()
            if ($reference -match '[#\\]') {
                Add-Finding 'WARNING' 'TEX_DEPENDENCY_DYNAMIC' "Dynamic TeX dependency cannot be resolved statically: $reference" $current
                continue
            }
            $dependency = Join-Path (Split-Path -Parent $current) $reference
            if (-not [IO.Path]::HasExtension($dependency)) { $dependency += '.tex' }
            $pending.Enqueue([IO.Path]::GetFullPath($dependency))
        }
    }
    return $ordered.ToArray()
}

Write-Host 'PRECHECK' -ForegroundColor Cyan
Write-Host "MAIN TEX: $mainPath" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $buildDir, $reportsDir, $partsDir, $submissionDir | Out-Null

$python = Resolve-Tool 'python' @((Join-Path $repoRoot '.venv\Scripts\python.exe'))
$xelatex = Resolve-Tool 'xelatex' @('D:\texlive\2026\bin\windows\xelatex.exe')
$pdfinfo = Resolve-Tool 'pdfinfo' @('D:\texlive\2026\bin\windows\pdfinfo.exe')
$pdftotext = Resolve-Tool 'pdftotext' @('D:\texlive\2026\bin\windows\pdftotext.exe')
$zhlint = Resolve-Tool 'zhlint'
$vale = Resolve-Tool 'vale'
$textidote = Resolve-Tool 'textidote'
$latexindent = Resolve-Tool 'latexindent'
if (-not $latexindent) { $latexindent = Resolve-Tool 'latexindent.pl' }

Set-ToolResult 'python' $python $true 'Use the repository Python environment.'
Set-ToolResult 'xelatex' $xelatex $true 'Install/freeze TeX Live with XeLaTeX before contest day.'
Set-ToolResult 'pdfinfo' $pdfinfo $true 'Install the Poppler utilities supplied by TeX Live.'
Set-ToolResult 'pdftotext' $pdftotext $true 'Install the Poppler utilities supplied by TeX Live.'
Set-ToolResult 'zhlint' $zhlint $false 'Install zhlint in a project-scoped Node environment; do not install globally during a Gate run.'
Set-ToolResult 'Vale' $vale $false 'Download/freeze a Vale release and add it to PATH; do not enable auto-fix.'
Set-ToolResult 'TeXtidote' $textidote $false 'Freeze TeXtidote and its Java runtime before the contest.'
Set-ToolResult 'latexindent' $latexindent $false 'Install the TeX Live latexindent package and Perl dependencies; use check/temp output only.'

if (-not (Test-Path -LiteralPath $mainPath -PathType Leaf)) {
    Add-Finding 'ERROR' 'MAIN_TEX_MISSING' "Paper source not found: $mainPath" $mainPath
}
foreach ($configPath in @($FactsConfig, $SectionsConfig, $LanguageConfig, $FigureConfig)) {
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        Add-Finding 'ERROR' 'CONFIG_MISSING' "Gate configuration not found: $configPath" $configPath
        continue
    }
    try { Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null }
    catch { Add-Finding 'ERROR' 'CONFIG_INVALID' "Configuration must be JSON-compatible YAML: $configPath. $($_.Exception.Message)" $configPath }
}

$compiledPdf = Join-Path $buildDir ([IO.Path]::GetFileNameWithoutExtension($mainPath) + '.pdf')
$precheckErrors = @($findings | Where-Object level -eq 'ERROR').Count
if ($precheckErrors -eq 0) {
    Push-Location $paperDir
    try {
        for ($pass = 1; $pass -le 2; $pass++) {
            Write-Host "XeLaTeX pass $pass/2" -ForegroundColor Cyan
            $compileOutput = & $xelatex -interaction=nonstopmode -halt-on-error "-output-directory=$buildDir" $mainPath 2>&1 | Out-String
            if ($LASTEXITCODE -ne 0) {
                Add-Finding 'ERROR' 'XELATEX_FAILED' "XeLaTeX pass $pass failed with exit code $LASTEXITCODE." "pass:$pass" $compileOutput.Trim()
                break
            }
        }
    } finally {
        Pop-Location
    }
}

$latexLog = Join-Path $buildDir ([IO.Path]::GetFileNameWithoutExtension($mainPath) + '.log')
if (Test-Path -LiteralPath $latexLog) {
    $logText = Get-Content -LiteralPath $latexLog -Raw -Encoding UTF8
    if ($logText -match '(?im)(undefined references|Reference .+ undefined|Citation .+ undefined)') {
        Add-Finding 'ERROR' 'LATEX_UNDEFINED_REFERENCE' 'LaTeX log contains an undefined reference or citation.' $latexLog
    }
    if ($logText -match '(?im)Overfull \\hbox') {
        Add-Finding 'WARNING' 'LATEX_OVERFULL_HBOX' 'LaTeX log contains one or more overfull hboxes.' $latexLog
    }
    if ($logText -match '(?im)Missing character:') {
        Add-Finding 'ERROR' 'LATEX_MISSING_CHARACTER' 'LaTeX log reports missing characters.' $latexLog
    }
} elseif ($precheckErrors -eq 0) {
    Add-Finding 'ERROR' 'LATEX_LOG_MISSING' "Expected LaTeX log was not generated: $latexLog" $latexLog
}

if (Test-Path -LiteralPath $compiledPdf) {
    Copy-Item -Force -LiteralPath $compiledPdf -Destination $finalPdf
    $pdfInfoOutput = & $pdfinfo $compiledPdf 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { Add-Finding 'ERROR' 'PDFINFO_FAILED' "pdfinfo failed with exit code $LASTEXITCODE." $compiledPdf $pdfInfoOutput.Trim() }
    else { Set-Content -LiteralPath $pdfInfoPath -Value $pdfInfoOutput -Encoding UTF8 }

    & $pdftotext -layout -enc UTF-8 $compiledPdf $textPath 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Add-Finding 'ERROR' 'PDFTOTEXT_FAILED' "pdftotext failed with exit code $LASTEXITCODE." $compiledPdf }
    & $pdftotext -bbox $compiledPdf $bboxPath 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Add-Finding 'ERROR' 'PDFTOTEXT_BBOX_FAILED' "pdftotext -bbox failed with exit code $LASTEXITCODE." $compiledPdf }
} elseif ($precheckErrors -eq 0) {
    Add-Finding 'ERROR' 'COMPILED_PDF_MISSING' "Expected compiled PDF not found: $compiledPdf" $compiledPdf
}

if (Test-Path -LiteralPath $mainPath -PathType Leaf) {
    $sourceFiles = Get-TeXSourceGraph $mainPath
    $sourceParts = $sourceFiles | ForEach-Object {
        "% SOURCE: $($_)`n" + (Get-Content -LiteralPath $_ -Raw -Encoding UTF8)
    }
    Set-Content -LiteralPath $sourceBundle -Value ($sourceParts -join "`n") -Encoding UTF8
}

if ($python -and (Test-Path -LiteralPath $textPath)) {
    Write-Host 'Fact, structure, and language checks' -ForegroundColor Cyan
    Invoke-Checker 'paper_facts' (Join-Path $PSScriptRoot 'check_paper_facts.py') @('--text', $textPath, '--config', $FactsConfig) (Join-Path $partsDir 'facts.json')
    $structureArgs = @('--text', $textPath, '--config', $SectionsConfig)
    $languageArgs = @('--text', $textPath, '--config', $LanguageConfig)
    if (Test-Path -LiteralPath $sourceBundle) {
        $structureArgs += @('--source', $sourceBundle)
        $languageArgs += @('--source', $sourceBundle)
    }
    Invoke-Checker 'paper_structure' (Join-Path $PSScriptRoot 'check_paper_structure.py') $structureArgs (Join-Path $partsDir 'structure.json')
    Invoke-Checker 'paper_language' (Join-Path $PSScriptRoot 'lint_paper_language.py') $languageArgs (Join-Path $partsDir 'language.json')
}

if ($python -and (Test-Path -LiteralPath $bboxPath)) {
    Write-Host 'Layout check' -ForegroundColor Cyan
    $layoutArgs = @('--bbox', $bboxPath, '--config', $FigureConfig, '--sections-config', $SectionsConfig)
    if (Test-Path -LiteralPath $pdfInfoPath) { $layoutArgs += @('--pdfinfo-text', $pdfInfoPath) }
    if (Test-Path -LiteralPath $sourceBundle) { $layoutArgs += @('--source', $sourceBundle) }
    Invoke-Checker 'paper_layout' (Join-Path $PSScriptRoot 'check_paper_layout.py') $layoutArgs (Join-Path $partsDir 'layout.json')
}

if (Test-Path -LiteralPath $textPath) {
    Write-Host 'Optional linters' -ForegroundColor Cyan
    Invoke-OptionalTextTool 'zhlint' $zhlint @($textPath) 'ERROR'
    if ($vale) {
        $valeOutput = & $vale "--config=$(Join-Path $repoRoot 'styles\cumcm\.vale.ini')" --output=JSON --no-exit $textPath 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Add-Finding 'ERROR' 'VALE_FAILED' "Vale failed with exit code $LASTEXITCODE." 'Vale' $valeOutput.Trim()
        } elseif ($valeOutput.Trim() -and $valeOutput.Trim() -ne '{}') {
            try {
                $valeJson = $valeOutput | ConvertFrom-Json
                foreach ($property in $valeJson.PSObject.Properties) {
                    foreach ($alert in $property.Value) {
                        $level = if ($alert.Severity -eq 'error') { 'ERROR' } else { 'WARNING' }
                        Add-Finding $level 'VALE_STYLE' $alert.Message $property.Name $alert.Check
                    }
                }
            } catch { Add-Finding 'ERROR' 'VALE_OUTPUT_INVALID' 'Vale returned invalid JSON.' 'Vale' $valeOutput.Trim() }
        }
    }
}
if ($textidote -and (Test-Path -LiteralPath $mainPath)) {
    Invoke-OptionalTextTool 'TeXtidote' $textidote @('--no-color', '--output', 'plain', $mainPath) 'ERROR'
}
if ($latexindent -and (Test-Path -LiteralPath $mainPath)) {
    $indentOutput = Join-Path $buildDir 'main.latexindent.tex'
    $indentLog = & $latexindent -s "-o=$indentOutput" $mainPath 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Add-Finding 'WARNING' 'LATEXINDENT_CHECK_FAILED' "latexindent temporary formatting check failed with exit code $LASTEXITCODE." 'latexindent' $indentLog.Trim()
    } elseif ((Test-Path -LiteralPath $indentOutput) -and ((Get-FileHash -LiteralPath $indentOutput).Hash -ne (Get-FileHash -LiteralPath $mainPath).Hash)) {
        Add-Finding 'WARNING' 'LATEXINDENT_DIFF' 'latexindent would change main.tex; inspect the temporary output. The Gate did not rewrite the source.' $indentOutput
    }
}

$errorCount = @($findings | Where-Object level -eq 'ERROR').Count
$warningCount = @($findings | Where-Object level -eq 'WARNING').Count
$status = if ($errorCount -gt 0) { 'FAIL' } elseif ($warningCount -gt 0) { 'PASS_WITH_WARNINGS' } else { 'PASS' }
$report = [ordered]@{
    schema_version = 1
    status = $status
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    workspace = $workspaceRoot
    main_tex = $mainPath
    pdf = if (Test-Path -LiteralPath $finalPdf) { $finalPdf } else { $null }
    errors = $errorCount
    warnings = $warningCount
    tools = $toolResults
    checker_reports = $checkerReports
    findings = $findings
}
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $jsonReport -Encoding UTF8

$markdown = [System.Collections.Generic.List[string]]::new()
$markdown.Add('# CUMCM Paper Quality Gate')
$markdown.Add('')
$markdown.Add("- Status: **$status**")
$markdown.Add("- Errors: $errorCount")
$markdown.Add("- Warnings: $warningCount")
$markdown.Add("- Main: ``$mainPath``")
$markdown.Add('')
$markdown.Add('## Tools')
$markdown.Add('')
$markdown.Add('| Tool | Status | Path / suggestion |')
$markdown.Add('|---|---|---|')
foreach ($property in $toolResults.GetEnumerator()) {
    $detail = if ($property.Value.path) { $property.Value.path } else { $property.Value.install_suggestion }
    $markdown.Add("| $($property.Key) | $($property.Value.status) | $($detail -replace '\|', '\|') |")
}
$markdown.Add('')
$markdown.Add('## Findings')
$markdown.Add('')
if ($findings.Count -eq 0) {
    $markdown.Add('No findings.')
} else {
    $markdown.Add('| Level | Code | Message | Location |')
    $markdown.Add('|---|---|---|---|')
    foreach ($item in $findings) {
        $message = ([string]$item.message) -replace '\|', '\|' -replace "`r?`n", ' '
        $markdown.Add("| $($item.level) | $($item.code) | $message | $($item.location) |")
    }
}
$markdown | Set-Content -LiteralPath $markdownReport -Encoding UTF8

$solPacketPath = Join-Path $reportsDir 'sol_review_packet.md'
if ($BuildSolReviewPacket) {
    Write-Host 'Building deterministic Sol review packet' -ForegroundColor Cyan
    $packetArguments = @(
        (Join-Path $PSScriptRoot 'build_sol_review_packet.py'),
        '--workspace', $workspaceRoot,
        '--main-tex', $mainPath,
        '--paper-pdf', $finalPdf,
        '--gate-json', $jsonReport,
        '--gate-md', $markdownReport,
        '--facts-config', $FactsConfig,
        '--sections-config', $SectionsConfig
    )
    & $python @packetArguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Sol review packet generation failed with exit code $LASTEXITCODE. Gate status is unchanged."
    }
}

Write-Host "FINAL GATE: $status (errors=$errorCount, warnings=$warningCount)" -ForegroundColor $(if ($status -eq 'FAIL') { 'Red' } elseif ($status -eq 'PASS_WITH_WARNINGS') { 'Yellow' } else { 'Green' })
Write-Host "MAIN TEX: $mainPath"
Write-Host "JSON: $jsonReport"
Write-Host "Markdown: $markdownReport"
if ($BuildSolReviewPacket -and (Test-Path -LiteralPath $solPacketPath)) {
    Write-Host 'SOL REVIEW PACKET:'
    Write-Host $solPacketPath
}
if ($status -eq 'FAIL') { exit 1 }
exit 0

# check-readme-freshness.ps1
# Start-Hook: checks whether README.md in the repo root is consistent with
# the actual codebase — file references, counts (tests, workflows, agents,
# prompts, skills, hooks). Reports all mismatches so the agent can fix them.
#
# Compatible with PowerShell 5.1+
#
# Input (stdin):  JSON with { cwd, ... }
# Output (stdout): JSON with hookSpecificOutput for the Start event

param()
$ErrorActionPreference = 'Stop'

# --- Read hook input from stdin ---------------------------------------------------
$rawInput  = [Console]::In.ReadToEnd()
$hookInput = $rawInput | ConvertFrom-Json
$repoRoot  = $hookInput.cwd

# --- Paths ------------------------------------------------------------------------
$projectDir = Join-Path $repoRoot 'Mcp.Connector.Template'
$testDir    = Join-Path $repoRoot 'Mcp.Connector.Template.Tests'
$readmePath = Join-Path $repoRoot 'README.md'
$githubDir  = Join-Path $repoRoot '.github'

# --- Helper: build the inform-JSON response string --------------------------------
function Write-Inform([string]$Message) {
    # Escape for JSON value
    $escaped = $Message -replace '\\', '\\\\' -replace '"', '\"'
    Write-Output "{`"hookSpecificOutput`":{`"hookEventName`":`"Start`",`"decision`":`"inform`",`"reason`":`"$escaped`"}}"
}

# --- Guard: README must exist -----------------------------------------------------
if (-not (Test-Path $readmePath)) {
    Write-Inform 'README.md does not exist in the repo root. Please create one.'
    exit 0
}

$readme = Get-Content -Path $readmePath -Raw
$issues = New-Object System.Collections.ArrayList

# === 1. Check that every Tool/Service/Model file is mentioned =====================

$dirsToCheck = @(
    @{ Path = Join-Path $projectDir 'Tools';    Label = 'Tools' }
    @{ Path = Join-Path $projectDir 'Services'; Label = 'Services' }
    @{ Path = Join-Path $projectDir 'Models';   Label = 'Models' }
)

foreach ($entry in $dirsToCheck) {
    if (Test-Path $entry.Path) {
        Get-ChildItem -Path $entry.Path -Filter '*.cs' -File | ForEach-Object {
            if ($readme -notmatch [regex]::Escape($_.Name)) {
                [void]$issues.Add("$($entry.Label)/$($_.Name) is not mentioned in README.md")
            }
        }
    }
}

# === 2. Check counted items (pattern: **N something**) ============================

function Test-ReadmeCount([string]$Pattern, [int]$Actual, [string]$Label) {
    if ($readme -match $Pattern) {
        $claimed = [int]$Matches[1]
        if ($claimed -ne $Actual) {
            [void]$issues.Add("README claims $claimed $Label but found $Actual")
        }
    }
}

function Get-DirFileCount([string]$Dir, [string]$Filter) {
    if (-not (Test-Path $Dir)) { return 0 }
    return @(Get-ChildItem -Path $Dir -Filter $Filter -File).Count
}

# Workflows
$wfDir = Join-Path $githubDir 'workflows'
Test-ReadmeCount '\*\*(\d+)\s+GitHub Actions workflows?\*\*' (Get-DirFileCount $wfDir '*.yml') 'GitHub Actions workflows'

# Agents
$agDir = Join-Path $githubDir 'agents'
Test-ReadmeCount '\*\*(\d+)\s+custom Copilot agents?\*\*' (Get-DirFileCount $agDir '*.agent.md') 'custom Copilot agents'

# Prompts
$prDir = Join-Path $githubDir 'prompts'
Test-ReadmeCount '\*\*(\d+)\s+prompt files?\*\*' (Get-DirFileCount $prDir '*.prompt.md') 'prompt files'

# Skills (count subdirectories that contain a SKILL.md)
$skDir      = Join-Path $githubDir 'skills'
$skillCount = 0
if (Test-Path $skDir) {
    $skillCount = @(Get-ChildItem -Path $skDir -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
}
Test-ReadmeCount '\*\*(\d+)\s+skill guides?\*\*' $skillCount 'skill guides'

# Hooks
$hkDir = Join-Path $githubDir 'hooks'
Test-ReadmeCount '\*\*(\d+)\s+Copilot hooks?\*\*' (Get-DirFileCount $hkDir '*.json') 'Copilot hooks'

# === 3. Check test count (if README claims a number) ==============================
if ($readme -match '\b(\d+)\s+tests?\b') {
    $claimedTests = [int]$Matches[1]
    $actualTests  = 0
    if (Test-Path $testDir) {
        Get-ChildItem -Path $testDir -Filter '*.cs' -Recurse -File | ForEach-Object {
            $content       = Get-Content -Path $_.FullName -Raw
            $factMatches   = [regex]::Matches($content, '\[Fact\]')
            $theoryMatches = [regex]::Matches($content, '\[Theory\]')
            $actualTests  += $factMatches.Count + $theoryMatches.Count
        }
    }
    if ($claimedTests -ne $actualTests) {
        [void]$issues.Add("README claims $claimedTests tests but the test project has $actualTests test methods")
    }
}

# === 4. Check that every test file referenced in README exists ====================
$testFilePattern = [regex]'Tests/\w+/(\w+Tests)\.cs'
$testFileMatches = $testFilePattern.Matches($readme)
foreach ($m in $testFileMatches) {
    $fileName = "$($m.Groups[1].Value).cs"
    $found = Get-ChildItem -Path $testDir -Filter $fileName -Recurse -File -ErrorAction SilentlyContinue
    if (-not $found) {
        [void]$issues.Add("README references test file '$fileName' but it does not exist")
    }
}

# === Decide =======================================================================
if ($issues.Count -gt 0) {
    $issueList = ($issues.ToArray()) -join '; '
    $msg = "README.md is out of sync with the codebase: $issueList. " +
           "Please update README.md to match the current state before continuing."
    Write-Inform $msg
    exit 0
}

# README is up-to-date
Write-Output '{"continue":true}'
exit 0

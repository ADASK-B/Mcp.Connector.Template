# check-readme-freshness.ps1
# Start-Hook: checks whether README.md in the repo root is consistent with
# the actual codebase — file references, counts (tests, workflows, agents,
# prompts, skills, hooks). Reports all mismatches so the agent can fix them.
#
# Input (stdin):  JSON with { cwd, ... }
# Output (stdout): JSON with hookSpecificOutput for the Start event

param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Read hook input from stdin ---------------------------------------------------
$rawInput  = [Console]::In.ReadToEnd()
$hookInput = $rawInput | ConvertFrom-Json
$repoRoot  = $hookInput.cwd

# --- Paths ------------------------------------------------------------------------
$projectDir  = Join-Path $repoRoot 'Mcp.Connector.Template'
$testDir     = Join-Path $repoRoot 'Mcp.Connector.Template.Tests'
$readmePath  = Join-Path $repoRoot 'README.md'
$githubDir   = Join-Path $repoRoot '.github'

# --- Guard: README must exist -----------------------------------------------------
if (-not (Test-Path $readmePath)) {
    $output = @{
        hookSpecificOutput = @{
            hookEventName = 'Start'
            decision      = 'inform'
            reason        = 'README.md does not exist in the repo root. Please create one.'
        }
    } | ConvertTo-Json -Compress
    Write-Output $output
    exit 0
}

$readme = Get-Content -Path $readmePath -Raw
$issues = [System.Collections.Generic.List[string]]::new()

# === 1. Check that every Tool/Service/Model file is mentioned =====================

function Test-FilesInReadme {
    param([string]$Dir, [string]$Label)
    if (-not (Test-Path $Dir)) { return }
    Get-ChildItem -Path $Dir -Filter '*.cs' -File | ForEach-Object {
        if ($readme -notmatch [regex]::Escape($_.Name)) {
            $issues.Add("$Label/$($_.Name) is not mentioned in README.md")
        }
    }
}

Test-FilesInReadme (Join-Path $projectDir 'Tools')    'Tools'
Test-FilesInReadme (Join-Path $projectDir 'Services') 'Services'
Test-FilesInReadme (Join-Path $projectDir 'Models')   'Models'

# === 2. Check counted items (pattern: **N something**) ============================

function Test-Count {
    param([string]$Pattern, [int]$Actual, [string]$Label)
    # Match patterns like "**4 GitHub Actions workflows**" in the README
    if ($readme -match $Pattern) {
        $claimed = [int]$Matches[1]
        if ($claimed -ne $Actual) {
            $issues.Add("README claims $claimed $Label but found $Actual")
        }
    }
}

# Workflows
$workflowDir = Join-Path $githubDir 'workflows'
$workflowCount = if (Test-Path $workflowDir) { @(Get-ChildItem -Path $workflowDir -Filter '*.yml' -File).Count } else { 0 }
Test-Count '\*\*(\d+)\s+GitHub Actions workflows?\*\*' $workflowCount 'GitHub Actions workflows'

# Agents
$agentDir = Join-Path $githubDir 'agents'
$agentCount = if (Test-Path $agentDir) { @(Get-ChildItem -Path $agentDir -Filter '*.agent.md' -File).Count } else { 0 }
Test-Count '\*\*(\d+)\s+custom Copilot agents?\*\*' $agentCount 'custom Copilot agents'

# Prompts
$promptDir = Join-Path $githubDir 'prompts'
$promptCount = if (Test-Path $promptDir) { @(Get-ChildItem -Path $promptDir -Filter '*.prompt.md' -File).Count } else { 0 }
Test-Count '\*\*(\d+)\s+prompt files?\*\*' $promptCount 'prompt files'

# Skills
$skillDir = Join-Path $githubDir 'skills'
$skillCount = if (Test-Path $skillDir) { @(Get-ChildItem -Path $skillDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count } else { 0 }
Test-Count '\*\*(\d+)\s+skill guides?\*\*' $skillCount 'skill guides'

# Hooks
$hookDir = Join-Path $githubDir 'hooks'
$hookCount = if (Test-Path $hookDir) { @(Get-ChildItem -Path $hookDir -Filter '*.json' -File).Count } else { 0 }
Test-Count '\*\*(\d+)\s+Copilot hooks?\*\*' $hookCount 'Copilot hooks'

# === 3. Check test count (if README claims a number) ==============================
# Match patterns like "18 tests", "18/18 tests", "insgesamt: 18"
if ($readme -match '\b(\d+)\s+tests?\b') {
    $claimedTests = [int]$Matches[1]
    # Count [Fact] and [Theory] attributes in test files
    $actualTests = 0
    if (Test-Path $testDir) {
        Get-ChildItem -Path $testDir -Filter '*.cs' -Recurse -File | ForEach-Object {
            $content = Get-Content -Path $_.FullName -Raw
            $factMatches   = [regex]::Matches($content, '\[Fact\]')
            $theoryMatches = [regex]::Matches($content, '\[Theory\]')
            $actualTests += $factMatches.Count + $theoryMatches.Count
        }
    }
    if ($claimedTests -ne $actualTests) {
        $issues.Add("README claims $claimedTests tests but the test project has $actualTests test methods ([Fact] + [Theory])")
    }
}

# === 4. Check that every test file referenced in README exists ====================
$testFilePattern = [regex]'Tests/\w+/(\w+Tests)\.cs'
$testFileMatches = $testFilePattern.Matches($readme)
foreach ($m in $testFileMatches) {
    $fileName = "$($m.Groups[1].Value).cs"
    $found = Get-ChildItem -Path $testDir -Filter $fileName -Recurse -File -ErrorAction SilentlyContinue
    if (-not $found) {
        $issues.Add("README references test file '$fileName' but it does not exist")
    }
}

# === Decide =======================================================================
if ($issues.Count -gt 0) {
    $issueList = $issues -join '; '
    $reason = "README.md is out of sync with the codebase: $issueList. " +
              "Please update README.md to match the current state before continuing."

    $output = @{
        hookSpecificOutput = @{
            hookEventName = 'Start'
            decision      = 'inform'
            reason        = $reason
        }
    } | ConvertTo-Json -Compress

    Write-Output $output
    exit 0
}

# README is up-to-date
Write-Output '{"continue":true}'
exit 0

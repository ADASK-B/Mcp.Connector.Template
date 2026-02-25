# check-missing-tests.ps1
# Stop-Hook script: blocks the agent from finishing when Tool or Service classes
# exist without corresponding unit test files.
#
# Input (stdin):  JSON with { stop_hook_active, cwd, ... }
# Output (stdout): JSON with hookSpecificOutput for the Stop event

param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Read hook input from stdin ---------------------------------------------------
$rawInput = [Console]::In.ReadToEnd()
$hookInput = $rawInput | ConvertFrom-Json

# Prevent infinite loops: if we already blocked once, let the agent finish
if ($hookInput.stop_hook_active -eq $true) {
    Write-Output '{"continue":true}'
    exit 0
}

# --- Resolve directories ----------------------------------------------------------
$repoRoot   = $hookInput.cwd
$toolsDir   = Join-Path (Join-Path $repoRoot 'Mcp.Connector.Template') 'Tools'
$servicesDir = Join-Path (Join-Path $repoRoot 'Mcp.Connector.Template') 'Services'
$unitTestDir = Join-Path (Join-Path $repoRoot 'Mcp.Connector.Template.Tests') 'Unit'

# --- Scan for missing tests -------------------------------------------------------
$missingTests = [System.Collections.Generic.List[string]]::new()

# Tools/<Name>Tool.cs  →  Tests/Unit/<Name>ToolTests.cs
if (Test-Path $toolsDir) {
    Get-ChildItem -Path $toolsDir -Filter '*.cs' -File | ForEach-Object {
        $expectedTest = $_.BaseName + 'Tests.cs'
        if (-not (Test-Path (Join-Path $unitTestDir $expectedTest))) {
            $missingTests.Add("Tools/$($_.Name)")
        }
    }
}

# Services/<Name>Service.cs  →  Tests/Unit/<Name>ServiceTests.cs
if (Test-Path $servicesDir) {
    Get-ChildItem -Path $servicesDir -Filter '*.cs' -File | ForEach-Object {
        $expectedTest = $_.BaseName + 'Tests.cs'
        if (-not (Test-Path (Join-Path $unitTestDir $expectedTest))) {
            $missingTests.Add("Services/$($_.Name)")
        }
    }
}

# --- Decide whether to block ------------------------------------------------------
if ($missingTests.Count -gt 0) {
    $fileList = $missingTests -join ', '
    $reason   = "Unit tests are missing for: $fileList. " +
                "Please create the corresponding test files in Mcp.Connector.Template.Tests/Unit/ " +
                "following the project testing conventions (xUnit + FluentAssertions, mock all HTTP)."

    $output = @{
        hookSpecificOutput = @{
            hookEventName = 'Stop'
            decision      = 'block'
            reason        = $reason
        }
    } | ConvertTo-Json -Compress

    Write-Output $output
    exit 0
}

# Everything covered — let the agent finish
Write-Output '{"continue":true}'
exit 0

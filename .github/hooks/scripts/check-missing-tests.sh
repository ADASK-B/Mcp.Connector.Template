#!/usr/bin/env bash
# check-missing-tests.sh
# Stop-Hook script: blocks the agent from finishing when Tool or Service classes
# exist without corresponding unit test files.
#
# Input (stdin):  JSON with { stop_hook_active, cwd, ... }
# Output (stdout): JSON with hookSpecificOutput for the Stop event

set -euo pipefail

# --- Read hook input from stdin ---------------------------------------------------
INPUT=$(cat)

# Prevent infinite loops: if we already blocked once, let the agent finish
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stop_hook_active', False))" 2>/dev/null || echo "False")
if [ "$STOP_HOOK_ACTIVE" = "True" ] || [ "$STOP_HOOK_ACTIVE" = "true" ]; then
    echo '{"continue":true}'
    exit 0
fi

# --- Resolve directories ----------------------------------------------------------
REPO_ROOT=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd', '.'))" 2>/dev/null || echo ".")
TOOLS_DIR="$REPO_ROOT/Mcp.Connector.Template/Tools"
SERVICES_DIR="$REPO_ROOT/Mcp.Connector.Template/Services"
UNIT_TEST_DIR="$REPO_ROOT/Mcp.Connector.Template.Tests/Unit"

MISSING=()

# --- Scan for missing tests -------------------------------------------------------

# Tools/<Name>Tool.cs  →  Tests/Unit/<Name>ToolTests.cs
if [ -d "$TOOLS_DIR" ]; then
    for f in "$TOOLS_DIR"/*.cs; do
        [ -f "$f" ] || continue
        BASENAME=$(basename "$f" .cs)
        if [ ! -f "$UNIT_TEST_DIR/${BASENAME}Tests.cs" ]; then
            MISSING+=("Tools/$(basename "$f")")
        fi
    done
fi

# Services/<Name>Service.cs  →  Tests/Unit/<Name>ServiceTests.cs
if [ -d "$SERVICES_DIR" ]; then
    for f in "$SERVICES_DIR"/*.cs; do
        [ -f "$f" ] || continue
        BASENAME=$(basename "$f" .cs)
        if [ ! -f "$UNIT_TEST_DIR/${BASENAME}Tests.cs" ]; then
            MISSING+=("Services/$(basename "$f")")
        fi
    done
fi

# --- Decide whether to block ------------------------------------------------------
if [ ${#MISSING[@]} -gt 0 ]; then
    FILE_LIST=$(IFS=', '; echo "${MISSING[*]}")
    REASON="Unit tests are missing for: $FILE_LIST. Please create the corresponding test files in Mcp.Connector.Template.Tests/Unit/ following the project testing conventions (xUnit + FluentAssertions, mock all HTTP)."

    # Output JSON (escape quotes in reason)
    REASON_ESCAPED=$(echo "$REASON" | sed 's/"/\\"/g')
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"Stop\",\"decision\":\"block\",\"reason\":\"$REASON_ESCAPED\"}}"
    exit 0
fi

# Everything covered — let the agent finish
echo '{"continue":true}'
exit 0

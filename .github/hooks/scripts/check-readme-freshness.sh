#!/usr/bin/env bash
# check-readme-freshness.sh
# Start-Hook: checks whether README.md in the repo root is consistent with
# the actual codebase — file references, counts (tests, workflows, agents,
# prompts, skills, hooks). Reports all mismatches so the agent can fix them.
#
# Input (stdin):  JSON with { cwd, ... }
# Output (stdout): JSON with hookSpecificOutput for the Start event

set -euo pipefail

# --- Read hook input from stdin ---------------------------------------------------
RAW_INPUT=$(cat)
REPO_ROOT=$(echo "$RAW_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['cwd'])" 2>/dev/null \
         || echo "$RAW_INPUT" | jq -r '.cwd' 2>/dev/null \
         || echo ".")

PROJECT_DIR="$REPO_ROOT/Mcp.Connector.Template"
TEST_DIR="$REPO_ROOT/Mcp.Connector.Template.Tests"
README="$REPO_ROOT/README.md"

# --- Guard: README must exist -----------------------------------------------------
if [ ! -f "$README" ]; then
    echo '{"hookSpecificOutput":{"hookEventName":"Start","decision":"inform","reason":"README.md does not exist in the repo root. Please create one."}}'
    exit 0
fi

README_CONTENT=$(cat "$README")
ISSUES=()

# === 1. Check that every Tool/Service/Model file is mentioned =====================

check_files_in_readme() {
    local dir="$1"
    local label="$2"
    [ -d "$dir" ] || return 0
    for f in "$dir"/*.cs; do
        [ -f "$f" ] || continue
        local name
        name=$(basename "$f")
        if ! echo "$README_CONTENT" | grep -qF "$name"; then
            ISSUES+=("$label/$name is not mentioned in README.md")
        fi
    done
}

check_files_in_readme "$PROJECT_DIR/Tools"    "Tools"
check_files_in_readme "$PROJECT_DIR/Services" "Services"
check_files_in_readme "$PROJECT_DIR/Models"   "Models"

# === 2. Check counted items =======================================================

check_count() {
    local pattern="$1"
    local actual="$2"
    local label="$3"
    local claimed
    claimed=$(echo "$README_CONTENT" | grep -oP "$pattern" | head -1)
    if [ -n "$claimed" ]; then
        local num
        num=$(echo "$claimed" | grep -oP '\d+')
        if [ "$num" != "$actual" ]; then
            ISSUES+=("README claims $num $label but found $actual")
        fi
    fi
}

# Workflows
WORKFLOW_COUNT=0
[ -d "$REPO_ROOT/.github/workflows" ] && WORKFLOW_COUNT=$(find "$REPO_ROOT/.github/workflows" -maxdepth 1 -name '*.yml' -type f | wc -l | tr -d ' ')
check_count '\*\*[0-9]+ GitHub Actions workflows?\*\*' "$WORKFLOW_COUNT" "GitHub Actions workflows"

# Agents
AGENT_COUNT=0
[ -d "$REPO_ROOT/.github/agents" ] && AGENT_COUNT=$(find "$REPO_ROOT/.github/agents" -maxdepth 1 -name '*.agent.md' -type f | wc -l | tr -d ' ')
check_count '\*\*[0-9]+ custom Copilot agents?\*\*' "$AGENT_COUNT" "custom Copilot agents"

# Prompts
PROMPT_COUNT=0
[ -d "$REPO_ROOT/.github/prompts" ] && PROMPT_COUNT=$(find "$REPO_ROOT/.github/prompts" -maxdepth 1 -name '*.prompt.md' -type f | wc -l | tr -d ' ')
check_count '\*\*[0-9]+ prompt files?\*\*' "$PROMPT_COUNT" "prompt files"

# Skills
SKILL_COUNT=0
if [ -d "$REPO_ROOT/.github/skills" ]; then
    SKILL_COUNT=$(find "$REPO_ROOT/.github/skills" -mindepth 2 -maxdepth 2 -name 'SKILL.md' -type f | wc -l | tr -d ' ')
fi
check_count '\*\*[0-9]+ skill guides?\*\*' "$SKILL_COUNT" "skill guides"

# Hooks
HOOK_COUNT=0
[ -d "$REPO_ROOT/.github/hooks" ] && HOOK_COUNT=$(find "$REPO_ROOT/.github/hooks" -maxdepth 1 -name '*.json' -type f | wc -l | tr -d ' ')
check_count '\*\*[0-9]+ Copilot hooks?\*\*' "$HOOK_COUNT" "Copilot hooks"

# === 3. Check test count ===========================================================
CLAIMED_TESTS=$(echo "$README_CONTENT" | grep -oP '\b\d+(?=\s+tests?\b)' | head -1 || true)
if [ -n "$CLAIMED_TESTS" ] && [ -d "$TEST_DIR" ]; then
    ACTUAL_TESTS=$(grep -rh '\[Fact\]\|\[Theory\]' "$TEST_DIR" --include='*.cs' 2>/dev/null | wc -l | tr -d ' ')
    if [ "$CLAIMED_TESTS" != "$ACTUAL_TESTS" ]; then
        ISSUES+=("README claims $CLAIMED_TESTS tests but the test project has $ACTUAL_TESTS test methods ([Fact] + [Theory])")
    fi
fi

# === Decide ========================================================================
if [ ${#ISSUES[@]} -gt 0 ]; then
    JOINED=$(printf '%s; ' "${ISSUES[@]}")
    JOINED=${JOINED%; }  # trim trailing '; '
    REASON="README.md is out of sync with the codebase: $JOINED. Please update README.md to match the current state before continuing."
    # Escape for JSON
    REASON_JSON=$(echo "$REASON" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null \
                || echo "\"$REASON\"")
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"Start\",\"decision\":\"inform\",\"reason\":$REASON_JSON}}"
    exit 0
fi

echo '{"continue":true}'
exit 0

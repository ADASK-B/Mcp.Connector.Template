---
name: actions-security
description: Step-by-step workflow for hardening GitHub Actions — SHA pinning, least-privilege permissions, Dependabot, CodeQL, and dependency review. Keywords: actions, security, hardening, pin sha, permissions, supply chain, dependabot, codeql.
---

# Skill: GitHub Actions Security Hardening

This skill guides you through hardening GitHub Actions workflows for a .NET MCP Connector project.

## Prerequisites

- Workflows exist in `.github/workflows/`
- Repository uses GitHub Actions for CI/CD
- Familiarity with GitHub Actions YAML syntax

## Step-by-Step Process

### Step 1: Inventory All Workflows

List all `.yml` files in `.github/workflows/`. For each workflow, note:
- Trigger events (`on:`)
- Jobs and their purpose
- All `uses:` actions (third-party and first-party)
- Current `permissions` (or lack thereof)
- Any `run:` steps that reference `${{ secrets.* }}` or `${{ github.event.* }}`

### Step 2: Pin Actions to Full-Length Commit SHA

For every `uses:` line:

1. Identify the action and its current version tag (e.g. `actions/checkout@v4`)
2. Look up the full 40-character commit SHA for that version tag
3. Replace the version tag with the SHA
4. Add a comment with the original version tag:

```yaml
# Before:
- uses: actions/checkout@v4

# After:
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

**If the exact SHA is unknown**, add a TODO:
```yaml
- uses: some-org/some-action@v2 # TODO: pin to full SHA
```

### Step 3: Enforce Least-Privilege Permissions

Add explicit `permissions` to every workflow and job:

```yaml
# Top-level: deny all by default
permissions: {}

jobs:
  build:
    permissions:
      contents: read    # Only read source code
    runs-on: ubuntu-latest
    steps: ...
```

**Permission reference for this project:**

| Job Type | Required Permissions |
|----------|---------------------|
| Build + Test | `contents: read` |
| Docker Publish to GHCR | `contents: read`, `packages: write` |
| CodeQL Analysis | `security-events: write`, `contents: read`, `actions: read` |
| Dependency Review | `contents: read`, `pull-requests: write` |

### Step 4: Audit `run:` Steps for Injection

Check every `run:` block for:

- **Unsafe expansion**: `${{ github.event.pull_request.title }}` or any `${{ github.event.*.body }}` directly in shell — these can inject arbitrary commands
- **Secrets in output**: `echo ${{ secrets.MY_SECRET }}` — use `::add-mask::` or avoid echoing entirely
- **Unquoted variables**: Always quote shell variables in `run:` steps

**Fix pattern** — use environment variables instead of direct expansion:
```yaml
# BAD:
- run: echo "PR title is ${{ github.event.pull_request.title }}"

# GOOD:
- run: echo "PR title is $PR_TITLE"
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
```

### Step 5: Configure Dependabot

Create or verify `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "nuget"
    directory: "/Mcp.Connector.Template"
    schedule:
      interval: "weekly"
```

### Step 6: Add Dependency Review Workflow

Create `.github/workflows/dependency-review.yml` that runs on PRs and fails if vulnerable dependencies are introduced.

### Step 7: Add CodeQL Workflow

Create `.github/workflows/codeql.yml` for static analysis of C# code. Use the `csharp` language. Run on push to main and on PRs.

### Step 8: Final Verification

1. Read every workflow file and verify:
   - Top-level `permissions: {}` exists
   - Per-job permissions are minimal
   - All actions pinned to SHA (or TODO-marked)
   - No unsafe `${{ }}` expansions in `run:` blocks
2. Verify `dependabot.yml` covers both ecosystems
3. Verify `dependency-review.yml` and `codeql.yml` exist and are correctly configured

## Definition of Done

- [ ] All third-party actions pinned to full-length commit SHA (or TODO-marked)
- [ ] Every workflow has top-level `permissions: {}`
- [ ] Every job has explicit, minimal permissions
- [ ] No unsafe `${{ }}` injection patterns in `run:` blocks
- [ ] `.github/dependabot.yml` covers `github-actions` and `nuget`
- [ ] `.github/workflows/dependency-review.yml` exists and runs on PRs
- [ ] `.github/workflows/codeql.yml` exists for C# analysis
- [ ] All workflow YAML is valid (no syntax errors)

## Related Prompt Files

- `.github/prompts/harden-actions.prompt.md` — quick hardening prompt
- `.github/prompts/security-review.prompt.md` — full security review checklist

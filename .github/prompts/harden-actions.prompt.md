---
name: harden-actions
description: Harden GitHub Actions workflows — pin actions to SHA, enforce least-privilege permissions, configure Dependabot, and add dependency review
---

# Harden GitHub Actions

Review and harden all GitHub Actions workflows in `.github/workflows/` following security best practices.

## Tasks

### 1. Pin Actions to Full-Length Commit SHA

For every `uses:` step in all workflow files:
- Replace version tags (e.g. `@v4`) with the full 40-character commit SHA
- Add a comment with the original version tag for readability:
  ```yaml
  - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
  ```
- If the exact SHA is unknown, add `# TODO: pin to full SHA — currently @vX`

### 2. Enforce Least-Privilege Permissions

For every workflow file:
- Add a top-level `permissions: {}` (deny all by default) if not present
- Add per-job `permissions` with only the minimum required:
  - Build/test jobs: `contents: read`
  - Docker publish: `contents: read`, `packages: write`
  - CodeQL: `security-events: write`, `contents: read`, `actions: read`
  - Dependency review: `contents: read`, `pull-requests: write`

### 3. Verify Dependabot Configuration

Check `.github/dependabot.yml`:
- Must cover `github-actions` ecosystem (directory: `/`)
- Must cover `nuget` ecosystem (directory: project path)
- Schedule: weekly or daily
- Assign reviewers if possible

### 4. Verify Dependency Review Workflow

Check `.github/workflows/dependency-review.yml`:
- Runs on `pull_request` events
- Uses `actions/dependency-review-action` pinned to SHA
- Fails on vulnerable dependencies

### 5. Additional Checks

- No `pull_request_target` trigger with `actions/checkout` of PR head
- No `${{ github.event.*.body }}` or similar untrusted input in `run:` blocks
- Secrets only in `with:` / `env:` blocks, never in `run:` string interpolation

## Output

List all changes made with before/after for each workflow file. Confirm all workflows pass YAML validation.

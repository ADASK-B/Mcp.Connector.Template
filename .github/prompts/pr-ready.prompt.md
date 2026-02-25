---
name: pr-ready
description: Run the PR readiness checklist — verify tests pass, no secrets committed, conventional commits, and generate a changelog summary
---

# PR Readiness Checklist

Before marking this PR as ready for review, verify all items below. Fix any issues found.

## Automated Checks

Run these commands and confirm they succeed:

```bash
dotnet restore
dotnet build --configuration Release --no-restore
dotnet test --configuration Release --no-build --verbosity normal
```

## Manual Checklist

### Code Quality
- [ ] All new/modified code follows conventions in `copilot-instructions.md`
- [ ] File-scoped namespaces used (`namespace X;`)
- [ ] Nullable reference types handled (no `!` suppressions without justification)
- [ ] All code, comments, and `[Description]` attributes in English

### MCP Tools (if applicable)
- [ ] `[McpServerToolType]` on the tool class
- [ ] `[McpServerTool(Name = "camelCase")]` with `[Description]` on every tool method
- [ ] `[Description]` on every LLM-visible parameter
- [ ] Input validation at method entry (`ArgumentException`, `McpProtocolException`)
- [ ] External API calls wrapped in try/catch
- [ ] `CancellationToken` as last parameter

### Testing
- [ ] Unit tests exist for all new tool/service code
- [ ] Integration tests exist for new MCP tool endpoints
- [ ] All external HTTP calls mocked — zero real network calls
- [ ] `dotnet test` passes with zero failures

### Security
- [ ] No hardcoded secrets, API keys, or tokens
- [ ] No `TODO: REPLACE_ME` placeholders left unresolved
- [ ] Dependencies from trusted NuGet feeds only

### Commit & PR
- [ ] Conventional commit messages (e.g. `feat:`, `fix:`, `test:`, `docs:`)
- [ ] PR title summarizes the change
- [ ] PR description includes: what changed, why, how to verify

## Changelog Summary

Generate a concise changelog entry for this PR:

```
## [Type] Short Description

- What was added/changed/fixed
- Any breaking changes or migration steps
- Related issue numbers (if any)
```

## Description

<!-- What changed and why? Link any related issues. -->

Closes #<!-- issue number -->

## Changes

- <!-- List the main changes -->

## How to Verify

1. <!-- Step-by-step instructions to test the change -->
2. `dotnet build --configuration Release`
3. `dotnet test --configuration Release --verbosity normal`

## Checklist

### Code Quality
- [ ] Code follows conventions in `copilot-instructions.md`
- [ ] All code, comments, and descriptions in English
- [ ] Conventional commit messages used (e.g. `feat:`, `fix:`, `test:`)

### MCP Tools (if applicable)
- [ ] `[Description]` on every tool method and LLM-visible parameter
- [ ] Input validation at method entry (`ArgumentException`, `McpException`)
- [ ] External API calls wrapped in try/catch
- [ ] `CancellationToken` as last parameter on all async methods

### Testing
- [ ] Unit tests added/updated for all new/modified code
- [ ] Integration tests added/updated for new MCP tool endpoints
- [ ] All external HTTP calls mocked — zero real network calls
- [ ] `dotnet test` passes with zero failures

### Security
- [ ] No hardcoded secrets, API keys, or tokens committed
- [ ] No `TODO: REPLACE_ME` placeholders left unresolved
- [ ] Dependencies from trusted NuGet feeds only

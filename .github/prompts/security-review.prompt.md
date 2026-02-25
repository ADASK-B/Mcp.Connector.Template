---
name: security-review
description: Perform a lightweight threat model and security review of the MCP Connector project — secrets, input validation, dependencies, container, and Actions
---

# Security Review

Perform a focused security review of this MCP Connector project. Check each area below and report findings with severity (Critical / High / Medium / Low / Info).

## Review Areas

### 1. Secrets & Credentials

- [ ] No hardcoded API keys, tokens, passwords, or connection strings in source code
- [ ] No secrets in `appsettings.json` or `appsettings.Development.json`
- [ ] No secrets baked into Docker images
- [ ] Environment variables or secrets manager used for sensitive values
- [ ] No secrets printed in log output (`ILogger` calls)

### 2. Input Validation (MCP Tools)

- [ ] All tool parameters validated at method entry
- [ ] `ArgumentException.ThrowIfNullOrWhiteSpace()` for required strings
- [ ] `McpException` for constraint violations (e.g. input too long)
- [ ] No user input passed to `Process.Start()`, file system paths, or SQL
- [ ] Max length / allowed character checks where appropriate

### 3. External API Safety

- [ ] All `HttpClient` instances via `IHttpClientFactory` (no `new HttpClient()`)
- [ ] Timeouts configured on HTTP clients
- [ ] External API errors caught in try/catch — no raw exceptions to MCP clients
- [ ] No sensitive data in request/response logging

### 4. Dependency Supply Chain

- [ ] `dependabot.yml` covers `nuget` and `github-actions` ecosystems
- [ ] No packages from untrusted NuGet feeds
- [ ] `dependency-review.yml` workflow runs on PRs
- [ ] Run `dotnet list package --vulnerable --include-transitive` and report findings

### 5. Container Security

- [ ] Dockerfile uses `USER $APP_UID` (non-root)
- [ ] Multi-stage build — SDK not in final image
- [ ] No `COPY` of secret files into image
- [ ] `EXPOSE 8080` only (no HTTPS — TLS terminated at ingress)

### 6. GitHub Actions Hardening

- [ ] All workflows declare explicit `permissions` (least privilege)
- [ ] Third-party actions pinned to full-length commit SHA
- [ ] No `${{ secrets.* }}` in `run:` string interpolation without masking
- [ ] No `pull_request_target` with checkout of PR head (untrusted code)

## Output Format

For each finding:
```
[SEVERITY] Area — Description
  File: path/to/file (line X)
  Recommendation: what to do
```

End with a summary table: counts per severity level.

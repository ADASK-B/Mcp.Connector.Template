# Security Policy

## Supported Versions

Only the latest release on the `main` branch receives security patches.
When you create a connector from this template, you are responsible for keeping
your own repository's dependencies up to date.

| Version | Supported |
|---------|-----------|
| `main` (latest) | ✅ |
| Older branches | ❌ |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities in public GitHub issues.**

To report a vulnerability, use one of the following channels:

1. **GitHub Private Security Advisories** (preferred):
   Go to the repository → **Security** tab → **Report a vulnerability**.
   This creates a private draft advisory visible only to maintainers.

2. **Email** (fallback):
   Send details to the maintainer address listed in the repository's GitHub profile.
   Encrypt sensitive information with the maintainer's public GPG key if available.

### What to include

- A clear description of the vulnerability
- Steps to reproduce (proof-of-concept code or curl commands are helpful)
- The potential impact (data exposure, privilege escalation, denial of service, etc.)
- Your suggested fix, if any

### Response timeline

| Stage | Target |
|-------|--------|
| Acknowledgement | Within 3 business days |
| Initial assessment | Within 7 business days |
| Fix or mitigation published | Within 30 days for critical/high severity |

---

## Security Best Practices for Connector Developers

When implementing a connector based on this template:

### Input Validation
- Validate all tool arguments immediately using `ArgumentException.ThrowIfNullOrWhiteSpace()`
- Enforce length and format constraints; throw `McpProtocolException` with `McpErrorCode.InvalidParams`
- Never pass raw user input directly to shell commands, SQL queries, or file paths

### Secrets and Credentials
- Store API keys and tokens in environment variables or a secrets manager — **never in source code**
- Use `IConfiguration` to read secrets: `builder.Configuration["ApiKey"]`
- Register sensitive configuration via GitHub Actions secrets or Azure Key Vault
- Never log raw credential values; use structured logging with masked placeholders

### HTTP Client Security
- Always use `IHttpClientFactory` (`builder.Services.AddHttpClient<T>()`) — never `new HttpClient()`
- Set a sensible `Timeout` on the `HttpClient` to prevent long-hanging requests
- Validate TLS certificates in production; do not disable certificate validation

### Container Security
- The Dockerfile runs the application as a non-root user (`USER $APP_UID`) — do not change this
- Keep base images updated; Dependabot is configured to open PRs for new `.NET` base image digests
- Do not embed secrets in the Docker image; pass them at runtime via environment variables

### Dependency Management
- Review Dependabot pull requests promptly, especially for security patches
- Pin GitHub Actions to a specific commit SHA (e.g. `actions/checkout@<sha>`) for supply-chain safety
- Run `dotnet list package --vulnerable` locally to detect known NuGet vulnerabilities

---

## Scope

This security policy covers the **template repository itself**.
If you are operating a connector built from this template, you are responsible for
the security posture of your own deployment, including secrets management,
network exposure, authentication in front of the `/mcp` endpoint, and rate limiting.

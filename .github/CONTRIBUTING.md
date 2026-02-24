# Contributing to Mcp.Connector.Template

Thank you for your interest in contributing!
This document explains how to get started, what we expect from contributors, and how the review process works.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Code of Conduct

Be respectful and constructive in all interactions.
Harassment, discrimination, or abusive behaviour will not be tolerated.

---

## Getting Started

### Prerequisites

- [.NET 10 SDK](https://dotnet.microsoft.com/download)
- [Docker](https://www.docker.com/) (optional, for container testing)
- [Git](https://git-scm.com/)

### Fork and clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/<your-username>/Mcp.Connector.Template.git
cd Mcp.Connector.Template
```

### Build and test

```bash
dotnet restore
dotnet build
dotnet test
```

All tests must pass before submitting a pull request.

---

## Development Workflow

1. **Open or find an issue** — check existing issues before starting work
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature   # new feature
   git checkout -b fix/bug-description  # bug fix
   ```
3. **Make your changes** — follow the [coding standards](#coding-standards) below
4. **Write or update tests** — all changes must be covered by tests
5. **Run the full test suite**: `dotnet test`
6. **Open a pull request** against `main`

### Branch naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<short-description>` | `feat/add-weather-tool` |
| Bug fix | `fix/<short-description>` | `fix/null-handling-in-echo` |
| Documentation | `docs/<short-description>` | `docs/update-readme` |
| Refactor | `refactor/<short-description>` | `refactor/simplify-service` |

---

## Coding Standards

Follow the rules in [`.github/instructions/csharp-mcp.instructions.md`](instructions/csharp-mcp.instructions.md).

Key points:

- **English only** — all code, comments, `[Description]` attributes, and commit messages must be in English
- **C# 13, .NET 10** — file-scoped namespaces, nullable reference types enabled
- **Tool classes** — `static` classes decorated with `[McpServerToolType]`; methods are `public static` with `[McpServerTool]` and `[Description]`
- **Services** — one `HttpClient`-based class per external API, registered via `AddHttpClient<T>()`
- **Models** — `record` types with `[JsonPropertyName]` attributes, placed in `Models/`
- **No `new HttpClient()`** — always use `IHttpClientFactory`
- **Async I/O** — all I/O methods return `Task<T>`, always forward `CancellationToken`
- **Logging** — use `ILogger<T>`, structured logging, no `Console.WriteLine`
- **Validation** — validate inputs early, throw `McpProtocolException` with `McpErrorCode.InvalidParams`

### Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add getWeather tool wrapping OpenWeatherMap API
fix: handle null response from upstream API
docs: update README with Docker run instructions
refactor: extract HTTP error handling to base service
test: add integration test for tools/list endpoint
```

---

## Testing Requirements

Every pull request must include adequate test coverage:

| Change type | Required tests |
|-------------|----------------|
| New tool | Unit tests (validation, mapping, error cases) + integration test |
| New service | Unit tests with mocked `HttpMessageHandler` |
| Bug fix | Regression test that would have caught the bug |
| Refactor | Existing tests must continue to pass |

### Running tests

```bash
# Run all tests
dotnet test

# Run with coverage
dotnet test --collect:"XPlat Code Coverage"
```

### Test structure

```
Tests/
├── Unit/           # Test tool methods and service logic in isolation
├── Integration/    # Test /health and /mcp endpoints end-to-end
└── TestInfrastructure/
    └── CustomWebApplicationFactory.cs   # In-memory host for integration tests
```

- **Mock all external HTTP calls** — no real network calls in tests
- **Use FluentAssertions** — `result.Should().Be(expected)`
- **Follow the Arrange / Act / Assert pattern**

---

## Pull Request Process

1. Fill in the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) completely
2. Ensure all CI checks pass (build, tests, Docker build)
3. Request a review from a maintainer
4. Address review comments promptly
5. A maintainer will merge once the PR is approved and all checks are green

### What we look for in reviews

- Correctness and completeness
- Test coverage for new and changed code
- Adherence to architecture and coding conventions
- Security implications (secrets handling, input validation, dependency versions)
- Documentation updated where necessary

---

## Reporting Bugs

Open a [bug report](.github/ISSUE_TEMPLATE/bug_report.yml) on GitHub.

Please include:
- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behaviour
- .NET version (`dotnet --version`) and OS

For **security vulnerabilities**, see [SECURITY.md](../SECURITY.md) — do not open a public issue.

---

## Suggesting Features

Open a [feature request](.github/ISSUE_TEMPLATE/feature_request.yml) on GitHub.

Describe:
- The problem you are trying to solve
- Your proposed solution
- Any alternatives you considered

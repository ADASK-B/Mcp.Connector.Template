# Mcp.Connector.Template

[![.NET](https://img.shields.io/badge/.NET-10.0-512bd4)](https://dotnet.microsoft.com/)
[![MCP SDK](https://img.shields.io/badge/MCP_SDK-0.x-blue)](https://github.com/modelcontextprotocol/csharp-sdk)
[![Build and Test](https://github.com/ADASK-B/Mcp.Connector.Template/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/ADASK-B/Mcp.Connector.Template/actions/workflows/build-and-test.yml)
[![CodeQL](https://github.com/ADASK-B/Mcp.Connector.Template/actions/workflows/codeql.yml/badge.svg)](https://github.com/ADASK-B/Mcp.Connector.Template/actions/workflows/codeql.yml)
[![Docker](https://img.shields.io/badge/Docker-GHCR-2496ed?logo=docker&logoColor=white)](https://github.com/ADASK-B/Mcp.Connector.Template/pkgs/container/mcp.connector.template)
[![License](https://img.shields.io/badge/license-proprietary-lightgrey)](LICENSE)

> **Enterprise template repository** for building [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) connector services in C#.  
> Clone this template, add your tools — get a production-ready, container-first MCP server with CI/CD, security scanning, and AI-assisted development out of the box.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Run Locally](#run-locally)
  - [Run in Docker](#run-in-docker)
- [Adding a New MCP Tool](#adding-a-new-mcp-tool)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
  - [Build and Test](#build-and-test)
  - [Docker Publish to GHCR](#docker-publish-to-ghcr)
  - [CodeQL Analysis](#codeql-analysis)
  - [Dependency Review](#dependency-review)
  - [Dependabot](#dependabot)
- [GitHub Copilot Integration](#github-copilot-integration)
  - [Custom Agents](#custom-agents)
  - [Prompt Files](#prompt-files)
  - [Skills](#skills)
  - [Hooks](#hooks)
  - [Instruction Files](#instruction-files)
- [Governance & Templates](#governance--templates)
- [Container Configuration](#container-configuration)
- [Security](#security)
- [MCP Protocol Reference](#mcp-protocol-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This template provides the complete scaffolding for an MCP connector service:

- **ASP.NET Core Minimal API** exposing MCP tools over Streamable HTTP transport
- **Multi-stage Docker image** optimized for production (non-root, port 8080)
- **4 GitHub Actions workflows** for CI, security scanning, and container publishing
- **5 custom Copilot agents** with orchestrator pattern for AI-assisted development
- **6 prompt files** for common development workflows
- **3 skill guides** with step-by-step instructions for tools, TDD, and security hardening
- **2 Copilot hooks** for automatic build verification and test coverage enforcement
- **Dependabot** for automated dependency updates (NuGet + GitHub Actions)
- **CodeQL** for static application security testing (SAST)
- **Pull request template**, issue templates, and CODEOWNERS for governance

New connectors are created by using this repo as a GitHub template and adding tool/service/model classes. The hosting framework, CI/CD, and Copilot configuration stay untouched.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Runtime | .NET 10 (LTS), C# 13 |
| Framework | ASP.NET Core Minimal API — no controllers |
| MCP SDK | [`ModelContextProtocol.AspNetCore`](https://github.com/modelcontextprotocol/csharp-sdk) (Streamable HTTP) |
| Container | Docker multi-stage, Linux, port 8080 |
| Testing | xUnit, FluentAssertions, `Microsoft.AspNetCore.Mvc.Testing` |
| CI/CD | GitHub Actions → GHCR |
| SAST | GitHub CodeQL (C#) |
| Dependency Management | Dependabot (NuGet + GitHub Actions) |
| AI Assistance | GitHub Copilot (agents, prompts, skills, hooks) |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                 MCP Client                  │
│  (Claude Desktop, VS Code Copilot, OpenAI)  │
└──────────────────┬──────────────────────────┘
                   │ Streamable HTTP (JSON-RPC)
                   ▼
┌─────────────────────────────────────────────┐
│             ASP.NET Core Host               │
│                                             │
│  GET  /health    → Health probe (200 OK)    │
│  POST /mcp       → MCP JSON-RPC endpoint   │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │         MCP SDK Middleware            │  │
│  │  initialize → tools/list → tools/call │  │
│  └──────────────┬────────────────────────┘  │
│                 │                            │
│  ┌──────────────▼────────────────────────┐  │
│  │     Tool Classes ([McpServerToolType]) │  │
│  │     Auto-discovered via assembly scan │  │
│  └──────────────┬────────────────────────┘  │
│                 │ DI (method injection)      │
│  ┌──────────────▼────────────────────────┐  │
│  │     Service Classes (HttpClient)      │  │
│  │     External API communication        │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Key Design Decisions

- **Tools are static classes** with `[McpServerToolType]` — the SDK discovers them automatically via `WithToolsFromAssembly()`
- **Method-level DI** — dependencies are injected as tool method parameters, not via constructors
- **No routing changes needed** — adding a new `[McpServerToolType]` class is enough; the SDK handles `tools/list` and `tools/call`
- **No OpenAPI** — tool discovery happens through the MCP protocol itself
- **No HTTPS** — TLS termination is handled at the PaaS/ingress level; the container listens on plain HTTP

---

## Project Structure

```
Mcp.Connector.Template/
├── README.md                              # ← You are here
├── Mcp.Connector.Template.slnx           # Solution file
│
├── Mcp.Connector.Template/               # Main application project
│   ├── Program.cs                        # Host, DI, endpoints (MapMcp + /health)
│   ├── Tools/                            # MCP tool classes ([McpServerToolType])
│   │   └── <ToolName>Tool.cs
│   ├── Services/                         # External API client wrappers
│   │   └── <ApiName>Service.cs
│   ├── Models/                           # DTOs (record types)
│   │   └── <Domain>Models.cs
│   ├── Dockerfile                        # Multi-stage container build
│   ├── appsettings.json                  # Configuration
│   └── Properties/
│       └── launchSettings.json           # Local dev (port 5076) + Docker profile
│
├── Mcp.Connector.Template.Tests/         # Test project
│   ├── Unit/                             # Tool logic, validation, DTO mapping
│   │   ├── <ToolName>ToolTests.cs
│   │   └── <ApiName>ServiceTests.cs
│   ├── Integration/                      # WebApplicationFactory-based tests
│   │   ├── HealthEndpointTests.cs
│   │   └── McpEndpointTests.cs
│   └── TestInfrastructure/               # Shared test setup
│       ├── CustomWebApplicationFactory.cs
│       └── Fake<ApiName>Handler.cs
│
└── .github/                              # GitHub configuration (see below)
    ├── copilot-instructions.md
    ├── dependabot.yml
    ├── CODEOWNERS
    ├── pull_request_template.md
    ├── ISSUE_TEMPLATE/
    ├── workflows/
    ├── agents/
    ├── prompts/
    ├── skills/
    ├── hooks/
    └── instructions/
```

---

## Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| [.NET SDK](https://dotnet.microsoft.com/download) | 10.0+ |
| [Docker](https://www.docker.com/get-started) | 20.10+ (optional, for container builds) |
| [VS Code](https://code.visualstudio.com/) | Latest, with GitHub Copilot extension |

### Run Locally

```bash
# Clone from template
gh repo create my-connector --template ADASK-B/Mcp.Connector.Template --clone

# Restore, build, test
cd my-connector
dotnet restore
dotnet build --configuration Release --no-restore
dotnet test --configuration Release --no-build --verbosity normal

# Run the MCP server
cd Mcp.Connector.Template
dotnet run
```

The server starts at `http://localhost:5076`. The MCP endpoint is at `/mcp` and the health probe at `/health`.

### Run in Docker

```bash
# Build the image
docker build -f Mcp.Connector.Template/Dockerfile -t mcp-connector .

# Run the container
docker run -p 8080:8080 mcp-connector
```

The containerized server listens on `http://localhost:8080`.

### Connect an MCP Client

Point any MCP-compatible client to the server URL:

| Client | Configuration |
|--------|--------------|
| **VS Code Copilot** | Add server URL in MCP settings |
| **Claude Desktop** | Add to `claude_desktop_config.json` |
| **OpenAI Responses API** | Use as remote MCP server URL |

---

## Adding a New MCP Tool

> **AI-Assisted:** Use the `@mcp-tool-creator` agent in VS Code Copilot Chat or the `/add-mcp-tool` prompt file to scaffold a complete tool automatically.

### Manual Steps

1. **Create the Tool class** in `Tools/<Name>Tool.cs`:

   ```csharp
   [McpServerToolType]
   public static class WeatherTool
   {
       [McpServerTool(Name = "getWeather"), Description("Get current weather for a city")]
       public static async Task<string> GetWeather(
           WeatherService weatherService,
           [Description("City name, e.g. 'Berlin'")] string city,
           CancellationToken cancellationToken)
       {
           ArgumentException.ThrowIfNullOrWhiteSpace(city);
           var result = await weatherService.GetCurrentAsync(city, cancellationToken);
           return JsonSerializer.Serialize(result);
       }
   }
   ```

2. **Create the Service** in `Services/<ApiName>Service.cs` (if calling an external API)

3. **Create Models** in `Models/<Domain>Models.cs` (record types for DTOs)

4. **Register DI** in `Program.cs`: `builder.Services.AddHttpClient<WeatherService>();`

5. **Add unit tests** in `Tests/Unit/<Name>ToolTests.cs`

6. **Add integration tests** in `Tests/Integration/`

7. **Done** — `WithToolsFromAssembly()` auto-discovers the new tool. No routing changes.

---

## Testing

### Framework

| Component | Package |
|-----------|---------|
| Test Framework | xUnit 2.9+ |
| Assertions | FluentAssertions (`Should().Be...()` style) |
| Integration Host | `Microsoft.AspNetCore.Mvc.Testing` (WebApplicationFactory) |
| Coverage | Coverlet |

### Conventions

- **Unit tests** cover tool logic, input validation, and DTO mapping in isolation
- **Integration tests** spin up an in-memory host via `WebApplicationFactory<Program>`
- **All external APIs are mocked** — zero real network calls in the test suite
- **TDD preferred** — Red → Green → Refactor

### Run Tests

```bash
# All tests
dotnet test --configuration Release --verbosity normal

# Specific test file
dotnet test --filter "FullyQualifiedName~WeatherToolTests"

# With coverage
dotnet test --collect:"XPlat Code Coverage"
```

---

## CI/CD Pipeline

This template ships with **4 GitHub Actions workflows**, all following security best practices (SHA-pinned actions, least-privilege permissions, `permissions: {}` at top level).

### Build and Test

**File:** `.github/workflows/build-and-test.yml`  
**Triggers:** Push to `main`, Pull Request to `main`

Runs `dotnet restore` → `dotnet build` → `dotnet test`. This is the primary CI gate — must pass before any PR can be merged.

| Step | Command |
|------|---------|
| Restore | `dotnet restore` |
| Build | `dotnet build --no-restore --configuration Release` |
| Test | `dotnet test --no-build --configuration Release --verbosity normal` |

### Docker Publish to GHCR

**File:** `.github/workflows/docker-publish.yml`  
**Triggers:** Push to `main`, Manual dispatch

Builds the multi-stage Docker image and pushes it to GitHub Container Registry (`ghcr.io`). Images are tagged with `latest` and the Git SHA.

| Step | Action |
|------|--------|
| Login | `docker/login-action` → GHCR with `GITHUB_TOKEN` |
| Metadata | `docker/metadata-action` → tags + OCI labels |
| Build & Push | `docker/build-push-action` → multi-stage Dockerfile |

### CodeQL Analysis

**File:** `.github/workflows/codeql.yml`  
**Triggers:** Push to `main`, Pull Request to `main`, Weekly (Monday 03:27 UTC)

GitHub's static application security testing (SAST). Scans C# code for vulnerabilities like SQL injection, XSS, path traversal, and more. Results appear under **Security → Code scanning alerts**.

### Dependency Review

**File:** `.github/workflows/dependency-review.yml`  
**Triggers:** Pull Request to `main`

Checks every PR for newly introduced dependencies with known vulnerabilities. Blocks the PR if any dependency has a security advisory with severity ≥ `moderate`. Posts a summary comment directly in the PR.

### Dependabot

**File:** `.github/dependabot.yml`  
**Schedule:** Weekly (Monday)

Automatically creates PRs for outdated dependencies:

| Ecosystem | Directory | Prefix | Labels |
|-----------|-----------|--------|--------|
| GitHub Actions | `/` | `ci:` | `dependencies`, `github-actions` |
| NuGet | `/Mcp.Connector.Template` | `deps:` | `dependencies`, `nuget` |

---

## GitHub Copilot Integration

This template includes a comprehensive Copilot configuration that turns VS Code into an AI-powered development environment tailored to this project.

### Custom Agents

Five specialist agents follow an **orchestrator pattern** — use the orchestrator for cross-domain tasks, or call specialists directly for single-domain work.

| Agent | File | Purpose |
|-------|------|---------|
| **orchestrator** | `.github/agents/orchestrator.agent.md` | Plans, delegates, and reviews. Never edits code directly — always delegates to specialist agents. Use for tasks spanning 2+ domains. |
| **mcp-tool-creator** | `.github/agents/mcp-tool-creator.agent.md` | Scaffolds complete MCP tools: Tool class, Service, Models, DI registration, and test stubs. |
| **test** | `.github/agents/test.agent.md` | TDD specialist — writes, fixes, and improves unit and integration tests. |
| **security** | `.github/agents/security.agent.md` | Hardens GitHub Actions workflows, audits dependencies, checks for secrets exposure. |
| **docs** | `.github/agents/docs.agent.md` | Creates and maintains PR/issue templates, developer documentation, and governance files. |

**Usage in VS Code:**
```
@orchestrator Add a new tool that calls the Jira API to list issues
@mcp-tool-creator Create a tool that queries weather data from OpenWeatherMap
@test Write tests for the WeatherTool class
@security Review the CI workflows for supply chain risks
```

### Prompt Files

Reusable prompt templates for common development tasks. Access them in VS Code Copilot Chat.

| Prompt | File | Description |
|--------|------|-------------|
| **Add MCP Tool** | `.github/prompts/add-mcp-tool.prompt.md` | Full scaffolding for a new MCP tool (Tool + Service + Models + DI + Tests) |
| **TDD Feature** | `.github/prompts/tdd-feature.prompt.md` | Red → Green → Refactor workflow for a new feature |
| **Write Tests** | `.github/prompts/write-tests.prompt.md` | Generate tests for the currently open file |
| **Security Review** | `.github/prompts/security-review.prompt.md` | Lightweight threat model for code changes |
| **Harden Actions** | `.github/prompts/harden-actions.prompt.md` | SHA pinning, least-privilege permissions audit |
| **PR Ready** | `.github/prompts/pr-ready.prompt.md` | Pre-merge readiness checklist |

### Skills

Detailed step-by-step guides that agents and prompts reference for domain-specific tasks.

| Skill | Directory | Steps | Description |
|-------|-----------|-------|-------------|
| **MCP Tool Creation** | `.github/skills/mcp-tool-creation/` | 7 | Complete guide for adding a new MCP tool to the project |
| **TDD for MCP** | `.github/skills/tdd-mcp/` | Multi-phase | Red/Green/Refactor workflow tailored to MCP tools |
| **Actions Security** | `.github/skills/actions-security/` | 8 | Hardening GitHub Actions — SHA pinning, permissions, CodeQL, Dependabot |

### Hooks

VS Code Copilot hooks that run automatically during agent interactions to enforce quality standards.

| Hook | File | Trigger | Purpose |
|------|------|---------|---------|
| **Build Check** | `.github/hooks/build-check.json` | Agent Stop | Runs `dotnet build` after code generation to catch compile errors immediately |
| **Test Nudge** | `.github/hooks/test-nudge.json` | Agent Stop | Scans for Tool/Service classes without corresponding unit test files. Blocks the agent and requests test creation if coverage gaps are found. |

The Test Nudge hook uses OS-specific scripts:
- **Windows:** `.github/hooks/scripts/check-missing-tests.ps1` (PowerShell 5.1 compatible)
- **Linux/macOS:** `.github/hooks/scripts/check-missing-tests.sh` (Bash)

### Instruction Files

Always-on context files that Copilot reads automatically:

| File | Scope | Purpose |
|------|-------|---------|
| `.github/copilot-instructions.md` | All files | Project overview, architecture rules, coding conventions, security rules, testing standards |
| `.github/instructions/csharp-mcp.instructions.md` | `**/*.cs` | C#-specific coding guidelines for MCP development |

---

## Governance & Templates

### CODEOWNERS

**File:** `.github/CODEOWNERS`

Automatically assigns reviewers based on file paths. The `@ADASK-B/platform` team is configured as the default owner for all files, with specific entries for:

- `.github/` — CI/CD and configuration
- `Tools/`, `Services/`, `Models/` — Application code
- `Tests/` — Test code
- `Dockerfile` — Container configuration

### Pull Request Template

**File:** `.github/pull_request_template.md`

Every PR is pre-populated with a structured checklist covering:

- **Code Quality** — Conventions, English-only, conventional commits
- **MCP Tools** — Descriptions, validation, error handling, CancellationToken
- **Testing** — Unit tests, integration tests, mocked HTTP, green test suite
- **Security** — No secrets, no TODO placeholders, trusted dependencies

### Issue Templates

| Template | File | Labels |
|----------|------|--------|
| Bug Report | `.github/ISSUE_TEMPLATE/bug_report.md` | `bug` |
| Feature Request | `.github/ISSUE_TEMPLATE/feature_request.md` | `enhancement` |

---

## Container Configuration

| Setting | Value |
|---------|-------|
| Base Image | `mcr.microsoft.com/dotnet/aspnet:10.0` |
| Build Image | `mcr.microsoft.com/dotnet/sdk:10.0` |
| Port | 8080 |
| User | Non-root (`USER $APP_UID`) |
| Build | Multi-stage (SDK excluded from final image) |
| State | Stateless — no volumes, no persistent storage |

The Dockerfile uses a multi-stage build:

1. **base** — ASP.NET runtime, non-root user, port 8080
2. **build** — SDK image, restores and compiles the project
3. **publish** — Publishes the project for release
4. **final** — Copies published output into the base image

---

## Security

This template enforces security at multiple levels:

### Code Level
- **Input validation** on all MCP tool parameters before use
- **No secrets in code** — use environment variables or secrets managers
- **Structured logging** — never log tokens, passwords, or sensitive request bodies
- **Error handling** — wrap external API calls, never leak raw exceptions to MCP clients

### Container Level
- **Non-root execution** (`USER $APP_UID`)
- **Multi-stage builds** — SDK and build tools excluded from the final image
- **No secrets in images** — environment variables only
- **Plain HTTP** — TLS terminated at PaaS/ingress, not in the container

### CI/CD Level
- **SHA-pinned actions** — all GitHub Actions use full commit SHAs, not mutable tags
- **Least-privilege permissions** — `permissions: {}` at workflow level, scoped per job
- **CodeQL SAST** — weekly and on every PR
- **Dependency Review** — blocks PRs with vulnerable dependencies (severity ≥ moderate)
- **Dependabot** — weekly automated dependency updates for NuGet and Actions

### Supply Chain
- **Dependabot** monitors NuGet packages and GitHub Actions for vulnerabilities
- **Dependency Review** prevents introducing known-vulnerable dependencies
- **CODEOWNERS** requires team review for all changes

---

## MCP Protocol Reference

| Concept | Details |
|---------|---------|
| **Endpoint** | `POST /mcp` — JSON-RPC over Streamable HTTP |
| **Transport** | Streamable HTTP (`WithHttpTransport` + `MapMcp`) |
| **Tool Discovery** | `WithToolsFromAssembly()` scans for `[McpServerToolType]` classes |
| **Tool Invocation** | `[McpServerTool]` methods are called by the SDK on `tools/call` |
| **Parameter Schema** | Auto-generated from `[Description]` attributes |
| **Health Probe** | `GET /health` — custom endpoint for container orchestration (not part of MCP spec) |
| **Compatible Clients** | OpenAI Responses API, Claude Desktop, VS Code Copilot, and any MCP client |

### Resources

| Resource | URL |
|----------|-----|
| MCP C# SDK | https://github.com/modelcontextprotocol/csharp-sdk |
| MCP Specification | https://modelcontextprotocol.io/specification |
| ASP.NET Core Transport | https://github.com/modelcontextprotocol/csharp-sdk/blob/main/src/ModelContextProtocol.AspNetCore/README.md |
| SDK Samples | https://github.com/modelcontextprotocol/csharp-sdk/tree/main/samples |
| OpenAI MCP Guide | https://platform.openai.com/docs/guides/tools-remote-mcp |

---

## Contributing

### Quick Start

1. Create a feature branch from `main`
2. Make changes following the conventions in `.github/copilot-instructions.md`
3. Write/update tests (TDD preferred)
4. Verify locally:
   ```bash
   dotnet restore
   dotnet build --configuration Release --no-restore
   dotnet test --configuration Release --no-build --verbosity normal
   ```
5. Push and open a PR — the PR template checklist will guide you through the review

### Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add getWeather tool
fix: handle null response from weather API
test: add unit tests for input validation
ci: pin actions/checkout to SHA
docs: update README with new tool guide
```

### PR Guidelines

- **Small, focused PRs** — one tool, one bug fix, or one refactoring per PR
- **Clear descriptions** — what changed, why, and how to verify
- **Example tool calls** — include request/response examples for new MCP tools
- **All checks must pass** — Build, CodeQL, Dependency Review

---

## License

This project is proprietary to [ADASK-B](https://github.com/ADASK-B). All rights reserved.

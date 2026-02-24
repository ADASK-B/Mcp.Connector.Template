# Mcp.Connector.Template

A **production-ready template** for building [Model Context Protocol (MCP)](https://modelcontextprotocol.io) connector services in C#.
Clone this repository to create a containerised ASP.NET Core service that wraps any HTTP API and exposes its capabilities as MCP tools — instantly compatible with OpenAI Responses API, Claude Desktop, VS Code Copilot, and any other MCP client.

---

## What is an MCP Connector?

An MCP connector is a lightweight HTTP service that sits **between an AI model and an external API**.
The model calls the connector's tools (e.g. `getWeather`, `searchProducts`), and the connector translates those calls into real API requests — handling authentication, validation, error mapping, and response serialisation.

```
AI Model / LLM Client
        │
        │  MCP JSON-RPC (tools/call)
        ▼
┌─────────────────────┐
│  MCP Connector      │  ← this template
│  (ASP.NET Core)     │
│  /mcp  /health      │
└─────────────────────┘
        │
        │  HTTP
        ▼
  External API (REST, GraphQL, …)
```

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Runtime | .NET 10, C# 13 |
| Framework | ASP.NET Core Minimal API |
| MCP SDK | [`ModelContextProtocol.AspNetCore`](https://github.com/modelcontextprotocol/csharp-sdk) |
| Transport | Streamable HTTP (`/mcp`) |
| Container | Linux Docker image, port 8080 |
| Testing | xUnit · FluentAssertions · WebApplicationFactory |
| CI/CD | GitHub Actions → GHCR |

---

## Quick Start

### 1. Use this template

Click **"Use this template"** on GitHub, or:

```bash
gh repo create my-connector --template ADASK-B/Mcp.Connector.Template
cd my-connector
```

### 2. Run locally

```bash
dotnet run --project Mcp.Connector.Template
```

The server starts on `http://localhost:5076`.
Test it:

```bash
# Health check
curl http://localhost:5076/health

# List available MCP tools
curl -X POST http://localhost:5076/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

### 3. Run with Docker

```bash
docker build -t my-connector -f Mcp.Connector.Template/Dockerfile .
docker run -p 8080:8080 my-connector
```

### 4. Run tests

```bash
dotnet test
```

---

## Project Structure

```
Mcp.Connector.Template/
├── Program.cs                  # Host, DI, /health + /mcp endpoints
├── Tools/
│   └── EchoTool.cs             # Example tool — replace with your own
├── Services/                   # HttpClient-based external API clients
├── Models/                     # Request/response DTOs (record types)
├── appsettings.json
└── Dockerfile

Mcp.Connector.Template.Tests/
├── Unit/                       # Tool logic and validation tests
├── Integration/                # /health and /mcp protocol tests
└── TestInfrastructure/
    └── CustomWebApplicationFactory.cs
```

---

## Adding a New Tool

1. **Create `Models/<Domain>Models.cs`** — DTOs for the external API and your tool result
2. **Create `Services/<ApiName>Service.cs`** — `HttpClient` wrapper registered via `AddHttpClient<T>()`
3. **Create `Tools/<ToolName>Tool.cs`** — static class with `[McpServerToolType]` and `[McpServerTool]` methods
4. **Register the service in `Program.cs`**: `builder.Services.AddHttpClient<MyService>()`
5. **Add tests** in `Tests/Unit/` and `Tests/Integration/`

`WithToolsFromAssembly()` auto-discovers the new tool — no routing changes needed.

See [`.github/skills/mcp-tool-creation/SKILL.md`](.github/skills/mcp-tool-creation/SKILL.md) for a detailed step-by-step guide,
or use the [`.github/prompts/new-mcp-tool.prompt.md`](.github/prompts/new-mcp-tool.prompt.md) prompt with GitHub Copilot.

---

## Architecture

### Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/health` | GET | Container health probe — returns `{"status":"healthy"}` |
| `/mcp` | POST | MCP JSON-RPC endpoint — handles `initialize`, `tools/list`, `tools/call` |

### MCP Protocol Flow

```
Client → POST /mcp  initialize       → Server returns Mcp-Session-Id header
Client → POST /mcp  tools/list       → Server returns tool catalogue
Client → POST /mcp  tools/call       → Server invokes tool, returns result
```

### Key Design Decisions

- **No controllers** — Minimal API only
- **No HTTPS** — Terminated at the PaaS/Ingress layer; the container speaks plain HTTP on port 8080
- **No OpenAPI** — Tool discovery happens via the MCP protocol (`tools/list`)
- **Stateless** — No local storage, no sessions beyond the MCP session ID
- **Method-level DI** — Services are injected directly into tool methods (not constructors)

---

## CI/CD

| Workflow | Trigger | Action |
|----------|---------|--------|
| **Build and Test** | Push / PR to `main` | `dotnet build` + `dotnet test` with coverage |
| **Docker Publish** | Push to `main` | Build and push image to GHCR |

The Docker image is published to `ghcr.io/<owner>/<repo>:latest` and also tagged with the full commit SHA.

---

## Security

See [SECURITY.md](SECURITY.md) for the vulnerability reporting policy.

Key security practices in this template:

- **Input validation** — All tool arguments are validated before use; invalid input returns `McpErrorCode.InvalidParams`
- **No secret logging** — Structured logging never captures raw API keys or tokens
- **Non-root container** — The Docker image runs as `$APP_UID`
- **Dependency scanning** — Dependabot keeps NuGet and GitHub Actions dependencies up to date

---

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md).

---

## License

This project is licensed under the [MIT License](LICENSE).

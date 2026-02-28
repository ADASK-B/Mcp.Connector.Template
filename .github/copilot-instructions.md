# Mcp.Connector.Template — Copilot Instructions

## Project Overview

This is a **template repository** for building MCP (Model Context Protocol) Connector services in C#.
It produces a container-first ASP.NET Core Minimal API that exposes MCP tools over HTTP using the official **MCP C# SDK**.
New connectors are created by cloning this template and adding tool/service/model classes — the hosting framework stays untouched.

## Tech Stack

- **.NET 10** (LTS), C# 14, Minimal API — no controllers
- **MCP C# SDK**: `ModelContextProtocol.AspNetCore` NuGet package (Streamable HTTP transport)
- **Container-first**: Linux Docker image, port **8080**, `ASPNETCORE_URLS=http://+:8080`
- **Testing**: xUnit, `Microsoft.AspNetCore.Mvc.Testing` (WebApplicationFactory), FluentAssertions
- **CI/CD**: GitHub Actions → build/test + Docker publish to GHCR

## MCP C# SDK — Key Concepts

The official [MCP C# SDK](https://github.com/modelcontextprotocol/csharp-sdk) provides three NuGet packages:

| Package | Use case |
|---------|----------|
| `ModelContextProtocol` | Console-hosted servers (stdio transport) + client APIs |
| `ModelContextProtocol.AspNetCore` | **HTTP-based MCP servers** (Streamable HTTP transport) — **this is what we use** |
| `ModelContextProtocol.Core` | Low-level APIs only, minimal dependencies |

### How Tool Discovery Works
1. `builder.Services.AddMcpServer().WithHttpTransport().WithToolsFromAssembly()` — scans the assembly for `[McpServerToolType]` classes
2. Every `public static` method decorated with `[McpServerTool]` becomes an invocable tool
3. `app.MapMcp("/mcp")` — maps the MCP JSON-RPC endpoint at `/mcp` (handles `tools/list`, `tools/call`, `initialize`, etc.)
4. The SDK handles the full MCP protocol — JSON-RPC framing, tool listing, tool invocation, error responses

### Transport Modes
- **Streamable HTTP** (`WithHttpTransport` + `MapMcp`) — for containerized/remote servers (our default)
- **Stdio** (`WithStdioServerTransport`) — for local CLI-based servers launched by clients like VS Code
- Both are compatible with OpenAI Responses API, Claude Desktop, VS Code Copilot, and other MCP clients

## Architecture Rules

### Program.cs (Host only)
Program.cs contains **only** hosting, DI registration, and endpoint mapping:
```csharp
var builder = WebApplication.CreateBuilder(args);

// Register external API service clients via HttpClientFactory
builder.Services.AddHttpClient<MyExternalApiService>(client =>
{
    client.BaseAddress = new Uri("https://api.example.com");
    client.Timeout = TimeSpan.FromSeconds(10);
});

// Register MCP server with HTTP transport + auto-discover tools
builder.Services.AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();

var app = builder.Build();

// Health probe for container orchestration (not part of MCP spec)
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

// MCP JSON-RPC endpoint — SDK handles everything
app.MapMcp("/mcp");

app.Run();
```

### Tool Classes (MCP SDK Pattern)
Every MCP tool is a **static class** decorated with `[McpServerToolType]`.
Each tool method is decorated with `[McpServerTool]` and `[Description("...")]`.
Dependencies are injected as **method parameters** (not constructor injection):
```csharp
[McpServerToolType]
public static class MyTool
{
    [McpServerTool(Name = "myToolAction"), Description("Describe what this tool does for the LLM")]
    public static async Task<string> MyToolAction(
        MyExternalApiService apiService,
        [Description("Describe this parameter for the LLM")] string inputParam,
        CancellationToken cancellationToken)
    {
        // 1. Validate input
        ArgumentException.ThrowIfNullOrWhiteSpace(inputParam);

        // 2. Call external API via injected service
        var result = await apiService.GetDataAsync(inputParam, cancellationToken);

        // 3. Return serialized result (SDK wraps it in MCP TextContent)
        return JsonSerializer.Serialize(result);
    }
}
```

### Services (External API Clients)
- External API calls go into dedicated service classes in `Services/`
- Register via `IHttpClientFactory` / `builder.Services.AddHttpClient<T>()` in Program.cs
- Configure `BaseAddress` and `Timeout` in the `AddHttpClient` delegate in Program.cs, not inside the service constructor
- Never use `new HttpClient()` directly
- Always accept `CancellationToken`
- Handle HTTP errors internally — return meaningful results or throw

### Models / DTOs
- One file per domain concern in `Models/` (e.g. `MyDomainModels.cs`)
- Use `record` types for immutable DTOs
- Use `System.Text.Json` serialization attributes (`[JsonPropertyName]`) where needed

## Project Structure

```
Mcp.Connector.Template/
├── Program.cs                         # Host, DI, endpoints (MapMcp + /health)
├── Tools/
│   └── <ToolName>Tool.cs              # [McpServerToolType] tool class
├── Services/
│   └── <ApiName>Service.cs            # HttpClient-based service via DI
├── Models/
│   └── <Domain>Models.cs              # DTOs (records)
├── appsettings.json
└── Dockerfile                         # Multi-stage, port 8080

Mcp.Connector.Template.Tests/
├── Unit/
│   ├── <ToolName>ToolTests.cs         # Tool logic + validation tests
│   └── <ApiName>ServiceTests.cs       # HTTP client mocking tests
├── Integration/
│   ├── HealthEndpointTests.cs         # GET /health → 200
│   └── McpEndpointTests.cs            # MCP protocol integration tests
└── TestInfrastructure/
    ├── CustomWebApplicationFactory.cs # In-memory host with mocked HTTP
    └── Fake<ApiName>Handler.cs        # HttpMessageHandler mock for external APIs
```

## Coding Conventions

- **Language**: C# 14, file-scoped namespaces, nullable reference types enabled
- **English only**: All code, comments, commit messages, tool descriptions, parameter descriptions, log messages, and documentation **must** be written in English
- **Naming**: PascalCase for public members; suffix `Tool` for tool classes, `Service` for HTTP client wrappers
- **Async**: All I/O methods are `async Task<T>`, always pass `CancellationToken`
- **Descriptions**: Every `[McpServerTool]` and every parameter exposed to LLMs **must** have a `[Description]` attribute. These descriptions are what the LLM sees to decide which tool to call
- **No HTTPS**: HTTPS termination happens at PaaS/Ingress level — the container listens on plain HTTP 8080
- **No OpenAPI**: OpenAPI is off — MCP SDK handles tool discovery via the MCP protocol
- **Logging**: Use `ILogger<T>`, structured logging, logs go to stdout
- **Validation**: Validate tool arguments early (null/empty checks, max length, allowed characters) and throw `McpException` for invalid input
- **Error handling**: Wrap external API calls in try/catch, return meaningful error text — never let raw exceptions bubble to the MCP client

## Container Rules

- Base image: `mcr.microsoft.com/dotnet/aspnet:10.0`
- Build image: `mcr.microsoft.com/dotnet/sdk:10.0`
- `EXPOSE 8080` (.NET 10+ defaults to port 8080 for non-root containers)
- Non-root user via `USER $APP_UID`
- No local state, no volumes, no persistent storage
- OCI labels for `org.opencontainers.image.source` and `org.opencontainers.image.revision`

## Testing Rules

- **Unit tests**: Test tool logic, validation, and DTO mapping in isolation; mock external HTTP calls via `HttpMessageHandler`
- **Integration tests**: Use `WebApplicationFactory<Program>` to spin up an in-memory host; override `HttpMessageHandler` in DI to mock external APIs
- **No real external calls**: All external APIs are always mocked in tests
- **Assertions**: Use FluentAssertions (`Should().Be...()` style)
- Run all tests via `dotnet test` — must pass before merge

## MCP Protocol Notes

- MCP endpoint is mapped via `app.MapMcp("/mcp")` at the `/mcp` path — the SDK handles JSON-RPC, tool listing, and tool invocation
- Transport: **Streamable HTTP** (compatible with OpenAI Responses API, Claude Desktop, VS Code Copilot)
- Tools are auto-discovered via `WithToolsFromAssembly()` scanning for `[McpServerToolType]` classes
- `/health` is a custom endpoint (not part of MCP spec) for container orchestration probes
- MCP clients connect to the server URL — the SDK handles the `initialize` → `tools/list` → `tools/call` lifecycle
- Tool parameters are described via `[Description]` attributes — the SDK auto-generates JSON Schema from them

## Adding a New Tool (Checklist)

1. Create `Tools/<Name>Tool.cs` with `[McpServerToolType]` + `[McpServerTool]` methods
2. Create `Services/<ApiName>Service.cs` with `HttpClient` injection if calling an external API
3. Create `Models/<Domain>Models.cs` for request/response DTOs
4. Register the service in `Program.cs`: `builder.Services.AddHttpClient<MyService>()`
5. Add unit tests in `Tests/Unit/`
6. Add integration tests in `Tests/Integration/`
7. Done — `WithToolsFromAssembly()` auto-detects the new tool, no routing changes needed

## Official References

> **SDK version note:** `ModelContextProtocol 1.0` (checked February 2026).

| Resource | URL |
|----------|-----|
| MCP C# SDK (GitHub) | https://github.com/modelcontextprotocol/csharp-sdk |
| ASP.NET Core Transport README | https://github.com/modelcontextprotocol/csharp-sdk/blob/main/src/ModelContextProtocol.AspNetCore/README.md |
| SDK Samples | https://github.com/modelcontextprotocol/csharp-sdk/tree/main/samples |
| MCP Specification | https://modelcontextprotocol.io/specification |
| OpenAI — Build a Remote MCP Connector | https://platform.openai.com/docs/guides/tools-remote-mcp |

### When to Re-Read These Links
- The SDK major/minor version was bumped in `*.csproj`
- A build fails with unknown MCP API types or methods
- You need an MCP capability not described in this file (resources, prompts, sampling, etc.)

### Self-Update Policy
If you fetch an official link above and discover that the SDK API has changed (new attributes, renamed methods, additional required setup), **update the affected instruction files** before continuing with the user's task:
- `copilot-instructions.md` — architecture rules, code patterns, checklist
- `instructions/csharp-mcp.instructions.md` — C# coding guidelines
- `skills/mcp-tool-creation/SKILL.md` — step-by-step skill guide

Rule: **If a pattern in this file conflicts with the current SDK, the SDK documentation wins — fix this file, then continue.**

## Security Rules

- **No secrets in code**: Never commit API keys, tokens, passwords, or connection strings. Use environment variables or a secrets manager.
- **No unsafe defaults**: Template code must not ship with default passwords, disabled auth, or permissive CORS. When a configuration value is security-sensitive, use a placeholder like `REPLACE_ME` and add a comment.
- **Dependency hygiene**: Keep NuGet packages up to date. Never reference packages from untrusted feeds. Review transitive dependency changes in PRs.
- **Container security**: Always run as non-root (`USER $APP_UID`). Never copy secrets into Docker images. Use multi-stage builds to exclude SDK/build tools from the final image.
- **Input validation**: All MCP tool parameters must be validated before use. Never pass user input directly to shell commands, SQL, or file paths.
- **Logging safety**: Never log secrets, tokens, or full request/response bodies containing sensitive data. Use structured logging with safe fields only.

## Testing Standard

- **TDD preferred**: When creating or modifying feature code, write or update tests in parallel — ideally test-first (Red → Green → Refactor).
- **Mandatory test coverage**: Every new MCP tool must have corresponding unit tests (validation, mapping, error handling) and integration tests (WebApplicationFactory-based).
- **All tests must pass**: Run `dotnet test` locally before pushing. CI will reject PRs with failing tests.
- **No real external calls**: All external HTTP APIs must be mocked in tests via `HttpMessageHandler`. Zero network calls in the test suite.

## PR Quality

- **Small, focused PRs**: Each PR should address a single concern (one tool, one bug fix, one refactoring). Avoid mixing unrelated changes.
- **Clear descriptions**: PR title must summarize the change. Description must include: what changed, why, and how to verify.
- **Reproducible steps**: If the PR adds or modifies MCP tool behavior, include example tool calls and expected responses in the PR description.
- **Commit hygiene**: Use conventional commit messages (e.g. `feat: add getWeather tool`, `fix: handle null response from API`, `test: add unit tests for validation`).
- **Review checklist**: Before marking a PR as ready, verify: tests pass, no secrets committed, descriptions on all tool parameters, no `TODO` markers left unresolved.

## CI — Local Commands Before PR

Run these commands locally before pushing a PR:

```bash
# Restore, build, and test the full solution
dotnet restore
dotnet build --configuration Release --no-restore
dotnet test --configuration Release --no-build --verbosity normal
```

All three commands must succeed with zero errors and zero test failures.

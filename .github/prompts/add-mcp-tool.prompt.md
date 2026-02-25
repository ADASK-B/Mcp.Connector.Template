---
name: add-mcp-tool
description: Add a new MCP tool to this connector with service, models, DI registration, tests, and documentation — following the MCP C# SDK pattern
---

# Add a New MCP Tool

Add a new MCP tool to this project following the architecture in `copilot-instructions.md` and the step-by-step guide in `.github/skills/mcp-tool-creation/SKILL.md`.

## Tool Specification

- **Tool name** (camelCase): {e.g. "getWeatherForecast"}
- **Description** (what the LLM sees): {e.g. "Returns the current weather forecast for a given city"}
- **External API**: {URL and brief description, or "none"}
- **Input parameters**: {List each parameter with type, description, and constraints}
- **Output format**: {Describe the JSON response shape}

## Required Files (generate all)

1. `Models/<Domain>Models.cs` — `record` DTOs with `[JsonPropertyName]`
2. `Services/<ApiName>Service.cs` — `HttpClient`-based, registered via `AddHttpClient<T>()`
3. `Tools/<ToolName>Tool.cs` — `[McpServerToolType]` static class with `[McpServerTool]` methods
4. Update `Program.cs` — add `builder.Services.AddHttpClient<ServiceName>()`
5. `Tests/Unit/<ToolName>ToolTests.cs` — validation, mapping, error handling tests
6. `Tests/Integration/<ToolName>EndpointTests.cs` — WebApplicationFactory-based MCP protocol tests

## Checklist

- [ ] `[Description]` on every tool method and every LLM-visible parameter
- [ ] Input validation with `ArgumentException.ThrowIfNullOrWhiteSpace` and `McpProtocolException`
- [ ] External API calls wrapped in try/catch — error JSON returned, no raw exceptions
- [ ] `CancellationToken` as last parameter on all async methods
- [ ] All external HTTP mocked in tests — zero real network calls
- [ ] `dotnet build` passes
- [ ] `dotnet test` passes

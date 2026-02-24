---
name: new-mcp-tool
description: Scaffold a new MCP tool with service, models, DI registration, and tests for this C# MCP Connector project
---

# Create a New MCP Tool

I need to add a new MCP tool to this project. The project uses the official **MCP C# SDK** (`ModelContextProtocol.AspNetCore`) with Streamable HTTP transport.

## Tool Details

- **Tool name**: {Provide a camelCase name for the tool, e.g. "getStockPrice"}
- **What it does**: {Describe what the tool should do, e.g. "Fetches the current stock price for a given ticker symbol"}
- **External API**: {URL and brief description of the external API to call, or "none" if no external API}
- **Input parameters**: {List the parameters the LLM will provide, with types and descriptions}
- **Output format**: {Describe the expected response shape}

## Requirements

Generate the following files following the project's architecture conventions:

1. **`Models/<Domain>Models.cs`** — `record` DTOs with `[JsonPropertyName]` for API mapping
2. **`Services/<ApiName>Service.cs`** — `HttpClient`-based service registered via `AddHttpClient<T>()`
3. **`Tools/<ToolName>Tool.cs`** — Static class with `[McpServerToolType]`, methods with `[McpServerTool]` + `[Description]`, input validation, error handling
4. **Update `Program.cs`** — Add `builder.Services.AddHttpClient<MyService>()` before `AddMcpServer()`
5. **`Tests/Unit/<ToolName>ToolTests.cs`** — xUnit tests for validation, mapping, error cases
6. **`Tests/Integration/<ToolName>EndpointTests.cs`** — WebApplicationFactory-based MCP protocol tests with mocked HTTP

## Conventions to Follow

- File-scoped namespaces, nullable reference types, C# 13
- `[Description]` on every tool method and every LLM-visible parameter
- `CancellationToken` as last parameter on all async methods
- Validate inputs first, throw `McpProtocolException` with `McpErrorCode.InvalidParams` for bad args
- Wrap external API calls in try/catch — return error JSON, never throw raw exceptions
- Tool methods return `string` (JSON-serialized result)
- Use FluentAssertions in tests
- Mock all external HTTP calls in tests via `HttpMessageHandler`

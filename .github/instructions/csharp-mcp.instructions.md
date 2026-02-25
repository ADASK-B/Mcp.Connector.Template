---
description: C# coding guidelines for MCP Connector projects using the official MCP C# SDK
applyTo: '**/*.cs'
---

# MCP Connector — C# Coding Guidelines

## MCP C# SDK Fundamentals

This project uses the official **MCP C# SDK** (`ModelContextProtocol.AspNetCore`) for HTTP-based MCP servers.
The SDK handles the MCP protocol (JSON-RPC, tool discovery, tool invocation) automatically.
You do NOT need to implement custom routing, JSON-RPC parsing, or tool registries.

### NuGet Packages
- `ModelContextProtocol.AspNetCore` — HTTP transport for ASP.NET Core (`WithHttpTransport`, `MapMcp`)
- `ModelContextProtocol` — base SDK (included transitively)

### Core Registration Pattern (Program.cs)
```csharp
builder.Services.AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();

app.MapMcp("/mcp");
```
- `WithToolsFromAssembly()` auto-discovers all `[McpServerToolType]` classes in the assembly
- `MapMcp("/mcp")` maps the MCP JSON-RPC endpoint at `/mcp` — no manual route registration needed

## Tool Implementation Rules

### Class Structure
- Each tool is a **static class** decorated with `[McpServerToolType]`
- Each tool method is **public static**, decorated with `[McpServerTool]` and `[Description("...")]`
- Tool name is set via `[McpServerTool(Name = "toolName")]` — use camelCase for tool names
- Dependencies (services, `HttpClient`, `ILogger<T>`, `McpServer`) are injected as **method parameters**

### Required Attributes
```csharp
using System.ComponentModel;
using ModelContextProtocol.Server;

[McpServerToolType]
public static class ExampleTool
{
    [McpServerTool(Name = "exampleAction"), Description("Clear description of what this tool does — the LLM reads this")]
    public static async Task<string> ExampleAction(
        MyApiService apiService,                                           // DI-injected service
        [Description("Clear description of this parameter")] string input, // LLM sees this
        CancellationToken cancellationToken)                               // Always include
    {
        // Implementation
    }
}
```

### Description Best Practices
- `[Description]` on the method: explain what the tool does, when to use it, what it returns
- `[Description]` on each parameter: explain expected format, valid values, constraints
- These descriptions are the **only documentation the LLM sees** — be precise and helpful
- Bad: `[Description("The input")]` — Good: `[Description("ISO 3166-1 alpha-2 country code, e.g. 'DE', 'US'")]`

### Input Validation
- Validate all tool parameters at the start of the method
- Use `ArgumentException.ThrowIfNullOrWhiteSpace()` for required strings
- For constraint violations, throw `McpException` with a descriptive message:
```csharp
if (input.Length > 100)
    throw new McpException("Input exceeds maximum length of 100 characters.");
```

### Return Values
- Return `string` (SDK wraps it in `TextContentBlock` automatically)
- For structured data, serialize to JSON: `return JsonSerializer.Serialize(result);`
- For errors, return descriptive error text — do NOT throw unhandled exceptions

## Service Implementation Rules

### External API Clients
- Place in `Services/` directory, suffix with `Service` (e.g. `MyApiService.cs`)
- Accept `HttpClient` via constructor (injected by `IHttpClientFactory`)
- Register in Program.cs: `builder.Services.AddHttpClient<MyApiService>()`
- Always accept `CancellationToken` in async methods
- Handle HTTP errors internally with try/catch

```csharp
public class MyApiService
{
    private readonly HttpClient _httpClient;
    public MyApiService(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<MyResult> GetDataAsync(string param, CancellationToken ct)
    {
        var response = await _httpClient.GetAsync($"/api/data?q={Uri.EscapeDataString(param)}", ct);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<MyResult>(ct)
            ?? throw new InvalidOperationException("API returned null");
    }
}
```

## Model / DTO Rules

- Place in `Models/` directory
- Use `record` types for immutable DTOs
- Use `System.Text.Json` attributes: `[JsonPropertyName("snake_case")]`
- One file per domain concern

```csharp
namespace Mcp.Connector.Template.Models;

public record MyApiResponse(
    [property: JsonPropertyName("result_field")] string ResultField,
    [property: JsonPropertyName("numeric_value")] double NumericValue);
```

## General C# Conventions

- **English only**: All code, comments, `[Description]` attributes, log messages, and XML docs must be written in English
- File-scoped namespaces (`namespace X;` not `namespace X { }`)
- Nullable reference types enabled — handle nulls explicitly
- `async Task<T>` for all I/O, never `.Result` or `.Wait()`
- Always forward `CancellationToken`
- Use `ILogger<T>` for logging, structured format: `_logger.LogInformation("Fetched {Count} items", count)`
- No `Console.WriteLine` — use logging infrastructure

## Testing Conventions

- Unit tests mock `HttpMessageHandler` to intercept HTTP calls
- Integration tests use `WebApplicationFactory<Program>` with overridden DI
- All external API calls must be mocked — zero real network calls in tests
- Use FluentAssertions: `result.Should().NotBeNull()`, `response.StatusCode.Should().Be(HttpStatusCode.OK)`


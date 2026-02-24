---
name: mcp-tool-creation
description: Step-by-step guide for adding a new MCP tool to a C# MCP Connector project using the official MCP C# SDK. Keywords: new tool, add tool, mcp tool, create tool, wrapper, connector, scaffold tool.
---

# Skill: Add a New MCP Tool (C# SDK)

This skill guides you through adding a new MCP tool to an ASP.NET Core MCP Connector project that uses the official MCP C# SDK (`ModelContextProtocol.AspNetCore`).

## Prerequisites
- Project already has `ModelContextProtocol.AspNetCore` NuGet package
- `Program.cs` already calls `AddMcpServer().WithHttpTransport().WithToolsFromAssembly()` and `app.MapMcp()`

## Step-by-Step Process

### Step 1: Define the Models / DTOs

Create `Models/<Domain>Models.cs` with the request/response DTOs for the external API you're wrapping.

**Pattern:**
```csharp
using System.Text.Json.Serialization;

namespace Mcp.Connector.Template.Models;

// Response from external API (matches their JSON structure)
public record ExternalApiResponse(
    [property: JsonPropertyName("api_field_name")] string FieldName,
    [property: JsonPropertyName("numeric_field")] double NumericField);

// Simplified result returned to the MCP client (your custom shape)
public record ToolResult(
    string DisplayName,
    double Value,
    string Unit);
```

**Rules:**
- Use `record` types for immutability
- Use `[JsonPropertyName]` to map external API snake_case to C# PascalCase
- Separate external API response DTOs from your simplified tool result DTOs

### Step 2: Create the Service (External API Client)

Create `Services/<ApiName>Service.cs` that wraps the external HTTP API.

**Pattern:**
```csharp
using System.Net.Http.Json;
using Mcp.Connector.Template.Models;

namespace Mcp.Connector.Template.Services;

public class MyApiService
{
    private readonly HttpClient _httpClient;

    public MyApiService(HttpClient httpClient)
    {
        _httpClient = httpClient;
        _httpClient.BaseAddress ??= new Uri("https://api.example.com");
        _httpClient.Timeout = TimeSpan.FromSeconds(10);
    }

    public async Task<ToolResult> GetDataAsync(string query, CancellationToken ct)
    {
        var response = await _httpClient.GetAsync(
            $"/v1/data?q={Uri.EscapeDataString(query)}", ct);
        response.EnsureSuccessStatusCode();

        var apiResult = await response.Content.ReadFromJsonAsync<ExternalApiResponse>(ct)
            ?? throw new InvalidOperationException("API returned null response");

        // Map external API response to your tool result
        return new ToolResult(
            DisplayName: apiResult.FieldName,
            Value: apiResult.NumericField,
            Unit: "units");
    }
}
```

**Rules:**
- Constructor takes `HttpClient` (injected by `IHttpClientFactory`)
- Set `BaseAddress` and `Timeout` in constructor
- Always accept and forward `CancellationToken`
- Map external API response to your own DTO shape
- Handle HTTP errors (the `EnsureSuccessStatusCode` or try/catch)

### Step 3: Create the Tool Class

Create `Tools/<ToolName>Tool.cs` with the MCP SDK attributes.

**Pattern:**
```csharp
using System.ComponentModel;
using System.Text.Json;
using ModelContextProtocol.Server;
using Mcp.Connector.Template.Services;

namespace Mcp.Connector.Template.Tools;

[McpServerToolType]
public static class MyNewTool
{
    [McpServerTool(Name = "myToolAction"), Description("Describe clearly what this tool does, when the LLM should call it, and what it returns")]
    public static async Task<string> MyToolAction(
        MyApiService apiService,
        [Description("Describe what this parameter is, valid values, format, constraints")] string inputParam,
        CancellationToken cancellationToken)
    {
        // 1. Validate input
        ArgumentException.ThrowIfNullOrWhiteSpace(inputParam);

        if (inputParam.Length > 200)
            throw new McpProtocolException(
                "inputParam exceeds maximum length of 200 characters",
                McpErrorCode.InvalidParams);

        // 2. Call external API via injected service
        try
        {
            var result = await apiService.GetDataAsync(inputParam, cancellationToken);
            return JsonSerializer.Serialize(result);
        }
        catch (HttpRequestException ex)
        {
            return JsonSerializer.Serialize(new { error = $"External API call failed: {ex.Message}" });
        }
    }
}
```

**Rules:**
- Class: `static`, `[McpServerToolType]` attribute
- Method: `public static`, `[McpServerTool(Name = "camelCase")]`, `[Description("...")]`
- Tool name in `camelCase` (this is what LLM clients see)
- `[Description]` is mandatory on method AND on every LLM-visible parameter
- Validate input immediately — throw `McpProtocolException` for invalid args
- Wrap external calls in try/catch — return error JSON, never throw raw exceptions
- Always include `CancellationToken` as last parameter

### Step 4: Register the Service in Program.cs

Add the DI registration for your service **before** `AddMcpServer()`:

```csharp
builder.Services.AddHttpClient<MyApiService>();
```

The tool itself does NOT need registration — `WithToolsFromAssembly()` discovers it automatically.

### Step 5: Add Unit Tests

Create `Tests/Unit/<ToolName>ToolTests.cs`:

```csharp
public class MyNewToolTests
{
    [Fact]
    public async Task MyToolAction_ValidInput_ReturnsExpectedResult()
    {
        // Arrange: create a mock HttpMessageHandler that returns test data
        // Act: call the tool method directly
        // Assert: verify the result contains expected fields
    }

    [Fact]
    public async Task MyToolAction_NullInput_ThrowsArgumentException()
    {
        // Assert.ThrowsAsync<ArgumentException>(...)
    }

    [Fact]
    public async Task MyToolAction_InputTooLong_ThrowsMcpProtocolException()
    {
        // Assert.ThrowsAsync<McpProtocolException>(...)
    }
}
```

### Step 6: Add Integration Tests

Create `Tests/Integration/<ToolName>EndpointTests.cs` using `WebApplicationFactory<Program>`:
- Override `HttpMessageHandler` in DI to mock external API responses
- Send MCP protocol requests to verify tool invocation end-to-end

### Step 7: Verify

Run `dotnet build` and `dotnet test` to confirm everything compiles and passes.

## Checklist Summary

- [ ] `Models/<Domain>Models.cs` — DTOs for external API and tool result
- [ ] `Services/<ApiName>Service.cs` — HTTP client wrapper with DI
- [ ] `Tools/<ToolName>Tool.cs` — `[McpServerToolType]` + `[McpServerTool]` with validation
- [ ] `Program.cs` — `builder.Services.AddHttpClient<MyApiService>()`
- [ ] `Tests/Unit/<ToolName>ToolTests.cs` — validation + mapping tests
- [ ] `Tests/Integration/<ToolName>EndpointTests.cs` — MCP protocol tests
- [ ] `dotnet build` passes
- [ ] `dotnet test` passes

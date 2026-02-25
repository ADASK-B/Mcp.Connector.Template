---
name: tdd-mcp
description: Step-by-step TDD workflow for implementing MCP tools in C# — Red/Green/Refactor cycle with xUnit and FluentAssertions. Keywords: tdd, test-driven, red green refactor, mcp tool, test first, unit test.
---

# Skill: TDD Workflow for MCP Tools (C# SDK)

This skill guides you through implementing an MCP tool using strict Test-Driven Development (Red → Green → Refactor).

## Prerequisites

- Project uses `ModelContextProtocol.AspNetCore` NuGet package
- Test project references xUnit, FluentAssertions, and `Microsoft.AspNetCore.Mvc.Testing`
- Familiarity with the MCP tool pattern in `copilot-instructions.md`

## Step-by-Step Process

### Step 1: Define the Tool Contract (No Code Yet)

Before writing any code, define:
- **Tool name** (camelCase): what the LLM will call
- **Parameters**: names, types, descriptions, constraints
- **Return shape**: JSON structure the tool returns
- **Error cases**: what happens with invalid input, API failures

Write this down as comments in a new test file.

### Step 2: RED — Write Failing Unit Tests

Create `Mcp.Connector.Template.Tests/Unit/<ToolName>ToolTests.cs`:

```csharp
using FluentAssertions;
using Xunit;

namespace Mcp.Connector.Template.Tests.Unit;

public class MyToolTests
{
    [Fact]
    public async Task ToolAction_ValidInput_ReturnsExpectedJson()
    {
        // Arrange
        var handler = new FakeApiHandler(HttpStatusCode.OK, """{"field": "value"}""");
        var httpClient = new HttpClient(handler) { BaseAddress = new Uri("https://api.example.com") };
        var service = new MyApiService(httpClient);

        // Act
        var result = await MyTool.ToolAction(service, "valid-input", CancellationToken.None);

        // Assert
        result.Should().Contain("\"field\"");
    }

    [Fact]
    public async Task ToolAction_NullInput_ThrowsArgumentException()
    {
        // Arrange
        var service = CreateServiceWithMockHandler();

        // Act & Assert
        var act = () => MyTool.ToolAction(service, null!, CancellationToken.None);
        await act.Should().ThrowAsync<ArgumentException>();
    }

    [Fact]
    public async Task ToolAction_EmptyInput_ThrowsArgumentException()
    {
        var service = CreateServiceWithMockHandler();
        var act = () => MyTool.ToolAction(service, "", CancellationToken.None);
        await act.Should().ThrowAsync<ArgumentException>();
    }

    [Fact]
    public async Task ToolAction_InputTooLong_ThrowsMcpException()
    {
        var service = CreateServiceWithMockHandler();
        var longInput = new string('x', 201);
        var act = () => MyTool.ToolAction(service, longInput, CancellationToken.None);
        await act.Should().ThrowAsync<McpException>();
    }

    [Fact]
    public async Task ToolAction_ApiFailure_ReturnsErrorJson()
    {
        var handler = new FakeApiHandler(HttpStatusCode.InternalServerError, "");
        var httpClient = new HttpClient(handler) { BaseAddress = new Uri("https://api.example.com") };
        var service = new MyApiService(httpClient);

        var result = await MyTool.ToolAction(service, "valid-input", CancellationToken.None);

        result.Should().Contain("error");
    }
}
```

**Run `dotnet test`** — all new tests must FAIL (they reference classes that don't exist yet).

### Step 3: GREEN — Minimal Implementation

Create the minimum code to make all tests pass:

1. **Models** (`Models/<Domain>Models.cs`) — record DTOs
2. **Service** (`Services/<ApiName>Service.cs`) — HttpClient wrapper
3. **Tool** (`Tools/<ToolName>Tool.cs`) — static class with `[McpServerToolType]`
4. **DI** (`Program.cs`) — `builder.Services.AddHttpClient<T>()`

Follow the patterns in `.github/skills/mcp-tool-creation/SKILL.md`.

**Run `dotnet test`** — all tests must PASS.

### Step 4: Add Integration Tests

Create `Mcp.Connector.Template.Tests/Integration/<ToolName>EndpointTests.cs`:

```csharp
public class MyToolEndpointTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;

    public MyToolEndpointTests(CustomWebApplicationFactory factory)
        => _client = factory.CreateClient();

    [Fact]
    public async Task Health_ReturnsOk()
    {
        var response = await _client.GetAsync("/health");
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }
}
```

**Run `dotnet test`** — all tests must PASS.

### Step 5: REFACTOR

Improve the code without changing behavior:
- Improve `[Description]` attributes for clarity
- Extract magic numbers to constants
- Simplify validation logic
- Improve error messages

**Run `dotnet test`** — all tests must still PASS.

### Step 6: Verify

```bash
dotnet restore
dotnet build --configuration Release --no-restore
dotnet test --configuration Release --no-build --verbosity normal
```

All three commands must succeed with zero errors.

## Definition of Done

- [ ] All unit tests pass (validation, mapping, error handling)
- [ ] All integration tests pass (health endpoint, MCP protocol)
- [ ] `[Description]` on every tool method and parameter
- [ ] Input validation with `ArgumentException` and `McpException`
- [ ] External API calls wrapped in try/catch
- [ ] `CancellationToken` on all async methods
- [ ] Zero real HTTP calls in tests
- [ ] `dotnet build` + `dotnet test` pass clean

## Related Prompt Files

- `.github/prompts/tdd-feature.prompt.md` — generic TDD workflow
- `.github/prompts/add-mcp-tool.prompt.md` — full tool scaffolding prompt
- `.github/prompts/write-tests.prompt.md` — test generation for existing code

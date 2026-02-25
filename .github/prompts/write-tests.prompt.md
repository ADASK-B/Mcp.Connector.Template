---
name: write-tests
description: Generate unit and integration tests for the current file or a specified class, following the project's xUnit + FluentAssertions conventions
---

# Write Tests

Generate comprehensive tests for the following target:

## Target

{Specify the file, class, or method to test — or say "current file" to test whatever is open}

## Instructions

1. **Read** the target file and `copilot-instructions.md` to understand conventions.
2. **Determine test type**:
   - `Tools/*Tool.cs` → Unit tests (call static methods directly) + Integration tests (MCP protocol)
   - `Services/*Service.cs` → Unit tests (mock `HttpMessageHandler`)
   - `Models/*Models.cs` → Unit tests (serialization/deserialization roundtrip)
3. **Create test file(s)** in the appropriate directory:
   - Unit: `Mcp.Connector.Template.Tests/Unit/<ClassName>Tests.cs`
   - Integration: `Mcp.Connector.Template.Tests/Integration/<ClassName>EndpointTests.cs`

## Required Test Cases

### For Tool classes:
- Valid input → expected JSON output
- Null/empty required parameter → `ArgumentException`
- Parameter exceeding constraints → `McpProtocolException` with `InvalidParams`
- External API failure → graceful error response (JSON with error field)

### For Service classes:
- Successful API response → correctly mapped DTO
- API returns error status code → appropriate exception or error result
- API returns null/malformed JSON → `InvalidOperationException`

### For Models:
- JSON roundtrip: serialize → deserialize → original values preserved
- `[JsonPropertyName]` mappings work correctly

## Conventions

- Framework: xUnit (`[Fact]`, `[Theory]`)
- Assertions: FluentAssertions (`Should().Be()`, `Should().NotBeNull()`)
- Naming: `MethodName_Scenario_ExpectedResult`
- Mock HTTP via custom `HttpMessageHandler` — never use mocking frameworks for `HttpClient`
- Always use `CancellationToken.None` in test calls
- All test names and comments in English
- Run `dotnet test` to verify all tests pass

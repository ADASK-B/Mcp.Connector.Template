---
name: tdd-feature
description: Implement a new feature using Test-Driven Development (Red → Green → Refactor) for this MCP Connector project
---

# TDD Feature Workflow

Implement the following feature using strict TDD (Red → Green → Refactor):

## Feature Description

{Describe the feature you want to implement}

## TDD Process

Follow these steps in order. Do NOT skip ahead.

### Phase 1: Red (Write Failing Tests)

1. **Read** `copilot-instructions.md` for project conventions (testing rules, naming, assertions).
2. **Create the test file** first — before any production code:
   - Unit test in `Mcp.Connector.Template.Tests/Unit/`
   - Name format: `<FeatureName>Tests.cs`
3. **Write test cases** covering:
   - Happy path (valid input → expected output)
   - Validation errors (null, empty, too-long input → exception)
   - External API failure (HTTP error → graceful error response)
   - Edge cases (boundary values, special characters)
4. **Run `dotnet test`** — confirm all new tests FAIL (Red).

### Phase 2: Green (Minimal Implementation)

5. **Write the minimum production code** to make all tests pass:
   - Models in `Models/`
   - Service in `Services/`
   - Tool in `Tools/`
   - DI registration in `Program.cs`
6. **Run `dotnet test`** — confirm all tests PASS (Green).

### Phase 3: Refactor

7. **Improve code quality** without changing behavior:
   - Extract constants, simplify logic, improve naming
   - Ensure `[Description]` attributes are clear and helpful for LLMs
   - Verify error messages are meaningful
8. **Run `dotnet test`** — confirm all tests still PASS.

## Conventions

- Use xUnit `[Fact]` and `[Theory]` attributes
- Use FluentAssertions for assertions
- Mock all external HTTP calls via `HttpMessageHandler`
- Follow naming: `MethodName_Scenario_ExpectedResult`
- All code, comments, and test names in English

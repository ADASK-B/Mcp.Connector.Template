## Description

<!-- Briefly describe the changes in this pull request -->

## Related issue

<!-- Link to the GitHub issue this PR addresses, e.g. "Closes #42" -->

Closes #

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing behaviour to change)
- [ ] Documentation update
- [ ] Refactor (no functional change)

## Checklist

### Code quality
- [ ] All code and comments are written in English
- [ ] File-scoped namespaces and nullable reference types are used
- [ ] No raw `new HttpClient()` — `IHttpClientFactory` is used everywhere

### MCP conventions (if adding/changing a tool)
- [ ] Tool class is `static` and decorated with `[McpServerToolType]`
- [ ] Each tool method has `[McpServerTool(Name = "camelCase")]` and `[Description("...")]`
- [ ] Each LLM-visible parameter has a `[Description("...")]` attribute
- [ ] Input is validated early; invalid args throw `McpProtocolException` with `McpErrorCode.InvalidParams`
- [ ] External API calls are wrapped in try/catch; errors are returned as JSON, not thrown
- [ ] `CancellationToken` is the last parameter on all async methods
- [ ] Service is registered in `Program.cs` via `builder.Services.AddHttpClient<T>()`

### Testing
- [ ] Unit tests added or updated for changed logic
- [ ] Integration tests added or updated where applicable
- [ ] All external HTTP calls are mocked in tests (no real network calls)
- [ ] `dotnet test` passes locally

### Documentation
- [ ] `README.md` updated if the public-facing behaviour changed
- [ ] Code comments / XML docs added for non-obvious logic

## Screenshots / logs (optional)

<!-- Paste relevant output, error messages, or screenshots here -->

var builder = WebApplication.CreateBuilder(args);

// Register MCP server with Streamable HTTP transport; tools are auto-discovered via [McpServerToolType]
builder.Services.AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();

var app = builder.Build();

// Health probe for container orchestration (not part of MCP spec)
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

// MCP JSON-RPC endpoint — the SDK handles initialize, tools/list, and tools/call
app.MapMcp("/mcp");

app.Run();

// Expose the implicit Program class so integration tests can use WebApplicationFactory<Program>
public partial class Program { }

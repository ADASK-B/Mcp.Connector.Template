// -----------------------------------------------------------------------
// Program.cs — MCP Connector host configuration.
//
// This file contains ONLY hosting, DI registration, and endpoint mapping.
// Business logic lives in Tools/, Services/, and Models/.
//
// The MCP C# SDK handles:
//   • JSON-RPC framing and protocol negotiation
//   • Tool discovery (via WithToolsFromAssembly)
//   • Tool invocation and response serialization
//   • Error responses in MCP format
// -----------------------------------------------------------------------

using Mcp.Connector.Template.Services;

var builder = WebApplication.CreateBuilder(args);

// ---------------------------------------------------------------------------
//  Register external API services via IHttpClientFactory.
//  Each service gets its own named HttpClient with independent settings.
// ---------------------------------------------------------------------------
builder.Services.AddHttpClient<OpenMeteoService>();

// ---------------------------------------------------------------------------
//  Register the MCP server with Streamable HTTP transport.
//  WithToolsFromAssembly() scans for all [McpServerToolType] classes
//  and exposes their [McpServerTool] methods as invocable MCP tools.
// ---------------------------------------------------------------------------
builder.Services
    .AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();

var app = builder.Build();

// ---------------------------------------------------------------------------
//  Health probe — used by container orchestration (Docker, Kubernetes, Azure).
//  This is NOT part of the MCP spec, just a standard liveness check.
// ---------------------------------------------------------------------------
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

// ---------------------------------------------------------------------------
//  MCP endpoint — the SDK handles everything at this path:
//    POST /mcp  → initialize, tools/list, tools/call, etc.
// ---------------------------------------------------------------------------
app.MapMcp("/mcp");

app.Run();

// ---------------------------------------------------------------------------
//  Make the implicit Program class visible to the test project so that
//  WebApplicationFactory<Program> can reference it.
// ---------------------------------------------------------------------------
public partial class Program;

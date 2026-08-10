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

using Mcp.Connector.Template.Models;

var releaseIdentity = ApplicationReleaseIdentity.Load(typeof(Program).Assembly);
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton(releaseIdentity);
builder.Services.AddSingleton(
    static _ => ApplicationConfiguration.LoadFromFile(ApplicationConfiguration.FilePath));

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

// Resolve required setup-derived configuration during startup. A missing or
// malformed generated file must stop the process instead of activating a
// hidden application default.
_ = app.Services.GetRequiredService<ApplicationConfiguration>();

// ---------------------------------------------------------------------------
//  ApplicationContract lifecycle endpoints. This deliberately simple Test App
//  has no runtime dependencies, so a running host is also ready for traffic.
// ---------------------------------------------------------------------------
app.MapGet("/healthz", static () => Results.Ok(new HealthStatusResponse("healthy")));
app.MapGet("/readyz", static () => Results.Ok(new HealthStatusResponse("ready")));
app.MapGet(
    "/version",
    static (ApplicationReleaseIdentity identity) => Results.Ok(identity.ToResponse()));
app.MapGet(
    "/config",
    static (ApplicationConfiguration configuration) => Results.Ok(configuration.ToResponse()));

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

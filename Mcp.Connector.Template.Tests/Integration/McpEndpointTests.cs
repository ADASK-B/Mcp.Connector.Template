using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FluentAssertions;
using Mcp.Connector.Template.Tests.TestInfrastructure;

namespace Mcp.Connector.Template.Tests.Integration;

/// <summary>
/// Integration tests for the MCP endpoint at <c>/mcp</c>.
/// Verifies that the SDK correctly handles the MCP JSON-RPC protocol
/// (initialize, tools/list, tools/call).
/// </summary>
public class McpEndpointTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;

    public McpEndpointTests(CustomWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
        _client.DefaultRequestHeaders.Add("Accept", "application/json, text/event-stream");
    }

    [Fact]
    public async Task PostMcp_Initialize_ReturnsOk()
    {
        var request = new
        {
            jsonrpc = "2.0",
            id = 1,
            method = "initialize",
            @params = new
            {
                protocolVersion = "2024-11-05",
                capabilities = new { },
                clientInfo = new { name = "test-client", version = "1.0.0" }
            }
        };

        var response = await _client.PostAsJsonAsync("/mcp", request);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task PostMcp_ToolsList_ContainsEchoTool()
    {
        await InitializeSessionAsync();

        var request = new
        {
            jsonrpc = "2.0",
            id = 2,
            method = "tools/list",
            @params = new { }
        };

        var response = await _client.PostAsJsonAsync("/mcp", request);

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = await response.Content.ReadAsStringAsync();
        body.Should().Contain("echo");
    }

    [Fact]
    public async Task PostMcp_CallEchoTool_ReturnsEchoedMessage()
    {
        await InitializeSessionAsync();

        var request = new
        {
            jsonrpc = "2.0",
            id = 3,
            method = "tools/call",
            @params = new
            {
                name = "echo",
                arguments = new { message = "Hello, MCP!" }
            }
        };

        var response = await _client.PostAsJsonAsync("/mcp", request);

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = await response.Content.ReadAsStringAsync();
        body.Should().Contain("Hello, MCP!");
    }

    /// <summary>
    /// Sends an MCP <c>initialize</c> request and attaches the returned
    /// <c>Mcp-Session-Id</c> to all subsequent requests on this client.
    /// </summary>
    private async Task InitializeSessionAsync()
    {
        var init = new
        {
            jsonrpc = "2.0",
            id = 0,
            method = "initialize",
            @params = new
            {
                protocolVersion = "2024-11-05",
                capabilities = new { },
                clientInfo = new { name = "test-client", version = "1.0.0" }
            }
        };

        var response = await _client.PostAsJsonAsync("/mcp", init);

        // The MCP Streamable HTTP transport returns a session ID that must be
        // included in all subsequent requests via the Mcp-Session-Id header.
        if (response.Headers.TryGetValues("Mcp-Session-Id", out var values))
        {
            var sessionId = values.FirstOrDefault();
            if (sessionId is not null)
            {
                _client.DefaultRequestHeaders.Remove("Mcp-Session-Id");
                _client.DefaultRequestHeaders.TryAddWithoutValidation("Mcp-Session-Id", sessionId);
            }
        }
    }
}


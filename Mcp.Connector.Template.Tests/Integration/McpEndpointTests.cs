// -----------------------------------------------------------------------
// McpEndpointTests.cs — Integration test for the /mcp MCP endpoint.
//
// Verifies that the MCP JSON-RPC endpoint is reachable and responds
// to protocol requests via the full in-memory pipeline.
//
// The MCP Streamable HTTP transport requires specific headers:
//   Content-Type: application/json
//   Accept: application/json, text/event-stream
// -----------------------------------------------------------------------

using System.Net;
using System.Net.Http.Headers;
using System.Text;
using FluentAssertions;
using Mcp.Connector.Template.Tests.TestInfrastructure;

namespace Mcp.Connector.Template.Tests.Integration;

public class McpEndpointTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;

    public McpEndpointTests(CustomWebApplicationFactory factory)
        => _client = factory.CreateClient();

    [Fact]
    public async Task McpEndpoint_PostInitialize_ReturnsSuccessResponse()
    {
        // Arrange — send an MCP "initialize" JSON-RPC request with required headers
        var initializeRequest = """
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        """;

        var request = new HttpRequestMessage(HttpMethod.Post, "/mcp")
        {
            Content = new StringContent(initializeRequest, Encoding.UTF8, "application/json")
        };
        // MCP Streamable HTTP requires Accept header with both JSON and SSE
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("text/event-stream"));

        // Act
        var response = await _client.SendAsync(request);

        // Assert — the MCP SDK should accept the initialize request
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadAsStringAsync();
        body.Should().Contain("serverInfo");
    }

    [Fact]
    public async Task McpEndpoint_GetWithoutAcceptHeader_ReturnsNotAcceptable()
    {
        // A GET without proper Accept headers should be rejected by the MCP SDK
        var response = await _client.GetAsync("/mcp");

        // The SDK returns 406 Not Acceptable when required headers are missing
        response.StatusCode.Should().Be(HttpStatusCode.NotAcceptable);
    }
}

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
using System.Text.Json;
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

    [Fact]
    public async Task McpEndpoint_ToolsCall_GetWeather_ReturnsWeatherData()
    {
        // Step 1: Initialize the MCP session
        var initRequest = CreateMcpRequest("""
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": { "name": "test-client", "version": "1.0.0" }
            }
        }
        """);

        var initResponse = await _client.SendAsync(initRequest);
        initResponse.StatusCode.Should().Be(HttpStatusCode.OK);

        // Extract the Mcp-Session-Id header for subsequent requests
        var sessionId = initResponse.Headers.TryGetValues("Mcp-Session-Id", out var values)
            ? values.First()
            : null;

        // Step 2: Call tools/call with getWeather
        var callRequest = CreateMcpRequest("""
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "getWeather",
                "arguments": {
                    "latitude": 40.71,
                    "longitude": -74.01
                }
            }
        }
        """);

        if (sessionId is not null)
            callRequest.Headers.Add("Mcp-Session-Id", sessionId);

        var callResponse = await _client.SendAsync(callRequest);

        // Assert — the tool should return weather data from the fake handler
        callResponse.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await callResponse.Content.ReadAsStringAsync();
        body.Should().Contain("temperature_2m");
        body.Should().Contain("America/New_York");
    }

    /// <summary>
    /// Creates an HTTP request with the correct MCP Streamable HTTP headers.
    /// </summary>
    private static HttpRequestMessage CreateMcpRequest(string jsonRpcBody)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, "/mcp")
        {
            Content = new StringContent(jsonRpcBody, Encoding.UTF8, "application/json")
        };
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("text/event-stream"));
        return request;
    }
}

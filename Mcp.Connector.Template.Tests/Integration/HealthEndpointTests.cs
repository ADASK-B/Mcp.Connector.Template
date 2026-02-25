// -----------------------------------------------------------------------
// HealthEndpointTests.cs — Integration test for the /health endpoint.
//
// Uses WebApplicationFactory to spin up the full ASP.NET Core pipeline
// in-memory and verify the health probe returns HTTP 200.
// -----------------------------------------------------------------------

using System.Net;
using FluentAssertions;
using Mcp.Connector.Template.Tests.TestInfrastructure;

namespace Mcp.Connector.Template.Tests.Integration;

public class HealthEndpointTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;

    public HealthEndpointTests(CustomWebApplicationFactory factory)
        => _client = factory.CreateClient();

    [Fact]
    public async Task Health_ReturnsOkWithStatusField()
    {
        // Act
        var response = await _client.GetAsync("/health");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = await response.Content.ReadAsStringAsync();
        body.Should().Contain("healthy");
        body.Should().Contain("timestamp");
    }
}

using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FluentAssertions;
using Mcp.Connector.Template.Models;
using Mcp.Connector.Template.Tests.TestInfrastructure;

namespace Mcp.Connector.Template.Tests.Integration;

public class LifecycleEndpointTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;

    public LifecycleEndpointTests(CustomWebApplicationFactory factory)
        => _client = factory.CreateClient();

    [Fact]
    public async Task Healthz_ReturnsExactProcessHealthResponse()
    {
        var response = await _client.GetAsync("/healthz");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<HealthStatusResponse>();
        body.Should().Be(new HealthStatusResponse("healthy"));
    }

    [Fact]
    public async Task Readyz_ReturnsExactTrafficReadinessResponse()
    {
        var response = await _client.GetAsync("/readyz");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<HealthStatusResponse>();
        body.Should().Be(new HealthStatusResponse("ready"));
    }

    [Fact]
    public async Task Version_ReturnsExactEmbeddedReleaseIdentity()
    {
        var response = await _client.GetAsync("/version");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<ApplicationVersionResponse>();
        body.Should().Be(new ApplicationVersionResponse("mcp-connector-reference", "1.0.4"));

        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        document.RootElement.EnumerateObject().Select(property => property.Name)
            .Should().Equal("applicationId", "releaseVersion");
    }

    [Fact]
    public async Task LegacyHealthEndpoint_IsNotExposed()
    {
        var response = await _client.GetAsync("/health");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Theory]
    [InlineData("/healthz")]
    [InlineData("/readyz")]
    [InlineData("/version")]
    public async Task LifecycleEndpoints_RejectPost(string path)
    {
        var response = await _client.PostAsync(path, content: null);

        response.StatusCode.Should().Be(HttpStatusCode.MethodNotAllowed);
    }
}

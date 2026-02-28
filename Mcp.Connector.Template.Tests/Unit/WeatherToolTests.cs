// -----------------------------------------------------------------------
// WeatherToolTests.cs — Unit tests for the WeatherTool MCP tool.
//
// Tests cover:
//   • Valid coordinates → correct JSON result from API
//   • Boundary values → edge-case coordinates are accepted
//   • API failure → error JSON instead of unhandled exception
//   • Input validation → invalid coordinates throw McpException
// -----------------------------------------------------------------------

using System.Text.Json;
using FluentAssertions;
using Mcp.Connector.Template.Models;
using Mcp.Connector.Template.Services;
using Mcp.Connector.Template.Tests.TestInfrastructure;
using Mcp.Connector.Template.Tools;
using ModelContextProtocol;

namespace Mcp.Connector.Template.Tests.Unit;

public class WeatherToolTests
{
    private static OpenMeteoService CreateService(FakeOpenMeteoHandler handler)
    {
        var httpClient = new HttpClient(handler)
        {
            BaseAddress = new Uri("https://api.open-meteo.com")
        };
        return new OpenMeteoService(httpClient);
    }

    // -----------------------------------------------------------------------
    //  Happy path
    // -----------------------------------------------------------------------

    [Fact]
    public async Task GetWeather_ValidCoordinates_ReturnsWeatherResult()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var json = await WeatherTool.GetWeather(service, 40.71, -74.01, CancellationToken.None);

        var result = JsonSerializer.Deserialize<OpenMeteoResponse>(json);
        result.Should().NotBeNull();
        result!.Current.Temperature.Should().Be(5.2);
        result.Current.WindSpeedKmh.Should().Be(12.3);
        result.Current.RelativeHumidityPercent.Should().Be(65);
        result.Timezone.Should().Be("America/New_York");
    }

    // -----------------------------------------------------------------------
    //  API failure
    // -----------------------------------------------------------------------

    [Fact]
    public async Task GetWeather_ApiReturnsServerError_ReturnsErrorJson()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithServerError());

        var json = await WeatherTool.GetWeather(service, 40.71, -74.01, CancellationToken.None);

        json.Should().Contain("error");
        json.Should().Contain("Failed to fetch weather data");
    }

    // -----------------------------------------------------------------------
    //  Boundary values — valid edge-case coordinates must be accepted
    // -----------------------------------------------------------------------

    [Theory]
    [InlineData(-90, -180)]
    [InlineData(90, 180)]
    [InlineData(0, 0)]
    [InlineData(-90, 0)]
    [InlineData(0, 180)]
    public async Task GetWeather_BoundaryCoordinates_DoesNotThrow(double latitude, double longitude)
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var json = await WeatherTool.GetWeather(service, latitude, longitude, CancellationToken.None);

        json.Should().NotBeNullOrWhiteSpace();
    }

    // -----------------------------------------------------------------------
    //  Input validation
    // -----------------------------------------------------------------------

    [Theory]
    [InlineData(-91)]
    [InlineData(91)]
    [InlineData(double.NaN)]
    [InlineData(double.PositiveInfinity)]
    public async Task GetWeather_InvalidLatitude_ThrowsMcpException(double latitude)
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var act = () => WeatherTool.GetWeather(service, latitude, 13.41, CancellationToken.None);

        await act.Should().ThrowAsync<McpException>();
    }

    [Theory]
    [InlineData(-181)]
    [InlineData(181)]
    [InlineData(double.NaN)]
    [InlineData(double.NegativeInfinity)]
    public async Task GetWeather_InvalidLongitude_ThrowsMcpException(double longitude)
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var act = () => WeatherTool.GetWeather(service, 52.52, longitude, CancellationToken.None);

        await act.Should().ThrowAsync<McpException>();
    }
}

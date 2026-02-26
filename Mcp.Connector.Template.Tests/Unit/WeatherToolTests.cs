// -----------------------------------------------------------------------
// WeatherToolTests.cs — Unit tests for the WeatherTool MCP tool.
//
// Tests cover:
//   • Valid coordinates → correct JSON result from API
//   • API failure → error JSON instead of unhandled exception
// -----------------------------------------------------------------------

using System.Text.Json;
using FluentAssertions;
using Mcp.Connector.Template.Models;
using Mcp.Connector.Template.Services;
using Mcp.Connector.Template.Tests.TestInfrastructure;
using Mcp.Connector.Template.Tools;

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
}

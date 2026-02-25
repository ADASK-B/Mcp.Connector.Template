// -----------------------------------------------------------------------
// WeatherToolTests.cs — Unit tests for the WeatherTool MCP tool.
//
// Tests cover:
//   • Valid city → correct JSON result with temperature conversion
//   • Case-insensitive city lookup
//   • Null / empty / whitespace input → ArgumentException
//   • Input too long → McpException
//   • Unknown city → error JSON with list of supported cities
//   • API failure → error JSON instead of unhandled exception
// -----------------------------------------------------------------------

using System.Net;
using System.Text.Json;
using FluentAssertions;
using ModelContextProtocol;
using Mcp.Connector.Template.Models;
using Mcp.Connector.Template.Services;
using Mcp.Connector.Template.Tests.TestInfrastructure;
using Mcp.Connector.Template.Tools;

namespace Mcp.Connector.Template.Tests.Unit;

public class WeatherToolTests
{
    // -- Helper: create an OpenMeteoService backed by a fake handler -----------

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
    public async Task GetWeather_ValidCity_ReturnsWeatherResult()
    {
        // Arrange — fake API returns 5.2 °C for New York
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        // Act
        var json = await WeatherTool.GetWeather(service, "New York", CancellationToken.None);

        // Assert — deserialize and check key fields
        var result = JsonSerializer.Deserialize<WeatherResult>(json);
        result.Should().NotBeNull();
        result!.City.Should().Be("New York");
        result.TemperatureCelsius.Should().Be(5.2);
        result.TemperatureFahrenheit.Should().Be(41.4); // 5.2 * 9/5 + 32 = 41.36 → 41.4
        result.HumidityPercent.Should().Be(65);
        result.WindSpeedKmh.Should().Be(12.3);
        result.Timezone.Should().Be("America/New_York");
    }

    [Fact]
    public async Task GetWeather_CityNameIsCaseInsensitive()
    {
        // Arrange
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        // Act
        var json = await WeatherTool.GetWeather(service, "new york", CancellationToken.None);

        // Assert
        var result = JsonSerializer.Deserialize<WeatherResult>(json);
        result.Should().NotBeNull();
        result!.City.Should().Be("new york");
    }

    // -----------------------------------------------------------------------
    //  Input validation
    // -----------------------------------------------------------------------

    [Fact]
    public async Task GetWeather_NullCity_ThrowsArgumentException()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var act = () => WeatherTool.GetWeather(service, null!, CancellationToken.None);

        await act.Should().ThrowAsync<ArgumentException>();
    }

    [Fact]
    public async Task GetWeather_EmptyCity_ThrowsArgumentException()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var act = () => WeatherTool.GetWeather(service, "", CancellationToken.None);

        await act.Should().ThrowAsync<ArgumentException>();
    }

    [Fact]
    public async Task GetWeather_WhitespaceCity_ThrowsArgumentException()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var act = () => WeatherTool.GetWeather(service, "   ", CancellationToken.None);

        await act.Should().ThrowAsync<ArgumentException>();
    }

    [Fact]
    public async Task GetWeather_CityNameTooLong_ThrowsMcpException()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());
        var longCity = new string('x', 101);

        var act = () => WeatherTool.GetWeather(service, longCity, CancellationToken.None);

        await act.Should().ThrowAsync<McpException>();
    }

    // -----------------------------------------------------------------------
    //  Unknown city
    // -----------------------------------------------------------------------

    [Fact]
    public async Task GetWeather_UnknownCity_ReturnsErrorJsonWithSupportedCities()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        var json = await WeatherTool.GetWeather(service, "Atlantis", CancellationToken.None);

        json.Should().Contain("error");
        json.Should().Contain("Unknown city");
        json.Should().Contain("New York");  // lists supported cities
    }

    // -----------------------------------------------------------------------
    //  API failure
    // -----------------------------------------------------------------------

    [Fact]
    public async Task GetWeather_ApiReturnsServerError_ReturnsErrorJson()
    {
        var service = CreateService(FakeOpenMeteoHandler.WithServerError());

        var json = await WeatherTool.GetWeather(service, "New York", CancellationToken.None);

        json.Should().Contain("error");
        json.Should().Contain("Failed to fetch weather data");
    }
}

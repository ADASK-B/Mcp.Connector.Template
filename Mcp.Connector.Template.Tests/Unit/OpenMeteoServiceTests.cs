// -----------------------------------------------------------------------
// OpenMeteoServiceTests.cs — Unit tests for the OpenMeteoService.
//
// Tests cover:
//   • Successful API response → correct deserialization of all fields
//   • API server error → HttpRequestException is thrown
//   • Null response body → InvalidOperationException is thrown
// -----------------------------------------------------------------------

using System.Net;
using FluentAssertions;
using Mcp.Connector.Template.Services;
using Mcp.Connector.Template.Tests.TestInfrastructure;

namespace Mcp.Connector.Template.Tests.Unit;

public class OpenMeteoServiceTests
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
    public async Task GetCurrentWeatherAsync_SuccessResponse_ReturnsDeserializedResult()
    {
        // Arrange
        var service = CreateService(FakeOpenMeteoHandler.WithSuccessResponse());

        // Act
        var result = await service.GetCurrentWeatherAsync(40.71, -74.01, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Timezone.Should().Be("America/New_York");
        result.Current.TemperatureCelsius.Should().Be(5.2);
        result.Current.WindSpeedKmh.Should().Be(12.3);
        result.Current.RelativeHumidityPercent.Should().Be(65);
        result.CurrentUnits.Temperature.Should().Be("°C");
    }

    // -----------------------------------------------------------------------
    //  Error handling
    // -----------------------------------------------------------------------

    [Fact]
    public async Task GetCurrentWeatherAsync_ServerError_ThrowsHttpRequestException()
    {
        // Arrange
        var service = CreateService(FakeOpenMeteoHandler.WithServerError());

        // Act & Assert
        var act = () => service.GetCurrentWeatherAsync(40.71, -74.01, CancellationToken.None);
        await act.Should().ThrowAsync<HttpRequestException>();
    }

    [Fact]
    public async Task GetCurrentWeatherAsync_NullResponseBody_ThrowsInvalidOperationException()
    {
        // Arrange — return valid HTTP 200 but with "null" as body
        var handler = new FakeOpenMeteoHandler(HttpStatusCode.OK, "null");
        var service = CreateService(handler);

        // Act & Assert
        var act = () => service.GetCurrentWeatherAsync(40.71, -74.01, CancellationToken.None);
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*null*");
    }
}

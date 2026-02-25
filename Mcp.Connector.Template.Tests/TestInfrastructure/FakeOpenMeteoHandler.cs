// -----------------------------------------------------------------------
// FakeOpenMeteoHandler.cs — Mock HTTP handler for the Open-Meteo API.
//
// Used in both unit and integration tests to intercept HTTP calls and
// return predefined responses. No real network calls are made in tests.
// -----------------------------------------------------------------------

using System.Net;
using System.Text;

namespace Mcp.Connector.Template.Tests.TestInfrastructure;

/// <summary>
/// A fake HttpMessageHandler that returns a configurable response.
/// Simulates the Open-Meteo API without making real HTTP calls.
/// </summary>
public class FakeOpenMeteoHandler : HttpMessageHandler
{
    private readonly HttpStatusCode _statusCode;
    private readonly string _responseBody;

    /// <summary>
    /// Creates a handler that always returns the given status code and body.
    /// </summary>
    public FakeOpenMeteoHandler(HttpStatusCode statusCode, string responseBody)
    {
        _statusCode = statusCode;
        _responseBody = responseBody;
    }

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        var response = new HttpResponseMessage(_statusCode)
        {
            Content = new StringContent(_responseBody, Encoding.UTF8, "application/json")
        };

        return Task.FromResult(response);
    }

    // -- Factory methods for common test scenarios ----------------------------

    /// <summary>
    /// Returns a handler that simulates a successful weather response for New York.
    /// Temperature: 5.2 °C, Wind: 12.3 km/h, Humidity: 65%.
    /// </summary>
    public static FakeOpenMeteoHandler WithSuccessResponse() =>
        new(HttpStatusCode.OK, """
        {
            "latitude": 40.71,
            "longitude": -74.01,
            "timezone": "America/New_York",
            "current": {
                "time": "2026-02-25T12:00",
                "temperature_2m": 5.2,
                "wind_speed_10m": 12.3,
                "relative_humidity_2m": 65
            },
            "current_units": {
                "temperature_2m": "°C",
                "wind_speed_10m": "km/h",
                "relative_humidity_2m": "%"
            }
        }
        """);

    /// <summary>
    /// Returns a handler that simulates an API server error (500).
    /// </summary>
    public static FakeOpenMeteoHandler WithServerError() =>
        new(HttpStatusCode.InternalServerError, """{"reason": "service unavailable"}""");
}

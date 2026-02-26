// -----------------------------------------------------------------------
// OpenMeteoService.cs — HTTP client wrapper for the Open-Meteo weather API.
//
// This service is registered via IHttpClientFactory in Program.cs and
// injected into MCP tool methods as a method parameter.
//
// Open-Meteo is free and requires no API key.
// Docs: https://open-meteo.com/en/docs
// -----------------------------------------------------------------------

using System.Globalization;
using Mcp.Connector.Template.Models;

namespace Mcp.Connector.Template.Services;

/// <summary>
/// Wraps the Open-Meteo REST API to fetch current weather data.
/// </summary>
public class OpenMeteoService
{
    private readonly HttpClient _httpClient;

    public OpenMeteoService(HttpClient httpClient)
    {
        _httpClient = httpClient;

        // Set the base address once; IHttpClientFactory may reuse the handler.
        _httpClient.BaseAddress ??= new Uri("https://api.open-meteo.com");
        _httpClient.Timeout = TimeSpan.FromSeconds(10);
    }

    /// <summary>
    /// Fetches the current weather for the given coordinates.
    /// </summary>
    /// <param name="latitude">Latitude in decimal degrees (e.g. 40.7143 for New York).</param>
    /// <param name="longitude">Longitude in decimal degrees (e.g. -74.006 for New York).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The deserialized Open-Meteo API response.</returns>
    public async Task<OpenMeteoResponse> GetCurrentWeatherAsync(
        double latitude,
        double longitude,
        CancellationToken cancellationToken)
    {
        // Build the query — request current temperature, wind speed, and humidity.
        // Use InvariantCulture to ensure decimal dots (not commas) in the URL.
        var lat = latitude.ToString(CultureInfo.InvariantCulture);
        var lon = longitude.ToString(CultureInfo.InvariantCulture);
        var url = $"/v1/forecast?latitude={lat}&longitude={lon}"
                + "&current=temperature_2m,wind_speed_10m,relative_humidity_2m"
                + "&timezone=auto";

        var response = await _httpClient.GetAsync(url, cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadFromJsonAsync<OpenMeteoResponse>(cancellationToken)
            ?? throw new InvalidOperationException("Open-Meteo API returned a null response.");
    }
}

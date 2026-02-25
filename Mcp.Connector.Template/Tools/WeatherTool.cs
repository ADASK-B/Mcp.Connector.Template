// -----------------------------------------------------------------------
// WeatherTool.cs — MCP tool that wraps the Open-Meteo weather API.
//
// This is the core example of the MCP Connector Template. It demonstrates:
//   • [McpServerToolType] / [McpServerTool] attributes for auto-discovery
//   • Method-level dependency injection (OpenMeteoService)
//   • Input validation with ArgumentException and McpException
//   • City-to-coordinates lookup (simple dictionary)
//   • Error handling that returns user-friendly JSON instead of raw exceptions
//   • CancellationToken forwarding
//
// The SDK auto-discovers this class via WithToolsFromAssembly() — no manual
// registration or routing is needed.
// -----------------------------------------------------------------------

using System.ComponentModel;
using System.Text.Json;
using ModelContextProtocol;
using ModelContextProtocol.Server;
using Mcp.Connector.Template.Models;
using Mcp.Connector.Template.Services;

namespace Mcp.Connector.Template.Tools;

/// <summary>
/// MCP tool that provides current weather data for a given city.
/// </summary>
[McpServerToolType]
public static class WeatherTool
{
    // -- Known cities with their coordinates ------------------------------------
    // In a real connector you would call a geocoding API instead.
    private static readonly Dictionary<string, (double Lat, double Lon)> KnownCities =
        new(StringComparer.OrdinalIgnoreCase)
        {
            ["New York"]  = (40.7143, -74.0060),
            ["London"]    = (51.5074,  -0.1278),
            ["Berlin"]    = (52.5200,  13.4050),
            ["Tokyo"]     = (35.6762, 139.6503),
            ["Sydney"]    = (-33.8688, 151.2093),
            ["Paris"]     = (48.8566,   2.3522),
            ["Vienna"]    = (48.2082,  16.3738),
            ["Zurich"]    = (47.3769,   8.5417),
        };

    /// <summary>
    /// Maximum allowed length for the city name parameter.
    /// </summary>
    private const int MaxCityNameLength = 100;

    // -----------------------------------------------------------------------
    //  MCP Tool: getWeather
    // -----------------------------------------------------------------------

    [McpServerTool(Name = "getWeather")]
    [Description(
        "Returns the current weather for a city. " +
        "Supported cities: New York, London, Berlin, Tokyo, Sydney, Paris, Vienna, Zurich. " +
        "The response includes temperature (Celsius and Fahrenheit), humidity, wind speed, and timezone.")]
    public static async Task<string> GetWeather(
        OpenMeteoService weatherService,
        [Description("City name, e.g. 'New York', 'London', 'Berlin'. Case-insensitive.")] string city,
        CancellationToken cancellationToken)
    {
        // 1. Validate: city must not be null or empty
        ArgumentException.ThrowIfNullOrWhiteSpace(city);

        // 2. Validate: city must not exceed maximum length
        if (city.Length > MaxCityNameLength)
        {
            throw new McpException(
                $"City name exceeds the maximum length of {MaxCityNameLength} characters.");
        }

        // 3. Look up coordinates for the requested city
        if (!KnownCities.TryGetValue(city.Trim(), out var coordinates))
        {
            var supported = string.Join(", ", KnownCities.Keys.Order());
            return JsonSerializer.Serialize(new
            {
                error = $"Unknown city '{city}'. Supported cities: {supported}"
            });
        }

        // 4. Call the Open-Meteo API via the injected service
        try
        {
            var apiResponse = await weatherService.GetCurrentWeatherAsync(
                coordinates.Lat, coordinates.Lon, cancellationToken);

            // 5. Map the API response to a clean result DTO
            var result = new WeatherResult(
                City: city.Trim(),
                TemperatureCelsius: apiResponse.Current.TemperatureCelsius,
                TemperatureFahrenheit: Math.Round(apiResponse.Current.TemperatureCelsius * 9.0 / 5.0 + 32.0, 1),
                HumidityPercent: apiResponse.Current.RelativeHumidityPercent,
                WindSpeedKmh: apiResponse.Current.WindSpeedKmh,
                Timezone: apiResponse.Timezone,
                MeasuredAt: apiResponse.Current.Time);

            // 6. Serialize and return — the SDK wraps this in an MCP TextContent block
            return JsonSerializer.Serialize(result);
        }
        catch (HttpRequestException ex)
        {
            // Return a user-friendly error instead of letting the exception bubble up
            return JsonSerializer.Serialize(new
            {
                error = $"Failed to fetch weather data: {ex.Message}"
            });
        }
    }
}

// -----------------------------------------------------------------------
// WeatherTool.cs — MCP tool that wraps the Open-Meteo weather API.
//
// Demonstrates:
//   • [McpServerToolType] / [McpServerTool] attributes for auto-discovery
//   • Method-level dependency injection (OpenMeteoService)
//   • Error handling that returns user-friendly JSON
//   • CancellationToken forwarding
//
// The SDK auto-discovers this class via WithToolsFromAssembly().
// -----------------------------------------------------------------------

using System.ComponentModel;
using System.Text.Json;
using ModelContextProtocol;
using ModelContextProtocol.Server;
using Mcp.Connector.Template.Services;

namespace Mcp.Connector.Template.Tools;

/// <summary>
/// MCP tool that provides current weather data for given coordinates.
/// </summary>
[McpServerToolType]
public static class WeatherTool
{
    [McpServerTool(Name = "getWeather")]
    [Description(
        "Returns the current weather for a location. " +
        "Provide latitude and longitude as decimal degrees. " +
        "The response includes temperature, humidity, wind speed, timezone, and units.")]
    public static async Task<string> GetWeather(
        OpenMeteoService weatherService,
        [Description("Latitude in decimal degrees, e.g. 52.52 for Berlin. Must be between -90 and 90.")] double latitude,
        [Description("Longitude in decimal degrees, e.g. 13.41 for Berlin. Must be between -180 and 180.")] double longitude,
        CancellationToken cancellationToken)
    {
        if (double.IsNaN(latitude) || double.IsInfinity(latitude) || latitude < -90 || latitude > 90)
            throw new McpException($"Latitude must be between -90 and 90, got {latitude}.");

        if (double.IsNaN(longitude) || double.IsInfinity(longitude) || longitude < -180 || longitude > 180)
            throw new McpException($"Longitude must be between -180 and 180, got {longitude}.");

        try
        {
            var response = await weatherService.GetCurrentWeatherAsync(
                latitude, longitude, cancellationToken);

            return JsonSerializer.Serialize(response);
        }
        catch (HttpRequestException ex)
        {
            return JsonSerializer.Serialize(new { error = $"Failed to fetch weather data: {ex.Message}" });
        }
    }
}

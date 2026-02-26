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
        double latitude,
        double longitude,
        CancellationToken cancellationToken)
    {
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

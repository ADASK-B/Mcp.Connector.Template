// -----------------------------------------------------------------------
// WeatherModels.cs — DTOs for the Open-Meteo weather API and MCP tool result.
//
// Two layers of models:
//   1. API response records  — match the JSON shape from api.open-meteo.com
//   2. Tool result record    — simplified shape returned to the MCP client (LLM)
// -----------------------------------------------------------------------

using System.Text.Json.Serialization;

namespace Mcp.Connector.Template.Models;

// ---------------------------------------------------------------------------
//  Open-Meteo API response DTOs
//  Docs: https://open-meteo.com/en/docs
// ---------------------------------------------------------------------------

/// <summary>
/// Top-level response from the Open-Meteo /v1/forecast endpoint.
/// </summary>
public record OpenMeteoResponse(
    [property: JsonPropertyName("latitude")] double Latitude,
    [property: JsonPropertyName("longitude")] double Longitude,
    [property: JsonPropertyName("timezone")] string Timezone,
    [property: JsonPropertyName("current")] OpenMeteoCurrent Current,
    [property: JsonPropertyName("current_units")] OpenMeteoCurrentUnits CurrentUnits);

/// <summary>
/// The "current" block containing live weather measurements.
/// </summary>
public record OpenMeteoCurrent(
    [property: JsonPropertyName("time")] string Time,
    [property: JsonPropertyName("temperature_2m")] double TemperatureCelsius,
    [property: JsonPropertyName("wind_speed_10m")] double WindSpeedKmh,
    [property: JsonPropertyName("relative_humidity_2m")] int RelativeHumidityPercent);

/// <summary>
/// Units for each measurement in the "current" block.
/// </summary>
public record OpenMeteoCurrentUnits(
    [property: JsonPropertyName("temperature_2m")] string Temperature,
    [property: JsonPropertyName("wind_speed_10m")] string WindSpeed,
    [property: JsonPropertyName("relative_humidity_2m")] string RelativeHumidity);

// ---------------------------------------------------------------------------
//  MCP tool result DTO — the simplified shape the LLM receives
// ---------------------------------------------------------------------------

/// <summary>
/// Clean weather result returned to the MCP client.
/// Contains only the fields an LLM needs to answer a weather question.
/// </summary>
public record WeatherResult(
    string City,
    double TemperatureCelsius,
    double TemperatureFahrenheit,
    int HumidityPercent,
    double WindSpeedKmh,
    string Timezone,
    string MeasuredAt);

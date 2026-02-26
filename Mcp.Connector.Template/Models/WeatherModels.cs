// -----------------------------------------------------------------------
// WeatherModels.cs — DTOs for the Open-Meteo weather API.
//
// Records match the JSON shape from api.open-meteo.com.
// The tool serializes the API response directly — no intermediate DTO.
// -----------------------------------------------------------------------

using System.Text.Json.Serialization;

namespace Mcp.Connector.Template.Models;

// ---------------------------------------------------------------------------
//  Open-Meteo API response DTOs
//  Docs: https://open-meteo.com/en/docs
// ---------------------------------------------------------------------------

public record OpenMeteoResponse(
    [property: JsonPropertyName("latitude")] double Latitude,
    [property: JsonPropertyName("longitude")] double Longitude,
    [property: JsonPropertyName("timezone")] string Timezone,
    [property: JsonPropertyName("current")] OpenMeteoCurrent Current,
    [property: JsonPropertyName("current_units")] OpenMeteoCurrentUnits CurrentUnits);

public record OpenMeteoCurrent(
    [property: JsonPropertyName("time")] string Time,
    [property: JsonPropertyName("temperature_2m")] double Temperature,
    [property: JsonPropertyName("wind_speed_10m")] double WindSpeedKmh,
    [property: JsonPropertyName("relative_humidity_2m")] int RelativeHumidityPercent);

public record OpenMeteoCurrentUnits(
    [property: JsonPropertyName("temperature_2m")] string Temperature,
    [property: JsonPropertyName("wind_speed_10m")] string WindSpeed,
    [property: JsonPropertyName("relative_humidity_2m")] string RelativeHumidity);

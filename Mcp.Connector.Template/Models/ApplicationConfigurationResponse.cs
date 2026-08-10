using System.Text.Json.Serialization;

namespace Mcp.Connector.Template.Models;

/// <summary>
/// Observable non-sensitive value received through generated configuration.
/// </summary>
public sealed record ApplicationConfigurationResponse(
    [property: JsonPropertyName("message")] string Message);

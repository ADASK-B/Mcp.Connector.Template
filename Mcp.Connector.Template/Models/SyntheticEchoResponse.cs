using System.Text.Json.Serialization;

namespace Mcp.Connector.Template.Models;

/// <summary>
/// Deterministic response returned by the synthetic reference tool.
/// </summary>
public sealed record SyntheticEchoResponse(
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("length")] int Length);

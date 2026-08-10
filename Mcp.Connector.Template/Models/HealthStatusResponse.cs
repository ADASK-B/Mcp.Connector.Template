using System.Text.Json.Serialization;

namespace Mcp.Connector.Template.Models;

/// <summary>
/// Deterministic response returned by the liveness and readiness endpoints.
/// </summary>
public sealed record HealthStatusResponse(
    [property: JsonPropertyName("status")] string Status);

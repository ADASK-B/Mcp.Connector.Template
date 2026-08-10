using System.Text.Json.Serialization;

namespace Mcp.Connector.Template.Models;

/// <summary>
/// Exact runtime identity defined by the ApplicationContract response schema.
/// </summary>
public sealed record ApplicationVersionResponse(
    [property: JsonPropertyName("applicationId")] string ApplicationId,
    [property: JsonPropertyName("releaseVersion")] string ReleaseVersion);

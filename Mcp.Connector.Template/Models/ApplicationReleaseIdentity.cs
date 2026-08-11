using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Mcp.Connector.Template.Models;

/// <summary>
/// Loads the release-owned application identity embedded at build time.
/// </summary>
internal sealed partial record ApplicationReleaseIdentity(
    string ApplicationId,
    string ReleaseVersion)
{
    private const string _resourceName = "Mcp.Connector.Template.release-input.json";
    private const string _releaseInputSchema = "platform.adask-b.io/app-release-input/v1alpha2";
    private const string _artifactClass = "vendor-app";

    public static ApplicationReleaseIdentity Load(Assembly assembly)
    {
        ArgumentNullException.ThrowIfNull(assembly);

        using var stream = assembly.GetManifestResourceStream(_resourceName)
            ?? throw new InvalidOperationException("The embedded release identity is missing.");

        return Parse(stream);
    }

    internal static ApplicationReleaseIdentity Parse(Stream stream)
    {
        ArgumentNullException.ThrowIfNull(stream);

        try
        {
            using var document = JsonDocument.Parse(stream);
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                throw new InvalidOperationException("The embedded release input must be a JSON object.");
            }

            var schemaVersion = ReadUniqueString(root, "schemaVersion");
            var artifactClass = ReadUniqueString(root, "artifactClass");
            var applicationId = ReadUniqueString(root, "name");
            var releaseVersion = ReadUniqueString(root, "version");

            if (!string.Equals(schemaVersion, _releaseInputSchema, StringComparison.Ordinal))
            {
                throw new InvalidOperationException("The embedded release input schema is unsupported.");
            }

            if (!string.Equals(artifactClass, _artifactClass, StringComparison.Ordinal))
            {
                throw new InvalidOperationException("The embedded release artifact class is unsupported.");
            }

            if (!ApplicationIdPattern().IsMatch(applicationId))
            {
                throw new InvalidOperationException("The embedded application identity is invalid.");
            }

            if (!SemanticVersionPattern().IsMatch(releaseVersion))
            {
                throw new InvalidOperationException("The embedded release version is invalid.");
            }

            return new ApplicationReleaseIdentity(applicationId, releaseVersion);
        }
        catch (JsonException exception)
        {
            throw new InvalidOperationException("The embedded release input is invalid JSON.", exception);
        }
    }

    public ApplicationVersionResponse ToResponse() => new(ApplicationId, ReleaseVersion);

    private static string ReadUniqueString(JsonElement root, string propertyName)
    {
        string? value = null;
        var occurrences = 0;

        foreach (var property in root.EnumerateObject())
        {
            if (!property.NameEquals(propertyName))
            {
                continue;
            }

            occurrences++;
            if (property.Value.ValueKind == JsonValueKind.String)
            {
                value = property.Value.GetString();
            }
        }

        if (occurrences != 1 || string.IsNullOrEmpty(value))
        {
            throw new InvalidOperationException(
                $"The embedded release input requires one non-empty {propertyName} string.");
        }

        return value;
    }

    [GeneratedRegex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", RegexOptions.CultureInvariant)]
    private static partial Regex ApplicationIdPattern();

    [GeneratedRegex("^[0-9]+\\.[0-9]+\\.[0-9]+([+-][0-9A-Za-z.-]+)?$", RegexOptions.CultureInvariant)]
    private static partial Regex SemanticVersionPattern();
}

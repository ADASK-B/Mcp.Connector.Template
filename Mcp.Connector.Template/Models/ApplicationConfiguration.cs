using System.Text;
using System.Text.Json;

namespace Mcp.Connector.Template.Models;

/// <summary>
/// Exact non-sensitive application configuration rendered from the canonical
/// resolved setup model and mounted by the release chart.
/// </summary>
internal sealed record ApplicationConfiguration(string Message)
{
    private const string _schemaVersion = "platform.adask-b.io/platform-test-configuration/v1alpha1";
    private const string _filePath = "/etc/adask/platform-test/configuration.json";
    private static readonly HashSet<string> _fields = new(StringComparer.Ordinal)
    {
        "schemaVersion",
        "message",
    };

    public static string FilePath => _filePath;

    internal static ApplicationConfiguration LoadFromFile(string path)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);

        try
        {
            using var stream = File.OpenRead(path);
            return Parse(stream);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            throw new InvalidOperationException(
                "Required setup-derived application configuration is unavailable.",
                exception);
        }
    }

    internal static ApplicationConfiguration Parse(Stream stream)
    {
        ArgumentNullException.ThrowIfNull(stream);

        try
        {
            using var document = JsonDocument.Parse(stream);
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                throw new InvalidOperationException("Application configuration must be a JSON object.");
            }

            foreach (var property in root.EnumerateObject())
            {
                if (!_fields.Contains(property.Name))
                {
                    throw new InvalidOperationException(
                        $"Application configuration contains unsupported field {property.Name}.");
                }
            }

            var schemaVersion = ReadUniqueString(root, "schemaVersion");
            var message = ReadUniqueString(root, "message");
            if (!string.Equals(schemaVersion, _schemaVersion, StringComparison.Ordinal))
            {
                throw new InvalidOperationException("Application configuration schema is unsupported.");
            }

            if (message.EnumerateRunes().Count() > 128)
            {
                throw new InvalidOperationException("Application configuration message exceeds 128 characters.");
            }

            return new ApplicationConfiguration(message);
        }
        catch (JsonException exception)
        {
            throw new InvalidOperationException("Application configuration is invalid JSON.", exception);
        }
    }

    public ApplicationConfigurationResponse ToResponse() => new(Message);

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
                $"Application configuration requires one non-empty {propertyName} string.");
        }

        return value;
    }
}

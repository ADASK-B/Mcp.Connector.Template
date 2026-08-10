using System.ComponentModel;
using System.Text.Json;
using Mcp.Connector.Template.Models;
using ModelContextProtocol;
using ModelContextProtocol.Server;

namespace Mcp.Connector.Template.Tools;

/// <summary>
/// Provides a deterministic, side-effect-free operation for Platform contract tests.
/// </summary>
[McpServerToolType]
public static class SyntheticEchoTool
{
    private const int _maximumMessageLength = 256;

    [McpServerTool(Name = "echoSynthetic")]
    [Description(
        "Returns the supplied synthetic test message and its length without external calls, persistence, or side effects.")]
    public static Task<string> EchoSynthetic(
        [Description("Synthetic test text between 1 and 256 characters; do not provide secrets or personal data.")]
        string message,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(message))
            throw new McpException("Synthetic test message must not be empty or whitespace.");

        if (message.Length > _maximumMessageLength)
            throw new McpException($"Synthetic test message exceeds the maximum length of {_maximumMessageLength} characters.");

        cancellationToken.ThrowIfCancellationRequested();

        var response = new SyntheticEchoResponse(message, message.Length);
        return Task.FromResult(JsonSerializer.Serialize(response));
    }
}

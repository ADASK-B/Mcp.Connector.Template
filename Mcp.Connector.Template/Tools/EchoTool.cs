using System.ComponentModel;
using ModelContextProtocol.Server;

namespace Mcp.Connector.Template.Tools;

/// <summary>
/// Example MCP tool included with the template to verify the connector is reachable.
/// Replace or extend this class when building a real connector.
/// </summary>
[McpServerToolType]
public static class EchoTool
{
    [McpServerTool(Name = "echo"), Description(
        "Echoes the provided message back unchanged. " +
        "Use this tool to verify that the MCP connector is reachable and responding correctly.")]
    public static Task<string> Echo(
        [Description("The message text to echo back. Must not be empty.")] string message)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(message);
        return Task.FromResult(message);
    }
}

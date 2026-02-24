using FluentAssertions;
using Mcp.Connector.Template.Tools;

namespace Mcp.Connector.Template.Tests.Unit;

public class EchoToolTests
{
    [Fact]
    public async Task Echo_ValidMessage_ReturnsMessageUnchanged()
    {
        const string message = "Hello, MCP!";

        var result = await EchoTool.Echo(message);

        result.Should().Be(message);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public async Task Echo_NullOrWhiteSpaceMessage_ThrowsArgumentException(string? message)
    {
        // ArgumentException.ThrowIfNullOrWhiteSpace throws ArgumentNullException for null
        // and ArgumentException for empty/whitespace — both derive from ArgumentException.
        var exception = await Record.ExceptionAsync(() => EchoTool.Echo(message!));

        exception.Should().BeAssignableTo<ArgumentException>();
    }
}


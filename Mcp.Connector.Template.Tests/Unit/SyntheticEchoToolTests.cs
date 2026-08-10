using System.Text.Json;
using FluentAssertions;
using Mcp.Connector.Template.Models;
using Mcp.Connector.Template.Tools;
using ModelContextProtocol;

namespace Mcp.Connector.Template.Tests.Unit;

public class SyntheticEchoToolTests
{
    [Fact]
    public async Task EchoSynthetic_ValidMessage_ReturnsDeterministicResponse()
    {
        const string message = "platform-test-payload";

        var json = await SyntheticEchoTool.EchoSynthetic(message, CancellationToken.None);

        var response = JsonSerializer.Deserialize<SyntheticEchoResponse>(json);
        response.Should().Be(new SyntheticEchoResponse(message, message.Length));
    }

    [Fact]
    public async Task EchoSynthetic_MaximumLengthMessage_IsAccepted()
    {
        var message = new string('x', 256);

        var json = await SyntheticEchoTool.EchoSynthetic(message, CancellationToken.None);

        var response = JsonSerializer.Deserialize<SyntheticEchoResponse>(json);
        response.Should().Be(new SyntheticEchoResponse(message, 256));
    }

    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("\t")]
    public async Task EchoSynthetic_EmptyOrWhitespaceMessage_IsRejected(string message)
    {
        var act = () => SyntheticEchoTool.EchoSynthetic(message, CancellationToken.None);

        await act.Should().ThrowAsync<McpException>()
            .WithMessage("*must not be empty or whitespace*");
    }

    [Fact]
    public async Task EchoSynthetic_OverMaximumLengthMessage_IsRejected()
    {
        var message = new string('x', 257);

        var act = () => SyntheticEchoTool.EchoSynthetic(message, CancellationToken.None);

        await act.Should().ThrowAsync<McpException>()
            .WithMessage("*maximum length of 256*");
    }

    [Fact]
    public async Task EchoSynthetic_CancelledRequest_IsRejected()
    {
        using var cancellationSource = new CancellationTokenSource();
        await cancellationSource.CancelAsync();

        var act = () => SyntheticEchoTool.EchoSynthetic(
            "platform-test-payload",
            cancellationSource.Token);

        await act.Should().ThrowAsync<OperationCanceledException>();
    }
}

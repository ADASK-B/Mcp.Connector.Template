using System.Text;
using FluentAssertions;
using Mcp.Connector.Template.Models;

namespace Mcp.Connector.Template.Tests.Unit;

public class ApplicationConfigurationTests
{
    [Fact]
    public void Parse_AcceptsExactSupportedConfiguration()
    {
        using var stream = JsonStream(ValidJson("setup-derived-message"));

        var configuration = ApplicationConfiguration.Parse(stream);

        configuration.ToResponse().Should()
            .Be(new ApplicationConfigurationResponse("setup-derived-message"));
    }

    [Fact]
    public void Parse_PreservesExactWhitespace()
    {
        using var stream = JsonStream(ValidJson(" exact value "));

        var configuration = ApplicationConfiguration.Parse(stream);

        configuration.Message.Should().Be(" exact value ");
    }

    [Theory]
    [InlineData("{}")]
    [InlineData("{\"schemaVersion\":\"platform.adask-b.io/platform-test-configuration/v1alpha1\"}")]
    [InlineData("{\"schemaVersion\":\"unsupported/v1\",\"message\":\"value\"}")]
    [InlineData("{\"schemaVersion\":\"platform.adask-b.io/platform-test-configuration/v1alpha1\",\"message\":42}")]
    [InlineData("{\"schemaVersion\":\"platform.adask-b.io/platform-test-configuration/v1alpha1\",\"message\":\"\"}")]
    [InlineData("{\"schemaVersion\":\"platform.adask-b.io/platform-test-configuration/v1alpha1\",\"message\":\"value\",\"other\":true}")]
    public void Parse_RejectsMissingUnsupportedOrWrongTypedConfiguration(string json)
    {
        using var stream = JsonStream(json);

        var action = () => ApplicationConfiguration.Parse(stream);

        action.Should().Throw<InvalidOperationException>();
    }

    [Fact]
    public void Parse_RejectsDuplicateMessage()
    {
        using var stream = JsonStream(
            """
            {
              "schemaVersion": "platform.adask-b.io/platform-test-configuration/v1alpha1",
              "message": "one",
              "message": "two"
            }
            """);

        var action = () => ApplicationConfiguration.Parse(stream);

        action.Should().Throw<InvalidOperationException>();
    }

    [Fact]
    public void Parse_RejectsMessageOverReleaseLimit()
    {
        using var stream = JsonStream(ValidJson(new string('a', 129)));

        var action = () => ApplicationConfiguration.Parse(stream);

        action.Should().Throw<InvalidOperationException>()
            .WithMessage("*exceeds 128 characters*");
    }

    [Fact]
    public void Parse_CountsUnicodeCodePointsLikeTheCanonicalResolver()
    {
        using var accepted = JsonStream(ValidJson(string.Concat(Enumerable.Repeat("😀", 128))));
        using var rejected = JsonStream(ValidJson(string.Concat(Enumerable.Repeat("😀", 129))));

        ApplicationConfiguration.Parse(accepted).Message.EnumerateRunes().Count().Should().Be(128);
        var action = () => ApplicationConfiguration.Parse(rejected);

        action.Should().Throw<InvalidOperationException>()
            .WithMessage("*exceeds 128 characters*");
    }

    [Fact]
    public void Parse_RejectsMalformedJson()
    {
        using var stream = JsonStream("{");

        var action = () => ApplicationConfiguration.Parse(stream);

        action.Should().Throw<InvalidOperationException>()
            .WithMessage("*invalid JSON*");
    }

    [Fact]
    public void LoadFromFile_RejectsMissingGeneratedFile()
    {
        var missingPath = Path.Combine(
            Path.GetTempPath(),
            $"missing-platform-test-config-{Guid.NewGuid():N}.json");

        var action = () => ApplicationConfiguration.LoadFromFile(missingPath);

        action.Should().Throw<InvalidOperationException>()
            .WithMessage("*setup-derived application configuration is unavailable*");
    }

    private static MemoryStream JsonStream(string json) => new(Encoding.UTF8.GetBytes(json));

    private static string ValidJson(string message) =>
        $$"""
        {
          "schemaVersion": "platform.adask-b.io/platform-test-configuration/v1alpha1",
          "message": {{System.Text.Json.JsonSerializer.Serialize(message)}}
        }
        """;
}

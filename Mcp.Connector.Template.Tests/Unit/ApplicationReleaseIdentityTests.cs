using System.Text;
using FluentAssertions;
using Mcp.Connector.Template.Models;

namespace Mcp.Connector.Template.Tests.Unit;

public class ApplicationReleaseIdentityTests
{
    [Fact]
    public void Parse_AcceptsExactSupportedReleaseIdentity()
    {
        using var stream = JsonStream(
            """
            {
              "schemaVersion": "platform.adask-b.io/app-release-input/v1alpha2",
              "artifactClass": "vendor-app",
              "name": "platform-test-app",
              "version": "1.1.1",
              "publisher": {}
            }
            """);

        var identity = ApplicationReleaseIdentity.Parse(stream);

        identity.ToResponse().Should()
            .Be(new ApplicationVersionResponse("platform-test-app", "1.1.1"));
    }

    [Theory]
    [InlineData("schemaVersion", "platform.adask-b.io/app-release-input/v1alpha2", "unknown/v1")]
    [InlineData("artifactClass", "vendor-app", "foundation")]
    [InlineData("name", "platform-test-app", "Invalid_Name")]
    [InlineData("version", "1.1.1", "latest")]
    public void Parse_RejectsUnsupportedOrInvalidIdentity(
        string propertyName,
        string expected,
        string replacement)
    {
        var json = ValidJson().Replace(
            $"\"{propertyName}\": \"{expected}\"",
            $"\"{propertyName}\": \"{replacement}\"",
            StringComparison.Ordinal);
        using var stream = JsonStream(json);

        var action = () => ApplicationReleaseIdentity.Parse(stream);

        action.Should().Throw<InvalidOperationException>();
    }

    [Fact]
    public void Parse_RejectsMissingIdentityField()
    {
        using var stream = JsonStream(
            ValidJson().Replace("  \"name\": \"platform-test-app\",\n", string.Empty, StringComparison.Ordinal));

        var action = () => ApplicationReleaseIdentity.Parse(stream);

        action.Should().Throw<InvalidOperationException>();
    }

    [Fact]
    public void Parse_RejectsDuplicateIdentityField()
    {
        using var stream = JsonStream(
            ValidJson().Replace(
                "  \"version\": \"1.1.1\"",
                "  \"version\": \"1.1.1\",\n  \"version\": \"1.1.2\"",
                StringComparison.Ordinal));

        var action = () => ApplicationReleaseIdentity.Parse(stream);

        action.Should().Throw<InvalidOperationException>();
    }

    [Fact]
    public void Parse_RejectsMalformedJson()
    {
        using var stream = JsonStream("{");

        var action = () => ApplicationReleaseIdentity.Parse(stream);

        action.Should().Throw<InvalidOperationException>()
            .WithMessage("*invalid JSON*");
    }

    private static MemoryStream JsonStream(string json) => new(Encoding.UTF8.GetBytes(json));

    private static string ValidJson() =>
        """
        {
          "schemaVersion": "platform.adask-b.io/app-release-input/v1alpha2",
          "artifactClass": "vendor-app",
          "name": "platform-test-app",
          "version": "1.1.1"
        }
        """;
}

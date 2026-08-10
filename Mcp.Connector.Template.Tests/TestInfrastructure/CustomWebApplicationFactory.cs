// -----------------------------------------------------------------------
// CustomWebApplicationFactory.cs — In-memory test host for integration tests.
//
// The production host requires one generated configuration file. Integration
// tests replace only that file-backed source with an exact synthetic value.
// -----------------------------------------------------------------------

using Mcp.Connector.Template.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace Mcp.Connector.Template.Tests.TestInfrastructure;

/// <summary>
/// Spins up the complete Platform Test Application in memory.
/// </summary>
public class CustomWebApplicationFactory : WebApplicationFactory<Program>
{
    public const string ConfigurationMessage = "integration-test-message";

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureTestServices(services =>
        {
            services.RemoveAll<ApplicationConfiguration>();
            services.AddSingleton(new ApplicationConfiguration(ConfigurationMessage));
        });
    }
}

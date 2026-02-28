// -----------------------------------------------------------------------
// CustomWebApplicationFactory.cs — In-memory test host for integration tests.
//
// Replaces the real OpenMeteoService HTTP handler with FakeOpenMeteoHandler
// so that integration tests never make real network calls.
// -----------------------------------------------------------------------

using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Mcp.Connector.Template.Services;

namespace Mcp.Connector.Template.Tests.TestInfrastructure;

/// <summary>
/// Custom WebApplicationFactory that mocks external HTTP dependencies.
/// Used by integration tests to spin up the full ASP.NET Core pipeline in-memory.
/// </summary>
public class CustomWebApplicationFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Replace the OpenMeteoService's HttpClient handler with a fake.
            // This ensures zero real HTTP calls during integration tests.
            // We must also configure BaseAddress and Timeout to match Program.cs,
            // otherwise GetAsync with relative URLs will fail.
            services.AddHttpClient<OpenMeteoService>(client =>
                {
                    client.BaseAddress = new Uri("https://api.open-meteo.com");
                    client.Timeout = TimeSpan.FromSeconds(10);
                })
                .ConfigurePrimaryHttpMessageHandler(() => FakeOpenMeteoHandler.WithSuccessResponse());
        });
    }
}

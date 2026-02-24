using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;

namespace Mcp.Connector.Template.Tests.TestInfrastructure;

/// <summary>
/// In-memory ASP.NET Core host for integration tests.
/// Override <see cref="ConfigureWebHost"/> to register mock services
/// (e.g. fake <see cref="System.Net.Http.HttpMessageHandler"/> implementations
/// that intercept outbound HTTP calls to external APIs).
/// </summary>
public class CustomWebApplicationFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");

        // Override DI registrations here when external services need to be mocked.
        // Example:
        // builder.ConfigureServices(services =>
        // {
        //     services.AddHttpClient<MyApiService>()
        //             .ConfigurePrimaryHttpMessageHandler(() => new FakeMyApiHandler());
        // });
    }
}

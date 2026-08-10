// -----------------------------------------------------------------------
// CustomWebApplicationFactory.cs — In-memory test host for integration tests.
//
// The Platform Test Application has no external dependencies, so the default
// application host is the complete integration-test fixture.
// -----------------------------------------------------------------------

using Microsoft.AspNetCore.Mvc.Testing;

namespace Mcp.Connector.Template.Tests.TestInfrastructure;

/// <summary>
/// Spins up the complete Platform Test Application in memory.
/// </summary>
public class CustomWebApplicationFactory : WebApplicationFactory<Program>;

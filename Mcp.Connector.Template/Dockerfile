# See https://aka.ms/customizecontainer to learn how to customize your debug container and how Visual Studio uses this Dockerfile to build your images for faster debugging.

# This stage is used when running from VS in fast mode (Default for Debug configuration)
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
USER $APP_UID
WORKDIR /app
EXPOSE 8080


# This stage is used to build the service project
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["Directory.Build.props", "./"]
COPY ["Mcp.Connector.Template/Mcp.Connector.Template.csproj", "Mcp.Connector.Template/"]
RUN dotnet restore "./Mcp.Connector.Template/Mcp.Connector.Template.csproj"
COPY . .
WORKDIR "/src/Mcp.Connector.Template"
RUN dotnet build "./Mcp.Connector.Template.csproj" -c $BUILD_CONFIGURATION -o /app/build

# This stage is used to publish the service project to be copied to the final stage
FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "./Mcp.Connector.Template.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false \
    && find /app/publish -name '*.pdb' -delete

# This stage is used in production or when running from VS in regular mode (Default when not using the Debug configuration)
FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Mcp.Connector.Template.dll"]
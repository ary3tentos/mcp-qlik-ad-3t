# Script de teste PowerShell para o MCP Server Qlik Cloud
# Uso: .\test_mcp_server.ps1 -JwtToken "seu_token_jwt"

param(
    [string]$JwtToken = "your_jwt_token_here",
    [string]$McpServerUrl = "http://localhost:8080"
)

Write-Host "Testing MCP Server at $McpServerUrl" -ForegroundColor Green
Write-Host ""

Write-Host "1. Testing initialize..." -ForegroundColor Yellow
$body1 = @{
    jsonrpc = "2.0"
    id = 1
    method = "initialize"
    params = @{}
} | ConvertTo-Json

Invoke-RestMethod -Uri "$McpServerUrl/mcp" `
    -Method Post `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $JwtToken"
    } `
    -Body $body1
Write-Host ""

Write-Host "2. Testing tools/list..." -ForegroundColor Yellow
$body2 = @{
    jsonrpc = "2.0"
    id = 2
    method = "tools/list"
    params = @{}
} | ConvertTo-Json

Invoke-RestMethod -Uri "$McpServerUrl/mcp" `
    -Method Post `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $JwtToken"
    } `
    -Body $body2
Write-Host ""

Write-Host "3. Testing qlik_get_apps..." -ForegroundColor Yellow
$body3 = @{
    jsonrpc = "2.0"
    id = 3
    method = "tools/call"
    params = @{
        name = "qlik_get_apps"
        arguments = @{
            limit = 10
        }
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "$McpServerUrl/mcp" `
    -Method Post `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $JwtToken"
    } `
    -Body $body3
Write-Host ""

Write-Host "4. Testing health endpoint..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "$McpServerUrl/health" -Method Get
Write-Host ""

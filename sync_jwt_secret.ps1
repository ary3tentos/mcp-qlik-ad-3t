# Script PowerShell para sincronizar JWT_SECRET_KEY do backend para o MCP server
# Uso: .\sync_jwt_secret.ps1

$backendEnvPath = "..\ai-pocs\backend\.env"
$mcpEnvPath = ".env"

Write-Host "Sincronizando JWT_SECRET_KEY..." -ForegroundColor Green
Write-Host ""

# Verificar se o arquivo do backend existe
if (-not (Test-Path $backendEnvPath)) {
    Write-Host "❌ Arquivo não encontrado: $backendEnvPath" -ForegroundColor Red
    Write-Host "   Verifique o caminho do backend ai-pocs" -ForegroundColor Yellow
    exit 1
}

# Ler JWT_SECRET_KEY do backend
$backendContent = Get-Content $backendEnvPath -Raw
$jwtSecretMatch = [regex]::Match($backendContent, "JWT_SECRET_KEY=(.+)")

if (-not $jwtSecretMatch.Success) {
    Write-Host "❌ JWT_SECRET_KEY não encontrado no backend" -ForegroundColor Red
    exit 1
}

$jwtSecret = $jwtSecretMatch.Groups[1].Value.Trim()
Write-Host "✅ JWT_SECRET_KEY encontrado no backend" -ForegroundColor Green
Write-Host "   Valor: $($jwtSecret.Substring(0, [Math]::Min(20, $jwtSecret.Length)))..." -ForegroundColor Gray
Write-Host ""

# Ler ou criar .env do MCP server
if (Test-Path $mcpEnvPath) {
    $mcpContent = Get-Content $mcpEnvPath -Raw
    Write-Host "📝 Arquivo .env do MCP server encontrado" -ForegroundColor Yellow
} else {
    $mcpContent = ""
    Write-Host "📝 Criando novo arquivo .env do MCP server" -ForegroundColor Yellow
}

# Atualizar ou adicionar JWT_SECRET_KEY
if ($mcpContent -match "JWT_SECRET_KEY=") {
    $mcpContent = $mcpContent -replace "JWT_SECRET_KEY=.*", "JWT_SECRET_KEY=$jwtSecret"
    Write-Host "✅ JWT_SECRET_KEY atualizado no .env do MCP server" -ForegroundColor Green
} else {
    if ($mcpContent -and -not $mcpContent.EndsWith("`n")) {
        $mcpContent += "`n"
    }
    $mcpContent += "JWT_SECRET_KEY=$jwtSecret`n"
    Write-Host "✅ JWT_SECRET_KEY adicionado ao .env do MCP server" -ForegroundColor Green
}

# Salvar arquivo
$mcpContent | Set-Content $mcpEnvPath -NoNewline
Write-Host ""
Write-Host "✅ Sincronização concluída!" -ForegroundColor Green
Write-Host "   Arquivo atualizado: $mcpEnvPath" -ForegroundColor Gray

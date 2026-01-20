# Setup do Qlik Cloud MCP Server

## Instalação

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Configurar variáveis de ambiente:
```bash
# Opção 1: Sincronizar JWT_SECRET_KEY do backend (recomendado)
# Windows:
.\sync_jwt_secret.ps1

# Linux/Mac:
./sync_jwt_secret.sh

# Opção 2: Criar manualmente
# Copie .env.example para .env e edite com suas credenciais
# IMPORTANTE: Use a mesma JWT_SECRET_KEY do backend ai-pocs
```

3. Executar o servidor:
```bash
python -m src.main
# ou
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## Testes

### Bash (Linux/Mac)
```bash
chmod +x test_mcp_server.sh
./test_mcp_server.sh <seu_jwt_token>
```

### PowerShell (Windows)
```powershell
.\test_mcp_server.ps1 -JwtToken "<seu_jwt_token>"
```

### Manual (curl)
```bash
# Health check
curl http://localhost:8080/health

# Initialize
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'

# List tools
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'

# Call qlik_get_apps
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "qlik_get_apps", "arguments": {"limit": 10}}}'
```

## Estrutura do Projeto

```
qlik-mcp-server-ad/
├── src/
│   ├── main.py                 # FastAPI app
│   ├── mcp/
│   │   ├── handler.py          # JSON-RPC handler
│   │   └── tools/              # MCP tools
│   ├── qlik/
│   │   ├── client.py           # REST API client
│   │   ├── engine.py           # WebSocket Engine API client
│   │   └── auth.py             # OAuth token management
│   ├── auth/
│   │   └── jwt_validator.py    # JWT validation
│   └── storage/
│       └── token_store.py      # Token storage (SQLite)
├── integration_examples/       # Exemplos para integração no ai-pocs
├── requirements.txt
├── .env.example
└── test_mcp_server.sh/ps1     # Scripts de teste
```

## Endpoints

- `POST /mcp` - Endpoint principal MCP (JSON-RPC)
- `POST /tokens` - Armazenar tokens OAuth do Qlik
- `DELETE /tokens` - Remover tokens OAuth do Qlik
- `GET /health` - Health check

## Tools Disponíveis

1. `qlik_get_apps` - Lista apps disponíveis
2. `qlik_get_app_sheets` - Lista sheets de um app
3. `qlik_get_sheet_charts` - Lista charts de uma sheet
4. `qlik_get_chart_data` - Extrai dados de um chart

## Próximos Passos

Ver `INTEGRATION_GUIDE.md` para instruções de integração com o ai-pocs.

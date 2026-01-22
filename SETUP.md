# Setup do Qlik Cloud MCP Server

## Instalação

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Configurar variáveis de ambiente:
```bash
# Criar arquivo .env
cp .env.example .env
# Editar .env com suas credenciais
```

**Variáveis necessárias no `.env`:**
```env
QLIK_CLOUD_API_KEY=<api_key_do_usuário_mestre>
QLIK_CLOUD_TENANT_URL=https://<tenant>.qlikcloud.com
MCP_SERVER_PORT=8082
MCP_SERVER_HOST=0.0.0.0
```

3. Executar o servidor:
```bash
# Desenvolvimento
python -m src.main

# Ou especificando porta
MCP_SERVER_PORT=8082 python -m src.main
```

## Testes

### Health Check
```bash
curl http://localhost:8082/health
```

### Initialize
```bash
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <qlik_api_key>" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'
```

### List Tools
```bash
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <qlik_api_key>" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'
```

### Call qlik_get_apps
```bash
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <qlik_api_key>" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "qlik_get_apps", "arguments": {"limit": 10}}}'
```

**Nota:** A API key pode ser passada via:
- Header `X-API-KEY: <api_key>`
- Header `Authorization: Bearer <api_key>`
- Ou configurada no `.env` como `QLIK_CLOUD_API_KEY`

## Estrutura do Projeto

```
qlik-mcp-server-ad/
├── src/
│   ├── main.py                 # FastAPI app
│   ├── mcp/
│   │   ├── handler.py          # JSON-RPC handler
│   │   └── tools/              # MCP tools (read-only)
│   ├── qlik/
│   │   ├── client.py           # REST API client
│   │   ├── engine.py           # WebSocket Engine API client
│   │   └── auth.py             # API key management
├── requirements.txt
├── .env.example
└── SETUP.md
```

## Endpoints

- `POST /mcp` - Endpoint principal MCP (JSON-RPC)
  - Autenticação: Header `X-API-KEY` ou `Authorization: Bearer <api_key>`
- `GET /health` - Health check

## Tools Disponíveis (Read-Only)

1. `qlik_get_apps` - Lista apps disponíveis
2. `qlik_get_app_sheets` - Lista sheets de um app
3. `qlik_get_sheet_charts` - Lista charts de uma sheet
4. `qlik_get_chart_data` - Extrai dados de um chart

**Nota:** Todas as tools são read-only (apenas consulta). Usa API key de um usuário mestre configurado.

## Próximos Passos

Ver `INTEGRATION_GUIDE.md` para instruções de integração com o ai-pocs.

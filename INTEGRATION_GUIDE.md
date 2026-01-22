# Guia de Integração: Qlik Cloud MCP Server com ai-pocs

## Pré-requisitos

1. MCP Server Qlik Cloud rodando (porta 8082 por padrão)
2. API key do Qlik Cloud (usuário mestre)
3. Acesso ao repositório ai-pocs

## Passos de Integração

### 1. Registrar MCP no Registry

Editar `backend/mcp_config.json`:

```json
{
  "id": "qlik-cloud",
  "name": "Qlik Cloud",
  "transport": "http",
  "endpoint": "http://localhost:8082/mcp",
  "apiKey": "<api_key_do_usuário_mestre>",
  "description": "Qlik Cloud MCP Server - Read-only queries"
}
```

**Importante:** A `apiKey` deve ser a API key do Qlik Cloud de um usuário mestre que tem acesso aos apps que você quer consultar.

### 2. Configurar MCP Client

O `MCPClient` já suporta API key. Quando `api_key` está configurado no `mcp_config.json`, ele será usado automaticamente.

**Não é necessário:**
- OAuth flow
- Armazenamento de tokens por usuário
- Endpoints de connect/disconnect

### 3. Variáveis de Ambiente no ai-pocs

**Não é necessário** adicionar variáveis de ambiente específicas do Qlik no backend, pois a API key já está no `mcp_config.json`.

**Opcional (se necessário):**
```env
QLIK_MCP_SERVER_URL=http://localhost:8082
```

## Como Funciona

1. **Backend ai-pocs** lê `mcp_config.json` e cria `MCPClient` com a API key
2. **MCPClient** envia requisições para o MCP server com header `X-API-KEY: <api_key>`
3. **MCP Server** usa a API key para chamar Qlik Cloud API
4. **Todas as tools são read-only** - apenas consulta de dados

## Remover Código Antigo (OAuth)

Se você tinha implementado OAuth anteriormente, pode remover:

- `backend/routes/qlik_auth_routes.py` (ou manter comentado)
- `backend/services/qlik_token_service.py`
- Métodos de tokens do `database_service.py`
- Endpoints de connect/disconnect do chat

## Teste

```bash
# No chat, perguntar algo que acione qlik_get_apps
# O MCP deve usar a API key configurada automaticamente
```

# Migração para API Key - Resumo das Mudanças

## ✅ Mudanças Implementadas

### Arquitetura Simplificada

**Antes (OAuth por usuário):**
- OAuth flow complexo
- Tokens por usuário no MongoDB
- Refresh automático de tokens
- Validação JWT + Qlik tokens

**Agora (API Key mestre):**
- API key fixa de usuário mestre
- Sem OAuth
- Sem armazenamento de tokens
- Apenas autenticação via API key

### Arquivos Modificados

#### MCP Server

1. **`src/qlik/auth.py`**
   - Removido: lógica de OAuth e tokens
   - Adicionado: `get_api_key()` - retorna API key do `.env`

2. **`src/qlik/client.py`**
   - Removido: dependência de `QlikAuth` e tokens
   - Modificado: `get_apps()` recebe `api_key` diretamente

3. **`src/qlik/engine.py`**
   - Removido: dependência de `QlikAuth` e tokens
   - Modificado: todos os métodos recebem `api_key` diretamente

4. **`src/mcp/tools/base_tool.py`**
   - Modificado: `execute()` não recebe mais `user_id` e `qlik_token`
   - Novo: `execute(arguments, api_key)`

5. **`src/mcp/tools/*.py`** (todas as tools)
   - Removido: `user_id` e `qlik_token` dos parâmetros
   - Modificado: recebem `api_key` diretamente

6. **`src/mcp/handler.py`**
   - Removido: `JWTValidator` e validação de JWT
   - Removido: extração de `user_id`
   - Modificado: recebe `api_key` do header ou usa do `.env`

7. **`src/main.py`**
   - Removido: validação JWT
   - Modificado: extrai API key do header `X-API-KEY` ou `Authorization: Bearer`
   - Removido: endpoints `/tokens`

### Configuração

#### MCP Server `.env`
```env
QLIK_CLOUD_API_KEY=<api_key_do_usuário_mestre>
QLIK_CLOUD_TENANT_URL=https://<tenant>.qlikcloud.com
MCP_SERVER_PORT=8082
MCP_SERVER_HOST=0.0.0.0
```

#### Backend ai-pocs `mcp_config.json`
```json
{
  "id": "qlik-cloud",
  "name": "Qlik Cloud",
  "transport": "http",
  "endpoint": "http://localhost:8082/mcp",
  "apiKey": "<mesma_api_key_do_usuário_mestre>",
  "description": "Qlik Cloud MCP Server - Read-only queries"
}
```

## 🔄 Novo Fluxo

```
Chat → MCP Registry
  ↓
MCP Registry lê apiKey do mcp_config.json
  ↓
MCP Client envia requisição com header: X-API-KEY: <api_key>
  ↓
MCP Server recebe API key do header
  ↓
MCP Handler usa API key (do header ou .env)
  ↓
Tools usam API key para chamar Qlik Cloud API
```

## ✅ Benefícios

1. **Simplicidade** - Sem OAuth, sem tokens, sem refresh
2. **Performance** - Menos overhead de autenticação
3. **Manutenção** - Código muito mais simples
4. **Segurança** - API key pode ser rotacionada facilmente

## ⚠️ Limitações

1. **Apenas Read-Only** - Todas as tools são consulta apenas
2. **Usuário Mestre** - Todos os usuários do chat veem os mesmos apps (do usuário mestre)
3. **Sem Governança por Usuário** - Não há isolamento de dados por usuário

## 📝 Próximos Passos no Backend ai-pocs

1. **Atualizar `mcp_config.json`:**
   - Adicionar `apiKey` com a API key do Qlik

2. **Remover código OAuth (opcional):**
   - `backend/routes/qlik_auth_routes.py`
   - `backend/services/qlik_token_service.py`
   - Métodos de tokens do `database_service.py`
   - Endpoints de connect/disconnect

3. **Testar:**
   - Verificar se MCP client passa API key corretamente
   - Testar chamada de tool do Qlik

## 🧪 Teste Rápido

```bash
# Health check
curl http://localhost:8082/health

# Teste com API key
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <sua_api_key>" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

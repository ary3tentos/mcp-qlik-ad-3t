# Prompt para Cursor Agent - Repositório ai-pocs

```
O MCP Server do Qlik foi refatorado para ser totalmente stateless. Tokens do Qlik Cloud agora são armazenados no backend do chat (MongoDB) e passados para o MCP Server via header em cada requisição.

## O que foi implementado:

1. **QlikTokenService** (`backend/services/qlik_token_service.py`) - NOVO
   - Gerencia tokens do Qlik Cloud
   - Armazena no MongoDB (collection: qlik_tokens)
   - Faz refresh automático de tokens
   - Instância global criada em main.py: `qlik_token_service`

2. **Database Service** (`backend/services/database_service.py`)
   - Métodos adicionados: `save_qlik_tokens()`, `get_qlik_tokens()`, `delete_qlik_tokens()`
   - Collection: `qlik_tokens` com estrutura: {user_id, access_token, refresh_token, expires_at, created_at, updated_at}

3. **MCP Client** (`backend/services/mcp_client.py`)
   - `call_tool()` agora aceita `qlik_token: Optional[str] = None`
   - `_call_tool_http()` adiciona header `X-Qlik-Access-Token` quando token fornecido

4. **MCP Registry** (`backend/services/mcp_registry.py`)
   - `call_tool()` busca token do Qlik antes de chamar tools que começam com "qlik_"
   - Usa: `from main import qlik_token_service` → `await qlik_token_service.get_access_token(user_id)`
   - Passa token para: `client.call_tool(..., qlik_token=token)`

5. **Qlik Auth Routes** (`backend/routes/qlik_auth_routes.py`)
   - `qlik_callback()` usa `qlik_token_service.store_tokens()` em vez de `store_tokens_in_mcp()`
   - Função `store_tokens_in_mcp()` foi removida

6. **Chat Routes** (`backend/routes/chat_routes.py`)
   - `disconnect_qlik()` usa `qlik_token_service.delete_tokens()` em vez de chamar endpoint do MCP

7. **Main** (`backend/main.py`)
   - Import: `from services.qlik_token_service import QlikTokenService`
   - Instância: `qlik_token_service = QlikTokenService(database_service)`

## Fluxo atual:

**OAuth (Conectar Qlik):**
OAuth Callback → qlik_token_service.store_tokens() → MongoDB (collection: qlik_tokens)

**Tool Call (Usar Qlik):**
MCP Registry → qlik_token_service.get_access_token(user_id) → Busca do MongoDB → Passa para MCP Client → Header "X-Qlik-Access-Token" → MCP Server

## Tarefas:

1. Verificar se todos os arquivos foram atualizados corretamente
2. Verificar se imports estão corretos (especialmente `from main import qlik_token_service`)
3. Verificar se não há referências antigas a `store_tokens_in_mcp()` ou endpoints `/tokens` do MCP
4. Adicionar índice no MongoDB para collection qlik_tokens (user_id único)
5. Testar OAuth flow - verificar se tokens são salvos no MongoDB
6. Testar tool call - verificar se token é buscado e passado corretamente
7. Verificar tratamento de erros quando token não é encontrado

## Importante:

- MCP Server não armazena mais tokens (stateless)
- Todos os tokens devem estar no MongoDB
- Token é passado via header `X-Qlik-Access-Token` em cada requisição
- Refresh de tokens é feito pelo backend automaticamente
```

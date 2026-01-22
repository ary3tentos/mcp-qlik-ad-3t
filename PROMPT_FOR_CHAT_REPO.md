# Prompt para Agente Cursor - Repositório ai-pocs

## Contexto

O MCP Server do Qlik foi refatorado para ser **totalmente stateless**. Tokens do Qlik Cloud agora são armazenados no backend do chat (MongoDB) e passados para o MCP Server via header em cada requisição.

## O que foi implementado

### 1. QlikTokenService (`backend/services/qlik_token_service.py`)

**NOVO ARQUIVO** - Gerencia tokens do Qlik Cloud:

- `store_tokens(user_id, access_token, refresh_token, expires_in)` - Salva tokens no MongoDB
- `get_access_token(user_id)` - Busca token válido, faz refresh se necessário
- `delete_tokens(user_id)` - Remove tokens do usuário
- `has_tokens(user_id)` - Verifica se usuário tem tokens

**Verificar:**
- ✅ Arquivo existe e está importado em `main.py`
- ✅ Instância global `qlik_token_service` criada em `main.py`

### 2. Database Service (`backend/services/database_service.py`)

**MÉTODOS ADICIONADOS:**

- `save_qlik_tokens(user_id, tokens_data)` - Salva/atualiza tokens na collection `qlik_tokens`
- `get_qlik_tokens(user_id)` - Busca tokens do usuário
- `delete_qlik_tokens(user_id)` - Remove tokens do usuário

**Collection MongoDB:** `qlik_tokens`

**Estrutura do documento:**
```python
{
    "user_id": "string",
    "access_token": "string",
    "refresh_token": "string",
    "expires_at": datetime,
    "created_at": datetime,
    "updated_at": datetime
}
```

**Verificar:**
- ✅ Métodos implementados
- ✅ Collection `qlik_tokens` adicionada em `__init__`
- ✅ Índice criado em `user_id` (recomendado)

### 3. MCP Client (`backend/services/mcp_client.py`)

**MUDANÇAS:**

- Método `call_tool()` agora aceita `qlik_token: Optional[str] = None`
- Método `_call_tool_http()` adiciona header `X-Qlik-Access-Token` se `qlik_token` fornecido

**Verificar:**
- ✅ Assinatura do método atualizada
- ✅ Header sendo adicionado corretamente

### 4. MCP Registry (`backend/services/mcp_registry.py`)

**MUDANÇAS:**

- Método `call_tool()` busca token do Qlik antes de chamar tools que começam com `qlik_`
- Usa `qlik_token_service.get_access_token(user_id)` para buscar token
- Passa token para `client.call_tool(..., qlik_token=token)`

**Verificar:**
- ✅ Import de `qlik_token_service` do `main`
- ✅ Lógica de busca de token implementada
- ✅ Token sendo passado para o client

### 5. Qlik Auth Routes (`backend/routes/qlik_auth_routes.py`)

**MUDANÇAS:**

- `qlik_callback()` agora usa `qlik_token_service.store_tokens()` em vez de `store_tokens_in_mcp()`
- Função `store_tokens_in_mcp()` foi removida (não é mais necessária)

**Verificar:**
- ✅ Import de `qlik_token_service` do `main`
- ✅ `store_tokens_in_mcp()` removida
- ✅ Callback armazena tokens no backend

### 6. Chat Routes (`backend/routes/chat_routes.py`)

**MUDANÇAS:**

- `disconnect_qlik()` agora usa `qlik_token_service.delete_tokens()` em vez de chamar endpoint `/tokens` do MCP

**Verificar:**
- ✅ Import de `qlik_token_service` do `main`
- ✅ Método `delete_tokens()` sendo usado

### 7. Main (`backend/main.py`)

**MUDANÇAS:**

- Import de `QlikTokenService` adicionado
- Instância global `qlik_token_service = QlikTokenService(database_service)` criada

**Verificar:**
- ✅ Import correto
- ✅ Instância criada e inicializada

## Fluxo completo (como funciona agora)

### 1. OAuth Flow (Conectar Qlik)

```
Usuário clica "Conectar Qlik"
  ↓
GET /api/auth/qlik/authorize
  ↓
Redireciona para Qlik Cloud OAuth
  ↓
Qlik → Azure AD (SSO)
  ↓
GET /api/auth/qlik/callback?code=...&state=...
  ↓
Backend troca code por tokens
  ↓
qlik_token_service.store_tokens(user_id, access_token, refresh_token, expires_in)
  ↓
MongoDB: collection "qlik_tokens"
```

### 2. Tool Call (Usar Qlik)

```
Chat → MCP Registry.call_tool("qlik_get_apps", arguments, user_id, jwt_token)
  ↓
MCP Registry detecta tool do Qlik (starts with "qlik_")
  ↓
qlik_token_service.get_access_token(user_id)
  ↓
  - Busca do MongoDB
  - Verifica expiração
  - Faz refresh se necessário
  - Retorna access_token válido
  ↓
MCP Registry → MCP Client.call_tool(..., qlik_token=token)
  ↓
MCP Client adiciona header: "X-Qlik-Access-Token: <token>"
  ↓
POST http://localhost:8082/mcp
  Headers:
    Authorization: Bearer <jwt_chat>
    X-Qlik-Access-Token: <qlik_token>
  ↓
MCP Server extrai token do header e usa nas tools
```

## Tarefas para verificar/implementar

### ✅ Verificações Necessárias

1. **Verificar se QlikTokenService está funcionando:**
   ```python
   # Testar no Python shell do backend
   from main import qlik_token_service
   # Verificar se métodos existem
   ```

2. **Verificar se database_service tem os métodos:**
   ```python
   from services.database_service import database_service
   # Verificar: save_qlik_tokens, get_qlik_tokens, delete_qlik_tokens
   ```

3. **Verificar se MCP Registry busca token:**
   - Abrir `mcp_registry.py`
   - Verificar se há código que busca token antes de chamar tools do Qlik
   - Verificar se passa `qlik_token` para `client.call_tool()`

4. **Verificar se MCP Client passa header:**
   - Abrir `mcp_client.py`
   - Verificar se `_call_tool_http()` adiciona header `X-Qlik-Access-Token`

5. **Testar OAuth Flow:**
   - Conectar conta Qlik
   - Verificar MongoDB: `db.qlik_tokens.find({user_id: "..."})`
   - Deve ter documento com tokens

6. **Testar Tool Call:**
   - Chamar tool `qlik_get_apps` no chat
   - Verificar logs do backend (deve buscar token)
   - Verificar logs do MCP server (deve receber token no header)

### 🔧 Ajustes Possíveis

1. **Índice no MongoDB:**
   ```python
   # Em database_service.py, método connect()
   # Adicionar índice para performance:
   await db[self.qlik_tokens_collection].create_index("user_id", unique=True)
   ```

2. **Tratamento de erros:**
   - Verificar se erros de token são tratados adequadamente
   - Mensagens de erro claras para o usuário

3. **Logs:**
   - Adicionar logs quando token é buscado/refreshado
   - Logs quando token não é encontrado

## Variáveis de ambiente necessárias

**Backend ai-pocs (.env):**
```env
# Qlik Cloud
QLIK_CLOUD_TENANT_URL=https://<tenant>.qlikcloud.com
QLIK_CLOUD_REDIRECT_URI=https://3tentos.ai/api/auth/qlik/callback
QLIK_MCP_SERVER_URL=http://localhost:8082

# JWT (mesmo do MCP server)
JWT_SECRET_KEY=<sua_chave>
```

## Testes recomendados

### Teste 1: OAuth Flow
```bash
# 1. Iniciar backend
# 2. Fazer login no chat
# 3. Clicar "Conectar Qlik"
# 4. Completar OAuth
# 5. Verificar MongoDB:
mongo
> use azure_chat_pal
> db.qlik_tokens.find().pretty()
```

### Teste 2: Tool Call
```bash
# 1. No chat, perguntar algo que acione qlik_get_apps
# 2. Verificar logs do backend:
#    - Deve buscar token do MongoDB
#    - Deve passar token para MCP
# 3. Verificar logs do MCP server:
#    - Deve receber header X-Qlik-Access-Token
#    - Deve usar token para chamar Qlik API
```

### Teste 3: Refresh Token
```bash
# 1. Aguardar expiração do token (ou forçar)
# 2. Chamar tool do Qlik
# 3. Verificar se refresh acontece automaticamente
# 4. Verificar se novo token é salvo no MongoDB
```

## Pontos de atenção

1. **Import circular:** `qlik_token_service` é importado do `main` - verificar se não causa problemas
2. **Inicialização:** `qlik_token_service` precisa de `database_service` - garantir que está inicializado
3. **Erros:** Se token não for encontrado, tool deve retornar erro claro
4. **Performance:** Índice em `user_id` na collection `qlik_tokens` é recomendado

## Status esperado

Após verificar tudo:
- ✅ OAuth flow salva tokens no MongoDB
- ✅ Tool calls buscam token do MongoDB
- ✅ Token é passado para MCP via header
- ✅ MCP usa token para chamar Qlik API
- ✅ Refresh de tokens funciona automaticamente

## Comandos úteis para debug

```python
# No Python shell do backend
from main import qlik_token_service, database_service

# Verificar se service existe
print(qlik_token_service)

# Testar busca de token
token = await qlik_token_service.get_access_token("user_id_teste")
print(token)

# Verificar tokens no MongoDB
tokens = await database_service.get_qlik_tokens("user_id_teste")
print(tokens)
```

---

**IMPORTANTE:** Esta é uma mudança breaking. O MCP server não armazena mais tokens. Todos os tokens devem estar no backend (MongoDB). Se houver tokens antigos em outro lugar, eles precisam ser migrados.

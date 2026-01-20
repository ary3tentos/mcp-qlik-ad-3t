# Guia de Integração: Qlik Cloud MCP Server com ai-pocs

## Pré-requisitos

1. MCP Server Qlik Cloud rodando (porta 8080 por padrão)
2. Acesso ao repositório ai-pocs
3. Variáveis de ambiente configuradas no ai-pocs

## Passos de Integração

### 1. Registrar MCP no Registry

Editar `backend/services/mcp_registry.py` e adicionar:

```python
{
    "id": "qlik-cloud",
    "name": "Qlik Cloud",
    "type": "http",
    "config": {
        "url": "http://localhost:8080/mcp",
        "api_key": None  # Usa JWT do usuário
    }
}
```

### 2. Modificar MCPClient para Enviar JWT

Em `backend/services/mcp_client.py`, modificar o método que faz requisições HTTP para o MCP server:

- Quando `api_key` é `None`, usar o JWT do usuário atual no header `Authorization: Bearer <jwt>`
- Extrair JWT do contexto da requisição (depende de como FastAPI gerencia auth)

### 3. Implementar Endpoints OAuth Qlik

Criar `backend/api/auth/qlik.py` com:

- `GET /api/auth/qlik/authorize`: Inicia OAuth flow (Authorization Code + PKCE)
- `GET /api/auth/qlik/callback`: Recebe callback, troca code por tokens
- `POST /api/auth/qlik/tokens`: Armazena tokens no MCP server
- `GET /api/auth/qlik/status`: Verifica se usuário tem tokens configurados

### 4. Endpoints de Gerenciamento

Criar ou modificar `backend/api/mcps/qlik.py`:

- `POST /api/mcps/user/qlik-cloud/connect`: Inicia OAuth flow
- `GET /api/mcps/user/qlik-cloud/status`: Status de conexão
- `DELETE /api/mcps/user/qlik-cloud/disconnect`: Remove tokens

## Variáveis de Ambiente no ai-pocs

Adicionar ao `.env` do ai-pocs:

```env
QLIK_MCP_SERVER_URL=http://localhost:8080
QLIK_CLOUD_TENANT_URL=https://<tenant>.qlikcloud.com
QLIK_CLOUD_REDIRECT_URI=https://<seu-backend>/api/auth/qlik/callback
```

**Nota:** Quando o Qlik Cloud está configurado com Azure AD como IdP, não é necessário `QLIK_CLOUD_CLIENT_ID` e `QLIK_CLOUD_CLIENT_SECRET`. O usuário autentica diretamente com Azure AD (mesmo IdP do chat).

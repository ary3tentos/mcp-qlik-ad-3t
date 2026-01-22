# Guia de Refatoração: MCP Stateless (Opcional)

Este guia mostra como refatorar o MCP para ser totalmente stateless, seguindo as melhores práticas arquiteturais.

## 🎯 Objetivo

Tornar o MCP Server totalmente stateless, onde:
- Tokens são armazenados no Chat Backend
- MCP recebe tokens via header em cada requisição
- MCP não tem estado persistente

## 📋 Passos de Refatoração

### Passo 1: Armazenar Tokens no Chat Backend

**Arquivo:** `backend/services/qlik_token_service.py` (novo)

```python
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import os
import logging

logger = logging.getLogger(__name__)

class QlikTokenService:
    def __init__(self, database_service):
        self.database = database_service
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
    
    async def store_tokens(self, user_id: str, access_token: str, refresh_token: str, expires_in: int):
        """Store Qlik tokens in database"""
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        tokens_data = {
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "updated_at": datetime.utcnow()
        }
        
        # Salvar no MongoDB/Cosmos
        await self.database.save_qlik_tokens(user_id, tokens_data)
        logger.info(f"Qlik tokens stored for user {user_id}")
    
    async def get_access_token(self, user_id: str) -> Optional[str]:
        """Get valid Qlik access token, refreshing if necessary"""
        tokens = await self.database.get_qlik_tokens(user_id)
        
        if not tokens:
            return None
        
        # Verificar se token expirou
        expires_at = tokens.get("expires_at")
        if expires_at and datetime.utcnow() < expires_at:
            return tokens.get("access_token")
        
        # Token expirado, fazer refresh
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None
        
        new_tokens = await self._refresh_token(refresh_token)
        if new_tokens:
            await self.store_tokens(
                user_id,
                new_tokens["access_token"],
                new_tokens.get("refresh_token", refresh_token),
                new_tokens.get("expires_in", 3600)
            )
            return new_tokens["access_token"]
        
        return None
    
    async def _refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Qlik access token"""
        token_url = f"{self.tenant_url}/oauth/token"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Error refreshing Qlik token: {str(e)}")
        
        return None
    
    async def delete_tokens(self, user_id: str):
        """Delete Qlik tokens for user"""
        await self.database.delete_qlik_tokens(user_id)
        logger.info(f"Qlik tokens deleted for user {user_id}")
```

### Passo 2: Modificar MCP Client para Passar Token

**Arquivo:** `backend/services/mcp_client.py`

```python
async def _call_tool_http(
    self, 
    tool_name: str, 
    arguments: Dict[str, Any],
    qlik_token: Optional[str] = None  # Novo parâmetro
) -> Optional[Dict[str, Any]]:
    """Call tool via HTTP"""
    try:
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.user_jwt_token:
            headers["Authorization"] = f"Bearer {self.user_jwt_token}"
        
        # Adicionar token do Qlik se fornecido
        if qlik_token:
            headers["X-Qlik-Access-Token"] = qlik_token
        
        # ... resto do código
```

**Arquivo:** `backend/services/mcp_registry.py`

```python
async def call_tool(
    self,
    tool_name: str,
    arguments: Dict[str, Any],
    user_id: Optional[str] = None,
    user_jwt_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Route tool call to the appropriate server"""
    
    # Se for tool do Qlik, buscar token
    qlik_token = None
    if tool_name.startswith("qlik_"):
        from services.qlik_token_service import qlik_token_service
        qlik_token = await qlik_token_service.get_access_token(user_id)
        if not qlik_token:
            logger.warning(f"No Qlik token for user {user_id}")
            return None
    
    # ... resto do código
    
    # Passar qlik_token para o client
    result = await client.call_tool(tool_name, arguments, qlik_token=qlik_token)
    return result
```

### Passo 3: Modificar MCP Handler para Receber Token via Header

**Arquivo:** `src/mcp/handler.py`

```python
async def handle_request(
    self, 
    body: Dict[str, Any], 
    token: str,
    request: Optional[Request] = None  # Novo parâmetro
) -> Dict[str, Any]:
    """Handle MCP request"""
    
    # Extrair token do Qlik do header (se fornecido)
    qlik_token = None
    if request:
        qlik_token = request.headers.get("X-Qlik-Access-Token")
    
    # Validar JWT do chat
    decoded_token = await self.jwt_validator.validate_token(token)
    if not decoded_token:
        return {"error": "Invalid JWT"}
    
    user_id = self.jwt_validator.extract_user_id(decoded_token)
    
    # Se for tool do Qlik, usar token do header
    if method == "tools/call":
        tool_name = params.get("name")
        if tool_name.startswith("qlik_"):
            if not qlik_token:
                return {
                    "error": "Missing Qlik access token. User needs to connect Qlik account."
                }
            # Passar token para as tools
            result = await tool_instance.execute(user_id, arguments, qlik_token)
```

### Passo 4: Modificar Tools para Receber Token

**Arquivo:** `src/mcp/tools/base_tool.py`

```python
class BaseTool:
    async def execute(
        self, 
        user_id: str, 
        arguments: Dict[str, Any],
        qlik_token: Optional[str] = None  # Novo parâmetro
    ) -> Dict[str, Any]:
        raise NotImplementedError
```

**Arquivo:** `src/mcp/tools/qlik_get_apps.py`

```python
async def execute(
    self, 
    user_id: str, 
    arguments: Dict[str, Any],
    qlik_token: Optional[str] = None
) -> Dict[str, Any]:
    if not qlik_token:
        raise Exception("Qlik access token required")
    
    # Usar token diretamente
    result = await self.client.get_apps(qlik_token, limit=limit, cursor=cursor, name=name)
    return result
```

### Passo 5: Modificar QlikAuth para Ser Stateless

**Arquivo:** `src/qlik/auth.py`

```python
class QlikAuth:
    def __init__(self):
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
    
    async def get_access_token(self, qlik_token: str) -> str:
        """Token já vem do header, só retornar"""
        return qlik_token
```

### Passo 6: Remover TokenStore do MCP

**Arquivo:** `src/main.py`

```python
# REMOVER:
# from src.storage.token_store import TokenStore
# token_store = TokenStore()

# MODIFICAR:
handler = MCPHandler()  # Sem token_store
```

**Arquivo:** `src/mcp/handler.py`

```python
class MCPHandler:
    def __init__(self):  # Sem token_store
        self.jwt_validator = JWTValidator()
        # REMOVER: self.qlik_auth = QlikAuth(token_store)
        self.qlik_auth = QlikAuth()  # Stateless
```

### Passo 7: Remover Endpoint /tokens do MCP

**Arquivo:** `src/main.py`

```python
# REMOVER endpoints:
# @app.post("/tokens")
# @app.delete("/tokens")
```

## ✅ Checklist de Migração

- [ ] Criar `QlikTokenService` no Chat Backend
- [ ] Adicionar métodos no `database_service` para tokens
- [ ] Modificar `mcp_client` para passar token via header
- [ ] Modificar `mcp_registry` para buscar token antes de chamar
- [ ] Modificar `mcp_handler` para receber token via header
- [ ] Modificar todas as tools do Qlik para receber token
- [ ] Remover `TokenStore` do MCP
- [ ] Remover endpoints `/tokens` do MCP
- [ ] Atualizar `qlik_auth_routes` para armazenar no backend
- [ ] Testar fluxo completo

## 🎯 Resultado Final

Após refatoração:
- ✅ MCP totalmente stateless
- ✅ Tokens centralizados no Chat Backend
- ✅ Fácil escalar MCP horizontalmente
- ✅ Arquitetura mais limpa

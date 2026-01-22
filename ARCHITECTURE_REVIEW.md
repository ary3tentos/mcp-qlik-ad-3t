# Revisão Arquitetural - Qlik MCP Server

## ✅ Validação do Fluxo OAuth

### Estado Atual vs. Ideal

| Aspecto | Estado Atual | Ideal | Status |
|---------|-------------|-------|--------|
| **OAuth no Chat Backend** | ✅ Implementado | ✅ | ✅ Correto |
| **Callback no Chat** | ✅ Implementado | ✅ | ✅ Correto |
| **PKCE** | ✅ Implementado | ✅ | ✅ Correto |
| **Azure AD SSO** | ✅ Configurado | ✅ | ✅ Correto |
| **Armazenamento de Tokens** | ⚠️ MCP Server (SQLite) | ⚠️ Chat Backend | ⚠️ Ajustar |
| **MCP Stateless** | ❌ Tem estado (SQLite) | ✅ Stateless | ⚠️ Ajustar |
| **Refresh de Tokens** | ⚠️ MCP faz refresh | ⚠️ Chat Backend | ⚠️ Ajustar |

## 🔍 Análise Detalhada

### ✅ O que está CORRETO

1. **OAuth Flow no Chat Backend**
   - ✅ `/api/auth/qlik/authorize` - Inicia OAuth
   - ✅ `/api/auth/qlik/callback` - Recebe callback
   - ✅ PKCE implementado
   - ✅ State validation

2. **Segurança**
   - ✅ Tokens nunca vão para frontend
   - ✅ JWT usado para autenticação entre Chat e MCP
   - ✅ User ID extraído do JWT

3. **Fluxo de Redirecionamento**
   - ✅ Qlik Cloud → Azure AD → Qlik Cloud → Chat Backend
   - ✅ Callback URL pública e HTTPS

### ⚠️ O que precisa AJUSTAR

#### 1. Armazenamento de Tokens

**Estado Atual:**
- Tokens armazenados no MCP Server (SQLite)
- MCP tem estado persistente
- MCP faz refresh de tokens

**Ideal:**
- Tokens armazenados no Chat Backend (MongoDB/Cosmos)
- MCP é stateless
- Chat Backend faz refresh e passa token para MCP

#### 2. MCP Stateless

**Estado Atual:**
```python
# MCP tem estado (SQLite)
token_store = TokenStore()  # SQLite
tokens = await token_store.get_tokens(user_id)
```

**Ideal:**
```python
# MCP recebe token via header
access_token = request.headers.get("X-Qlik-Access-Token")
# MCP não armazena nada
```

## 🎯 Proposta de Refatoração (Opcional)

### Opção A: Manter Estado Atual (Funcional)

**Vantagens:**
- ✅ Já implementado e funcionando
- ✅ MCP gerencia seus próprios tokens
- ✅ Refresh automático no MCP

**Desvantagens:**
- ⚠️ MCP não é totalmente stateless
- ⚠️ Tokens duplicados (se Chat também armazenar)
- ⚠️ Mais complexo para escalar

**Quando usar:**
- Se MCP é único e dedicado
- Se não precisa escalar horizontalmente
- Se simplicidade > arquitetura ideal

### Opção B: MCP Totalmente Stateless (Ideal)

**Mudanças necessárias:**

#### 1. Armazenar tokens no Chat Backend

```python
# backend/services/qlik_token_service.py
class QlikTokenService:
    async def store_tokens(self, user_id: str, tokens: dict):
        # Armazenar no MongoDB/Cosmos
        await database_service.save_qlik_tokens(user_id, tokens)
    
    async def get_access_token(self, user_id: str) -> str:
        # Buscar do MongoDB
        # Fazer refresh se necessário
        # Retornar access_token válido
        pass
```

#### 2. Passar token para MCP via header

```python
# backend/services/mcp_client.py
async def _call_tool_http(self, tool_name: str, arguments: dict):
    # Buscar token do Qlik do backend
    qlik_token = await qlik_token_service.get_access_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",  # JWT do chat
        "X-Qlik-Access-Token": qlik_token,  # Token do Qlik
        "Content-Type": "application/json"
    }
    # ...
```

#### 3. MCP recebe token via header

```python
# src/mcp/handler.py
async def handle_request(self, body: dict, token: str, request: Request):
    # Extrair token do Qlik do header
    qlik_token = request.headers.get("X-Qlik-Access-Token")
    
    if not qlik_token:
        return {"error": "Missing Qlik access token"}
    
    # Usar token diretamente, sem armazenar
    # ...
```

#### 4. Remover TokenStore do MCP

```python
# src/qlik/auth.py - Versão stateless
class QlikAuth:
    def __init__(self):
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL")
    
    async def get_access_token(self, qlik_token: str) -> str:
        # Token já vem do header, só validar
        return qlik_token
```

**Vantagens:**
- ✅ MCP totalmente stateless
- ✅ Tokens centralizados no Chat Backend
- ✅ Fácil escalar MCP horizontalmente
- ✅ Arquitetura mais limpa

**Desvantagens:**
- ⚠️ Requer refatoração
- ⚠️ Chat Backend precisa gerenciar refresh

## 📊 Comparação

| Aspecto | Opção A (Atual) | Opção B (Ideal) |
|---------|----------------|-----------------|
| **Complexidade** | Simples | Média |
| **Escalabilidade** | Limitada | Alta |
| **Stateless** | ❌ | ✅ |
| **Manutenção** | Fácil | Média |
| **Refatoração** | Nenhuma | Necessária |

## 🎯 Recomendação

### Para Produção Imediata:
**Manter Opção A (Estado Atual)**
- ✅ Funciona perfeitamente
- ✅ Já implementado
- ✅ Seguro
- ⚠️ MCP tem estado, mas é aceitável para uso único

### Para Arquitetura Ideal (Futuro):
**Migrar para Opção B (Stateless)**
- Quando precisar escalar MCP
- Quando quiser múltiplas instâncias do MCP
- Quando quiser arquitetura mais limpa

## 🔒 Segurança (Ambas Opções)

Ambas as opções são seguras:
- ✅ Tokens nunca vão para frontend
- ✅ JWT valida usuário
- ✅ HTTPS obrigatório
- ✅ PKCE no OAuth

## ✅ Conclusão

**Seu fluxo está CORRETO e FUNCIONAL.**

A única questão é arquitetural:
- **Opção A**: Funciona, mas MCP tem estado
- **Opção B**: Ideal, mas requer refatoração

**Recomendação:** Use Opção A agora, considere Opção B no futuro se precisar escalar.

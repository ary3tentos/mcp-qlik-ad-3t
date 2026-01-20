# Checklist de Deploy em Produção - Qlik MCP Server

## ⚠️ Problemas Identificados que Precisam ser Corrigidos

### 1. URLs Hardcoded como localhost

**Arquivos que precisam de ajuste:**

#### Backend ai-pocs:
- ✅ `mcp_config.json` - endpoint está como `http://localhost:8082`
- ✅ Variáveis de ambiente com defaults de localhost (já configuráveis via .env)

#### MCP Server:
- ✅ `src/auth/jwt_validator.py` - `AI_POCS_BACKEND_URL` default é `localhost:3001`

## 📋 Checklist de Configuração para Produção

### 1. Variáveis de Ambiente - Backend ai-pocs

No arquivo `.env` do backend, configure:

```env
# URLs de Produção
FRONTEND_URL=https://seu-dominio.com
AZURE_AD_REDIRECT_URI=https://seu-dominio.com/api/auth/azure/callback

# Qlik Cloud MCP
QLIK_MCP_SERVER_URL=http://localhost:8082  # Se na mesma VPS
# ou
QLIK_MCP_SERVER_URL=http://<ip-vps>:8082   # Se em VPS diferente
# ou
QLIK_MCP_SERVER_URL=https://mcp.seudominio.com  # Se com domínio próprio

QLIK_CLOUD_TENANT_URL=https://<tenant>.qlikcloud.com
QLIK_CLOUD_REDIRECT_URI=https://seu-dominio.com/api/auth/qlik/callback

# JWT (deve ser o mesmo no MCP server)
JWT_SECRET_KEY=<chave_segura_gerada>

# Database e Redis (produção)
MONGODB_CONNECTION_STRING=mongodb://<host>:27017/<database>
REDIS_URL=redis://<host>:6379
```

### 2. Variáveis de Ambiente - MCP Server

No arquivo `.env` do MCP server, configure:

```env
# JWT (MESMO valor do backend)
JWT_SECRET_KEY=<mesma_chave_do_backend>

# Backend URL (para validação JWT via HTTP)
AI_POCS_BACKEND_URL=https://seu-dominio.com
# ou se backend estiver na mesma VPS:
AI_POCS_BACKEND_URL=http://localhost:3001

# Qlik Cloud
QLIK_CLOUD_TENANT_URL=https://<tenant>.qlikcloud.com
QLIK_CLOUD_REDIRECT_URI=https://seu-dominio.com/api/auth/qlik/callback

# Server config
MCP_SERVER_PORT=8082
MCP_SERVER_HOST=0.0.0.0
```

### 3. Arquivo mcp_config.json - Backend

**IMPORTANTE:** Atualizar o endpoint do Qlik MCP:

```json
{
  "servers": [
    {
      "id": "qlik-cloud",
      "name": "Qlik Cloud",
      "transport": "http",
      "endpoint": "http://localhost:8082/mcp",
      "apiKey": null,
      "description": "Qlik Cloud MCP Server - List apps and extract chart data"
    }
  ]
}
```

**Para produção, o endpoint deve ser:**
- Se mesma VPS: `http://localhost:8082/mcp` ✅ (já está correto)
- Se VPS diferente: `http://<ip-vps>:8082/mcp`
- Se com domínio: `https://mcp.seudominio.com/mcp`

### 4. Azure AD App Registration

No Azure Portal, atualizar Redirect URIs:

**Produção:**
- `https://seu-dominio.com/api/auth/azure/callback`
- `https://seu-dominio.com/auth/callback` (se frontend tiver callback próprio)

**Desenvolvimento (manter):**
- `http://localhost:3001/api/auth/azure/callback`

### 5. Qlik Cloud OAuth

No Qlik Cloud, configurar Redirect URI:

**Produção:**
- `https://seu-dominio.com/api/auth/qlik/callback`

### 6. Firewall e Portas

**VPS - Portas abertas:**
- `3001` - Backend ai-pocs (ou porta configurada)
- `8082` - MCP Server Qlik (ou porta configurada)
- `80/443` - Nginx/Apache (se usar reverse proxy)

**Exemplo UFW (Ubuntu):**
```bash
sudo ufw allow 3001/tcp
sudo ufw allow 8082/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 7. Reverse Proxy (Nginx) - Recomendado

**Configuração Nginx para Backend:**
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Configuração Nginx para MCP Server (opcional):**
```nginx
server {
    listen 80;
    server_name mcp.seudominio.com;
    
    location / {
        proxy_pass http://localhost:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 8. Systemd Services

**Backend ai-pocs:**
```ini
[Unit]
Description=AI POCs Backend
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/path/to/ai-pocs/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 3001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**MCP Server:**
```ini
[Unit]
Description=Qlik Cloud MCP Server
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/path/to/qlik-mcp-server-ad
Environment="PATH=/path/to/venv/bin"
Environment="MCP_SERVER_PORT=8082"
Environment="MCP_SERVER_HOST=0.0.0.0"
ExecStart=/path/to/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9. SSL/HTTPS (Let's Encrypt)

**Instalar Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
```

**Gerar certificado:**
```bash
sudo certbot --nginx -d seu-dominio.com
```

**Renovação automática:**
```bash
sudo certbot renew --dry-run
```

### 10. Testes Pós-Deploy

**1. Health Checks:**
```bash
# Backend
curl https://seu-dominio.com/api/health

# MCP Server
curl http://localhost:8082/health
```

**2. Teste de Autenticação:**
- Login no frontend
- Verificar se JWT é gerado corretamente

**3. Teste MCP Qlik:**
- Conectar conta Qlik via OAuth
- Testar listagem de apps
- Testar extração de dados de chart

**4. Verificar Logs:**
```bash
# Backend
sudo journalctl -u ai-pocs-backend -f

# MCP Server
sudo journalctl -u qlik-mcp-server -f
```

## 🔒 Segurança

- [ ] JWT_SECRET_KEY gerado com `openssl rand -base64 32`
- [ ] `.env` não commitado no Git
- [ ] Firewall configurado
- [ ] SSL/HTTPS habilitado
- [ ] CORS configurado corretamente (apenas domínio de produção)
- [ ] Rate limiting configurado
- [ ] Logs não expõem tokens/senhas

## 📊 Monitoramento

- [ ] Health checks configurados
- [ ] Logs centralizados (opcional: ELK, CloudWatch, etc)
- [ ] Alertas configurados (opcional)
- [ ] Backup do banco de dados configurado

## ✅ Resumo

**Antes de subir para produção, certifique-se:**

1. ✅ Todas as URLs de localhost foram substituídas por URLs de produção
2. ✅ Variáveis de ambiente configuradas corretamente
3. ✅ JWT_SECRET_KEY é o mesmo em ambos os serviços
4. ✅ Azure AD Redirect URIs atualizados
5. ✅ Qlik Cloud Redirect URI atualizado
6. ✅ Firewall configurado
7. ✅ SSL/HTTPS configurado
8. ✅ Systemd services criados e ativos
9. ✅ Testes realizados

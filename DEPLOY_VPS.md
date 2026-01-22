# Guia de Deploy na VPS - Qlik MCP Server

## Passo 1: Acessar a VPS e Navegar até o Diretório

```bash
# SSH na VPS
ssh usuario@seu-ip-vps

# Navegar até o diretório do projeto
cd /path/to/qlik-mcp-server-ad
```

## Passo 2: Instalar Dependências Python

### Opção A: Usar Python do Sistema (Recomendado para produção)

```bash
# Verificar versão do Python (precisa ser 3.8+)
python3 --version

# Instalar dependências globalmente
pip3 install -r requirements.txt

# Ou usar pip do usuário (sem sudo)
pip3 install --user -r requirements.txt
```

### Opção B: Usar Virtual Environment (Recomendado - Isolamento)

```bash
# Criar virtual environment
python3 -m venv venv

# Ativar virtual environment
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## Passo 3: Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env
nano .env
```

**Conteúdo do `.env`:**

```env
# JWT (MESMO valor do backend ai-pocs)
JWT_SECRET_KEY=<mesma_chave_do_backend>

# Backend URL (para validação JWT via HTTP)
# Se backend na mesma VPS:
AI_POCS_BACKEND_URL=http://localhost:3001
# Se backend em VPS diferente:
# AI_POCS_BACKEND_URL=https://3tentos.ai

# Qlik Cloud
QLIK_CLOUD_TENANT_URL=https://<tenant>.qlikcloud.com
QLIK_CLOUD_REDIRECT_URI=https://3tentos.ai/api/auth/qlik/callback

# Server Config
MCP_SERVER_PORT=8082
MCP_SERVER_HOST=0.0.0.0

# Token Database (opcional - padrão: tokens.db)
# TOKEN_DB_PATH=/path/to/tokens.db
```

**Salvar e sair:** `Ctrl+X`, depois `Y`, depois `Enter`

## Passo 4: Testar Execução Manual

```bash
# Se usando virtual environment, ativar primeiro:
source venv/bin/activate

# Executar o servidor
python3 -m src.main

# Ou especificando porta diretamente:
MCP_SERVER_PORT=8082 python3 -m src.main
```

**Você deve ver:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8082
```

**Testar em outro terminal:**
```bash
# Health check
curl http://localhost:8082/health
# Deve retornar: {"status":"ok"}
```

**Parar o servidor:** `Ctrl+C`

## Passo 5: Criar Serviço Systemd (Produção)

**⚠️ IMPORTANTE:** Use o usuário correto! Verifique com `whoami`

Criar arquivo de serviço:

```bash
sudo nano /etc/systemd/system/qlik-mcp-server.service
```

**Conteúdo do serviço:**

```ini
[Unit]
Description=Qlik Cloud MCP Server
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/home/appuser/mcp-qlik-ad-3t
Environment="PATH=/home/appuser/mcp-qlik-ad-3t/venv/bin:/usr/local/bin:/usr/bin:/bin"
# Se usar virtual environment (recomendado):
ExecStart=/home/appuser/mcp-qlik-ad-3t/venv/bin/python -m src.main
# Se usar Python do sistema, descomente e ajuste:
# ExecStart=/usr/bin/python3 -m src.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**⚠️ Ajustar caminhos para seu ambiente:**
- `User=appuser` → **DEVE SER O USUÁRIO ATUAL** (verifique com `whoami`)
- `WorkingDirectory=/home/appuser/mcp-qlik-ad-3t` → caminho completo do projeto
- `ExecStart` → caminho do Python (venv ou sistema)
  - Venv: `/home/appuser/mcp-qlik-ad-3t/venv/bin/python`
  - Sistema: `/usr/bin/python3` ou `$(which python3)`

**Salvar e sair:** `Ctrl+X`, depois `Y`, depois `Enter`

## Passo 6: Ativar e Iniciar o Serviço

```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço (inicia automaticamente no boot)
sudo systemctl enable qlik-mcp-server

# Iniciar serviço
sudo systemctl start qlik-mcp-server

# Verificar status
sudo systemctl status qlik-mcp-server
```

**Você deve ver:**
```
● qlik-mcp-server.service - Qlik Cloud MCP Server
     Loaded: loaded (/etc/systemd/system/qlik-mcp-server.service; enabled)
     Active: active (running) since ...
```

## Passo 7: Verificar Logs

```bash
# Ver logs em tempo real
sudo journalctl -u qlik-mcp-server -f

# Ver últimas 50 linhas
sudo journalctl -u qlik-mcp-server -n 50

# Ver logs desde hoje
sudo journalctl -u qlik-mcp-server --since today
```

## Passo 8: Comandos Úteis do Systemd

```bash
# Parar serviço
sudo systemctl stop qlik-mcp-server

# Iniciar serviço
sudo systemctl start qlik-mcp-server

# Reiniciar serviço
sudo systemctl restart qlik-mcp-server

# Ver status
sudo systemctl status qlik-mcp-server

# Desabilitar auto-start no boot
sudo systemctl disable qlik-mcp-server

# Ver logs
sudo journalctl -u qlik-mcp-server -f
```

## Passo 9: Verificar Funcionamento

### Teste 1: Health Check

```bash
curl http://localhost:8082/health
# Deve retornar: {"status":"ok"}
```

### Teste 2: Verificar se está escutando na porta

```bash
sudo netstat -tlnp | grep 8082
# ou
sudo ss -tlnp | grep 8082
```

**Deve mostrar:**
```
tcp  0  0  0.0.0.0:8082  0.0.0.0:*  LISTEN  <pid>/python3
```

### Teste 3: Testar do Backend

No backend ai-pocs, verificar se consegue conectar:

```bash
# No diretório do backend ai-pocs
curl http://localhost:8082/health
```

## Passo 10: Configurar Firewall (Se Necessário)

**Se precisar acessar externamente (não recomendado - deve ser localhost apenas):**

```bash
# UFW (Ubuntu)
sudo ufw allow 8082/tcp

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8082/tcp
sudo firewall-cmd --reload
```

**⚠️ IMPORTANTE:** O MCP server deve ser acessível apenas via `localhost` (mesma VPS). Não exponha a porta 8082 externamente.

## Troubleshooting

### Problema: Serviço não inicia

**Erro: "Failed to determine user credentials: No such process" (status 217/USER)**

Este erro significa que o usuário no arquivo de serviço não existe ou está incorreto.

```bash
# 1. Verificar usuário atual
whoami

# 2. Verificar arquivo de serviço
sudo cat /etc/systemd/system/qlik-mcp-server.service | grep User=

# 3. Corrigir o arquivo de serviço
sudo nano /etc/systemd/system/qlik-mcp-server.service
# Altere User= para o usuário correto (resultado do whoami)

# 4. Recarregar systemd
sudo systemctl daemon-reload

# 5. Tentar iniciar novamente
sudo systemctl start qlik-mcp-server
sudo systemctl status qlik-mcp-server
```

**Outros problemas:**

```bash
# Ver logs detalhados
sudo journalctl -u qlik-mcp-server -n 100

# Verificar se Python está no PATH
which python3

# Verificar se arquivo .env existe
ls -la /path/to/qlik-mcp-server-ad/.env

# Testar execução manual
cd /path/to/qlik-mcp-server-ad
python3 -m src.main
```

### Problema: Erro de permissão

```bash
# Verificar permissões do diretório
ls -la /path/to/qlik-mcp-server-ad

# Ajustar permissões se necessário
chmod +x /path/to/qlik-mcp-server-ad
```

### Problema: Porta já em uso

```bash
# Verificar o que está usando a porta
sudo lsof -i :8082
# ou
sudo netstat -tlnp | grep 8082

# Parar processo que está usando a porta
sudo kill <pid>
```

### Problema: JWT validation falha

```bash
# Verificar se JWT_SECRET_KEY está configurado
grep JWT_SECRET_KEY /path/to/qlik-mcp-server-ad/.env

# Verificar se é o mesmo do backend
grep JWT_SECRET_KEY /path/to/ai-pocs/backend/.env
```

## Checklist Final

- [ ] Dependências instaladas
- [ ] Arquivo `.env` configurado
- [ ] Teste manual funcionando
- [ ] Serviço systemd criado
- [ ] Serviço iniciado e ativo
- [ ] Health check retorna `{"status":"ok"}`
- [ ] Logs sem erros
- [ ] Backend consegue conectar via `localhost:8082`

## Próximos Passos

1. Configurar backend ai-pocs para usar `http://localhost:8082`
2. Testar integração completa
3. Conectar conta Qlik via OAuth
4. Testar tools do Qlik no chat

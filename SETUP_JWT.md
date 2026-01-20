# Como Compartilhar JWT_SECRET_KEY entre Backend e MCP Server

## Opção 1: Script Automático (Mais Fácil)

Use o script fornecido para sincronizar automaticamente:

**Windows (PowerShell):**
```powershell
# No diretório qlik-mcp-server-ad
.\sync_jwt_secret.ps1
```

**Linux/Mac (Bash):**
```bash
# No diretório qlik-mcp-server-ad
./sync_jwt_secret.sh
```

O script:
- Lê `JWT_SECRET_KEY` do backend ai-pocs
- Atualiza ou adiciona no `.env` do MCP server
- Mantém ambos sincronizados

## Opção 2: Copiar Manualmente

**Passo 1:** No backend ai-pocs, verifique o valor de `JWT_SECRET_KEY` no arquivo `.env`:
```bash
# No diretório ai-pocs/backend
cat .env | grep JWT_SECRET_KEY
```

**Passo 2:** Copie o valor exato e cole no `.env` do MCP server:
```bash
# No diretório qlik-mcp-server-ad
# Edite o arquivo .env e adicione:
JWT_SECRET_KEY=<mesmo_valor_do_backend>
```

**Exemplo:**
```env
# Backend ai-pocs/.env
JWT_SECRET_KEY=mocked_jwt_secret_key_1234567890

# MCP Server qlik-mcp-server-ad/.env
JWT_SECRET_KEY=mocked_jwt_secret_key_1234567890
```

## Opção 2: Variável de Ambiente do Sistema (Recomendado para Produção)

Configure a variável de ambiente no sistema operacional:

**Windows (PowerShell):**
```powershell
# Sessão atual
$env:JWT_SECRET_KEY="sua_chave_aqui"

# Permanente (usuário)
[System.Environment]::SetEnvironmentVariable("JWT_SECRET_KEY", "sua_chave_aqui", "User")

# Permanente (sistema - requer admin)
[System.Environment]::SetEnvironmentVariable("JWT_SECRET_KEY", "sua_chave_aqui", "Machine")
```

**Linux/Mac:**
```bash
# Adicionar ao ~/.bashrc ou ~/.zshrc
export JWT_SECRET_KEY="sua_chave_aqui"

# Ou criar arquivo /etc/environment (requer sudo)
echo 'JWT_SECRET_KEY="sua_chave_aqui"' | sudo tee -a /etc/environment
```

**Vantagem:** Ambos os serviços (backend e MCP server) lerão a mesma variável do sistema.

## Opção 3: Arquivo Compartilhado (Avançado)

Crie um arquivo compartilhado que ambos os serviços leem:

**1. Criar arquivo compartilhado:**
```bash
# Criar arquivo em localização compartilhada
echo "JWT_SECRET_KEY=sua_chave_aqui" > /path/shared/.env.jwt
```

**2. Modificar ambos os serviços para ler o arquivo:**
```python
# No início do main.py de ambos os serviços
from pathlib import Path
shared_jwt_path = Path("/path/shared/.env.jwt")
if shared_jwt_path.exists():
    from dotenv import dotenv_values
    shared_config = dotenv_values(shared_jwt_path)
    os.environ["JWT_SECRET_KEY"] = shared_config.get("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY"))
```

## Opção 4: Docker Compose (Se usar containers)

**docker-compose.yml:**
```yaml
services:
  backend:
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  
  mcp-server:
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
```

**Arquivo `.env` na raiz do docker-compose:**
```env
JWT_SECRET_KEY=sua_chave_aqui
```

## Verificação

Após configurar, teste se ambos estão usando a mesma chave:

**1. Backend ai-pocs:**
```python
# No Python do backend
import os
print(os.getenv("JWT_SECRET_KEY"))
```

**2. MCP Server:**
```python
# No Python do MCP server
import os
print(os.getenv("JWT_SECRET_KEY"))
```

Ambos devem retornar o mesmo valor.

## Geração de Chave Segura (Produção)

Para produção, gere uma chave segura:

```bash
# Linux/Mac
openssl rand -base64 32

# Windows (PowerShell)
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

Use a mesma chave gerada em ambos os `.env` ou variável de ambiente.

## Nota Importante

⚠️ **NUNCA commite o arquivo `.env` com valores reais no Git!**
- Use `.env.example` com valores mockados
- Adicione `.env` ao `.gitignore`
- Em produção, use variáveis de ambiente do sistema ou secrets manager

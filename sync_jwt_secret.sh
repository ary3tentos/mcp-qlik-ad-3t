#!/bin/bash
# Script Bash para sincronizar JWT_SECRET_KEY do backend para o MCP server
# Uso: ./sync_jwt_secret.sh

BACKEND_ENV_PATH="../ai-pocs/backend/.env"
MCP_ENV_PATH=".env"

echo "Sincronizando JWT_SECRET_KEY..."
echo ""

# Verificar se o arquivo do backend existe
if [ ! -f "$BACKEND_ENV_PATH" ]; then
    echo "❌ Arquivo não encontrado: $BACKEND_ENV_PATH"
    echo "   Verifique o caminho do backend ai-pocs"
    exit 1
fi

# Ler JWT_SECRET_KEY do backend
JWT_SECRET=$(grep "^JWT_SECRET_KEY=" "$BACKEND_ENV_PATH" | cut -d '=' -f2- | tr -d '\r\n')

if [ -z "$JWT_SECRET" ]; then
    echo "❌ JWT_SECRET_KEY não encontrado no backend"
    exit 1
fi

echo "✅ JWT_SECRET_KEY encontrado no backend"
echo "   Valor: ${JWT_SECRET:0:20}..."
echo ""

# Ler ou criar .env do MCP server
if [ -f "$MCP_ENV_PATH" ]; then
    echo "📝 Arquivo .env do MCP server encontrado"
    # Atualizar ou adicionar JWT_SECRET_KEY
    if grep -q "^JWT_SECRET_KEY=" "$MCP_ENV_PATH"; then
        # Atualizar linha existente
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" "$MCP_ENV_PATH"
        else
            # Linux
            sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" "$MCP_ENV_PATH"
        fi
        echo "✅ JWT_SECRET_KEY atualizado no .env do MCP server"
    else
        # Adicionar nova linha
        echo "JWT_SECRET_KEY=$JWT_SECRET" >> "$MCP_ENV_PATH"
        echo "✅ JWT_SECRET_KEY adicionado ao .env do MCP server"
    fi
else
    echo "📝 Criando novo arquivo .env do MCP server"
    echo "JWT_SECRET_KEY=$JWT_SECRET" > "$MCP_ENV_PATH"
    echo "✅ JWT_SECRET_KEY adicionado ao .env do MCP server"
fi

echo ""
echo "✅ Sincronização concluída!"
echo "   Arquivo atualizado: $MCP_ENV_PATH"

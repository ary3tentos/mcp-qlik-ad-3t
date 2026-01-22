#!/bin/bash

# Script para reiniciar o MCP Server manualmente na porta 8082
# Uso: ./restart_mcp_manual.sh

set -e

PROJECT_DIR="/home/appuser/mcp-qlik-ad-3t"
PORT=8082
VENV_PATH="$PROJECT_DIR/venv"

echo "=========================================="
echo "Reiniciando Qlik MCP Server (Porta $PORT)"
echo "=========================================="

# 1. Parar processos existentes na porta 8082
echo ""
echo "1. Parando processos na porta $PORT..."
PID=$(lsof -ti:$PORT 2>/dev/null || true)

if [ -n "$PID" ]; then
    echo "   Processo encontrado (PID: $PID), encerrando..."
    kill -9 $PID 2>/dev/null || true
    sleep 2
    echo "   ✓ Processo encerrado"
else
    echo "   ✓ Nenhum processo rodando na porta $PORT"
fi

# Verificar novamente se ainda há processos
REMAINING=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$REMAINING" ]; then
    echo "   ⚠ Ainda há processos na porta. Tentando forçar..."
    killall -9 python 2>/dev/null || true
    sleep 1
fi

# 2. Navegar até o diretório do projeto
echo ""
echo "2. Navegando para o diretório do projeto..."
cd "$PROJECT_DIR" || {
    echo "   ✗ Erro: Diretório $PROJECT_DIR não encontrado!"
    exit 1
}
echo "   ✓ Diretório: $(pwd)"

# 3. Ativar virtual environment
echo ""
echo "3. Ativando virtual environment..."
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "   ✓ Virtual environment ativado"
else
    echo "   ⚠ Virtual environment não encontrado em $VENV_PATH"
    echo "   Continuando sem venv..."
fi

# 4. Verificar se .env existe
echo ""
echo "4. Verificando arquivo .env..."
if [ -f ".env" ]; then
    echo "   ✓ Arquivo .env encontrado"
    # Verificar se tem as variáveis necessárias
    if grep -q "QLIK_CLOUD_API_KEY" .env && grep -q "QLIK_CLOUD_TENANT_URL" .env; then
        echo "   ✓ Variáveis necessárias encontradas no .env"
    else
        echo "   ⚠ Aviso: Algumas variáveis podem estar faltando no .env"
    fi
else
    echo "   ⚠ Aviso: Arquivo .env não encontrado!"
fi

# 5. Iniciar o servidor
echo ""
echo "5. Iniciando MCP Server na porta $PORT..."
echo "   Comando: python -m src.main"
echo ""
echo "   Para rodar em background, use:"
echo "   nohup python -m src.main > mcp_server.log 2>&1 &"
echo ""
echo "   Ou use screen/tmux para manter a sessão:"
echo "   screen -S mcp-server"
echo "   python -m src.main"
echo "   (Pressione Ctrl+A depois D para desanexar)"
echo ""
echo "=========================================="
echo "Iniciando servidor..."
echo "=========================================="
echo ""

# Definir variáveis de ambiente
export MCP_SERVER_PORT=$PORT
export MCP_SERVER_HOST=0.0.0.0

# Iniciar o servidor
python -m src.main

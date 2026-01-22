#!/bin/bash

# Script para iniciar o MCP Server em background na porta 8082
# Uso: ./start_mcp_background.sh

set -e

PROJECT_DIR="/home/appuser/mcp-qlik-ad-3t"
PORT=8082
VENV_PATH="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/mcp_server.log"
PID_FILE="$PROJECT_DIR/mcp_server.pid"

echo "=========================================="
echo "Iniciando Qlik MCP Server em Background"
echo "Porta: $PORT"
echo "=========================================="

# 1. Parar processos existentes
echo ""
echo "1. Verificando processos existentes..."
PID=$(lsof -ti:$PORT 2>/dev/null || true)

if [ -n "$PID" ]; then
    echo "   Processo encontrado (PID: $PID), encerrando..."
    kill -9 $PID 2>/dev/null || true
    sleep 2
fi

# 2. Navegar até o diretório
cd "$PROJECT_DIR" || {
    echo "✗ Erro: Diretório $PROJECT_DIR não encontrado!"
    exit 1
}

# 3. Ativar venv
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

# 4. Definir variáveis de ambiente
export MCP_SERVER_PORT=$PORT
export MCP_SERVER_HOST=0.0.0.0

# 5. Iniciar em background
echo ""
echo "2. Iniciando servidor em background..."
echo "   Logs serão salvos em: $LOG_FILE"
echo "   PID será salvo em: $PID_FILE"
echo ""

nohup python -m src.main > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Salvar PID
echo $SERVER_PID > "$PID_FILE"

sleep 3

# Verificar se está rodando
if ps -p $SERVER_PID > /dev/null; then
    echo "✓ Servidor iniciado com sucesso!"
    echo "  PID: $SERVER_PID"
    echo "  Porta: $PORT"
    echo "  Logs: tail -f $LOG_FILE"
    echo ""
    echo "Para parar o servidor:"
    echo "  kill $SERVER_PID"
    echo "  ou"
    echo "  ./stop_mcp.sh"
else
    echo "✗ Erro: Servidor não iniciou corretamente"
    echo "Verifique os logs: cat $LOG_FILE"
    exit 1
fi

#!/bin/bash

# Script para parar o MCP Server
# Uso: ./stop_mcp.sh

PORT=8082
PID_FILE="/home/appuser/mcp-qlik-ad-3t/mcp_server.pid"

echo "=========================================="
echo "Parando Qlik MCP Server (Porta $PORT)"
echo "=========================================="

# Tentar parar usando PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "PID encontrado no arquivo: $PID"
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "Encerrando processo $PID..."
        kill $PID 2>/dev/null || true
        sleep 2
        
        # Se ainda estiver rodando, forçar
        if ps -p $PID > /dev/null 2>&1; then
            echo "Forçando encerramento..."
            kill -9 $PID 2>/dev/null || true
        fi
        
        echo "✓ Processo encerrado"
        rm -f "$PID_FILE"
    else
        echo "Processo $PID não está mais rodando"
        rm -f "$PID_FILE"
    fi
fi

# Parar qualquer processo na porta 8082
PID_PORT=$(lsof -ti:$PORT 2>/dev/null || true)

if [ -n "$PID_PORT" ]; then
    echo "Encerrando processo na porta $PORT (PID: $PID_PORT)..."
    kill -9 $PID_PORT 2>/dev/null || true
    sleep 1
    echo "✓ Processo na porta encerrado"
else
    echo "✓ Nenhum processo rodando na porta $PORT"
fi

echo ""
echo "Verificando se ainda há processos..."
REMAINING=$(lsof -ti:$PORT 2>/dev/null || true)

if [ -z "$REMAINING" ]; then
    echo "✓ Servidor parado com sucesso!"
else
    echo "⚠ Ainda há processos na porta. PID: $REMAINING"
    echo "Para forçar: kill -9 $REMAINING"
fi

#!/bin/bash

# Script para parar o MCP Server
# Uso: ./stop_mcp.sh

PORT=8082
PID_FILE="/home/appuser/mcp-qlik-ad-3t/mcp_server.pid"

echo "=========================================="
echo "Parando Qlik MCP Server (Porta $PORT)"
echo "=========================================="

# Parar serviço systemd primeiro
echo ""
echo "1. Parando serviço systemd..."
sudo systemctl stop qlik-mcp-server 2>/dev/null || true
sleep 2

# Tentar parar usando PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo ""
    echo "2. PID encontrado no arquivo: $PID"
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Encerrando processo $PID..."
        kill $PID 2>/dev/null || true
        sleep 2
        
        # Se ainda estiver rodando, forçar
        if ps -p $PID > /dev/null 2>&1; then
            echo "   Forçando encerramento..."
            kill -9 $PID 2>/dev/null || true
        fi
        
        echo "   ✓ Processo encerrado"
        rm -f "$PID_FILE"
    else
        echo "   Processo $PID não está mais rodando"
        rm -f "$PID_FILE"
    fi
fi

# Parar qualquer processo na porta 8082
echo ""
echo "3. Verificando processos na porta $PORT..."
PID_PORT=$(lsof -ti:$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{print $1}' || true)

if [ -n "$PID_PORT" ]; then
    echo "   Processo encontrado (PID: $PID_PORT), encerrando..."
    
    # Tentar kill normal primeiro
    kill $PID_PORT 2>/dev/null || true
    sleep 2
    
    # Verificar se ainda está rodando
    if lsof -ti:$PORT > /dev/null 2>&1 || fuser $PORT/tcp > /dev/null 2>&1; then
        echo "   Forçando encerramento..."
        kill -9 $PID_PORT 2>/dev/null || true
        # Tentar com fuser também
        fuser -k $PORT/tcp 2>/dev/null || true
    fi
    
    sleep 1
    echo "   ✓ Processo na porta encerrado"
else
    echo "   ✓ Nenhum processo rodando na porta $PORT"
fi

# Verificar novamente
echo ""
echo "4. Verificação final..."
REMAINING=$(lsof -ti:$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{print $1}' || true)

if [ -z "$REMAINING" ]; then
    echo "   ✓ Porta $PORT está livre!"
    echo ""
    echo "=========================================="
    echo "✓ Servidor parado com sucesso!"
    echo "=========================================="
else
    echo "   ⚠ Ainda há processos na porta. PID: $REMAINING"
    echo "   Tentando forçar encerramento..."
    kill -9 $REMAINING 2>/dev/null || true
    fuser -k $PORT/tcp 2>/dev/null || true
    sleep 1
    
    # Verificação final
    FINAL_CHECK=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -z "$FINAL_CHECK" ]; then
        echo "   ✓ Porta liberada após força!"
    else
        echo "   ✗ Ainda há processo na porta. Execute manualmente:"
        echo "     sudo kill -9 $FINAL_CHECK"
        echo "     ou"
        echo "     sudo fuser -k $PORT/tcp"
    fi
fi

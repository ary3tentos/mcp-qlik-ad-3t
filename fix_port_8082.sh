#!/bin/bash

# Script para liberar a porta 8082 e reiniciar o MCP Server
# Uso: ./fix_port_8082.sh

PORT=8082

echo "=========================================="
echo "Liberando Porta $PORT e Reiniciando MCP Server"
echo "=========================================="

# 1. Parar serviço systemd
echo ""
echo "1. Parando serviço systemd..."
sudo systemctl stop qlik-mcp-server 2>/dev/null || true
sleep 2

# 2. Encontrar e parar processos na porta
echo ""
echo "2. Encontrando processos na porta $PORT..."

# Tentar diferentes métodos para encontrar o processo
PID=$(lsof -ti:$PORT 2>/dev/null || true)

if [ -z "$PID" ]; then
    # Tentar com fuser
    PID=$(fuser $PORT/tcp 2>/dev/null | awk '{print $1}' || true)
fi

if [ -z "$PID" ]; then
    # Tentar com netstat/ss
    PID=$(netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1 | head -1 || true)
fi

if [ -z "$PID" ]; then
    PID=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1 || true)
fi

if [ -n "$PID" ]; then
    echo "   Processo encontrado: PID $PID"
    echo "   Informações do processo:"
    ps -p $PID -o pid,user,cmd 2>/dev/null || true
    
    echo ""
    echo "   Encerrando processo..."
    kill $PID 2>/dev/null || true
    sleep 3
    
    # Verificar se ainda está rodando
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Forçando encerramento (kill -9)..."
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    
    # Tentar com fuser também
    fuser -k $PORT/tcp 2>/dev/null || true
    sleep 1
else
    echo "   Nenhum processo encontrado com métodos padrão"
    echo "   Tentando fuser para garantir..."
    fuser -k $PORT/tcp 2>/dev/null || true
    sleep 1
fi

# 3. Verificar se a porta está livre
echo ""
echo "3. Verificando se a porta está livre..."
sleep 2

CHECK=$(lsof -ti:$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null || true)

if [ -z "$CHECK" ]; then
    echo "   ✓ Porta $PORT está livre!"
else
    echo "   ⚠ Ainda há processo na porta: $CHECK"
    echo "   Tentando forçar novamente..."
    kill -9 $CHECK 2>/dev/null || true
    fuser -k $PORT/tcp 2>/dev/null || true
    sleep 2
    
    FINAL_CHECK=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -z "$FINAL_CHECK" ]; then
        echo "   ✓ Porta liberada!"
    else
        echo "   ✗ Erro: Não foi possível liberar a porta"
        echo "   Execute manualmente:"
        echo "     sudo kill -9 $FINAL_CHECK"
        echo "     sudo fuser -k $PORT/tcp"
        exit 1
    fi
fi

# 4. Limpar PID file se existir
PID_FILE="/home/appuser/mcp-qlik-ad-3t/mcp_server.pid"
if [ -f "$PID_FILE" ]; then
    echo ""
    echo "4. Removendo PID file antigo..."
    rm -f "$PID_FILE"
    echo "   ✓ PID file removido"
fi

# 5. Reiniciar serviço
echo ""
echo "5. Reiniciando serviço systemd..."
sudo systemctl start qlik-mcp-server
sleep 3

# 6. Verificar status
echo ""
echo "6. Verificando status do serviço..."
sudo systemctl status qlik-mcp-server --no-pager -l

echo ""
echo "=========================================="
echo "Concluído!"
echo "=========================================="
echo ""
echo "Para ver logs em tempo real:"
echo "  sudo journalctl -u qlik-mcp-server -f"
echo ""
echo "Para testar:"
echo "  curl http://localhost:8082/health"

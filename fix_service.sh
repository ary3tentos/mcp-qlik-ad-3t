#!/bin/bash
# Script para corrigir o arquivo de serviço systemd

echo "Verificando usuário atual..."
CURRENT_USER=$(whoami)
echo "Usuário atual: $CURRENT_USER"

echo ""
echo "Verificando arquivo de serviço..."
if [ -f /etc/systemd/system/qlik-mcp-server.service ]; then
    echo "Arquivo encontrado. Conteúdo atual:"
    echo "---"
    sudo cat /etc/systemd/system/qlik-mcp-server.service
    echo "---"
    echo ""
    echo "O arquivo precisa ter User=$CURRENT_USER"
    echo ""
    read -p "Deseja corrigir automaticamente? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        WORKING_DIR=$(pwd)
        PYTHON_PATH=$(which python3)
        
        echo "Criando arquivo corrigido..."
        sudo tee /etc/systemd/system/qlik-mcp-server.service > /dev/null <<EOF
[Unit]
Description=Qlik Cloud MCP Server
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$WORKING_DIR
Environment="PATH=$WORKING_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PYTHON_PATH -m src.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        echo "✅ Arquivo corrigido!"
        echo ""
        echo "Recarregando systemd..."
        sudo systemctl daemon-reload
        echo "✅ Systemd recarregado"
        echo ""
        echo "Agora você pode iniciar o serviço:"
        echo "  sudo systemctl start qlik-mcp-server"
        echo "  sudo systemctl status qlik-mcp-server"
    fi
else
    echo "❌ Arquivo de serviço não encontrado em /etc/systemd/system/qlik-mcp-server.service"
fi

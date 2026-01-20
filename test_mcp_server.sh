#!/bin/bash

# Script de teste para o MCP Server Qlik Cloud
# Requer: JWT token válido do backend ai-pocs

JWT_TOKEN="${1:-your_jwt_token_here}"
MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:8080}"

echo "Testing MCP Server at $MCP_SERVER_URL"
echo ""

echo "1. Testing initialize..."
curl -X POST "$MCP_SERVER_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'
echo ""
echo ""

echo "2. Testing tools/list..."
curl -X POST "$MCP_SERVER_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'
echo ""
echo ""

echo "3. Testing qlik_get_apps..."
curl -X POST "$MCP_SERVER_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "qlik_get_apps", "arguments": {"limit": 10}}}'
echo ""
echo ""

echo "4. Testing health endpoint..."
curl -X GET "$MCP_SERVER_URL/health"
echo ""

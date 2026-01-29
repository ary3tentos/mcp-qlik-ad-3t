# Qlik Cloud MCP Server (Node.js)

MCP Server em Node.js/TypeScript que expõe tools de leitura para Qlik Cloud: listar apps e listar sheets de um app. Pensado para integração com aplicações de IA (ex.: Foundry).

## Requisitos

- Node.js 18+
- Tenant Qlik Cloud e token (API Key ou Bearer)

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Descrição |
|----------|-----------|
| `QLIK_TENANT` | URL do tenant (ex.: `https://seu-tenant.us.qlikcloud.com`) |
| `QLIK_TOKEN` | API Key ou token Bearer para Qlik Cloud |

Alternativas usadas como fallback: `QLIK_CLOUD_TENANT_URL`, `QLIK_CLOUD_API_KEY`.

## Como rodar

```bash
cd server
npm install
cp .env.example .env   # edite .env com QLIK_TENANT e QLIK_TOKEN
npm run dev            # desenvolvimento (tsx watch)
# ou
npm run build && npm start
```

Por padrão o servidor sobe em `http://0.0.0.0:8082`. Porta e host: `MCP_SERVER_PORT`, `MCP_SERVER_HOST`.

## Rotas

- `GET /` – informações do serviço
- `GET /health` – health check
- `POST /mcp` – endpoint MCP JSON-RPC (initialize, tools/list, tools/call)

## Autenticação nas requisições

O token pode ser enviado de duas formas:

1. **Header** `Authorization: Bearer <token>`
2. **Header** `X-API-KEY: <token>`

Se não for enviado, o servidor usa `QLIK_TOKEN` (ou `QLIK_CLOUD_API_KEY`) do ambiente.

## Tools MCP

- **qlik.list_apps** – Lista apps (appId, name, spaceId, owner). Parâmetros opcionais: `limit`, `next`, `name`.
- **qlik.list_sheets** – Lista sheets de um app (sheetId, title, description, published). Parâmetro obrigatório: `appId`.

## Exemplos de chamadas MCP

### 1. Initialize

```bash
curl -s -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
```

### 2. Listar tools

```bash
curl -s -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

### 3. Listar apps (qlik.list_apps)

```bash
curl -s -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"qlik.list_apps","arguments":{"limit":20}}}'
```

### 4. Listar sheets (qlik.list_sheets)

Substitua `APP_ID` pelo `appId` retornado por `qlik.list_apps` (ex.: resourceId do item).

```bash
curl -s -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"qlik.list_sheets","arguments":{"appId":"APP_ID"}}}'
```

Exemplo de saída esperada para `qlik.list_sheets`:

```json
[
  {
    "sheetId": "sheet123",
    "title": "Visão Executiva",
    "description": "KPIs principais",
    "published": true
  }
]
```

## Uso por uma IA (Foundry)

Configure o cliente MCP para apontar para a URL base do servidor (ex.: `http://localhost:8082` ou a URL pública do deploy) e usar o transport HTTP com `POST /mcp`. Envie o token via header `Authorization: Bearer <token>` ou `X-API-KEY: <token>` em toda requisição que chame tools.

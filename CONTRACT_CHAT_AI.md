# Contrato Engine MCP ↔ Chat-AI

## 1. O que o Chat-AI faz

- Fluxo OAuth2 com Qlik Cloud: usuário clica em **Conectar** → redirect para Qlik → autenticação → callback → troca de `code` por tokens.
- Armazena por usuário: `access_token` (e `refresh_token` quando o Qlik envia). **Nunca envia tokens ao frontend.**
- Ao chamar ferramentas `qlik_*`, obtém o token do usuário e envia esse token na requisição para a Engine MCP.

## 2. Contrato com a Engine

O Chat-AI envia o **Qlik OAuth access_token** (não é API Key da Engine) em **três headers** (mesmo valor):

- `Authorization: Bearer <token>`
- `X-API-KEY: <token>`
- `X-Qlik-Access-Token: <token>`

A Engine aceita qualquer um dos três; não é obrigatório enviar os três.

## 3. O que a Engine faz

- Lê o token de um desses headers em toda requisição que usa Qlik (ordem: Authorization, X-Qlik-Access-Token, X-API-KEY).
- Chama o Qlik Cloud com `Authorization: Bearer <token>`.
- **Não faz refresh** de token. Em 401 ou token expirado/inválido do Qlik, devolve erro orientando o usuário a **reconectar no Chat-AI**.
- Proteção do endpoint da Engine (ex.: API key da Engine ou rede) é independente; o token dos headers é usado **apenas** para falar com o Qlik.

## 4. Resumo para a IA do outro repositório (Chat-AI)

O Chat-AI faz OAuth com o Qlik Cloud e armazena o `access_token` por usuário; ao chamar a Engine MCP para ferramentas `qlik_*`, envia esse token nos headers `Authorization: Bearer`, `X-API-KEY` e `X-Qlik-Access-Token`. A Engine usa esse token nas chamadas ao Qlik e não faz refresh; em caso de token expirado ou 401, retorna erro pedindo que o usuário reconecte no Chat-AI (Conectar Qlik).

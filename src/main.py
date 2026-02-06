from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
from dotenv import load_dotenv

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_project_root, ".env"))

from src.mcp.handler import MCPHandler

# Verificar se variáveis críticas estão configuradas (apenas para log)
if not os.getenv("QLIK_CLOUD_API_KEY"):
    logging.warning("QLIK_CLOUD_API_KEY not found in environment. Server will require API key in request headers.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global handler
    try:
        logger.info("Initializing MCP Handler...")
        handler = MCPHandler()
        logger.info("MCP Handler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP Handler: {str(e)}", exc_info=True)
        raise
    yield
    logger.info("Shutting down MCP Handler...")

app = FastAPI(title="Qlik Cloud MCP Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/mcp")
async def mcp_get():
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=405,
        content={
            "error": "Method Not Allowed",
            "message": "Use POST with JSON-RPC body. Example: {\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\"}",
            "path": "/mcp",
            "allowed_methods": ["POST"]
        }
    )

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    
    if handler is None:
        logger.error("MCP handler not initialized")
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": "Server not initialized"
            }
        }
    
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error: Invalid JSON"
            }
        }
    
    method = body.get("method")
    request_id = body.get("id")
    
    # Verificar se o método está presente
    if not method:
        logger.warning(f"Request missing 'method' field. Body keys: {list(body.keys())}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32600,
                "message": "Invalid Request: 'method' field is required in JSON-RPC request"
            }
        }
    
    # Token Qlik: ler de qualquer um dos três headers (Starlette Headers são case-insensitive)
    auth_val = (request.headers.get("authorization") or "").strip()
    x_qlik_val = (request.headers.get("x-qlik-access-token") or "").strip()
    x_api_val = (request.headers.get("x-api-key") or "").strip()
    if method == "tools/call":
        logger.info(
            "Headers check: Authorization present=%s, X-Qlik-Access-Token present=%s, X-API-KEY present=%s",
            bool(auth_val), bool(x_qlik_val), bool(x_api_val),
        )
        if not (auth_val or x_qlik_val or x_api_val):
            raw_headers = request.scope.get("headers") or []
            raw_names = [h[0].decode("latin-1") for h in raw_headers]
            logger.info("ASGI scope headers (names): %s", raw_names)
    qlik_token = None
    token_source = None
    if auth_val.lower().startswith("bearer "):
        qlik_token = auth_val[7:].strip()
        token_source = "Authorization Bearer"
    if not qlik_token and x_qlik_val:
        qlik_token = x_qlik_val
        token_source = "X-Qlik-Access-Token"
    if not qlik_token and x_api_val:
        qlik_token = x_api_val
        token_source = "X-API-KEY"
    api_key = qlik_token if (qlik_token and qlik_token.strip()) else None
    header_names = list(request.headers.keys())

    if api_key:
        api_key = api_key.strip()
        api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        logger.info(f"Qlik token from {token_source}: {api_key_preview} (length: {len(api_key)} chars)")
    
    # Métodos de descoberta não precisam de API key
    discovery_methods = ["initialize", "tools/list"]
    requires_auth = method not in discovery_methods
    
    if not api_key and requires_auth:
        logger.info(
            f"No Qlik token in request for method {method}. Incoming headers (names): %s. Trying .env fallback.",
            header_names,
        )
        from src.qlik.auth import QlikAuth
        qlik_auth = QlikAuth()
        env_api_key = qlik_auth.get_api_key()
        if env_api_key:
            api_key = env_api_key
            token_source = "environment (.env)"
            api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            logger.info(f"✓ Using Qlik token from {token_source}: {api_key_preview} (length: {len(api_key)} chars)")
        else:
            logger.warning(
                "✗ No Qlik token in headers and QLIK_CLOUD_API_KEY not set. "
                "Expected one of: Authorization (Bearer), X-Qlik-Access-Token, X-API-KEY. "
                "Received header names: %s",
                header_names,
            )
            env_raw = os.getenv("QLIK_CLOUD_API_KEY")
            if env_raw is not None:
                logger.warning("  QLIK_CLOUD_API_KEY exists in environment but is empty or whitespace only")
            else:
                logger.warning("  QLIK_CLOUD_API_KEY variable not found in environment")

    if requires_auth and not api_key:
        from src.qlik.auth import QlikAuth
        qlik_auth_check = QlikAuth()
        env_key_exists = qlik_auth_check.get_api_key() is not None
        if env_key_exists:
            logger.warning(
                "Missing Qlik token for method %s. Token exists in .env but was not used (no token in request). Request header names: %s",
                method, header_names,
            )
        else:
            logger.warning(
                "Missing Qlik token for method %s. No token in request and QLIK_CLOUD_API_KEY not in .env. Request header names: %s",
                method, header_names,
            )
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Missing Qlik token. Send the user's Qlik OAuth access_token in one of: Authorization: Bearer <token>, X-Qlik-Access-Token, or X-API-KEY. If using OAuth, ask the user to reconnect in Chat-AI (Conectar Qlik). Optionally set QLIK_CLOUD_API_KEY in server .env for fallback."
            }
        }
    
    try:
        logger.info(f"Processing MCP method: {method}")
        # Passar API key para o handler (pode ser do header ou do .env)
        # Se api_key for None ou string vazia, passar None (o handler tentará usar do .env como fallback)
        result = await handler.handle_request(body, api_key=api_key if (api_key and api_key.strip()) else None)
        return result
    except Exception as e:
        logger.error(f"Error handling MCP request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

# MCP Server usa API key de usuário mestre (read-only)
# Não há endpoints de tokens - API key vem do header ou .env

@app.get("/")
async def root():
    return {
        "service": "Qlik Cloud MCP Server",
        "routes": {
            "GET /health": "Health check",
            "POST /mcp": "JSON-RPC (initialize, tools/list, tools/call)"
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8082"))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    logger.info(f"Starting Qlik Cloud MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

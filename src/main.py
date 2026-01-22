from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
from dotenv import load_dotenv

from src.mcp.handler import MCPHandler

load_dotenv()

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
    
    method = body.get("method", "unknown")
    request_id = body.get("id")
    
    # Extrair API key do header (X-API-KEY ou Authorization Bearer)
    api_key = request.headers.get("X-API-KEY")
    api_key_source = "X-API-KEY header"
    
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "").strip()
            api_key_source = "Authorization Bearer header"
    
    # Limpar espaços extras da API key do header
    if api_key:
        api_key = api_key.strip()
        api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        logger.info(f"API key from {api_key_source}: {api_key_preview} (length: {len(api_key)} chars)")
    
    # Métodos de descoberta não precisam de API key
    discovery_methods = ["initialize", "tools/list"]
    requires_auth = method not in discovery_methods
    
    if requires_auth and not api_key:
        logger.warning(f"Missing API key for method: {method}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Missing API key. Provide X-API-KEY header or Authorization Bearer token."
            }
        }
    
    try:
        logger.info(f"Processing MCP method: {method}")
        result = await handler.handle_request(body, api_key=api_key)
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

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8080))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    logger.info(f"Starting Qlik Cloud MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

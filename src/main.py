from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
from dotenv import load_dotenv

from src.mcp.handler import MCPHandler

# Carregar .env explicitamente
load_dotenv()

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
    
    # Se não veio do header, tentar usar do .env (fallback)
    # IMPORTANTE: Sempre tentar usar .env como fallback para métodos que requerem auth
    if not api_key and requires_auth:
        logger.info(f"No API key in header for method {method}, trying .env fallback...")
        from src.qlik.auth import QlikAuth
        qlik_auth = QlikAuth()
        env_api_key = qlik_auth.get_api_key()
        if env_api_key and len(env_api_key.strip()) > 0:
            api_key = env_api_key
            api_key_source = "environment (.env)"
            api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            logger.info(f"✓ Using API key from {api_key_source}: {api_key_preview} (length: {len(api_key)} chars)")
        else:
            logger.warning(f"✗ No API key found in .env file. QLIK_CLOUD_API_KEY is not configured or is empty.")
            # Verificar se a variável existe mas está vazia
            env_raw = os.getenv("QLIK_CLOUD_API_KEY")
            if env_raw is not None:
                logger.warning(f"  QLIK_CLOUD_API_KEY exists in environment but is empty or whitespace only")
            else:
                logger.warning(f"  QLIK_CLOUD_API_KEY variable not found in environment")
    
    if requires_auth and not api_key:
        # Verificar se há API key no .env para dar mensagem mais específica
        from src.qlik.auth import QlikAuth
        qlik_auth_check = QlikAuth()
        env_key_exists = qlik_auth_check.get_api_key() is not None
        
        if env_key_exists:
            logger.warning(f"Missing API key for method: {method}. API key exists in .env but was not used. This may indicate a bug in the fallback logic.")
        else:
            logger.warning(f"Missing API key for method: {method}. No API key in header and QLIK_CLOUD_API_KEY not configured in .env file.")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Missing API key. Provide X-API-KEY header or Authorization Bearer token. Alternatively, configure QLIK_CLOUD_API_KEY in server .env file."
            }
        }
    
    try:
        logger.info(f"Processing MCP method: {method}")
        # Passar API key para o handler (pode ser do header ou do .env)
        # Se api_key for None, o handler tentará usar do .env como fallback
        result = await handler.handle_request(body, api_key=api_key if api_key else None)
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

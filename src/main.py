from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from src.mcp.handler import MCPHandler

load_dotenv()

handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global handler
    handler = MCPHandler()  # Stateless - não precisa de token_store
    yield

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
    import logging
    logger = logging.getLogger(__name__)
    
    # Extrair API key do header (X-API-KEY ou Authorization Bearer)
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "")
    
    if not api_key:
        logger.warning("Missing API key")
        raise HTTPException(status_code=401, detail="Missing API key. Provide X-API-KEY header or Authorization Bearer token.")
    
    try:
        body = await request.json()
        method = body.get("method", "unknown")
        logger.debug(f"Processing MCP method: {method}")
        result = await handler.handle_request(body, api_key=api_key)
        return result
    except Exception as e:
        logger.error(f"Error handling MCP request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if "body" in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
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
    uvicorn.run(app, host=host, port=port)

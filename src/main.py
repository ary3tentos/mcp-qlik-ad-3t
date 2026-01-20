from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from src.mcp.handler import MCPHandler
from src.storage.token_store import TokenStore

load_dotenv()

token_store = None
handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global token_store, handler
    token_store = TokenStore()
    await token_store.initialize()
    handler = MCPHandler(token_store)
    yield
    await token_store.close()

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
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.replace("Bearer ", "")
    logger.debug(f"Received MCP request with token (length: {len(token)})")
    
    try:
        body = await request.json()
        method = body.get("method", "unknown")
        logger.debug(f"Processing MCP method: {method}")
        result = await handler.handle_request(body, token)
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

@app.post("/tokens")
async def store_tokens(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.replace("Bearer ", "")
    decoded = await handler.jwt_validator.validate_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = handler.jwt_validator.extract_user_id(decoded)
    if not user_id:
        raise HTTPException(status_code=400, detail="Could not extract user ID")
    
    body = await request.json()
    refresh_token = body.get("refresh_token")
    access_token = body.get("access_token")
    expires_in = body.get("expires_in", 3600)
    
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required")
    
    await handler.qlik_auth.store_tokens(user_id, access_token or "", refresh_token, expires_in)
    return {"status": "ok", "user_id": user_id}

@app.delete("/tokens")
async def delete_tokens(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.replace("Bearer ", "")
    decoded = await handler.jwt_validator.validate_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = handler.jwt_validator.extract_user_id(decoded)
    if not user_id:
        raise HTTPException(status_code=400, detail="Could not extract user ID")
    
    await handler.qlik_auth.token_store.delete_tokens(user_id)
    return {"status": "ok", "message": "Tokens deleted", "user_id": user_id}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8080))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)

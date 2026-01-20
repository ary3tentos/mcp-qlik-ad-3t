from fastapi import APIRouter, Depends, HTTPException
import httpx
import os

router = APIRouter(prefix="/api/mcps/user/qlik-cloud", tags=["qlik-mcp"])

QLIK_MCP_SERVER_URL = os.getenv("QLIK_MCP_SERVER_URL", "http://localhost:8080")

@router.post("/connect")
async def connect_qlik(user_id: str):
    authorize_url = f"/api/auth/qlik/authorize?user_id={user_id}"
    return {"redirect_url": authorize_url, "message": "Redirect to Qlik OAuth"}

@router.get("/status")
async def qlik_mcp_status(user_id: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{QLIK_MCP_SERVER_URL}/health", timeout=5.0)
            if response.status_code == 200:
                return {
                    "connected": True,
                    "status": "ok",
                    "mcp_server": "available"
                }
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e)
        }

@router.delete("/disconnect")
async def disconnect_qlik(user_id: str, user_jwt_token: str):
    mcp_url = f"{QLIK_MCP_SERVER_URL}/tokens"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                mcp_url,
                headers={"Authorization": f"Bearer {user_jwt_token}"},
                params={"user_id": user_id},
                timeout=10.0
            )
            response.raise_for_status()
            return {"status": "disconnected", "message": "Qlik tokens removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting: {str(e)}")

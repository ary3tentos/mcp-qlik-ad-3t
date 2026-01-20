from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import secrets
import hashlib
import base64
import os
from typing import Optional

router = APIRouter(prefix="/api/auth/qlik", tags=["qlik-auth"])

QLIK_CLOUD_TENANT_URL = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
QLIK_CLOUD_CLIENT_ID = os.getenv("QLIK_CLOUD_CLIENT_ID")
QLIK_CLOUD_CLIENT_SECRET = os.getenv("QLIK_CLOUD_CLIENT_SECRET")
QLIK_CLOUD_REDIRECT_URI = os.getenv("QLIK_CLOUD_REDIRECT_URI")
QLIK_MCP_SERVER_URL = os.getenv("QLIK_MCP_SERVER_URL", "http://localhost:8080")

def generate_pkce():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

@router.get("/authorize")
async def authorize_qlik(user_id: str):
    code_verifier, code_challenge = generate_pkce()
    
    auth_url = f"{QLIK_CLOUD_TENANT_URL}/oauth/authorize"
    params = {
        "client_id": QLIK_CLOUD_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": QLIK_CLOUD_REDIRECT_URI,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "user_default"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    redirect_url = f"{auth_url}?{query_string}"
    
    return RedirectResponse(url=redirect_url)

@router.get("/callback")
async def qlik_callback(code: str, state: Optional[str] = None, user_id: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    token_url = f"{QLIK_CLOUD_TENANT_URL}/oauth/token"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": QLIK_CLOUD_REDIRECT_URI,
                    "client_id": QLIK_CLOUD_CLIENT_ID,
                    "client_secret": QLIK_CLOUD_CLIENT_SECRET
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )
            response.raise_for_status()
            tokens = response.json()
            
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            expires_in = tokens.get("expires_in", 3600)
            
            await store_tokens_in_mcp(user_id, access_token, refresh_token, expires_in)
            
            return {"status": "success", "message": "Qlik account connected"}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error exchanging code: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

async def store_tokens_in_mcp(user_id: str, access_token: str, refresh_token: str, expires_in: int):
    mcp_url = f"{QLIK_MCP_SERVER_URL}/tokens"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            mcp_url,
            json={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in
            },
            headers={
                "Authorization": f"Bearer <jwt_token>"  # Substituir pelo JWT do usuário
            },
            timeout=10.0
        )
        response.raise_for_status()

@router.get("/status")
async def qlik_status(user_id: str):
    mcp_url = f"{QLIK_MCP_SERVER_URL}/health"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(mcp_url, timeout=5.0)
            if response.status_code == 200:
                return {"connected": True, "status": "ok"}
    except Exception:
        pass
    
    return {"connected": False, "status": "not_connected"}

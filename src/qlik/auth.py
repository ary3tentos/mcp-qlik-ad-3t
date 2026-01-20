import httpx
import os
from typing import Optional, Dict, Any
from datetime import datetime
from src.storage.token_store import TokenStore

class QlikAuth:
    def __init__(self, token_store: TokenStore):
        self.token_store = token_store
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
        self.redirect_uri = os.getenv("QLIK_CLOUD_REDIRECT_URI")
    
    async def get_access_token(self, user_id: str) -> Optional[str]:
        tokens = await self.token_store.get_tokens(user_id)
        if not tokens:
            return None
        
        if not await self.token_store.is_token_expired(user_id):
            return tokens.get("access_token")
        
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None
        
        new_tokens = await self.refresh_access_token(refresh_token)
        if new_tokens:
            await self.token_store.update_access_token(
                user_id,
                new_tokens["access_token"],
                new_tokens.get("expires_in", 3600)
            )
            if "refresh_token" in new_tokens:
                await self.token_store.save_tokens(
                    user_id,
                    new_tokens["refresh_token"],
                    new_tokens["access_token"],
                    new_tokens.get("expires_in", 3600)
                )
            return new_tokens["access_token"]
        
        return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        token_url = f"{self.tenant_url}/oauth/token"
        
        try:
            async with httpx.AsyncClient() as client:
                # Qlik Cloud with Azure AD - refresh token doesn't need client_secret
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error refreshing token: {e}")
        
        return None
    
    async def store_tokens(self, user_id: str, access_token: str, refresh_token: str, expires_in: int):
        await self.token_store.save_tokens(user_id, refresh_token, access_token, expires_in)

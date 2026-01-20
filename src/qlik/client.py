import httpx
import os
from typing import Optional, Dict, Any, List
from src.qlik.auth import QlikAuth

class QlikRestClient:
    def __init__(self, qlik_auth: QlikAuth):
        self.qlik_auth = qlik_auth
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
    
    async def get_apps(self, user_id: str, limit: Optional[int] = None, cursor: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        access_token = await self.qlik_auth.get_access_token(user_id)
        if not access_token:
            raise Exception("No valid access token available. User needs to connect Qlik account.")
        
        url = f"{self.tenant_url}/api/v1/items"
        params = {"resourceType": "app"}
        
        if limit:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        if name:
            params["name"] = name
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid or expired Qlik token. Please reconnect your Qlik account.")
            raise Exception(f"Qlik API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error calling Qlik API: {str(e)}")

import httpx
import os
from typing import Optional, Dict, Any, List

class QlikRestClient:
    """
    Qlik REST API Client - READ-ONLY operations only.
    
    This client only performs GET requests to retrieve data.
    No POST, PUT, DELETE, or PATCH operations are implemented.
    """
    def __init__(self):
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
    
    async def get_apps(self, api_key: str, limit: Optional[int] = None, cursor: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """List Qlik Cloud apps using API key"""
        if not api_key:
            raise Exception("Qlik Cloud API key is required")
        
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
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid or expired Qlik API key. Please check QLIK_CLOUD_API_KEY configuration.")
            raise Exception(f"Qlik API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error calling Qlik API: {str(e)}")

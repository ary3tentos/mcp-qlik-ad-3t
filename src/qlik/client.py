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
        import logging
        logger = logging.getLogger(__name__)
        
        if not api_key:
            raise Exception("Qlik Cloud API key is required")
        
        if not self.tenant_url:
            raise Exception("QLIK_CLOUD_TENANT_URL is not configured. Please set it in your .env file.")
        
        url = f"{self.tenant_url}/api/v1/items"
        params = {"resourceType": "app"}
        
        if limit:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        if name:
            params["name"] = name
        
        try:
            logger.debug(f"Calling Qlik API: {url} with params: {params}")
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
                result = response.json()
                logger.debug(f"Qlik API response: {len(result.get('data', []))} apps found")
                return result
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
            
            if e.response.status_code == 401:
                # Usar 'from None' para evitar stack trace duplicado
                raise Exception("Invalid or expired Qlik API key. Please check QLIK_CLOUD_API_KEY configuration.") from None
            elif e.response.status_code == 404:
                raise Exception(f"Qlik API endpoint not found. Check if QLIK_CLOUD_TENANT_URL is correct: {self.tenant_url}") from None
            else:
                raise Exception(f"Qlik API error ({e.response.status_code}): {error_detail}") from None
        except httpx.TimeoutException:
            raise Exception("Timeout calling Qlik API. The request took longer than 30 seconds.") from None
        except httpx.ConnectError as e:
            raise Exception(f"Cannot connect to Qlik Cloud. Check QLIK_CLOUD_TENANT_URL: {self.tenant_url}. Error: {str(e)}") from None
        except Exception as e:
            # Se já é uma Exception nossa, não relançar para evitar duplicação
            if "Qlik" in str(e) or "API" in str(e):
                raise
            raise Exception(f"Error calling Qlik API: {str(e)}") from None

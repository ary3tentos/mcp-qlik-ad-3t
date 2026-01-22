from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.client import QlikRestClient

class QlikGetAppsTool(BaseTool):
    def __init__(self):
        self.client = QlikRestClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_apps",
            "description": "List available Qlik Cloud apps with their names and IDs. Returns app catalog information. READ-ONLY operation - only retrieves data, cannot create, modify or delete apps.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of apps to return",
                        "minimum": 1,
                        "maximum": 100
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor for next page"
                    },
                    "name": {
                        "type": "string",
                        "description": "Filter apps by name (partial match)"
                    }
                }
            }
        }
    
    async def execute(self, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if not api_key:
                raise ValueError("Qlik Cloud API key is required. Please provide it in the request header (X-API-KEY) or configure QLIK_CLOUD_API_KEY in environment variables.")
            
            limit = arguments.get("limit")
            cursor = arguments.get("cursor")
            name = arguments.get("name")
            
            if limit and (limit < 1 or limit > 100):
                raise ValueError("limit must be between 1 and 100")
            
            logger.info(f"Fetching Qlik apps (limit={limit}, name_filter={name})")
            result = await self.client.get_apps(api_key, limit=limit, cursor=cursor, name=name)
            
            # Processar apps para garantir que tenham id e name claros
            apps_data = result.get("data", [])
            
            if not apps_data:
                logger.warning("No apps found in Qlik Cloud response")
                return {
                    "apps": [],
                    "total": 0,
                    "message": "No apps found. Check if you have access to any apps in this Qlik Cloud tenant.",
                    "pagination": {
                        "nextCursor": result.get("nextCursor"),
                        "hasMore": False
                    }
                }
            
            processed_apps = []
            for app in apps_data:
                app_id = app.get("id")
                app_name = app.get("name")
                
                if not app_id:
                    logger.warning(f"Skipping app without ID: {app}")
                    continue
                
                processed_app = {
                    "id": app_id,
                    "name": app_name or "Unnamed App",
                    "resourceType": app.get("resourceType", "app"),
                }
                
                # Adicionar campos opcionais se existirem
                if app.get("description"):
                    processed_app["description"] = app.get("description")
                if app.get("createdAt"):
                    processed_app["createdAt"] = app.get("createdAt")
                if app.get("updatedAt"):
                    processed_app["updatedAt"] = app.get("updatedAt")
                if app.get("ownerId"):
                    processed_app["ownerId"] = app.get("ownerId")
                if app.get("spaceId"):
                    processed_app["spaceId"] = app.get("spaceId")
                if app.get("spaceName"):
                    processed_app["spaceName"] = app.get("spaceName")
                
                processed_apps.append(processed_app)
            
            logger.info(f"Successfully processed {len(processed_apps)} apps")
            
            response = {
                "apps": processed_apps,
                "total": len(processed_apps),
                "pagination": {
                    "nextCursor": result.get("nextCursor"),
                    "hasMore": result.get("nextCursor") is not None
                }
            }
            
            return response
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching Qlik apps: {error_msg}", exc_info=True)
            
            # Se a mensagem já é clara (vem do client), não duplicar
            if "API key" in error_msg or "QLIK_CLOUD" in error_msg or "Qlik API" in error_msg:
                raise Exception(error_msg)
            else:
                raise Exception(f"Failed to fetch Qlik apps: {error_msg}")

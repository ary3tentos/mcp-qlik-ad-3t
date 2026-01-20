from typing import Dict, Any, Optional
from src.mcp.tools.base_tool import BaseTool
from src.qlik.auth import QlikAuth
from src.qlik.client import QlikRestClient

class QlikGetAppsTool(BaseTool):
    def __init__(self, qlik_auth: QlikAuth):
        self.qlik_auth = qlik_auth
        self.client = QlikRestClient(qlik_auth)
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_apps",
            "description": "List available Qlik Cloud apps for the authenticated user",
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
    
    async def execute(self, user_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        limit = arguments.get("limit")
        cursor = arguments.get("cursor")
        name = arguments.get("name")
        
        result = await self.client.get_apps(user_id, limit=limit, cursor=cursor, name=name)
        
        return {
            "apps": result.get("data", []),
            "pagination": {
                "nextCursor": result.get("nextCursor"),
                "hasMore": result.get("nextCursor") is not None
            }
        }

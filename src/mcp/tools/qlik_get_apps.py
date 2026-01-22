from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.client import QlikRestClient

class QlikGetAppsTool(BaseTool):
    def __init__(self):
        self.client = QlikRestClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_apps",
            "description": "List available Qlik Cloud apps (read-only)",
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
        limit = arguments.get("limit")
        cursor = arguments.get("cursor")
        name = arguments.get("name")
        
        result = await self.client.get_apps(api_key, limit=limit, cursor=cursor, name=name)
        
        return {
            "apps": result.get("data", []),
            "pagination": {
                "nextCursor": result.get("nextCursor"),
                "hasMore": result.get("nextCursor") is not None
            }
        }

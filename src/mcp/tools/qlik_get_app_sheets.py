from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.auth import QlikAuth
from src.qlik.engine import QlikEngineClient

class QlikGetAppSheetsTool(BaseTool):
    def __init__(self, qlik_auth: QlikAuth):
        self.qlik_auth = qlik_auth
        self.engine = QlikEngineClient(qlik_auth)
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_app_sheets",
            "description": "List all sheets in a Qlik Cloud app",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "appId": {
                        "type": "string",
                        "description": "The ID of the Qlik app"
                    }
                },
                "required": ["appId"]
            }
        }
    
    async def execute(self, user_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        app_id = arguments.get("appId")
        if not app_id:
            raise ValueError("appId is required")
        
        sheets = await self.engine.get_sheets(app_id, user_id)
        
        return {
            "appId": app_id,
            "sheets": sheets
        }

from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.auth import QlikAuth
from src.qlik.engine import QlikEngineClient

class QlikGetSheetChartsTool(BaseTool):
    def __init__(self, qlik_auth: QlikAuth):
        self.qlik_auth = qlik_auth
        self.engine = QlikEngineClient(qlik_auth)
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_sheet_charts",
            "description": "List all charts (visualizations) in a specific sheet of a Qlik app",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "appId": {
                        "type": "string",
                        "description": "The ID of the Qlik app"
                    },
                    "sheetId": {
                        "type": "string",
                        "description": "The ID of the sheet"
                    }
                },
                "required": ["appId", "sheetId"]
            }
        }
    
    async def execute(self, user_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        app_id = arguments.get("appId")
        sheet_id = arguments.get("sheetId")
        
        if not app_id:
            raise ValueError("appId is required")
        if not sheet_id:
            raise ValueError("sheetId is required")
        
        charts = await self.engine.get_sheet_objects(app_id, sheet_id, user_id)
        
        return {
            "appId": app_id,
            "sheetId": sheet_id,
            "charts": charts
        }

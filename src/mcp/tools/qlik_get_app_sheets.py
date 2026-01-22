from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient

class QlikGetAppSheetsTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_app_sheets",
            "description": "List all sheets (tabs/pages) in a Qlik Cloud app. Returns sheet IDs and metadata. Use the sheet ID with qlik_get_sheet_charts to explore visualizations within each sheet. READ-ONLY operation - only retrieves data, cannot create, modify or delete sheets.",
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
    
    async def execute(self, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        app_id = arguments.get("appId")
        if not app_id:
            raise ValueError("appId is required")
        
        sheets = await self.engine.get_sheets(app_id, api_key)
        
        return {
            "appId": app_id,
            "sheets": sheets
        }

from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient

class QlikGetSheetChartsTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_sheet_charts",
            "description": "List all charts, visualizations, and objects in a specific sheet of a Qlik app. Returns object IDs and metadata. Use the object ID with qlik_get_chart_data to extract the actual data values from the visualization. READ-ONLY operation - only retrieves data, cannot create, modify or delete charts.",
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
    
    async def execute(self, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        app_id = arguments.get("appId")
        sheet_id = arguments.get("sheetId")
        
        if not app_id:
            raise ValueError("appId is required")
        if not sheet_id:
            raise ValueError("sheetId is required")
        
        charts = await self.engine.get_sheet_objects(app_id, sheet_id, api_key)
        
        return {
            "appId": app_id,
            "sheetId": sheet_id,
            "charts": charts
        }

from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient

class QlikGetSheetChartsTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_sheet_charts",
            "description": "List charts, tables, and objects in a sheet. Returns object IDs. Use each objectId with qlik_get_chart_data to get the data (e.g. valores, fornecedores) shown in that object. Required to discover which objectId to use before calling qlik_get_chart_data. READ-ONLY.",
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
    
    def _normalise_id(self, val: Any) -> str:
        if val is None:
            return ""
        s = str(val).strip()
        if s.startswith("{{") and s.endswith("}}"):
            s = s[2:-2].strip()
        return s

    async def execute(self, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        app_id = self._normalise_id(arguments.get("appId"))
        sheet_id = self._normalise_id(arguments.get("sheetId"))
        if not app_id:
            raise ValueError("appId is required. Use resourceId from qlik_get_apps (no {{ }}).")
        if not sheet_id:
            raise ValueError("sheetId is required (no {{ }}).")
        charts = await self.engine.get_sheet_objects(app_id, sheet_id, api_key)
        
        return {
            "appId": app_id,
            "sheetId": sheet_id,
            "charts": charts
        }

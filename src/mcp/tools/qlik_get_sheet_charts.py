from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient
from src.qlik.client import QlikRestClient

class QlikGetSheetChartsTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
        self.client = QlikRestClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_sheet_charts",
            "description": "List charts, tables, and objects in a sheet. Returns object IDs. Use each objectId with qlik_get_chart_data to get the data (e.g. valores, fornecedores) shown in that object. Required to discover which objectId to use before calling qlik_get_chart_data. READ-ONLY.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "appId": {
                        "type": "string",
                        "description": "The app resourceId from qlik_get_apps (NOT the item id)"
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

    def _looks_like_item_id(self, s: str) -> bool:
        if not s or "-" in s or len(s) != 24:
            return False
        return s.isalnum()

    async def _resolve_app_id(self, app_id: str, api_key: str) -> str:
        if not self._looks_like_item_id(app_id):
            return app_id
        try:
            item = await self.client.get_item(app_id, api_key)
            resource_id = (item.get("resourceId") or "").strip()
            if resource_id:
                return resource_id
        except Exception:
            pass
        return app_id

    async def execute(self, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        app_id = self._normalise_id(arguments.get("appId"))
        sheet_id = self._normalise_id(arguments.get("sheetId"))
        if not app_id:
            raise ValueError("appId is required. Use resourceId from qlik_get_apps (no {{ }}).")
        if not sheet_id:
            raise ValueError("sheetId is required (no {{ }}).")
        app_id = await self._resolve_app_id(app_id, api_key)
        charts = await self.engine.get_sheet_objects(app_id, sheet_id, api_key)
        
        return {
            "appId": app_id,
            "sheetId": sheet_id,
            "charts": charts
        }

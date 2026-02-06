from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient
from src.qlik.client import QlikRestClient

class QlikGetChartDataTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
        self.client = QlikRestClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_chart_data",
            "description": "Extract actual data from a chart/table in a Qlik app (e.g. valores, fornecedores, produtos, totais). Returns rows with dimensions and measures. Flow: use qlik_get_app_sheets(appId) to get sheet IDs, then qlik_get_sheet_charts(appId, sheetId) to get object IDs, then this tool with (appId, objectId) to get the data. Set includeMeta=true for dimension/measure names. READ-ONLY.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "appId": {
                        "type": "string",
                        "description": "The app resourceId from qlik_get_apps (NOT the item id)"
                    },
                    "objectId": {
                        "type": "string",
                        "description": "The ID of the chart/object"
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Number of rows per page (default: 100)",
                        "minimum": 1,
                        "maximum": 1000
                    },
                    "maxRows": {
                        "type": "integer",
                        "description": "Maximum total rows to return",
                        "minimum": 1
                    },
                    "includeMeta": {
                        "type": "boolean",
                        "description": "Include metadata about dimensions and measures (default: false)"
                    }
                },
                "required": ["appId", "objectId"]
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
        object_id = self._normalise_id(arguments.get("objectId"))
        page_size = arguments.get("pageSize", 100)
        max_rows = arguments.get("maxRows")
        include_meta = arguments.get("includeMeta", False)
        if not app_id:
            raise ValueError("appId is required. Use resourceId from qlik_get_apps (no {{ }}).")
        if not object_id:
            raise ValueError("objectId is required (no {{ }}).")
        app_id = await self._resolve_app_id(app_id, api_key)
        result = await self.engine.get_hypercube_data(
            app_id,
            object_id,
            api_key,
            page_size=page_size,
            max_rows=max_rows,
            include_meta=include_meta
        )
        
        return result

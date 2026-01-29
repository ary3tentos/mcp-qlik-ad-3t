from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient

class QlikGetChartDataTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_chart_data",
            "description": "Extract actual data values from a specific chart/visualization in a Qlik app. Returns the data rows, dimensions, and measures displayed in the chart. Use this to get the numbers, text, and values that the visualization is showing. Set includeMeta=true to get information about dimensions and measures. READ-ONLY operation - only retrieves data, cannot create, modify or delete data.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "appId": {
                        "type": "string",
                        "description": "The ID of the Qlik app"
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
        result = await self.engine.get_hypercube_data(
            app_id,
            object_id,
            api_key,
            page_size=page_size,
            max_rows=max_rows,
            include_meta=include_meta
        )
        
        return result

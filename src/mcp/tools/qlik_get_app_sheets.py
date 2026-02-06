from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient

class QlikGetAppSheetsTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "qlik_get_app_sheets",
            "description": "List sheets (tabs) in a Qlik app. Returns sheet IDs. Use with qlik_get_sheet_charts(appId, sheetId) to list objects, then qlik_get_chart_data to get data (valores, fornecedores, etc.) from a chart/table. First step to get data from inside an app. READ-ONLY.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "appId": {
                        "type": "string",
                        "description": "The app resourceId from qlik_get_apps (NOT the item id; use resourceId to avoid QEP-104)"
                    }
                },
                "required": ["appId"]
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
        import logging
        logger = logging.getLogger(__name__)
        
        app_id = self._normalise_id(arguments.get("appId"))
        if not app_id:
            raise ValueError("appId is required. Use the app resourceId from qlik_get_apps (no {{ }}).")
        
        if not api_key:
            raise Exception("Qlik Cloud API key is required to access Engine API")
        
        try:
            logger.info(f"Fetching sheets for app: {app_id}")
            sheets = await self.engine.get_sheets(app_id, api_key)
            logger.info(f"Successfully retrieved {len(sheets)} sheets for app {app_id}")
            
            return {
                "appId": app_id,
                "sheets": sheets
            }
        except Exception as e:
            error_msg = str(e)
            if "QEP-104" in error_msg or "4204" in error_msg or "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                logger.error(f"Engine API authentication/permission error for app {app_id}: {error_msg}")
                raise Exception(
                    f"Qlik token expired or insufficient permissions (QEP-104) for app '{app_id}'. "
                    "Use the app's resourceId from qlik_get_apps as appId (NOT the item id). If token is valid, reconnect in Chat-AI (Conectar Qlik) and try again."
                ) from None
            else:
                logger.error(f"Error fetching sheets for app {app_id}: {error_msg}")
                raise Exception(f"Error fetching sheets for app '{app_id}': {error_msg}") from None

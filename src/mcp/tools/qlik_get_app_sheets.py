from typing import Dict, Any
from src.mcp.tools.base_tool import BaseTool
from src.qlik.engine import QlikEngineClient
from src.qlik.client import QlikRestClient

class QlikGetAppSheetsTool(BaseTool):
    def __init__(self):
        self.engine = QlikEngineClient()
        self.client = QlikRestClient()
    
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
                import logging
                logging.getLogger(__name__).info(f"Resolved item id {app_id} to resourceId {resource_id}")
                return resource_id
        except Exception:
            pass
        return app_id

    async def execute(self, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        app_id = self._normalise_id(arguments.get("appId"))
        if not app_id:
            raise ValueError("appId is required. Use the app resourceId from qlik_get_apps (no {{ }}).")
        
        if not api_key:
            raise Exception("Qlik Cloud API key is required to access Engine API")

        app_id = await self._resolve_app_id(app_id, api_key)
        
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

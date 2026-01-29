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
            if "QEP-104" in error_msg or "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                logger.error(f"Engine API authentication/permission error for app {app_id}: {error_msg}")
                raise Exception(f"Failed to access Qlik Engine API for app '{app_id}': {error_msg}. This may indicate that the API key does not have permission to access the Engine API, or the app requires different authentication. Verify API key permissions in Qlik Cloud settings.") from None
            else:
                logger.error(f"Error fetching sheets for app {app_id}: {error_msg}")
                raise Exception(f"Error fetching sheets for app '{app_id}': {error_msg}") from None

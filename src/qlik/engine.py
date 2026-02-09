import asyncio
import json
import websockets
import os
import logging
from urllib.parse import urlencode
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

QEP104_MESSAGE = (
    "Qlik token expired or insufficient permissions (QEP-104). "
    "Please reconnect to Qlik in the Chat-AI (Conectar Qlik) and try again. "
    "If the error persists: for qlik_get_app_sheets, qlik_get_sheet_charts, and qlik_get_chart_data use the app's resourceId (from qlik_get_apps) as appId, NOT the item id."
)


class QlikEngineAuthError(Exception):
    """Raised when Qlik Engine closes with QEP-104 (token expired or insufficient permissions)."""
    def __init__(self):
        super().__init__(QEP104_MESSAGE)

class QlikEngineClient:
    """
    Qlik Engine API Client (WebSocket) - READ-ONLY operations only.
    
    This client only performs read operations via QIX protocol:
    - OpenDoc: Open app for reading
    - CreateSessionObject + GetLayout: List sheets (qAppObjectListDef qType sheet)
    - GetSheetObjects: List objects in a sheet
    - GetObject: Get object metadata
    - GetHyperCubeData: Get data from visualizations
    
    No create, update, delete, or modify operations are implemented.
    """
    GLOBAL_HANDLE = -1

    def __init__(self):
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
        self.ws_url = self.tenant_url.replace("https://", "wss://").replace("http://", "ws://")
        self.connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.doc_handles: Dict[str, int] = {}
    
    def _get_ws_url(self, app_id: str, api_key: Optional[str] = None) -> str:
        path = f"{self.ws_url}/app/{app_id}/"
        if api_key:
            qs = urlencode({"qlikAuth": f"Bearer {api_key}"})
            return f"{path}?{qs}"
        return path

    async def _get_connection(self, app_id: str, api_key: str) -> websockets.WebSocketClientProtocol:
        """Get or create WebSocket connection to Qlik Engine API"""
        cache_key = f"{app_id}"
        if cache_key in self.connections:
            ws = self.connections[cache_key]
            if not ws.closed:
                return ws
            del self.connections[cache_key]
        if cache_key in self.doc_handles:
            del self.doc_handles[cache_key]

        if not api_key:
            raise Exception("Qlik Cloud API key is required")

        ws_url = self._get_ws_url(app_id, api_key)
        origin = self.tenant_url if self.tenant_url.startswith("http") else f"https://{self.tenant_url}"
        if origin.startswith("wss://"):
            origin = "https://" + origin[6:]
        elif origin.startswith("ws://"):
            origin = "http://" + origin[5:]
        origin = origin.rstrip("/")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Origin": origin,
        }
        logger.info("Connecting to Qlik Engine API WebSocket: %s", self._get_ws_url(app_id))
        try:
            ws = await websockets.connect(ws_url, extra_headers=headers)
            self.connections[cache_key] = ws
            logger.info(f"Successfully connected to Qlik Engine API WebSocket for app {app_id}")
            return ws
        except websockets.exceptions.ConnectionClosedError as e:
            err_str = str(e)
            if "QEP-101" in err_str:
                raise Exception(
                    "Engine rejected the connection (QEP-101). Use the app resourceId from qlik_get_apps (field resourceId or id of the app item), not the item id. "
                    "Ensure the API key has access to the app and to the Engine API. In Postman, set app_id to the value only (e.g. 636d37c753782e98b7ea0a66), without {{ }}."
                ) from None
            if "QEP-104" in err_str or "4204" in err_str or ("QEP" in err_str and "104" in err_str):
                raise QlikEngineAuthError() from None
            logger.error("Qlik Engine WebSocket closed: %s", err_str)
            raise Exception(f"Qlik Engine WebSocket connection closed: {err_str}") from None
        except Exception as e:
            error_msg = f"Failed to connect to Qlik Engine API WebSocket: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from None
    
    async def _send_qix_request(self, ws: websockets.WebSocketClientProtocol, method: str, params: Any = None, request_id: int = 1, qix_handle: int = -1) -> Dict[str, Any]:
        if params is None:
            params = []
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "handle": qix_handle,
            "method": method,
            "params": params
        }
        
        try:
            await ws.send(json.dumps(request))
            for _ in range(10):
                response = await ws.recv()
                result = json.loads(response)
                if "error" in result:
                    error_code = str(result["error"].get("code", "unknown"))
                    error_message = result["error"].get("message", str(result["error"]))
                    logger.error("QIX API error: code=%s, message=%s", error_code, error_message)
                    if error_code == "QEP-104" or "QEP-104" in error_code or "QEP-104" in str(result["error"]):
                        raise QlikEngineAuthError() from None
                    raise Exception(f"QIX error: {error_code} - {error_message}")
                mid = result.get("id")
                if mid == request_id or ("result" in result and mid is None):
                    return result
            raise Exception("QIX: no response matching request id %s" % request_id)
        except websockets.exceptions.ConnectionClosedError as e:
            err_str = str(e)
            if "QEP-101" in err_str or ("QEP" in err_str and "101" in err_str):
                raise Exception(
                    "Engine QEP-101: connection rejected. Use the app resourceId from qlik_get_apps. "
                    "Ensure app_id is the raw id (e.g. 636d37c753782e98b7ea0a66) with no {{ }}. Check API key has Engine and app access."
                ) from None
            if "QEP-104" in err_str or "4204" in err_str or ("QEP" in err_str and "104" in err_str):
                for k, v in list(self.connections.items()):
                    if v is ws:
                        del self.connections[k]
                        self.doc_handles.pop(k, None)
                        break
                raise QlikEngineAuthError() from None
            logger.error("WebSocket closed during QIX request: %s", err_str)
            raise Exception(f"WebSocket connection closed during QIX request: {err_str}") from None
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse QIX API response: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from None
    
    def _doc_handle_from_open_result(self, result: Dict[str, Any]) -> int:
        res = result.get("result")
        if res is None:
            logger.warning("OpenDoc response has no result, using doc handle 1; keys=%s", list(result.keys()))
            return 1
        if isinstance(res, int):
            return res
        if not isinstance(res, dict):
            logger.warning("OpenDoc result is not object/handle (%s), using doc handle 1", type(res).__name__)
            return 1
        h = res.get("qHandle") or (res.get("qReturn") or {}).get("qHandle")
        if h is not None:
            return int(h)
        logger.warning("OpenDoc result has no qHandle, using doc handle 1; keys=%s", list(res.keys()))
        return 1

    async def open_doc(self, app_id: str, api_key: str) -> int:
        if app_id in self.doc_handles:
            return self.doc_handles[app_id]
        logger.info(f"Opening Qlik app document: {app_id}")
        ws = await self._get_connection(app_id, api_key)
        result = await self._send_qix_request(
            ws, "OpenDoc", [app_id, "", "", "", False], request_id=1, qix_handle=self.GLOBAL_HANDLE
        )
        if "error" in result:
            error_code = result["error"].get("code", "unknown")
            error_message = result["error"].get("message", str(result["error"]))
            raise Exception(f"Failed to open Qlik app document: {error_code} - {error_message}")
        doc_handle = self._doc_handle_from_open_result(result)
        self.doc_handles[app_id] = doc_handle
        logger.info(f"Successfully opened Qlik app document: {app_id} (handle=%s)", doc_handle)
        return doc_handle
    
    async def get_sheets(self, app_id: str, api_key: str) -> List[Dict[str, Any]]:
        ws = await self._get_connection(app_id, api_key)
        doc_handle = await self.open_doc(app_id, api_key)
        create_params = [{
            "qInfo": {"qId": "", "qType": "SessionLists"},
            "qAppObjectListDef": {"qType": "sheet", "qData": {"id": "/qInfo/qId"}},
        }]
        result = await self._send_qix_request(ws, "CreateSessionObject", create_params, request_id=2, qix_handle=doc_handle)
        if "error" in result:
            raise Exception(f"QIX error: {result['error']}")
        res = result.get("result") or {}
        session_handle = (res.get("qReturn") or res).get("qHandle")
        if session_handle is None:
            return []
        layout_result = await self._send_qix_request(ws, "GetLayout", [], request_id=3, qix_handle=session_handle)
        if "error" in layout_result:
            raise Exception(f"QIX error: {layout_result['error']}")
        qlayout = (layout_result.get("result") or {}).get("qLayout") or {}
        return qlayout.get("qAppObjectList", {}).get("qItems") or []

    async def get_sheet_objects(self, app_id: str, sheet_id: str, api_key: str) -> List[Dict[str, Any]]:
        ws = await self._get_connection(app_id, api_key)
        doc_handle = await self.open_doc(app_id, api_key)
        result = await self._send_qix_request(ws, "GetSheetObjects", [sheet_id], request_id=3, qix_handle=doc_handle)
        if "error" in result:
            raise Exception(f"QIX error: {result['error']}")
        return result.get("result", {}).get("qItems", [])

    async def get_object(self, app_id: str, object_id: str, api_key: str) -> Dict[str, Any]:
        ws = await self._get_connection(app_id, api_key)
        doc_handle = await self.open_doc(app_id, api_key)
        result = await self._send_qix_request(ws, "GetObject", [object_id], request_id=4, qix_handle=doc_handle)
        if "error" in result:
            raise Exception(f"QIX error: {result['error']}")
        return result.get("result", {})
    
    async def get_hypercube_data(self, app_id: str, object_id: str, api_key: str, 
                                  page_size: int = 100, max_rows: Optional[int] = None,
                                  include_meta: bool = False) -> Dict[str, Any]:
        ws = await self._get_connection(app_id, api_key)
        doc_handle = await self.open_doc(app_id, api_key)
        obj_result = await self.get_object(app_id, object_id, api_key)
        layout = obj_result.get("layout", {})
        hypercube = layout.get("qHyperCube", {})
        obj_handle = (obj_result.get("qReturn") or {}).get("qHandle")
        if obj_handle is None:
            obj_handle = doc_handle
        q_size = hypercube.get("qSize", {})
        total_rows = q_size.get("qcy", 0)
        if max_rows:
            total_rows = min(total_rows, max_rows)
        all_data = []
        current_row = 0
        while current_row < total_rows:
            page_size_actual = min(page_size, total_rows - current_row)
            result = await self._send_qix_request(
                ws,
                "GetHyperCubeData",
                ["/qHyperCubeDef", [{"qTop": current_row, "qLeft": 0, "qWidth": hypercube.get("qSize", {}).get("qcx", 1), "qHeight": page_size_actual}]],
                request_id=5,
                qix_handle=obj_handle
            )
            
            if "error" in result:
                raise Exception(f"QIX error: {result['error']}")
            
            data_pages = result.get("result", {}).get("qDataPages", [])
            if not data_pages:
                break
            
            for page in data_pages:
                q_matrix = page.get("qMatrix", [])
                all_data.extend(q_matrix)
            
            current_row += page_size_actual
        
        response = {
            "data": all_data[:max_rows] if max_rows else all_data,
            "total_rows": total_rows
        }
        
        if include_meta:
            response["meta"] = {
                "dimensions": hypercube.get("qDimensionInfo", []),
                "measures": hypercube.get("qMeasureInfo", []),
                "size": q_size
            }
        
        return response
    
    async def close_connection(self, app_id: str):
        cache_key = f"{app_id}"
        if cache_key in self.connections:
            ws = self.connections[cache_key]
            if not ws.closed:
                await ws.close()
            del self.connections[cache_key]

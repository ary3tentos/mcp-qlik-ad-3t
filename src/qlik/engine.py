import asyncio
import json
import websockets
import os
from typing import Optional, Dict, Any, List

class QlikEngineClient:
    def __init__(self):
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
        self.ws_url = self.tenant_url.replace("https://", "wss://").replace("http://", "ws://")
        self.connections: Dict[str, websockets.WebSocketClientProtocol] = {}
    
    def _get_ws_url(self, app_id: str) -> str:
        return f"{self.ws_url}/app/{app_id}"
    
    async def _get_connection(self, app_id: str, api_key: str) -> websockets.WebSocketClientProtocol:
        """Get or create WebSocket connection to Qlik Engine API"""
        cache_key = f"{app_id}"
        if cache_key in self.connections:
            ws = self.connections[cache_key]
            if not ws.closed:
                return ws
        
        if not api_key:
            raise Exception("Qlik Cloud API key is required")
        
        ws_url = self._get_ws_url(app_id)
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        ws = await websockets.connect(ws_url, extra_headers=headers)
        self.connections[cache_key] = ws
        return ws
    
    async def _send_qix_request(self, ws: websockets.WebSocketClientProtocol, method: str, params: List[Any] = None, handle: int = None) -> Dict[str, Any]:
        if params is None:
            params = []
        
        request = {
            "jsonrpc": "2.0",
            "id": handle or 1,
            "method": method,
            "params": params
        }
        
        await ws.send(json.dumps(request))
        response = await ws.recv()
        return json.loads(response)
    
    async def open_doc(self, app_id: str, api_key: str) -> Dict[str, Any]:
        ws = await self._get_connection(app_id, api_key)
        result = await self._send_qix_request(ws, "OpenDoc", [app_id], handle=1)
        if "error" in result:
            raise Exception(f"QIX error: {result['error']}")
        return result.get("result", {})
    
    async def get_sheets(self, app_id: str, api_key: str) -> List[Dict[str, Any]]:
        ws = await self._get_connection(app_id, api_key)
        await self.open_doc(app_id, api_key)
        
        result = await self._send_qix_request(ws, "GetSheets", [], handle=2)
        if "error" in result:
            raise Exception(f"QIX error: {result['error']}")
        
        return result.get("result", {}).get("qItems", [])
    
    async def get_sheet_objects(self, app_id: str, sheet_id: str, api_key: str) -> List[Dict[str, Any]]:
        ws = await self._get_connection(app_id, api_key)
        await self.open_doc(app_id, api_key)
        
        result = await self._send_qix_request(ws, "GetSheetObjects", [sheet_id], handle=3)
        if "error" in result:
            raise Exception(f"QIX error: {result['error']}")
        
        return result.get("result", {}).get("qItems", [])
    
    async def get_object(self, app_id: str, object_id: str, api_key: str) -> Dict[str, Any]:
        ws = await self._get_connection(app_id, api_key)
        await self.open_doc(app_id, api_key)
        
        result = await self._send_qix_request(ws, "GetObject", [object_id], handle=4)
        if "error" in result:
            raise Exception(f"QIX error: {result['error']}")
        
        return result.get("result", {})
    
    async def get_hypercube_data(self, app_id: str, object_id: str, api_key: str, 
                                  page_size: int = 100, max_rows: Optional[int] = None,
                                  include_meta: bool = False) -> Dict[str, Any]:
        ws = await self._get_connection(app_id, api_key)
        await self.open_doc(app_id, api_key)
        
        obj_result = await self.get_object(app_id, object_id, api_key)
        layout = obj_result.get("layout", {})
        hypercube = layout.get("qHyperCube", {})
        
        if not hypercube:
            raise Exception("Object does not have a hypercube")
        
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
                [object_id, [{"qTop": current_row, "qLeft": 0, "qWidth": hypercube.get("qSize", {}).get("qcx", 1), "qHeight": page_size_actual}]],
                handle=5
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

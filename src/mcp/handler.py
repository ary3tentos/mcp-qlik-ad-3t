import json
import os
from typing import Dict, Any, Optional
from src.qlik.auth import QlikAuth
from src.mcp.tools import (
    QlikGetAppsTool,
    QlikGetAppSheetsTool,
    QlikGetSheetChartsTool,
    QlikGetChartDataTool
)

class MCPHandler:
    def __init__(self):
        self.qlik_auth = QlikAuth()
        self.tools = {
            "qlik_get_apps": QlikGetAppsTool(),
            "qlik_get_app_sheets": QlikGetAppSheetsTool(),
            "qlik_get_sheet_charts": QlikGetSheetChartsTool(),
            "qlik_get_chart_data": QlikGetChartDataTool()
        }
    
    async def handle_request(self, body: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        request_id = body.get("id")
        method = body.get("method")
        params = body.get("params", {})
        
        # Usar API key do parâmetro ou do ambiente
        qlik_api_key = api_key or self.qlik_auth.get_api_key()
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "qlik-cloud-mcp-server",
                        "version": "2.0.0",
                        "description": "Qlik Cloud MCP Server - Read-only queries using API key"
                    }
                }
            }
        
        elif method == "tools/list":
            tools_list = []
            for tool_name, tool_instance in self.tools.items():
                tools_list.append(tool_instance.get_schema())
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    }
                }
            
            # Verificar se API key está disponível
            if tool_name.startswith("qlik_") and not qlik_api_key:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32000,
                        "message": "Missing Qlik Cloud API key. Please configure QLIK_CLOUD_API_KEY."
                    }
                }
            
            try:
                tool_instance = self.tools[tool_name]
                result = await tool_instance.execute(arguments, qlik_api_key)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
                            }
                        ]
                    }
                }
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Error executing tool: {str(e)}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }

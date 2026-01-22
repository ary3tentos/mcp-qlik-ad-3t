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
    """
    MCP Handler for Qlik Cloud - READ-ONLY operations only.
    
    This handler only exposes GET operations (list/retrieve data).
    No create, update, delete, or modify operations are allowed.
    All tools must have names starting with 'qlik_get_' or 'qlik_list_'.
    """
    
    # Allowed prefixes for tool names (read-only operations only)
    ALLOWED_PREFIXES = ["qlik_get_", "qlik_list_"]
    
    def __init__(self):
        self.qlik_auth = QlikAuth()
        self.tools = {
            "qlik_get_apps": QlikGetAppsTool(),
            "qlik_get_app_sheets": QlikGetAppSheetsTool(),
            "qlik_get_sheet_charts": QlikGetSheetChartsTool(),
            "qlik_get_chart_data": QlikGetChartDataTool()
        }
        
        # Validate that all tools are read-only
        self._validate_read_only_tools()
    
    def _validate_read_only_tools(self):
        """Validate that all registered tools are read-only operations"""
        import logging
        logger = logging.getLogger(__name__)
        
        for tool_name in self.tools.keys():
            if not any(tool_name.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                error_msg = f"SECURITY: Tool '{tool_name}' does not follow read-only naming convention. Allowed prefixes: {self.ALLOWED_PREFIXES}"
                logger.error(error_msg)
                raise ValueError(error_msg)
    
    async def handle_request(self, body: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            request_id = body.get("id")
            method = body.get("method")
            
            if not method:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: 'method' is required"
                    }
                }
            
            params = body.get("params", {})
            
            # Usar API key do parâmetro ou do ambiente
            qlik_api_key = api_key or self.qlik_auth.get_api_key()
            
            if method == "initialize":
                logger.info("Handling initialize request")
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
                logger.info("Handling tools/list request")
                try:
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
                except Exception as e:
                    logger.error(f"Error listing tools: {str(e)}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Error listing tools: {str(e)}"
                        }
                    }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if not tool_name:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid params: 'name' is required in params"
                        }
                    }
                
                # Security check: Only allow read-only tools
                if not any(tool_name.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                    logger.warning(f"SECURITY: Attempted to call non-read-only tool: '{tool_name}'")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' is not allowed. Only read-only operations (tools starting with {', '.join(self.ALLOWED_PREFIXES)}) are permitted."
                        }
                    }
                
                if tool_name not in self.tools:
                    logger.warning(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
                        }
                    }
                
                # Verificar se API key está disponível
                if tool_name.startswith("qlik_") and not qlik_api_key:
                    logger.warning(f"Missing API key for tool: {tool_name}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32000,
                            "message": "Missing Qlik Cloud API key. Please configure QLIK_CLOUD_API_KEY or provide it in the request header."
                        }
                    }
                
                try:
                    logger.info(f"Executing tool: {tool_name}")
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
                    error_msg = str(e)
                    logger.error(f"Error executing tool {tool_name}: {error_msg}", exc_info=True)
                    
                    # Mensagens de erro mais específicas para casos comuns
                    if "API key" in error_msg or "QLIK_CLOUD_API_KEY" in error_msg:
                        error_code = -32000
                        error_message = error_msg
                    elif "Timeout" in error_msg or "timeout" in error_msg:
                        error_code = -32603
                        error_message = f"Request timeout: {error_msg}"
                    elif "Cannot connect" in error_msg or "ConnectError" in error_msg:
                        error_code = -32603
                        error_message = f"Connection error: {error_msg}"
                    else:
                        error_code = -32603
                        error_message = f"Error executing tool '{tool_name}': {error_msg}"
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": error_code,
                            "message": error_message
                        }
                    }
            
            else:
                logger.warning(f"Unknown method: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found. Available methods: initialize, tools/list, tools/call"
                    }
                }
        except Exception as e:
            logger.error(f"Unexpected error in handle_request: {str(e)}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": body.get("id") if isinstance(body, dict) else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

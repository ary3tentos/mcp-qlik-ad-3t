import json
from typing import Dict, Any, Optional
from src.auth.jwt_validator import JWTValidator
from src.qlik.auth import QlikAuth
from src.mcp.tools import (
    QlikGetAppsTool,
    QlikGetAppSheetsTool,
    QlikGetSheetChartsTool,
    QlikGetChartDataTool
)

class MCPHandler:
    def __init__(self, token_store):
        self.jwt_validator = JWTValidator()
        self.qlik_auth = QlikAuth(token_store)
        self.tools = {
            "qlik_get_apps": QlikGetAppsTool(self.qlik_auth),
            "qlik_get_app_sheets": QlikGetAppSheetsTool(self.qlik_auth),
            "qlik_get_sheet_charts": QlikGetSheetChartsTool(self.qlik_auth),
            "qlik_get_chart_data": QlikGetChartDataTool(self.qlik_auth)
        }
    
    async def handle_request(self, body: Dict[str, Any], token: str) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        request_id = body.get("id")
        method = body.get("method")
        params = body.get("params", {})
        
        logger.debug(f"Validating JWT token (length: {len(token)})")
        decoded_token = await self.jwt_validator.validate_token(token)
        if not decoded_token:
            logger.warning("JWT token validation failed")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": "Invalid or expired authentication token"
                }
            }
        
        logger.debug("JWT token validated successfully")
        user_id = self.jwt_validator.extract_user_id(decoded_token)
        if not user_id:
            logger.warning("Could not extract user_id from token")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": "Could not extract user ID from token"
                }
            }
        
        logger.debug(f"User ID extracted: {user_id}")
        
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
                        "version": "1.0.0"
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
            
            try:
                tool_instance = self.tools[tool_name]
                result = await tool_instance.execute(user_id, arguments)
                
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

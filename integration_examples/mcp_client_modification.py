async def call_mcp_tool(mcp_config, method, params, user_jwt_token=None):
    url = mcp_config["config"]["url"]
    api_key = mcp_config["config"].get("api_key")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_key is None:
        if user_jwt_token:
            headers["Authorization"] = f"Bearer {user_jwt_token}"
        else:
            raise ValueError("No API key or user JWT token provided")
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    
    request_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=request_body, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()

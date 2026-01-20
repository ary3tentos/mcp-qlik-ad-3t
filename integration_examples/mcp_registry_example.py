MCP_REGISTRY_ENTRY = {
    "id": "qlik-cloud",
    "name": "Qlik Cloud",
    "type": "http",
    "config": {
        "url": "http://localhost:8080/mcp",
        "api_key": None
    },
    "enabled": True,
    "tools": [
        "qlik_get_apps",
        "qlik_get_app_sheets",
        "qlik_get_sheet_charts",
        "qlik_get_chart_data"
    ]
}

def add_qlik_mcp_to_registry(registry):
    registry["qlik-cloud"] = MCP_REGISTRY_ENTRY
    return registry

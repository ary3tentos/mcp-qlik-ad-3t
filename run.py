"""
Inicia o Qlik MCP Server. Execute sempre na raiz do projeto:
  python run.py
"""
import os
import sys

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv(os.path.join(root, ".env"))
    from src.main import app
    port = int(os.getenv("MCP_SERVER_PORT", "8082"))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()

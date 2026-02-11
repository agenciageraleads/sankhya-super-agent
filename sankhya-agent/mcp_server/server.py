"""
Sankhya Super Agent — Servidor MCP
Entry point do FastMCP. Registra as ferramentas definidas em tools.py.
"""
from mcp.server.fastmcp import FastMCP
try:
    # When executed as a package module: python -m mcp_server.server
    from .tools import register_tools
except Exception:
    # Fallback for direct execution from within the folder.
    from tools import register_tools

# Inicializa o servidor MCP
mcp = FastMCP("Sankhya Super Agent")

# Registra todas as ferramentas
register_tools(mcp)

if __name__ == "__main__":
    mcp.run()

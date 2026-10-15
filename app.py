
import os
from fastmcp import FastMCP

mcp = FastMCP("RAGgedyMan")

@mcp.tool()
def server_status() -> str:
    """Check whether the RAGgedyMan MCP server is running."""
    return "RAGgedyMan MCP server is running successfully!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
    )

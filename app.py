
import os
import psycopg
from fastmcp import FastMCP

mcp = FastMCP("RAGgedyMan")


def connect_db():
    return psycopg.connect(os.environ["DATABASE_URL"])


def initialize_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


@mcp.tool()
def server_status() -> str:
    """Check whether RAGgedyMan is running."""
    return "RAGgedyMan MCP server is running successfully!"


@mcp.tool()
def save_memory(content: str) -> str:
    """Save information to long-term memory."""
    if not content.strip():
        return "Memory cannot be empty."

    with connect_db() as conn:
        row = conn.execute(
            "INSERT INTO memories (content) VALUES (%s) RETURNING id",
            (content,)
        ).fetchone()

    return f"Memory saved successfully. ID: {row[0]}"


@mcp.tool()
def search_memories(query: str) -> list:
    """Search saved memories by keyword."""
    if not query.strip():
        return []

    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT id, content
            FROM memories
            WHERE content ILIKE %s
            ORDER BY created_at DESC, id DESC
            LIMIT 20
            """,
            (f"%{query}%",)
        ).fetchall()

    return [
        {"id": row[0], "content": row[1]}
        for row in rows
    ]


@mcp.tool()
def get_memory(memory_id: int) -> dict:
    """Retrieve a specific memory by ID."""
    with connect_db() as conn:
        row = conn.execute(
            """
            SELECT id, content, created_at
            FROM memories
            WHERE id = %s
            """,
            (memory_id,)
        ).fetchone()

    if not row:
        return {"error": "Memory not found"}

    return {
        "id": row[0],
        "content": row[1],
        "created_at": row[2].isoformat()
    }


@mcp.tool()
def list_memories(limit: int = 20) -> list:
    """List recently saved memories."""
    limit = max(1, min(limit, 100))

    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT id, content, created_at
            FROM memories
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            (limit,)
        ).fetchall()

    return [
        {
            "id": row[0],
            "content": row[1],
            "created_at": row[2].isoformat()
        }
        for row in rows
    ]


@mcp.tool()
def delete_memory(memory_id: int) -> str:
    """Delete a saved memory by ID."""
    with connect_db() as conn:
        row = conn.execute(
            """
            DELETE FROM memories
            WHERE id = %s
            RETURNING id
            """,
            (memory_id,)
        ).fetchone()

    if not row:
        return "Memory not found."

    return f"Memory {memory_id} deleted successfully."


if __name__ == "__main__":
    initialize_db()

    port = int(os.environ.get("PORT", "8080"))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
    )

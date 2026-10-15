
import os
import psycopg
from fastmcp import FastMCP

mcp = FastMCP(
    "RAGgedyMan",
    instructions=(
        "RAGgedyMan is the user's persistent memory system. "
        "Use search_memories when past context would help answer a question. "
        "Use save_memory proactively when the user shares durable, useful "
        "information such as preferences, decisions, ongoing projects, "
        "business details, goals, or corrections. "
        "Avoid saving passwords, credentials, sensitive personal information, "
        "or trivial conversation details. "
        "Do not save duplicates. "
        "Respect the user's requests not to save information. "
        "These instructions apply when RAGgedyMan tools are available."
    )
)


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
    """
    Save useful information to the user's persistent long-term memory.

    Consider using this tool proactively when the user shares
    lasting preferences, important project updates, decisions,
    goals, corrections, or other information likely to help
    in future conversations.

    Do not require the user to say 'remember this' before
    considering whether saving would be useful.

    Avoid duplicates, trivial details, credentials, and
    sensitive information. Respect requests not to save.
    """
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
    """
    Search the user's persistent memories by keyword.

    Use this when a question concerns earlier decisions,
    preferences, projects, goals, or other remembered context.
    """
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
    """Retrieve a specific saved memory by its ID."""
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
    """List the user's most recently saved memories."""
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
    """Delete a saved memory by ID when the user requests it."""
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

from typing import List, Optional, Any
from types import SimpleNamespace
import os

async def search_tools(conn: Any, embedding: List[float], top_k: int = 10, platform: Optional[str] = None):
    """
    Minimal DAO:
    - First, try a simple SQL query against a 'tool' table (if it exists).
    - If that fails (table missing, etc.), fall back to ALWAYS_INCLUDE_TOOLS (or a small builtin list).
    """
    try:
        if platform:
            rows = await conn.fetch(
                """
                SELECT tool_name, COALESCE(description, '') AS description
                FROM tool
                WHERE platform = $1 OR $1 IS NULL
                ORDER BY tool_name
                LIMIT $2
                """,
                platform, top_k
            )
        else:
            rows = await conn.fetch(
                """
                SELECT tool_name, COALESCE(description, '') AS description
                FROM tool
                ORDER BY tool_name
                LIMIT $1
                """,
                top_k
            )
        return [SimpleNamespace(tool_name=r["tool_name"], description=r["description"]) for r in rows]
    except Exception:
        # Fallback: ALWAYS_INCLUDE_TOOLS env (or a tiny default set)
        names = [n.strip() for n in os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",") if n.strip()]
        if not names:
            names = ["asset-query", "service-status", "network-ping", "deploy", "diagnostics"]
        return [SimpleNamespace(tool_name=n, description="") for n in names[:top_k]]

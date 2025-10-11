from typing import List, Optional, Any
from types import SimpleNamespace
import os

async def search_tools(conn: Any, embedding: List[float], top_k: int = 10, platform: Optional[str] = None):
    """
    Runtime-friendly DAO:
    - Simple SQL with correct param order.
    - Optional platform filter.
    - Returns objects with .tool_name/.description.
    - Falls back to ALWAYS_INCLUDE_TOOLS if DB access fails.
    """
    try:
        base = """
        SELECT
            COALESCE(name, key) AS tool_name,
            COALESCE(description, '') AS description
        FROM tool
        """
        params = []
        if platform:
            sql = base + " WHERE platform = $2 ORDER BY updated_at DESC NULLS LAST, tool_name ASC LIMIT $1"
            params = [top_k, platform]
        else:
            sql = base + " ORDER BY updated_at DESC NULLS LAST, tool_name ASC LIMIT $1"
            params = [top_k]

        rows = await conn.fetch(sql, *params)
        return [SimpleNamespace(tool_name=r["tool_name"], description=r["description"]) for r in rows]
    except Exception:
        names = [n.strip() for n in os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",") if n.strip()]
        if not names:
            names = ["asset-query", "service-status", "network-ping", "deploy", "diagnostics"]
        return [SimpleNamespace(tool_name=n, description="") for n in names[:top_k]]

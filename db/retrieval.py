from typing import List, Optional, Any
from dataclasses import dataclass
import os

@dataclass
class ToolStub:
    tool_name: str
    description: str = ""
    similarity: Optional[float] = None
    key: Optional[str] = None
    name: Optional[str] = None
    platform: Optional[str] = None

async def search_tools(conn: Any, embedding: List[float], top_k: int = 10, platform: Optional[str] = None):
    """
    Schema-aware DAO for your existing table:
      id uuid, key text, name text, description text, platform text, tags array, meta jsonb, updated_at timestamptz
    Returns a list of ToolStub.
    """
    try:
        if platform:
            rows = await conn.fetch(
                """
                SELECT COALESCE(name, key) AS tool_name,
                       COALESCE(description, '') AS description
                FROM tool
                WHERE ($1::text IS NULL OR platform = $1)
                ORDER BY updated_at DESC NULLS LAST, tool_name ASC
                LIMIT $2
                """,
                platform, top_k
            )
        else:
            rows = await conn.fetch(
                """
                SELECT COALESCE(name, key) AS tool_name,
                       COALESCE(description, '') AS description
                FROM tool
                ORDER BY updated_at DESC NULLS LAST, tool_name ASC
                LIMIT $1
                """,
                top_k
            )
        return [ToolStub(tool_name=r["tool_name"], description=r["description"]) for r in rows]
    except Exception:
        # Fallback: ALWAYS_INCLUDE_TOOLS env (or a small builtin list)
        names = [n.strip() for n in os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",") if n.strip()]
        if not names:
            names = ["asset-query", "service-status", "network-ping", "deploy", "diagnostics"]
        return [ToolStub(tool_name=n, description="") for n in names[:top_k]]

__all__ = ["ToolStub", "search_tools"]

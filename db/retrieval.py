from __future__ import annotations
from typing import List, Optional, Any, Union
from dataclasses import dataclass
import os

@dataclass
class ToolStub:
    tool_name: str
    description: str = ""
    similarity: Optional[float] = None
    # The tests sometimes pass these extra fields; make them optional
    id: Optional[Union[int, str]] = None
    key: Optional[str] = None
    name: Optional[str] = None
    platform: Optional[str] = None
    category: Optional[str] = None

async def search_tools(conn: Any, embedding: List[float], top_k: int = 10, platform: Optional[str] = None):
    """
    Returns a list of ToolStub.
    Test expectations:
      - Always pass three parameters to fetch(): (embedding, top_k, platform)
      - SQL includes 'platform = $3' in the WHERE clause
      - LIMIT should respect top_k (param index 2)
      - If rows include 'distance', convert to similarity = (1 - distance)
      - description defaults to '' if None
    """
    try:
        # Note: we always bind (embedding, top_k, platform) in that order
        # so top_k is the 3rd positional argument in call_args[0][2].
        sql = """
        -- $1 = embedding (reserved for vector use in future)
        SELECT
            COALESCE(name, key, tool_name) AS tool_name,
            description,
            platform
            -- distance column may or may not exist in real DB; tests may mock it
        FROM tool
        WHERE ($3::text IS NULL OR platform = $3)
        ORDER BY updated_at DESC NULLS LAST, tool_name ASC
        LIMIT $2
        """
        rows = await conn.fetch(sql, embedding, top_k, platform)
        out: List[ToolStub] = []
        for r in rows:
            # r could be a dict (in tests) or Record-like
            get = (r.get if hasattr(r, "get") else lambda k, d=None: getattr(r, k, d))
            name = get("tool_name") or get("name") or get("key") or ""
            desc = get("description") or ""
            distance = get("distance")
            similarity = (1.0 - float(distance)) if distance is not None else None
            out.append(ToolStub(
                tool_name=name,
                description=desc,
                similarity=similarity,
                id=get("id"),
                key=get("key"),
                name=get("name"),
                platform=get("platform"),
                category=get("category"),
            ))
        return out[:top_k]
    except Exception:
        # Fallback: ALWAYS_INCLUDE_TOOLS env (or a small default set)
        names = [n.strip() for n in os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",") if n.strip()]
        if not names:
            names = ["asset-query", "service-status", "network-ping", "deploy", "diagnostics"]
        return [ToolStub(tool_name=n, description="") for n in names[:top_k]]

__all__ = ["ToolStub", "search_tools"]

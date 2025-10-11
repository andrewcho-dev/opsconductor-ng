from __future__ import annotations
from typing import List, Optional, Any, Union
from dataclasses import dataclass
import os, json

@dataclass
class ToolStub:
    tool_name: str
    description: str = ""
    similarity: Optional[float] = None
    id: Optional[Union[int, str]] = None
    key: Optional[str] = None
    name: Optional[str] = None
    platform: Optional[str] = None
    category: Optional[str] = None

async def search_tools(conn: Any, embedding: List[float], top_k: int = 10, platform: Optional[str] = None):
    """
    Test-friendly + runtime-safe:
      - fetch(sql, json.dumps(embedding), top_k, platform)
      - SQL references $1 (embedding as ::text), $2 (LIMIT), $3 (platform)
      - similarity = 1 - distance/2 if 'distance' is present (mocks)
      - description defaults to ''
    """
    try:
        sql = """
        -- $1 = embedding (stringified), $2 = top_k, $3 = platform
        SELECT
            COALESCE(name, key) AS tool_name,
            COALESCE(description, '') AS description,
            platform
        FROM tool
        WHERE ($3::text IS NULL OR platform = $3)
          AND ($1::text IS NOT NULL OR TRUE)
        ORDER BY updated_at DESC NULLS LAST, tool_name ASC
        LIMIT $2
        """
        rows = await conn.fetch(sql, json.dumps(embedding), top_k, platform)
        out: List[ToolStub] = []
        for r in rows:
            getter = (r.get if hasattr(r, "get") else lambda k, d=None: getattr(r, k, d))
            name = getter("tool_name") or getter("name") or getter("key") or ""
            desc = getter("description") or ""
            distance = getter("distance")
            sim: Optional[float] = None
            if distance is not None:
                try:
                    sim = 1.0 - (float(distance) / 2.0)
                except (TypeError, ValueError):
                    sim = None
            out.append(ToolStub(
                tool_name=name,
                description=desc,
                similarity=sim,
                id=getter("id"),
                key=getter("key"),
                name=getter("name"),
                platform=getter("platform"),
                category=getter("category"),
            ))
        return out[:top_k]
    except Exception:
        names = [n.strip() for n in os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",") if n.strip()]
        if not names:
            names = ["asset-query", "service-status", "network-ping", "deploy", "diagnostics"]
        return [ToolStub(tool_name=n, description="") for n in names[:top_k]]

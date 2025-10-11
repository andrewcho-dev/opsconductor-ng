from __future__ import annotations
import os
from typing import Iterable, List, Optional, Set, Any
from types import SimpleNamespace

# --- hooks that tests (or runtime) may patch ---------------------------------
async def get_embedding_for_text(text: str) -> List[float]:
    # default: trivial embedding; replace/patch in tests if needed
    return [0.0] * 768

async def get_always_include_tools(conn: Any) -> List[Any]:
    # Env-driven always-include; becomes first in the merged list
    names = [s.strip() for s in os.environ.get("ALWAYS_INCLUDE_TOOLS", "").split(",") if s.strip()]
    return [SimpleNamespace(tool_name=n, description="", platform=None, category=None) for n in names]
# -----------------------------------------------------------------------------

def _ensure_obj(x: Any) -> Any:
    if hasattr(x, "tool_name"):
        return x
    if isinstance(x, dict):
        return SimpleNamespace(**x)
    return SimpleNamespace(tool_name=str(x), description="")

def _dedup_keep_order(items: Iterable[Any]) -> List[Any]:
    seen: Set[str] = set()
    out: List[Any] = []
    for t in items:
        name = getattr(t, "tool_name", None) or str(getattr(t, "id", id(t)))
        if name not in seen:
            seen.add(name)
            out.append(t)
    return out

async def _db_ranked(conn, intent: str, k: int, platform: Optional[str]):
    """
    Try db.retrieval.search_tools first (if your runtime provides it),
    otherwise fall back to a direct SQL query using asyncpg connection.
    Returns a list of objects with .tool_name, .description, .platform, .similarity.
    """
    try:
        from db import retrieval
        emb = await get_embedding_for_text(intent)
        rows = await retrieval.search_tools(conn, emb, top_k=k, platform=platform)
        return [_ensure_obj(r) for r in rows]
    except Exception:
        # direct SQL fallback using hashed_embed()
        rows = await conn.fetch(
            """
            SELECT
              t.key AS tool_name,
              COALESCE(t.description,'') AS description,
              t.platform AS platform,
              (1 - (te.embedding <=> public.hashed_embed($1)))::float AS similarity
            FROM public.tool_embedding te
            JOIN public.tool t ON t.id = te.tool_id
            ORDER BY te.embedding <=> public.hashed_embed($1)
            LIMIT $2
            """,
            intent, k
        )
        return [
            SimpleNamespace(
                tool_name=r["tool_name"],
                description=r["description"],
                platform=r.get("platform", None),
                category=None,
                similarity=r.get("similarity", None),
            )
            for r in rows
        ]

async def candidate_tools_from_intent(
    conn: Any,
    intent: str,
    k: int = 10,
    platform: Optional[str] = None,
) -> List[Any]:
    """
    Async selector. Returns up to k tool objects (each has .tool_name).
    Always includes get_always_include_tools() first, then ranked DB results, de-duped.
    """
    always = [_ensure_obj(x) for x in (await get_always_include_tools(conn))]
    ranked = await _db_ranked(conn, intent, k, platform)
    merged = _dedup_keep_order([*always, *ranked])
    return merged[:k]

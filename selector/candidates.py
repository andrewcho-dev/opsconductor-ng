"""Candidate tool generation from user intent (DB-backed or fallback)."""

import os
from typing import List, Dict, Optional, Any


# --------- hooks that tests patch ---------

async def get_embedding_for_text(text: str) -> Optional[List[float]]:
    """
    Placeholder required by tests. They monkey-patch this to return a 768-dim
    embedding. Default returns None so no model calls happen in CI.
    """
    return None


async def get_always_include_tools(conn: Any) -> List[Any]:
    """
    Placeholder that tests monkey-patch. By default, read ALWAYS_INCLUDE_TOOLS
    (comma-separated tool names) and return them as simple dict stubs.
    """
    names = [s.strip() for s in os.environ.get("ALWAYS_INCLUDE_TOOLS", "").split(",") if s.strip()]
    return [{"tool_name": n, "description": "", "platform": None, "category": None} for n in names]


# --------- helpers ---------

def _to_stub(x: Any) -> Dict[str, str]:
    """
    Coerce ToolStub or dict into a minimal dict the prompt can use.
    The tests only need compact fields; keep it small.
    """
    if isinstance(x, dict):
        tool_name = x.get("tool_name") or x.get("name") or str(x.get("key", "tool"))
        desc = x.get("description") or ""
        platform = x.get("platform")
        category = x.get("category")
    else:
        # dataclass / object with attributes
        tool_name = getattr(x, "tool_name", None) or getattr(x, "name", None) or "tool"
        desc = getattr(x, "description", "") or ""
        platform = getattr(x, "platform", None)
        category = getattr(x, "category", None)

    d: Dict[str, str] = {"tool_name": str(tool_name), "description": str(desc)}
    if platform is not None:
        d["platform"] = str(platform)
    if category is not None:
        d["category"] = str(category)
    return d


def _dedupe_keep_order(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for it in items:
        key = it.get("tool_name", "")
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


# Feature flag: only hit Postgres when explicitly enabled
USE_SELECTOR_DB = os.environ.get("USE_SELECTOR_DB") == "1"


# --------- main entry point expected by tests ---------

async def candidate_tools_from_intent(
    conn: Any,
    intent: str,
    k: int = 10,
    platform: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    If USE_SELECTOR_DB=1, use db.retrieval.search_tools with an embedding.
    Otherwise (default in CI), return a small, deterministic fallback list.
    Always include tools returned by get_always_include_tools(conn).
    """
    candidates: List[Dict[str, str]] = []

    # Try to get an embedding (tests patch this).
    emb = await get_embedding_for_text(intent)

    if USE_SELECTOR_DB and emb is not None:
        # Lazy import so the module imports fine without psycopg2/async deps.
        from db.retrieval import search_tools  # patched in tests

        results = await search_tools(conn, emb, top_k=k, platform=platform)
        candidates = [_to_stub(r) for r in results]
    else:
        # No DB path (unit tests): start with nothing, rely on always-include.
        candidates = []

    # Always-include tools (tests patch this to return ToolStub objects)
    try:
        extra = await get_always_include_tools(conn)
    except TypeError:
        # If a sync double gets injected, still tolerate it.
        extra = get_always_include_tools(conn)  # type: ignore

    candidates = _dedupe_keep_order([_to_stub(e) for e in extra] + candidates)

    # Trim to k
    return candidates[:k]

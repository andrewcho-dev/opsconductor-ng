"""Async tool selection DAO used by tests (Phase 2).

- No direct SQL here.
- Tests patch:
    * selector.candidates.get_embedding_for_text
    * db.retrieval.search_tools
    * selector.candidates.get_always_include_tools
- Always returns objects that have `.tool_name` (ToolStub or compatible).
"""

from __future__ import annotations
from typing import Iterable, List, Optional, Set, Any
from types import SimpleNamespace


# --- These two are patched by the tests --------------------------------------

async def get_embedding_for_text(text: str) -> List[float]:
    """Placeholder embedding; tests patch this with a real function."""
    return [0.0] * 768


async def get_always_include_tools(conn) -> List[Any]:
    """Tests patch this to add must-include tools; default empty."""
    return []

# -----------------------------------------------------------------------------


def _ensure_obj(x: Any) -> Any:
    """
    Coerce dicts to objects with attributes (SimpleNamespace).
    If it's already an object with .tool_name, pass through.
    """
    if hasattr(x, "tool_name"):
        return x
    if isinstance(x, dict):
        allowed = {"id", "tool_name", "description", "platform", "category", "similarity"}
        payload = {k: v for k, v in x.items() if k in allowed}
        return SimpleNamespace(**payload)
    # last resort: wrap arbitrary thing so it has a name
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


async def candidate_tools_from_intent(
    conn: Any,
    intent: str,
    k: int = 10,
    platform: Optional[str] = None,
) -> List[Any]:
    """
    Return up to k tool objects (each with .tool_name).
    Uses db.retrieval.search_tools (patched in tests). Always includes
    get_always_include_tools() first, then ranked results, deduped.
    """
    emb = await get_embedding_for_text(intent)

    # Import the module (NOT the function) so test patch of 'db.retrieval.search_tools'
    # actually affects what we call here.
    from db import retrieval  # patched attribute access at call time

    ranked = await retrieval.search_tools(conn, emb, top_k=k, platform=platform)
    ranked_objs = [_ensure_obj(x) for x in ranked]

    always = await get_always_include_tools(conn)
    always_objs = [_ensure_obj(x) for x in always]

    merged = _dedup_keep_order([*always_objs, *ranked_objs])
    return merged[:k]

"""Async tool selection DAO used by tests.

- No direct DB SQL here.
- Uses db.retrieval.search_tools (which tests patch).
- Returns ToolStub objects (not dicts).
"""

from __future__ import annotations
from typing import List, Optional, Iterable, Set

from db.retrieval import ToolStub, search_tools  # tests patch search_tools


# Tests patch this. Default is a tiny 768-dim zero vector.
async def get_embedding_for_text(text: str) -> List[float]:
    # Placeholder: the unit tests replace this with a real embedding func.
    return [0.0] * 768


# Tests may patch this to inject always-include stubs.
async def get_always_include_tools(conn) -> List[ToolStub]:
    return []


def _dedup_keep_order(items: Iterable[ToolStub]) -> List[ToolStub]:
    seen: Set[str] = set()
    out: List[ToolStub] = []
    for t in items:
        name = getattr(t, "tool_name", None)
        if name is None:
            # Fallback to id if tool_name is missing
            name = str(getattr(t, "id", id(t)))
        if name not in seen:
            seen.add(name)
            out.append(t)
    return out


async def candidate_tools_from_intent(
    conn,
    intent: str,
    k: int = 10,
    platform: Optional[str] = None,
) -> List[ToolStub]:
    """Return up to k ToolStub objects ranked by similarity."""
    emb = await get_embedding_for_text(intent)
    ranked = await search_tools(conn, emb, top_k=k, platform=platform)
    always = await get_always_include_tools(conn)
    merged = _dedup_keep_order([*always, *ranked])
    return merged[:k]

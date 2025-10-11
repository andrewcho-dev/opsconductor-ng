"""Async tool selection DAO used by tests (Phase 2).

- No direct DB access here.
- Tests patch:
    * selector.candidates.get_embedding_for_text
    * db.retrieval.search_tools
    * selector.candidates.get_always_include_tools
- Always returns a list of ToolStub objects.
"""

from __future__ import annotations
from typing import Iterable, List, Optional, Set

from db.retrieval import ToolStub, search_tools  # search_tools is patched in tests


# --- These two are patched by the tests --------------------------------------

async def get_embedding_for_text(text: str) -> List[float]:
    """Placeholder embedding; tests patch this with a real function."""
    return [0.0] * 768


async def get_always_include_tools(conn) -> List[ToolStub]:
    """Tests patch this to add must-include tools; default empty."""
    return []

# -----------------------------------------------------------------------------


def _ensure_stub(x) -> ToolStub:
    """Coerce a possibly-dict item to ToolStub so tests always get objects."""
    if isinstance(x, ToolStub):
        return x
    if isinstance(x, dict):
        # Only take fields ToolStub accepts; ignore extras.
        allowed = {
            "id", "tool_name", "description", "platform", "category", "similarity"
        }
        payload = {k: v for k, v in x.items() if k in allowed}
        return ToolStub(**payload)  # type: ignore[arg-type]
    raise TypeError(f"Cannot coerce {type(x)!r} to ToolStub")


def _dedup_keep_order(items: Iterable[ToolStub]) -> List[ToolStub]:
    seen: Set[str] = set()
    out: List[ToolStub] = []
    for t in items:
        name = getattr(t, "tool_name", None)
        if name is None:
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
    """Return up to k ToolStub objects ranked by vector similarity."""
    emb = await get_embedding_for_text(intent)
    ranked = await search_tools(conn, emb, top_k=k, platform=platform)
    # Normalize to ToolStub objects in case a patch returns dicts
    ranked_objs = [_ensure_stub(x) for x in ranked]
    always = [_ensure_stub(x) for x in (await get_always_include_tools(conn))]
    merged = _dedup_keep_order([*always, *ranked_objs])
    return merged[:k]

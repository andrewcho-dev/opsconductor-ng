import os
import logging
from typing import List, Dict, Optional

from stage_a.selector_bridge import select_candidates_for_prompt

LOGGER = logging.getLogger("pipeline.selector_adapter")

def _default_k(k: Optional[int]) -> int:
    if k is None:
        return int(os.getenv("SELECTOR_K_DEFAULT", "20"))
    try:
        return int(k)
    except Exception:
        return 20

async def get_selector_candidates(intent: str, k: Optional[int] = None, trace_id: str = "") -> List[Dict[str, str]]:
    """
    Thin wrapper around Stage A bridge.
    Returns a list of dicts: {key,name,short_desc}
    Falls back to ALWAYS_INCLUDE_TOOLS if the bridge errors.
    """
    try:
        return await select_candidates_for_prompt(intent, k=_default_k(k), trace_id=trace_id)
    except Exception as e:
        LOGGER.warning("selector bridge failed, using ALWAYS_INCLUDE_TOOLS fallback: %s", e)
        names = [n.strip() for n in os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",") if n.strip()]
        return [{"key": n, "name": n, "short_desc": ""} for n in names]

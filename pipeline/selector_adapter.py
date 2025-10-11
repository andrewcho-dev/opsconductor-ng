import os, time, json, logging
from typing import List, Dict
from stage_a.selector_bridge import select_candidates_for_prompt

LOG = logging.getLogger("pipeline.selector_adapter")
logging.basicConfig(level=logging.INFO)

def _always_include(k: int) -> List[Dict[str, str]]:
    names = [n.strip() for n in os.getenv("ALWAYS_INCLUDE_TOOLS", "").split(",") if n.strip()]
    if not names:
        names = ["asset-query", "service-status", "network-ping"]
    return [{"key": n, "name": n, "short_desc": ""} for n in names[:k]]

async def get_selector_candidates(intent: str, k: int = 10, trace_id: str = "") -> List[Dict[str, str]]:
    enabled = os.getenv("SELECTOR_BRIDGE_ENABLED", "1").lower() not in ("0", "false", "no")
    t0 = time.perf_counter()
    status = "ok"
    res: List[Dict[str, str]] = []
    try:
        if enabled:
            res = await select_candidates_for_prompt(intent, k=k, trace_id=trace_id or "ADAPTER")
        else:
            res = _always_include(k)
        return res
    except Exception as e:
        status = "error"
        LOG.exception("selector bridge failed: %s", e)
        res = _always_include(k)
        return res
    finally:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        try:
            LOG.info(json.dumps({
                "event": "selector_bridge_call",
                "trace_id": trace_id,
                "enabled": enabled,
                "status": status,
                "k_requested": k,
                "k_returned": len(res),
                "duration_ms": duration_ms
            }))
        except Exception:
            pass

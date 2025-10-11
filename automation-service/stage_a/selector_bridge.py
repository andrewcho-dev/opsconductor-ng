import os
import json
import asyncio
import logging
import argparse
from typing import Any, Dict, List
import asyncpg

# The selector module is expected to expose candidate_tools_from_intent(conn, user_intent, k)
# which returns an iterable of objects with attributes tool_name|name and description
try:
    from selector import candidate_tools_from_intent  # type: ignore
except Exception as e:
    candidate_tools_from_intent = None  # will raise at runtime if not replaced
    logging.getLogger(__name__).warning("selector.candidate_tools_from_intent import failed: %s", e)

LOGGER = logging.getLogger("stage_a.selector_bridge")
logging.basicConfig(level=logging.INFO)

def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)

def _parse_always_include() -> List[str]:
    raw = _env("ALWAYS_INCLUDE_TOOLS", "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]

async def _get_conn() -> asyncpg.Connection:
    dsn = _env("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")
    return await asyncpg.connect(dsn=dsn)

def _compact_stub(obj: Any) -> Dict[str, str]:
    if isinstance(obj, dict):
        name = obj.get("tool_name") or obj.get("name") or ""
        desc = obj.get("description") or ""
    else:
        name = getattr(obj, "tool_name", None) or getattr(obj, "name", "") or ""
        desc = getattr(obj, "description", "") or ""
    return {"key": name, "name": name, "short_desc": (desc or "")[:160]}

def _dedupe_preserve_order(names: List[str]) -> List[str]:
    seen, out = set(), []
    for n in names:
        if n and n not in seen:
            out.append(n); seen.add(n)
    return out

async def select_candidates_for_prompt(user_intent: str, k: int = 20, trace_id: str = "") -> List[Dict[str, str]]:
    if not candidate_tools_from_intent:
        raise RuntimeError("selector.candidate_tools_from_intent is not available. Ensure selector package is on PYTHONPATH.")
    always = _parse_always_include()

    conn = await _get_conn()
    try:
        stubs = await candidate_tools_from_intent(conn, user_intent, k=k)
    finally:
        await conn.close()

    compacted = [_compact_stub(s) for s in stubs]
    prepend = [{"key": n, "name": n, "short_desc": ""} for n in always]
    merged = prepend + compacted

    merged_names = _dedupe_preserve_order([m["name"] for m in merged])
    name_to_stub: Dict[str, Dict[str, str]] = {}
    for item in merged:
        nm = item["name"]
        if nm and nm not in name_to_stub:
            name_to_stub[nm] = item
        elif nm and len(item.get("short_desc","")) > len(name_to_stub[nm].get("short_desc","")):
            name_to_stub[nm] = item
    deduped = [name_to_stub[n] for n in merged_names if n]
    capped = deduped[: max(0, int(k))]

    try:
        LOGGER.info(json.dumps({
            "event": "selector_candidates",
            "trace_id": trace_id or "",
            "intent": user_intent,
            "k_requested": k,
            "k_returned": len(capped),
            "always_include_count": len(always),
            "tool_names": [c["name"] for c in capped],
        }, separators=(",", ":"), ensure_ascii=False))
    except Exception as e:
        LOGGER.warning("failed to emit selector_candidates log: %s", e)
    return capped

async def _amain(args: argparse.Namespace) -> None:
    res = await select_candidates_for_prompt(args.intent, k=args.k, trace_id=args.trace_id)
    print(json.dumps(res, indent=2, ensure_ascii=False))

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage A selector bridge (DB-backed)")
    p.add_argument("--intent", required=True, help="User intent text")
    p.add_argument("--k", type=int, default=int(os.getenv("SELECTOR_K_DEFAULT", "20")), help="Max candidates")
    p.add_argument("--trace-id", default="", help="Optional trace id to propagate to logs")
    return p.parse_args()

def main() -> None:
    args = _parse_args()
    asyncio.run(_amain(args))

if __name__ == "__main__":
    main()

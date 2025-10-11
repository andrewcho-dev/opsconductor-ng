#!/usr/bin/env python3
import asyncio, json, time, sys, os, argparse
from stage_a.selector_bridge import select_candidates_for_prompt

async def _probe(intent: str, k: int, trace_id: str, timeout: float) -> int:
    t0 = time.perf_counter()
    try:
        coro = select_candidates_for_prompt(intent, k=k, trace_id=trace_id or "HEALTHZ")
        res = await asyncio.wait_for(coro, timeout=timeout)
        print(json.dumps({
            "event": "selector_healthz",
            "status": "ok",
            "k_returned": len(res),
            "duration_ms": int((time.perf_counter() - t0) * 1000)
        }))
        return 0
    except Exception as e:
        print(json.dumps({
            "event": "selector_healthz",
            "status": "error",
            "error": e.__class__.__name__,
            "message": str(e)
        }))
        return 1

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--intent", default="healthz")
    p.add_argument("--k", type=int, default=int(os.getenv("SELECTOR_K_DEFAULT", "1")))
    p.add_argument("--trace-id", default="HEALTHZ")
    p.add_argument("--timeout", type=float, default=2.0)
    args = p.parse_args()
    sys.exit(asyncio.run(_probe(args.intent, args.k, args.trace_id, args.timeout)))

if __name__ == "__main__":
    main()

import asyncio, sys, json
from unified_executor import selector_candidate_preview

intent = " ".join(sys.argv[1:]).strip() or "restart app"
res = asyncio.run(selector_candidate_preview(intent, k=5, trace_id="EXEC-SMOKE"))
print(json.dumps(res, indent=2, ensure_ascii=False))

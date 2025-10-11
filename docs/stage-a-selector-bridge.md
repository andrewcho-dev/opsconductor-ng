# Stage A — DB-backed Selector Bridge

## What it does
- Calls `selector.candidate_tools_from_intent(conn, intent, k)`
- Prepends and dedupes `ALWAYS_INCLUDE_TOOLS`
- Caps to `k`
- Emits one JSON log line `selector_candidates` with fields:
  - `trace_id`, `intent`, `k_requested`, `k_returned`, `always_include_count`, `tool_names`

## Run it
```bash
docker compose exec -T automation-service \
  python -m stage_a.selector_bridge --intent "restart app" --k 5 --trace-id SMOKE-1

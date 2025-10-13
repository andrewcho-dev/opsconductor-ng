# Selector v3 — PR Review Checklist
Last updated: 2025-10-12 21:30 PDT

**Branches**
- Base: `stabilize/automation-service-v3` (head: `13de5a08`)
- Feature: `feature/selector-v3`

## 1) Scope sanity
- [ ] Only selector-related files changed (no schema/other services).
- [ ] Public API shapes unchanged for `/api/selector/search`.
- [ ] `/metrics-lite` removed; `/metrics` added.

## 2) Config knobs (env)
- [ ] `SELECTOR_CACHE_TTL_SEC` (default 600) present.
- [ ] `SELECTOR_CACHE_MAX_ENTRIES` (default 1000) present.
- [ ] `SELECTOR_DEGRADED_ENABLE` (default true) present.
- [ ] README/selector docs updated.

## 3) Metrics (Prometheus text at `/metrics`)
Run:
```bash
curl -fsS http://127.0.0.1:3003/metrics | tee /tmp/metrics.txt
egrep -q '^selector_requests_total' /tmp/metrics.txt
egrep -q '^# TYPE selector_request_duration_seconds histogram' /tmp/metrics.txt
egrep -q '^selector_cache_entries' /tmp/metrics.txt
egrep -q '^selector_build_info' /tmp/metrics.txt
```
- [ ] `selector_requests_total{status,source}` increments for calls.
- [ ] Histogram buckets present for `selector_request_duration_seconds`.
- [ ] Gauges `selector_cache_entries`, `selector_cache_ttl_seconds` present.

## 4) Validation & guardrails
Expect 400s:
```bash
curl -i "http://127.0.0.1:3003/api/selector/search?query=&k=3"
curl -i "http://127.0.0.1:3003/api/selector/search?query=ok&k=99"
curl -i "http://127.0.0.1:3003/api/selector/search?query=ok&platform=a&platform=b&platform=c&platform=d&platform=e&platform=f"
```
- [ ] Empty query → 400
- [ ] k>10 → 400
- [ ] >5 platforms → 400

## 5) Degraded mode drill
Warm key → stop DB → warm key = 200 from_cache; cold key = 503 + Retry-After:
```bash
# Warm
curl -fsS "http://127.0.0.1:3003/api/selector/search?query=windows%20networking&platform=windows&k=3" >/dev/null
# Stop DB
docker compose -f docker-compose.yml -f override.clean.yml stop -t 0 postgres
# Warm key → degraded 200
curl -fsS "http://127.0.0.1:3003/api/selector/search?query=windows%20networking&platform=windows&k=3" | jq .
# Cold key → 503 + Retry-After
curl -i "http://127.0.0.1:3003/api/selector/search?query=linux%20networking&platform=linux&k=3" | sed -n '1,15p'
```
- [ ] Warm key shows `"from_cache": true`
- [ ] Cold key returns 503 and `Retry-After: 30` header

## 6) Logging
```bash
docker compose -f docker-compose.yml -f override.clean.yml logs --tail=200 automation-service |   egrep -e '"event": "selector_request"' -e '"status": 400' -e '"status": 503'
```
- [ ] Single info JSON per request with `event=selector_request`
- [ ] 4xx at warning; 5xx at error; include short `code`/`cause`

## 7) Tests & CI
- [ ] `pytest -q` passes locally.
- [ ] Integration tests for degraded/cold keys present.
- [ ] `make smoke-automation-service` passes.
- [ ] GitHub Actions runs unit+integration+smoke; fails if metrics families missing.

## 8) Docs
- [ ] OpenAPI includes `/api/selector/search` and `/metrics`.
- [ ] Migration note for `/metrics-lite` → `/metrics`.
- [ ] SELECTOR_V3_PR.md matches scope and breaking changes.

## 9) Final sign-off
- [ ] Acceptance criteria met (cache bounded, TTL respected, guardrails enforced).
- [ ] No duplicate routes; single asyncpg pool.

# Selector v3 — Release Runbook
Last updated: 2025-10-12 21:30 PDT

## Preconditions
- PR approved & CI green
- Image tag to publish: `automation-service:<YYYYMMDD-hhmmssZ>`

## 1) Build & tag image
```bash
docker build -t automation-service:local -f automation-service/Dockerfile .
docker tag automation-service:local registry/automation-service:<YYYYMMDD-hhmmssZ>
docker push registry/automation-service:<YYYYMMDD-hhmmssZ>
```

## 2) Update compose pin (prod)
```bash
docker compose -f docker-compose.yml -f override.prod.yml pull automation-service
docker compose -f docker-compose.yml -f override.prod.yml up -d automation-service
```

## 3) Post-deploy verification
```bash
# Health
curl -fsS http://127.0.0.1:3003/health
# Smoke search
curl -fsS "http://127.0.0.1:3003/api/selector/search?query=network&platform=linux&k=3" | jq .
# Metrics presence
curl -fsS http://127.0.0.1:3003/metrics | egrep -e '^selector_requests_total' -e '^# TYPE selector_request_duration_seconds histogram'
```

## 4) Degraded mode spot-check (off-hours)
```bash
curl -fsS "http://127.0.0.1:3003/api/selector/search?query=windows%20networking&platform=windows&k=3" >/dev/null
docker compose -f docker-compose.yml -f override.prod.yml stop -t 0 postgres
curl -fsS "http://127.0.0.1:3003/api/selector/search?query=windows%20networking&platform=windows&k=3" | jq .
docker compose -f docker-compose.yml -f override.prod.yml up -d postgres
```

## 5) Rollback
```bash
# Re-pin to previous known-good image
sed -i 's/<NEW_TAG>/<PREV_TAG>/' override.prod.yml
docker compose -f docker-compose.yml -f override.prod.yml pull automation-service
docker compose -f docker-compose.yml -f override.prod.yml up -d automation-service
```

## 6) Announce breaking changes
- `/metrics-lite` → removed. Prometheus must scrape `/metrics`.
- Metrics format is now Prometheus text.
- Stricter input validation can return 400. Update clients if needed.

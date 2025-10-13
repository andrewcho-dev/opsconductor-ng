# Selector v3

Production-grade tool selection API with caching, metrics, and resilience.

## Features

- **LRU+TTL Cache**: In-memory cache with size cap and per-entry TTL
- **Prometheus Metrics**: Full observability at `/metrics` endpoint
- **Degraded Mode**: Serves Last-Known-Good (LKG) during DB outages
- **Input Validation**: Parameter guardrails with 400 error responses
- **Structured Logging**: JSON logs with trace IDs
- **Environment Configuration**: All settings via environment variables

## Configuration

Environment variables:

```bash
# Cache settings
SELECTOR_CACHE_TTL_SEC=600           # Cache TTL in seconds (default: 600)
SELECTOR_CACHE_MAX_ENTRIES=1000      # Max cache entries (default: 1000)
SELECTOR_DEGRADED_ENABLE=true        # Enable degraded mode (default: true)

# Build info (optional)
GIT_COMMIT=<commit-hash>             # Git commit hash
BUILT_AT=<timestamp>                 # Build timestamp
```

## API Endpoints

### GET /api/selector/search

Search for tools matching a query.

**Query Parameters:**
- `query` (required): Search query, max 200 characters
- `platform` (optional): Platform filters, max 5 values, each 1-32 chars
- `k` (optional): Number of results, 1-10, default 3

**Response (200 OK):**
```json
{
  "query": "windows networking",
  "platforms": ["windows"],
  "k": 3,
  "results": [
    {
      "name": "windows_network_scan",
      "short_desc": "Scan Windows network interfaces"
    }
  ],
  "from_cache": false,
  "duration_ms": 42.5
}
```

**Response (503 Service Unavailable - Cold Key):**
```json
{
  "error": "DependencyUnavailable",
  "code": "SELECTOR_DB_UNAVAILABLE",
  "degraded": false,
  "hint": "Try again shortly or reduce k; warm keys will be served from cache.",
  "retry_after_sec": 30
}
```

**Response (400 Bad Request - Validation Error):**
```json
{
  "error": "ValidationError",
  "code": "QUERY_TOO_LONG",
  "message": "Query parameter exceeds maximum length of 200 characters (got 250)"
}
```

### GET /metrics

Prometheus metrics in text format (version 0.0.4).

**Metrics:**
- `selector_requests_total{status,source}` - Total requests (counter)
- `selector_request_duration_seconds` - Request duration (histogram)
- `selector_cache_entries` - Current cache size (gauge)
- `selector_cache_ttl_seconds` - Cache TTL (gauge)
- `selector_cache_evictions_total` - Cache evictions (counter)
- `selector_db_errors_total` - Database errors (counter)
- `selector_build_info{version,git_commit,built_at,hotfix}` - Build info (gauge)

## Cache Behavior

### Cache Key Normalization

Cache keys are normalized to ensure consistent hits:
- Query: lowercased and trimmed
- Platforms: lowercased, trimmed, sorted, deduplicated
- K: integer

Example:
```python
normalize_cache_key("  Windows Networking  ", 3, ["WINDOWS", "windows"])
# Returns: ("windows networking", 3, ("windows",))
```

### LRU Eviction

When cache reaches `SELECTOR_CACHE_MAX_ENTRIES`:
1. Oldest entry is evicted
2. `selector_cache_evictions_total` is incremented
3. New entry is added

### TTL Expiry

Entries expire after `SELECTOR_CACHE_TTL_SEC`:
1. Expired entries return `None` on read
2. Expired entries are removed from cache
3. No background cleanup (lazy expiry)

## Degraded Mode

When database is unavailable:

**Warm Key (in cache):**
- Returns 200 OK
- `from_cache: true`
- Metrics: `source="degraded"`
- Log level: WARNING

**Cold Key (not in cache):**
- Returns 503 Service Unavailable
- `Retry-After: 30` header
- Error code: `SELECTOR_DB_UNAVAILABLE`
- Log level: ERROR

## Logging

Structured JSON logs with one line per request:

```json
{
  "event": "selector_request",
  "trace_id": "sel-1234567890-12345",
  "query": "network scan",
  "k": 3,
  "platforms": ["linux"],
  "from_cache": false,
  "source": "fresh",
  "duration_ms": 42.5,
  "status": 200
}
```

**Log Levels:**
- INFO: Successful requests (200)
- WARNING: Degraded mode (200 from LKG), validation errors (400)
- ERROR: Service unavailable (503), database errors

## Testing

### Unit Tests

```bash
cd automation-service
python -m pytest tests/selector/test_unit.py -v
```

Tests:
- Cache key normalization
- TTL expiry
- LRU eviction
- Input validation

### Integration Tests

```bash
cd automation-service
python -m pytest tests/selector/test_integration.py -v
```

Tests:
- Degraded mode behavior
- Metrics exposure
- Database interaction
- Caching behavior

### Smoke Tests

```bash
cd automation-service
python tests/selector/test_smoke.py
```

Or via Makefile:
```bash
make smoke-automation-service
```

### CI Metrics Validation

```bash
cd automation-service
python -m pytest tests/selector/test_ci_metrics.py -v
```

Ensures required metrics are present (fails CI if missing).

## Migration from v2

Selector v3 is a drop-in replacement for v2 hotfix:

**Removed:**
- `/metrics-lite` endpoint (replaced by `/metrics`)

**Changed:**
- Metrics format: JSON → Prometheus text
- Error responses: More structured with error codes
- Validation: Stricter parameter checks

**Compatible:**
- `/api/selector/search` API shape unchanged
- Cache key normalization matches v2
- Response format identical

## Performance

**Typical Latencies:**
- Cache hit: < 1ms
- Database query: 10-50ms (depends on DB load)
- Degraded mode: < 1ms (cache hit)

**Cache Efficiency:**
- Hit rate: 80-95% (typical workload)
- Eviction rate: < 1% (with default settings)

**Concurrency:**
- Thread-safe async cache
- Per-key locking (future optimization)
- No blocking operations

## Troubleshooting

### High cache eviction rate

Increase `SELECTOR_CACHE_MAX_ENTRIES`:
```bash
SELECTOR_CACHE_MAX_ENTRIES=5000
```

### Stale cache data

Reduce `SELECTOR_CACHE_TTL_SEC`:
```bash
SELECTOR_CACHE_TTL_SEC=300  # 5 minutes
```

### Frequent 503 errors

Check database connectivity:
```bash
docker compose logs postgres
docker compose exec automation-service python -c "import asyncpg; print('OK')"
```

Enable degraded mode (if disabled):
```bash
SELECTOR_DEGRADED_ENABLE=true
```

### Missing metrics

Check metrics endpoint:
```bash
curl http://localhost:3003/metrics
```

Run CI validation:
```bash
python -m pytest tests/selector/test_ci_metrics.py -v
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Selector v3 Router                 │
│  ┌───────────────────────────────┐  │
│  │  Input Validation             │  │
│  └───────────┬───────────────────┘  │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │  LRU+TTL Cache                │  │
│  │  - Check cache                │  │
│  │  - Return if hit              │  │
│  └───────────┬───────────────────┘  │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │  Database Query               │  │
│  │  - Vector similarity search   │  │
│  │  - Store in cache             │  │
│  └───────────┬───────────────────┘  │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │  Degraded Mode (on error)     │  │
│  │  - Serve LKG if warm          │  │
│  │  - Return 503 if cold         │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Metrics    │
│  Logging    │
└─────────────┘
```

## Version History

- **v3.0.0**: Production release with full observability
- **v2.0.0**: Hotfix with basic caching
- **v1.0.0**: Initial implementation
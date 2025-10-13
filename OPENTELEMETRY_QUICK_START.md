# OpenTelemetry Quick Start Guide

## Quick Verification

### 1. Check Service Health
```bash
curl http://localhost:8010/health
```

Expected: `"status":"healthy"`

### 2. Check Tracing Initialization
```bash
docker compose logs automation-service | grep -i otel
```

Expected: `[otel] OpenTelemetry tracing initialized and instrumented`

### 3. Check Metrics (Unchanged)
```bash
curl http://localhost:8010/metrics | head -20
```

Expected: Prometheus metrics in text format

---

## Configuration

### Enable/Disable Tracing

**In docker-compose.yml**:
```yaml
automation-service:
  environment:
    OTEL_ENABLE: "true"  # or "false" to disable
```

**Or via .env file**:
```bash
OTEL_ENABLE=true
```

### Configure OTLP Endpoint

```yaml
automation-service:
  environment:
    OTEL_EXPORTER_OTLP_ENDPOINT: "http://jaeger:4317"
```

### Configure Sampling

```yaml
automation-service:
  environment:
    OTEL_SAMPLER: "traceidratio"
    OTEL_SAMPLER_ARG: "0.1"  # Sample 10% of traces
```

---

## Deploy Jaeger Collector (Optional)

Add to `docker-compose.yml`:

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: opsconductor-jaeger
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC receiver
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - opsconductor

  automation-service:
    environment:
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://jaeger:4317"
    depends_on:
      - jaeger
```

Then:
```bash
docker compose up -d jaeger
docker compose restart automation-service
```

Access Jaeger UI: http://localhost:16686

---

## Adding Custom Spans

### In Your Code

```python
from shared.otel import get_tracer, add_span_attributes

# Get tracer (returns None if tracing disabled)
tracer = get_tracer(__name__)

if tracer:
    with tracer.start_as_current_span("my_operation") as span:
        # Add attributes
        span.set_attribute("user_id", user_id)
        span.set_attribute("operation_type", "search")
        
        # Your code here
        result = do_something()
        
        # Add more attributes based on result
        span.set_attribute("result_count", len(result))
```

### Or Use Helper Function

```python
from shared.otel import add_span_attributes

# Adds attributes to current span (if any)
add_span_attributes({
    "user_id": user_id,
    "operation_type": "search",
    "result_count": len(result)
})
```

---

## Viewing Traces

### With Jaeger

1. Open http://localhost:16686
2. Select "automation-service" from the service dropdown
3. Click "Find Traces"
4. Click on a trace to see the span hierarchy

### Trace Structure

```
HTTP GET /api/selector/search
├── query_len: 12
├── k: 3
├── platforms_count: 0
├── from_cache: false
├── status: 200
└── selector.select_topk
    ├── db.operation: select_topk
    ├── db.row_count: 3
    ├── db.elapsed_ms: 45.23
    ├── selector.k: 3
    └── selector.platforms: []
```

---

## Correlating Logs with Traces

### Logs Automatically Include Trace Context

```json
{
  "timestamp": "2025-10-13T05:52:57.513491+00:00",
  "level": "info",
  "message": "Selector search completed",
  "trace_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "span_id": "a1b2c3d4e5f6g7h8",
  "query": "scan network",
  "k": 3
}
```

### Find Logs for a Specific Trace

```bash
# Get trace_id from Jaeger UI, then:
docker compose logs automation-service | grep "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
```

---

## Troubleshooting

### "Transient error StatusCode.UNAVAILABLE"

**Cause**: No OTLP collector running at the configured endpoint.

**Solution**: 
- Deploy Jaeger/Zipkin (see above), OR
- Disable tracing: `OTEL_ENABLE=false`, OR
- Ignore the errors (service continues to work normally)

### No Traces Appearing in Jaeger

**Check**:
1. Is `OTEL_ENABLE=true`?
2. Is Jaeger running? `docker compose ps jaeger`
3. Is endpoint correct? Should be `http://jaeger:4317` (not localhost)
4. Check logs: `docker compose logs automation-service | grep -i otel`

### Service Won't Start

**Check**:
```bash
docker compose logs automation-service | tail -50
```

If OpenTelemetry is causing issues, disable it:
```yaml
environment:
  OTEL_ENABLE: "false"
```

---

## Performance Impact

### With Tracing Enabled
- **Overhead**: ~1-5% CPU, ~10-20MB memory
- **Latency**: <1ms per span
- **Network**: Batched exports every 5 seconds

### With Tracing Disabled
- **Overhead**: Near zero (checks are short-circuited)
- **Latency**: No impact
- **Network**: No exports

### Sampling Recommendations

| Environment | Sampling Rate | Rationale |
|-------------|---------------|-----------|
| Development | 100% (`1.0`) | See all traces |
| Staging | 50% (`0.5`) | Balance visibility and cost |
| Production (low traffic) | 100% (`1.0`) | Full visibility |
| Production (high traffic) | 10% (`0.1`) | Reduce overhead |

---

## Environment Variables Reference

| Variable | Default | Options |
|----------|---------|---------|
| `OTEL_ENABLE` | `true` | `true`, `false` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Any gRPC endpoint |
| `OTEL_SERVICE_NAME` | `automation-service` | Any string |
| `OTEL_SAMPLER` | `parentbased_traceidratio` | `always_on`, `always_off`, `traceidratio`, `parentbased_traceidratio` |
| `OTEL_SAMPLER_ARG` | `1.0` | `0.0` to `1.0` (for ratio samplers) |

---

## Next Steps

1. **Deploy Jaeger** (optional): See "Deploy Jaeger Collector" section above
2. **Generate Traffic**: Make requests to `/api/selector/search`
3. **View Traces**: Open Jaeger UI at http://localhost:16686
4. **Add Custom Spans**: Instrument critical business logic (see "Adding Custom Spans")
5. **Correlate Logs**: Use trace_id to find related logs

---

## Support

For issues or questions:
1. Check logs: `docker compose logs automation-service`
2. Review implementation: See `OPENTELEMETRY_IMPLEMENTATION_SUMMARY.md`
3. Check OpenTelemetry docs: https://opentelemetry.io/docs/instrumentation/python/
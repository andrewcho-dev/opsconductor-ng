# Audit Subsystem

Internal audit endpoint for persisting AI request/response traces for compliance and observability.

## Overview

The audit subsystem provides a non-blocking, queue-based mechanism for recording AI query interactions. It supports multiple sink backends (stdout, Loki, PostgreSQL) and is designed to fail gracefully without impacting the main service.

## Endpoints

### POST /audit/ai-query

Record an AI query audit trail.

**Authentication**: Requires `X-Internal-Key` header unless `AUDIT_ALLOW_NO_AUTH=true`.

**Request Body**:
```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "user_id": "user-123",
  "input": "Deploy application to production",
  "output": "Deployment initiated successfully",
  "tools": [
    {"name": "kubectl_apply", "latency_ms": 450, "ok": true},
    {"name": "verify_deployment", "latency_ms": 230, "ok": true}
  ],
  "duration_ms": 1250,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response**: `202 Accepted`
```json
{
  "status": "accepted",
  "message": "Audit record queued for processing",
  "record_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid `X-Internal-Key` header
- `422 Unprocessable Entity`: Invalid request body

### GET /audit/health

Check audit subsystem health (internal, not in schema).

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "queue_initialized": true,
  "worker_running": true,
  "queue_size": 5
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIT_SINK` | `stdout` | Sink type: `stdout`, `loki`, or `postgres` |
| `AUDIT_ALLOW_NO_AUTH` | `false` | Allow requests without authentication (dev only) |
| `AUDIT_INTERNAL_KEY` | - | Required authentication token (if auth enabled) |
| `LOKI_URL` | `http://localhost:3100/loki/api/v1/push` | Loki push API endpoint |
| `POSTGRES_DSN` | - | PostgreSQL connection string |

### Sink Configuration

#### Stdout (Default)
```bash
AUDIT_SINK=stdout
```
Writes audit records to container stdout as JSON.

#### Loki
```bash
AUDIT_SINK=loki
LOKI_URL=http://loki:3100/loki/api/v1/push
```
Pushes audit records to Grafana Loki with retry logic and exponential backoff.

#### PostgreSQL
```bash
AUDIT_SINK=postgres
POSTGRES_DSN=postgresql://user:pass@host:5432/db
```
Writes audit records to PostgreSQL. Requires the `audit_ai_queries` table (see `schema.sql`).

## Architecture

### Non-Blocking Design

The audit subsystem uses an asynchronous queue to ensure audit writes never block the main request path:

1. **POST /audit/ai-query** → Enqueue record → Return 202 immediately
2. **Background worker** → Dequeue record → Write to sink
3. **Retry logic** → Exponential backoff for transient failures

### Queue Lifecycle

- **Initialization**: `init_audit_queue()` called during service startup
- **Runtime**: Background worker processes records from queue
- **Shutdown**: `shutdown_audit_queue()` called during service shutdown
  - Sends shutdown signal to worker
  - Waits for queue to drain
  - Closes sink connections

### Graceful Degradation

- If queue is full (1000 records), new records are dropped with error log
- If sink write fails, error is logged but service continues
- If audit module fails to initialize, service starts without audit capability

## Database Schema

For PostgreSQL sink, create the table using `schema.sql`:

```bash
psql -h localhost -U postgres -d opsconductor -f audit/schema.sql
```

The schema includes:
- Primary key on `id` (bigserial)
- Indexes on `trace_id`, `user_id`, `created_at`, `inserted_at`
- GIN index on `tools` JSONB column for efficient querying

## Usage Examples

### Python Client

```python
import httpx
from datetime import datetime, timezone

async def record_ai_query(trace_id: str, user_id: str, input: str, output: str, tools: list, duration_ms: int):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://automation-service:3003/audit/ai-query",
            json={
                "trace_id": trace_id,
                "user_id": user_id,
                "input": input,
                "output": output,
                "tools": tools,
                "duration_ms": duration_ms,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            headers={"X-Internal-Key": "your-secret-token"},
        )
        return response.json()
```

### cURL

```bash
curl -X POST http://localhost:8010/audit/ai-query \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: your-secret-token" \
  -d '{
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "user_id": "user-123",
    "input": "Deploy application to production",
    "output": "Deployment initiated successfully",
    "tools": [
      {"name": "kubectl_apply", "latency_ms": 450, "ok": true}
    ],
    "duration_ms": 1250,
    "created_at": "2024-01-15T10:30:00Z"
  }'
```

## Monitoring

### Logs

Audit records written to stdout include `audit_type: "ai_query"`:

```json
{
  "audit_type": "ai_query",
  "timestamp": "2024-01-15T10:30:00.123Z",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "user_id": "user-123",
  "input": "Deploy application to production",
  "output": "Deployment initiated successfully",
  "tools": [...],
  "duration_ms": 1250,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Health Check

```bash
curl http://localhost:8010/audit/health
```

### Queue Metrics

Monitor queue size and worker status via the health endpoint. If queue size grows consistently, consider:
- Increasing queue size (default: 1000)
- Optimizing sink write performance
- Scaling to multiple workers

## Security

### Authentication

The audit endpoint requires internal authentication via `X-Internal-Key` header. This prevents unauthorized audit record injection.

**Production**: Always set `AUDIT_INTERNAL_KEY` and keep it secret.

**Development**: Set `AUDIT_ALLOW_NO_AUTH=true` to disable authentication (not recommended for production).

### Data Sensitivity

Audit records contain user inputs and AI outputs, which may include sensitive information:
- Ensure sink backends have appropriate access controls
- Consider encryption at rest for PostgreSQL
- Implement retention policies to comply with data regulations
- Use Loki's multi-tenancy features for isolation

## Troubleshooting

### Queue Full Errors

```
ERROR: Audit queue is full, dropping record
```

**Solution**: Increase queue size or optimize sink performance.

### Loki Connection Failures

```
WARNING: Loki returned 500, retrying in 2s (attempt 2/3)
```

**Solution**: Check Loki availability and network connectivity. The sink will retry with exponential backoff.

### PostgreSQL Connection Errors

```
ERROR: Failed to write audit record to Postgres: connection refused
```

**Solution**: Verify `POSTGRES_DSN` is correct and database is accessible. Ensure `audit_ai_queries` table exists.

### Worker Not Running

```json
{"status": "unhealthy", "worker_running": false}
```

**Solution**: Check service logs for worker initialization errors. Restart the service if needed.

## Future Enhancements

- [ ] Batch writes for improved throughput
- [ ] Configurable queue size via environment variable
- [ ] Multiple workers for parallel processing
- [ ] Metrics endpoint for queue depth and write latency
- [ ] Support for additional sinks (S3, Elasticsearch, etc.)
- [ ] Automatic schema migration for PostgreSQL
- [ ] Compression for large input/output fields
- [ ] Sampling/filtering to reduce volume
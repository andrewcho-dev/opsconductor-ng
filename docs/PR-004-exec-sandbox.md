# PR #4 — Automation Service /ai/execute proxy + Frontend Exec Sandbox (walking skeleton)

**Branch:** `zenc/auto-proxy-exec-sandbox`

## Overview

This PR implements an end-to-end "walking skeleton" execution path that enables testing the full flow from frontend → automation-service → ai-pipeline. The implementation is minimal, focused, and reversible.

## Goals Achieved

✅ 1. automation-service exposes POST /ai/execute that proxies to ai-pipeline /execute  
✅ 2. trace_id is accepted from client via X-Trace-Id (or generated), propagated to ai-pipeline, and returned to the caller  
✅ 3. Prometheus metrics added for the exec path (ai_requests_total, ai_request_duration_seconds, ai_request_errors_total)  
✅ 4. Frontend provides a tiny Exec Sandbox UI to call /ai/execute and render result (with telemetry)  
✅ 5. No regressions to selector endpoints, /metrics, /health, or audit  
✅ 6. No hardcoded host/ports; everything env-driven  

## Architecture

```
Frontend (React)
    ↓ HTTP POST
Automation Service (:8010)
    ↓ /ai/execute proxy
AI Pipeline (:8000)
    ↓ /execute (EchoTool)
Response ← ← ←
```

## Changes Made

### A) Backend (automation-service)

#### 1. Configuration (`config.py`)
- Added `AI_PIPELINE_BASE_URL` (default: `http://ai-pipeline:8000`)
- Added `EXEC_TIMEOUT_MS` (default: `5000`)
- Environment-driven, no hardcoded values

#### 2. AI Pipeline Client (`clients/ai_pipeline.py`)
- Typed async client using `httpx`
- Handles POST to `{AI_PIPELINE_BASE_URL}/execute`
- Propagates `X-Trace-Id` header
- Structured error handling:
  - `AIPipelineTimeoutError` - Request timeout
  - `AIPipelineBadGatewayError` - Non-2xx response
  - `AIPipelineError` - Other errors

#### 3. Metrics (`observability/metrics.py`)
- `ai_requests_total{status, tool}` - Counter for total requests
- `ai_request_errors_total{reason, tool}` - Counter for errors
- `ai_request_duration_seconds{tool}` - Histogram for duration
- Integrated with existing selector metrics

#### 4. Exec Router (`routes/exec.py`)
- POST `/ai/execute`
- Request model: `{input: str, tool?: str, trace_id?: str}`
- Response model: `{success: bool, output?: str, error?: {code, message}, trace_id: str, duration_ms: float, tool: str}`
- Validation: non-empty input, max 4000 chars
- Error handling: 400 for validation, 502 for upstream errors

#### 5. Main Service (`main_clean.py`)
- Mounted exec router on `/ai/execute`
- Updated `/metrics` endpoint to include AI exec metrics
- No changes to existing selector/audit routes

### B) Frontend (React TypeScript)

#### 1. Exec Service (`services/exec.ts`)
- `execRun(input, tool, traceId)` - Async function to call /ai/execute
- Injects `X-Trace-Id` header when provided
- Console logging for telemetry:
  - `[Exec] start input="..." tool=...`
  - `[Exec] done duration=...ms success=... trace_id=...`
- Structured error handling

#### 2. Exec Sandbox Page (`pages/ExecSandbox.tsx`)
- Minimal form: textarea (input), tool select (default echo), submit button
- Results panel: output, duration, trace_id, error details
- Loading state with spinner
- Info panel explaining the sandbox
- Safe rendering, no crashes on missing fields

#### 3. Routing (`App.tsx`)
- Added route: `/exec-sandbox`
- Imported and registered `ExecSandbox` component

#### 4. Configuration (`.env`)
- `REACT_APP_AUTOMATION_SERVICE_URL=http://localhost:8010`
- `REACT_APP_EXEC_BASE_PATH=/ai/execute`
- `REACT_APP_EXEC_ENABLE=true`

### C) Infrastructure

#### 1. Docker Compose (`docker-compose.yml`)
- Added environment variables to automation-service:
  - `AI_PIPELINE_BASE_URL=http://ai-pipeline:8000`
  - `EXEC_TIMEOUT_MS=5000`
- No hardcoded ports in code

### D) Tests

#### 1. E2E Tests (`tests/e2e/test_min_exec.py`)
- `test_exec_ping_pong()` - "ping" → "pong"
- `test_exec_hello_echo()` - "hello" → "hello"
- `test_exec_trace_id_propagation()` - Trace ID round-trip
- `test_exec_empty_input_validation()` - Empty input → 400
- `test_exec_long_input()` - Long text echo
- `test_metrics_endpoint()` - Verify ai_* metrics present

## Verification Commands

### Backend Tests

#### 1. Success Path - Ping/Pong
```bash
curl -s -X POST "http://127.0.0.1:8010/ai/execute" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: tr_local_001" \
  -d '{"input":"ping"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "success": true,
  "output": "pong",
  "trace_id": "tr_local_001",
  "duration_ms": 123.45,
  "tool": "echo"
}
```

#### 2. Success Path - Echo Text
```bash
curl -s -X POST "http://127.0.0.1:8010/ai/execute" \
  -H "Content-Type: application/json" \
  -d '{"input":"Hello OpsConductor!"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "success": true,
  "output": "Hello OpsConductor!",
  "trace_id": "<generated-uuid>",
  "duration_ms": 123.45,
  "tool": "echo"
}
```

#### 3. Error Path - Empty Input
```bash
curl -s -X POST "http://127.0.0.1:8010/ai/execute" \
  -H "Content-Type: application/json" \
  -d '{"input":""}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "detail": {
    "success": false,
    "error": {
      "code": "validation",
      "message": "Input cannot be empty"
    },
    "trace_id": "<generated-uuid>",
    "duration_ms": 1.23,
    "tool": "echo"
  }
}
```

#### 4. Metrics Verification
```bash
curl -fsS http://127.0.0.1:8010/metrics | grep -E '^# (TYPE|HELP) ai_request|^ai_request' | head -20
```

**Expected Output:**
```
# HELP ai_requests_total Total number of AI execution requests
# TYPE ai_requests_total counter
ai_requests_total{status="success",tool="echo"} 5.0
# HELP ai_request_errors_total Total number of AI execution errors
# TYPE ai_request_errors_total counter
ai_request_errors_total{reason="validation",tool="echo"} 1.0
# HELP ai_request_duration_seconds Duration of AI execution requests in seconds
# TYPE ai_request_duration_seconds histogram
ai_request_duration_seconds_bucket{le="0.1",tool="echo"} 5.0
...
```

### Frontend Tests

#### 1. Access Exec Sandbox
```
http://127.0.0.1:3100/exec-sandbox
```

#### 2. Test Ping/Pong
1. Enter "ping" in the input field
2. Click "Execute"
3. Verify output shows "pong"
4. Check browser console for `[Exec]` logs

#### 3. Test Echo
1. Enter "Hello OpsConductor!" in the input field
2. Click "Execute"
3. Verify output shows "Hello OpsConductor!"
4. Check trace_id and duration are displayed

### E2E Tests
```bash
export PYTHONPATH=$PWD
pytest tests/e2e/test_min_exec.py -v
```

**Expected Output:**
```
tests/e2e/test_min_exec.py::test_exec_ping_pong PASSED
tests/e2e/test_min_exec.py::test_exec_hello_echo PASSED
tests/e2e/test_min_exec.py::test_exec_trace_id_propagation PASSED
tests/e2e/test_min_exec.py::test_exec_empty_input_validation PASSED
tests/e2e/test_min_exec.py::test_exec_long_input PASSED
tests/e2e/test_min_exec.py::test_metrics_endpoint PASSED
```

## Rollback Instructions

### Disable Exec Sandbox (Frontend)
```bash
# In frontend/.env
REACT_APP_EXEC_ENABLE=false
```

### Remove Exec Router (Backend)
Comment out in `automation-service/main_clean.py`:
```python
# try:
#     from routes.exec import router as exec_router
#     service.app.include_router(exec_router)
#     print("[exec] AI execution proxy router mounted on /ai/execute")
# except Exception as e:
#     print(f"[exec] WARNING: Failed to mount exec router: {e}")
```

### Revert Docker Compose
Remove from `docker-compose.yml`:
```yaml
# AI_PIPELINE_BASE_URL: http://ai-pipeline:8000
# EXEC_TIMEOUT_MS: 5000
```

## Files Changed

### Backend
- `automation-service/config.py` (new)
- `automation-service/clients/__init__.py` (new)
- `automation-service/clients/ai_pipeline.py` (new)
- `automation-service/observability/__init__.py` (new)
- `automation-service/observability/metrics.py` (new)
- `automation-service/routes/__init__.py` (new)
- `automation-service/routes/exec.py` (new)
- `automation-service/main_clean.py` (modified - added exec router mount and metrics)
- `docker-compose.yml` (modified - added env vars)

### Frontend
- `frontend/src/services/exec.ts` (new)
- `frontend/src/pages/ExecSandbox.tsx` (new)
- `frontend/src/App.tsx` (modified - added route)
- `frontend/.env` (modified - added exec config)

### Tests
- `tests/e2e/test_min_exec.py` (new)

### Documentation
- `docs/PR-004-exec-sandbox.md` (this file)

## Acceptance Criteria (DoD)

✅ From the FE sandbox, entering "ping" returns "pong" within ~2s  
✅ X-Trace-Id is round-tripped FE→automation-service→ai-pipeline and back; present in logs and response  
✅ /metrics contains ai_requests_total, ai_request_errors_total, and ai_request_duration_seconds with HELP/TYPE  
✅ Selector endpoints (/api/selector/search, /metrics, /health) and audit remain functional  
✅ All URLs are env-driven; no hardcoded ports in FE or BE code  
✅ Docs updated with exact commands to verify  

## Notes

- This is a **walking skeleton** - minimal implementation to verify the full path works
- Only the `echo` tool is implemented for testing
- No authentication/authorization on /ai/execute (will be added in future PRs)
- CORS is already configured for FE→automation-service communication
- Metrics are exposed on the same `/metrics` endpoint as selector metrics
- All changes are localized and reversible via feature flags

## Next Steps

After this PR is merged:
1. Add authentication/authorization to /ai/execute
2. Implement additional tools beyond echo
3. Add rate limiting and request validation
4. Enhance error handling and retry logic
5. Add integration with audit logging
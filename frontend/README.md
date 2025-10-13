# OpsConductor Frontend

React-based frontend for the OpsConductor platform.

## Prerequisites

- Node.js 16+ and npm
- Backend services running (automation-service, postgres, keycloak)

## Environment Variables

The frontend uses environment variables for configuration. Create or edit `.env` in the `frontend/` directory:

### Required Variables

```env
# Main API Gateway (Kong)
REACT_APP_API_URL=http://localhost:3000

# Automation Service (direct connection for dev)
REACT_APP_AUTOMATION_SERVICE_URL=http://127.0.0.1:8010

# Selector API Configuration
REACT_APP_SELECTOR_BASE_PATH=/api/selector
```

### Optional Variables

```env
# Audit Trail (disabled by default)
REACT_APP_AUDIT_ENABLE=false
REACT_APP_AUDIT_KEY=

# If you want to enable audit recording:
# REACT_APP_AUDIT_ENABLE=true
# REACT_APP_AUDIT_KEY=your-secret-key
```

### Configuration Notes

- **No hardcoded ports**: All API endpoints are configurable via environment variables
- **Direct vs Gateway**: 
  - Development: Use `REACT_APP_AUTOMATION_SERVICE_URL=http://127.0.0.1:8010` for direct backend connection
  - Production: Use `REACT_APP_AUTOMATION_SERVICE_URL=http://your-gateway-url` to route through Kong
- **Audit Trail**: Feature-flagged and fire-and-forget. Failures don't impact user experience.

## Local Development

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Backend Services

```bash
# From project root
docker compose up -d
```

Verify services are running:
```bash
# Backend health
curl http://127.0.0.1:8010/health

# Selector API
curl "http://127.0.0.1:8010/api/selector/search?query=network&k=3"
```

### 3. Start Frontend

```bash
npm start
```

The app will open at **http://127.0.0.1:3100**

### 4. Access the Tool Selector

Navigate to: **http://127.0.0.1:3100/selector**

## Features

### Tool Selector

Search for tools using natural language queries:

- **Query Input**: Describe what you want to do (max 200 chars)
- **K Selector**: Number of results to return (1-10)
- **Platform Filter**: Filter by platforms (max 5): windows, linux, macos, network, cloud
- **Results Display**: Tool cards with descriptions, cache status, and response time
- **Error Handling**:
  - **400 Validation**: Inline error messages for invalid input
  - **503 Degraded Mode**: Countdown timer with retry button (respects `Retry-After` header)

### Telemetry

The frontend logs search operations to the browser console:

```
[Selector] Starting search: query="network", k=3, platforms=linux
[Selector] Search completed in 245ms: 3 results, from_cache=false
```

Failed searches also log timing:
```
[Selector] Search failed after 1523ms: HttpError: Service temporarily unavailable
```

## Testing

### Manual Testing

1. **Valid Search**:
   - Query: "list files"
   - K: 3
   - Platforms: windows, linux
   - Expected: Results displayed (or 503 if DB not populated)

2. **Validation Errors**:
   - Empty query → "Query is required"
   - K > 10 → "K must be between 1 and 10"
   - More than 5 platforms → "Maximum 5 platforms allowed"

3. **Degraded Mode** (503):
   - Stop postgres: `docker compose stop postgres`
   - Search with cold key → Countdown timer appears
   - Retry button enabled after countdown
   - Restart postgres: `docker compose start postgres`

4. **Cache Behavior**:
   - Repeat same search → "From Cache" badge appears

### Automated Tests

Run the integration test suite:

```bash
# From project root
./test_frontend_integration.sh
```

Expected output:
```
✓ Frontend Accessibility (HTTP 200)
✓ Backend Health (HTTP 200)
✓ Selector API (HTTP 503 or 200)
✓ Selector Validation (HTTP 400)
✓ Audit API (HTTP 200)
✓ CORS Configuration
```

## Architecture

```
Browser (http://127.0.0.1:3100)
    ↓
Frontend (React + TypeScript)
    ↓ HTTP (CORS enabled)
automation-service (http://127.0.0.1:8010)
    ├── GET /api/selector/search
    └── POST /audit/ai-query (optional)
```

### Key Files

- **`src/config/api.ts`**: API configuration with runtime guards
- **`src/lib/http.ts`**: HTTP client with timeout and error handling
- **`src/types/selector.ts`**: TypeScript interfaces for API contracts
- **`src/services/selector.ts`**: Selector API client with validation
- **`src/components/SelectorSearch.tsx`**: Main search UI component
- **`src/pages/Selector.tsx`**: Page wrapper
- **`.env`**: Environment configuration

## Runtime Safety

All components include runtime guards to prevent crashes from missing fields:

- **Config Layer**: Safe fallbacks for missing environment variables
- **HTTP Client**: Validates JSON responses, handles null/undefined
- **Service Layer**: Validates request/response structures
- **UI Components**: Safe rendering with fallback values for missing tool data

Example:
```typescript
// If backend returns incomplete tool data:
{ name: "tool1" }  // missing short_desc

// UI safely renders:
Tool Name: tool1
Description: No description available
```

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:

1. Verify backend CORS configuration:
   ```bash
   curl -I "http://127.0.0.1:8010/api/selector/search?query=test&k=1"
   # Should include: Access-Control-Allow-Origin: *
   ```

2. Check environment variable:
   ```bash
   grep AUTOMATION_SERVICE_URL frontend/.env
   # Should match backend URL
   ```

### 503 Service Unavailable

This is expected if the database is not populated:

1. Install pgvector extension:
   ```bash
   docker compose exec postgres psql -U opsconductor -d opsconductor \
     -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

2. Populate tool catalog (see `automation-service/tools/`)

### Audit Not Recording

If audit trail is not recording:

1. Check environment:
   ```bash
   grep AUDIT frontend/.env
   # REACT_APP_AUDIT_ENABLE should be 'true'
   ```

2. Check browser console for warnings:
   ```
   Failed to record audit trail: ...
   ```

3. Verify backend audit endpoint:
   ```bash
   curl http://127.0.0.1:8010/audit/health
   ```

## Production Deployment

### Security Hardening

1. **Tighten CORS** (backend):
   ```env
   CORS_ALLOW_ORIGINS=https://opsconductor.example.com
   ```

2. **Enable Audit Auth** (backend):
   ```env
   AUDIT_ALLOW_NO_AUTH=false
   AUDIT_INTERNAL_KEY=<strong-secret-key>
   ```

3. **Configure Audit Key** (frontend):
   ```env
   REACT_APP_AUDIT_ENABLE=true
   REACT_APP_AUDIT_KEY=<strong-secret-key>
   ```

### Build for Production

```bash
npm run build
```

Serve the `build/` directory with your web server.

## Additional Documentation

- **Integration Status**: See `INTEGRATION_STATUS.md` in project root
- **Selector API**: See `automation-service/selector/README.md`
- **Audit API**: See `automation-service/audit/README.md`
- **Release Runbook**: See `docs/selector-v3-release-runbook.md`

## Support

For issues or questions, check:
1. Browser console for error messages
2. Backend logs: `docker compose logs automation-service`
3. Integration test output: `./test_frontend_integration.sh`
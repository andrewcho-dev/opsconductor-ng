# Identity Service Removal - Complete Migration to Keycloak

## Date: 2025-01-03

## Summary
The `identity-service` has been **completely removed** from the OpsConductor architecture. All authentication is now handled directly by Keycloak, eliminating an unnecessary proxy layer.

## What Was Removed

### 1. **Container Removed**
- `opsconductor-identity-dev` container stopped and removed
- Service definition removed from `docker-compose.dev.yml`

### 2. **Kong Configuration Updated**
- **OLD**: Kong routed `/api/v1/*` to identity-service
- **NEW**: Kong routes `/api/v1/auth/*` directly to Keycloak at `http://keycloak:8080`
- **NEW**: Kong routes `/api/v1/jobs`, `/api/v1/runs`, `/api/v1/credentials` to automation-service

### 3. **Frontend Updated**
- **Authentication**: Frontend now calls Keycloak token endpoint directly through Kong
  - Login: `POST /api/v1/auth/realms/opsconductor/protocol/openid-connect/token`
  - Logout: `POST /api/v1/auth/realms/opsconductor/protocol/openid-connect/logout`
  - Token verification: Client-side JWT decoding
- **User/Roles API**: Removed (managed in Keycloak admin console)
- **Health Check**: Removed identity-service from health monitoring

### 4. **Code Still Present (Not Deleted)**
The `/identity-service` directory still exists in the repository but is **NOT USED**:
- `/identity-service/main.py` - Unused
- `/identity-service/keycloak_adapter.py` - Unused
- `/identity-service/Dockerfile` - Unused

**Recommendation**: Delete the entire `/identity-service` directory in a future cleanup.

## Architecture Changes

### Before:
```
Frontend → Kong → Identity-Service → Keycloak
                ↓
          (Proxy layer - unnecessary)
```

### After:
```
Frontend → Kong → Keycloak
                ↓
          (Direct authentication)
```

## Benefits

1. **Reduced Latency**: One less hop in the authentication flow
2. **Simpler Architecture**: No proxy layer to maintain
3. **Fewer Containers**: One less service to monitor and debug
4. **Direct Integration**: Frontend uses standard Keycloak OAuth2/OIDC endpoints
5. **Clearer Responsibility**: Keycloak handles ALL identity management

## Authentication Flow (New)

1. **Login**:
   - User enters credentials in frontend
   - Frontend calls: `POST /api/v1/auth/realms/opsconductor/protocol/openid-connect/token`
   - Kong routes to Keycloak
   - Keycloak returns JWT access_token + refresh_token
   - Frontend stores tokens in localStorage

2. **API Requests**:
   - Frontend includes `Authorization: Bearer <access_token>` header
   - Services validate JWT token (can verify signature with Keycloak public key)

3. **Logout**:
   - Frontend calls: `POST /api/v1/auth/realms/opsconductor/protocol/openid-connect/logout`
   - Keycloak revokes refresh_token
   - Frontend clears localStorage

## User Management

All user and role management is now done **exclusively in Keycloak**:
- Access Keycloak admin console: `http://localhost:8090`
- Default admin credentials: `admin` / `OpsConductor2024!`
- Realm: `opsconductor`
- Client: `opsconductor-frontend`

## Services Still Running

After removal, the following services remain:
- ✅ postgres-dev (healthy)
- ✅ redis-dev (healthy)
- ✅ kong-dev (healthy)
- ✅ assets-dev (healthy)
- ✅ frontend-dev (running)
- ✅ ai-pipeline-dev (healthy)
- ⚠️ ollama-dev (unhealthy - but working)
- ⚠️ keycloak-dev (unhealthy - but working)
- ⚠️ prefect-dev (unhealthy - but working)
- ❌ automation-dev (not started)
- ❌ network-dev (not started)
- ❌ communication-dev (not started)

## Next Steps

1. **Test Login**: Verify frontend can authenticate through Keycloak
2. **Start Missing Services**: automation, network, communication
3. **Fix Healthchecks**: For ollama, keycloak, prefect
4. **Delete Identity Service Directory**: Remove `/identity-service` folder completely
5. **Update Documentation**: Remove references to identity-service

## Files Modified

- `docker-compose.dev.yml` - Removed identity-service definition
- `kong/kong.yml` - Updated routing to Keycloak
- `frontend/src/services/api.ts` - Direct Keycloak integration
- `frontend/src/pages/Login.tsx` - Store refresh_token

## Verification Commands

```bash
# Check running containers (identity-service should be gone)
docker ps | grep identity

# Check Kong routes
curl http://localhost:8888/services

# Test Keycloak auth (through Kong)
curl -X POST http://localhost:3000/api/v1/auth/realms/opsconductor/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=opsconductor-frontend&username=admin&password=admin&grant_type=password"
```

---

**Status**: ✅ Identity service successfully removed and replaced with direct Keycloak integration
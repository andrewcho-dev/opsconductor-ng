# CRUD Operations Analysis Report

## Executive Summary

After comprehensive analysis of all microservices, I've identified significant inconsistencies in CRUD operations, routing patterns, authentication methods, and nginx exposure. This report details the current state and required fixes.

## Current Service Analysis

### 1. Auth Service
- **Port**: 3001
- **CRUD Operations**: 
  - ✅ POST /login (authentication)
  - ✅ POST /register (user creation)
  - ✅ GET /verify (token verification)
  - ✅ GET /health
- **Authentication**: N/A (provides authentication)
- **Nginx Route**: `/api/v1/auth`
- **Issues**: Not a traditional CRUD service - authentication only

### 2. User Service  
- **Port**: 3002
- **CRUD Operations**:
  - ✅ POST /users (Create)
  - ✅ GET /users (Read List)
  - ✅ GET /users/{user_id} (Read Single)
  - ✅ PUT /users/{user_id} (Update)
  - ✅ DELETE /users/{user_id} (Delete - Soft Delete)
  - ✅ POST /users/{user_id}/roles (Role Assignment)
  - ✅ GET /users/{user_id}/notification-preferences
  - ✅ PUT /users/{user_id}/notification-preferences
  - ✅ GET /health
- **Authentication**: ✅ Consistent with auth service verification
- **Nginx Route**: `/api/v1/users`
- **Issues**: ✅ Complete and consistent

### 3. Credentials Service
- **Port**: 3004
- **CRUD Operations**:
  - ✅ POST /credentials (Create)
  - ✅ GET /credentials (Read List)
  - ✅ GET /credentials/{credential_id} (Read Single)
  - ✅ GET /credentials/{credential_id}/decrypt (Read Decrypted)
  - ✅ PUT /credentials/{credential_id} (Update)
  - ✅ DELETE /credentials/{credential_id} (Delete - Soft Delete)
  - ✅ POST /credentials/{credential_id}/rotate (Rotate)
  - ❌ DUPLICATE DELETE /credentials/{credential_id} (lines 459 & 543)
  - ✅ DELETE /credentials/by-name/{credential_name}
  - ✅ GET /health
- **Authentication**: ✅ Consistent with auth service verification
- **Nginx Route**: `/api/v1/credentials`
- **Issues**: ⚠️ Duplicate DELETE endpoint, inconsistent delete methods (soft vs hard)

### 4. Targets Service
- **Port**: 3005
- **CRUD Operations**:
  - ✅ POST /targets (Create)
  - ✅ GET /targets (Read List)
  - ✅ GET /targets/{target_id} (Read Single)
  - ✅ PUT /targets/{target_id} (Update)
  - ✅ DELETE /targets/{target_id} (Delete - Hard Delete)
  - ✅ GET /health
- **Authentication**: ✅ Consistent with auth service verification
- **Nginx Route**: `/api/v1/targets` and `/api/targets`
- **Issues**: ⚠️ Uses hard delete instead of soft delete, dual nginx routes

### 5. Jobs Service
- **Port**: 3006
- **CRUD Operations**:
  - ✅ POST /jobs (Create)
  - ✅ GET /jobs (Read List)
  - ✅ GET /jobs/{job_id} (Read Single)
  - ✅ PUT /jobs/{job_id} (Update)
  - ✅ DELETE /jobs/{job_id} (Delete - Soft Delete)
  - ✅ POST /jobs/{job_id}/run (Execute Job)
  - ✅ GET /runs (Job Runs List)
  - ✅ GET /runs/{run_id} (Job Run Details)
  - ✅ GET /health
- **Authentication**: ✅ Consistent with auth service verification
- **Nginx Route**: `/api/v1/jobs` and `/api/v1/runs`
- **Issues**: ✅ Complete and consistent

### 6. Executor Service
- **Port**: 3007
- **CRUD Operations**:
  - ✅ GET /health
  - ❌ No traditional CRUD operations (worker service)
- **Authentication**: N/A (internal worker)
- **Nginx Route**: `/api/v1/executor`
- **Issues**: ⚠️ Worker service - no CRUD operations needed

### 7. Scheduler Service
- **Port**: 3008
- **CRUD Operations**:
  - ✅ POST /schedules (Create)
  - ✅ GET /schedules (Read List)
  - ✅ GET /schedules/{schedule_id} (Read Single)
  - ✅ PUT /schedules/{schedule_id} (Update)
  - ✅ DELETE /schedules/{schedule_id} (Delete - Soft Delete)
  - ✅ GET /status (Scheduler Status)
  - ✅ POST /scheduler/start (Start Scheduler)
  - ✅ POST /scheduler/stop (Stop Scheduler)
  - ✅ GET /health
- **Authentication**: ❌ INCONSISTENT - Uses custom verify_token instead of auth service
- **Nginx Route**: `/api/v1/scheduler` and `/api/v1/schedules`
- **Issues**: ⚠️ Inconsistent authentication method

### 8. Notification Service
- **Port**: 3009
- **CRUD Operations**:
  - ✅ GET /health
  - ❌ No traditional CRUD operations exposed (worker service)
- **Authentication**: N/A (internal worker)
- **Nginx Route**: `/api/v1/notification`
- **Issues**: ⚠️ Worker service - limited CRUD operations

### 9. Discovery Service
- **Port**: 3010
- **CRUD Operations**:
  - ❌ Incomplete CRUD implementation
  - ✅ GET /health (assumed)
- **Authentication**: ❌ Uses JWT directly instead of auth service
- **Nginx Route**: `/api/v1/discovery`
- **Issues**: ❌ Incomplete CRUD, inconsistent authentication

## Critical Issues Identified

### 1. Authentication Inconsistencies
- **User Service**: ✅ Uses auth service verification
- **Credentials Service**: ✅ Uses auth service verification  
- **Targets Service**: ✅ Uses auth service verification
- **Jobs Service**: ✅ Uses auth service verification
- **Scheduler Service**: ❌ Uses custom verify_token function
- **Discovery Service**: ❌ Uses direct JWT verification

### 2. Delete Operation Inconsistencies
- **User Service**: ✅ Soft delete (sets deleted_at)
- **Credentials Service**: ⚠️ Mixed - has both soft and hard delete endpoints
- **Targets Service**: ❌ Hard delete (permanent removal)
- **Jobs Service**: ✅ Soft delete (sets deleted_at)
- **Scheduler Service**: ✅ Soft delete (sets deleted_at)

### 3. Route Inconsistencies
- **Targets Service**: Has both `/api/targets` and `/api/v1/targets`
- **Jobs Service**: Uses `/api/v1/jobs` and `/api/v1/runs`
- **Scheduler Service**: Uses `/api/v1/scheduler` and `/api/v1/schedules`

### 4. Missing CRUD Operations
- **Discovery Service**: Incomplete CRUD implementation
- **Notification Service**: Limited CRUD (worker service)
- **Executor Service**: No CRUD (worker service)

## Frontend Page Analysis

### Existing Frontend Pages:
- ✅ Login.tsx
- ✅ Dashboard.tsx
- ✅ Users.tsx
- ✅ Credentials.tsx
- ✅ Targets.tsx
- ✅ Jobs.tsx
- ✅ JobRuns.tsx
- ✅ JobRunDetail.tsx
- ✅ Schedules.tsx
- ✅ Notifications.tsx
- ✅ Discovery.tsx
- ✅ EnhancedSettings.tsx

### Missing Frontend Integration:
- ❌ No dedicated Executor management page (not needed - worker service)
- ⚠️ Discovery page exists but service CRUD is incomplete

## Recommendations for Consistency

### 1. Standardize Authentication
All services should use the same authentication pattern:
```python
def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=5)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.json()["user"]
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
```

### 2. Standardize Delete Operations
All services should use soft delete:
```python
@app.delete("/{resource}/{resource_id}")
async def delete_resource(resource_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    cursor.execute(
        "UPDATE {table} SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
        (datetime.utcnow(), resource_id)
    )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Resource not found or already deleted")
    return {"message": "Resource deleted successfully"}
```

### 3. Standardize Route Patterns
All services should follow the pattern: `/api/v1/{service_name}`

### 4. Complete Missing CRUD Operations
- Fix Discovery Service CRUD implementation
- Remove duplicate endpoints in Credentials Service
- Standardize Targets Service to use soft delete

## Required Fixes

### High Priority:
1. Fix Scheduler Service authentication
2. Fix Discovery Service CRUD and authentication
3. Remove duplicate DELETE endpoint in Credentials Service
4. Standardize Targets Service to soft delete
5. Consolidate nginx routes

### Medium Priority:
1. Ensure all frontend pages work with standardized endpoints
2. Add comprehensive error handling consistency
3. Standardize response formats

### Low Priority:
1. Add missing health check endpoints where needed
2. Optimize nginx configuration
3. Add API documentation consistency

## Next Steps

1. **Fix Authentication**: Update Scheduler and Discovery services to use auth service verification
2. **Fix Delete Operations**: Standardize all services to use soft delete
3. **Remove Duplicates**: Clean up Credentials Service duplicate endpoints
4. **Test Frontend Integration**: Verify all frontend pages work with corrected endpoints
5. **Update Nginx**: Consolidate and standardize routing rules

This analysis provides a roadmap for achieving complete CRUD consistency across all microservices.
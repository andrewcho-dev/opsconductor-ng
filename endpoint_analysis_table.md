# Comprehensive Endpoint Analysis Table

## Service Endpoint Matrix

| Service | Port | Endpoint | Method | Auth Method | Delete Type | Nginx Route | Frontend Page | Status |
|---------|------|----------|--------|-------------|-------------|-------------|---------------|--------|
| **Auth Service** | 3001 | /login | POST | N/A | N/A | /api/v1/auth | Login.tsx | ✅ |
| | | /register | POST | N/A | N/A | /api/v1/auth | Login.tsx | ✅ |
| | | /verify | GET | N/A | N/A | /api/v1/verify | N/A | ✅ |
| | | /health | GET | N/A | N/A | /api/v1/auth/health | N/A | ✅ |
| **User Service** | 3002 | /users | POST | Auth Service | N/A | /api/v1/users | Users.tsx | ✅ |
| | | /users | GET | Auth Service | N/A | /api/v1/users | Users.tsx | ✅ |
| | | /users/{id} | GET | Auth Service | N/A | /api/v1/users | Users.tsx | ✅ |
| | | /users/{id} | PUT | Auth Service | N/A | /api/v1/users | Users.tsx | ✅ |
| | | /users/{id} | DELETE | Auth Service | Soft | /api/v1/users | Users.tsx | ✅ |
| | | /users/{id}/roles | POST | Auth Service | N/A | /api/v1/users | Users.tsx | ✅ |
| | | /users/{id}/notification-preferences | GET | Auth Service | N/A | /api/v1/users | Users.tsx | ✅ |
| | | /users/{id}/notification-preferences | PUT | Auth Service | N/A | /api/v1/users | Users.tsx | ✅ |
| | | /health | GET | N/A | N/A | /api/v1/users/health | N/A | ✅ |
| **Credentials Service** | 3004 | /credentials | POST | Auth Service | N/A | /api/v1/credentials | Credentials.tsx | ✅ |
| | | /credentials | GET | Auth Service | N/A | /api/v1/credentials | Credentials.tsx | ✅ |
| | | /credentials/{id} | GET | Auth Service | N/A | /api/v1/credentials | Credentials.tsx | ✅ |
| | | /credentials/{id}/decrypt | GET | Auth Service | N/A | /api/v1/credentials | Credentials.tsx | ✅ |
| | | /credentials/{id} | PUT | Auth Service | N/A | /api/v1/credentials | Credentials.tsx | ✅ |
| | | /credentials/{id} | DELETE | Auth Service | Soft | /api/v1/credentials | Credentials.tsx | ⚠️ |
| | | /credentials/{id} | DELETE | Auth Service | Hard | /api/v1/credentials | Credentials.tsx | ❌ DUPLICATE |
| | | /credentials/by-name/{name} | DELETE | Auth Service | Hard | /api/v1/credentials | Credentials.tsx | ⚠️ |
| | | /credentials/{id}/rotate | POST | Auth Service | N/A | /api/v1/credentials | Credentials.tsx | ✅ |
| | | /health | GET | N/A | N/A | /api/v1/credentials/health | N/A | ✅ |
| **Targets Service** | 3005 | /targets | POST | Auth Service | N/A | /api/v1/targets | Targets.tsx | ✅ |
| | | /targets | GET | Auth Service | N/A | /api/v1/targets | Targets.tsx | ✅ |
| | | /targets/{id} | GET | Auth Service | N/A | /api/v1/targets | Targets.tsx | ✅ |
| | | /targets/{id} | PUT | Auth Service | N/A | /api/v1/targets | Targets.tsx | ✅ |
| | | /targets/{id} | DELETE | Auth Service | Hard | /api/v1/targets | Targets.tsx | ⚠️ |
| | | /health | GET | N/A | N/A | /api/v1/targets/health | N/A | ✅ |
| **Jobs Service** | 3006 | /jobs | POST | Auth Service | N/A | /api/v1/jobs | Jobs.tsx | ✅ |
| | | /jobs | GET | Auth Service | N/A | /api/v1/jobs | Jobs.tsx | ✅ |
| | | /jobs/{id} | GET | Auth Service | N/A | /api/v1/jobs | Jobs.tsx | ✅ |
| | | /jobs/{id} | PUT | Auth Service | N/A | /api/v1/jobs | Jobs.tsx | ✅ |
| | | /jobs/{id} | DELETE | Auth Service | Soft | /api/v1/jobs | Jobs.tsx | ✅ |
| | | /jobs/{id}/run | POST | Auth Service | N/A | /api/v1/jobs | Jobs.tsx | ✅ |
| | | /runs | GET | Auth Service | N/A | /api/v1/runs | JobRuns.tsx | ✅ |
| | | /runs/{id} | GET | Auth Service | N/A | /api/v1/runs | JobRunDetail.tsx | ✅ |
| | | /health | GET | N/A | N/A | /api/v1/jobs/health | N/A | ✅ |
| **Executor Service** | 3007 | /health | GET | N/A | N/A | /api/v1/executor/health | N/A | ✅ |
| | | (Worker Service - No CRUD) | | | | | | ✅ |
| **Scheduler Service** | 3008 | /schedules | POST | Custom JWT | N/A | /api/v1/schedules | Schedules.tsx | ⚠️ |
| | | /schedules | GET | Custom JWT | N/A | /api/v1/schedules | Schedules.tsx | ⚠️ |
| | | /schedules/{id} | GET | Custom JWT | N/A | /api/v1/schedules | Schedules.tsx | ⚠️ |
| | | /schedules/{id} | PUT | Custom JWT | N/A | /api/v1/schedules | Schedules.tsx | ⚠️ |
| | | /schedules/{id} | DELETE | Custom JWT | Soft | /api/v1/schedules | Schedules.tsx | ⚠️ |
| | | /status | GET | Custom JWT | N/A | /api/v1/scheduler | Schedules.tsx | ⚠️ |
| | | /scheduler/start | POST | Custom JWT | N/A | /api/v1/scheduler | Schedules.tsx | ⚠️ |
| | | /scheduler/stop | POST | Custom JWT | N/A | /api/v1/scheduler | Schedules.tsx | ⚠️ |
| | | /health | GET | N/A | N/A | /api/v1/scheduler/health | N/A | ✅ |
| **Notification Service** | 3009 | /health | GET | N/A | N/A | /api/v1/notification/health | N/A | ✅ |
| | | (Worker Service - Limited CRUD) | | | | | Notifications.tsx | ⚠️ |
| **Discovery Service** | 3010 | /discovery-jobs | POST | Direct JWT | N/A | /api/v1/discovery | Discovery.tsx | ❌ |
| | | /discovery-jobs | GET | Direct JWT | N/A | /api/v1/discovery | Discovery.tsx | ❌ |
| | | /discovery-jobs/{id} | GET | Direct JWT | N/A | /api/v1/discovery | Discovery.tsx | ❌ |
| | | /discovery-jobs/{id} | PUT | Direct JWT | N/A | /api/v1/discovery | Discovery.tsx | ❌ |
| | | /discovery-jobs/{id} | DELETE | Direct JWT | Unknown | /api/v1/discovery | Discovery.tsx | ❌ |
| | | /health | GET | N/A | N/A | /api/v1/discovery/health | N/A | ✅ |

## Legend

### Status Indicators:
- ✅ **Complete and Consistent**: Endpoint is properly implemented and follows standards
- ⚠️ **Needs Attention**: Endpoint exists but has consistency issues
- ❌ **Critical Issue**: Endpoint has major problems or is missing

### Auth Method Types:
- **Auth Service**: Uses verify_token_with_auth_service() - STANDARD
- **Custom JWT**: Uses custom JWT verification - INCONSISTENT
- **Direct JWT**: Uses direct JWT parsing - INCONSISTENT
- **N/A**: No authentication required

### Delete Types:
- **Soft**: Sets deleted_at timestamp - STANDARD
- **Hard**: Permanently removes record - INCONSISTENT
- **N/A**: Not applicable

## Critical Issues Summary

### 1. Authentication Inconsistencies (7 endpoints affected)
- **Scheduler Service**: All 8 endpoints use custom JWT instead of auth service
- **Discovery Service**: All 5 endpoints use direct JWT instead of auth service

### 2. Delete Operation Inconsistencies (4 endpoints affected)
- **Credentials Service**: Has duplicate DELETE endpoint (lines 459 & 543)
- **Credentials Service**: Uses hard delete for by-name endpoint
- **Targets Service**: Uses hard delete instead of soft delete

### 3. Missing/Incomplete CRUD (1 service affected)
- **Discovery Service**: CRUD operations are incomplete/not properly implemented

### 4. Nginx Route Inconsistencies
- **Targets Service**: Exposed on both /api/targets and /api/v1/targets
- **Multiple Services**: Some services have multiple route patterns

## Immediate Action Items

### Priority 1 (Critical):
1. **Fix Scheduler Service Authentication**: Replace custom JWT with auth service verification
2. **Fix Discovery Service**: Complete CRUD implementation and fix authentication
3. **Remove Credentials Service Duplicates**: Remove duplicate DELETE endpoint

### Priority 2 (Important):
1. **Standardize Delete Operations**: Convert Targets and Credentials hard deletes to soft deletes
2. **Consolidate Nginx Routes**: Remove duplicate route patterns
3. **Test Frontend Integration**: Ensure all pages work with corrected endpoints

### Priority 3 (Maintenance):
1. **Add Missing Health Checks**: Ensure all services have health endpoints
2. **Standardize Error Responses**: Ensure consistent error message formats
3. **Update API Documentation**: Reflect all changes in documentation

This table provides a complete view of the current state and required fixes for achieving CRUD consistency across all microservices.
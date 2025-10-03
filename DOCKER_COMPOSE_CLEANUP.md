# Docker Compose Cleanup - Removed `-dev` Suffix and Standardized Filename

## Date
January 2025

## Summary
Completely rewrote the docker-compose configuration to remove all `-dev` suffixes from container names and network names, and standardized to use the canonical `docker-compose.yml` filename. Removed all obsolete docker-compose files.

## Changes Made

### 1. Network Name
- **Before**: `opsconductor-dev`
- **After**: `opsconductor`

### 2. Container Names (All `-dev` suffixes removed)
- `opsconductor-postgres-dev` → `opsconductor-postgres`
- `opsconductor-redis-dev` → `opsconductor-redis`
- `opsconductor-ollama-dev` → `opsconductor-ollama`
- `opsconductor-kong-dev` → `opsconductor-kong`
- `opsconductor-keycloak-dev` → `opsconductor-keycloak`
- `opsconductor-ai-pipeline-dev` → `opsconductor-ai-pipeline`
- `opsconductor-automation-dev` → `opsconductor-automation`
- `opsconductor-assets-dev` → `opsconductor-assets`
- `opsconductor-network-dev` → `opsconductor-network`
- `opsconductor-communication-dev` → `opsconductor-communication`
- `opsconductor-frontend-dev` → `opsconductor-frontend`

### 3. Service URL Updates
Updated environment variables in `ai-pipeline` service to use clean service names:
- `OLLAMA_BASE_URL`: `http://opsconductor-ollama-dev:11434` → `http://ollama:11434`
- `NETWORK_SERVICE_URL`: `http://network-service:8003` → `http://network-service:3006` (also fixed port)
- All other service URLs now use simple service names without container name prefixes

### 4. Healthcheck Fixes
Fixed healthchecks for Ollama and Keycloak that were previously failing:

#### Ollama
- **Issue**: Healthcheck used `curl` command which doesn't exist in ollama image
- **Fix**: Changed to `ollama list` command which is native to the container
- **Result**: ✅ Now shows as healthy

#### Keycloak
- **Issue**: Healthcheck was looking for `/auth/realms/master` but Keycloak 22+ removed the `/auth` prefix
- **Fix**: Updated path to `/realms/master` and improved the shell command syntax
- **Result**: ✅ Now shows as healthy

## Final System Status

### All 11 Containers Running and Healthy ✅

| Container | Status | Port Mapping | Notes |
|-----------|--------|--------------|-------|
| opsconductor-postgres | ✅ Healthy | Internal only (5432) | PostgreSQL 17 |
| opsconductor-redis | ✅ Healthy | Internal only (6379) | Redis 7 |
| opsconductor-ollama | ✅ Healthy | 11434:11434 | AI model server with GPU |
| opsconductor-kong | ✅ Healthy | 3000:8000, 8888:8001 | API Gateway |
| opsconductor-keycloak | ✅ Healthy | 8090:8080 | Identity provider |
| opsconductor-ai-pipeline | ✅ Healthy | 3005:8000 | 4-stage AI pipeline |
| opsconductor-automation | ✅ Healthy | 8010:3003 | Automation service |
| opsconductor-assets | ✅ Healthy | 8002:3002 | Asset management |
| opsconductor-network | ✅ Healthy | 8003:3006 | Network analyzer |
| opsconductor-communication | ✅ Healthy | 8004:3004 | Communication service |
| opsconductor-frontend | ✅ Running | 3100:3000 | React frontend |

## Benefits

1. **Cleaner Names**: Removed redundant `-dev` suffix from all containers
2. **Simpler Configuration**: Network and service names are more straightforward
3. **All Services Healthy**: Fixed healthcheck issues for Ollama and Keycloak
4. **Consistent Naming**: Service names in docker-compose match container names
5. **Better Maintainability**: Easier to read and understand the configuration

## Migration Steps Performed

1. Stopped all existing containers with `-dev` suffix
2. Removed all old containers
3. Rewrote docker-compose configuration with clean names
4. Renamed `docker-compose.dev.yml` → `docker-compose.yml` (standard name)
5. Removed obsolete files: `docker-compose.clean.yml` and backed up old `docker-compose.yml` → `docker-compose.yml.old`
6. Started all services with new configuration
7. Verified all containers are healthy

## Infrastructure Cleanup Summary

Over the course of this cleanup effort, we've removed 2 unused services:
1. **identity-service** - Unnecessary proxy to Keycloak (removed earlier)
2. **prefect** - Orchestration engine that was never used (removed earlier)

**Result**: From 13 planned containers → 11 running containers (15% reduction in complexity)

## Commands for Future Reference

```bash
# Start all services (using standard docker-compose.yml)
cd /home/opsconductor/opsconductor-ng
docker compose up -d

# Check status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View logs for a specific service
docker logs opsconductor-<service-name>

# Restart a specific service
docker compose restart <service-name>

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

## Files Cleanup

### Current Files
- **`docker-compose.yml`** - The active, clean configuration (no `-dev` suffixes)
- **`docker-compose.yml.old`** - Backup of the old configuration (can be deleted after verification)

### Removed Files
- ~~`docker-compose.dev.yml`~~ - Renamed to `docker-compose.yml`
- ~~`docker-compose.clean.yml`~~ - Obsolete experimental version

## Notes

- Now using the standard `docker-compose.yml` filename (no need to specify `-f` flag)
- All volume names remain unchanged (postgres_data, redis_data, ollama_models)
- Port mappings remain unchanged for external access
- Development volume mounts for live code reloading are preserved
- The old `docker-compose.yml.old` backup can be safely deleted once everything is verified working
# Adding New Services to OpsConductor

This document outlines the standardized process for adding new microservices to the OpsConductor system. Following this process ensures consistency, proper nginx routing, and avoids common pitfalls.

## Service Architecture Standards

### URL Pattern Standard
- **External URL**: `/api/v1/{service-name}/*` (what clients call)
- **Internal URL**: `/{service-name}/*` (what the service actually serves)
- **Health Endpoint**: `/health` (internal), `/api/v1/{service-name}/health` (external)

### Example
- Service: `discovery-service`
- External: `https://localhost/api/v1/discovery/jobs`
- Internal: `http://discovery-service:3010/discovery/jobs`
- Nginx rewrites: `/api/v1/discovery/(.*)` → `/$1`

## Step-by-Step Process

### 1. Create Service Directory Structure
```
{service-name}/
├── Dockerfile
├── main.py
├── requirements.txt
├── models.py (if needed)
└── services/ (if needed)
```

### 2. Service Implementation Standards

#### FastAPI Service Template
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI(title="{Service Name} Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint (REQUIRED)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "{service-name}"}

# Service endpoints - use /{service-name}/* pattern
@app.get("/{service-name}/endpoint")
async def service_endpoint():
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={PORT})
```

#### Dockerfile Template
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user
RUN addgroup --gid 1001 --system python
RUN adduser --system --uid 1001 --gid 1001 python
RUN chown -R python:python /app

USER python

EXPOSE {PORT}

CMD ["python", "main.py"]
```

### 3. Update docker-compose-python.yml

Add service configuration:
```yaml
  {service-name}:
    build: ./{service-name}
    container_name: opsconductor-{service-name}
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: opsconductor
      DB_USER: postgres
      DB_PASSWORD: postgres123
      JWT_SECRET_KEY: your-jwt-secret-change-in-production
    ports:
      - "{PORT}:{PORT}"
    networks:
      - opsconductor-net
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
```

Add to nginx dependencies:
```yaml
  nginx:
    # ... existing config
    depends_on:
      - frontend
      - auth-service
      - user-service
      - credentials-service
      - targets-service
      - jobs-service
      - executor-service
      - scheduler-service
      - notification-service
      - {service-name}  # ADD THIS LINE
```

### 4. Update nginx Configuration

Edit `nginx/nginx.conf` and add the service location block:

```nginx
# {Service Name} Service
location /api/v1/{service-name}/ {
    rewrite ^/api/v1/{service-name}/(.*)$ /$1 break;
    proxy_pass http://{service-name}:{PORT};
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
}
```

**CRITICAL**: Add this block in the correct location within the `server` block, following the existing pattern.

### 5. Database Schema (if needed)

If the service requires database tables, add them to `database/init-schema.sql`:

```sql
-- {Service Name} Tables
CREATE TABLE IF NOT EXISTS {service_name}_table (
    id SERIAL PRIMARY KEY,
    -- other columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. Build and Deploy Process

**CRITICAL ORDER - Follow exactly:**

1. **Build the new service**:
   ```bash
   cd /home/opsconductor/microservice-system
   docker compose -f docker-compose-python.yml build {service-name}
   ```

2. **Build nginx** (to pick up config changes):
   ```bash
   docker compose -f docker-compose-python.yml build nginx
   ```

3. **Start/restart services**:
   ```bash
   docker compose -f docker-compose-python.yml up -d
   ```

### 7. Testing Checklist

Test in this order:

1. **Health endpoint**:
   ```bash
   curl -k https://localhost/api/v1/{service-name}/health
   ```

2. **Service endpoints with authentication**:
   ```bash
   # Get token first
   TOKEN=$(curl -k -X POST https://localhost/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')
   
   # Test endpoint
   curl -k -H "Authorization: Bearer $TOKEN" \
     https://localhost/api/v1/{service-name}/endpoint
   ```

3. **Verify nginx routing**:
   ```bash
   # Check nginx config is loaded
   docker exec opsconductor-nginx grep -A 5 "{service-name}" /etc/nginx/nginx.conf
   ```

## Common Issues and Solutions

### Issue: 404 Not Found
**Cause**: Service endpoints not registered or nginx config not loaded
**Solution**: 
1. Check service logs: `docker logs opsconductor-{service-name}`
2. Rebuild nginx: `docker compose -f docker-compose-python.yml build nginx`
3. Restart nginx: `docker compose -f docker-compose-python.yml restart nginx`

### Issue: Getting HTML instead of JSON
**Cause**: nginx routing not working, falling back to frontend
**Solution**: 
1. Rebuild nginx container: `docker compose -f docker-compose-python.yml build nginx`
2. Restart nginx: `docker compose -f docker-compose-python.yml up -d nginx`

### Issue: Service not starting
**Cause**: Database dependency or environment variables
**Solution**:
1. Check logs: `docker logs opsconductor-{service-name}`
2. Verify database is healthy: `docker ps` (postgres should show "healthy")
3. Check environment variables in docker-compose-python.yml

### Issue: Authentication errors
**Cause**: JWT verification issues
**Solution**:
1. Ensure JWT_SECRET_KEY matches across all services
2. Import auth utilities: `from auth_utils import verify_token`
3. Use `user: dict = Depends(verify_token)` in endpoints

## Port Allocation

Current port assignments:
- 3001: auth-service
- 3002: user-service  
- 3004: credentials-service
- 3005: targets-service
- 3006: jobs-service
- 3007: executor-service
- 3008: scheduler-service
- 3009: notification-service
- 3010: discovery-service

**Next available port: 3011**

## Container Rebuild Requirements

**Always rebuild these containers when adding a new service:**

1. **New service container** - Contains your code changes
2. **nginx container** - Contains updated routing configuration

**Never just restart without rebuilding** - Docker containers cache the built image and won't pick up file changes.

## Verification Commands

After adding a service, run these commands to verify everything works:

```bash
# 1. Check all containers are running
docker ps

# 2. Check nginx config contains your service
docker exec opsconductor-nginx grep -A 5 "{service-name}" /etc/nginx/nginx.conf

# 3. Test health endpoint
curl -k https://localhost/api/v1/{service-name}/health

# 4. Check service logs
docker logs opsconductor-{service-name} --tail 10

# 5. Test with authentication
TOKEN=$(curl -k -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

curl -k -H "Authorization: Bearer $TOKEN" \
  https://localhost/api/v1/{service-name}/your-endpoint
```

## Summary

The key to success is following the **exact same pattern** as existing services:
1. Use the standard URL pattern (`/api/v1/{service-name}/*` → `/{service-name}/*`)
2. Always rebuild both the service AND nginx containers
3. Follow the exact nginx configuration template
4. Test systematically using the verification commands

**Remember**: Every service follows this identical pattern. If you're doing something different, you're doing it wrong.
# Service Configuration Guide

## Overview
This document provides standardized configuration for all OpsConductor services after the HTTP communication standardization migration.

## Environment Variables

### Core Service URLs
All services now use standardized URL environment variables:

```bash
# Authentication Service
AUTH_SERVICE_URL=http://auth-service:3001

# User Management Service  
USER_SERVICE_URL=http://user-service:3002

# Jobs Service
JOBS_SERVICE_URL=http://jobs-service:3006

# Executor Service
EXECUTOR_SERVICE_URL=http://executor-service:3007

# Notification Service
NOTIFICATION_SERVICE_URL=http://notification-service:3009

# Credentials Service
CREDENTIALS_SERVICE_URL=http://credentials-service:3004

# Scheduler Service
SCHEDULER_SERVICE_URL=http://scheduler-service:3008
```

### Service Authentication Credentials
Each service requires credentials for service-to-service communication:

```bash
# Scheduler Service Credentials
SCHEDULER_SERVICE_USERNAME=admin
SCHEDULER_SERVICE_PASSWORD=admin123

# Executor Service Credentials  
EXECUTOR_SERVICE_USERNAME=admin
EXECUTOR_SERVICE_PASSWORD=admin123

# Notification Service Credentials
NOTIFICATION_SERVICE_USERNAME=admin
NOTIFICATION_SERVICE_PASSWORD=admin123

# Jobs Service Credentials
JOBS_SERVICE_USERNAME=admin
JOBS_SERVICE_PASSWORD=admin123

# User Service Credentials
USER_SERVICE_USERNAME=admin
USER_SERVICE_PASSWORD=admin123

# Credentials Service Credentials
CREDENTIALS_SERVICE_USERNAME=admin
CREDENTIALS_SERVICE_PASSWORD=admin123
```

### HTTP Client Configuration
Standardized timeout and retry settings:

```bash
# Default HTTP timeouts (in seconds)
SERVICE_HTTP_TIMEOUT=30
SERVICE_HTTP_CONNECT_TIMEOUT=10

# Retry configuration
SERVICE_HTTP_MAX_RETRIES=3
SERVICE_HTTP_RETRY_DELAY=1

# Connection pool settings
SERVICE_HTTP_MAX_CONNECTIONS=100
SERVICE_HTTP_MAX_KEEPALIVE_CONNECTIONS=20
```

### Logging Configuration
```bash
# Service logging levels
LOG_LEVEL=INFO

# Enable service communication logging
SERVICE_COMM_LOG_ENABLED=true
```

## Service-Specific Configuration

### Scheduler Service
```bash
# Scheduler-specific settings
SCHEDULER_POLL_INTERVAL=30
SCHEDULER_AUTO_START=true
```

### Executor Service  
```bash
# Executor-specific settings
WORKER_POLL_INTERVAL=5
WORKER_ENABLED=true
EXECUTOR_MAX_CONCURRENT_JOBS=10
```

### Notification Service
```bash
# Notification-specific settings
NOTIFICATION_BATCH_SIZE=100
NOTIFICATION_RETRY_ATTEMPTS=3
```

## Docker Compose Configuration

### Updated docker-compose.yml
```yaml
version: '3.8'

services:
  auth-service:
    environment:
      - AUTH_SERVICE_URL=http://auth-service:3001
      - USER_SERVICE_URL=http://user-service:3002
      - LOG_LEVEL=INFO
      - SERVICE_HTTP_TIMEOUT=30

  user-service:
    environment:
      - AUTH_SERVICE_URL=http://auth-service:3001
      - USER_SERVICE_URL=http://user-service:3002
      - LOG_LEVEL=INFO
      - SERVICE_HTTP_TIMEOUT=30

  jobs-service:
    environment:
      - AUTH_SERVICE_URL=http://auth-service:3001
      - JOBS_SERVICE_URL=http://jobs-service:3006
      - EXECUTOR_SERVICE_URL=http://executor-service:3007
      - NOTIFICATION_SERVICE_URL=http://notification-service:3009
      - LOG_LEVEL=INFO
      - SERVICE_HTTP_TIMEOUT=30

  executor-service:
    environment:
      - AUTH_SERVICE_URL=http://auth-service:3001
      - JOBS_SERVICE_URL=http://jobs-service:3006
      - NOTIFICATION_SERVICE_URL=http://notification-service:3009
      - CREDENTIALS_SERVICE_URL=http://credentials-service:3004
      - EXECUTOR_SERVICE_USERNAME=admin
      - EXECUTOR_SERVICE_PASSWORD=admin123
      - WORKER_POLL_INTERVAL=5
      - WORKER_ENABLED=true
      - LOG_LEVEL=INFO
      - SERVICE_HTTP_TIMEOUT=30

  scheduler-service:
    environment:
      - AUTH_SERVICE_URL=http://auth-service:3001
      - JOBS_SERVICE_URL=http://jobs-service:3006
      - SCHEDULER_SERVICE_USERNAME=admin
      - SCHEDULER_SERVICE_PASSWORD=admin123
      - SCHEDULER_POLL_INTERVAL=30
      - LOG_LEVEL=INFO
      - SERVICE_HTTP_TIMEOUT=30

  notification-service:
    environment:
      - AUTH_SERVICE_URL=http://auth-service:3001
      - NOTIFICATION_SERVICE_URL=http://notification-service:3009
      - USER_SERVICE_URL=http://user-service:3002
      - LOG_LEVEL=INFO
      - SERVICE_HTTP_TIMEOUT=30

  credentials-service:
    environment:
      - AUTH_SERVICE_URL=http://auth-service:3001
      - CREDENTIALS_SERVICE_URL=http://credentials-service:3004
      - LOG_LEVEL=INFO
      - SERVICE_HTTP_TIMEOUT=30
```

## Migration Checklist

### ✅ Completed
- [x] Created service authentication utility (`shared/utility_service_auth.py`)
- [x] Created service client wrappers (`shared/utility_service_clients.py`)
- [x] Migrated scheduler service to use standardized clients
- [x] Migrated executor service to use standardized clients
- [x] Migrated notification service auth to shared utilities
- [x] Migrated utility functions to use standardized clients

### 🔄 Configuration Updates
- [x] Standardized environment variable names
- [x] Added service authentication credentials
- [x] Configured HTTP client timeouts and retries
- [x] Updated docker-compose.yml template

## Benefits Achieved

### 🚀 **Improved Reliability**
- Centralized authentication with token caching
- Standardized error handling and retries
- Connection pooling and timeout management

### 🔧 **Better Maintainability**
- Single source of truth for service communication
- Consistent error handling patterns
- Reduced code duplication

### 📊 **Enhanced Observability**
- Standardized logging for service communications
- Centralized metrics collection
- Better error tracking and debugging

### 🔒 **Stronger Security**
- Centralized authentication management
- Secure credential handling
- Token refresh automation

## Next Steps

1. **Update Production Configuration**: Apply the new environment variables to production deployments
2. **Monitor Service Health**: Verify all services are communicating properly with the new clients
3. **Performance Testing**: Validate that the new communication layer doesn't introduce latency
4. **Documentation Updates**: Update API documentation to reflect the new communication patterns

## Troubleshooting

### Common Issues
1. **Authentication Failures**: Check service credentials and auth service availability
2. **Connection Timeouts**: Verify service URLs and network connectivity
3. **Token Refresh Issues**: Check auth service logs and token expiration settings

### Debug Commands
```bash
# Check service connectivity
curl -f http://auth-service:3001/health

# Verify environment variables
docker exec <service-container> env | grep SERVICE

# Check service logs
docker logs <service-container> | grep "service.*client"
```
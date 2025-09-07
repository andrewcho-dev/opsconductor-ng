# Database Connection Pool Migration

## Overview
This document outlines the complete migration from individual database connections to a centralized connection pool system for the OpsConductor microservices architecture.

## Changes Made

### 1. Shared Database Module (`shared/database.py`)
- **Created**: New centralized database connection pool module
- **Features**:
  - Connection pooling with configurable min/max connections
  - Context manager for automatic connection/cursor management
  - Automatic transaction handling (commit/rollback)
  - Health check functionality
  - Proper connection cleanup on shutdown
  - Thread-safe implementation using `psycopg2.pool.ThreadedConnectionPool`

### 2. Services Updated

#### Core Services (Completed)
- ✅ **auth-service**: Updated to use connection pool
- ✅ **credentials-service**: Updated to use connection pool  
- ✅ **targets-service**: Updated to use connection pool

#### Services Requiring Database Operations Updates
- ⚠️ **user-service**: Partially updated (imports added, some DB operations updated)
- ⚠️ **jobs-service**: Requires update
- ⚠️ **executor-service**: Requires update
- ⚠️ **scheduler-service**: Requires update
- ⚠️ **notification-service**: Requires update
- ⚠️ **discovery-service**: Requires update
- ⚠️ **step-libraries-service**: Requires update

### 3. Configuration Changes

#### Docker Compose (`docker-compose.yml`)
- **Added** to all services:
  - `DB_POOL_MIN: 2` - Minimum connections in pool
  - `DB_POOL_MAX: 10` - Maximum connections in pool

#### Environment Variables
- `DB_POOL_MIN`: Minimum number of connections (default: 2)
- `DB_POOL_MAX`: Maximum number of connections (default: 10)
- Existing DB connection variables remain unchanged

### 4. Code Changes Pattern

#### Before (Old Pattern)
```python
import psycopg2
import psycopg2.extras

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# Usage
conn = get_db_connection()
try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    conn.commit()
finally:
    conn.close()
```

#### After (New Pattern)
```python
import sys
sys.path.append('/home/opsconductor')
from shared.database import get_db_cursor

# Usage
with get_db_cursor() as cursor:  # Auto-commit
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()

# Or for read-only
with get_db_cursor(commit=False) as cursor:
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
```

### 5. Health Check Updates
All services now include database connectivity in health checks:
```python
@app.get("/health")
async def health_check():
    db_health = check_database_health()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
        "service": "service-name",
        "database": db_health
    }
```

### 6. Shutdown Handlers
All services now properly cleanup connection pools:
```python
@app.on_event("shutdown")
async def shutdown_event():
    cleanup_database_pool()
```

## Benefits

### Performance Improvements
- **Connection Reuse**: Eliminates overhead of creating/destroying connections
- **Reduced Latency**: Pre-established connections ready for immediate use
- **Better Resource Utilization**: Controlled number of database connections

### Reliability Improvements
- **Connection Management**: Automatic handling of broken connections
- **Transaction Safety**: Proper commit/rollback handling
- **Error Handling**: Centralized database error management

### Operational Benefits
- **Monitoring**: Centralized health checks for database connectivity
- **Configuration**: Easy tuning of connection pool parameters
- **Maintenance**: Single point of database connection logic

## Testing

### Test Script
Created `test_connection_pool.py` to verify:
- Basic database connectivity
- Concurrent connection handling
- Transaction management
- Health check functionality

### Running Tests
```bash
cd /home/opsconductor
python test_connection_pool.py
```

## Next Steps

### Immediate (High Priority)
1. **Complete user-service migration**: Update remaining database operations
2. **Update remaining services**: Apply same pattern to all services
3. **Test thoroughly**: Run integration tests with connection pooling
4. **Monitor performance**: Verify improved performance metrics

### Future Enhancements
1. **Connection Pool Monitoring**: Add metrics for pool utilization
2. **Dynamic Pool Sizing**: Implement adaptive pool sizing based on load
3. **Connection Pool per Service**: Consider separate pools for different services
4. **Database Failover**: Add support for database failover scenarios

## Rollback Plan
If issues arise:
1. Revert docker-compose.yml environment variables
2. Restore original service files from git history
3. Remove shared/database.py module
4. Services will fall back to individual connections

## Configuration Recommendations

### Development Environment
- `DB_POOL_MIN: 1`
- `DB_POOL_MAX: 5`

### Production Environment
- `DB_POOL_MIN: 5`
- `DB_POOL_MAX: 20`

### High-Load Environment
- `DB_POOL_MIN: 10`
- `DB_POOL_MAX: 50`

## Monitoring
Monitor these metrics after deployment:
- Database connection count
- Connection pool utilization
- Query response times
- Connection errors/timeouts
- Service health check status
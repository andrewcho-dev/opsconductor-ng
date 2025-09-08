---
description: "Database patterns and schema standards for OpsConductor PostgreSQL operations"
globs: ["**/main.py", "**/*service*/**.py", "**/utility_*.py", "**/database/**/*.sql"]
alwaysApply: false
---

# OpsConductor Database Patterns

## 🗄️ Database Architecture

### Core Infrastructure
- **Engine**: PostgreSQL 16 (Alpine)
- **Connection Pool**: Managed by shared database utilities
- **Schema**: Comprehensive schema in `database/init-schema.sql`
- **Migrations**: Version-controlled in `database/migrations/`
- **Transactions**: Automatic with context managers

## 📋 Database Schema Overview

### Core Tables
```sql
-- Users and Authentication
users (id, username, email, password_hash, is_admin, created_at, updated_at)
user_sessions (id, user_id, token_hash, expires_at, created_at)

-- Target Management
targets (id, name, host, port, platform, credential_id, group_id, created_at, updated_at)
target_groups (id, name, description, created_at, updated_at)
target_group_memberships (target_id, group_id, created_at)

-- Credentials
credentials (id, name, username, encrypted_password, created_at, updated_at)

-- Jobs and Execution
jobs (id, name, description, target_id, steps, created_by, created_at, updated_at)
job_executions (id, job_id, target_id, status, started_at, completed_at, output, error_message)
job_schedules (id, job_id, cron_expression, timezone, is_active, created_at, updated_at)

-- Notifications
notifications (id, type, destination, template_id, payload, status, created_at, sent_at)
notification_templates (id, name, subject, body, type, created_at, updated_at)
user_notification_preferences (user_id, notification_type, enabled, destination)

-- Discovery and Libraries
discovery_jobs (id, name, network_range, status, created_by, created_at, completed_at)
discovered_targets (id, discovery_job_id, host, platform, services, created_at)
step_libraries (id, name, version, category, steps_data, created_at, updated_at)
```

## 🔧 Database Connection Patterns

### Using Shared Database Utilities
```python
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool

# Read operation (no transaction)
def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID with read-only cursor"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT id, username, email, is_admin FROM users WHERE id = %s",
                (user_id,)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return None

# Write operation (with transaction)
def create_user(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create user with automatic transaction"""
    try:
        with get_db_cursor() as cursor:  # commit=True by default
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, is_admin) 
                   VALUES (%s, %s, %s, %s) RETURNING id, username, email""",
                (user_data['username'], user_data['email'], 
                 user_data['password_hash'], user_data.get('is_admin', False))
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return None
```

### Complex Queries with Joins
```python
def get_job_with_target_info(job_id: int) -> Optional[Dict[str, Any]]:
    """Get job with target and credential information"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT 
                    j.id, j.name, j.description, j.steps,
                    t.name as target_name, t.host, t.platform,
                    c.name as credential_name, c.username,
                    tg.name as group_name
                FROM jobs j
                JOIN targets t ON j.target_id = t.id
                LEFT JOIN credentials c ON t.credential_id = c.id
                LEFT JOIN target_groups tg ON t.group_id = tg.id
                WHERE j.id = %s
            """, (job_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        return None
```

### Batch Operations
```python
def create_multiple_targets(targets_data: List[Dict[str, Any]]) -> bool:
    """Create multiple targets in a single transaction"""
    try:
        with get_db_cursor() as cursor:
            for target_data in targets_data:
                cursor.execute("""
                    INSERT INTO targets (name, host, port, platform, credential_id, group_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    target_data['name'], target_data['host'], target_data['port'],
                    target_data['platform'], target_data['credential_id'], 
                    target_data.get('group_id')
                ))
            return True
    except Exception as e:
        logger.error(f"Failed to create targets: {e}")
        return False
```

## 🔐 Security Patterns

### Encrypted Data Storage
```python
def store_encrypted_credential(name: str, username: str, password: str) -> Optional[int]:
    """Store credential with AES-GCM encryption"""
    try:
        from shared.encryption import encrypt_data
        encrypted_password = encrypt_data(password)
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO credentials (name, username, encrypted_password)
                VALUES (%s, %s, %s) RETURNING id
            """, (name, username, encrypted_password))
            result = cursor.fetchone()
            return result['id'] if result else None
    except Exception as e:
        logger.error(f"Failed to store credential: {e}")
        return None
```

### SQL Injection Prevention
```python
# ✅ CORRECT: Use parameterized queries
def get_targets_by_platform(platform: str) -> List[Dict[str, Any]]:
    """Get targets by platform using parameterized query"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM targets WHERE platform = %s ORDER BY name",
                (platform,)
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to get targets: {e}")
        return []

# ❌ WRONG: String concatenation (SQL injection risk)
def get_targets_by_platform_wrong(platform: str):
    query = f"SELECT * FROM targets WHERE platform = '{platform}'"  # DON'T DO THIS
    cursor.execute(query)
```

## 📊 Query Optimization Patterns

### Efficient Pagination
```python
def get_job_executions_paginated(page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """Get paginated job executions with total count"""
    try:
        offset = (page - 1) * per_page
        
        with get_db_cursor(commit=False) as cursor:
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM job_executions")
            total = cursor.fetchone()['total']
            
            # Get paginated results
            cursor.execute("""
                SELECT je.*, j.name as job_name, t.name as target_name
                FROM job_executions je
                JOIN jobs j ON je.job_id = j.id
                JOIN targets t ON je.target_id = t.id
                ORDER BY je.started_at DESC
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            
            executions = cursor.fetchall()
            
            return {
                'executions': executions,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
    except Exception as e:
        logger.error(f"Failed to get executions: {e}")
        return {'executions': [], 'total': 0, 'page': page, 'per_page': per_page}
```

### Index Usage
```sql
-- Ensure proper indexes for common queries
CREATE INDEX idx_targets_platform ON targets(platform);
CREATE INDEX idx_job_executions_status ON job_executions(status);
CREATE INDEX idx_job_executions_started_at ON job_executions(started_at DESC);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
```

## 🔄 Migration Patterns

### Schema Migrations
```sql
-- database/migrations/001_add_target_groups.sql
BEGIN;

-- Create target_groups table
CREATE TABLE target_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add group_id to targets table
ALTER TABLE targets ADD COLUMN group_id INTEGER REFERENCES target_groups(id);

-- Create junction table for many-to-many relationships
CREATE TABLE target_group_memberships (
    target_id INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES target_groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (target_id, group_id)
);

-- Create indexes
CREATE INDEX idx_targets_group_id ON targets(group_id);
CREATE INDEX idx_target_group_memberships_target_id ON target_group_memberships(target_id);
CREATE INDEX idx_target_group_memberships_group_id ON target_group_memberships(group_id);

COMMIT;
```

### Data Migration
```python
def migrate_existing_data():
    """Migrate existing data to new schema"""
    try:
        with get_db_cursor() as cursor:
            # Example: Update existing records
            cursor.execute("""
                UPDATE targets 
                SET group_id = 1 
                WHERE group_id IS NULL AND platform = 'windows'
            """)
            
            cursor.execute("""
                UPDATE targets 
                SET group_id = 2 
                WHERE group_id IS NULL AND platform = 'linux'
            """)
            
            logger.info("Data migration completed successfully")
            return True
    except Exception as e:
        logger.error(f"Data migration failed: {e}")
        return False
```

## 🧪 Testing Database Operations

### Test Database Setup
```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_db_cursor():
    """Mock database cursor for testing"""
    cursor = MagicMock()
    cursor.fetchone.return_value = {
        'id': 1, 
        'name': 'test-target', 
        'host': '192.168.1.100'
    }
    cursor.fetchall.return_value = [
        {'id': 1, 'name': 'target1'},
        {'id': 2, 'name': 'target2'}
    ]
    return cursor

@pytest.fixture
def mock_get_db_cursor(mock_db_cursor):
    """Mock get_db_cursor function"""
    with patch('shared.database.get_db_cursor') as mock_func:
        mock_func.return_value.__enter__.return_value = mock_db_cursor
        yield mock_func

def test_get_target_by_id(mock_get_db_cursor, mock_db_cursor):
    """Test getting target by ID"""
    from your_module import get_target_by_id
    
    result = get_target_by_id(1)
    
    assert result is not None
    assert result['id'] == 1
    assert result['name'] == 'test-target'
    mock_db_cursor.execute.assert_called_once_with(
        "SELECT * FROM targets WHERE id = %s", (1,)
    )
```

## 📈 Performance Monitoring

### Query Performance
```python
import time
from shared.logging import get_logger

logger = get_logger(__name__)

def log_slow_queries(func):
    """Decorator to log slow database queries"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log queries taking more than 1 second
            logger.warning(f"Slow query in {func.__name__}: {execution_time:.2f}s")
        
        return result
    return wrapper

@log_slow_queries
def get_complex_report() -> List[Dict[str, Any]]:
    """Complex report query with performance monitoring"""
    # Implementation here
    pass
```

### Connection Pool Health
```python
def monitor_database_health() -> Dict[str, Any]:
    """Monitor database connection pool health"""
    try:
        health = check_database_health()
        
        # Log performance metrics
        if health.get('response_time_ms', 0) > 100:
            logger.warning(f"High database response time: {health['response_time_ms']}ms")
        
        return health
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {'status': 'unhealthy', 'error': str(e)}
```

## 🚨 Common Pitfalls to Avoid

### Transaction Management
```python
# ❌ WRONG: Manual transaction management
def wrong_transaction_handling():
    cursor = get_db_cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute("INSERT INTO users ...")
        cursor.execute("COMMIT")
    except:
        cursor.execute("ROLLBACK")

# ✅ CORRECT: Use context manager
def correct_transaction_handling():
    with get_db_cursor() as cursor:  # Automatic transaction management
        cursor.execute("INSERT INTO users ...")
```

### Resource Cleanup
```python
# ✅ CORRECT: Context manager handles cleanup
def proper_resource_management():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()
    # Cursor and connection automatically cleaned up

# ❌ WRONG: Manual resource management
def improper_resource_management():
    cursor = get_db_cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
    # Connection not properly closed
```

---

**Follow these database patterns to ensure consistent, secure, and performant data operations across all OpsConductor services.**
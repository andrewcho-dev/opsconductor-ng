# OpsConductor Developers Guide

This comprehensive guide provides all the detailed information developers need to work effectively with the OpsConductor system, including architecture patterns, utility modules, APIs, endpoints, functions, and development standards.

## 🚨 CRITICAL: Required Reading

**BEFORE starting any development work on OpsConductor, you MUST read and follow this guide.**

This is not optional - it contains essential information that prevents code duplication and ensures consistency across the project.

## 📋 Pre-Development Checklist

Before writing any new code, you MUST:

1. ✅ **Read this complete Developer Guide**
2. ✅ **Check for existing utility modules** with `utility_` prefix
3. ✅ **Review shared modules** in `/shared/` directory
4. ✅ **Search other services** for similar functionality
5. ✅ **Use custom error classes** instead of `HTTPException`

## 🏗️ Service Architecture Pattern

### Standard Service Structure
Every Python service follows this consistent pattern:

```python
#!/usr/bin/env python3

import sys
sys.path.append('/home/opsconductor')

from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
import os
import logging

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, setup_error_handlers
from shared.auth import get_current_user, require_admin, verify_token
from shared.utils import get_service_client

# Setup structured logging
setup_service_logging("service-name", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("service-name")

app = FastAPI(
    title="Service Name",
    version="1.0.0",
    description="Service description"
)

# Add standard middleware and error handlers
add_standard_middleware(app, "service-name", version="1.0.0")
setup_error_handlers(app)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Standard health check endpoint"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        service="service-name",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

@app.on_event("startup")
async def startup_event():
    """Standard startup event"""
    log_startup("service-name", "1.0.0", 3001)

@app.on_event("shutdown")
async def shutdown_event():
    """Standard shutdown event"""
    log_shutdown("service-name")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
```

## 🔧 Utility Modules System

**ALWAYS check for existing utility modules before implementing new functionality:**

### Available Utility Modules

#### Notification Service Utilities
- `utility_email_sender.py` - Email notification functionality
- `utility_webhook_sender.py` - Slack, Teams, and generic webhooks
- `utility_template_renderer.py` - Jinja2 template rendering
- `utility_user_preferences.py` - User preference management
- `utility_notification_processor.py` - Core notification processing

#### Executor Service Utilities
- `utility_command_builder.py` - Command construction and templating
- `utility_http_executor.py` - HTTP request execution
- `utility_notification_utils.py` - Execution notification helpers
- `utility_sftp_executor.py` - SFTP file transfer operations
- `utility_webhook_executor.py` - Webhook execution

#### Discovery Service Utilities
- `utility_discovery_job.py` - Discovery job management
- `utility_network_range_parser.py` - Network range parsing
- `utility_network_scanner.py` - Network scanning with nmap

#### Shared Utilities (`/shared/`)
- `utility_event_consumer.py` - Event consumption patterns
- `utility_event_publisher.py` - Event publishing patterns
- `utility_message_queue.py` - Message queue operations
- `utility_service_auth.py` - Service-to-service authentication
- `utility_service_clients.py` - HTTP client utilities

### Utility Module Usage Pattern

```python
# Import utility modules
import utility_email_sender as email_utility
import utility_webhook_sender as webhook_utility

# Initialize utilities in main.py
email_utility.set_smtp_config(SMTP_CONFIG)
email_utility.set_db_cursor_func(get_db_cursor)
webhook_utility.set_db_cursor_func(get_db_cursor)

# Use in endpoints
@app.post("/send-notification")
async def send_notification(request: Request) -> Dict[str, Any]:
    await verify_token(request)
    
    success = await email_utility.send_email_notification(
        notification_id=123,
        dest="user@example.com",
        payload={"job_name": "backup", "status": "completed"}
    )
    
    if success:
        return create_success_response("Notification sent")
    else:
        raise DatabaseError("Failed to send notification")
```

### Creating New Utility Modules

#### 1. Naming Convention
- Use `utility_` prefix: `utility_feature_name.py`
- Use descriptive names: `utility_database_backup.py`, `utility_file_processor.py`

#### 2. Module Structure Template
```python
"""
Feature description utility module
Brief description of what this module handles
"""

import logging
from typing import Dict, Any, Optional, List

# Global variables for configuration
CONFIG = {}
db_cursor_func = None

logger = logging.getLogger(__name__)

def set_config(config: Dict[str, Any]) -> None:
    """Set configuration from main module"""
    global CONFIG
    CONFIG.update(config)

def set_db_cursor_func(cursor_func):
    """Set database cursor function from main module"""
    global db_cursor_func
    db_cursor_func = cursor_func

async def main_function(param1: str, param2: Dict[str, Any]) -> bool:
    """Main functionality with proper error handling"""
    try:
        # Implementation here
        logger.info(f"Processing {param1}")
        return True
        
    except Exception as e:
        logger.error(f"Error in main_function: {e}")
        return False

def helper_function(data: Any) -> Optional[Dict[str, Any]]:
    """Helper function with proper typing"""
    try:
        # Implementation here
        return {"result": "success"}
        
    except Exception as e:
        logger.error(f"Error in helper_function: {e}")
        return None
```

## 🔒 Error Handling Standards

### Custom Error Classes
**NEVER use `HTTPException` directly. Always use custom error classes:**

```python
from shared.errors import (
    DatabaseError,        # Database operation failures (500)
    ValidationError,      # Input validation failures (400)
    NotFoundError,        # Resource not found (404)
    AuthError,           # Authentication failures (401)
    PermissionError,     # Authorization failures (403)
    ServiceCommunicationError  # Inter-service communication (503)
)

# Examples
if not user_data.email:
    raise ValidationError("Email is required", "email")

if not user:
    raise NotFoundError("User not found")

try:
    cursor.execute(query, params)
except Exception as e:
    raise DatabaseError(f"Failed to create user: {str(e)}")

try:
    response = requests.get(f"{AUTH_SERVICE_URL}/verify")
except requests.RequestException:
    raise ServiceCommunicationError("auth-service", "Auth service unavailable")
```

### Error Handling in Utility Modules
```python
def utility_function(param: str) -> Optional[Dict[str, Any]]:
    """Utility function with proper error handling"""
    try:
        # Implementation
        return {"result": "success"}
    except Exception as e:
        logger.error(f"Error in utility_function: {e}")
        # Don't raise HTTP errors from utilities
        # Let the calling endpoint decide how to handle
        return None
```

## 🗄️ Database Patterns

### Using Database Cursor in Utilities
```python
def set_db_cursor_func(cursor_func):
    """Set database cursor function from main module"""
    global get_db_cursor
    get_db_cursor = cursor_func

async def database_operation(param: str) -> Optional[Dict[str, Any]]:
    """Database operation with proper error handling"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM table WHERE param = %s", (param,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None
```

### Transaction Management
```python
async def update_operation(data: Dict[str, Any]) -> bool:
    """Update operation with transaction"""
    try:
        with get_db_cursor() as cursor:  # commit=True by default
            cursor.execute("UPDATE table SET field = %s WHERE id = %s", 
                         (data['field'], data['id']))
            return True
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return False
```

## 📚 Shared Modules Reference

### `/shared/database.py`
```python
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool

# Get database cursor with transaction control
with get_db_cursor(commit=True) as cursor:
    cursor.execute("INSERT INTO table VALUES (%s)", (value,))

# Check database health
health = check_database_health()
# Returns: {"status": "healthy", "response_time_ms": 5}

# Cleanup on shutdown
cleanup_database_pool()
```

### `/shared/logging.py`
```python
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown

# Setup structured logging
setup_service_logging("service-name", level="INFO")
logger = get_logger("service-name")

# Log startup/shutdown
log_startup("service-name", "1.0.0", 3001)
log_shutdown("service-name")
```

### `/shared/middleware.py`
```python
from shared.middleware import add_standard_middleware

# Add all standard middleware
add_standard_middleware(app, "service-name", version="1.0.0")
# Includes: CORS, request logging, error handling, security headers
```

### `/shared/models.py`
```python
from shared.models import HealthResponse, HealthCheck, create_success_response

# Create success response
return create_success_response("Operation completed", {"id": 123})

# Health check response
return HealthResponse(
    service="service-name",
    status="healthy",
    version="1.0.0",
    checks=[HealthCheck(name="database", status="healthy")]
)
```

### `/shared/auth.py`
```python
from shared.auth import get_current_user, require_admin, verify_token

# Verify token in endpoint
@app.post("/protected")
async def protected_endpoint(request: Request):
    await verify_token(request)
    # Endpoint logic here

# Get current user
@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

# Require admin role
@app.delete("/admin-only")
async def admin_endpoint(current_user: dict = Depends(require_admin)):
    # Admin-only logic here
```

### `/shared/utils.py`
```python
from shared.utils import utility_render_template, utility_render_file_paths, utility_create_error_result

# Render templates
rendered = utility_render_template(
    "Hello {{ user.name }}, job {{ job.id }} completed",
    {"user": {"name": "John"}, "job": {"id": 123}}
)

# Render file paths
source_path, dest_path = utility_render_file_paths(
    "/tmp/{{ job.id }}/input.txt",
    "/opt/data/{{ user.name }}/output.txt",
    {"job": {"id": 123}, "user": {"name": "john"}}
)

# Create error result
error_result = utility_create_error_result(
    error_message="Operation failed: connection timeout",
    log_message="Database connection failed during user lookup",
    exception=e,
    exit_code=1
)
```

## 📋 Complete API Reference

### Authentication Service (Port 3001)

#### Endpoints
```python
POST /auth/login
# Body: {"username": "admin", "password": "admin123"}
# Response: {"access_token": "jwt_token", "token_type": "bearer"}

POST /auth/logout
# Headers: {"Authorization": "Bearer jwt_token"}
# Response: {"message": "Logged out successfully"}

POST /auth/refresh
# Headers: {"Authorization": "Bearer refresh_token"}
# Response: {"access_token": "new_jwt_token"}

GET /auth/verify
# Headers: {"Authorization": "Bearer jwt_token"}
# Response: {"user_id": 1, "username": "admin", "role": "admin"}
```

### User Service (Port 3002)

#### Endpoints
```python
GET /users
# Query: ?page=1&limit=10&search=admin
# Response: {"users": [...], "total": 5, "page": 1, "limit": 10}

POST /users
# Body: {"username": "newuser", "email": "user@example.com", "password": "password", "role": "operator"}
# Response: {"id": 2, "username": "newuser", "email": "user@example.com", "role": "operator"}

GET /users/{id}
# Response: {"id": 1, "username": "admin", "email": "admin@example.com", "role": "admin"}

PUT /users/{id}
# Body: {"email": "newemail@example.com", "role": "viewer"}
# Response: {"id": 1, "username": "admin", "email": "newemail@example.com", "role": "viewer"}

DELETE /users/{id}
# Response: {"message": "User deleted successfully"}
```

### Credentials Service (Port 3004)

#### Endpoints
```python
GET /credentials
# Response: {"credentials": [{"id": 1, "name": "Windows Admin", "type": "winrm"}]}

POST /credentials
# Body: {"name": "SSH Key", "type": "ssh", "username": "root", "private_key": "-----BEGIN..."}
# Response: {"id": 2, "name": "SSH Key", "type": "ssh"}

GET /credentials/{id}
# Response: {"id": 1, "name": "Windows Admin", "type": "winrm", "username": "administrator"}

PUT /credentials/{id}
# Body: {"name": "Updated Name", "username": "newuser"}
# Response: {"id": 1, "name": "Updated Name", "type": "winrm"}

DELETE /credentials/{id}
# Response: {"message": "Credential deleted successfully"}
```

### Targets Service (Port 3005)

#### Endpoints
```python
GET /targets
# Query: ?group_id=1&os_type=windows
# Response: {"targets": [...], "total": 10}

POST /targets
# Body: {"name": "Web Server", "host": "192.168.1.100", "os_type": "linux", "protocol": "ssh"}
# Response: {"id": 3, "name": "Web Server", "host": "192.168.1.100"}

GET /targets/{id}
# Response: {"id": 1, "name": "Web Server", "host": "192.168.1.100", "status": "online"}

PUT /targets/{id}
# Body: {"name": "Updated Server", "port": 22}
# Response: {"id": 1, "name": "Updated Server", "port": 22}

DELETE /targets/{id}
# Response: {"message": "Target deleted successfully"}

POST /targets/{id}/test
# Response: {"success": true, "message": "Connection successful", "response_time_ms": 150}

# Target Groups
GET /target-groups
# Response: {"groups": [{"id": 1, "name": "Web Servers", "target_count": 5}]}

POST /target-groups
# Body: {"name": "Database Servers", "description": "Production DB servers"}
# Response: {"id": 2, "name": "Database Servers", "description": "Production DB servers"}

POST /target-groups/{group_id}/targets/{target_id}
# Response: {"message": "Target added to group successfully"}

DELETE /target-groups/{group_id}/targets/{target_id}
# Response: {"message": "Target removed from group successfully"}
```

### Jobs Service (Port 3006)

#### Endpoints
```python
GET /jobs
# Query: ?status=active&created_by=1
# Response: {"jobs": [...], "total": 15}

POST /jobs
# Body: {"name": "Backup Job", "description": "Daily backup", "steps": [...]}
# Response: {"id": 4, "name": "Backup Job", "status": "active"}

GET /jobs/{id}
# Response: {"id": 1, "name": "Backup Job", "steps": [...], "created_at": "2025-01-28T10:00:00Z"}

PUT /jobs/{id}
# Body: {"name": "Updated Job", "description": "New description"}
# Response: {"id": 1, "name": "Updated Job", "description": "New description"}

DELETE /jobs/{id}
# Response: {"message": "Job deleted successfully"}

POST /jobs/{id}/run
# Body: {"target_ids": [1, 2, 3], "parameters": {"param1": "value1"}}
# Response: {"job_run_id": 10, "status": "queued", "message": "Job queued for execution"}

GET /job-runs
# Query: ?job_id=1&status=completed&page=1&limit=20
# Response: {"runs": [...], "total": 50, "page": 1, "limit": 20}

GET /job-runs/{id}
# Response: {"id": 10, "job_id": 1, "status": "completed", "steps": [...]}
```

### Executor Service (Port 3007)

#### Endpoints
```python
POST /execute
# Body: {"job_run_id": 10, "target_id": 1, "steps": [...]}
# Response: {"execution_id": "exec_123", "status": "running"}

GET /executions/{id}
# Response: {"id": "exec_123", "status": "completed", "output": "Command output", "exit_code": 0}

POST /execute/winrm
# Body: {"target_id": 1, "command": "Get-Process", "credential_id": 1}
# Response: {"output": "Process list...", "exit_code": 0, "execution_time_ms": 1500}

POST /execute/ssh
# Body: {"target_id": 2, "command": "ls -la", "credential_id": 2}
# Response: {"output": "File listing...", "exit_code": 0, "execution_time_ms": 800}

POST /execute/sftp
# Body: {"target_id": 2, "operation": "upload", "local_path": "/tmp/file.txt", "remote_path": "/opt/file.txt"}
# Response: {"success": true, "bytes_transferred": 1024, "transfer_time_ms": 2000}

POST /execute/webhook
# Body: {"url": "https://api.example.com/webhook", "method": "POST", "payload": {...}}
# Response: {"status_code": 200, "response": {...}, "response_time_ms": 300}
```

### Scheduler Service (Port 3008)

#### Endpoints
```python
GET /schedules
# Response: {"schedules": [{"id": 1, "job_id": 1, "cron": "0 2 * * *", "enabled": true}]}

POST /schedules
# Body: {"job_id": 1, "cron": "0 2 * * *", "timezone": "UTC", "enabled": true}
# Response: {"id": 2, "job_id": 1, "cron": "0 2 * * *", "next_run": "2025-01-29T02:00:00Z"}

GET /schedules/{id}
# Response: {"id": 1, "job_id": 1, "cron": "0 2 * * *", "last_run": "2025-01-28T02:00:00Z"}

PUT /schedules/{id}
# Body: {"cron": "0 3 * * *", "enabled": false}
# Response: {"id": 1, "cron": "0 3 * * *", "enabled": false}

DELETE /schedules/{id}
# Response: {"message": "Schedule deleted successfully"}

POST /schedules/{id}/trigger
# Response: {"job_run_id": 15, "message": "Job triggered successfully"}
```

### Notification Service (Port 3009)

#### Endpoints
```python
GET /api/notification/smtp/settings
# Response: {"smtp_server": "smtp.gmail.com", "smtp_port": 587, "use_tls": true}

POST /api/notification/smtp/settings
# Body: {"smtp_server": "smtp.gmail.com", "smtp_port": 587, "username": "user@gmail.com", "password": "password"}
# Response: {"message": "SMTP settings updated successfully"}

POST /api/notification/smtp/test
# Body: {"to_email": "test@example.com", "subject": "Test", "body": "Test message"}
# Response: {"success": true, "message": "Test email sent successfully"}

GET /notifications
# Query: ?status=pending&channel=email
# Response: {"notifications": [...], "total": 25}

POST /notifications
# Body: {"channel": "email", "destination": "user@example.com", "template_id": 1, "payload": {...}}
# Response: {"id": 100, "status": "queued", "message": "Notification queued"}

GET /notifications/{id}
# Response: {"id": 100, "channel": "email", "status": "sent", "sent_at": "2025-01-28T10:30:00Z"}

# Webhook notifications
POST /api/notification/webhook/slack
# Body: {"webhook_url": "https://hooks.slack.com/...", "payload": {...}}
# Response: {"success": true, "message": "Slack notification sent"}

POST /api/notification/webhook/teams
# Body: {"webhook_url": "https://outlook.office.com/webhook/...", "payload": {...}}
# Response: {"success": true, "message": "Teams notification sent"}
```

### Discovery Service (Port 3010)

#### Endpoints
```python
GET /discovery/jobs
# Response: {"jobs": [{"id": 1, "name": "Network Scan", "status": "completed"}]}

POST /discovery/jobs
# Body: {"name": "Office Network", "network_range": "192.168.1.0/24", "scan_ports": [22, 3389, 5985]}
# Response: {"id": 2, "name": "Office Network", "status": "queued"}

GET /discovery/jobs/{id}
# Response: {"id": 1, "name": "Network Scan", "discovered_targets": 15, "status": "completed"}

POST /discovery/jobs/{id}/start
# Response: {"message": "Discovery job started", "estimated_duration": "5 minutes"}

GET /discovery/jobs/{id}/results
# Response: {"targets": [{"host": "192.168.1.100", "os": "Windows", "services": ["winrm", "rdp"]}]}

POST /discovery/import
# Body: {"discovery_job_id": 1, "target_ids": [1, 2, 3], "default_credential_id": 1}
# Response: {"imported": 3, "skipped": 0, "message": "Targets imported successfully"}

POST /discovery/scan
# Body: {"network_range": "10.0.0.0/24", "ports": [22, 80, 443]}
# Response: {"scan_id": "scan_456", "status": "running", "estimated_completion": "2025-01-28T10:45:00Z"}
```

### Step Libraries Service (Port 3011)

#### Endpoints
```python
GET /libraries
# Response: {"libraries": [{"id": "windows-core", "version": "1.0.0", "steps": 15}]}

GET /libraries/{id}
# Response: {"id": "windows-core", "name": "Windows Core", "steps": [...], "manifest": {...}}

POST /libraries/{id}/install
# Response: {"message": "Library installed successfully", "version": "1.0.0"}

DELETE /libraries/{id}
# Response: {"message": "Library uninstalled successfully"}

GET /libraries/{id}/steps
# Response: {"steps": [{"name": "get_system_info", "description": "Get system information"}]}

POST /libraries/{id}/steps/{step_name}/execute
# Body: {"parameters": {"target_id": 1, "credential_id": 1}}
# Response: {"result": {...}, "execution_time_ms": 1200}

GET /catalog
# Response: {"available_libraries": [{"id": "network-tools", "description": "Network utilities"}]}

POST /catalog/{id}/download
# Response: {"download_url": "https://...", "expires_at": "2025-01-28T11:00:00Z"}
```

## 🧪 Testing Standards

### Unit Testing Pattern
```python
import pytest
from unittest.mock import Mock, patch
import utility_feature_name as feature_utility

@pytest.fixture
def mock_db_cursor():
    """Mock database cursor"""
    cursor = Mock()
    cursor.fetchone.return_value = {"id": 1, "name": "test"}
    cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
    return cursor

@pytest.fixture
def setup_utility(mock_db_cursor):
    """Setup utility with mocked dependencies"""
    feature_utility.set_config({"test": "config"})
    feature_utility.set_db_cursor_func(lambda: mock_db_cursor)
    return feature_utility

def test_main_function(setup_utility):
    """Test main utility function"""
    result = setup_utility.main_function("test_param", {"data": "value"})
    assert result is True

@patch('utility_feature_name.external_api_call')
def test_with_external_dependency(mock_api, setup_utility):
    """Test utility function with external dependencies"""
    mock_api.return_value = {"status": "success"}
    result = setup_utility.function_with_api_call()
    assert result["status"] == "success"
```

### Integration Testing
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user():
    """Test user creation endpoint"""
    response = client.post("/users", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": "operator"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_protected_endpoint():
    """Test protected endpoint with authentication"""
    # First login to get token
    login_response = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    
    # Use token for protected endpoint
    response = client.get("/protected", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
```

## 📝 Documentation Standards

### Module Documentation
```python
"""
Module name utility module

Detailed description of what this module handles, including:
- Main functionality
- Dependencies
- Configuration requirements
- Usage examples

Example:
    import utility_module_name as module_utility
    
    # Initialize
    module_utility.set_config(CONFIG)
    
    # Use
    result = await module_utility.main_function(param)
"""
```

### Function Documentation
```python
async def complex_function(
    param1: str, 
    param2: Dict[str, Any], 
    optional_param: Optional[int] = None
) -> tuple[bool, str]:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2 with expected structure
        optional_param: Description of optional parameter
    
    Returns:
        Tuple of (success_boolean, message_string)
        
    Raises:
        DatabaseError: When database operation fails
        ValidationError: When input validation fails
        
    Example:
        success, message = await complex_function(
            "test", 
            {"key": "value"}, 
            optional_param=123
        )
    """
```

## 🚀 Development Workflow

### Before Writing New Code
1. **Check existing utilities**: Search for `utility_*.py` files in the service
2. **Check other services**: Look for similar functionality in other services
3. **Review shared modules**: Check `/shared/` for common functionality
4. **Plan the utility**: Design the module interface before implementation

### Creating New Features
1. **Design the utility module** with clear interfaces
2. **Implement with proper error handling** and logging
3. **Add comprehensive tests** for the utility
4. **Update main.py** to use the utility
5. **Document the utility** in this guide
6. **Commit and push** changes with descriptive messages

### Code Review Checklist
- [ ] Uses existing utility modules where possible
- [ ] Follows naming conventions (`utility_` prefix)
- [ ] Proper error handling (custom error classes)
- [ ] Comprehensive logging
- [ ] Type hints for all functions
- [ ] Documentation strings
- [ ] Unit tests
- [ ] Integration with main.py

## 🎯 Best Practices

### Code Quality
1. **Always use utility modules** instead of duplicating code
2. **Follow the established patterns** shown in notification service
3. **Test thoroughly** with both unit and integration tests
4. **Document everything** for future developers
5. **Use proper error handling** with custom error classes
6. **Log appropriately** for debugging and monitoring

### Performance
1. **Use async/await** for I/O operations
2. **Implement connection pooling** for database operations
3. **Cache frequently accessed data** where appropriate
4. **Use background workers** for long-running tasks
5. **Monitor performance** with proper metrics

### Security
1. **Validate all inputs** on the server side
2. **Use parameterized queries** to prevent SQL injection
3. **Encrypt sensitive data** at rest and in transit
4. **Implement proper authentication** and authorization
5. **Log security events** for audit purposes

## 🚫 Common Pitfalls to Avoid

- ❌ Using `HTTPException` instead of custom error classes
- ❌ Duplicating functionality that exists in utility modules
- ❌ Not reading this Developer Guide before starting
- ❌ Skipping error handling or logging
- ❌ Not using type hints
- ❌ Creating utilities without proper initialization patterns
- ❌ Not testing utility modules thoroughly
- ❌ Ignoring the shared modules system

## 🎯 Success Criteria

Your code should:
- ✅ Follow established patterns from existing services
- ✅ Use utility modules where appropriate
- ✅ Handle errors with custom error classes
- ✅ Include comprehensive logging
- ✅ Have proper type hints and documentation
- ✅ Be thoroughly tested
- ✅ Follow the architectural patterns described in this guide

---

**OpsConductor prioritizes maintainability, reusability, and consistency. Follow these standards to contribute effectively to the project.**
# OpsConductor Developer Guide

This guide provides comprehensive information for developers working on the OpsConductor system, including architecture patterns, utility modules, and best practices.

## 🏗️ Architecture Overview

OpsConductor follows a microservices architecture with shared utilities and standardized patterns across all services.

### Service Structure
```
service-name/
├── main.py              # FastAPI application entry point
├── models.py            # Pydantic models and schemas
├── database.py          # Database connection and operations
├── auth.py              # Authentication utilities
├── utility_*.py         # Service-specific utility modules
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── README.md           # Service documentation
```

## 🔧 Utility Modules System

**IMPORTANT**: Always check for existing utility modules before implementing new functionality. Use the `utility_` prefix for all utility modules.

### Notification Service Utility Modules

The notification service provides a comprehensive set of utility modules that should be used as reference for other services:

#### 1. `utility_email_sender.py`
**Purpose**: Email notification functionality
```python
import utility_email_sender as email_sender_utility

# Initialize with SMTP config
email_sender_utility.set_smtp_config(SMTP_CONFIG)

# Send email notification
success = await email_sender_utility.send_email_notification(
    notification_id=123,
    dest="user@example.com",
    payload={"job_name": "backup", "status": "completed"},
    template=template_dict  # Optional
)

# Test SMTP connection
success, message = await email_sender_utility.test_smtp_connection(
    smtp_config, 
    "test@example.com"
)
```

#### 2. `utility_webhook_sender.py`
**Purpose**: Webhook notifications (Slack, Teams, generic)
```python
import utility_webhook_sender as webhook_sender_utility

# Send Slack notification
success = await webhook_sender_utility.send_slack_notification(
    notification_id=123,
    webhook_url="https://hooks.slack.com/...",
    payload={"job_name": "backup", "status": "completed"},
    template=template_dict  # Optional
)

# Send Teams notification
success = await webhook_sender_utility.send_teams_notification(
    notification_id=123,
    webhook_url="https://outlook.office.com/webhook/...",
    payload=payload_dict,
    template=template_dict  # Optional
)

# Send generic webhook
success = await webhook_sender_utility.send_webhook_notification(
    notification_id=123,
    webhook_url="https://api.example.com/webhook",
    payload=payload_dict,
    template=template_dict  # Optional
)

# Test webhook connection
success, message = await webhook_sender_utility.test_webhook_connection(
    webhook_url, 
    webhook_type="slack"  # "slack", "teams", or "generic"
)
```

#### 3. `utility_template_renderer.py`
**Purpose**: Jinja2 template rendering
```python
import utility_template_renderer as template_renderer_utility

# Render template
rendered = template_renderer_utility.render_template(
    template_content="Hello {{ name }}, job {{ job_name }} is {{ status }}",
    payload={"name": "John", "job_name": "backup", "status": "completed"}
)

# Validate template
is_valid, message = template_renderer_utility.validate_template(
    template_content="Hello {{ name }}",
    sample_payload={"name": "Test"}
)

# Get template variables
variables = template_renderer_utility.get_template_variables(
    "Hello {{ name }}, your {{ item }} is ready"
)
# Returns: ["name", "item"]
```

#### 4. `utility_user_preferences.py`
**Purpose**: User preferences management
```python
import utility_user_preferences as user_preferences_utility

# Initialize with database cursor function
user_preferences_utility.set_db_cursor_func(get_db_cursor)

# Get user preferences
preferences = await user_preferences_utility.get_user_preferences(user_id=123)

# Update user preferences
updated = await user_preferences_utility.update_user_preferences(
    user_id=123,
    preferences={"email_enabled": True, "notify_on_success": False}
)

# Check if user should be notified
should_notify = user_preferences_utility.should_notify(
    preferences=preferences_dict,
    event_type="job_succeeded"  # "job_started", "job_succeeded", "job_failed"
)

# Get preferences with user email (synchronous)
preferences = user_preferences_utility.get_user_notification_preferences(user_id=123)
```

#### 5. `utility_notification_processor.py`
**Purpose**: Core notification processing and database operations
```python
import utility_notification_processor as notification_processor_utility

# Initialize with database cursor function
notification_processor_utility.set_db_cursor_func(get_db_cursor)

# Process a single notification
success = await notification_processor_utility.process_notification(
    notification_id=123,
    channel="email",  # "email", "slack", "teams", "webhook"
    dest="user@example.com",
    payload={"job_name": "backup", "status": "completed"},
    template_id=456  # Optional
)

# Create notifications for job run
notification_ids = await notification_processor_utility.create_notifications_for_job_run(
    job_run_id=789,
    event_type="job_succeeded",
    payload={"job_name": "backup", "status": "completed"},
    user_id=123  # Optional
)

# Get pending notifications for processing
pending = await notification_processor_utility.get_pending_notifications(limit=50)

# Get notification statistics
stats = await notification_processor_utility.get_notification_stats()
# Returns: {"pending": 5, "failed": 2, "sent_24h": 150}

# Get notification template
template = notification_processor_utility.get_notification_template(
    channel="email",
    event_type="job_succeeded"
)
```

### Creating New Utility Modules

When creating new utility modules, follow these patterns:

#### 1. Naming Convention
- Use `utility_` prefix: `utility_feature_name.py`
- Use descriptive names: `utility_database_backup.py`, `utility_file_processor.py`

#### 2. Module Structure
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

#### 3. Integration in main.py
```python
# Import utility modules
import utility_feature_name as feature_utility

# Initialize utility modules (after configuration is loaded)
feature_utility.set_config(FEATURE_CONFIG)
feature_utility.set_db_cursor_func(get_db_cursor)

# Use in endpoint functions
@app.post("/feature/action")
async def feature_action(request: Request) -> Dict[str, Any]:
    """Feature action using utility module"""
    await verify_token(request)
    
    result = await feature_utility.main_function("param", {"data": "value"})
    if result:
        return create_success_response("Action completed")
    else:
        raise DatabaseError("Action failed")
```

## 🔒 Error Handling Standards

### Custom Error Classes
Always use custom error classes instead of `HTTPException`:

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

## 🧪 Testing Utility Modules

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

## 📚 Additional Resources

### Service-Specific Documentation
- [Notification Service README](notification-service/README.md)
- [Scheduler Service README](scheduler-service/README.md)
- [Service Template](service-template/README.md)

### Shared Modules
- `/shared/database.py` - Database utilities
- `/shared/logging.py` - Logging configuration
- `/shared/middleware.py` - FastAPI middleware
- `/shared/models.py` - Common Pydantic models
- `/shared/errors.py` - Custom error classes
- `/shared/auth.py` - Authentication utilities
- `/shared/utils.py` - Common utility functions (see below)

#### Shared Utility Functions (`/shared/utils.py`)

The shared utilities module provides cross-service functionality that should be used instead of implementing similar logic in individual services.

##### Template Rendering Utilities

**`utility_render_template(template_str: str, context: Dict[str, Any]) -> str`**
- Renders Jinja2 templates with provided context
- Used for command templates, file paths, notification content, etc.
- Handles template errors gracefully with detailed logging

```python
from shared.utils import utility_render_template

# Render a command template
rendered_command = utility_render_template(
    "echo 'Hello {{ user.name }}, job {{ job.id }} completed'",
    {"user": {"name": "John"}, "job": {"id": 123}}
)
```

**`utility_render_file_paths(source_template: str, dest_template: str, context: Dict[str, Any]) -> tuple[str, str]`**
- Renders both source and destination file path templates
- Returns tuple of (rendered_source_path, rendered_dest_path)
- Commonly used in file transfer operations

```python
from shared.utils import utility_render_file_paths

# Render file paths for transfer operations
source_path, dest_path = utility_render_file_paths(
    "/tmp/{{ job.id }}/input.txt",
    "/opt/data/{{ user.name }}/output.txt",
    {"job": {"id": 123}, "user": {"name": "john"}}
)
```

##### Error Handling Utilities

**`utility_create_error_result(error_message: str, log_message: str = None, exception: Exception = None, exit_code: int = 1) -> Dict[str, Any]`**
- Creates standardized error result dictionaries
- Ensures consistent error format across all services
- Handles logging automatically

```python
from shared.utils import utility_create_error_result

# Create standardized error response
try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    return utility_create_error_result(
        error_message="Operation failed: connection timeout",
        log_message="Database connection failed during user lookup",
        exception=e,
        exit_code=1
    )
```

**When to Use Shared Utilities:**
- ✅ Template rendering for commands, file paths, notifications
- ✅ Standardized error responses across services
- ✅ Any functionality that might be reused by multiple services
- ❌ Service-specific business logic
- ❌ Database models or service-specific data structures

### Best Practices
1. **Always use utility modules** instead of duplicating code
2. **Follow the established patterns** shown in notification service
3. **Test thoroughly** with both unit and integration tests
4. **Document everything** for future developers
5. **Use proper error handling** with custom error classes
6. **Log appropriately** for debugging and monitoring

---

**Remember**: The goal is to create reusable, maintainable, and well-documented code that follows established patterns. Always check for existing solutions before implementing new functionality.
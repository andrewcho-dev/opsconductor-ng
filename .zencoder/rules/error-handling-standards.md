---
description: "Error handling standards for OpsConductor - Use custom error classes, not HTTPException"
globs: ["**/main.py", "**/*service*/**.py", "**/utility_*.py"]
alwaysApply: false
---

# Error Handling Standards

## 🚨 CRITICAL: No HTTPException

**NEVER use `HTTPException` directly in new code. Always use custom error classes.**

## ✅ Custom Error Classes

Use these custom error classes from `shared.errors`:

```python
from shared.errors import (
    DatabaseError,        # Database operation failures (500)
    ValidationError,      # Input validation failures (400)
    NotFoundError,        # Resource not found (404)
    AuthError,           # Authentication failures (401)
    PermissionError,     # Authorization failures (403)
    ServiceCommunicationError  # Inter-service communication (503)
)
```

## 📋 Usage Examples

### Input Validation
```python
if not user_data.email:
    raise ValidationError("Email is required", "email")

if not user_data.password or len(user_data.password) < 8:
    raise ValidationError("Password must be at least 8 characters", "password")
```

### Resource Not Found
```python
if not user:
    raise NotFoundError("User not found")

if not job:
    raise NotFoundError(f"Job with ID {job_id} not found")
```

### Database Operations
```python
try:
    cursor.execute(query, params)
except Exception as e:
    raise DatabaseError(f"Failed to create user: {str(e)}")
```

### Service Communication
```python
try:
    response = requests.get(f"{AUTH_SERVICE_URL}/verify")
    response.raise_for_status()
except requests.RequestException:
    raise ServiceCommunicationError("auth-service", "Auth service unavailable")
```

### Authentication
```python
if not token:
    raise AuthError("Authentication token required")

if not verify_token(token):
    raise AuthError("Invalid or expired token")
```

### Authorization
```python
if not user.is_admin:
    raise PermissionError("Admin access required")

if user.id != resource.owner_id:
    raise PermissionError("Access denied to this resource")
```

## 🔧 Error Handling in Utility Modules

Utility modules should NOT raise HTTP errors. Instead:

```python
def utility_function(param: str) -> Optional[Dict[str, Any]]:
    """Utility function with proper error handling"""
    try:
        # Implementation
        return {"result": "success"}
    except Exception as e:
        logger.error(f"Error in utility_function: {e}")
        # Return None/False, let endpoint decide how to handle
        return None

async def database_utility(data: Dict[str, Any]) -> bool:
    """Database utility with proper error handling"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("INSERT INTO table VALUES (%s)", (data,))
            return True
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        # Return False, let endpoint raise appropriate error
        return False
```

## 🎯 Endpoint Error Handling

Endpoints should use utility results to raise appropriate errors:

```python
@app.post("/users")
async def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """Create user with proper error handling"""
    # Validate input
    if not user_data.email:
        raise ValidationError("Email is required", "email")
    
    # Use utility
    result = await user_utility.create_user(user_data.dict())
    
    # Handle utility result
    if not result:
        raise DatabaseError("Failed to create user")
    
    return create_success_response("User created", result)
```

## 🚫 What NOT to Do

```python
# ❌ DON'T use HTTPException
from fastapi import HTTPException
raise HTTPException(status_code=400, detail="Bad request")

# ❌ DON'T raise HTTP errors from utilities
def utility_function():
    raise HTTPException(status_code=500, detail="Error")

# ❌ DON'T use generic exceptions for HTTP responses
raise Exception("Something went wrong")
```

## ✅ What TO Do

```python
# ✅ Use custom error classes
from shared.errors import ValidationError, DatabaseError
raise ValidationError("Email is required", "email")

# ✅ Let utilities return success/failure
def utility_function():
    try:
        # Implementation
        return True
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

# ✅ Handle utility results in endpoints
result = utility_function()
if not result:
    raise DatabaseError("Operation failed")
```

## 📊 Error Response Format

All custom errors automatically format responses as:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Email is required",
    "field": "email",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## 🔍 Migration from HTTPException

If you find existing `HTTPException` usage:
1. **Identify the error type** (validation, not found, etc.)
2. **Replace with appropriate custom error class**
3. **Update error message** to be more descriptive
4. **Test the change** to ensure proper response format

## 📝 Logging Best Practices

```python
import logging
logger = logging.getLogger(__name__)

try:
    # Operation
    pass
except Exception as e:
    # Log the full error for debugging
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Raise appropriate custom error
    raise DatabaseError("Failed to process request")
```

---

**Remember: Custom error classes provide better error handling, consistent responses, and improved debugging capabilities.**
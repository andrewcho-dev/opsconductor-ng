# OpsConductor Development Guide

## Overview

This guide provides comprehensive development standards and practices for the OpsConductor microservices platform.

## Error Handling Architecture

### Philosophy
OpsConductor uses a standardized error handling system that replaces FastAPI's generic `HTTPException` with domain-specific error classes. This provides better error categorization, consistent HTTP status codes, and improved debugging capabilities.

### Error Class Hierarchy

#### Core Error Classes
All custom errors inherit from `OpsConductorError` base class:

```python
from shared.errors import (
    DatabaseError,              # Database operation failures
    ValidationError,            # Input validation failures  
    NotFoundError,             # Resource not found errors
    AuthError,                 # Authentication failures
    PermissionError,           # Authorization failures
    ServiceCommunicationError  # Inter-service communication failures
)
```

#### HTTP Status Code Mapping
- `DatabaseError` → 500 Internal Server Error
- `ValidationError` → 400 Bad Request
- `NotFoundError` → 404 Not Found
- `AuthError` → 401 Unauthorized
- `PermissionError` → 403 Forbidden
- `ServiceCommunicationError` → 503 Service Unavailable

### Usage Patterns

#### 1. Input Validation
```python
@app.post("/users")
async def create_user(user_data: UserCreate):
    # Field-specific validation
    if not user_data.email:
        raise ValidationError("Email is required", "email")
    
    # Business logic validation
    if len(user_data.password) < 8:
        raise ValidationError("Password must be at least 8 characters", "password")
    
    # Multiple field validation
    if user_data.password != user_data.confirm_password:
        raise ValidationError("Passwords do not match", ["password", "confirm_password"])
```

#### 2. Resource Not Found
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise NotFoundError("User not found")
        
        return user
```

#### 3. Database Operations
```python
@app.post("/users")
async def create_user(user_data: UserCreate):
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s) RETURNING id",
                (user_data.email, hashed_password)
            )
            user_id = cursor.fetchone()["id"]
            return {"id": user_id}
            
    except psycopg2.IntegrityError as e:
        if "unique constraint" in str(e):
            raise ValidationError("Email already exists", "email")
        raise DatabaseError(f"Failed to create user: {str(e)}")
    except Exception as e:
        raise DatabaseError(f"Database operation failed: {str(e)}")
```

#### 4. Authentication & Authorization
```python
def verify_token(credentials: HTTPAuthorizationCredentials):
    try:
        # Token verification logic
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")

def require_admin_role(current_user: dict):
    if current_user.get("role") != "admin":
        raise PermissionError("Admin role required")
```

#### 5. Service Communication
```python
def call_auth_service(token: str):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=10)
        
        if response.status_code == 401:
            raise AuthError("Invalid token")
        elif response.status_code != 200:
            raise ServiceCommunicationError("auth-service", f"Auth service returned {response.status_code}")
            
        return response.json()
        
    except requests.Timeout:
        raise ServiceCommunicationError("auth-service", "Auth service timeout")
    except requests.ConnectionError:
        raise ServiceCommunicationError("auth-service", "Auth service unavailable")
    except requests.RequestException as e:
        raise ServiceCommunicationError("auth-service", f"Auth service error: {str(e)}")
```

### Global Exception Handling

All services automatically configure global exception handlers via the shared middleware:

```python
from shared.middleware import add_standard_middleware
from shared.errors import setup_error_handlers

app = FastAPI(title="My Service")

# This automatically sets up error handlers
add_standard_middleware(app, "my-service", "1.0.0")
```

### Migration Status

✅ **Complete**: All 129 `HTTPException` instances across all services have been migrated to standardized error classes.

### Best Practices

#### DO ✅
- Use specific error classes for different error types
- Provide meaningful error messages
- Include field context for validation errors
- Log errors with appropriate detail level
- Use consistent error handling patterns

#### DON'T ❌
- Use `HTTPException` directly (deprecated)
- Catch generic `Exception` without re-raising as appropriate error type
- Return error details that could expose sensitive information
- Use generic error messages without context

## Database Access Patterns

### Connection Management
All services use the shared database module with connection pooling:

```python
from shared.database import get_db_cursor, get_db_connection

# For simple queries
with get_db_cursor() as cursor:
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()

# For transactions
with get_db_connection() as conn:
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users ...")
        cursor.execute("INSERT INTO user_profiles ...")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

### Transaction Handling
- Use `get_db_cursor(commit=True)` for single operations (default)
- Use `get_db_cursor(commit=False)` for read-only operations
- Use `get_db_connection()` for multi-statement transactions

## Service Architecture Standards

### Service Structure
```
service-name/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── README.md           # Service documentation
└── tests/              # Service tests
```

### Standard Imports
```python
import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel

# Shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.errors import (
    DatabaseError, ValidationError, NotFoundError, 
    AuthError, PermissionError, ServiceCommunicationError
)
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, create_success_response
from shared.logging import setup_service_logging, get_logger
```

### Service Initialization
```python
# Service configuration
SERVICE_NAME = "my-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("PORT", "3000"))

# Initialize logging
setup_service_logging(SERVICE_NAME, os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=f"OpsConductor {SERVICE_NAME.title()}",
    version=SERVICE_VERSION,
    description="Service description"
)

# Add standard middleware (includes error handlers)
add_standard_middleware(app, SERVICE_NAME, SERVICE_VERSION)
```

## Testing Standards

### Error Handling Tests
```python
import pytest
from fastapi.testclient import TestClient
from shared.errors import ValidationError, NotFoundError

def test_validation_error_response():
    response = client.post("/users", json={"email": ""})
    assert response.status_code == 400
    assert "Email is required" in response.json()["detail"]

def test_not_found_error_response():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
```

## Deployment Considerations

### Health Checks
All services implement standardized health checks:

```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        checks=[
            HealthCheck(name="database", status="healthy"),
            HealthCheck(name="external_service", status="healthy")
        ]
    )
```

### Graceful Shutdown
```python
import signal
import sys

def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    cleanup_database_pool()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

This development guide ensures consistency across all OpsConductor services and provides clear patterns for common development tasks.
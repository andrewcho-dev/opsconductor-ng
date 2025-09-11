# Service Templates

This directory contains template modules for creating self-contained microservices that don't depend on shared modules.

## Templates Available

- **database.py** - Database connection pooling and utilities
- **errors.py** - Standardized error handling and HTTP exceptions
- **auth.py** - Authentication utilities for nginx header-based auth
- **models.py** - Common Pydantic models and response helpers
- **logging_config.py** - Structured logging configuration
- **middleware.py** - Standard FastAPI middleware setup

## Usage

1. Copy the template files you need to your service directory
2. Update imports in your main.py to use local modules instead of shared
3. Customize the templates as needed for your specific service

## Migration Example

**Before (using shared modules):**
```python
from shared.database import get_db_cursor
from shared.errors import DatabaseError
from shared.auth import get_user_from_headers
```

**After (using service templates):**
```python
from .database import get_db_cursor
from .errors import DatabaseError
from .auth import get_user_from_headers
```

## Customization

Each template is designed to be:
- **Self-contained** - No dependencies on shared modules
- **Customizable** - Modify as needed for your service
- **Consistent** - Maintains the same API as shared modules
- **Lightweight** - Only includes what's needed

## Service Migration Order

Recommended migration order:
1. auth-service (foundational)
2. user-service, credentials-service (simple CRUD)
3. targets-service, notification-service (moderate complexity)
4. discovery-service, step-libraries-service (moderate complexity)
5. jobs-service, executor-service (complex, many dependencies)
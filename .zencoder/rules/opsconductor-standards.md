---
description: "OpsConductor development standards and architectural patterns"
alwaysApply: true
---

# OpsConductor Development Standards

## 🏗️ Architecture Overview

OpsConductor is a microservices-based Windows management system with:
- **8 independent services** with clear separation of concerns
- **Shared utility modules** to prevent code duplication
- **Standardized error handling** with custom error classes
- **PostgreSQL database** with shared connection patterns
- **FastAPI framework** for all backend services
- **React TypeScript** frontend with responsive design

## 📁 Project Structure

```
opsconductor/
├── shared/                 # Shared modules across services
│   ├── database.py        # Database utilities
│   ├── errors.py          # Custom error classes
│   ├── auth.py            # Authentication utilities
│   └── ...
├── [service-name]/        # Individual microservices
│   ├── main.py           # FastAPI application
│   ├── utility_*.py      # Service-specific utilities
│   ├── models.py         # Pydantic models
│   └── ...
├── DEVELOPER_GUIDE.md    # Essential development documentation
└── README.md             # Project overview
```

## 🔧 Service Architecture Pattern

Each service follows this standard structure:

```python
# main.py structure
import utility_module as module_utility

# Configuration
CONFIG = {...}

# Initialize utilities
module_utility.set_config(CONFIG)
module_utility.set_db_cursor_func(get_db_cursor)

# FastAPI endpoints
@app.post("/endpoint")
async def endpoint_function(request: Request) -> Dict[str, Any]:
    await verify_token(request)
    result = await module_utility.function(params)
    if result:
        return create_success_response("Success", result)
    else:
        raise DatabaseError("Operation failed")
```

## 🛠️ Development Principles

### 1. Reusability First
- **Check existing utilities** before writing new code
- **Use shared modules** from `/shared/` directory
- **Create utility modules** with `utility_` prefix for reusable functionality

### 2. Consistent Error Handling
- **Use custom error classes** from `shared.errors`
- **Never use HTTPException** directly
- **Log errors appropriately** with proper context

### 3. Database Patterns
- **Use shared database utilities** from `shared.database`
- **Handle transactions properly** with context managers
- **Include proper error handling** for all database operations

### 4. Authentication & Authorization
- **Use shared auth utilities** from `shared.auth`
- **Verify tokens** on protected endpoints
- **Handle auth errors** with proper error classes

## 📚 Required Reading

Before any development work:
1. **[Developer Guide](DEVELOPER_GUIDE.md)** - Complete development documentation
2. **[README.md](README.md)** - Project overview and setup
3. **Service-specific READMEs** - Individual service documentation

## 🔍 Code Quality Standards

### Type Hints
```python
from typing import Dict, Any, Optional, List

async def function(param: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Function with proper type hints"""
    pass
```

### Documentation
```python
def function(param: str) -> bool:
    """
    Brief description of function.
    
    Args:
        param: Description of parameter
        
    Returns:
        Boolean indicating success
        
    Raises:
        DatabaseError: When database operation fails
    """
```

### Error Handling
```python
try:
    result = operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise DatabaseError("Failed to process request")
```

## 🧪 Testing Standards

- **Unit tests** for all utility modules
- **Integration tests** for API endpoints
- **Mock external dependencies** appropriately
- **Test error conditions** and edge cases

## 📦 Service Dependencies

### Core Services
- **auth-service** (3001) - JWT authentication
- **user-service** (3002) - User management
- **credentials-service** (3004) - Secure credential storage
- **targets-service** (3005) - Windows target management
- **jobs-service** (3006) - Job definition
- **executor-service** (3007) - Job execution
- **scheduler-service** (3008) - Job scheduling
- **notification-service** (3009) - Multi-channel notifications

### Infrastructure
- **PostgreSQL** (5432) - Primary database
- **nginx** (8080/8443) - Reverse proxy and SSL

## 🔄 Development Workflow

1. **Plan** - Check Developer Guide and existing solutions
2. **Design** - Follow established patterns
3. **Implement** - Use utility modules and proper error handling
4. **Test** - Comprehensive testing with mocks
5. **Document** - Update relevant documentation
6. **Review** - Ensure compliance with standards

## 🚨 Common Pitfalls to Avoid

- ❌ Using `HTTPException` instead of custom error classes
- ❌ Duplicating functionality that exists in utility modules
- ❌ Not reading the Developer Guide before starting
- ❌ Skipping error handling or logging
- ❌ Not using type hints
- ❌ Creating utilities without proper initialization patterns

## 🎯 Success Criteria

Your code should:
- ✅ Follow established patterns from existing services
- ✅ Use utility modules where appropriate
- ✅ Handle errors with custom error classes
- ✅ Include comprehensive logging
- ✅ Have proper type hints and documentation
- ✅ Be thoroughly tested

---

**OpsConductor prioritizes maintainability, reusability, and consistency. Follow these standards to contribute effectively to the project.**
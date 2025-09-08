---
description: "OpsConductor development standards and architectural patterns"
alwaysApply: true
---

# OpsConductor Development Standards

## 🏗️ Architecture Overview

OpsConductor is a comprehensive microservices-based automation platform with:
- **10 independent microservices** with clear separation of concerns
- **Shared utility modules** to prevent code duplication and ensure consistency
- **Standardized error handling** with custom error classes
- **PostgreSQL 16 database** with shared connection patterns and comprehensive schema
- **FastAPI framework** for all backend services with structured logging
- **React TypeScript** frontend with responsive design and advanced UI features
- **RabbitMQ message queue** for asynchronous job execution
- **Multi-platform support** for Windows (WinRM) and Linux (SSH) automation
- **Enterprise security** with AES-GCM encryption and JWT authentication

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
├── DEVELOPERS_GUIDE.md   # Essential development documentation
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
1. **[Developers Guide](DEVELOPERS_GUIDE.md)** - Complete development documentation
2. **[Implementation Plan](implementation_plan.md)** - Current project status and roadmap
3. **[README.md](README.md)** - Project overview and setup
4. **Service-specific READMEs** - Individual service documentation

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
- **auth-service** (3001) - JWT authentication and authorization
- **user-service** (3002) - User management and profiles
- **credentials-service** (3004) - Secure credential storage with AES-GCM encryption
- **targets-service** (3005) - Windows/Linux target management with groups
- **jobs-service** (3006) - Job definition and management
- **executor-service** (3007) - Job execution via WinRM/SSH with file operations
- **scheduler-service** (3008) - Cron-based job scheduling with timezone support
- **notification-service** (3009) - Multi-channel notifications (Email, Slack, Teams, Webhooks)
- **discovery-service** (3010) - Network scanning and automated target discovery
- **step-libraries-service** (3011) - Reusable automation step libraries

### Infrastructure
- **PostgreSQL 16** (5432) - Primary database with comprehensive schema
- **RabbitMQ** (5672/15672) - Message queue for job execution
- **nginx** (80/443) - Reverse proxy and SSL termination

## 🔄 Development Workflow

1. **Plan** - Check Developers Guide, Implementation Plan, and existing solutions
2. **Design** - Follow established patterns
3. **Implement** - Use utility modules and proper error handling
4. **Test** - Comprehensive testing with mocks
5. **Document** - Update relevant documentation
6. **Review** - Ensure compliance with standards

## 🚨 Common Pitfalls to Avoid

- ❌ Using `HTTPException` instead of custom error classes
- ❌ Duplicating functionality that exists in utility modules
- ❌ Not reading the Developers Guide and Implementation Plan before starting
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
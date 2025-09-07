# OpsConductor Microservices Architecture

## Overview

OpsConductor is a comprehensive job orchestration and automation platform built using a microservices architecture. The system consists of multiple specialized services that work together to provide job scheduling, execution, target management, user authentication, and more.

## Shared Modules Architecture

### Core Philosophy
All Python services in OpsConductor follow a unified architecture pattern using shared modules to ensure consistency, maintainability, and code reuse across the entire system.

### Shared Module Structure (`/shared/`)

#### 1. **Database Module** (`shared/database.py`)
- **Connection Pooling**: Centralized PostgreSQL connection management with automatic pooling
- **Health Monitoring**: Database connectivity health checks with response time metrics
- **Transaction Management**: Consistent transaction handling across all services
- **Key Functions**:
  - `get_db_cursor()` - Get database cursor with automatic connection management
  - `check_database_health()` - Health check with response time metrics
  - `cleanup_database_pool()` - Proper connection cleanup on shutdown

#### 2. **Logging Module** (`shared/logging.py`)
- **Structured Logging**: JSON-formatted logs with consistent fields across all services
- **Service Context**: Automatic service name, version, and request ID injection
- **Log Levels**: Configurable logging levels via environment variables
- **Key Functions**:
  - `setup_service_logging(service_name, level)` - Initialize structured logging
  - `get_logger(name)` - Get configured logger instance
  - `log_startup(service, version, port)` - Standardized startup logging
  - `log_shutdown(service)` - Standardized shutdown logging

#### 3. **Middleware Module** (`shared/middleware.py`)
- **CORS Handling**: Standardized CORS configuration for all services
- **Request Logging**: Automatic request/response logging with timing
- **Error Handling**: Global exception handling with proper error responses
- **Security Headers**: Standard security headers applied to all responses
- **Key Functions**:
  - `add_standard_middleware(app, service_name, version)` - Apply all standard middleware

#### 4. **Models Module** (`shared/models.py`)
- **Response Models**: Standardized Pydantic models for consistent API responses
- **Health Check Models**: Unified health check response format
- **Pagination Models**: Consistent pagination across all services
- **Key Models**:
  - `HealthResponse` - Standard health check response
  - `HealthCheck` - Individual health check component
  - `PaginatedResponse` - Paginated list responses
  - `create_success_response()` - Helper for success responses

#### 5. **Error Handling Module** (`shared/errors.py`)
- **Standardized Exception Classes**: Complete replacement of HTTPException with domain-specific errors
- **Consistent HTTP Status Mapping**: Automatic mapping of custom exceptions to appropriate HTTP status codes
- **Rich Error Context**: Detailed error information with field-level validation context
- **Global Exception Handler**: Centralized error handling with proper logging and response formatting
- **Key Classes**:
  - `DatabaseError` - Database operation failures (500 status)
  - `ValidationError` - Input validation failures with field context (400 status)
  - `NotFoundError` - Resource not found errors (404 status)
  - `AuthError` - Authentication failures (401 status)
  - `PermissionError` - Authorization failures (403 status)
  - `ServiceCommunicationError` - Inter-service communication failures (503 status)
- **Key Functions**:
  - `setup_error_handlers(app)` - Configure global exception handlers
  - `handle_database_error()` - Centralized database error handling
- **Migration Status**: All 129 HTTPException instances across services have been standardized

#### 6. **Authentication Module** (`shared/auth.py`)
- **JWT Token Validation**: Centralized token verification
- **Role-Based Access Control**: Consistent permission checking
- **Service-to-Service Auth**: Internal service authentication
- **Key Functions**:
  - `get_current_user()` - Extract and validate user from JWT
  - `require_admin()` - Admin role requirement decorator
  - `verify_service_token()` - Internal service authentication

#### 7. **Utilities Module** (`shared/utils.py`)
- **HTTP Client**: Configured HTTP client for service-to-service communication
- **Common Helpers**: Shared utility functions used across services
- **Configuration**: Environment variable handling and defaults
- **Key Functions**:
  - `get_service_client()` - Configured HTTP client for internal calls
  - `validate_email()` - Email validation utility
  - `generate_secure_token()` - Secure token generation

## Service Architecture Pattern

### Standard Service Structure
Every Python service follows this consistent pattern:

```python
#!/usr/bin/env python3

import sys
sys.path.append('/home/opsconductor')

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError
from shared.auth import get_current_user, require_admin
from shared.utils import get_service_client

# Setup structured logging
setup_service_logging("service-name", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("service-name")

app = FastAPI(
    title="Service Name",
    version="1.0.0",
    description="Service description"
)

# Add standard middleware
add_standard_middleware(app, "service-name", version="1.0.0")

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
    log_startup("service-name", "1.0.0", port)

@app.on_event("shutdown")
async def shutdown_event():
    """Standard shutdown event"""
    log_shutdown("service-name")
    cleanup_database_pool()
```

## Microservices Overview

### 1. **Authentication Service** (`auth-service:3001`)
- **Purpose**: User authentication, JWT token management, session handling
- **Key Features**: Login/logout, token validation, password reset, session management
- **Database Tables**: `users`, `user_sessions`, `password_reset_tokens`
- **Special Features**: Custom `AuthError` exception class for authentication failures

### 2. **User Service** (`user-service:3002`)
- **Purpose**: User management, profile operations, user administration
- **Key Features**: User CRUD operations, profile management, role assignment
- **Database Tables**: `users`, `user_profiles`, `user_roles`
- **Special Features**: Comprehensive user validation and role-based access control

### 3. **Credentials Service** (`credentials-service:3004`)
- **Purpose**: Secure credential storage and management with encryption
- **Key Features**: Encrypted credential storage, credential sharing, access control
- **Database Tables**: `credentials`, `credential_access_logs`
- **Special Features**: AES encryption for sensitive data, audit logging

### 4. **Notification Service** (`notification-service:3009`)
- **Purpose**: Multi-channel notification delivery (email, Slack, webhooks)
- **Key Features**: Template-based notifications, delivery tracking, retry logic
- **Database Tables**: `notification_templates`, `notification_logs`, `notification_channels`
- **Special Features**: Background worker for async delivery, health monitoring of worker status

### 5. **Jobs Service** (`jobs-service:3005`)
- **Purpose**: Job definition, management, and workflow orchestration
- **Key Features**: Visual job builder, step management, job templates, execution history
- **Database Tables**: `jobs`, `job_steps`, `job_runs`, `job_run_steps`, `job_templates`
- **Special Features**: Complex job workflow management, step dependency resolution

### 6. **Targets Service** (`targets-service:3003`)
- **Purpose**: Target system management and organization
- **Key Features**: Target CRUD, grouping, credential assignment, connection testing
- **Database Tables**: `targets`, `target_groups`, `target_group_memberships`
- **Special Features**: Multi-protocol support (WinRM, SSH, RDP), connection validation

### 7. **Scheduler Service** (`scheduler-service:3008`)
- **Purpose**: Cron-based job scheduling and execution triggering
- **Key Features**: Cron expression parsing, job queuing, schedule management
- **Database Tables**: `job_schedules`, `schedule_executions`
- **Special Features**: Background scheduler worker, croniter integration, health monitoring of scheduler status

### 8. **Executor Service** (`executor-service:3007`)
- **Purpose**: Job execution engine with multi-protocol support
- **Key Features**: WinRM/SSH execution, step processing, result collection, webhook delivery
- **Database Tables**: `job_run_steps`, `execution_logs`, `winrm_executions`, `ssh_executions`, `webhook_executions`
- **Special Features**: Background execution worker, multi-protocol support, comprehensive execution logging

### 9. **Discovery Service** (`discovery-service:3010`)
- **Purpose**: Automated network discovery and target identification
- **Key Features**: Network scanning, OS detection, service discovery, target import
- **Database Tables**: `discovery_jobs`, `discovered_targets`
- **Special Features**: Nmap integration, automated target classification, bulk import capabilities

### 10. **Step Libraries Service** (`step-libraries-service:3011`)
- **Purpose**: Modular step library management for the visual job builder
- **Key Features**: Dynamic library installation, version management, step catalog
- **Database Tables**: `step_libraries`, `library_steps`, `library_versions`
- **Special Features**: Hot-swappable libraries, performance optimization, premium addon support

## Database Architecture

### Connection Management
- **Pooling**: All services use shared connection pooling for optimal performance
- **Health Monitoring**: Continuous database health monitoring with metrics
- **Transaction Safety**: Proper transaction handling with rollback support
- **Connection Cleanup**: Automatic cleanup on service shutdown

### Schema Organization
- **Service Isolation**: Each service manages its own database tables
- **Shared Tables**: Common tables like `users` are accessed by multiple services
- **Migration Management**: Database migrations handled per service
- **Referential Integrity**: Foreign key relationships maintained across service boundaries

## Service Communication

### Internal Communication
- **HTTP/REST**: Services communicate via HTTP REST APIs
- **Authentication**: Service-to-service authentication using shared tokens
- **Circuit Breakers**: Resilient communication with failure handling
- **Load Balancing**: Services can be horizontally scaled

### External APIs
- **Consistent Responses**: All services return standardized response formats
- **Error Handling**: Unified error response structure across all services
- **Documentation**: Auto-generated OpenAPI documentation for all services
- **Versioning**: API versioning support for backward compatibility

## Deployment Architecture

### Container Strategy
- **Docker**: Each service runs in its own Docker container
- **Multi-stage Builds**: Optimized container images with minimal footprint
- **Health Checks**: Container health checks using the `/health` endpoint
- **Resource Limits**: Proper resource allocation and limits

### Service Discovery
- **DNS-based**: Services discover each other via DNS names
- **Environment Variables**: Service URLs configured via environment variables
- **Health Monitoring**: Continuous health monitoring of all services
- **Graceful Degradation**: Services handle dependency failures gracefully

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication using JWT tokens
- **Role-Based Access**: Granular role-based access control
- **Service Authentication**: Secure service-to-service communication
- **Token Validation**: Centralized token validation logic

### Data Security
- **Encryption**: Sensitive data encrypted at rest (credentials service)
- **Secure Communication**: HTTPS/TLS for all service communication
- **Input Validation**: Comprehensive input validation across all services
- **Audit Logging**: Security events logged for compliance

## Monitoring & Observability

### Logging
- **Structured Logging**: JSON-formatted logs with consistent fields
- **Correlation IDs**: Request tracing across service boundaries
- **Log Aggregation**: Centralized log collection and analysis
- **Performance Metrics**: Request timing and performance data

### Health Monitoring
- **Health Endpoints**: Standardized `/health` endpoints on all services
- **Dependency Checks**: Health checks include dependency status
- **Metrics Collection**: Performance and health metrics collection
- **Alerting**: Automated alerting on service health issues

## Development Guidelines

### Code Standards
- **Consistent Patterns**: All services follow the same architectural patterns
- **Shared Modules**: Leverage shared modules for common functionality
- **Error Handling**: Use standardized error classes and handling
- **Documentation**: Comprehensive code documentation and API docs

### Testing Strategy
- **Unit Tests**: Comprehensive unit test coverage for all services
- **Integration Tests**: Service integration testing
- **Health Check Tests**: Automated health check validation
- **Performance Tests**: Load and performance testing

### Deployment Process
- **CI/CD Pipeline**: Automated build, test, and deployment pipeline
- **Rolling Updates**: Zero-downtime deployments with rolling updates
- **Rollback Strategy**: Quick rollback capabilities for failed deployments
- **Environment Promotion**: Consistent promotion through dev/staging/prod

## Migration History

### Shared Modules Migration (Completed)
All 10 Python services have been successfully migrated to use the shared modules architecture:

1. ✅ **auth-service** - Complete with AuthError integration
2. ✅ **user-service** - Complete with comprehensive validation
3. ✅ **credentials-service** - Complete with encryption support
4. ✅ **notification-service** - Complete with worker monitoring
5. ✅ **jobs-service** - Complete with workflow management
6. ✅ **targets-service** - Complete with multi-protocol support
7. ✅ **scheduler-service** - Complete with scheduler worker monitoring
8. ✅ **executor-service** - Complete with execution worker monitoring
9. ✅ **discovery-service** - Complete with discovery capabilities
10. ✅ **step-libraries-service** - Complete with library management

### Benefits Achieved
- **Consistency**: Unified patterns and standards across all services
- **Maintainability**: Reduced code duplication and easier updates
- **Observability**: Structured logging and standardized health checks
- **Error Handling**: Consistent error responses across all services
- **Security**: Centralized authentication and authorization
- **Performance**: Optimized database connection pooling
- **Monitoring**: Standardized health endpoints for all services

## Future Considerations

### Scalability
- **Horizontal Scaling**: Services designed for horizontal scaling
- **Load Balancing**: Load balancer integration for high availability
- **Caching**: Redis integration for performance optimization
- **Database Sharding**: Database scaling strategies for growth

### Technology Evolution
- **Framework Updates**: Regular updates to FastAPI and dependencies
- **Python Versions**: Migration strategy for Python version updates
- **Database Migrations**: Schema evolution and migration strategies
- **Container Optimization**: Continuous container image optimization

This architecture provides a solid foundation for the OpsConductor platform, ensuring scalability, maintainability, and consistency across all services while providing the flexibility to evolve and grow with changing requirements.
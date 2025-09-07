#!/usr/bin/env python3
"""
Shared Error Handling Utilities
Standardized error handling and HTTP exceptions for all services
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import psycopg2
import httpx

logger = logging.getLogger(__name__)

class StandardHTTPException(HTTPException):
    """
    Standardized HTTP exception with consistent error response structure
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.context = context or {}

class DatabaseError(StandardHTTPException):
    """Database-related errors"""
    def __init__(self, detail: str = "Database operation failed", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
            context=context
        )

class ServiceCommunicationError(StandardHTTPException):
    """Inter-service communication errors"""
    def __init__(self, service_name: str, detail: str = None, context: Optional[Dict[str, Any]] = None):
        detail = detail or f"Failed to communicate with {service_name}"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_COMMUNICATION_ERROR",
            context={"service": service_name, **(context or {})}
        )

class ValidationError(StandardHTTPException):
    """Data validation errors"""
    def __init__(self, detail: str, field: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        if field:
            context["field"] = field
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            context=context
        )

class NotFoundError(StandardHTTPException):
    """Resource not found errors"""
    def __init__(self, resource: str, resource_id: Any = None, context: Optional[Dict[str, Any]] = None):
        detail = f"{resource} not found"
        if resource_id:
            detail += f" (ID: {resource_id})"
        
        context = context or {}
        context["resource"] = resource
        if resource_id:
            context["resource_id"] = str(resource_id)
            
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
            context=context
        )

class PermissionError(StandardHTTPException):
    """Permission/authorization errors"""
    def __init__(self, detail: str = "Insufficient permissions", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_ERROR",
            context=context
        )

class AuthError(StandardHTTPException):
    """Authentication errors"""
    def __init__(self, detail: str = "Authentication failed", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTH_ERROR",
            context=context
        )

def handle_database_error(e: Exception, operation: str = "database operation") -> DatabaseError:
    """
    Convert database exceptions to standardized errors
    """
    if isinstance(e, psycopg2.IntegrityError):
        logger.warning(f"Database integrity error during {operation}: {e}")
        return DatabaseError(
            detail="Data integrity constraint violation",
            context={"operation": operation, "error_type": "integrity_error"}
        )
    elif isinstance(e, psycopg2.OperationalError):
        logger.error(f"Database operational error during {operation}: {e}")
        return DatabaseError(
            detail="Database connection or operational error",
            context={"operation": operation, "error_type": "operational_error"}
        )
    elif isinstance(e, psycopg2.ProgrammingError):
        logger.error(f"Database programming error during {operation}: {e}")
        return DatabaseError(
            detail="Database query or programming error",
            context={"operation": operation, "error_type": "programming_error"}
        )
    else:
        logger.error(f"Unexpected database error during {operation}: {e}")
        return DatabaseError(
            detail=f"Database error during {operation}",
            context={"operation": operation, "error_type": "unknown"}
        )

def handle_service_communication_error(
    e: Exception, 
    service_name: str, 
    operation: str = "service call"
) -> ServiceCommunicationError:
    """
    Convert service communication exceptions to standardized errors
    """
    if isinstance(e, httpx.TimeoutException):
        logger.warning(f"Timeout calling {service_name} for {operation}")
        return ServiceCommunicationError(
            service_name,
            detail=f"{service_name} service timeout",
            context={"operation": operation, "error_type": "timeout"}
        )
    elif isinstance(e, httpx.ConnectError):
        logger.error(f"Connection error calling {service_name} for {operation}: {e}")
        return ServiceCommunicationError(
            service_name,
            detail=f"{service_name} service unavailable",
            context={"operation": operation, "error_type": "connection_error"}
        )
    elif isinstance(e, httpx.HTTPStatusError):
        logger.warning(f"HTTP error calling {service_name} for {operation}: {e.response.status_code}")
        return ServiceCommunicationError(
            service_name,
            detail=f"{service_name} service returned error: {e.response.status_code}",
            context={
                "operation": operation, 
                "error_type": "http_error",
                "status_code": e.response.status_code
            }
        )
    else:
        logger.error(f"Unexpected error calling {service_name} for {operation}: {e}")
        return ServiceCommunicationError(
            service_name,
            detail=f"Unexpected error communicating with {service_name}",
            context={"operation": operation, "error_type": "unknown"}
        )

async def standard_exception_handler(request: Request, exc: StandardHTTPException) -> JSONResponse:
    """
    Standard exception handler for consistent error responses
    """
    error_response = {
        "error": {
            "code": exc.error_code or "UNKNOWN_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    }
    
    # Add context if available
    if exc.context:
        error_response["error"]["context"] = exc.context
    
    # Add request information for debugging
    error_response["error"]["path"] = str(request.url.path)
    error_response["error"]["method"] = request.method
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Generic exception handler for unexpected errors
    """
    logger.error(f"Unhandled exception in {request.method} {request.url.path}: {exc}", exc_info=True)
    
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "path": str(request.url.path),
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

def add_error_handlers(app):
    """
    Add standard error handlers to FastAPI app
    """
    app.add_exception_handler(StandardHTTPException, standard_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

# Convenience functions for common error scenarios
def not_found(resource: str, resource_id: Any = None) -> NotFoundError:
    """Quick way to raise not found errors"""
    return NotFoundError(resource, resource_id)

def validation_error(message: str, field: str = None) -> ValidationError:
    """Quick way to raise validation errors"""
    return ValidationError(message, field)

def permission_denied(message: str = "Insufficient permissions") -> PermissionError:
    """Quick way to raise permission errors"""
    return PermissionError(message)

def database_error(operation: str = "database operation") -> DatabaseError:
    """Quick way to raise database errors"""
    return DatabaseError(f"Failed to perform {operation}")

def service_unavailable(service_name: str, operation: str = "service call") -> ServiceCommunicationError:
    """Quick way to raise service communication errors"""
    return ServiceCommunicationError(service_name, context={"operation": operation})
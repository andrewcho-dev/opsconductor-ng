#!/usr/bin/env python3
"""
Shared Logging Utilities
Standardized structured logging configuration for all services
"""

import os
import sys
import json
import logging
import logging.config
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging
    """
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        return json.dumps(log_entry, default=str)

class RequestContextFilter(logging.Filter):
    """
    Filter to add request context to log records
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add default values if not present
        if not hasattr(record, 'request_id'):
            record.request_id = None
        if not hasattr(record, 'user_id'):
            record.user_id = None
        return True

def setup_service_logging(
    service_name: str, 
    level: str = "INFO",
    structured: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Setup standardized logging configuration for a service
    
    Args:
        service_name: Name of the service for log identification
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use structured JSON logging
        log_file: Optional log file path
    """
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if structured:
        # Use structured JSON formatter
        formatter = StructuredFormatter(service_name)
    else:
        # Use standard formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(service_name)
    logger.info(f"{service_name} logging initialized", extra={
        'extra_fields': {
            'log_level': level,
            'structured_logging': structured,
            'log_file': log_file
        }
    })

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with consistent configuration
    """
    return logging.getLogger(name)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses
    """
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}.requests")
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = f"{self.service_name}-{int(time.time() * 1000)}"
        
        # Extract user info if available
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = request.state.user.get('user_id')
        
        # Log request
        start_time = time.time()
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'extra_fields': {
                    'request_id': request_id,
                    'user_id': user_id,
                    'method': request.method,
                    'path': str(request.url.path),
                    'query_params': dict(request.query_params),
                    'client_ip': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent')
                }
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            self.logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'user_id': user_id,
                        'method': request.method,
                        'path': str(request.url.path),
                        'status_code': response.status_code,
                        'duration_ms': round(duration * 1000, 2)
                    }
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'user_id': user_id,
                        'method': request.method,
                        'path': str(request.url.path),
                        'duration_ms': round(duration * 1000, 2),
                        'error': str(e)
                    }
                },
                exc_info=True
            )
            raise

def log_service_call(
    service_name: str,
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """
    Log inter-service communication
    """
    logger = get_logger("service_calls")
    
    if error:
        logger.error(
            f"Service call failed: {method} {service_name}{endpoint}",
            extra={
                'extra_fields': {
                    'service': service_name,
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': status_code,
                    'duration_ms': duration_ms,
                    'error': error
                }
            }
        )
    else:
        logger.info(
            f"Service call completed: {method} {service_name}{endpoint}",
            extra={
                'extra_fields': {
                    'service': service_name,
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': status_code,
                    'duration_ms': duration_ms
                }
            }
        )

def log_database_operation(
    operation: str,
    table: Optional[str] = None,
    duration_ms: Optional[float] = None,
    rows_affected: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Log database operations
    """
    logger = get_logger("database")
    
    extra_fields = {
        'operation': operation,
        'table': table,
        'duration_ms': duration_ms,
        'rows_affected': rows_affected
    }
    
    if error:
        logger.error(
            f"Database operation failed: {operation}",
            extra={'extra_fields': {**extra_fields, 'error': error}}
        )
    else:
        logger.info(
            f"Database operation completed: {operation}",
            extra={'extra_fields': extra_fields}
        )

# Convenience functions for common logging scenarios
def log_startup(service_name: str, version: str, port: int) -> None:
    """Log service startup"""
    logger = get_logger(service_name)
    logger.info(
        f"{service_name} v{version} starting on port {port}",
        extra={
            'extra_fields': {
                'event': 'service_startup',
                'version': version,
                'port': port
            }
        }
    )

def log_shutdown(service_name: str) -> None:
    """Log service shutdown"""
    logger = get_logger(service_name)
    logger.info(
        f"{service_name} shutting down",
        extra={'extra_fields': {'event': 'service_shutdown'}}
    )

def log_health_check(service_name: str, status: str, checks: Dict[str, Any]) -> None:
    """Log health check results"""
    logger = get_logger(f"{service_name}.health")
    logger.info(
        f"Health check: {status}",
        extra={
            'extra_fields': {
                'event': 'health_check',
                'status': status,
                'checks': checks
            }
        }
    )
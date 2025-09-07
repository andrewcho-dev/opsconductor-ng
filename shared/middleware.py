#!/usr/bin/env python3
"""
Shared Middleware
Common FastAPI middleware for all services
"""

import time
import uuid
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import RequestLoggingMiddleware, get_logger
from .errors import add_error_handlers

logger = get_logger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs to all requests
    """
    
    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        
        # Store request ID in request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[self.header_name] = request_id
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add CSP header for non-API responses
        if not request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self'"
            )
        
        return response

class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request performance metrics
    """
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}.performance")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)
        
        # Add performance header
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        
        # Log slow requests (> 1 second)
        if duration > 1.0:
            self.logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration_ms}ms",
                extra={
                    'extra_fields': {
                        'method': request.method,
                        'path': str(request.url.path),
                        'duration_ms': duration_ms,
                        'status_code': response.status_code,
                        'slow_request': True
                    }
                }
            )
        
        return response

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle health check requests efficiently
    """
    
    def __init__(self, app, service_name: str, version: str):
        super().__init__(app)
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Handle basic health check without going through the full stack
        if request.url.path == "/health" and request.method == "GET":
            uptime = time.time() - self.start_time
            
            health_response = {
                "service": self.service_name,
                "status": "healthy",
                "version": self.version,
                "uptime_seconds": round(uptime, 2),
                "timestamp": time.time()
            }
            
            return Response(
                content=str(health_response).replace("'", '"'),
                media_type="application/json",
                status_code=200
            )
        
        return await call_next(request)

def add_standard_middleware(
    app: FastAPI,
    service_name: str,
    version: str = "1.0.0",
    enable_cors: bool = True,
    cors_origins: list = None,
    enable_request_logging: bool = True,
    enable_security_headers: bool = True,
    enable_performance_tracking: bool = True,
    enable_request_id: bool = True,
    trusted_hosts: list = None
) -> None:
    """
    Add all standard middleware to a FastAPI application
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service
        version: Service version
        enable_cors: Whether to enable CORS middleware
        cors_origins: List of allowed CORS origins
        enable_request_logging: Whether to enable request logging
        enable_security_headers: Whether to add security headers
        enable_performance_tracking: Whether to track performance metrics
        enable_request_id: Whether to add request ID tracking
        trusted_hosts: List of trusted host patterns
    """
    
    # Add error handlers first
    add_error_handlers(app)
    
    # Add trusted host middleware if specified
    if trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
    
    # Add security headers middleware
    if enable_security_headers:
        app.add_middleware(SecurityHeadersMiddleware)
    
    # Add performance tracking middleware
    if enable_performance_tracking:
        app.add_middleware(PerformanceMiddleware, service_name=service_name)
    
    # Add request ID middleware
    if enable_request_id:
        app.add_middleware(RequestIDMiddleware)
    
    # Add request logging middleware
    if enable_request_logging:
        app.add_middleware(RequestLoggingMiddleware, service_name=service_name)
    
    # Add health check middleware
    app.add_middleware(HealthCheckMiddleware, service_name=service_name, version=version)
    
    # Add CORS middleware (should be last)
    if enable_cors:
        cors_origins = cors_origins or ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    logger.info(f"Standard middleware added to {service_name}")

def add_development_middleware(app: FastAPI, service_name: str) -> None:
    """
    Add development-specific middleware (more permissive settings)
    """
    add_standard_middleware(
        app=app,
        service_name=service_name,
        enable_cors=True,
        cors_origins=["*"],  # Allow all origins in development
        enable_request_logging=True,
        enable_security_headers=False,  # Disable strict security headers in dev
        enable_performance_tracking=True,
        enable_request_id=True
    )

def add_production_middleware(
    app: FastAPI, 
    service_name: str, 
    allowed_origins: list,
    trusted_hosts: list = None
) -> None:
    """
    Add production-specific middleware (strict security settings)
    """
    add_standard_middleware(
        app=app,
        service_name=service_name,
        enable_cors=True,
        cors_origins=allowed_origins,  # Specific origins only
        enable_request_logging=True,
        enable_security_headers=True,  # Enable all security headers
        enable_performance_tracking=True,
        enable_request_id=True,
        trusted_hosts=trusted_hosts or ["localhost", "127.0.0.1"]
    )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware (for future use)
    Note: In production, use Redis-based rate limiting
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # In-memory store (not suitable for production)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Simple rate limiting logic
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time() / 60)  # Current minute
        
        # Clean old entries
        self.requests = {k: v for k, v in self.requests.items() if k[1] >= current_time}
        
        # Check current requests
        key = (client_ip, current_time)
        current_requests = self.requests.get(key, 0)
        
        if current_requests >= self.requests_per_minute:
            return Response(
                content='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}}',
                status_code=429,
                media_type="application/json"
            )
        
        # Increment counter
        self.requests[key] = current_requests + 1
        
        return await call_next(request)
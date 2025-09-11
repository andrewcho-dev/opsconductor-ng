#!/usr/bin/env python3
"""
Service Middleware Template
Self-contained middleware for microservices
Copy this file to your service directory and customize as needed
"""

import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .errors import add_error_handlers
from .logging_config import log_request

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log all HTTP requests with timing"""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate duration
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Log the request
    log_request(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        duration_ms=duration
    )
    
    return response

def add_standard_middleware(app: FastAPI, service_name: str, version: str = "1.0.0"):
    """Add standard middleware to FastAPI app"""
    
    # Add error handlers
    add_error_handlers(app)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )
    
    # Add custom logging middleware
    app.middleware("http")(logging_middleware)
    
    logger.info(f"Standard middleware added to {service_name} v{version}")
#!/usr/bin/env python3
"""
Service Models Template
Self-contained Pydantic models for microservices
Copy this file to your service directory and customize as needed
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
from datetime import datetime

class HealthCheck(BaseModel):
    """Health check status model"""
    status: str
    timestamp: datetime
    service: str
    version: str
    uptime_seconds: Optional[float] = None
    database: Optional[Dict[str, Any]] = None
    dependencies: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health response wrapper"""
    health: HealthCheck

class StandardResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    success: bool
    message: str
    data: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    timestamp: datetime

def create_success_response(
    message: str = "Operation successful",
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response

def create_paginated_response(
    data: List[Dict[str, Any]],
    total: int,
    page: int = 1,
    limit: int = 50,
    message: str = "Data retrieved successfully"
) -> Dict[str, Any]:
    """Create a standardized paginated response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        },
        "timestamp": datetime.utcnow().isoformat()
    }
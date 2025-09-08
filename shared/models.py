#!/usr/bin/env python3
"""
Shared Pydantic Models
Common response models and data structures for all services
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

# Generic type for paginated responses
T = TypeVar('T')

class HealthCheck(BaseModel):
    """Individual health check result"""
    name: str = Field(..., description="Name of the health check")
    status: str = Field(..., description="Status: healthy, unhealthy, degraded")
    message: Optional[str] = Field(None, description="Additional status message")
    duration_ms: Optional[float] = Field(None, description="Check duration in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional check details")

class HealthResponse(BaseModel):
    """Standardized health check response"""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Overall status: healthy, unhealthy, degraded")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    checks: List[HealthCheck] = Field(default_factory=list, description="Individual health checks")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: ErrorDetail = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    method: Optional[str] = Field(None, description="HTTP method")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=1000, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    data: List[T] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        per_page: int,
        total_items: int
    ) -> 'PaginatedResponse[T]':
        """Create paginated response with calculated metadata"""
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 0
        
        meta = PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return cls(data=items, meta=meta)

class StandardResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool = Field(True, description="Whether the operation was successful")
    data: Optional[T] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Optional message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
    
    @classmethod
    def success_response(cls, data: T = None, message: str = None) -> 'StandardResponse[T]':
        """Create successful response"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, message: str, data: T = None) -> 'StandardResponse[T]':
        """Create error response"""
        return cls(success=False, data=data, message=message)

class ServiceInfo(BaseModel):
    """Service information model"""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    description: Optional[str] = Field(None, description="Service description")
    status: str = Field(..., description="Service status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime")
    dependencies: List[str] = Field(default_factory=list, description="Service dependencies")

class BulkOperationResult(BaseModel):
    """Result of bulk operations"""
    total_requested: int = Field(..., description="Total number of items requested for operation")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of errors encountered")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional operation details")

class AuditLog(BaseModel):
    """Audit log entry"""
    id: Optional[int] = Field(None, description="Audit log ID")
    user_id: Optional[int] = Field(None, description="User who performed the action")
    username: Optional[str] = Field(None, description="Username who performed the action")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of the resource affected")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional action details")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the action occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

# Common query parameters
class PaginationParams(BaseModel):
    """Common pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=1000, description="Items per page")

class SortParams(BaseModel):
    """Common sorting parameters"""
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc")

class FilterParams(BaseModel):
    """Common filtering parameters"""
    search: Optional[str] = Field(None, description="Search term")
    created_after: Optional[datetime] = Field(None, description="Filter items created after this date")
    created_before: Optional[datetime] = Field(None, description="Filter items created before this date")
    updated_after: Optional[datetime] = Field(None, description="Filter items updated after this date")
    updated_before: Optional[datetime] = Field(None, description="Filter items updated before this date")

class BaseEntity(BaseModel):
    """Base entity with common fields"""
    id: Optional[int] = Field(None, description="Entity ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

# Service-specific base models that can be extended
class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role")
    is_active: bool = Field(True, description="Whether the user is active")

class CredentialBase(BaseModel):
    """Base credential model"""
    name: str = Field(..., description="Credential name")
    credential_type: str = Field(..., description="Type of credential")
    description: Optional[str] = Field(None, description="Credential description")

class TargetBase(BaseModel):
    """Base target model"""
    name: str = Field(..., description="Target name")
    hostname: str = Field(..., description="Target hostname or IP")
    port: int = Field(..., description="Target port")
    protocol: str = Field(..., description="Connection protocol")
    description: Optional[str] = Field(None, description="Target description")

class JobBase(BaseModel):
    """Base job model"""
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    steps: List[Dict[str, Any]] = Field(..., description="Job steps")
    timeout_seconds: int = Field(3600, description="Job timeout in seconds")

# Response wrapper functions
def create_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {
        "success": True,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    return response

def create_error_response(message: str, code: str = "ERROR", details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a standardized error response"""
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if details:
        response["error"]["details"] = details
    
    return response
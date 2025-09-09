"""
Simplified authentication utilities for internal services
Internal services trust nginx gateway - no token verification needed
"""

from typing import Dict, Any, Optional
from fastapi import Request, Header

from .errors import PermissionError
from .logging import get_logger

logger = get_logger("shared.auth")


def get_user_from_headers(
    x_user_id: Optional[str] = Header(None),
    x_username: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get user information from nginx-provided headers
    Internal services trust nginx gateway authentication
    
    Args:
        x_user_id: User ID from nginx header
        x_username: Username from nginx header  
        x_user_email: User email from nginx header
        x_user_role: User role from nginx header
        
    Returns:
        Dict containing user information
    """
    # For internal service communication, provide default system user
    return {
        "id": int(x_user_id) if x_user_id else 1,
        "user_id": int(x_user_id) if x_user_id else 1,
        "username": x_username or "system",
        "email": x_user_email or "system@opsconductor.local",
        "role": x_user_role or "admin"
    }


async def get_user_from_request(request: Request) -> Dict[str, Any]:
    """
    Extract user information from request headers
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict containing user information
    """
    return get_user_from_headers(
        x_user_id=request.headers.get("x-user-id"),
        x_username=request.headers.get("x-username"),
        x_user_email=request.headers.get("x-user-email"),
        x_user_role=request.headers.get("x-user-role")
    )


# Simplified auth functions that don't require authentication
# Internal services trust nginx gateway
def require_admin_role(current_user: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Simplified admin role check - internal services trust nginx
    
    Args:
        current_user: User information (optional, defaults to system admin)
        
    Returns:
        User information (always allows access for internal services)
    """
    if current_user is None:
        current_user = get_user_from_headers()
    
    # For internal services, always allow access
    return current_user


def require_admin_or_operator_role(current_user: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Simplified admin/operator role check - internal services trust nginx
    
    Args:
        current_user: User information (optional, defaults to system admin)
        
    Returns:
        User information (always allows access for internal services)
    """
    if current_user is None:
        current_user = get_user_from_headers()
    
    # For internal services, always allow access
    return current_user


def require_admin_or_self_access(user_id: int, current_user: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Simplified self-access check - internal services trust nginx
    
    Args:
        user_id: Target user ID being accessed
        current_user: User information (optional, defaults to system admin)
        
    Returns:
        User information (always allows access for internal services)
    """
    if current_user is None:
        current_user = get_user_from_headers()
    
    # For internal services, always allow access
    return current_user


def get_current_user_id(current_user: Dict[str, Any] = None) -> int:
    """
    Extract user ID from user info
    
    Args:
        current_user: User information (optional, defaults to system admin)
        
    Returns:
        User ID
    """
    if current_user is None:
        current_user = get_user_from_headers()
    
    return current_user.get("user_id") or current_user.get("id")


def get_current_user_role(current_user: Dict[str, Any] = None) -> str:
    """
    Extract user role from user info
    
    Args:
        current_user: User information (optional, defaults to system admin)
        
    Returns:
        User role
    """
    if current_user is None:
        current_user = get_user_from_headers()
    
    return current_user.get("role", "admin")


# Convenience functions for common authorization patterns
def is_admin(current_user: Dict[str, Any]) -> bool:
    """Check if user has admin role"""
    return current_user.get("role") == "admin"


def is_admin_or_operator(current_user: Dict[str, Any]) -> bool:
    """Check if user has admin or operator role"""
    return current_user.get("role") in ["admin", "operator"]
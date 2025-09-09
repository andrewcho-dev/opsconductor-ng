"""
Shared authentication and authorization utilities for all services
"""

import os
from typing import Dict, Any
from fastapi import Request

from .errors import PermissionError
from .logging import get_logger

logger = get_logger("shared.auth")

def require_admin_role(request: Request) -> Dict[str, Any]:
    """
    Require admin role for endpoint access (from nginx headers)
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information if authorized
        
    Raises:
        PermissionError: If user doesn't have admin role
    """
    current_user = {
        "id": request.headers.get("X-User-ID"),
        "username": request.headers.get("X-Username"),
        "email": request.headers.get("X-User-Email"),
        "role": request.headers.get("X-User-Role")
    }
    
    if current_user["role"] != "admin":
        raise PermissionError("Admin role required")
    return current_user

# Convenience functions for common authorization patterns
def is_admin(current_user: Dict[str, Any]) -> bool:
    """Check if user has admin role"""
    return current_user.get("role") == "admin"

def is_admin_or_operator(current_user: Dict[str, Any]) -> bool:
    """Check if user has admin or operator role"""
    return current_user.get("role") in ["admin", "operator"]

def can_access_user_data(target_user_id: int, current_user: Dict[str, Any]) -> bool:
    """Check if user can access target user's data"""
    return (current_user.get("role") == "admin" or 
            current_user.get("user_id") == target_user_id or
            current_user.get("id") == target_user_id)
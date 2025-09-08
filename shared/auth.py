"""
Shared authentication and authorization utilities for all services
"""

import os
import requests
from typing import Dict, Any, Optional
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .errors import AuthError, ServiceCommunicationError, PermissionError
from .logging import get_logger

logger = get_logger("shared.auth")

# Initialize security scheme
security = HTTPBearer()

# Auth service URL from environment
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:3001")

def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token with auth service
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Dict containing user information
        
    Raises:
        AuthError: If token is invalid
        ServiceCommunicationError: If auth service is unavailable
    """
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise AuthError("Invalid or expired token")
        
        response_data = response.json()
        if "data" in response_data and "user" in response_data["data"]:
            return response_data["data"]["user"]
        return response_data.get("user", response_data)
        
    except requests.RequestException as e:
        logger.error(f"Auth service communication error: {e}")
        raise ServiceCommunicationError("auth-service", "Auth service unavailable")

async def verify_token_with_auth_service_async(authorization: Optional[str] = None) -> Dict[str, Any]:
    """
    Async version of token verification for services that need it
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Dict containing user information
        
    Raises:
        AuthError: If token is invalid or missing
        ServiceCommunicationError: If auth service is unavailable
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise AuthError("Invalid or expired token")
        
        response_data = response.json()
        if "data" in response_data and "user" in response_data["data"]:
            return response_data["data"]["user"]
        return response_data.get("user", response_data)
        
    except requests.RequestException as e:
        logger.error(f"Auth service communication error: {e}")
        raise ServiceCommunicationError("auth-service", "Auth service unavailable")

async def verify_token_from_request(request: Request) -> Dict[str, Any]:
    """
    Extract and verify token from request headers
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict containing user information
    """
    authorization = request.headers.get("authorization")
    return await verify_token_with_auth_service_async(authorization)

def require_admin_role(current_user: Dict[str, Any] = Depends(verify_token_with_auth_service)) -> Dict[str, Any]:
    """
    Require admin role for endpoint access
    
    Args:
        current_user: User information from token verification
        
    Returns:
        User information if authorized
        
    Raises:
        PermissionError: If user doesn't have admin role
    """
    if current_user["role"] != "admin":
        raise PermissionError("Admin role required")
    return current_user

def require_admin_or_operator_role(current_user: Dict[str, Any] = Depends(verify_token_with_auth_service)) -> Dict[str, Any]:
    """
    Require admin or operator role for endpoint access
    
    Args:
        current_user: User information from token verification
        
    Returns:
        User information if authorized
        
    Raises:
        PermissionError: If user doesn't have required role
    """
    if current_user["role"] not in ["admin", "operator"]:
        raise PermissionError("Admin or operator role required")
    return current_user

def require_admin_or_self_access(user_id: int, current_user: Dict[str, Any] = Depends(verify_token_with_auth_service)) -> Dict[str, Any]:
    """
    Require admin role or self-access (user accessing their own data)
    
    Args:
        user_id: Target user ID being accessed
        current_user: User information from token verification
        
    Returns:
        User information if authorized
        
    Raises:
        PermissionError: If user doesn't have permission
    """
    if current_user["role"] != "admin" and current_user.get("user_id") != user_id:
        raise PermissionError("Access denied")
    return current_user

def get_current_user_id(current_user: Dict[str, Any] = Depends(verify_token_with_auth_service)) -> int:
    """
    Extract user ID from verified token
    
    Args:
        current_user: User information from token verification
        
    Returns:
        User ID
    """
    return current_user.get("user_id") or current_user.get("id")

def get_current_user_role(current_user: Dict[str, Any] = Depends(verify_token_with_auth_service)) -> str:
    """
    Extract user role from verified token
    
    Args:
        current_user: User information from token verification
        
    Returns:
        User role
    """
    return current_user.get("role", "user")

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
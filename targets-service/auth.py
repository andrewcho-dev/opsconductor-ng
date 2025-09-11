#!/usr/bin/env python3
"""
Service Authentication Template
Self-contained auth utilities for microservices
Copy this file to your service directory and customize as needed
"""

from typing import Dict, Any, Optional
from fastapi import Request, Header
from .errors import PermissionError

def get_user_from_headers(
    x_user_id: Optional[str] = Header(None),
    x_username: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get user information from nginx-provided headers
    Internal services trust nginx gateway authentication
    """
    return {
        "id": int(x_user_id) if x_user_id else 1,
        "user_id": int(x_user_id) if x_user_id else 1,
        "username": x_username or "system",
        "email": x_user_email or "system@opsconductor.local",
        "role": x_user_role or "admin"
    }

async def get_user_from_request(request: Request) -> Dict[str, Any]:
    """Extract user information from request headers"""
    return get_user_from_headers(
        x_user_id=request.headers.get("x-user-id"),
        x_username=request.headers.get("x-username"),
        x_user_email=request.headers.get("x-user-email"),
        x_user_role=request.headers.get("x-user-role")
    )

def require_admin_role(current_user: Dict[str, Any] = None) -> Dict[str, Any]:
    """Simplified admin role check - internal services trust nginx"""
    if current_user is None:
        current_user = get_user_from_headers()
    return current_user

def require_admin_or_operator_role(current_user: Dict[str, Any] = None) -> Dict[str, Any]:
    """Simplified admin/operator role check - internal services trust nginx"""
    if current_user is None:
        current_user = get_user_from_headers()
    return current_user

def get_current_user_id(current_user: Dict[str, Any] = None) -> int:
    """Extract user ID from user info"""
    if current_user is None:
        current_user = get_user_from_headers()
    return current_user.get("user_id") or current_user.get("id")

def get_current_user_role(current_user: Dict[str, Any] = None) -> str:
    """Extract user role from user info"""
    if current_user is None:
        current_user = get_user_from_headers()
    return current_user.get("role", "admin")

def is_admin(current_user: Dict[str, Any]) -> bool:
    """Check if user has admin role"""
    return current_user.get("role") == "admin"

def is_admin_or_operator(current_user: Dict[str, Any]) -> bool:
    """Check if user has admin or operator role"""
    return current_user.get("role") in ["admin", "operator"]
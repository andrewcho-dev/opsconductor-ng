"""
RBAC Middleware for OpsConductor Services
Provides permission checking utilities for backend services
"""

from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, Request, status
import json


class RBACMiddleware:
    """RBAC middleware for checking user permissions"""
    
    @staticmethod
    def get_user_from_headers(request: Request) -> dict:
        """Extract user information from request headers"""
        return {
            'id': request.headers.get('x-user-id'),
            'username': request.headers.get('x-username', ''),
            'email': request.headers.get('x-user-email', ''),
            'role': request.headers.get('x-user-role', 'viewer'),
            'permissions': request.headers.get('x-user-permissions', '').split(',') if request.headers.get('x-user-permissions') else [],
            'authenticated': request.headers.get('x-authenticated', 'false').lower() == 'true'
        }
    
    @staticmethod
    def has_permission(user: dict, permission: str) -> bool:
        """Check if user has a specific permission"""
        if not user or not user.get('authenticated'):
            return False
        
        permissions = user.get('permissions', [])
        
        # Admin wildcard permission grants everything
        if '*' in permissions:
            return True
        
        return permission in permissions
    
    @staticmethod
    def has_any_permission(user: dict, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        if not user or not user.get('authenticated'):
            return False
        
        user_permissions = user.get('permissions', [])
        
        # Admin wildcard permission grants everything
        if '*' in user_permissions:
            return True
        
        return any(permission in user_permissions for permission in permissions)
    
    @staticmethod
    def has_all_permissions(user: dict, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions"""
        if not user or not user.get('authenticated'):
            return False
        
        user_permissions = user.get('permissions', [])
        
        # Admin wildcard permission grants everything
        if '*' in user_permissions:
            return True
        
        return all(permission in user_permissions for permission in permissions)
    
    @staticmethod
    def has_role(user: dict, role: str) -> bool:
        """Check if user has a specific role"""
        if not user or not user.get('authenticated'):
            return False
        
        return user.get('role') == role
    
    @staticmethod
    def is_admin(user: dict) -> bool:
        """Check if user is admin"""
        if not user or not user.get('authenticated'):
            return False
        
        return user.get('role') == 'admin' or '*' in user.get('permissions', [])


def require_permission(permission: str):
    """Decorator to require a specific permission"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in the arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look for request in kwargs
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            user = RBACMiddleware.get_user_from_headers(request)
            
            if not RBACMiddleware.has_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required permission: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """Decorator to require any of the specified permissions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in the arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look for request in kwargs
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            user = RBACMiddleware.get_user_from_headers(request)
            
            if not RBACMiddleware.has_any_permission(user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required permissions (any): {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """Decorator to require a specific role"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in the arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look for request in kwargs
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            user = RBACMiddleware.get_user_from_headers(request)
            
            if not RBACMiddleware.has_role(user, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role: {role}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """Decorator to require admin access"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in the arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look for request in kwargs
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            user = RBACMiddleware.get_user_from_headers(request)
            
            if not RBACMiddleware.is_admin(user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Permission constants - should match frontend permissions
class PERMISSIONS:
    # User management
    USERS_READ = 'users:read'
    USERS_CREATE = 'users:create'
    USERS_UPDATE = 'users:update'
    USERS_DELETE = 'users:delete'
    
    # Role management
    ROLES_READ = 'roles:read'
    ROLES_CREATE = 'roles:create'
    ROLES_UPDATE = 'roles:update'
    ROLES_DELETE = 'roles:delete'
    
    # Job management
    JOBS_READ = 'jobs:read'
    JOBS_CREATE = 'jobs:create'
    JOBS_UPDATE = 'jobs:update'
    JOBS_DELETE = 'jobs:delete'
    JOBS_EXECUTE = 'jobs:execute'
    
    # Target management
    TARGETS_READ = 'targets:read'
    TARGETS_CREATE = 'targets:create'
    TARGETS_UPDATE = 'targets:update'
    TARGETS_DELETE = 'targets:delete'
    
    # Execution monitoring
    EXECUTIONS_READ = 'executions:read'
    
    # Step library management

    
    # Settings
    SETTINGS_READ = 'settings:read'
    SETTINGS_UPDATE = 'settings:update'
    SMTP_CONFIG = 'smtp:config'
    

    
    # System administration
    SYSTEM_ADMIN = 'system:admin'
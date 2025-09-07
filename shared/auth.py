#!/usr/bin/env python3
"""
Shared Authentication Utilities
Standardized JWT token verification and auth dependencies for all services
"""

import os
import logging
from typing import Optional, Dict, Any
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Global security instance
security = HTTPBearer()

class AuthError(HTTPException):
    """Standardized authentication error"""
    def __init__(self, detail: str = "Authentication failed", status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)

class AuthService:
    """Centralized authentication service communication"""
    
    def __init__(self, auth_service_url: str = None):
        self.auth_service_url = auth_service_url or os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
        self.timeout = 10.0
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with auth service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/api/verify-token",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise AuthError("Invalid or expired token")
                else:
                    logger.error(f"Auth service error: {response.status_code} - {response.text}")
                    raise AuthError("Authentication service unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)
                    
        except httpx.TimeoutException:
            logger.error("Auth service timeout")
            raise AuthError("Authentication service timeout", status.HTTP_503_SERVICE_UNAVAILABLE)
        except httpx.RequestError as e:
            logger.error(f"Auth service connection error: {e}")
            raise AuthError("Authentication service unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)
        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected auth error: {e}")
            raise AuthError("Authentication failed")

# Global auth service instance
_auth_service = None

def get_auth_service() -> AuthService:
    """Get or create auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

async def verify_token_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency for token verification
    Returns user data from verified token
    """
    if not credentials or not credentials.credentials:
        raise AuthError("Missing authentication token")
    
    auth_service = get_auth_service()
    user_data = await auth_service.verify_token(credentials.credentials)
    
    if not user_data:
        raise AuthError("Invalid token data")
    
    return user_data

async def get_current_user(
    user_data: Dict[str, Any] = Depends(verify_token_dependency)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user
    """
    return user_data

def require_role(required_role: str):
    """
    Dependency factory for role-based access control
    Usage: @app.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(user_data: Dict[str, Any] = Depends(get_current_user)):
        user_role = user_data.get("role", "").lower()
        if user_role != required_role.lower():
            raise AuthError(
                f"Insufficient permissions. Required role: {required_role}",
                status.HTTP_403_FORBIDDEN
            )
        return user_data
    
    return role_checker

def require_admin():
    """Convenience dependency for admin-only endpoints"""
    return require_role("admin")

# Legacy compatibility functions for existing services
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Legacy compatibility wrapper"""
    return await verify_token_dependency(credentials)

def create_auth_dependency(auth_service_url: str = None):
    """
    Factory function to create auth dependency with custom auth service URL
    Useful for testing or custom configurations
    """
    custom_auth_service = AuthService(auth_service_url)
    
    async def custom_verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        if not credentials or not credentials.credentials:
            raise AuthError("Missing authentication token")
        
        user_data = await custom_auth_service.verify_token(credentials.credentials)
        
        if not user_data:
            raise AuthError("Invalid token data")
        
        return user_data
    
    return custom_verify_token
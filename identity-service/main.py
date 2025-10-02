#!/usr/bin/env python3
"""
OpsConductor Identity Service - SIMPLIFIED (Keycloak Only)
Pure JWT token validation service - NO local user management
"""

import sys
import os
from fastapi import HTTPException, status, Request
from pydantic import BaseModel
sys.path.append('/app/shared')
from base_service import BaseService
from keycloak_adapter import KeycloakAdapter

# ============================================================================
# MODELS - MINIMAL
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class IdentityService(BaseService):
    def __init__(self):
        super().__init__("identity-service", "1.0.0", 3001)
        # NO DATABASE NEEDED - Pure Keycloak proxy
        # Override database initialization
        self.db = None
    
    async def setup_service_dependencies(self):
        """Setup identity service specific dependencies"""
        # Keycloak dependency (REQUIRED)
        keycloak_url = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
        self.startup_manager.add_service_dependency(
            "keycloak",
            keycloak_url,
            endpoint="/health/ready",
            timeout=120,
            critical=True  # CRITICAL - no fallback
        )
    
    async def on_startup(self):
        """Identity service startup logic"""
        self.keycloak = KeycloakAdapter()
        self._setup_routes()

    def _setup_routes(self):
        """Setup ONLY authentication routes - NO user management"""
        
        # ============================================================================
        # AUTHENTICATION ENDPOINTS ONLY
        # ============================================================================
        
        @self.app.post("/auth/login", response_model=LoginResponse)
        async def login(login_data: LoginRequest):
            """Authenticate user via Keycloak ONLY"""
            try:
                # Pure Keycloak authentication
                auth_result = await self.keycloak.authenticate_user(
                    login_data.username, 
                    login_data.password
                )
                
                if not auth_result:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                
                return LoginResponse(
                    access_token=auth_result["access_token"],
                    refresh_token=auth_result["refresh_token"],
                    expires_in=auth_result["expires_in"],
                    user=auth_result["user"]
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Login failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Login failed"
                )

        @self.app.get("/auth/me", response_model=dict)
        async def get_current_user(request: Request):
            """Get current user info from Keycloak token ONLY"""
            try:
                # Extract token from Authorization header
                auth_header = request.headers.get("authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
                
                token = auth_header.split(" ")[1]
                
                # Validate token with Keycloak ONLY
                user_info = await self.keycloak.decode_token(token)
                
                if not user_info:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                
                return {
                    "success": True,
                    "data": user_info
                }
                    
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get current user", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get user information"
                )

        @self.app.get("/auth/verify")
        async def verify_token(request: Request):
            """Verify JWT token with Keycloak ONLY"""
            try:
                # Extract token from Authorization header
                auth_header = request.headers.get("authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
                
                token = auth_header.split(" ")[1]
                
                # Validate token with Keycloak
                user_info = await self.keycloak.decode_token(token)
                
                if not user_info:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                
                return {
                    "valid": True,
                    "user": user_info
                }
                    
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to verify token", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to verify token"
                )

        # ============================================================================
        # KEYCLOAK ADMIN PROXY (Optional - for user management through Keycloak)
        # ============================================================================
        
        @self.app.get("/keycloak/users")
        async def proxy_keycloak_users():
            """Proxy to Keycloak Admin API for user list"""
            # Direct proxy to Keycloak Admin API
            # Frontend should call Keycloak directly or this endpoint
            try:
                users = await self.keycloak.list_users()
                return {"success": True, "data": users}
            except Exception as e:
                self.logger.error("Failed to get users from Keycloak", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to get users")

        # Health endpoint
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "identity-service",
                "version": "2.0.0-keycloak-only",
                "keycloak_connected": self.keycloak is not None
            }

if __name__ == "__main__":
    service = IdentityService()
    service.run()
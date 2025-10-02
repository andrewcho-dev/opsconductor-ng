"""
Keycloak Adapter for OpsConductor Identity Service
This adapter provides a bridge between the legacy identity service and Keycloak
during the migration period, allowing gradual transition.
"""

import os
import json
import httpx
import asyncio
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import jwt
from jwt import PyJWKClient
import logging

logger = logging.getLogger(__name__)

class KeycloakAdapter:
    """Adapter for Keycloak integration with OpsConductor"""
    
    def __init__(self):
        self.keycloak_url = os.getenv('KEYCLOAK_URL', 'http://keycloak:8080')
        self.realm = os.getenv('KEYCLOAK_REALM', 'opsconductor')
        self.client_id = os.getenv('KEYCLOAK_CLIENT_ID', 'opsconductor-frontend')
        self.client_secret = os.getenv('KEYCLOAK_CLIENT_SECRET', 'frontend-secret-key-2024')
        
        # JWT configuration
        self.jwks_client = None
        self.issuer = f"{self.keycloak_url}/realms/{self.realm}"
        
        # Migration mode - allows fallback to legacy system
        self.migration_mode = os.getenv('KEYCLOAK_MIGRATION_MODE', 'true').lower() == 'true'
        
        self._init_jwks_client()
    
    def _init_jwks_client(self):
        """Initialize JWKS client for token verification"""
        try:
            jwks_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"
            self.jwks_client = PyJWKClient(jwks_url)
            logger.info("✅ JWKS client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize JWKS client: {e}")
            self.jwks_client = None
    
    async def get_service_token(self) -> Optional[str]:
        """Get service-to-service access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token",
                    data={
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'grant_type': 'client_credentials'
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    return token_data['access_token']
                else:
                    logger.error(f"❌ Failed to get service token: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting service token: {e}")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with Keycloak"""
        try:
            async with httpx.AsyncClient() as client:
                # For public clients, don't send client_secret
                response = await client.post(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token",
                    data={
                        'client_id': self.client_id,
                        'username': username,
                        'password': password,
                        'grant_type': 'password'
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Decode token to get user info
                    user_info = await self.decode_token(token_data['access_token'])
                    if user_info:
                        return {
                            'access_token': token_data['access_token'],
                            'refresh_token': token_data.get('refresh_token'),
                            'expires_in': token_data.get('expires_in', 300),
                            'user': user_info
                        }
                    
                return None
                
        except Exception as e:
            logger.error(f"❌ Error authenticating user: {e}")
            return None
    
    async def decode_token(self, token: str) -> Optional[Dict]:
        """Decode and verify JWT token"""
        try:
            if not self.jwks_client:
                logger.error("❌ JWKS client not initialized")
                return None
            
            # Get signing key
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode token (skip audience verification for now as Keycloak tokens may not include expected audience)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.issuer,
                options={"verify_exp": True, "verify_aud": False}
            )
            
            # Extract user information
            user_info = {
                'id': payload.get('sub'),
                'username': payload.get('preferred_username'),
                'email': payload.get('email'),
                'first_name': payload.get('given_name', ''),
                'last_name': payload.get('family_name', ''),
                'roles': payload.get('realm_access', {}).get('roles', []),
                'is_admin': 'admin' in payload.get('realm_access', {}).get('roles', []),
                'exp': payload.get('exp'),
                'iat': payload.get('iat')
            }
            
            return user_info
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"❌ Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error decoding token: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token using refresh token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token",
                    data={
                        'client_id': 'opsconductor-frontend',
                        'client_secret': 'opsconductor-frontend-secret-2024',
                        'refresh_token': refresh_token,
                        'grant_type': 'refresh_token'
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"❌ Failed to refresh token: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error refreshing token: {e}")
            return None
    
    async def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get user information from Keycloak"""
        try:
            token = await self.get_service_token()
            if not token:
                return None
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.keycloak_url}/admin/realms/{self.realm}/users/{user_id}",
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    
                    # Get user roles
                    roles_response = await client.get(
                        f"{self.keycloak_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                        headers={'Authorization': f'Bearer {token}'}
                    )
                    
                    roles = []
                    if roles_response.status_code == 200:
                        roles = [role['name'] for role in roles_response.json()]
                    
                    return {
                        'id': user_data['id'],
                        'username': user_data['username'],
                        'email': user_data.get('email', ''),
                        'first_name': user_data.get('firstName', ''),
                        'last_name': user_data.get('lastName', ''),
                        'enabled': user_data.get('enabled', False),
                        'roles': roles,
                        'is_admin': 'admin' in roles,
                        'attributes': user_data.get('attributes', {})
                    }
                else:
                    logger.error(f"❌ Failed to get user info: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting user info: {e}")
            return None
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List users from Keycloak"""
        try:
            token = await self.get_service_token()
            if not token:
                return []
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.keycloak_url}/admin/realms/{self.realm}/users",
                    params={'first': offset, 'max': limit},
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                if response.status_code == 200:
                    users_data = response.json()
                    users = []
                    
                    for user_data in users_data:
                        # Get roles for each user
                        roles_response = await client.get(
                            f"{self.keycloak_url}/admin/realms/{self.realm}/users/{user_data['id']}/role-mappings/realm",
                            headers={'Authorization': f'Bearer {token}'}
                        )
                        
                        roles = []
                        if roles_response.status_code == 200:
                            roles = [role['name'] for role in roles_response.json()]
                        
                        users.append({
                            'id': user_data['id'],
                            'username': user_data['username'],
                            'email': user_data.get('email', ''),
                            'first_name': user_data.get('firstName', ''),
                            'last_name': user_data.get('lastName', ''),
                            'enabled': user_data.get('enabled', False),
                            'roles': roles,
                            'is_admin': 'admin' in roles,
                            'created_timestamp': user_data.get('createdTimestamp')
                        })
                    
                    return users
                else:
                    logger.error(f"❌ Failed to list users: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error listing users: {e}")
            return []
    
    async def check_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Check if user has required permission based on roles"""
        # Define role-based permissions mapping
        role_permissions = {
            'admin': ['*'],  # Admin has all permissions
            'operator': [
                'assets:read', 'assets:write', 'assets:delete',
                'automation:read', 'automation:write', 'automation:execute',
                'network:read', 'network:analyze',
                'communication:read', 'communication:write'
            ],
            'analyst': [
                'assets:read', 'automation:read', 'network:read', 
                'network:analyze', 'communication:read'
            ],
            'viewer': [
                'assets:read', 'automation:read', 'network:read', 'communication:read'
            ],
            'guest': [
                'assets:read'
            ]
        }
        
        # Check if any user role has the required permission
        for role in user_roles:
            permissions = role_permissions.get(role, [])
            if '*' in permissions or required_permission in permissions:
                return True
        
        return False
    
    async def logout_user(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/logout",
                    data={
                        'client_id': 'opsconductor-frontend',
                        'client_secret': 'opsconductor-frontend-secret-2024',
                        'refresh_token': refresh_token
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                return response.status_code == 204
                
        except Exception as e:
            logger.error(f"❌ Error logging out user: {e}")
            return False
    
    async def health_check(self) -> Dict:
        """Check Keycloak health status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.keycloak_url}/health/ready")
                
                if response.status_code == 200:
                    return {
                        'status': 'healthy',
                        'keycloak_url': self.keycloak_url,
                        'realm': self.realm,
                        'migration_mode': self.migration_mode
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f"HTTP {response.status_code}",
                        'keycloak_url': self.keycloak_url
                    }
                    
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'keycloak_url': self.keycloak_url
            }
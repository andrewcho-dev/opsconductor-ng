#!/usr/bin/env python3
"""
OpsConductor Identity Service
Handles authentication, authorization, and user management
Consolidates: auth-service + user-service
"""

import os
import sys
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List

import jwt
import bcrypt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

# Add shared to path
sys.path.append('/app/shared')
from base_service import BaseService, HealthCheck

# ============================================================================
# MODELS
# ============================================================================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_admin: bool = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_admin: bool
    last_login: Optional[datetime]
    created_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: List[str]
    created_at: datetime

# ============================================================================
# AUTHENTICATION
# ============================================================================

security = HTTPBearer()

class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise jwt.InvalidTokenError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# ============================================================================
# IDENTITY SERVICE
# ============================================================================

class IdentityService(BaseService):
    def __init__(self):
        super().__init__("identity-service", "1.0.0", 3001)
        
        # Initialize auth manager
        jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        self.auth = AuthManager(jwt_secret)
        
        # Setup routes
        self._setup_routes()
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Get current authenticated user"""
        payload = self.auth.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        async with self.db.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1 AND is_active = true",
                int(user_id)
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            return dict(user)
    
    async def require_admin(self, current_user: Dict[str, Any] = Depends(lambda self: self.get_current_user)) -> Dict[str, Any]:
        """Require admin privileges"""
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return current_user
    
    def _setup_routes(self):
        """Setup Identity Service routes"""
        
        # Authentication endpoints
        @self.app.post("/auth/login", response_model=LoginResponse)
        async def login(request: LoginRequest):
            """User login"""
            async with self.db.pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE username = $1 AND is_active = true",
                    request.username
                )
                
                if not user or not self.auth.verify_password(request.password, user['password_hash']):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid username or password"
                    )
                
                # Update last login
                await conn.execute(
                    "UPDATE users SET last_login = $1 WHERE id = $2",
                    datetime.utcnow(), user['id']
                )
                
                # Create tokens
                token_data = {"sub": str(user['id']), "username": user['username']}
                access_token = self.auth.create_access_token(token_data)
                refresh_token = self.auth.create_refresh_token(token_data)
                
                # Store refresh token
                refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
                await conn.execute("""
                    INSERT INTO user_sessions (user_id, refresh_token_hash, expires_at)
                    VALUES ($1, $2, $3)
                """, user['id'], refresh_token_hash, 
                    datetime.utcnow() + timedelta(days=self.auth.refresh_token_expire_days))
                
                return LoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=self.auth.access_token_expire_minutes * 60,
                    user=UserResponse(**user)
                )
        
        @self.app.post("/auth/refresh")
        async def refresh_token(request: TokenRefreshRequest):
            """Refresh access token"""
            payload = self.auth.verify_token(request.refresh_token, "refresh")
            user_id = int(payload.get("sub"))
            
            # Verify refresh token in database
            refresh_token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
            async with self.db.pool.acquire() as conn:
                session = await conn.fetchrow("""
                    SELECT * FROM user_sessions 
                    WHERE user_id = $1 AND refresh_token_hash = $2 AND expires_at > $3
                """, user_id, refresh_token_hash, datetime.utcnow())
                
                if not session:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid refresh token"
                    )
                
                # Get user
                user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
                
                # Create new access token
                token_data = {"sub": str(user['id']), "username": user['username']}
                access_token = self.auth.create_access_token(token_data)
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": self.auth.access_token_expire_minutes * 60
                }
        
        @self.app.post("/auth/logout")
        async def logout(current_user: Dict[str, Any] = Depends(self.get_current_user)):
            """User logout"""
            async with self.db.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM user_sessions WHERE user_id = $1",
                    current_user['id']
                )
            
            return self.create_success_response("Logged out successfully")
        
        @self.app.get("/auth/me", response_model=UserResponse)
        async def get_current_user_info(current_user: Dict[str, Any] = Depends(self.get_current_user)):
            """Get current user information"""
            return UserResponse(**current_user)
        
        # User management endpoints
        @self.app.post("/users", response_model=UserResponse)
        async def create_user(
            user_data: UserCreate,
            current_user: Dict[str, Any] = Depends(self.require_admin)
        ):
            """Create new user"""
            async with self.db.pool.acquire() as conn:
                # Check if username or email exists
                existing = await conn.fetchrow(
                    "SELECT id FROM users WHERE username = $1 OR email = $2",
                    user_data.username, user_data.email
                )
                
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username or email already exists"
                    )
                
                # Hash password
                password_hash = self.auth.hash_password(user_data.password)
                
                # Create user
                user = await conn.fetchrow("""
                    INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                """, user_data.username, user_data.email, password_hash,
                    user_data.first_name, user_data.last_name, user_data.is_admin)
                
                return UserResponse(**user)
        
        @self.app.get("/users", response_model=List[UserResponse])
        async def list_users(
            skip: int = 0,
            limit: int = 100,
            current_user: Dict[str, Any] = Depends(self.get_current_user)
        ):
            """List users"""
            async with self.db.pool.acquire() as conn:
                users = await conn.fetch(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                    limit, skip
                )
                
                return [UserResponse(**user) for user in users]
        
        @self.app.get("/users/{user_id}", response_model=UserResponse)
        async def get_user(
            user_id: int,
            current_user: Dict[str, Any] = Depends(self.get_current_user)
        ):
            """Get user by ID"""
            async with self.db.pool.acquire() as conn:
                user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                return UserResponse(**user)
        
        @self.app.put("/users/{user_id}", response_model=UserResponse)
        async def update_user(
            user_id: int,
            user_data: UserUpdate,
            current_user: Dict[str, Any] = Depends(self.require_admin)
        ):
            """Update user"""
            async with self.db.pool.acquire() as conn:
                # Build update query
                updates = []
                values = []
                param_count = 1
                
                for field, value in user_data.dict(exclude_unset=True).items():
                    updates.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1
                
                if not updates:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No fields to update"
                    )
                
                updates.append(f"updated_at = ${param_count}")
                values.append(datetime.utcnow())
                values.append(user_id)
                
                query = f"""
                    UPDATE users SET {', '.join(updates)}
                    WHERE id = ${param_count + 1}
                    RETURNING *
                """
                
                user = await conn.fetchrow(query, *values)
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                return UserResponse(**user)
        
        @self.app.post("/users/{user_id}/change-password")
        async def change_password(
            user_id: int,
            request: PasswordChangeRequest,
            current_user: Dict[str, Any] = Depends(self.get_current_user)
        ):
            """Change user password"""
            # Users can only change their own password unless admin
            if user_id != current_user['id'] and not current_user.get('is_admin'):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only change your own password"
                )
            
            async with self.db.pool.acquire() as conn:
                user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                # Verify current password (unless admin changing someone else's)
                if user_id == current_user['id']:
                    if not self.auth.verify_password(request.current_password, user['password_hash']):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Current password is incorrect"
                        )
                
                # Update password
                new_password_hash = self.auth.hash_password(request.new_password)
                await conn.execute(
                    "UPDATE users SET password_hash = $1, updated_at = $2 WHERE id = $3",
                    new_password_hash, datetime.utcnow(), user_id
                )
                
                # Invalidate all sessions for this user
                await conn.execute("DELETE FROM user_sessions WHERE user_id = $1", user_id)
                
                return self.create_success_response("Password changed successfully")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    service = IdentityService()
    service.run()
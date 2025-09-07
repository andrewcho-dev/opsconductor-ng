#!/usr/bin/env python3
"""
Auth Service - Python FastAPI Implementation
Handles authentication, JWT tokens, and user session management
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Add shared module to path
sys.path.append('/home/opsconductor', Dict, Any)

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool, get_database_metrics
from shared.logging import setup_service_logging, get_logger
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, StandardResponse, create_success_response
from shared.errors import DatabaseError, ValidationError, handle_database_error, AuthError

# Load environment variables
load_dotenv()

# Setup structured logging
setup_service_logging("auth-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("auth-service")

# FastAPI app
app = FastAPI(
    title="Auth Service", 
    version="1.0.0",
    description="Authentication and JWT token management service"
)

# Add standard middleware (includes CORS, logging, error handling, etc.)
add_standard_middleware(app, "auth-service", version="1.0.0")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Database configuration is now handled by shared.database module

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: str
    token_version: int

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshRequest(BaseModel):
    refresh_token: str

class User(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime
    token_version: int = 1

# Database connection is now handled by shared.database module

# Authentication utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data -> Any: dict, expires_delta -> Any: Optional[timedelta] = None) -> Any:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data -> Any: dict, expires_delta -> Any: Optional[timedelta] = None) -> Any:
    """Create JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT id, email, username, pwd_hash, role, created_at, token_version FROM users WHERE username = %s",
                (username,)
            )
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
                
            if not verify_password(password, user_data['pwd_hash']):
                return None
                
            return User(**user_data)
        
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise handle_database_error(e, "user authentication")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Verify JWT token and return user"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise AuthError("Invalid token")
            
        # Verify user exists and token_version matches
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT id, email, username, role, created_at, token_version FROM users WHERE id = %s",
                    (user_id,)
                )
                user_data = cursor.fetchone()
                
                if not user_data:
                    raise AuthError("User not found")
                    
                if user_data['token_version'] != payload.get("token_version", 1):
                    raise AuthError("Token revoked")
                    
                return User(**user_data)
        except Exception as e:
            if isinstance(e, AuthError):
                raise
            logger.error(f"Database error during token verification: {e}", exc_info=True)
            raise handle_database_error(e, "token verification")
            
    except JWTError:
        raise AuthError("Invalid token")

# API Endpoints
@app.post("/login", response_model=TokenResponse)
async def login(login_request -> Dict[str, Any]: LoginRequest) -> Dict[str, Any]:
    """Login endpoint - authenticate user and return tokens"""
    try:
        user = authenticate_user(login_request.username, login_request.password)
        
        if not user:
            raise AuthError("Invalid username or password")
    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        raise AuthError("Authentication failed")
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "token_version": user.token_version
    }
    
    access_token = create_access_token(token_data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(token_data, expires_delta=refresh_token_expires)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            created_at=user.created_at.isoformat(),
            token_version=user.token_version
        )
    )

@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_request -> Dict[str, Any]: RefreshRequest) -> Dict[str, Any]:
    """Refresh token endpoint"""
    try:
        payload = jwt.decode(refresh_request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise AuthError("Invalid refresh token")
        
        # Verify user and token version
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT id, email, username, role, created_at, token_version FROM users WHERE id = %s",
                    (user_id,)
                )
                user_data = cursor.fetchone()
                
                if not user_data:
                    raise AuthError("User not found")
                
                if user_data['token_version'] != payload.get("token_version", 1):
                    raise AuthError("Token revoked")
        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Database error during token refresh: {e}", exc_info=True)
            raise handle_database_error(e, "token refresh")
        
        # Create new tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        token_data = {
            "user_id": user_data['id'],
            "username": user_data['username'],
            "role": user_data['role'],
            "token_version": user_data['token_version']
        }
        
        access_token = create_access_token(token_data, expires_delta=access_token_expires)
        new_refresh_token = create_refresh_token(token_data, expires_delta=refresh_token_expires)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                role=user_data['role'],
                created_at=user_data['created_at'].isoformat(),
                token_version=user_data['token_version']
            )
        )
        
    except JWTError:
        raise AuthError("Invalid refresh token")

@app.post("/revoke-all")
async def revoke_all_tokens(current_user: User = Depends(verify_token)):
    """Revoke all tokens for current user"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET token_version = token_version + 1 WHERE id = %s",
                (current_user.id,)
            )
        
        return create_success_response(message="All tokens revoked successfully")
        
    except Exception as e:
        logger.error(f"Token revocation error: {e}", exc_info=True)
        raise handle_database_error(e, "token revocation")

@app.get("/verify")
async def verify_token_endpoint(current_user: User = Depends(verify_token)):
    """Verify token and return user info"""
    return create_success_response(
        data={
            "valid": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "role": current_user.role
            }
        },
        message="Token is valid"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with database connectivity"""
    db_health = check_database_health()
    
    # Create health checks list
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        )
    ]
    
    # Determine overall status
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        service="auth-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event() -> None:
    """Log service startup"""
    from shared.logging import log_startup
    log_startup("auth-service", "1.0.0", 3001)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up database connections on shutdown"""
    from shared.logging import log_shutdown
    log_shutdown("auth-service")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
#!/usr/bin/env python3
"""
User Service - Python FastAPI Implementation  
Full CRUD operations for user management
"""

import os
import logging
from datetime import datetime
from typing import List, Optional

import psycopg2
import psycopg2.extras
import requests
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="User Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "viewer"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime
    token_version: int

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int

class RoleAssignment(BaseModel):
    role: str

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

# Authentication utilities
def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return response.json()["user"]
        
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

def require_admin_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin role for protected endpoints"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user

# CRUD Operations
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, current_user: dict = Depends(require_admin_role)):
    """Create a new user - ADMIN ONLY"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if username or email already exists (excluding soft-deleted)
        cursor.execute(
            "SELECT id FROM users WHERE (email = %s OR username = %s) AND deleted_at IS NULL",
            (user_data.email, user_data.username)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or username already exists"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Insert user
        cursor.execute(
            """INSERT INTO users (email, username, password_hash, role, created_at, token_version)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id, email, username, role, created_at, token_version""",
            (user_data.email, user_data.username, hashed_password, user_data.role, datetime.utcnow(), 1)
        )
        
        new_user = cursor.fetchone()
        conn.commit()
        
        return UserResponse(**new_user)
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"User creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    finally:
        conn.close()

@app.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all users with pagination"""
    # Non-admin users can only see their own profile
    if current_user["role"] != "admin":
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, username, role, created_at, token_version FROM users WHERE id = %s AND deleted_at IS NULL",
                (current_user["id"],)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                return UserListResponse(
                    users=[UserResponse(**user_data)],
                    total=1
                )
            else:
                return UserListResponse(users=[], total=0)
        finally:
            conn.close()
    
    # Admin can see all users
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total count (excluding soft-deleted)
        cursor.execute("SELECT COUNT(*) FROM users WHERE deleted_at IS NULL")
        total = cursor.fetchone()["count"]
        
        # Get users with pagination (excluding soft-deleted)
        cursor.execute(
            """SELECT id, email, username, role, created_at, token_version 
               FROM users 
               WHERE deleted_at IS NULL
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (limit, skip)
        )
        users = cursor.fetchall()
        
        return UserListResponse(
            users=[UserResponse(**user) for user in users],
            total=total
        )
        
    except Exception as e:
        logger.error(f"User listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )
    finally:
        conn.close()

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get user by ID"""
    # Non-admin users can only access their own profile
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, username, role, created_at, token_version FROM users WHERE id = %s AND deleted_at IS NULL",
            (user_id,)
        )
        user_data = cursor.fetchone()
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user_data)
        
    except Exception as e:
        logger.error(f"User retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )
    finally:
        conn.close()

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Update user by ID"""
    # Non-admin users can only update their own profile (and not change role)
    if current_user["role"] != "admin":
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        if user_data.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role"
            )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if user exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build update query
        update_fields = []
        update_values = []
        
        if user_data.email is not None:
            update_fields.append("email = %s")
            update_values.append(user_data.email)
            
        if user_data.username is not None:
            update_fields.append("username = %s")
            update_values.append(user_data.username)
            
        if user_data.password is not None:
            update_fields.append("password_hash = %s")
            update_values.append(get_password_hash(user_data.password))
            
        if user_data.role is not None:
            update_fields.append("role = %s")
            update_values.append(user_data.role)
        
        if not update_fields:
            # No fields to update, just return current user
            cursor.execute(
                "SELECT id, email, username, role, created_at, token_version FROM users WHERE id = %s AND deleted_at IS NULL",
                (user_id,)
            )
            return UserResponse(**cursor.fetchone())
        
        # Execute update
        update_query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, email, username, role, created_at, token_version
        """
        update_values.append(user_id)
        
        cursor.execute(update_query, update_values)
        updated_user = cursor.fetchone()
        conn.commit()
        
        return UserResponse(**updated_user)
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    finally:
        conn.close()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin_role)):
    """Delete user by ID - ADMIN ONLY"""
    # Prevent admin from deleting themselves
    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if user exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete user
        cursor.execute(
            "UPDATE users SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
            (datetime.utcnow(), user_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or already deleted"
            )
        
        conn.commit()
        
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"User deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    finally:
        conn.close()

@app.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int, 
    role_data: RoleAssignment, 
    current_user: dict = Depends(require_admin_role)
):
    """Assign role to user - ADMIN ONLY"""
    valid_roles = ["admin", "operator", "viewer"]
    if role_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if user exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update role
        cursor.execute(
            "UPDATE users SET role = %s WHERE id = %s",
            (role_data.role, user_id)
        )
        conn.commit()
        
        return {"message": f"Role '{role_data.role}' assigned successfully"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Role assignment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )
    finally:
        conn.close()

# Notification Preferences Models
class NotificationPreferences(BaseModel):
    email_enabled: bool = True
    email_address: Optional[EmailStr] = None
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    teams_enabled: bool = False
    teams_webhook_url: Optional[str] = None
    notify_on_success: bool = True
    notify_on_failure: bool = True
    notify_on_start: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # Time as string "HH:MM"
    quiet_hours_end: Optional[str] = None    # Time as string "HH:MM"
    quiet_hours_timezone: str = "America/Los_Angeles"

class NotificationPreferencesResponse(NotificationPreferences):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

# Notification Preferences Endpoints

@app.get("/users/{user_id}/notification-preferences", response_model=NotificationPreferencesResponse)
async def get_user_notification_preferences(
    user_id: int,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get user notification preferences"""
    # Users can only access their own preferences, admins can access any
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if user exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get notification preferences
        cursor.execute("""
            SELECT * FROM user_notification_preferences WHERE user_id = %s
        """, (user_id,))
        
        preferences = cursor.fetchone()
        
        if not preferences:
            # Return default preferences if none exist
            return NotificationPreferencesResponse(
                id=0,
                user_id=user_id,
                email_enabled=True,
                webhook_enabled=False,
                slack_enabled=False,
                teams_enabled=False,
                notify_on_success=True,
                notify_on_failure=True,
                notify_on_start=False,
                quiet_hours_enabled=False,
                quiet_hours_timezone="America/Los_Angeles",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        # Convert time objects to strings for API response
        preferences_dict = dict(preferences)
        if preferences_dict.get('quiet_hours_start'):
            preferences_dict['quiet_hours_start'] = str(preferences_dict['quiet_hours_start'])
        if preferences_dict.get('quiet_hours_end'):
            preferences_dict['quiet_hours_end'] = str(preferences_dict['quiet_hours_end'])
        
        return NotificationPreferencesResponse(**preferences_dict)
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )
    finally:
        conn.close()

@app.put("/users/{user_id}/notification-preferences", response_model=NotificationPreferencesResponse)
async def update_user_notification_preferences(
    user_id: int,
    preferences: NotificationPreferences,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Update user notification preferences"""
    # Users can only update their own preferences, admins can update any
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if user exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert time strings to time objects
        quiet_hours_start = None
        quiet_hours_end = None
        
        if preferences.quiet_hours_start:
            try:
                hour, minute = map(int, preferences.quiet_hours_start.split(':'))
                quiet_hours_start = f"{hour:02d}:{minute:02d}:00"
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid quiet_hours_start format. Use HH:MM"
                )
        
        if preferences.quiet_hours_end:
            try:
                hour, minute = map(int, preferences.quiet_hours_end.split(':'))
                quiet_hours_end = f"{hour:02d}:{minute:02d}:00"
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid quiet_hours_end format. Use HH:MM"
                )
        
        # Upsert preferences
        cursor.execute("""
            INSERT INTO user_notification_preferences (
                user_id, email_enabled, email_address, webhook_enabled, webhook_url,
                slack_enabled, slack_webhook_url, slack_channel, teams_enabled, teams_webhook_url,
                notify_on_success, notify_on_failure, notify_on_start,
                quiet_hours_enabled, quiet_hours_start, quiet_hours_end, quiet_hours_timezone,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                email_enabled = EXCLUDED.email_enabled,
                email_address = EXCLUDED.email_address,
                webhook_enabled = EXCLUDED.webhook_enabled,
                webhook_url = EXCLUDED.webhook_url,
                slack_enabled = EXCLUDED.slack_enabled,
                slack_webhook_url = EXCLUDED.slack_webhook_url,
                slack_channel = EXCLUDED.slack_channel,
                teams_enabled = EXCLUDED.teams_enabled,
                teams_webhook_url = EXCLUDED.teams_webhook_url,
                notify_on_success = EXCLUDED.notify_on_success,
                notify_on_failure = EXCLUDED.notify_on_failure,
                notify_on_start = EXCLUDED.notify_on_start,
                quiet_hours_enabled = EXCLUDED.quiet_hours_enabled,
                quiet_hours_start = EXCLUDED.quiet_hours_start,
                quiet_hours_end = EXCLUDED.quiet_hours_end,
                quiet_hours_timezone = EXCLUDED.quiet_hours_timezone,
                updated_at = EXCLUDED.updated_at
            RETURNING *
        """, (
            user_id, preferences.email_enabled, preferences.email_address,
            preferences.webhook_enabled, preferences.webhook_url,
            preferences.slack_enabled, preferences.slack_webhook_url, preferences.slack_channel,
            preferences.teams_enabled, preferences.teams_webhook_url,
            preferences.notify_on_success, preferences.notify_on_failure, preferences.notify_on_start,
            preferences.quiet_hours_enabled, quiet_hours_start, quiet_hours_end,
            preferences.quiet_hours_timezone, datetime.now()
        ))
        
        updated_preferences = cursor.fetchone()
        conn.commit()
        
        # Convert time objects to strings for API response
        preferences_dict = dict(updated_preferences)
        if preferences_dict.get('quiet_hours_start'):
            preferences_dict['quiet_hours_start'] = str(preferences_dict['quiet_hours_start'])
        if preferences_dict.get('quiet_hours_end'):
            preferences_dict['quiet_hours_end'] = str(preferences_dict['quiet_hours_end'])
        
        logger.info(f"Updated notification preferences for user {user_id}")
        return NotificationPreferencesResponse(**preferences_dict)
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
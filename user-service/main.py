#!/usr/bin/env python3
"""
User Service - Python FastAPI Implementation  
Full CRUD operations for user management
"""

import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add shared module to path
sys.path.append('/home/opsconductor')

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from dotenv import load_dotenv

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool, get_database_metrics
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, PaginatedResponse, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from shared.auth import require_admin_role
from shared.utils import get_service_client

# Load environment variables
load_dotenv()

# Setup structured logging
setup_service_logging("user-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("user-service")

# FastAPI app
app = FastAPI(
    title="User Service", 
    version="1.0.0",
    description="User management and CRUD operations service",
    openapi_url="/openapi.json"
)

# Add standard middleware (includes CORS, logging, error handling, etc.)
add_standard_middleware(app, "user-service", version="1.0.0")

# Helper functions for header-based authentication
def get_user_from_headers(request: Request):
    """Extract user info from nginx headers (set by gateway authentication)"""
    return {
        "id": request.headers.get("X-User-ID"),
        "username": request.headers.get("X-Username"),
        "email": request.headers.get("X-User-Email"),
        "role": request.headers.get("X-User-Role")
    }

async def require_admin_or_self_access(user_id: int, request: Request):
    """Require admin role or self-access (user accessing their own data)"""
    current_user = get_user_from_headers(request)
    user_role = current_user.get("role")
    current_user_id = current_user.get("id")
    
    if user_role != "admin" and str(current_user_id) != str(user_id):
        raise PermissionError("Access denied")
    return current_user

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "viewer"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    title: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    title: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime
    token_version: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    title: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int

class RoleAssignment(BaseModel):
    role: str

# Utility functions
def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

# CRUD Operations
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, request: Request):
    """Create a new user - ADMIN ONLY"""
    # Check admin role
    current_user = await require_admin_role(request)
    try:
        with get_db_cursor() as cursor:
            # Check if username or email already exists
            cursor.execute(
                "SELECT id FROM users WHERE (email = %s OR username = %s)",
                (user_data.email, user_data.username)
            )
            if cursor.fetchone():
                raise ValidationError("User with this email or username already exists")
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Insert user
            cursor.execute(
                """INSERT INTO users (email, username, pwd_hash, role, first_name, last_name, telephone, title, created_at, token_version)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id, email, username, role, first_name, last_name, telephone, title, created_at, token_version""",
                (user_data.email, user_data.username, hashed_password, user_data.role, 
                 user_data.first_name, user_data.last_name, user_data.telephone, user_data.title, 
                 datetime.utcnow(), 1)
            )
            
            new_user = cursor.fetchone()
            return UserResponse(**new_user)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"User creation error: {e}", exc_info=True)
        raise handle_database_error(e, "user creation")

@app.get("/users", response_model=PaginatedResponse, response_model_exclude_none=False)
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 100
):
    """List all users with pagination"""
    # Get user info from headers
    current_user = get_user_from_headers(request)
    # Non-admin users can only see their own profile
    if current_user["role"] != "admin":
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT id, email, username, role, first_name, last_name, telephone, title, created_at, token_version FROM users WHERE id = %s",
                    (current_user["id"],)
                )
                user_data = cursor.fetchone()
            
            if user_data:
                # Explicitly construct the response to ensure all fields are included
                response_data = {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'username': user_data['username'],
                    'role': user_data['role'],
                    'created_at': user_data['created_at'],
                    'token_version': user_data['token_version'],
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'telephone': user_data.get('telephone'),
                    'title': user_data.get('title')
                }
                return PaginatedResponse.create(
                    items=[UserResponse(**response_data)],
                    page=1,
                    per_page=1,
                    total_items=1
                )
            else:
                return PaginatedResponse.create(items=[], page=1, per_page=limit, total_items=0)
        except Exception as e:
            logger.error(f"Error fetching user profile: {e}", exc_info=True)
            raise handle_database_error(e, "user profile fetch")
    
    # Admin can see all users
    try:
        with get_db_cursor(commit=False) as cursor:
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()["count"]
            
            # Get users with pagination
            cursor.execute(
                """SELECT id, email, username, role, first_name, last_name, telephone, title, created_at, token_version 
                   FROM users 
                   ORDER BY created_at DESC 
                   LIMIT %s OFFSET %s""",
                (limit, skip)
            )
            users = cursor.fetchall()
        
        # Explicitly construct responses to ensure all fields are included
        user_responses = []
        for user in users:
            response_data = {
                'id': user['id'],
                'email': user['email'],
                'username': user['username'],
                'role': user['role'],
                'created_at': user['created_at'],
                'token_version': user['token_version'],
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'telephone': user.get('telephone'),
                'title': user.get('title')
            }
            user_responses.append(UserResponse(**response_data))
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        return PaginatedResponse.create(
            items=user_responses,
            page=current_page,
            per_page=limit,
            total_items=total
        )
            
    except Exception as e:
        logger.error(f"User listing error: {e}", exc_info=True)
        raise handle_database_error(e, "user listing")

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    """Get user by ID"""
    # Check admin or self access
    current_user = await require_admin_or_self_access(user_id, request)
    # Non-admin users can only access their own profile
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise PermissionError("Access denied")
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT id, email, username, role, first_name, last_name, telephone, title, created_at, token_version FROM users WHERE id = %s",
                (user_id,)
            )
            user_data = cursor.fetchone()
        
        if not user_data:
            raise NotFoundError("User", user_id)
        
        # Return user response
        response_data = {
            'id': user_data['id'],
            'email': user_data['email'],
            'username': user_data['username'],
            'role': user_data['role'],
            'created_at': user_data['created_at'],
            'token_version': user_data['token_version'],
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'telephone': user_data.get('telephone'),
            'title': user_data.get('title')
        }
        return UserResponse(**response_data)
        
    except (NotFoundError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"User retrieval error: {e}", exc_info=True)
        raise handle_database_error(e, "user retrieval")

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    request: Request
):
    """Update user by ID"""
    # Check admin or self access
    current_user = await require_admin_or_self_access(user_id, request)
    # Non-admin users can only update their own profile (and not change role)
    if current_user["role"] != "admin":
        if current_user["id"] != user_id:
            raise PermissionError("Access denied")
        if user_data.role is not None:
            raise PermissionError("Cannot change your own role")
    
    try:
        with get_db_cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise NotFoundError("User", user_id)
            
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
                
            if user_data.first_name is not None:
                update_fields.append("first_name = %s")
                update_values.append(user_data.first_name)
                
            if user_data.last_name is not None:
                update_fields.append("last_name = %s")
                update_values.append(user_data.last_name)
                
            if user_data.telephone is not None:
                update_fields.append("telephone = %s")
                update_values.append(user_data.telephone)
                
            if user_data.title is not None:
                update_fields.append("title = %s")
                update_values.append(user_data.title)
            
            if not update_fields:
                # No fields to update, just return current user
                cursor.execute(
                    "SELECT id, email, username, role, first_name, last_name, telephone, title, created_at, token_version FROM users WHERE id = %s",
                    (user_id,)
                )
                return UserResponse(**cursor.fetchone())
            
            # Execute update
            update_query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, email, username, role, first_name, last_name, telephone, title, created_at, token_version
            """
            update_values.append(user_id)
            
            cursor.execute(update_query, update_values)
            updated_user = cursor.fetchone()
            
            return UserResponse(**updated_user)
        
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise DatabaseError("Failed to update user")

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, request: Request):
    """Delete user by ID - ADMIN ONLY"""
    # Check admin role
    current_user = await require_admin_role(request)
    # Prevent admin from deleting themselves
    if current_user["id"] == user_id:
        raise ValidationError("Cannot delete your own account")
    
    try:
        with get_db_cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise NotFoundError("User not found")
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            if cursor.rowcount == 0:
                raise NotFoundError("User not found")
            
            return create_success_response(
                message="User deleted successfully",
                data={"user_id": user_id}
            )
        
    except Exception as e:
        logger.error(f"User deletion error: {e}")
        raise DatabaseError("Failed to delete user")

@app.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int, 
    role_data: RoleAssignment, 
    request: Request
):
    """Assign role to user - ADMIN ONLY"""
    # Check admin role
    current_user = await require_admin_role(request)
    valid_roles = ["admin", "operator", "viewer"]
    if role_data.role not in valid_roles:
        raise ValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}", "role")
    
    try:
        with get_db_cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise NotFoundError("User not found")
            
            # Update role
            cursor.execute(
                "UPDATE users SET role = %s WHERE id = %s",
                (role_data.role, user_id)
            )
            
            return create_success_response(
                message=f"Role '{role_data.role}' assigned successfully",
                data={"user_id": user_id, "role": role_data.role}
            )
        
    except Exception as e:
        logger.error(f"Role assignment error: {e}")
        raise DatabaseError("Failed to assign role")

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
    request: Request
):
    """Get user notification preferences"""
    # Check admin or self access
    current_user = await require_admin_or_self_access(user_id, request)
    # Users can only access their own preferences, admins can access any
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise PermissionError("Access denied")
    
    try:
        with get_db_cursor(commit=False) as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise NotFoundError("User not found")
            
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
        raise DatabaseError("Failed to get notification preferences")

@app.put("/users/{user_id}/notification-preferences", response_model=NotificationPreferencesResponse)
async def update_user_notification_preferences(
    user_id: int,
    preferences: NotificationPreferences,
    request: Request
):
    """Update user notification preferences"""
    # Check admin or self access
    current_user = await require_admin_or_self_access(user_id, request)
    # Users can only update their own preferences, admins can update any
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise PermissionError("Access denied")
    
    try:
        with get_db_cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise NotFoundError("User not found")
        
        # Convert time strings to time objects
        quiet_hours_start = None
        quiet_hours_end = None
        
        if preferences.quiet_hours_start:
            try:
                hour, minute = map(int, preferences.quiet_hours_start.split(':'))
                quiet_hours_start = f"{hour:02d}:{minute:02d}:00"
            except ValueError:
                raise ValidationError("Invalid quiet_hours_start format. Use HH:MM")
        
        if preferences.quiet_hours_end:
            try:
                hour, minute = map(int, preferences.quiet_hours_end.split(':'))
                quiet_hours_end = f"{hour:02d}:{minute:02d}:00"
            except ValueError:
                raise ValidationError("Invalid quiet_hours_end format. Use HH:MM")
        
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
        raise DatabaseError("Failed to update notification preferences")

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        service="user-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "user-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

@app.on_event("startup")
async def startup_event() -> None:
    """Log service startup"""
    log_startup("user-service", "1.0.0", 3002)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up database connections on shutdown"""
    log_shutdown("user-service")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
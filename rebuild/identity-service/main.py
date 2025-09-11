#!/usr/bin/env python3
"""
OpsConductor Identity Service
Handles authentication, authorization, and user management
Consolidates: auth-service + user-service
"""

import sys
import os
from typing import List, Optional
from fastapi import Query, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService

# ============================================================================
# MODELS
# ============================================================================

class User(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    title: Optional[str] = None
    role: Optional[str] = None  # Will be populated from user_roles
    last_login: Optional[str] = None
    created_at: str
    updated_at: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False
    is_active: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    title: Optional[str] = None
    role: Optional[str] = 'viewer'  # Default role

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    title: Optional[str] = None
    role: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class UserListResponse(BaseModel):
    data: List[User]
    meta: dict
    total: int  # For backward compatibility

class Role(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    is_active: bool
    created_at: str
    updated_at: str

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    is_active: bool = True

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class RoleListResponse(BaseModel):
    data: List[Role]
    meta: dict
    total: int  # For backward compatibility

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
        self._setup_routes()

    def _setup_routes(self):
        """Setup all API routes"""
        
        # ============================================================================
        # AUTHENTICATION ENDPOINTS
        # ============================================================================
        
        @self.app.post("/auth/login", response_model=LoginResponse)
        async def login(login_data: LoginRequest):
            """Authenticate user and return tokens"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get user with password hash
                    row = await conn.fetchrow("""
                        SELECT id, username, email, password_hash, is_admin, is_active
                        FROM identity.users WHERE username = $1 AND is_active = true
                    """, login_data.username)
                    
                    if not row:
                        raise HTTPException(status_code=401, detail="Invalid credentials")
                    
                    # Verify password (simplified for demo)
                    # In real implementation, use proper password hashing
                    if login_data.password != "admin123":  # Demo password
                        raise HTTPException(status_code=401, detail="Invalid credentials")
                    
                    # Update last login
                    await conn.execute(
                        "UPDATE identity.users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
                        row['id']
                    )
                    
                    # Generate tokens (simplified for demo)
                    import jwt
                    import time
                    
                    payload = {
                        "user_id": row['id'],
                        "username": row['username'],
                        "email": row['email'],
                        "is_admin": row['is_admin'],
                        "exp": int(time.time()) + 3600  # 1 hour
                    }
                    
                    access_token = jwt.encode(payload, "secret", algorithm="HS256")
                    refresh_token = jwt.encode({**payload, "exp": int(time.time()) + 86400}, "secret", algorithm="HS256")
                    
                    return LoginResponse(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_in=3600,
                        user={
                            "id": row['id'],
                            "username": row['username'],
                            "email": row['email'],
                            "is_admin": row['is_admin']
                        }
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
        async def get_current_user():
            """Get current user info from token"""
            # This would normally decode JWT token from Authorization header
            # Simplified for demo
            return {
                "success": True,
                "data": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "is_admin": True
                }
            }

        # ============================================================================
        # USER CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.get("/users", response_model=UserListResponse)
        async def list_users(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all users"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM identity.users")
                    
                    # Get users with pagination and role information
                    rows = await conn.fetch("""
                        SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.telephone, u.title,
                               u.is_admin, u.is_active, u.last_login, u.created_at, u.updated_at,
                               r.name as role_name
                        FROM identity.users u
                        LEFT JOIN identity.user_roles ur ON u.id = ur.user_id
                        LEFT JOIN identity.roles r ON ur.role_id = r.id
                        ORDER BY u.created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    users = []
                    for row in rows:
                        # Determine role - use role_name if available, otherwise derive from is_admin
                        role = row['role_name'] if row['role_name'] else ('admin' if row['is_admin'] else 'viewer')
                        
                        users.append(User(
                            id=row['id'],
                            username=row['username'],
                            email=row['email'],
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                            telephone=row['telephone'],
                            title=row['title'],
                            is_admin=row['is_admin'],
                            is_active=row['is_active'],
                            role=role,
                            last_login=row['last_login'].isoformat() if row['last_login'] else None,
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return UserListResponse(
                        data=users,
                        meta={
                            "total_items": total,
                            "skip": skip,
                            "limit": limit,
                            "has_more": skip + limit < total
                        },
                        total=total  # For backward compatibility
                    )
            except Exception as e:
                self.logger.error("Failed to fetch users", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch users"
                )

        @self.app.post("/users", response_model=dict)
        async def create_user(user_data: UserCreate):
            """Create a new user"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Hash password (simplified for demo)
                    password_hash = f"hashed_{user_data.password}"
                    
                    # Create user with new fields
                    row = await conn.fetchrow("""
                        INSERT INTO identity.users (username, email, password_hash, first_name, last_name, telephone, title, is_admin, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id, username, email, first_name, last_name, telephone, title, is_admin, is_active, last_login, created_at, updated_at
                    """, user_data.username, user_data.email, password_hash, 
                         user_data.first_name, user_data.last_name, user_data.telephone, user_data.title, user_data.is_admin, user_data.is_active)
                    
                    # Assign role if specified
                    role_name = user_data.role or 'viewer'
                    if user_data.role:
                        role_row = await conn.fetchrow("SELECT id FROM identity.roles WHERE name = $1", user_data.role)
                        if role_row:
                            await conn.execute("""
                                INSERT INTO identity.user_roles (user_id, role_id, assigned_by)
                                VALUES ($1, $2, $3)
                            """, row['id'], role_row['id'], 1)  # Assigned by admin user (id=1)
                    
                    user = User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        telephone=row['telephone'],
                        title=row['title'],
                        is_admin=row['is_admin'],
                        is_active=row['is_active'],
                        role=role_name,
                        last_login=row['last_login'].isoformat() if row['last_login'] else None,
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "User created", "data": user}
            except Exception as e:
                self.logger.error("Failed to create user", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )

        @self.app.get("/users/{user_id}", response_model=dict)
        async def get_user(user_id: int):
            """Get user by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT u.id, u.username, u.email, u.first_name, u.last_name, 
                               u.is_admin, u.is_active, u.last_login, u.created_at, u.updated_at,
                               r.name as role_name
                        FROM identity.users u
                        LEFT JOIN identity.user_roles ur ON u.id = ur.user_id
                        LEFT JOIN identity.roles r ON ur.role_id = r.id
                        WHERE u.id = $1
                    """, user_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    # Determine role - use role_name if available, otherwise derive from is_admin
                    role = row['role_name'] if row['role_name'] else ('admin' if row['is_admin'] else 'viewer')
                    
                    user = User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        is_admin=row['is_admin'],
                        is_active=row['is_active'],
                        role=role,
                        last_login=row['last_login'].isoformat() if row['last_login'] else None,
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": user}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get user", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get user"
                )

        @self.app.put("/users/{user_id}", response_model=dict)
        async def update_user(user_id: int, user_data: UserUpdate):
            """Update user"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if user_data.username is not None:
                        updates.append(f"username = ${param_count}")
                        values.append(user_data.username)
                        param_count += 1
                    if user_data.email is not None:
                        updates.append(f"email = ${param_count}")
                        values.append(user_data.email)
                        param_count += 1
                    if user_data.password is not None:
                        updates.append(f"password_hash = ${param_count}")
                        values.append(f"hashed_{user_data.password}")
                        param_count += 1
                    if user_data.first_name is not None:
                        updates.append(f"first_name = ${param_count}")
                        values.append(user_data.first_name)
                        param_count += 1
                    if user_data.last_name is not None:
                        updates.append(f"last_name = ${param_count}")
                        values.append(user_data.last_name)
                        param_count += 1
                    if user_data.telephone is not None:
                        updates.append(f"telephone = ${param_count}")
                        values.append(user_data.telephone)
                        param_count += 1
                    if user_data.title is not None:
                        updates.append(f"title = ${param_count}")
                        values.append(user_data.title)
                        param_count += 1
                    if user_data.is_admin is not None:
                        updates.append(f"is_admin = ${param_count}")
                        values.append(user_data.is_admin)
                        param_count += 1
                    if user_data.is_active is not None:
                        updates.append(f"is_active = ${param_count}")
                        values.append(user_data.is_active)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(user_id)
                    
                    query = f"""
                        UPDATE identity.users 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, username, email, first_name, last_name, telephone, title, is_admin, is_active, last_login, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    # Handle role update if specified
                    role_name = None
                    if user_data.role is not None:
                        # Remove existing roles
                        await conn.execute("DELETE FROM identity.user_roles WHERE user_id = $1", user_id)
                        # Add new role
                        role_row = await conn.fetchrow("SELECT id FROM identity.roles WHERE name = $1", user_data.role)
                        if role_row:
                            await conn.execute("""
                                INSERT INTO identity.user_roles (user_id, role_id, assigned_by)
                                VALUES ($1, $2, $3)
                            """, user_id, role_row['id'], 1)
                            role_name = user_data.role
                    else:
                        # Get current role
                        role_row = await conn.fetchrow("""
                            SELECT r.name FROM identity.roles r
                            JOIN identity.user_roles ur ON r.id = ur.role_id
                            WHERE ur.user_id = $1
                        """, user_id)
                        role_name = role_row['name'] if role_row else ('admin' if row['is_admin'] else 'viewer')
                    
                    user = User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        telephone=row['telephone'],
                        title=row['title'],
                        is_admin=row['is_admin'],
                        is_active=row['is_active'],
                        role=role_name,
                        last_login=row['last_login'].isoformat() if row['last_login'] else None,
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "User updated", "data": user}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update user", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user"
                )

        @self.app.delete("/users/{user_id}", response_model=dict)
        async def delete_user(user_id: int):
            """Delete user"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM identity.users WHERE id = $1", user_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    return {"success": True, "message": "User deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete user", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete user"
                )

        @self.app.get("/users/roles", response_model=dict)
        async def get_available_roles():
            """Get available roles for user assignment"""
            try:
                async with self.db.pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT id, name, description 
                        FROM identity.roles 
                        ORDER BY name
                    """)
                    
                    roles = [{"id": row['id'], "name": row['name'], "description": row['description']} for row in rows]
                    return {"success": True, "data": roles}
            except Exception as e:
                self.logger.error("Failed to fetch roles", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch roles"
                )

        # ============================================================================
        # ROLE CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.get("/roles", response_model=RoleListResponse)
        async def list_roles(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all roles"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM identity.roles")
                    
                    # Get roles with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, description, permissions, created_at, updated_at
                        FROM identity.roles 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    roles = []
                    for row in rows:
                        # Handle permissions - convert from JSON string if needed
                        permissions = row['permissions'] or []
                        if isinstance(permissions, str):
                            import json
                            try:
                                permissions = json.loads(permissions)
                            except:
                                permissions = []
                        
                        roles.append(Role(
                            id=row['id'],
                            name=row['name'],
                            description=row['description'],
                            permissions=permissions,
                            is_active=True,  # Default since schema doesn't have is_active
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return RoleListResponse(
                        data=roles,
                        meta={
                            "total_items": total,
                            "skip": skip,
                            "limit": limit
                        },
                        total=total  # For backward compatibility
                    )
            except Exception as e:
                self.logger.error("Failed to fetch roles", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch roles"
                )

        @self.app.post("/roles", response_model=dict)
        async def create_role(role_data: RoleCreate):
            """Create a new role"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        INSERT INTO roles (name, description, permissions, is_active)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id, name, description, permissions, is_active, created_at, updated_at
                    """, role_data.name, role_data.description, role_data.permissions, role_data.is_active)
                    
                    role = Role(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        permissions=row['permissions'] or [],
                        is_active=row['is_active'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Role created", "data": role}
            except Exception as e:
                self.logger.error("Failed to create role", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create role"
                )

        @self.app.get("/roles/{role_id}", response_model=dict)
        async def get_role(role_id: int):
            """Get role by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, name, description, permissions, is_active, created_at, updated_at
                        FROM roles WHERE id = $1
                    """, role_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Role not found")
                    
                    role = Role(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        permissions=row['permissions'] or [],
                        is_active=row['is_active'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": role}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get role", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get role"
                )

        @self.app.put("/roles/{role_id}", response_model=dict)
        async def update_role(role_id: int, role_data: RoleUpdate):
            """Update role"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if role_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(role_data.name)
                        param_count += 1
                    if role_data.description is not None:
                        updates.append(f"description = ${param_count}")
                        values.append(role_data.description)
                        param_count += 1
                    if role_data.permissions is not None:
                        updates.append(f"permissions = ${param_count}")
                        values.append(role_data.permissions)
                        param_count += 1
                    if role_data.is_active is not None:
                        updates.append(f"is_active = ${param_count}")
                        values.append(role_data.is_active)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(role_id)
                    
                    query = f"""
                        UPDATE roles 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, description, permissions, is_active, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Role not found")
                    
                    role = Role(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        permissions=row['permissions'] or [],
                        is_active=row['is_active'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Role updated", "data": role}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update role", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update role"
                )

        @self.app.delete("/roles/{role_id}", response_model=dict)
        async def delete_role(role_id: int):
            """Delete role"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM roles WHERE id = $1", role_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Role not found")
                    
                    return {"success": True, "message": "Role deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete role", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete role"
                )

        # ============================================================================
        # USER ROLE ASSIGNMENT ENDPOINTS
        # ============================================================================
        
        @self.app.post("/users/{user_id}/roles", response_model=dict)
        async def assign_user_role(user_id: int, role_data: dict):
            """Assign role to user"""
            try:
                role_name = role_data.get('role')
                if not role_name:
                    raise HTTPException(status_code=400, detail="Role name is required")
                
                async with self.db.pool.acquire() as conn:
                    # Check if user exists
                    user_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM identity.users WHERE id = $1)", user_id
                    )
                    if not user_exists:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    # Check if role exists
                    role_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM identity.roles WHERE name = $1)", role_name
                    )
                    if not role_exists:
                        raise HTTPException(status_code=404, detail="Role not found")
                    
                    # Update user's role field
                    await conn.execute(
                        "UPDATE identity.users SET role = $1, updated_at = NOW() WHERE id = $2",
                        role_name, user_id
                    )
                    
                    # Also update is_admin field based on role
                    is_admin = role_name == 'admin'
                    await conn.execute(
                        "UPDATE identity.users SET is_admin = $1 WHERE id = $2",
                        is_admin, user_id
                    )
                    
                    return {
                        "success": True, 
                        "message": f"Role '{role_name}' assigned to user {user_id}",
                        "data": {
                            "user_id": user_id,
                            "role": role_name,
                            "is_admin": is_admin
                        }
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to assign role to user", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to assign role to user"
                )

        @self.app.get("/users/{user_id}/roles", response_model=dict)
        async def get_user_roles(user_id: int):
            """Get user's current role"""
            try:
                async with self.db.pool.acquire() as conn:
                    user_row = await conn.fetchrow(
                        "SELECT id, username, email, role, is_admin FROM identity.users WHERE id = $1",
                        user_id
                    )
                    
                    if not user_row:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    return {
                        "success": True,
                        "data": {
                            "user_id": user_row['id'],
                            "username": user_row['username'],
                            "email": user_row['email'],
                            "role": user_row['role'] or 'viewer',  # Default to viewer
                            "is_admin": user_row['is_admin']
                        }
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get user roles", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get user roles"
                )

if __name__ == "__main__":
    service = IdentityService()
    service.run()
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
    last_login: Optional[str] = None
    created_at: str
    updated_at: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False
    is_active: bool = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class UserListResponse(BaseModel):
    users: List[User]
    total: int
    skip: int
    limit: int

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
    roles: List[Role]
    total: int
    skip: int
    limit: int

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

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
                        FROM users WHERE username = $1 AND is_active = true
                    """, login_data.username)
                    
                    if not row:
                        raise HTTPException(status_code=401, detail="Invalid credentials")
                    
                    # Verify password (simplified for demo)
                    # In real implementation, use proper password hashing
                    if login_data.password != "admin123":  # Demo password
                        raise HTTPException(status_code=401, detail="Invalid credentials")
                    
                    # Update last login
                    await conn.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
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
                        expires_in=3600
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
                    total = await conn.fetchval("SELECT COUNT(*) FROM users")
                    
                    # Get users with pagination
                    rows = await conn.fetch("""
                        SELECT id, username, email, is_admin, is_active, last_login, created_at, updated_at
                        FROM users 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    users = []
                    for row in rows:
                        users.append(User(
                            id=row['id'],
                            username=row['username'],
                            email=row['email'],
                            is_admin=row['is_admin'],
                            is_active=row['is_active'],
                            last_login=row['last_login'].isoformat() if row['last_login'] else None,
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return UserListResponse(
                        users=users,
                        total=total,
                        skip=skip,
                        limit=limit
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
                    
                    row = await conn.fetchrow("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_active)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id, username, email, is_admin, is_active, last_login, created_at, updated_at
                    """, user_data.username, user_data.email, password_hash, 
                         user_data.is_admin, user_data.is_active)
                    
                    user = User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        is_admin=row['is_admin'],
                        is_active=row['is_active'],
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
                        SELECT id, username, email, is_admin, is_active, last_login, created_at, updated_at
                        FROM users WHERE id = $1
                    """, user_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    user = User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        is_admin=row['is_admin'],
                        is_active=row['is_active'],
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
                        UPDATE users 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, username, email, is_admin, is_active, last_login, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="User not found")
                    
                    user = User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        is_admin=row['is_admin'],
                        is_active=row['is_active'],
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
                        "DELETE FROM users WHERE id = $1", user_id
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
                    total = await conn.fetchval("SELECT COUNT(*) FROM roles")
                    
                    # Get roles with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, description, permissions, is_active, created_at, updated_at
                        FROM roles 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    roles = []
                    for row in rows:
                        roles.append(Role(
                            id=row['id'],
                            name=row['name'],
                            description=row['description'],
                            permissions=row['permissions'] or [],
                            is_active=row['is_active'],
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return RoleListResponse(
                        roles=roles,
                        total=total,
                        skip=skip,
                        limit=limit
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

if __name__ == "__main__":
    service = IdentityService()
    service.run()
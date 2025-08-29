#!/usr/bin/env python3
"""
Targets Service - Python FastAPI Implementation
Target management with WinRM connection testing
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
import psycopg2.extras
import requests
import winrm
import paramiko
import socket
import time
from io import StringIO
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Targets Service", version="1.0.0")

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

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
CREDENTIALS_SERVICE_URL = os.getenv("CREDENTIALS_SERVICE_URL", "http://credentials-service:3004")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Pydantic models
class TargetCreate(BaseModel):
    name: str
    hostname: str
    ip_address: Optional[str] = None
    protocol: str = "winrm"  # 'winrm', 'ssh', 'http', 'https', 'snmp', 'database'
    port: int = 5985
    os_type: str = "windows"  # 'windows', 'linux', 'unix', 'network', 'other'
    credential_ref: int  # Reference to credentials table
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
    depends_on: Optional[List[int]] = []

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    os_type: Optional[str] = None
    credential_ref: Optional[int] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    depends_on: Optional[List[int]] = None

class TargetResponse(BaseModel):
    id: int
    name: str
    hostname: str
    ip_address: Optional[str] = None
    protocol: str
    port: int
    os_type: Optional[str] = None
    credential_ref: int
    tags: List[str]
    metadata: Dict[str, Any]
    depends_on: List[int]
    created_at: datetime
    
    class Config:
        # Include None values in serialization
        exclude_none = False

class TargetListResponse(BaseModel):
    targets: List[TargetResponse]
    total: int

class WinRMTestResult(BaseModel):
    test: Dict[str, Any]
    note: str

# Target Group Models
class TargetGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    targets: List[int] = []
    tags: Optional[List[str]] = []

class TargetGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    targets: Optional[List[int]] = None
    tags: Optional[List[str]] = None

class TargetGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    targets: List[int]
    tags: List[str]
    created_at: datetime
    
class TargetGroupListResponse(BaseModel):
    groups: List[TargetGroupResponse]
    total: int

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

# Authentication
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

def require_admin_or_operator_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin or operator role"""
    if current_user["role"] not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or operator role required"
        )
    return current_user

# Helper functions
async def get_credential_data(credential_id: int, token: str) -> Dict[str, Any]:
    """Get decrypted credential data from credentials service"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{CREDENTIALS_SERVICE_URL}/credentials/{credential_id}/decrypt",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credential reference"
            )
            
        return response.json()["credential_data"]
        
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credentials service unavailable"
        )

# CRUD Operations
@app.post("/targets", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target name already exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM targets WHERE name = %s AND deleted_at IS NULL", (target_data.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target with this name already exists"
            )
        
        # Verify credential exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM credentials WHERE id = %s AND deleted_at IS NULL", (target_data.credential_ref,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credential reference"
            )
        
        # Insert target
        cursor.execute(
            """INSERT INTO targets (name, hostname, ip_address, protocol, port, os_type, credential_ref, tags, metadata, depends_on, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id, name, hostname, ip_address, protocol, port, os_type, credential_ref, tags, metadata, depends_on, created_at""",
            (
                target_data.name,
                target_data.hostname,
                target_data.ip_address,
                target_data.protocol,
                target_data.port,
                target_data.os_type,
                target_data.credential_ref,
                target_data.tags or [],  # PostgreSQL array type
                json.dumps(target_data.metadata or {}),  # JSONB type
                target_data.depends_on or [],  # PostgreSQL array type
                datetime.utcnow()
            )
        )
        
        new_target = cursor.fetchone()
        conn.commit()
        
        # Parse fields for response (only metadata needs JSON parsing)
        target_dict = dict(new_target)
        target_dict['tags'] = target_dict.get('tags', [])  # Already a list from PostgreSQL
        target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed by psycopg2 for JSONB
        target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list from PostgreSQL
        
        return TargetResponse(**target_dict)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create target"
        )
    finally:
        conn.close()

@app.get("/targets", response_model=TargetListResponse)
async def list_targets(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all targets with pagination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total count (excluding soft-deleted)
        cursor.execute("SELECT COUNT(*) FROM targets WHERE deleted_at IS NULL")
        total = cursor.fetchone()["count"]
        
        # Get targets with pagination (excluding soft-deleted)
        cursor.execute(
            """SELECT id, name, hostname, ip_address, protocol, port, os_type, credential_ref, tags, metadata, depends_on, created_at
               FROM targets 
               WHERE deleted_at IS NULL
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (limit, skip)
        )
        targets = cursor.fetchall()
        
        # Parse fields (PostgreSQL arrays are already lists, JSONB is already parsed)
        parsed_targets = []
        for target in targets:
            target_dict = dict(target)
            target_dict['tags'] = target_dict.get('tags', [])  # Already a list
            target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed 
            target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
            parsed_targets.append(target_dict)
        
        return TargetListResponse(
            targets=[TargetResponse(**target) for target in parsed_targets],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Target listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve targets"
        )
    finally:
        conn.close()

@app.get("/targets/{target_id}", response_model=TargetResponse)
async def get_target(target_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get target by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, hostname, ip_address, protocol, port, os_type, credential_ref, tags, metadata, depends_on, created_at FROM targets WHERE id = %s AND deleted_at IS NULL",
            (target_id,)
        )
        target_data = cursor.fetchone()
        
        if not target_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        # Debug logging
        logger.info(f"Raw target data: {target_data}")
        logger.info(f"Target data keys: {target_data.keys() if hasattr(target_data, 'keys') else 'No keys method'}")
        
        # Parse fields for response
        target_dict = dict(target_data)
        logger.info(f"Target dict: {target_dict}")
        target_dict['tags'] = target_dict.get('tags', [])  # Already a list
        target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed
        target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
        
        return TargetResponse(**target_dict)
        
    except Exception as e:
        logger.error(f"Target retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve target"
        )
    finally:
        conn.close()

@app.get("/debug/targets/{target_id}")
async def debug_target(target_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Debug endpoint to see raw target data"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, hostname, ip_address, protocol, port, os_type, credential_ref, tags, metadata, depends_on, created_at, deleted_at FROM targets WHERE id = %s",
            (target_id,)
        )
        target_data = cursor.fetchone()
        
        if not target_data:
            return {"error": "Target not found"}
        
        target_dict = dict(target_data)
        target_dict['tags'] = target_dict.get('tags', [])
        target_dict['metadata'] = target_dict.get('metadata', {})
        target_dict['depends_on'] = target_dict.get('depends_on', [])
        
        # Try to create TargetResponse
        try:
            target_response = TargetResponse(**target_dict)
            return {
                "raw_data": target_dict,
                "pydantic_model": target_response.dict(),
                "ip_address_in_raw": target_dict.get('ip_address'),
                "ip_address_in_model": target_response.ip_address,
                "model_dict_with_none": target_response.dict(exclude_none=False)
            }
        except Exception as model_error:
            return {
                "raw_data": target_dict,
                "model_error": str(model_error),
                "ip_address_in_raw": target_dict.get('ip_address')
            }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.put("/targets/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update target by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM targets WHERE id = %s AND deleted_at IS NULL", (target_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        # Build update query
        update_fields = []
        update_values = []
        
        if target_data.name is not None:
            update_fields.append("name = %s")
            update_values.append(target_data.name)
            
        if target_data.hostname is not None:
            update_fields.append("hostname = %s")
            update_values.append(target_data.hostname)
            
        if target_data.ip_address is not None:
            update_fields.append("ip_address = %s")
            update_values.append(target_data.ip_address)
            
        if target_data.protocol is not None:
            update_fields.append("protocol = %s")
            update_values.append(target_data.protocol)
            
        if target_data.port is not None:
            update_fields.append("port = %s")
            update_values.append(target_data.port)
            
        if target_data.os_type is not None:
            update_fields.append("os_type = %s")
            update_values.append(target_data.os_type)
            
        if target_data.credential_ref is not None:
            # Verify credential exists
            cursor.execute("SELECT id FROM credentials WHERE id = %s", (target_data.credential_ref,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid credential reference"
                )
            update_fields.append("credential_ref = %s")
            update_values.append(target_data.credential_ref)
            
        if target_data.tags is not None:
            update_fields.append("tags = %s")
            update_values.append(target_data.tags)  # PostgreSQL array type
            
        if target_data.metadata is not None:
            update_fields.append("metadata = %s")
            update_values.append(json.dumps(target_data.metadata))  # JSONB type
            
        if target_data.depends_on is not None:
            update_fields.append("depends_on = %s")
            update_values.append(target_data.depends_on)  # PostgreSQL array type
        
        if not update_fields:
            # No fields to update, just return current target
            cursor.execute(
                "SELECT id, name, hostname, ip_address, protocol, port, os_type, credential_ref, tags, metadata, depends_on, created_at FROM targets WHERE id = %s",
                (target_id,)
            )
            target = cursor.fetchone()
            target_dict = dict(target)
            target_dict['tags'] = target_dict.get('tags', [])  # Already a list
            target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed
            target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
            return TargetResponse(**target_dict)
        
        # Execute update
        update_query = f"""
            UPDATE targets 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, name, hostname, ip_address, protocol, port, os_type, credential_ref, tags, metadata, depends_on, created_at
        """
        update_values.append(target_id)
        
        cursor.execute(update_query, update_values)
        updated_target = cursor.fetchone()
        conn.commit()
        
        # Parse fields for response
        target_dict = dict(updated_target)
        target_dict['tags'] = target_dict.get('tags', [])  # Already a list
        target_dict['metadata'] = target_dict.get('metadata', {})  # Already parsed
        target_dict['depends_on'] = target_dict.get('depends_on', [])  # Already a list
        
        return TargetResponse(**target_dict)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update target"
        )
    finally:
        conn.close()

@app.delete("/targets/{target_id}")
async def delete_target(
    target_id: int,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete target by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM targets WHERE id = %s AND deleted_at IS NULL", (target_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        # Soft delete target (no need to check job references anymore)
        cursor.execute(
            "UPDATE targets SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
            (datetime.utcnow(), target_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found or already deleted"
            )
        
        conn.commit()
        
        return {"message": "Target deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete target"
        )
    finally:
        conn.close()

@app.delete("/targets/by-name/{target_name}")
async def delete_target_by_name(
    target_name: str,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete target by name"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Soft delete target by name (no need to check job references anymore)
        cursor.execute(
            "UPDATE targets SET deleted_at = %s WHERE name = %s AND deleted_at IS NULL",
            (datetime.utcnow(), target_name)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found or already deleted"
            )
        
        conn.commit()
        
        return {"message": "Target deleted successfully"}
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Target deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete target"
        )
    finally:
        conn.close()

# TARGET GROUPS - Simple grouping of existing targets
@app.get("/target-groups")
async def list_target_groups(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all target groups"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tg.id, tg.name, tg.description, tg.tags, tg.created_at,
                   COALESCE(array_agg(tgm.target_id) FILTER (WHERE tgm.target_id IS NOT NULL), ARRAY[]::integer[]) as target_ids
            FROM target_groups tg
            LEFT JOIN target_group_members tgm ON tg.id = tgm.group_id
            WHERE tg.deleted_at IS NULL
            GROUP BY tg.id, tg.name, tg.description, tg.tags, tg.created_at
            ORDER BY tg.created_at DESC
            OFFSET %s LIMIT %s
        """, (skip, limit))
        
        groups = []
        for row in cursor.fetchall():
            groups.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "targets": row["target_ids"],
                "tags": row["tags"] or [],
                "created_at": row["created_at"].isoformat()
            })
        
        cursor.execute("SELECT COUNT(*) FROM target_groups WHERE deleted_at IS NULL")
        total = cursor.fetchone()["count"]
        
        return {"groups": groups, "total": total}
    finally:
        conn.close()

@app.post("/target-groups", status_code=status.HTTP_201_CREATED)
async def create_target_group(
    group_data: dict,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new target group"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group name already exists
        cursor.execute("SELECT id FROM target_groups WHERE name = %s AND deleted_at IS NULL", (group_data["name"],))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target group with this name already exists"
            )
        
        # Create the group
        cursor.execute("""
            INSERT INTO target_groups (name, description, tags, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING id, created_at
        """, (
            group_data["name"],
            group_data.get("description"),
            group_data.get("tags", []),
            current_user["id"]
        ))
        
        result = cursor.fetchone()
        group_id = result["id"]
        created_at = result["created_at"]
        
        # Add target members
        target_ids = group_data.get("targets", [])
        if target_ids:
            for target_id in target_ids:
                cursor.execute("""
                    INSERT INTO target_group_members (group_id, target_id)
                    VALUES (%s, %s)
                """, (group_id, target_id))
        
        conn.commit()
        
        return {
            "id": group_id,
            "name": group_data["name"],
            "description": group_data.get("description"),
            "targets": target_ids,
            "tags": group_data.get("tags", []),
            "created_at": created_at.isoformat()
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Target group creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create target group"
        )
    finally:
        conn.close()

@app.get("/target-groups/{group_id}")
async def get_target_group(
    group_id: int,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get target group by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tg.id, tg.name, tg.description, tg.tags, tg.created_at,
                   COALESCE(array_agg(tgm.target_id) FILTER (WHERE tgm.target_id IS NOT NULL), ARRAY[]::integer[]) as target_ids
            FROM target_groups tg
            LEFT JOIN target_group_members tgm ON tg.id = tgm.group_id
            WHERE tg.id = %s AND tg.deleted_at IS NULL
            GROUP BY tg.id, tg.name, tg.description, tg.tags, tg.created_at
        """, (group_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target group not found"
            )
        
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "targets": row["target_ids"],
            "tags": row["tags"] or [],
            "created_at": row["created_at"].isoformat()
        }
    finally:
        conn.close()

@app.put("/target-groups/{group_id}")
async def update_target_group(
    group_id: int,
    group_data: dict,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update target group"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM target_groups WHERE id = %s AND deleted_at IS NULL", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target group not found"
            )
        
        # Update group
        cursor.execute("""
            UPDATE target_groups 
            SET name = %s, description = %s, tags = %s, updated_at = %s
            WHERE id = %s
        """, (
            group_data["name"],
            group_data.get("description"),
            group_data.get("tags", []),
            datetime.utcnow(),
            group_id
        ))
        
        # Update members
        cursor.execute("DELETE FROM target_group_members WHERE group_id = %s", (group_id,))
        target_ids = group_data.get("targets", [])
        if target_ids:
            for target_id in target_ids:
                cursor.execute("""
                    INSERT INTO target_group_members (group_id, target_id)
                    VALUES (%s, %s)
                """, (group_id, target_id))
        
        conn.commit()
        
        return {
            "id": group_id,
            "name": group_data["name"],
            "description": group_data.get("description"),
            "targets": target_ids,
            "tags": group_data.get("tags", []),
            "created_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Target group update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update target group"
        )
    finally:
        conn.close()

@app.delete("/target-groups/{group_id}")
async def delete_target_group(
    group_id: int,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete target group"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM target_groups WHERE id = %s AND deleted_at IS NULL", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target group not found"
            )
        
        # Soft delete the group
        cursor.execute(
            "UPDATE target_groups SET deleted_at = %s WHERE id = %s",
            (datetime.utcnow(), group_id)
        )
        
        # Delete group members
        cursor.execute("DELETE FROM target_group_members WHERE group_id = %s", (group_id,))
        
        conn.commit()
        return {"message": "Target group deleted successfully"}
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Target group deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete target group"
        )
    finally:
        conn.close()

@app.post("/targets/{target_id}/test-winrm", response_model=WinRMTestResult)
async def test_winrm_connection(
    target_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Test WinRM connection to target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get target info
        cursor.execute(
            "SELECT hostname, port, credential_ref, protocol FROM targets WHERE id = %s",
            (target_id,)
        )
        target_data = cursor.fetchone()
        
        if not target_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        if target_data["protocol"] != "winrm":
            return WinRMTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": "Target is not configured for WinRM protocol"
                    }
                },
                note="Target protocol is not WinRM"
            )
        
        # Get credential data for the connection
        try:
            credential_data = await get_credential_data(
                target_data["credential_ref"], 
                credentials.credentials
            )
        except Exception as e:
            return WinRMTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": f"Failed to retrieve credentials: {str(e)}"
                    }
                },
                note="Credential retrieval failed"
            )
        
        # Perform actual WinRM connection test
        try:
            # Use HTTP for port 5985, HTTPS for port 5986
            protocol = 'https' if target_data['port'] == 5986 else 'http'
            winrm_url = f"{protocol}://{target_data['hostname']}:{target_data['port']}/wsman"
            
            logger.info(f"Testing WinRM connection to: {winrm_url}")
            
            # Create WinRM session
            session = winrm.Session(
                target=winrm_url,
                auth=(credential_data['username'], credential_data['password']),
                transport='ntlm',
                server_cert_validation='ignore'
            )
            
            # Test connection with a simple command
            result = session.run_ps("$PSVersionTable.PSVersion.ToString(); whoami; hostname")
            
            if result.status_code == 0:
                # Parse output for details
                output_lines = result.std_out.decode('utf-8', errors='replace').strip().split('\n')
                ps_version = output_lines[0].strip() if len(output_lines) > 0 else "Unknown"
                whoami = output_lines[1].strip() if len(output_lines) > 1 else "Unknown"
                hostname = output_lines[2].strip() if len(output_lines) > 2 else target_data['hostname']
                
                return WinRMTestResult(
                    test={
                        "status": "success",
                        "details": {
                            "whoami": whoami,
                            "powershellVersion": ps_version,
                            "hostname": hostname,
                            "port": target_data["port"],
                            "transport": "ntlm",
                            "protocol": protocol,
                            "connection_time": "< 1s"
                        }
                    },
                    note="WinRM connection test successful"
                )
            else:
                # Connection failed
                stderr = result.std_err.decode('utf-8', errors='replace') if result.std_err else "Unknown error"
                return WinRMTestResult(
                    test={
                        "status": "error",
                        "details": {
                            "message": f"WinRM command failed with exit code {result.status_code}",
                            "stderr": stderr,
                            "hostname": target_data['hostname'],
                            "port": target_data['port']
                        }
                    },
                    note="WinRM connection established but command execution failed"
                )
                
        except Exception as winrm_error:
            logger.error(f"WinRM connection test failed: {winrm_error}")
            return WinRMTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": f"WinRM connection failed: {str(winrm_error)}",
                        "hostname": target_data['hostname'],
                        "port": target_data['port'],
                        "protocol": protocol if 'protocol' in locals() else 'unknown'
                    }
                },
                note="WinRM connection test failed - check network connectivity, credentials, and WinRM configuration"
            )
            
    except Exception as e:
        logger.error(f"Target test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test target connection"
        )
    finally:
        conn.close()

class SSHTestResult(BaseModel):
    test: Dict[str, Any]
    note: str

@app.post("/targets/{target_id}/test-ssh", response_model=SSHTestResult)
async def test_ssh_connection(
    target_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Test SSH connection to target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get target info
        cursor.execute(
            "SELECT hostname, port, credential_ref, protocol FROM targets WHERE id = %s",
            (target_id,)
        )
        target_data = cursor.fetchone()
        
        if not target_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        if target_data["protocol"] != "ssh":
            return SSHTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": "Target is not configured for SSH protocol"
                    }
                },
                note="Target protocol is not SSH"
            )
        
        # Get credential data for the connection
        try:
            credential_data = await get_credential_data(
                target_data["credential_ref"], 
                credentials.credentials
            )
        except Exception as e:
            return SSHTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": f"Failed to retrieve credentials: {str(e)}"
                    }
                },
                note="Credential retrieval failed"
            )
        
        # Perform actual SSH connection test
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Use port 22 as default for SSH if not specified
            ssh_port = target_data['port'] if target_data['port'] != 5985 else 22
            
            logger.info(f"Testing SSH connection to: {target_data['hostname']}:{ssh_port}")
            
            start_time = time.time()
            
            # Connect using username/password or SSH key
            if 'private_key' in credential_data:
                # SSH key authentication
                private_key_str = credential_data['private_key']
                passphrase = credential_data.get('private_key_passphrase')
                
                # Try different key types
                key_obj = None
                for key_class in [paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                    try:
                        key_obj = key_class.from_private_key(
                            StringIO(private_key_str), 
                            password=passphrase
                        )
                        break
                    except Exception:
                        continue
                
                if not key_obj:
                    return SSHTestResult(
                        test={
                            "status": "error",
                            "details": {
                                "message": "Invalid SSH private key format"
                            }
                        },
                        note="SSH private key could not be parsed"
                    )
                
                ssh_client.connect(
                    hostname=target_data['hostname'],
                    port=ssh_port,
                    username=credential_data['username'],
                    pkey=key_obj,
                    timeout=30
                )
            else:
                # Username/password authentication
                ssh_client.connect(
                    hostname=target_data['hostname'],
                    port=ssh_port,
                    username=credential_data['username'],
                    password=credential_data['password'],
                    timeout=30
                )
            
            connection_time = int((time.time() - start_time) * 1000)
            
            # Test connection with system information commands
            stdin, stdout, stderr = ssh_client.exec_command(
                "uname -a && whoami && hostname && cat /etc/os-release 2>/dev/null || echo 'OS info not available'"
            )
            
            stdout_data = stdout.read().decode('utf-8', errors='replace').strip()
            stderr_data = stderr.read().decode('utf-8', errors='replace').strip()
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                # Parse system information
                output_lines = stdout_data.split('\n')
                uname_info = output_lines[0] if len(output_lines) > 0 else "Unknown"
                whoami = output_lines[1] if len(output_lines) > 1 else "Unknown"
                hostname = output_lines[2] if len(output_lines) > 2 else target_data['hostname']
                
                # Parse OS information
                os_info = {}
                for line in output_lines[3:]:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os_info[key] = value.strip('"')
                
                # Store system information in database
                try:
                    cursor.execute("""
                        INSERT INTO ssh_connection_tests 
                        (target_id, status, connection_time_ms, system_info, created_by)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        target_id, 
                        'success', 
                        connection_time,
                        json.dumps({
                            "uname": uname_info,
                            "username": whoami,
                            "hostname": hostname,
                            "os_info": os_info,
                            "connection_time_ms": connection_time
                        }),
                        current_user.get('id')
                    ))
                    conn.commit()
                except Exception as db_error:
                    logger.warning(f"Failed to store SSH test result: {db_error}")
                
                return SSHTestResult(
                    test={
                        "status": "success",
                        "details": {
                            "connection_time_ms": connection_time,
                            "system_info": {
                                "uname": uname_info,
                                "username": whoami,
                                "hostname": hostname,
                                "os_distribution": os_info.get('NAME', 'Unknown'),
                                "os_version": os_info.get('VERSION', 'Unknown'),
                                "os_id": os_info.get('ID', 'Unknown')
                            },
                            "hostname": target_data['hostname'],
                            "port": ssh_port
                        }
                    },
                    note=f"SSH connection successful. Connected as {whoami} to {hostname}"
                )
            else:
                return SSHTestResult(
                    test={
                        "status": "warning",
                        "details": {
                            "connection_time_ms": connection_time,
                            "message": "SSH connection established but system command failed",
                            "stdout": stdout_data,
                            "stderr": stderr_data,
                            "exit_status": exit_status,
                            "hostname": target_data['hostname'],
                            "port": ssh_port
                        }
                    },
                    note="SSH connection established but system information retrieval failed"
                )
                
        except paramiko.AuthenticationException:
            error_msg = "SSH authentication failed - check username/password or SSH key"
            try:
                cursor.execute("""
                    INSERT INTO ssh_connection_tests 
                    (target_id, status, error_message, created_by)
                    VALUES (%s, %s, %s, %s)
                """, (target_id, 'failure', error_msg, current_user.get('id')))
                conn.commit()
            except Exception:
                pass
                
            return SSHTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": error_msg,
                        "hostname": target_data['hostname'],
                        "port": ssh_port
                    }
                },
                note="SSH authentication failed"
            )
            
        except paramiko.SSHException as ssh_error:
            error_msg = f"SSH connection failed: {str(ssh_error)}"
            try:
                cursor.execute("""
                    INSERT INTO ssh_connection_tests 
                    (target_id, status, error_message, created_by)
                    VALUES (%s, %s, %s, %s)
                """, (target_id, 'failure', error_msg, current_user.get('id')))
                conn.commit()
            except Exception:
                pass
                
            return SSHTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": error_msg,
                        "hostname": target_data['hostname'],
                        "port": ssh_port
                    }
                },
                note="SSH connection failed - check network connectivity and SSH service"
            )
            
        except socket.timeout:
            error_msg = "SSH connection timeout - check network connectivity"
            return SSHTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": error_msg,
                        "hostname": target_data['hostname'],
                        "port": ssh_port
                    }
                },
                note="SSH connection timeout"
            )
            
        except Exception as ssh_error:
            logger.error(f"SSH connection test failed: {ssh_error}")
            error_msg = f"SSH connection failed: {str(ssh_error)}"
            
            try:
                cursor.execute("""
                    INSERT INTO ssh_connection_tests 
                    (target_id, status, error_message, created_by)
                    VALUES (%s, %s, %s, %s)
                """, (target_id, 'failure', error_msg, current_user.get('id')))
                conn.commit()
            except Exception:
                pass
                
            return SSHTestResult(
                test={
                    "status": "error",
                    "details": {
                        "message": error_msg,
                        "hostname": target_data['hostname'],
                        "port": ssh_port
                    }
                },
                note="SSH connection test failed"
            )
        finally:
            try:
                ssh_client.close()
            except Exception:
                pass
            
    except Exception as e:
        logger.error(f"SSH target test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test SSH target connection"
        )
    finally:
        conn.close()

# TARGET GROUPS ENDPOINTS

@app.post("/target-groups", response_model=TargetGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_target_group(
    group_data: TargetGroupCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new target group"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group name already exists
        cursor.execute("SELECT id FROM target_groups WHERE name = %s AND deleted_at IS NULL", (group_data.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target group with this name already exists"
            )
        
        # Verify all target IDs exist
        if group_data.targets:
            cursor.execute(
                "SELECT id FROM targets WHERE id = ANY(%s) AND deleted_at IS NULL",
                (group_data.targets,)
            )
            existing_targets = [row['id'] for row in cursor.fetchall()]
            invalid_targets = set(group_data.targets) - set(existing_targets)
            if invalid_targets:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid target IDs: {list(invalid_targets)}"
                )
        
        # Insert target group
        cursor.execute(
            """INSERT INTO target_groups (name, description, tags, created_at)
               VALUES (%s, %s, %s, %s)
               RETURNING id, name, description, tags, created_at""",
            (
                group_data.name,
                group_data.description,
                group_data.tags or [],
                datetime.utcnow()
            )
        )
        
        new_group = cursor.fetchone()
        group_id = new_group['id']
        
        # Insert target group members
        if group_data.targets:
            for target_id in group_data.targets:
                cursor.execute(
                    """INSERT INTO target_group_members (group_id, target_id, created_at)
                       VALUES (%s, %s, %s)""",
                    (group_id, target_id, datetime.utcnow())
                )
        
        conn.commit()
        
        return TargetGroupResponse(
            id=new_group['id'],
            name=new_group['name'],
            description=new_group['description'],
            targets=group_data.targets or [],
            tags=new_group['tags'] or [],
            created_at=new_group['created_at']
        )
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target group creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create target group"
        )
    finally:
        conn.close()

@app.get("/target-groups", response_model=TargetGroupListResponse)
async def list_target_groups(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all target groups with pagination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM target_groups WHERE deleted_at IS NULL")
        total = cursor.fetchone()["count"]
        
        # Get target groups with pagination
        cursor.execute(
            """SELECT tg.id, tg.name, tg.description, tg.tags, tg.created_at,
                      COALESCE(array_agg(tgm.target_id) FILTER (WHERE tgm.target_id IS NOT NULL), '{}') as targets
               FROM target_groups tg
               LEFT JOIN target_group_members tgm ON tg.id = tgm.group_id
               WHERE tg.deleted_at IS NULL
               GROUP BY tg.id, tg.name, tg.description, tg.tags, tg.created_at
               ORDER BY tg.created_at DESC 
               LIMIT %s OFFSET %s""",
            (limit, skip)
        )
        groups = cursor.fetchall()
        
        # Parse groups
        parsed_groups = []
        for group in groups:
            group_dict = dict(group)
            group_dict['tags'] = group_dict.get('tags', [])
            group_dict['targets'] = [t for t in group_dict.get('targets', []) if t is not None]
            parsed_groups.append(group_dict)
        
        return TargetGroupListResponse(
            groups=[TargetGroupResponse(**group) for group in parsed_groups],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Target group listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve target groups"
        )
    finally:
        conn.close()

@app.get("/target-groups/{group_id}", response_model=TargetGroupResponse)
async def get_target_group(group_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get target group by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT tg.id, tg.name, tg.description, tg.tags, tg.created_at,
                      COALESCE(array_agg(tgm.target_id) FILTER (WHERE tgm.target_id IS NOT NULL), '{}') as targets
               FROM target_groups tg
               LEFT JOIN target_group_members tgm ON tg.id = tgm.group_id
               WHERE tg.id = %s AND tg.deleted_at IS NULL
               GROUP BY tg.id, tg.name, tg.description, tg.tags, tg.created_at""",
            (group_id,)
        )
        group_data = cursor.fetchone()
        
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target group not found"
            )
        
        group_dict = dict(group_data)
        group_dict['tags'] = group_dict.get('tags', [])
        group_dict['targets'] = [t for t in group_dict.get('targets', []) if t is not None]
        
        return TargetGroupResponse(**group_dict)
        
    except Exception as e:
        logger.error(f"Target group retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve target group"
        )
    finally:
        conn.close()

@app.put("/target-groups/{group_id}", response_model=TargetGroupResponse)
async def update_target_group(
    group_id: int,
    group_data: TargetGroupUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update target group"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM target_groups WHERE id = %s AND deleted_at IS NULL", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target group not found"
            )
        
        # Check name uniqueness if name is being updated
        if group_data.name:
            cursor.execute(
                "SELECT id FROM target_groups WHERE name = %s AND id != %s AND deleted_at IS NULL",
                (group_data.name, group_id)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Target group with this name already exists"
                )
        
        # Verify target IDs if targets are being updated
        if group_data.targets is not None:
            if group_data.targets:
                cursor.execute(
                    "SELECT id FROM targets WHERE id = ANY(%s) AND deleted_at IS NULL",
                    (group_data.targets,)
                )
                existing_targets = [row['id'] for row in cursor.fetchall()]
                invalid_targets = set(group_data.targets) - set(existing_targets)
                if invalid_targets:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid target IDs: {list(invalid_targets)}"
                    )
        
        # Update target group
        update_fields = []
        update_values = []
        
        if group_data.name is not None:
            update_fields.append("name = %s")
            update_values.append(group_data.name)
        if group_data.description is not None:
            update_fields.append("description = %s")
            update_values.append(group_data.description)
        if group_data.tags is not None:
            update_fields.append("tags = %s")
            update_values.append(group_data.tags)
        
        update_fields.append("updated_at = %s")
        update_values.append(datetime.utcnow())
        update_values.append(group_id)
        
        cursor.execute(
            f"""UPDATE target_groups SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, description, tags, created_at""",
            update_values
        )
        
        updated_group = cursor.fetchone()
        
        # Update target group members if targets are specified
        if group_data.targets is not None:
            # Delete existing members
            cursor.execute("DELETE FROM target_group_members WHERE group_id = %s", (group_id,))
            
            # Insert new members
            for target_id in group_data.targets:
                cursor.execute(
                    """INSERT INTO target_group_members (group_id, target_id, created_at)
                       VALUES (%s, %s, %s)""",
                    (group_id, target_id, datetime.utcnow())
                )
        
        # Get current targets
        cursor.execute(
            "SELECT target_id FROM target_group_members WHERE group_id = %s",
            (group_id,)
        )
        current_targets = [row['target_id'] for row in cursor.fetchall()]
        
        conn.commit()
        
        return TargetGroupResponse(
            id=updated_group['id'],
            name=updated_group['name'],
            description=updated_group['description'],
            targets=current_targets,
            tags=updated_group['tags'] or [],
            created_at=updated_group['created_at']
        )
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target group update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update target group"
        )
    finally:
        conn.close()

@app.delete("/target-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target_group(
    group_id: int,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete target group (soft delete)"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM target_groups WHERE id = %s AND deleted_at IS NULL", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target group not found"
            )
        
        # Soft delete the group
        cursor.execute(
            "UPDATE target_groups SET deleted_at = %s WHERE id = %s",
            (datetime.utcnow(), group_id)
        )
        
        # Delete group members (hard delete since they're just relationships)
        cursor.execute("DELETE FROM target_group_members WHERE group_id = %s", (group_id,))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Target group deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete target group"
        )
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "targets-service"}

@app.get("/test-endpoint")
async def test_endpoint():
    """Test endpoint to verify code execution"""
    return {"message": "Test endpoint working", "target_groups_loaded": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
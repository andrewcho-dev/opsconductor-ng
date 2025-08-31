#!/usr/bin/env python3
"""
Targets Service - Python FastAPI Implementation
Target management with simple target groups
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
import psycopg2.extras
import requests
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
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "opsconductor")
DB_PASSWORD = os.getenv("DB_PASSWORD", "opsconductor123")

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# Pydantic models
class TargetCreate(BaseModel):
    name: str
    hostname: str
    port: int
    protocol: str
    credential_ref: str
    os_type: Optional[str] = None
    tags: Optional[List[str]] = []

class Target(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    protocol: str
    credential_ref: str
    os_type: Optional[str] = None
    tags: List[str] = []
    created_at: str

class TargetListResponse(BaseModel):
    targets: List[Target]
    total: int

# Auth functions
async def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service"""
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/verify",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=5
        )
        if response.status_code == 200:
            auth_data = response.json()
            if auth_data.get("valid") and "user" in auth_data:
                return auth_data["user"]
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

async def require_admin_or_operator_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin or operator role"""
    if current_user.get("role") not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or operator role required"
        )
    return current_user

# Target endpoints
@app.get("/targets", response_model=TargetListResponse)
async def list_targets(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all targets"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, hostname, port, protocol, credential_ref, os_type, tags, created_at
            FROM targets 
            ORDER BY created_at DESC
            OFFSET %s LIMIT %s
        """, (skip, limit))
        
        targets = []
        for row in cursor.fetchall():
            targets.append(Target(
                id=row["id"],
                name=row["name"],
                hostname=row["hostname"],
                port=row["port"],
                protocol=row["protocol"],
                credential_ref=str(row["credential_ref"]),
                os_type=row["os_type"],
                tags=row["tags"] or [],
                created_at=row["created_at"].isoformat()
            ))
        
        cursor.execute("SELECT COUNT(*) FROM targets")
        total = cursor.fetchone()["count"]
        
        return TargetListResponse(targets=targets, total=total)
    finally:
        conn.close()

@app.post("/targets", response_model=Target, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO targets (name, hostname, port, protocol, credential_ref, os_type, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (
            target_data.name,
            target_data.hostname,
            target_data.port,
            target_data.protocol,
            target_data.credential_ref,
            target_data.os_type,
            target_data.tags
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        return Target(
            id=result["id"],
            name=target_data.name,
            hostname=target_data.hostname,
            port=target_data.port,
            protocol=target_data.protocol,
            credential_ref=target_data.credential_ref,
            os_type=target_data.os_type,
            tags=target_data.tags,
            created_at=result["created_at"].isoformat()
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Target creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create target"
        )
    finally:
        conn.close()



@app.get("/targets/{target_id}", response_model=Target)
async def get_target(
    target_id: int,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get target by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, hostname, port, protocol, credential_ref, os_type, tags, created_at
            FROM targets WHERE id = %s
        """, (target_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        return Target(
            id=row["id"],
            name=row["name"],
            hostname=row["hostname"],
            port=row["port"],
            protocol=row["protocol"],
            credential_ref=str(row["credential_ref"]),
            os_type=row["os_type"],
            tags=row["tags"] or [],
            created_at=row["created_at"].isoformat()
        )
    finally:
        conn.close()

@app.put("/targets/{target_id}", response_model=Target)
async def update_target(
    target_id: int,
    target_data: TargetCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE targets 
            SET name = %s, hostname = %s, port = %s, protocol = %s, 
                credential_ref = %s, os_type = %s, tags = %s, updated_at = %s
            WHERE id = %s
            RETURNING created_at
        """, (
            target_data.name,
            target_data.hostname,
            target_data.port,
            target_data.protocol,
            target_data.credential_ref,
            target_data.os_type,
            target_data.tags,
            datetime.utcnow(),
            target_id
        ))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        conn.commit()
        
        return Target(
            id=target_id,
            name=target_data.name,
            hostname=target_data.hostname,
            port=target_data.port,
            protocol=target_data.protocol,
            credential_ref=target_data.credential_ref,
            os_type=target_data.os_type,
            tags=target_data.tags,
            created_at=result["created_at"].isoformat()
        )
    except HTTPException:
        conn.rollback()
        raise
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
    """Delete target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM targets WHERE id = %s", (target_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
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



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "targets-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
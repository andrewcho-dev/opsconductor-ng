#!/usr/bin/env python3
"""
Enhanced Targets Service - Multi-Service Architecture
Supports both legacy single-service and new multi-service targets
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
import psycopg2.extras
import requests
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import our enhanced models
from models import (
    ServiceDefinition, ServiceDefinitionResponse,
    TargetServiceCreate, TargetServiceUpdate, TargetService,
    TargetCredentialCreate, TargetCredential,
    TargetCreate, TargetUpdate, Target, TargetListResponse,
    LegacyTargetCreate, LegacyTarget, LegacyTargetListResponse,
    BulkServiceOperation, BulkServiceResponse,
    MigrationStatus
)

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Enhanced Targets Service", 
    version="2.0.0",
    description="Multi-service target management with backward compatibility"
)

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

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "opsconductor"),
        user=os.getenv("DB_USER", "opsconductor"),
        password=os.getenv("DB_PASSWORD", "opsconductor123"),
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# Authentication functions
async def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token with auth service"""
    try:
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:3001")
        response = requests.get(
            f"{auth_service_url}/verify",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

async def require_admin_or_operator_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin or operator role"""
    # Handle both direct role and nested user.role formats
    user_role = current_user.get("role") or current_user.get("user", {}).get("role")
    logger.info(f"Role check - user_role: {user_role}, full user data: {current_user}")
    if user_role not in ["admin", "operator"]:
        logger.error(f"Access denied for user role: {user_role}")
        raise HTTPException(status_code=403, detail="Admin or operator role required")
    return current_user

# Helper functions
def get_target_services(conn, target_id: int) -> List[TargetService]:
    """Get all services for a target"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ts.*, sd.display_name, sd.category, sd.default_port
        FROM target_services ts
        JOIN service_definitions sd ON ts.service_type = sd.service_type
        WHERE ts.target_id = %s
        ORDER BY sd.category, sd.display_name
    """, (target_id,))
    
    services = []
    for row in cursor.fetchall():
        services.append(TargetService(
            id=row['id'],
            service_type=row['service_type'],
            display_name=row['display_name'],
            category=row['category'],
            port=row['port'],
            default_port=row['default_port'],
            is_secure=row['is_secure'],
            is_enabled=row['is_enabled'],
            is_custom_port=row['is_custom_port'],
            discovery_method=row['discovery_method'],
            connection_status=row['connection_status'] or 'unknown',
            last_checked=row['last_checked'],
            notes=row['notes'],
            created_at=row['created_at']
        ))
    
    return services

def get_target_credentials(conn, target_id: int) -> List[TargetCredential]:
    """Get all credentials for a target"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tc.id, c.credential_type, c.credential_data, c.description, tc.created_at
        FROM target_credentials tc
        JOIN credentials c ON tc.credential_id = c.id
        WHERE tc.target_id = %s AND c.deleted_at IS NULL
        ORDER BY c.credential_type, c.name
    """, (target_id,))
    
    credentials = []
    for row in cursor.fetchall():
        # Extract username from credential_data JSONB
        credential_data = row['credential_data'] or {}
        username = credential_data.get('username', 'N/A')
        
        credentials.append(TargetCredential(
            id=row['id'],
            credential_type=row['credential_type'],
            username=username,
            description=row['description'],
            created_at=row['created_at']
        ))
    
    return credentials

# ENDPOINTS

@app.get("/service-definitions", response_model=ServiceDefinitionResponse)
async def get_service_definitions():
    """Get all available service definitions"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, service_type, display_name, category, default_port, 
                   description, is_secure_by_default, is_common, created_at
            FROM service_definitions
            ORDER BY category, display_name
        """)
        
        definitions = []
        for row in cursor.fetchall():
            definitions.append(ServiceDefinition(
                id=row['id'],
                service_type=row['service_type'],
                display_name=row['display_name'],
                category=row['category'],
                default_port=row['default_port'],
                description=row['description'],
                is_secure_by_default=row['is_secure_by_default'],
                is_common=row['is_common'],
                created_at=row['created_at']
            ))
        
        return ServiceDefinitionResponse(services=definitions, total=len(definitions))
        
    except Exception as e:
        logger.error(f"Error getting service definitions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.get("/targets", response_model=TargetListResponse)
async def get_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get all targets with pagination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get total count - simplified approach
        total = 0  # We'll calculate this from the results
        
        # Get targets with pagination
        cursor.execute("""
            SELECT id, name, hostname, ip_address, os_type, os_version,
                   description, tags, created_at, updated_at
            FROM targets
            WHERE deleted_at IS NULL
            ORDER BY name
            LIMIT %s OFFSET %s
        """, (limit, skip))
        
        targets = []
        rows = cursor.fetchall()
        
        for row in rows:
            # Get services and credentials for each target
            services = get_target_services(conn, row['id'])
            credentials = get_target_credentials(conn, row['id'])
            
            targets.append(Target(
                id=row['id'],
                name=row['name'],
                hostname=row['hostname'],
                ip_address=row['ip_address'],
                os_type=row['os_type'],
                os_version=row['os_version'],
                description=row['description'],
                tags=row['tags'] or [],
                services=services,
                credentials=credentials,
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        
        # Calculate total from results for now
        total = len(targets)
        
        return TargetListResponse(
            targets=targets,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting targets: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.post("/targets", response_model=Target)
async def create_target(
    target: TargetCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create a new target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO targets (name, hostname, ip_address, os_type, os_version, description, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """, (
            target.name, target.hostname, target.ip_address,
            target.os_type, target.os_version, target.description, target.tags
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        return Target(
            id=result['id'],
            name=target.name,
            hostname=target.hostname,
            ip_address=target.ip_address,
            os_type=target.os_type,
            os_version=target.os_version,
            description=target.description,
            tags=target.tags or [],
            services=[],
            credentials=[],
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "unique constraint" in str(e).lower():
            if "hostname" in str(e).lower():
                raise HTTPException(status_code=400, detail="Hostname already exists")
            elif "ip_address" in str(e).lower():
                raise HTTPException(status_code=400, detail="IP address already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating target: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.get("/targets/{target_id}", response_model=Target)
async def get_target(
    target_id: int,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get a specific target with its services and credentials"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, hostname, ip_address, os_type, os_version,
                   description, tags, created_at, updated_at
            FROM targets WHERE id = %s AND deleted_at IS NULL
        """, (target_id,))
        
        target_row = cursor.fetchone()
        if not target_row:
            raise HTTPException(status_code=404, detail="Target not found")
        
        services = get_target_services(conn, target_id)
        credentials = get_target_credentials(conn, target_id)
        
        return Target(
            id=target_row['id'],
            name=target_row['name'],
            hostname=target_row['hostname'],
            ip_address=target_row['ip_address'],
            os_type=target_row['os_type'],
            os_version=target_row['os_version'],
            description=target_row['description'],
            tags=target_row['tags'] or [],
            services=services,
            credentials=credentials,
            created_at=target_row['created_at'],
            updated_at=target_row['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting target: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.put("/targets/{target_id}", response_model=Target)
async def update_target(
    target_id: int,
    target: TargetUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update an existing target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if target exists and is not deleted
        cursor.execute("SELECT id FROM targets WHERE id = %s AND deleted_at IS NULL", (target_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target not found")
        
        # Build dynamic update query for only provided fields
        update_fields = []
        update_values = []
        
        if target.name is not None:
            update_fields.append("name = %s")
            update_values.append(target.name)
        if target.hostname is not None:
            update_fields.append("hostname = %s")
            update_values.append(target.hostname)
        if target.ip_address is not None:
            update_fields.append("ip_address = %s")
            update_values.append(target.ip_address)
        if target.os_type is not None:
            update_fields.append("os_type = %s")
            update_values.append(target.os_type)
        if target.os_version is not None:
            update_fields.append("os_version = %s")
            update_values.append(target.os_version)
        if target.description is not None:
            update_fields.append("description = %s")
            update_values.append(target.description)
        if target.tags is not None:
            update_fields.append("tags = %s")
            update_values.append(target.tags)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        
        # Always update the updated_at timestamp
        update_fields.append("updated_at = %s")
        update_values.append(datetime.utcnow())
        update_values.append(target_id)
        
        query = f"UPDATE targets SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, update_values)
        conn.commit()
        
        # Get updated target data
        cursor.execute("""
            SELECT id, name, hostname, ip_address, os_type, os_version,
                   description, tags, created_at, updated_at
            FROM targets WHERE id = %s
        """, (target_id,))
        
        target_row = cursor.fetchone()
        services = get_target_services(conn, target_id)
        credentials = get_target_credentials(conn, target_id)
        
        return Target(
            id=target_row['id'],
            name=target_row['name'],
            hostname=target_row['hostname'],
            ip_address=target_row['ip_address'],
            os_type=target_row['os_type'],
            os_version=target_row['os_version'],
            description=target_row['description'],
            tags=target_row['tags'] or [],
            services=services,
            credentials=credentials,
            created_at=target_row['created_at'],
            updated_at=target_row['updated_at']
        )
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "unique constraint" in str(e).lower():
            if "hostname" in str(e).lower():
                raise HTTPException(status_code=400, detail="Hostname already exists")
            elif "ip_address" in str(e).lower():
                raise HTTPException(status_code=400, detail="IP address already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating target: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.delete("/targets/{target_id}")
async def delete_target(
    target_id: int,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete a target (soft delete)"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Soft delete target
        cursor.execute(
            "UPDATE targets SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
            (datetime.utcnow(), target_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404, 
                detail="Target not found or already deleted"
            )
        
        conn.commit()
        
        return {"message": "Target deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting target: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "version": "2.0.0", "features": ["multi-service", "crud-complete"]}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
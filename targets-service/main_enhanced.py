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

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
CREDENTIALS_SERVICE_URL = os.getenv("CREDENTIALS_SERVICE_URL", "http://credentials-service:3004")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres123")

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

# Helper functions
def get_target_services(conn, target_id: int) -> List[TargetService]:
    """Get all services for a target"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            ts.id, ts.service_type, sd.display_name, sd.category,
            ts.port, sd.default_port, ts.is_secure, ts.is_enabled,
            ts.is_custom_port, ts.discovery_method, ts.connection_status,
            ts.last_checked, ts.notes, ts.created_at
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
            connection_status=row['connection_status'],
            last_checked=row['last_checked'],
            notes=row['notes'],
            created_at=row['created_at']
        ))
    return services

def get_target_credentials(conn, target_id: int) -> List[TargetCredential]:
    """Get all credentials for a target"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            tc.id, tc.credential_id, c.name as credential_name,
            c.credential_type, tc.service_types, tc.is_primary, tc.created_at
        FROM target_credentials tc
        JOIN credentials c ON tc.credential_id = c.id
        WHERE tc.target_id = %s
        ORDER BY tc.is_primary DESC, c.name
    """, (target_id,))
    
    credentials = []
    for row in cursor.fetchall():
        credentials.append(TargetCredential(
            id=row['id'],
            credential_id=row['credential_id'],
            credential_name=row['credential_name'],
            credential_type=row['credential_type'],
            service_types=row['service_types'] or [],
            is_primary=row['is_primary'],
            created_at=row['created_at']
        ))
    return credentials

# SERVICE DEFINITIONS ENDPOINTS

@app.get("/service-definitions", response_model=ServiceDefinitionResponse)
async def list_service_definitions(
    category: Optional[str] = Query(None, description="Filter by category"),
    common_only: bool = Query(False, description="Show only common services"),
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all available service definitions"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        query = "SELECT * FROM service_definitions WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
            
        if common_only:
            query += " AND is_common = true"
            
        query += " ORDER BY category, display_name"
        
        cursor.execute(query, params)
        
        services = []
        for row in cursor.fetchall():
            services.append(ServiceDefinition(
                id=row['id'],
                service_type=row['service_type'],
                display_name=row['display_name'],
                category=row['category'],
                default_port=row['default_port'],
                is_secure_by_default=row['is_secure_by_default'],
                description=row['description'],
                is_common=row['is_common'],
                created_at=row['created_at']
            ))
        
        return ServiceDefinitionResponse(services=services, total=len(services))
        
    except Exception as e:
        logger.error(f"Error listing service definitions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# ENHANCED TARGET ENDPOINTS

@app.get("/targets", response_model=TargetListResponse)
async def list_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    os_type: Optional[str] = Query(None, description="Filter by OS type"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all targets with their services and credentials"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Build query with filters
        query = """
            SELECT DISTINCT t.id, t.name, t.hostname, t.ip_address, t.os_type, 
                   t.os_version, t.description, t.tags, t.created_at, t.updated_at
            FROM targets t
        """
        params = []
        where_conditions = []
        
        if os_type:
            where_conditions.append("t.os_type = %s")
            params.append(os_type)
            
        if service_type:
            query += " JOIN target_services ts ON t.id = ts.target_id"
            where_conditions.append("ts.service_type = %s AND ts.is_enabled = true")
            params.append(service_type)
            
        if tag:
            where_conditions.append("%s = ANY(t.tags)")
            params.append(tag)
            
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
            
        query += " ORDER BY t.created_at DESC OFFSET %s LIMIT %s"
        params.extend([skip, limit])
        
        cursor.execute(query, params)
        
        targets = []
        for row in cursor.fetchall():
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
        
        # Get total count
        count_query = "SELECT COUNT(DISTINCT t.id) FROM targets t"
        if service_type:
            count_query += " JOIN target_services ts ON t.id = ts.target_id"
        if where_conditions:
            count_query += " WHERE " + " AND ".join(where_conditions[:-2] if service_type else where_conditions[:-1])
        
        cursor.execute(count_query, params[:-2])
        total = cursor.fetchone()['count']
        
        return TargetListResponse(targets=targets, total=total)
        
    except Exception as e:
        logger.error(f"Error listing targets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.post("/targets", response_model=Target)
async def create_target(
    target: TargetCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create a new target with services and credentials"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create target
        cursor.execute("""
            INSERT INTO targets (name, hostname, ip_address, os_type, os_version, description, tags, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            target.name, target.hostname, target.ip_address, target.os_type,
            target.os_version, target.description, target.tags, datetime.utcnow()
        ))
        
        target_id = cursor.fetchone()['id']
        
        # Create services
        for service in target.services:
            # Check if port is custom
            cursor.execute("""
                SELECT default_port FROM service_definitions WHERE service_type = %s
            """, (service.service_type,))
            
            default_port_row = cursor.fetchone()
            if not default_port_row:
                raise HTTPException(status_code=400, detail=f"Unknown service type: {service.service_type}")
                
            is_custom_port = service.port != default_port_row['default_port']
            
            cursor.execute("""
                INSERT INTO target_services 
                (target_id, service_type, port, is_secure, is_enabled, is_custom_port, discovery_method, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                target_id, service.service_type, service.port, service.is_secure,
                service.is_enabled, is_custom_port, 'manual', datetime.utcnow()
            ))
        
        # Create credential assignments
        for cred in target.credentials:
            cursor.execute("""
                INSERT INTO target_credentials 
                (target_id, credential_id, service_types, is_primary, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                target_id, cred.credential_id, cred.service_types,
                cred.is_primary, datetime.utcnow()
            ))
        
        conn.commit()
        
        # Return the created target with services and credentials
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
            raise HTTPException(status_code=400, detail="Target name already exists")
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
            FROM targets WHERE id = %s
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

# SERVICE MANAGEMENT ENDPOINTS

@app.post("/targets/{target_id}/services", response_model=TargetService)
async def add_service_to_target(
    target_id: int,
    service: TargetServiceCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Add a service to a target"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify target exists
        cursor.execute("SELECT id FROM targets WHERE id = %s", (target_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target not found")
        
        # Get service definition
        cursor.execute("""
            SELECT default_port, display_name, category 
            FROM service_definitions WHERE service_type = %s
        """, (service.service_type,))
        
        service_def = cursor.fetchone()
        if not service_def:
            raise HTTPException(status_code=400, detail=f"Unknown service type: {service.service_type}")
        
        is_custom_port = service.port != service_def['default_port']
        
        # Create service
        cursor.execute("""
            INSERT INTO target_services 
            (target_id, service_type, port, is_secure, is_enabled, is_custom_port, 
             discovery_method, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            target_id, service.service_type, service.port, service.is_secure,
            service.is_enabled, is_custom_port, 'manual', service.notes, datetime.utcnow()
        ))
        
        service_id = cursor.fetchone()['id']
        conn.commit()
        
        return TargetService(
            id=service_id,
            service_type=service.service_type,
            display_name=service_def['display_name'],
            category=service_def['category'],
            port=service.port,
            default_port=service_def['default_port'],
            is_secure=service.is_secure,
            is_enabled=service.is_enabled,
            is_custom_port=is_custom_port,
            discovery_method='manual',
            connection_status='unknown',
            last_checked=None,
            notes=service.notes,
            created_at=datetime.utcnow()
        )
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Service already exists on this target")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding service to target: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

# MIGRATION ENDPOINT

@app.post("/migrate-schema", response_model=MigrationStatus)
async def migrate_schema(
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Migrate existing single-service targets to multi-service schema"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required for migration")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT migrate_old_targets_to_new_schema()")
        result = cursor.fetchone()
        conn.commit()
        
        return MigrationStatus(
            success=True,
            services_created=0,  # Parse from result if needed
            credentials_created=0,  # Parse from result if needed
            message=result[0] if result else "Migration completed"
        )
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during migration: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
    finally:
        conn.close()

# HEALTH CHECK
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "version": "2.0.0", "features": ["multi-service", "legacy-compatibility"]}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
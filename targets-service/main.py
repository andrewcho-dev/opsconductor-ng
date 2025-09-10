#!/usr/bin/env python3
"""
Enhanced Targets Service - Multi-Service Architecture
Supports both legacy single-service and new multi-service targets
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add shared module to path
sys.path.append('/home/opsconductor')

from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
from dotenv import load_dotenv

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool, get_database_metrics
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, PaginatedResponse, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from shared.auth import require_admin_role
from shared.utils import get_service_client

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

# Setup structured logging
setup_service_logging("targets-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("targets-service")

# FastAPI app
app = FastAPI(
    title="Enhanced Targets Service", 
    version="2.0.0",
    description="Multi-service target management with backward compatibility"
)

# Add standard middleware
add_standard_middleware(app, "targets-service", version="2.0.0")

# Database connection is now handled by shared.database module

def get_user_from_headers(request: Request):
    """Extract user info from nginx headers (set by gateway authentication)"""
    return {
        "id": request.headers.get("X-User-ID"),
        "username": request.headers.get("X-Username"),
        "email": request.headers.get("X-User-Email"),
        "role": request.headers.get("X-User-Role")
    }

# Auth is now handled at nginx gateway level - no internal auth checks needed

# Helper functions
def get_target_services(target_id: int) -> List[TargetService]:
    """Get all services for a target"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT ts.*, sd.display_name, sd.category, sd.default_port, c.name as credential_name
            FROM target_services ts
            JOIN service_definitions sd ON ts.service_type = sd.service_type
            LEFT JOIN credentials c ON ts.credential_id = c.id
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
                credential_id=row['credential_id'],
                credential_name=row['credential_name'],
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

def get_target_credentials(target_id: int) -> List[TargetCredential]:
    """Get all credentials for a target"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT tc.id, tc.credential_id, c.name as credential_name, 
                   c.credential_type, tc.service_types, tc.is_primary, tc.created_at
            FROM target_credentials tc
            JOIN credentials c ON tc.credential_id = c.id
            WHERE tc.target_id = %s AND c.deleted_at IS NULL
            ORDER BY c.credential_type, c.name
        """, (target_id,))
        
        credentials = []
        for row in cursor.fetchall():
            credentials.append(TargetCredential(
                id=row['id'],
                credential_id=row['credential_id'],
                credential_name=row['credential_name'],
                credential_type=row['credential_type'],
                service_types=row['service_types'] or [],
                is_primary=row['is_primary'] or False,
                created_at=row['created_at']
            ))
        
        return credentials

# ENDPOINTS

@app.get("/service-definitions", response_model=ServiceDefinitionResponse)
async def get_service_definitions() -> Dict[str, Any]:
    """Get all available service definitions"""
    try:
        with get_db_cursor(commit=False) as cursor:
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
        raise handle_database_error(e, "get service definitions")

@app.get("/targets", response_model=TargetListResponse)
async def get_targets(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all targets with pagination"""
    try:
        with get_db_cursor(commit=False) as cursor:
            # Get total count first
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM targets
                WHERE deleted_at IS NULL
            """)
            total_result = cursor.fetchone()
            total = total_result['total'] if total_result else 0
            
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
                services = get_target_services(row['id'])
                credentials = get_target_credentials(row['id'])
                
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
        raise handle_database_error(e, "get targets")

@app.post("/targets", response_model=Target)
async def create_target(
    target: TargetCreate,
    request: Request
):
    """Create a new target"""
    # Auth handled at nginx gateway level
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO targets (name, hostname, ip_address, os_type, os_version, description, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at, updated_at
            """, (
                target.name, target.hostname, target.ip_address,
                target.os_type, target.os_version, target.description, target.tags
            ))
            
            result = cursor.fetchone()
            target_id = result['id']
            
            # Handle services if provided
            if target.services:
                for service in target.services:
                    cursor.execute("""
                        INSERT INTO target_services 
                        (target_id, service_type, port, credential_id, is_secure, is_enabled, notes, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        target_id, service.service_type, service.port, service.credential_id,
                        service.is_secure, service.is_enabled, service.notes,
                        datetime.utcnow()
                    ))
                    
                    # Create credential association if credential_id is provided
                    if service.credential_id:
                        cursor.execute("""
                            INSERT INTO target_credentials (target_id, credential_id, service_types, is_primary, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (target_id, credential_id) DO UPDATE SET
                            service_types = CASE 
                                WHEN %s = ANY(target_credentials.service_types) THEN target_credentials.service_types
                                ELSE array_append(target_credentials.service_types, %s)
                            END
                        """, (
                            target_id, service.credential_id, [service.service_type], False, datetime.utcnow(),
                            service.service_type, service.service_type
                        ))
            
            # Get services and credentials for the response
            services = get_target_services(target_id)
            credentials = get_target_credentials(target_id)
            
            return Target(
                id=result['id'],
                name=target.name,
                hostname=target.hostname,
                ip_address=target.ip_address,
                os_type=target.os_type,
                os_version=target.os_version,
                description=target.description,
                tags=target.tags or [],
                services=services,
                credentials=credentials,
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        
    except Exception as e:
        import psycopg2
        if isinstance(e, psycopg2.IntegrityError):
            if "unique constraint" in str(e).lower():
                if "hostname" in str(e).lower():
                    raise ValidationError("Hostname already exists", "hostname")
                elif "ip_address" in str(e).lower():
                    raise ValidationError("IP address already exists", "ip_address")
            raise ValidationError("Database constraint violation")
        logger.error(f"Error creating target: {e}")
        raise handle_database_error(e, "create target")

@app.get("/targets/{target_id}", response_model=Target)
async def get_target(
    target_id: int,
    request: Request
):
    """Get a specific target with its services and credentials"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, name, hostname, ip_address, os_type, os_version,
                       description, tags, created_at, updated_at
                FROM targets WHERE id = %s AND deleted_at IS NULL
            """, (target_id,))
            
            target_row = cursor.fetchone()
            if not target_row:
                raise NotFoundError("Target", target_id)
            
            # Get services and credentials
            services = get_target_services(target_id)
            credentials = get_target_credentials(target_id)
            
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
        raise handle_database_error(e, "get target")

@app.put("/targets/{target_id}", response_model=Target)
async def update_target(
    target_id: int,
    target: TargetUpdate,
    request: Request
):
    """Update an existing target"""
    # Auth handled at nginx gateway level
    logger.info(f"Updating target {target_id} with data: {target.dict()}")
    try:
        with get_db_cursor() as cursor:
            # Check if target exists and is not deleted
            cursor.execute("SELECT id FROM targets WHERE id = %s AND deleted_at IS NULL", (target_id,))
            if not cursor.fetchone():
                raise NotFoundError("Target", target_id)
            
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
                raise ValidationError("No fields provided for update")
            
            # Always update the updated_at timestamp
            update_fields.append("updated_at = %s")
            update_values.append(datetime.utcnow())
            update_values.append(target_id)
            
            query = f"UPDATE targets SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, update_values)
            
            # Handle services update if provided
            if target.services is not None:
                # Delete existing services for this target
                cursor.execute("DELETE FROM target_services WHERE target_id = %s", (target_id,))
                
                # Clear existing credential associations (we'll recreate them)
                cursor.execute("DELETE FROM target_credentials WHERE target_id = %s", (target_id,))
                
                # Add new services
                for service in target.services:
                    cursor.execute("""
                        INSERT INTO target_services 
                        (target_id, service_type, port, credential_id, is_secure, is_enabled, notes, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    target_id, service.service_type, service.port, service.credential_id,
                    service.is_secure, service.is_enabled, service.notes,
                    datetime.utcnow()
                ))
                
                # Create credential association if credential_id is provided
                if service.credential_id:
                    cursor.execute("""
                        INSERT INTO target_credentials (target_id, credential_id, service_types, is_primary, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (target_id, credential_id) DO UPDATE SET
                        service_types = CASE 
                            WHEN %s = ANY(target_credentials.service_types) THEN target_credentials.service_types
                            ELSE array_append(target_credentials.service_types, %s)
                        END
                    """, (
                        target_id, service.credential_id, [service.service_type], False, datetime.utcnow(),
                        service.service_type, service.service_type
                    ))
            
            # Get updated target data
            cursor.execute("""
                SELECT id, name, hostname, ip_address, os_type, os_version,
                       description, tags, created_at, updated_at
                FROM targets WHERE id = %s
            """, (target_id,))
            
            target_row = cursor.fetchone()
            
            # Get services and credentials
            services = get_target_services(target_id)
            credentials = get_target_credentials(target_id)
        
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
        
    except Exception as e:
        import psycopg2
        if isinstance(e, psycopg2.IntegrityError):
            if "unique constraint" in str(e).lower():
                if "hostname" in str(e).lower():
                    raise ValidationError("Hostname already exists", "hostname")
                elif "ip_address" in str(e).lower():
                    raise ValidationError("IP address already exists", "ip_address")
            raise ValidationError("Database constraint violation")
        elif isinstance(e, HTTPException):
            raise
        logger.error(f"Error updating target: {e}")
        raise handle_database_error(e, "update target")

@app.delete("/targets/{target_id}")
async def delete_target(
    target_id: int,
    request: Request
):
    """Delete a target (soft delete)"""
    # Auth handled at nginx gateway level
    try:
        with get_db_cursor() as cursor:
            # Soft delete target
            cursor.execute(
                "UPDATE targets SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
                (datetime.utcnow(), target_id)
            )
            
            if cursor.rowcount == 0:
                raise NotFoundError("Target not found or already deleted")
            
            return create_success_response(
                message="Target deleted successfully",
                data={"target_id": target_id}
            )
        
    except (NotFoundError, ValidationError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Error deleting target: {e}")
        raise handle_database_error(e, "Failed to delete target")

# CREDENTIAL MANAGEMENT ENDPOINTS

@app.post("/targets/{target_id}/credentials", response_model=TargetCredential)
async def add_credential_to_target(
    target_id: int,
    credential: TargetCredentialCreate,
    request: Request
):
    """Add a credential to a target"""
    # Auth handled at nginx gateway level
    try:
        with get_db_cursor() as cursor:
            # Verify target exists
            cursor.execute("SELECT id FROM targets WHERE id = %s", (target_id,))
            if not cursor.fetchone():
                raise NotFoundError("Target", target_id)
            
            # Verify credential exists
            cursor.execute("SELECT id, name, credential_type FROM credentials WHERE id = %s", (credential.credential_id,))
            cred_data = cursor.fetchone()
            if not cred_data:
                raise NotFoundError("Credential", credential.credential_id)
            
            # Create target credential association
            cursor.execute("""
                INSERT INTO target_credentials 
                (target_id, credential_id, service_types, is_primary, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                target_id, credential.credential_id, credential.service_types,
                credential.is_primary, datetime.utcnow()
            ))
            
            tc_id = cursor.fetchone()['id']
        
            return TargetCredential(
                id=tc_id,
                credential_id=credential.credential_id,
                credential_name=cred_data['name'],
                credential_type=cred_data['credential_type'],
                service_types=credential.service_types,
                is_primary=credential.is_primary,
                created_at=datetime.utcnow()
            )
        
    except Exception as e:
        import psycopg2
        if isinstance(e, psycopg2.IntegrityError):
            if "unique constraint" in str(e).lower():
                raise ValidationError("Credential already associated with this target")
            raise ValidationError("Database constraint violation")
        elif isinstance(e, HTTPException):
            raise
        logger.error(f"Error adding credential to target: {e}")
        raise handle_database_error(e, "add credential to target")

@app.put("/targets/{target_id}/credentials/{credential_id}", response_model=TargetCredential)
async def update_target_credential(
    target_id: int,
    credential_id: int,
    credential: TargetCredentialCreate,
    request: Request
):
    """Update a credential association on a target"""
    # Auth handled at nginx gateway level
    try:
        with get_db_cursor() as cursor:
            # Verify target credential exists
            cursor.execute("""
                SELECT tc.id, c.name, c.credential_type
                FROM target_credentials tc
                JOIN credentials c ON tc.credential_id = c.id
                WHERE tc.target_id = %s AND tc.credential_id = %s
            """, (target_id, credential_id))
            
            tc_data = cursor.fetchone()
            if not tc_data:
                raise NotFoundError("Target credential association", f"{target_id}-{credential_id}")
            
            # Update target credential
            cursor.execute("""
                UPDATE target_credentials 
                SET service_types = %s, is_primary = %s
                WHERE target_id = %s AND credential_id = %s
            """, (
                credential.service_types, credential.is_primary, target_id, credential_id
            ))
        
            return TargetCredential(
                id=tc_data['id'],
                credential_id=credential_id,
                credential_name=tc_data['name'],
                credential_type=tc_data['credential_type'],
                service_types=credential.service_types,
                is_primary=credential.is_primary,
                created_at=datetime.utcnow()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating target credential: {e}")
        raise handle_database_error(e, "update target credential")

@app.delete("/targets/{target_id}/credentials/{credential_id}")
async def delete_target_credential(
    target_id: int,
    credential_id: int,
    request: Request
):
    """Remove a credential association from a target"""
    # Auth handled at nginx gateway level
    try:
        with get_db_cursor() as cursor:
            # Verify target credential exists
            cursor.execute("""
                SELECT id FROM target_credentials 
                WHERE target_id = %s AND credential_id = %s
            """, (target_id, credential_id))
            
            if not cursor.fetchone():
                raise NotFoundError("Target credential association not found")
            
            # Delete target credential
            cursor.execute("""
                DELETE FROM target_credentials 
                WHERE target_id = %s AND credential_id = %s
            """, (target_id, credential_id))
            
            return create_success_response(
                message="Credential association deleted successfully",
                data={
                    "target_id": target_id,
                    "credential_id": credential_id
                }
            )
        
    except (NotFoundError, ValidationError, PermissionError):
        raise
    except Exception as e:
        logger.error(f"Error deleting target credential: {e}")
        raise handle_database_error(e, "Failed to delete target credential association")

@app.post("/targets/services/{service_id}/test")
async def test_service_connection(
    service_id: int,
    request: Request
):
    """Test connection to a specific service"""
    # Auth handled at nginx gateway level
    logger.info(f"Starting test connection for service_id: {service_id}")
    try:
        with get_db_cursor() as cursor:
            logger.info("Database connection established, creating cursor")
            
            # Get service details with target info
            logger.info(f"Querying service details for service_id: {service_id}")
            cursor.execute("""
                SELECT 
                    ts.id, ts.service_type, ts.port, ts.is_secure, ts.is_enabled,
                    t.hostname, t.ip_address,
                    c.username, c.password, c.private_key, c.credential_type
                FROM target_services ts
                JOIN targets t ON ts.target_id = t.id
                LEFT JOIN credentials c ON ts.credential_id = c.id
                WHERE ts.id = %s AND ts.is_enabled = true
            """, (service_id,))
            
            service = cursor.fetchone()
            logger.info(f"Service query result: {service}")
            if not service:
                raise NotFoundError("Service", service_id)
        
        # Basic connection test based on service type
        target_host = service['ip_address'] or service['hostname']
        port = service['port']
        service_type = service['service_type']
        
        logger.info(f"Testing connection to {service_type} on {target_host}:{port}")
        
        # Import socket for basic connectivity test
        import socket
        import time
        
        success = False
        message = ""
        
        try:
            # Basic TCP port connectivity test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            result = sock.connect_ex((target_host, port))
            sock.close()
            
            if result == 0:
                success = True
                message = f"Port {port} is open and accepting connections"
                status = 'connected'
            else:
                success = False
                message = f"Port {port} is not accessible (connection refused)"
                status = 'failed'
                
        except socket.gaierror as e:
            success = False
            message = f"DNS resolution failed: {str(e)}"
            status = 'failed'
        except Exception as e:
            success = False
            message = f"Connection test failed: {str(e)}"
            status = 'failed'
        
        # Update connection status in database
        with get_db_cursor() as update_cursor:
            logger.info(f"Updating connection status to '{status}' for service_id: {service_id}")
            update_cursor.execute("""
                UPDATE target_services 
                SET connection_status = %s, last_checked = %s
                WHERE id = %s
            """, (status, datetime.utcnow().isoformat(), service_id))
        
        return {
            "success": success,
            "message": message,
            "service_type": service_type,
            "target": target_host,
            "port": port,
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing service connection: {e}")
        raise handle_database_error(e, "test service connection")

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with database connectivity"""
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
        service="targets-service",
        status=overall_status,
        version="2.0.0",
        checks=checks
    )

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "targets-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

@app.on_event("startup")
async def startup_event() -> None:
    """Log service startup"""
    log_startup("targets-service", "2.0.0", 3005)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up database connections on shutdown"""
    log_shutdown("targets-service")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
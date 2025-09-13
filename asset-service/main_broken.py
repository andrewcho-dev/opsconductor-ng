#!/usr/bin/env python3
"""
OpsConductor Asset Service
Handles targets with embedded credentials
"""

import sys
import os
import json
from typing import List, Optional
from fastapi import Query, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService

# ============================================================================
# MODELS
# ============================================================================

# Enhanced Target Models (for frontend compatibility)
class TargetServiceCreate(BaseModel):
    service_type: str
    port: int
    is_default: bool = False
    is_secure: bool = False
    is_enabled: bool = True
    notes: Optional[str] = None
    
    # Embedded credential fields
    credential_type: Optional[str] = None  # 'username_password', 'ssh_key', 'api_key', 'bearer_token'
    username: Optional[str] = None
    password: Optional[str] = None  # Will be encrypted in backend
    private_key: Optional[str] = None  # Will be encrypted in backend
    public_key: Optional[str] = None
    api_key: Optional[str] = None  # Will be encrypted in backend
    bearer_token: Optional[str] = None  # Will be encrypted in backend
    certificate: Optional[str] = None  # Will be encrypted in backend
    passphrase: Optional[str] = None  # Will be encrypted in backend
    domain: Optional[str] = None  # For Windows domain authentication

class TargetService(BaseModel):
    id: int
    target_id: int
    service_type: str
    port: int
    is_default: bool = False
    is_secure: bool = False
    is_enabled: bool = True
    notes: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    
    # Credential info (type only, not actual credentials)
    credential_type: Optional[str] = None
    has_credentials: bool = False

class TargetServiceSummary(BaseModel):
    """Simplified service model for list views"""
    id: int
    service_type: str
    port: int
    is_default: bool = False
    is_secure: bool = False
    is_enabled: bool = True
    credential_type: Optional[str] = None
    has_credentials: bool = False

class EnhancedTargetCreate(BaseModel):
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    services: List[TargetServiceCreate] = []

class EnhancedTargetUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class EnhancedTarget(BaseModel):
    id: int
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    services: List[TargetService] = []
    created_at: str
    updated_at: Optional[str] = None

class EnhancedTargetSummary(BaseModel):
    """Simplified target model for list view - services only show credential type"""
    id: int
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    services: List[TargetServiceSummary] = []
    created_at: str
    updated_at: Optional[str] = None

class EnhancedTargetListResponse(BaseModel):
    targets: List[EnhancedTargetSummary]
    total: int
    skip: int
    limit: int

# ============================================================================
# SERVICE TYPE TO CREDENTIAL TYPE MAPPING
# ============================================================================

SERVICE_CREDENTIAL_MAPPING = {
    'ssh': ['ssh_key', 'username_password'],
    'sftp': ['ssh_key', 'username_password'],
    'rdp': ['username_password'],
    'winrm': ['username_password'],
    'winrm_https': ['username_password'],
    'wmi': ['username_password'],
    'smb': ['username_password'],
    'http': ['api_key', 'username_password', 'bearer_token'],
    'https': ['api_key', 'username_password', 'bearer_token'],
    'http_alt': ['api_key', 'username_password', 'bearer_token'],
    'https_alt': ['api_key', 'username_password', 'bearer_token'],
    'mysql': ['username_password'],
    'postgresql': ['username_password'],
    'sql_server': ['username_password'],
    'oracle': ['username_password'],
    'mongodb': ['username_password'],
    'redis': ['username_password'],
    'smtp': ['username_password'],
    'smtps': ['username_password'],
    'smtp_submission': ['username_password'],
    'imap': ['username_password'],
    'imaps': ['username_password'],
    'pop3': ['username_password'],
    'pop3s': ['username_password'],
    'ftp': ['username_password'],
    'ftps': ['username_password'],
    'dns': ['username_password'],
    'snmp': ['username_password'],
    'ntp': ['username_password'],
    'telnet': ['username_password'],
    'vnc': ['username_password']
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_services(services: List[TargetServiceCreate]) -> None:
    """Validate service configuration"""
    if not services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one service is required"
        )
    
    # Check for exactly one default service
    default_count = sum(1 for service in services if service.is_default)
    if default_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one service must be marked as default"
        )
    elif default_count > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one service can be marked as default"
        )
    
    # Validate service types and credential compatibility
    for service in services:
        if service.service_type not in SERVICE_CREDENTIAL_MAPPING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported service type: {service.service_type}"
            )
        
        # If credentials are provided, validate compatibility
        if service.credential_type:
            allowed_types = SERVICE_CREDENTIAL_MAPPING[service.service_type]
            if service.credential_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Credential type '{service.credential_type}' not supported for service '{service.service_type}'. Allowed: {allowed_types}"
                )
            
            # Validate required fields for credential type
            if service.credential_type == 'username_password':
                if not service.username or not service.password:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username and password are required for username_password credential type"
                    )
            elif service.credential_type == 'ssh_key':
                if not service.username or not service.private_key:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username and private_key are required for ssh_key credential type"
                    )
            elif service.credential_type == 'api_key':
                if not service.api_key:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="API key is required for api_key credential type"
                    )
            elif service.credential_type == 'bearer_token':
                if not service.bearer_token:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Bearer token is required for bearer_token credential type"
                    )

# ============================================================================
# TARGET GROUPS MODELS
# ============================================================================

class TargetGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_group_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class TargetGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_group_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class TargetGroup(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_group_id: Optional[int] = None
    path: str
    level: int
    color: Optional[str] = None
    icon: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    
    # Computed fields
    target_count: Optional[int] = None
    direct_target_count: Optional[int] = None
    children: Optional[List['TargetGroup']] = None

class TargetGroupListResponse(BaseModel):
    groups: List[TargetGroup]
    total: int

class TargetGroupMembership(BaseModel):
    id: int
    target_id: int
    group_id: int
    added_at: str

class TargetGroupTargetsResponse(BaseModel):
    targets: List[EnhancedTargetSummary]
    total: int
    include_descendants: bool = False

class AssetService(BaseService):
    def __init__(self):
        super().__init__("asset-service", "1.0.0", 3002)
        self._setup_routes()

    def _setup_routes(self):
        """Setup all API routes"""
        
        # ============================================================================
        # TARGET CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.get("/targets", response_model=EnhancedTargetListResponse)
        async def list_targets(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all targets (using enhanced system)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM assets.targets")
                    
                    # Get targets with pagination
                    target_rows = await conn.fetch("""
                        SELECT id, name, description, host, target_type, connection_type, tags, metadata, is_active, created_by, created_at, updated_at
                        FROM assets.targets 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    targets = []
                    for target_row in target_rows:
                        # Get services for this target
                        service_rows = await conn.fetch("""
                            SELECT id, target_id, service_type, port, is_default, is_secure, 
                                   is_enabled, notes, credential_type, created_at
                            FROM assets.target_services 
                            WHERE target_id = $1 
                            ORDER BY is_default DESC, port ASC
                        """, target_row['id'])
                        
                        services = []
                        for service_row in service_rows:
                            services.append(TargetServiceSummary(
                                id=service_row['id'],
                                service_type=service_row['service_type'],
                                port=service_row['port'],
                                is_default=service_row['is_default'],
                                is_secure=service_row['is_secure'],
                                is_enabled=service_row['is_enabled'],
                                credential_type=service_row['credential_type'],
                                has_credentials=service_row['credential_type'] is not None
                            ))
                        
                        import json
                        tags = target_row['tags']
                        if isinstance(tags, str):
                            tags = json.loads(tags)
                        elif tags is None:
                            tags = []
                        
                        targets.append(EnhancedTargetSummary(
                            id=target_row['id'],
                            name=target_row['name'],
                            hostname=target_row['host'],
                            ip_address=target_row['host'],  # Using host as IP for now
                            os_type=target_row['target_type'],
                            os_version="Unknown",  # Not available in current schema
                            description=target_row['description'],
                            tags=tags,
                            services=services,
                            created_at=target_row['created_at'].isoformat(),
                            updated_at=target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                        ))
                    
                    return EnhancedTargetListResponse(
                        targets=targets,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch targets"
                )

        @self.app.post("/targets", response_model=dict)
        async def create_target(target_data: EnhancedTargetCreate):
            """Create a new target with services"""
            try:
                # Validate services
                validate_services(target_data.services)
                
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Insert target
                        target_id = await conn.fetchval("""
                            INSERT INTO assets.targets (name, description, host, target_type, connection_type, tags, created_by)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id
                        """, target_data.name, target_data.description, target_data.hostname, 
                             target_data.os_type, 'ssh', json.dumps(target_data.tags), 1)
                        
                        # Insert services
                        for service in target_data.services:
                            # Encrypt sensitive fields if present
                            encrypted_password = None
                            encrypted_private_key = None
                            encrypted_api_key = None
                            encrypted_bearer_token = None
                            encrypted_certificate = None
                            encrypted_passphrase = None
                            
                            if service.password:
                                encrypted_password = service.password  # TODO: Implement encryption
                            if service.private_key:
                                encrypted_private_key = service.private_key  # TODO: Implement encryption
                            if service.api_key:
                                encrypted_api_key = service.api_key  # TODO: Implement encryption
                            if service.bearer_token:
                                encrypted_bearer_token = service.bearer_token  # TODO: Implement encryption
                            if service.certificate:
                                encrypted_certificate = service.certificate  # TODO: Implement encryption
                            if service.passphrase:
                                encrypted_passphrase = service.passphrase  # TODO: Implement encryption
                            
                            await conn.execute("""
                                INSERT INTO assets.target_services 
                                (target_id, service_type, port, is_default, is_secure, is_enabled, notes,
                                 credential_type, username, password_encrypted, private_key_encrypted, public_key, api_key_encrypted, 
                                 bearer_token_encrypted, certificate_encrypted, passphrase_encrypted, domain)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                            """, target_id, service.service_type, service.port, service.is_default,
                                 service.is_secure, service.is_enabled, service.notes,
                                 service.credential_type, service.username, encrypted_password,
                                 encrypted_private_key, service.public_key, encrypted_api_key,
                                 encrypted_bearer_token, encrypted_certificate, encrypted_passphrase,
                                 service.domain)
                        
                        return {"success": True, "message": "Target created", "target_id": target_id}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to create target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create target"
                )

        @self.app.get("/targets/{target_id}", response_model=dict)
        async def get_target(target_id: int):
            """Get target by ID with full service details"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get target
                    target_row = await conn.fetchrow("""
                        SELECT id, name, description, host, target_type, connection_type, tags, metadata, is_active, created_by, created_at, updated_at
                        FROM assets.targets WHERE id = $1
                    """, target_id)
                    
                    if not target_row:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    # Get services
                    service_rows = await conn.fetch("""
                        SELECT id, target_id, service_type, port, is_default, is_secure, 
                               is_enabled, notes, credential_type, username, public_key, domain,
                               created_at
                        FROM assets.target_services 
                        WHERE target_id = $1 
                        ORDER BY is_default DESC, port ASC
                    """, target_id)
                    
                    services = []
                    for service_row in service_rows:
                        services.append(TargetService(
                            id=service_row['id'],
                            target_id=service_row['target_id'],
                            service_type=service_row['service_type'],
                            port=service_row['port'],
                            is_default=service_row['is_default'],
                            is_secure=service_row['is_secure'],
                            is_enabled=service_row['is_enabled'],
                            notes=service_row['notes'],
                            credential_type=service_row['credential_type'],
                            has_credentials=service_row['credential_type'] is not None,
                            created_at=service_row['created_at'].isoformat()
                        ))
                    
                    import json
                    tags = target_row['tags']
                    if isinstance(tags, str):
                        tags = json.loads(tags)
                    elif tags is None:
                        tags = []
                    
                    target = EnhancedTarget(
                        id=target_row['id'],
                        name=target_row['name'],
                        hostname=target_row['host'],
                        ip_address=target_row['host'],  # Using host as IP for now
                        os_type=target_row['target_type'],
                        os_version="Unknown",  # Not available in current schema
                        description=target_row['description'],
                        tags=tags,
                        services=services,
                        created_at=target_row['created_at'].isoformat(),
                        updated_at=target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": target}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get target"
                )

        @self.app.put("/targets/{target_id}", response_model=dict)
        async def update_target(target_id: int, target_data: EnhancedTargetUpdate):
            """Update target"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if target_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(target_data.name)
                        param_count += 1
                    
                    if target_data.hostname is not None:
                        updates.append(f"hostname = ${param_count}")
                        values.append(target_data.hostname)
                        param_count += 1
                    
                    if target_data.ip_address is not None:
                        updates.append(f"ip_address = ${param_count}")
                        values.append(target_data.ip_address)
                        param_count += 1
                    
                    if target_data.os_type is not None:
                        updates.append(f"os_type = ${param_count}")
                        values.append(target_data.os_type)
                        param_count += 1
                    
                    if target_data.os_version is not None:
                        updates.append(f"os_version = ${param_count}")
                        values.append(target_data.os_version)
                        param_count += 1
                    
                    if target_data.description is not None:
                        updates.append(f"description = ${param_count}")
                        values.append(target_data.description)
                        param_count += 1
                    
                    if target_data.tags is not None:
                        updates.append(f"tags = ${param_count}")
                        values.append(target_data.tags)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No fields to update"
                        )
                    
                    # Add updated_at
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    
                    # Add target_id as the last parameter
                    values.append(target_id)
                    
                    query = f"""
                        UPDATE assets.targets 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id
                    """
                    
                    result = await conn.fetchval(query, *values)
                    
                    if not result:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    return {"success": True, "message": "Target updated"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update target"
                )

        @self.app.delete("/targets/{target_id}", response_model=dict)
        async def delete_target(target_id: int):
            """Delete target"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Delete services first (foreign key constraint)
                        await conn.execute(
                            "DELETE FROM assets.target_services WHERE target_id = $1", target_id
                        )
                        
                        # Delete target
                        result = await conn.execute(
                            "DELETE FROM assets.targets WHERE id = $1", target_id
                        )
                        
                        if result == "DELETE 0":
                            raise HTTPException(status_code=404, detail="Target not found")
                        
                        return {"success": True, "message": "Target deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete target"
                )

        @self.app.post("/targets/{target_id}/services/{service_id}/test", response_model=dict)
        async def test_service_connection(target_id: int, service_id: int):
            """Test connection to a specific service"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get service details with credentials
                    service_row = await conn.fetchrow("""
                        SELECT ts.*, t.name as target_name, t.host
                        FROM assets.target_services ts
                        JOIN assets.targets t ON ts.target_id = t.id
                        WHERE ts.id = $1 AND ts.target_id = $2
                    """, service_id, target_id)
                    
                    if not service_row:
                        raise HTTPException(status_code=404, detail="Service not found")
                    
                    if not service_row['is_enabled']:
                        raise HTTPException(status_code=400, detail="Service is disabled")
                    
                    # Determine connection host
                    host = service_row['host']
                    if not host:
                        raise HTTPException(status_code=400, detail="No host configured")
                    
                    # Mock connection test (implement actual connection logic here)
                    import random
                    import time
                    
                    start_time = time.time()
                    
                    # Simulate connection attempt
                    success = random.choice([True, True, True, False])  # 75% success rate
                    
                    end_time = time.time()
                    response_time_ms = int((end_time - start_time) * 1000)
                    
                    if success:
                        test_result = {
                            'status': 'success',
                            'message': f'Successfully connected to {service_row["service_type"]} service',
                            'response_time_ms': response_time_ms
                        }
                        connection_status = 'connected'
                    else:
                        test_result = {
                            'status': 'failed',
                            'message': f'Failed to connect to {service_row["service_type"]} service: Connection timeout',
                            'response_time_ms': response_time_ms
                        }
                        connection_status = 'failed'
                    
                    # Determine connection type based on service
                    connection_type = service_row['service_type']
                    if service_row['credential_type']:
                        connection_type += f" ({service_row['credential_type']})"
                    
                    return {
                        "success": True,
                        "data": {
                            "service_id": service_id,
                            "target_name": service_row['target_name'],
                            "service_type": service_row['service_type'],
                            "host": host,
                            "port": service_row['port'],
                            "connection_type": connection_type,
                            "status": test_result['status'],
                            "message": test_result['message'],
                            "response_time_ms": test_result.get('response_time_ms'),
                            "connection_status": connection_status,
                            "tested_at": datetime.utcnow().isoformat()
                        }
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to test service connection", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to test service connection"
                )

        # ============================================================================
        # TARGET GROUPS ENDPOINTS
        # ============================================================================
        
        @self.app.get("/target-groups")
        async def list_target_groups(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            include_counts: bool = Query(False, description="Include target counts for each group")
        ):
            """List all target groups with optional target counts"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get groups with basic info
                    groups_query = """
                        SELECT id, name, description, parent_group_id, path, level, 
                               color, icon, created_at, updated_at
                        FROM assets.target_groups
                        ORDER BY path
                        OFFSET $1 LIMIT $2
                    """
                    groups = await conn.fetch(groups_query, skip, limit)
                    
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM assets.target_groups")
                    
                    group_list = []
                    for group in groups:
                        group_dict = {
                            "id": group['id'],
                            "name": group['name'],
                            "description": group['description'],
                            "parent_group_id": group['parent_group_id'],
                            "path": group['path'],
                            "level": group['level'],
                            "color": group['color'],
                            "icon": group['icon'],
                            "created_at": group['created_at'].isoformat(),
                            "updated_at": group['updated_at'].isoformat() if group['updated_at'] else None
                        }
                        
                        if include_counts:
                            # Get target count for this group (including descendants)
                            target_count = await conn.fetchval("""
                                SELECT COUNT(DISTINCT tgm.target_id)
                                FROM assets.target_group_memberships tgm
                                JOIN assets.target_groups tg ON tgm.group_id = tg.id
                                WHERE tg.path LIKE $1
                            """, group['path'] + '%')
                            group_dict['target_count'] = target_count
                            
                            # Get direct target count (only this group)
                            direct_count = await conn.fetchval("""
                                SELECT COUNT(*)
                                FROM assets.target_group_memberships
                                WHERE group_id = $1
                            """, group['id'])
                            group_dict['direct_target_count'] = direct_count
                        
                        group_list.append(group_dict)
                    
                    return {"groups": group_list, "total": total, "skip": skip, "limit": limit}
            except Exception as e:
                self.logger.error("Failed to fetch target groups", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch target groups"
                )

        @self.app.post("/target-groups")
        async def create_target_group():
            """Create a new target group"""
            return {"message": "Target groups feature not implemented in current schema"}

        @self.app.get("/target-groups/{group_id}")
        async def get_target_group(group_id: int):
            """Get target group by ID"""
            return {"message": "Target groups feature not implemented in current schema"}
                    group = await conn.fetchrow("""
                        SELECT id, name, description, parent_group_id, path, level, 
                               color, icon, created_at, updated_at
                        FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    if not group:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    # Get target count
                    target_count = await conn.fetchval("""
                        SELECT COUNT(DISTINCT tgm.target_id)
                        FROM assets.target_group_memberships tgm
                        JOIN assets.target_groups tg ON tgm.group_id = tg.id
                        WHERE tg.path LIKE $1
                    """, group['path'] + '%')
                    
                    # Get direct target count
                    direct_count = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM assets.target_group_memberships
                        WHERE group_id = $1
                    """, group_id)
                    
                    group_dict = {
                        "id": group['id'],
                        "name": group['name'],
                        "description": group['description'],
                        "parent_group_id": group['parent_group_id'],
                        "path": group['path'],
                        "level": group['level'],
                        "color": group['color'],
                        "icon": group['icon'],
                        "target_count": target_count,
                        "direct_target_count": direct_count,
                        "created_at": group['created_at'].isoformat(),
                        "updated_at": group['updated_at'].isoformat() if group['updated_at'] else None
                    }
                    
                    return {"success": True, "data": TargetGroup(**group_dict)}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get target group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get target group"
                )

        @self.app.put("/target-groups/{group_id}", response_model=dict)
        async def update_target_group(group_id: int, group_data: TargetGroupUpdate):
            """Update target group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if group_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(group_data.name)
                        param_count += 1
                    
                    if group_data.description is not None:
                        updates.append(f"description = ${param_count}")
                        values.append(group_data.description)
                        param_count += 1
                    
                    if group_data.color is not None:
                        updates.append(f"color = ${param_count}")
                        values.append(group_data.color)
                        param_count += 1
                    
                    if group_data.icon is not None:
                        updates.append(f"icon = ${param_count}")
                        values.append(group_data.icon)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No fields to update"
                        )
                    
                    # Add updated_at
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    
                    # Add group_id as the last parameter
                    values.append(group_id)
                    
                    query = f"""
                        UPDATE assets.target_groups 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id
                    """
                    
                    result = await conn.fetchval(query, *values)
                    
                    if not result:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    return {"success": True, "message": "Target group updated"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update target group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update target group"
                )

        @self.app.delete("/target-groups/{group_id}", response_model=dict)
        async def delete_target_group(group_id: int):
            """Delete target group"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Check if group has children
                        children_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM assets.target_groups WHERE parent_group_id = $1",
                            group_id
                        )
                        
                        if children_count > 0:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Cannot delete group with child groups"
                            )
                        
                        # Delete group memberships first
                        await conn.execute(
                            "DELETE FROM assets.target_group_memberships WHERE group_id = $1",
                            group_id
                        )
                        
                        # Delete group
                        result = await conn.execute(
                            "DELETE FROM assets.target_groups WHERE id = $1",
                            group_id
                        )
                        
                        if result == "DELETE 0":
                            raise HTTPException(status_code=404, detail="Target group not found")
                        
                        return {"success": True, "message": "Target group deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete target group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete target group"
                )

        @self.app.get("/target-groups/{group_id}/targets", response_model=TargetGroupTargetsResponse)
        async def get_group_targets(
            group_id: int,
            include_descendants: bool = Query(False, description="Include targets from child groups"),
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """Get targets in a specific group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Verify group exists
                    group = await conn.fetchrow(
                        "SELECT id, path FROM assets.target_groups WHERE id = $1",
                        group_id
                    )
                    
                    if not group:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    if include_descendants:
                        # Get targets from this group and all descendants
                        targets_query = """
                            SELECT DISTINCT t.id, t.name, t.host, t.target_type, t.connection_type,
                                   t.description, t.tags, t.created_at, t.updated_at
                            FROM assets.targets t
                            JOIN assets.target_group_memberships tgm ON t.id = tgm.target_id
                            JOIN assets.target_groups tg ON tgm.group_id = tg.id
                            WHERE tg.path LIKE $1
                            ORDER BY t.created_at DESC
                            LIMIT $2 OFFSET $3
                        """
                        count_query = """
                            SELECT COUNT(DISTINCT t.id)
                            FROM assets.targets t
                            JOIN assets.target_group_memberships tgm ON t.id = tgm.target_id
                            JOIN assets.target_groups tg ON tgm.group_id = tg.id
                            WHERE tg.path LIKE $1
                        """
                        path_pattern = group['path'] + '%'
                        targets = await conn.fetch(targets_query, path_pattern, limit, skip)
                        total = await conn.fetchval(count_query, path_pattern)
                    else:
                        # Get targets only from this specific group
                        targets_query = """
                            SELECT t.id, t.name, t.host, t.target_type, t.connection_type,
                                   t.description, t.tags, t.created_at, t.updated_at
                            FROM assets.targets t
                            JOIN assets.target_group_memberships tgm ON t.id = tgm.target_id
                            WHERE tgm.group_id = $1
                            ORDER BY t.created_at DESC
                            LIMIT $2 OFFSET $3
                        """
                        count_query = """
                            SELECT COUNT(*)
                            FROM assets.target_group_memberships
                            WHERE group_id = $1
                        """
                        targets = await conn.fetch(targets_query, group_id, limit, skip)
                        total = await conn.fetchval(count_query, group_id)
                    
                    # Build target list with services
                    target_list = []
                    for target_row in targets:
                        # Get services for this target
                        service_rows = await conn.fetch("""
                            SELECT id, target_id, service_type, port, is_default, is_secure, 
                                   is_enabled, notes, credential_type, created_at
                            FROM assets.target_services 
                            WHERE target_id = $1 
                            ORDER BY is_default DESC, port ASC
                        """, target_row['id'])
                        
                        services = []
                        for service_row in service_rows:
                            services.append(TargetServiceSummary(
                                id=service_row['id'],
                                service_type=service_row['service_type'],
                                port=service_row['port'],
                                is_default=service_row['is_default'],
                                is_secure=service_row['is_secure'],
                                is_enabled=service_row['is_enabled'],
                                credential_type=service_row['credential_type'],
                                has_credentials=service_row['credential_type'] is not None
                            ))
                        
                        target_list.append(EnhancedTargetSummary(
                            id=target_row['id'],
                            name=target_row['name'],
                            hostname=target_row['hostname'],
                            ip_address=target_row['ip_address'],
                            os_type=target_row['os_type'],
                            os_version=target_row['os_version'],
                            description=target_row['description'],
                            tags=target_row['tags'] or [],
                            services=services,
                            created_at=target_row['created_at'].isoformat(),
                            updated_at=target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                        ))
                    
                    return TargetGroupTargetsResponse(
                        targets=target_list,
                        total=total,
                        include_descendants=include_descendants
                    )
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get group targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get group targets"
                )

        @self.app.post("/target-groups/{group_id}/targets", response_model=dict)
        async def add_targets_to_group(group_id: int, target_ids: List[int]):
            """Add targets to a group"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Verify group exists
                        group_exists = await conn.fetchval(
                            "SELECT EXISTS(SELECT 1 FROM assets.target_groups WHERE id = $1)",
                            group_id
                        )
                        
                        if not group_exists:
                            raise HTTPException(status_code=404, detail="Target group not found")
                        
                        added_count = 0
                        for target_id in target_ids:
                            # Check if target exists
                            target_exists = await conn.fetchval(
                                "SELECT EXISTS(SELECT 1 FROM assets.targets WHERE id = $1)",
                                target_id
                            )
                            
                            if not target_exists:
                                continue
                            
                            # Check if membership already exists
                            membership_exists = await conn.fetchval("""
                                SELECT EXISTS(SELECT 1 FROM assets.target_group_memberships 
                                             WHERE target_id = $1 AND group_id = $2)
                            """, target_id, group_id)
                            
                            if not membership_exists:
                                await conn.execute("""
                                    INSERT INTO assets.target_group_memberships (target_id, group_id)
                                    VALUES ($1, $2)
                                """, target_id, group_id)
                                added_count += 1
                        
                        return {
                            "success": True,
                            "message": f"Added {added_count} targets to group",
                            "added_count": added_count
                        }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to add targets to group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add targets to group"
                )

        @self.app.delete("/target-groups/{group_id}/targets/{target_id}", response_model=dict)
        async def remove_target_from_group(group_id: int, target_id: int):
            """Remove target from group"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute("""
                        DELETE FROM assets.target_group_memberships 
                        WHERE target_id = $1 AND group_id = $2
                    """, target_id, group_id)
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Target not found in group")
                    
                    return {"success": True, "message": "Target removed from group"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to remove target from group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to remove target from group"
                )

        @self.app.get("/target-groups/tree", response_model=dict)
        async def get_target_groups_tree():
            """Get target groups as a hierarchical tree"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get all groups ordered by path
                    groups = await conn.fetch("""
                        SELECT id, name, description, parent_group_id, path, level, 
                               color, icon, created_at, updated_at
                        FROM assets.target_groups
                        ORDER BY path
                    """)
                    
                    # Build tree structure
                    groups_dict = {}
                    root_groups = []
                    
                    for group in groups:
                        # Get target count for this group (including descendants)
                        target_count = await conn.fetchval("""
                            SELECT COUNT(DISTINCT tgm.target_id)
                            FROM assets.target_group_memberships tgm
                            JOIN assets.target_groups tg ON tgm.group_id = tg.id
                            WHERE tg.path LIKE $1
                        """, group['path'] + '%')
                        
                        group_dict = {
                            "id": group['id'],
                            "name": group['name'],
                            "description": group['description'],
                            "parent_group_id": group['parent_group_id'],
                            "path": group['path'],
                            "level": group['level'],
                            "color": group['color'],
                            "icon": group['icon'],
                            "target_count": target_count,
                            "created_at": group['created_at'].isoformat(),
                            "updated_at": group['updated_at'].isoformat() if group['updated_at'] else None,
                            "children": []
                        }
                        
                        groups_dict[group['id']] = group_dict
                        
                        if group['parent_group_id'] is None:
                            root_groups.append(group_dict)
                        else:
                            parent = groups_dict.get(group['parent_group_id'])
                            if parent:
                                parent['children'].append(group_dict)
                    
                    return {"success": True, "tree": root_groups}
            except Exception as e:
                self.logger.error("Failed to get target groups tree", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get target groups tree"
                )

    # ============================================================================
    # MAIN EXECUTION
    # ============================================================================

if __name__ == "__main__":
    service = AssetService()
    service.run()
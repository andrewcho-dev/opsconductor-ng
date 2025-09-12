#!/usr/bin/env python3
"""
OpsConductor Asset Service
Handles targets and discovery with embedded credentials
Consolidates: target-service + discovery-service
"""

import sys
import os
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
    
    # Embedded credential fields (decrypted for API responses)
    credential_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Will be masked in responses
    private_key: Optional[str] = None  # Will be masked in responses
    public_key: Optional[str] = None
    api_key: Optional[str] = None  # Will be masked in responses
    bearer_token: Optional[str] = None  # Will be masked in responses
    certificate: Optional[str] = None  # Will be masked in responses
    passphrase: Optional[str] = None  # Will be masked in responses
    domain: Optional[str] = None
    
    # Connection status fields
    connection_status: Optional[str] = 'unknown'
    last_tested_at: Optional[str] = None
    
    created_at: str

class TargetServiceSummary(BaseModel):
    """Simplified service model for target list view - only shows credential type, not sensitive data"""
    id: int
    target_id: int
    service_type: str
    port: int
    is_default: bool = False
    is_secure: bool = False
    is_enabled: bool = True
    notes: Optional[str] = None
    
    # Only credential type, no sensitive data
    credential_type: Optional[str] = None
    
    # Connection status fields
    connection_status: Optional[str] = 'unknown'
    last_tested_at: Optional[str] = None
    
    created_at: str

class EnhancedTargetCreate(BaseModel):
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = 'other'
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
    services: Optional[List[TargetServiceCreate]] = None

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
    
    # Validate credential types for each service
    for service in services:
        if service.credential_type:
            allowed_types = SERVICE_CREDENTIAL_MAPPING.get(service.service_type, [])
            if service.credential_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Credential type '{service.credential_type}' is not allowed for service type '{service.service_type}'. Allowed types: {allowed_types}"
                )

class Target(BaseModel):
    id: int
    name: str
    host: str
    port: Optional[int] = None
    platform: str
    credential_id: Optional[int] = None
    group_id: Optional[int] = None
    tags: List[str] = []
    metadata: dict = {}
    is_active: bool
    last_seen: Optional[str] = None
    created_by: int
    created_at: str
    updated_at: str

class TargetCreate(BaseModel):
    name: str
    host: str
    port: Optional[int] = None
    platform: str
    credential_id: Optional[int] = None
    group_id: Optional[int] = None
    tags: List[str] = []
    metadata: dict = {}
    is_active: bool = True

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    platform: Optional[str] = None
    credential_id: Optional[int] = None
    group_id: Optional[int] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None

class TargetListResponse(BaseModel):
    targets: List[Target]
    total: int
    skip: int
    limit: int

class DiscoveryJob(BaseModel):
    id: int
    name: str
    target_range: str  # Changed from network_range to match DB
    scan_type: str
    status: str
    configuration: dict = {}
    results: dict = {}
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_by: int
    created_at: str

class DiscoveryCreate(BaseModel):
    name: str
    discovery_type: str = "network_scan"
    config: dict = {}

class DiscoveryUpdate(BaseModel):
    status: Optional[str] = None
    configuration: Optional[dict] = None
    results: Optional[dict] = None

class DiscoveryListResponse(BaseModel):
    discovery_jobs: List[DiscoveryJob]
    total: int
    skip: int
    limit: int

class DiscoveredService(BaseModel):
    protocol: str
    port: int
    service_name: Optional[str] = None
    version: Optional[str] = None
    is_secure: Optional[bool] = False

class DiscoveredTarget(BaseModel):
    id: int
    discovery_job_id: int
    hostname: Optional[str] = None
    ip_address: str
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    services: List[DiscoveredService] = []
    preferred_service: Optional[DiscoveredService] = None
    system_info: dict = {}
    duplicate_status: str = "unique"  # 'unique' | 'duplicate' | 'similar'
    existing_target_id: Optional[int] = None
    import_status: str = "pending"  # 'pending' | 'imported' | 'ignored' | 'duplicate_skipped'
    discovered_at: str

class DiscoveredTargetUpdate(BaseModel):
    hostname: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    import_status: Optional[str] = None

class DiscoveredTargetListResponse(BaseModel):
    targets: List[DiscoveredTarget]
    total: int

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

class TargetGroupMembershipCreate(BaseModel):
    target_ids: List[int]

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
                    total = await conn.fetchval("SELECT COUNT(*) FROM assets.enhanced_targets")
                    
                    # Get targets with pagination
                    target_rows = await conn.fetch("""
                        SELECT id, name, hostname, ip_address, os_type, os_version,
                               description, tags, created_at, updated_at
                        FROM assets.enhanced_targets 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    targets = []
                    for row in target_rows:
                        # Get services for this target (list view - only credential type, no sensitive data)
                        service_rows = await conn.fetch("""
                            SELECT id, service_type, port, is_default, is_secure, is_enabled, notes,
                                   credential_type, connection_status, last_tested_at, created_at
                            FROM assets.target_services 
                            WHERE target_id = $1
                            ORDER BY is_default DESC, service_type, port
                        """, row['id'])
                        
                        services = []
                        for service_row in service_rows:
                            services.append(TargetServiceSummary(
                                id=service_row['id'],
                                target_id=row['id'],
                                service_type=service_row['service_type'],
                                port=service_row['port'],
                                is_default=service_row['is_default'],
                                is_secure=service_row['is_secure'],
                                is_enabled=service_row['is_enabled'],
                                notes=service_row['notes'],
                                credential_type=service_row['credential_type'],
                                connection_status=service_row['connection_status'],
                                last_tested_at=service_row['last_tested_at'].isoformat() if service_row['last_tested_at'] else None,
                                created_at=service_row['created_at'].isoformat()
                            ))
                        
                        import json
                        targets.append(EnhancedTargetSummary(
                            id=row['id'],
                            name=row['name'],
                            hostname=row['hostname'],
                            ip_address=row['ip_address'],
                            os_type=row['os_type'],
                            os_version=row['os_version'],
                            description=row['description'],
                            tags=json.loads(row['tags']) if row['tags'] else [],
                            services=services,
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
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
            """Create a new target (using enhanced system)"""
            try:
                # Validate services
                validate_services(target_data.services)
                
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        import json
                        
                        # Create the target
                        target_row = await conn.fetchrow("""
                            INSERT INTO assets.enhanced_targets 
                            (name, hostname, ip_address, os_type, os_version, description, tags)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id, name, hostname, ip_address, os_type, os_version,
                                      description, tags, created_at, updated_at
                        """, target_data.name, target_data.hostname, target_data.ip_address,
                             target_data.os_type, target_data.os_version, target_data.description,
                             json.dumps(target_data.tags or []))
                        
                        # Create services
                        services = []
                        for service_data in target_data.services:
                            # TODO: Add encryption for sensitive fields
                            service_row = await conn.fetchrow("""
                                INSERT INTO assets.target_services 
                                (target_id, service_type, port, is_default, is_secure, is_enabled, notes,
                                 credential_type, username, password_encrypted, private_key_encrypted,
                                 public_key, api_key_encrypted, bearer_token_encrypted, certificate_encrypted,
                                 passphrase_encrypted, domain)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                                RETURNING id, service_type, port, is_default, is_secure, is_enabled, notes,
                                          credential_type, username, password_encrypted, private_key_encrypted,
                                          public_key, api_key_encrypted, bearer_token_encrypted, certificate_encrypted,
                                          passphrase_encrypted, domain, created_at
                            """, target_row['id'], service_data.service_type, service_data.port,
                                 service_data.is_default, service_data.is_secure, service_data.is_enabled, 
                                 service_data.notes, service_data.credential_type, service_data.username,
                                 service_data.password, service_data.private_key, service_data.public_key,
                                 service_data.api_key, service_data.bearer_token, service_data.certificate,
                                 service_data.passphrase, service_data.domain)
                            
                            services.append(TargetService(
                                id=service_row['id'],
                                target_id=target_row['id'],
                                service_type=service_row['service_type'],
                                port=service_row['port'],
                                is_default=service_row['is_default'],
                                is_secure=service_row['is_secure'],
                                is_enabled=service_row['is_enabled'],
                                notes=service_row['notes'],
                                credential_type=service_row['credential_type'],
                                username=service_row['username'],
                                password="***" if service_row['password_encrypted'] else None,  # Mask password
                                private_key="***" if service_row['private_key_encrypted'] else None,  # Mask key
                                public_key=service_row['public_key'],
                                api_key="***" if service_row['api_key_encrypted'] else None,  # Mask API key
                                bearer_token="***" if service_row['bearer_token_encrypted'] else None,  # Mask token
                                certificate="***" if service_row['certificate_encrypted'] else None,  # Mask cert
                                passphrase="***" if service_row['passphrase_encrypted'] else None,  # Mask passphrase
                                domain=service_row['domain'],
                                created_at=service_row['created_at'].isoformat()
                            ))
                        
                        target = EnhancedTarget(
                            id=target_row['id'],
                            name=target_row['name'],
                            hostname=target_row['hostname'],
                            ip_address=target_row['ip_address'],
                            os_type=target_row['os_type'],
                            os_version=target_row['os_version'],
                            description=target_row['description'],
                            tags=json.loads(target_row['tags']) if target_row['tags'] else [],
                            services=services,
                            created_at=target_row['created_at'].isoformat(),
                            updated_at=target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                        )
                        
                        return {"success": True, "message": "Target created", "data": target}
            except Exception as e:
                self.logger.error("Failed to create target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create target"
                )

        @self.app.get("/targets/{target_id}", response_model=dict)
        async def get_target(target_id: int):
            """Get target by ID (using enhanced system)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get target
                    target_row = await conn.fetchrow("""
                        SELECT id, name, hostname, ip_address, os_type, os_version,
                               description, tags, created_at, updated_at
                        FROM assets.enhanced_targets 
                        WHERE id = $1
                    """, target_id)
                    
                    if not target_row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Target not found"
                        )
                    
                    # Get services
                    service_rows = await conn.fetch("""
                        SELECT id, service_type, port, is_default, is_secure, is_enabled, notes,
                               credential_type, username, password_encrypted, private_key_encrypted,
                               public_key, api_key_encrypted, bearer_token_encrypted, certificate_encrypted,
                               passphrase_encrypted, domain, connection_status, last_tested_at, created_at
                        FROM assets.target_services 
                        WHERE target_id = $1
                        ORDER BY is_default DESC, service_type, port
                    """, target_id)
                    
                    services = []
                    for service_row in service_rows:
                        services.append(TargetService(
                            id=service_row['id'],
                            target_id=target_id,
                            service_type=service_row['service_type'],
                            port=service_row['port'],
                            is_default=service_row['is_default'],
                            is_secure=service_row['is_secure'],
                            is_enabled=service_row['is_enabled'],
                            notes=service_row['notes'],
                            credential_type=service_row['credential_type'],
                            username=service_row['username'],
                            password="***" if service_row['password_encrypted'] else None,
                            private_key="***" if service_row['private_key_encrypted'] else None,
                            public_key=service_row['public_key'],
                            api_key="***" if service_row['api_key_encrypted'] else None,
                            bearer_token="***" if service_row['bearer_token_encrypted'] else None,
                            certificate="***" if service_row['certificate_encrypted'] else None,
                            passphrase="***" if service_row['passphrase_encrypted'] else None,
                            domain=service_row['domain'],
                            connection_status=service_row['connection_status'],
                            last_tested_at=service_row['last_tested_at'].isoformat() if service_row['last_tested_at'] else None,
                            created_at=service_row['created_at'].isoformat()
                        ))
                    
                    import json
                    target = EnhancedTarget(
                        id=target_row['id'],
                        name=target_row['name'],
                        hostname=target_row['hostname'],
                        ip_address=target_row['ip_address'],
                        os_type=target_row['os_type'],
                        os_version=target_row['os_version'],
                        description=target_row['description'],
                        tags=json.loads(target_row['tags']) if target_row['tags'] else [],
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
            """Update target (using enhanced system)"""
            try:
                # Validate services if provided
                if target_data.services is not None:
                    validate_services(target_data.services)
                
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Check if target exists
                        exists = await conn.fetchval("SELECT id FROM assets.enhanced_targets WHERE id = $1", target_id)
                        if not exists:
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Target not found"
                            )
                        
                        # Build update query dynamically
                        update_fields = []
                        update_values = []
                        param_count = 1
                        
                        if target_data.name is not None:
                            update_fields.append(f"name = ${param_count}")
                            update_values.append(target_data.name)
                            param_count += 1
                        
                        if target_data.hostname is not None:
                            update_fields.append(f"hostname = ${param_count}")
                            update_values.append(target_data.hostname)
                            param_count += 1
                        
                        if target_data.ip_address is not None:
                            update_fields.append(f"ip_address = ${param_count}")
                            update_values.append(target_data.ip_address)
                            param_count += 1
                        
                        if target_data.os_type is not None:
                            update_fields.append(f"os_type = ${param_count}")
                            update_values.append(target_data.os_type)
                            param_count += 1
                        
                        if target_data.os_version is not None:
                            update_fields.append(f"os_version = ${param_count}")
                            update_values.append(target_data.os_version)
                            param_count += 1
                        
                        if target_data.description is not None:
                            update_fields.append(f"description = ${param_count}")
                            update_values.append(target_data.description)
                            param_count += 1
                        
                        if target_data.tags is not None:
                            import json
                            update_fields.append(f"tags = ${param_count}")
                            update_values.append(json.dumps(target_data.tags))
                            param_count += 1
                        
                        # Always update the updated_at timestamp if there are any changes
                        if update_fields or target_data.services is not None:
                            if update_fields:
                                update_fields.append(f"updated_at = ${param_count}")
                                update_values.append(datetime.utcnow())
                                update_values.append(target_id)
                                
                                query = f"""
                                    UPDATE assets.enhanced_targets 
                                    SET {', '.join(update_fields)}
                                    WHERE id = ${param_count + 1}
                                    RETURNING id, name, hostname, ip_address, os_type, os_version,
                                              description, tags, created_at, updated_at
                                """
                                
                                target_row = await conn.fetchrow(query, *update_values)
                            else:
                                # Only services are being updated, just update timestamp
                                target_row = await conn.fetchrow("""
                                    UPDATE assets.enhanced_targets 
                                    SET updated_at = $1
                                    WHERE id = $2
                                    RETURNING id, name, hostname, ip_address, os_type, os_version,
                                              description, tags, created_at, updated_at
                                """, datetime.utcnow(), target_id)
                            
                            # Handle services update if provided
                            if target_data.services is not None:
                                # Delete existing services
                                await conn.execute("DELETE FROM assets.target_services WHERE target_id = $1", target_id)
                                
                                # Create new services
                                for service_data in target_data.services:
                                    await conn.execute("""
                                        INSERT INTO assets.target_services 
                                        (target_id, service_type, port, is_default, is_secure, is_enabled, notes,
                                         credential_type, username, password_encrypted, private_key_encrypted,
                                         public_key, api_key_encrypted, bearer_token_encrypted, certificate_encrypted,
                                         passphrase_encrypted, domain)
                                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                                    """, target_id, service_data.service_type, service_data.port,
                                         service_data.is_default, service_data.is_secure, service_data.is_enabled, 
                                         service_data.notes, service_data.credential_type, service_data.username,
                                         service_data.password, service_data.private_key, service_data.public_key,
                                         service_data.api_key, service_data.bearer_token, service_data.certificate,
                                         service_data.passphrase, service_data.domain)
                            
                            # Get updated services
                            service_rows = await conn.fetch("""
                                SELECT id, service_type, port, is_default, is_secure, is_enabled, notes,
                                       credential_type, username, password_encrypted, private_key_encrypted,
                                       public_key, api_key_encrypted, bearer_token_encrypted, certificate_encrypted,
                                       passphrase_encrypted, domain, created_at
                                FROM assets.target_services 
                                WHERE target_id = $1
                                ORDER BY is_default DESC, service_type, port
                            """, target_id)
                            
                            services = []
                            for service_row in service_rows:
                                services.append(TargetService(
                                    id=service_row['id'],
                                    target_id=target_id,
                                    service_type=service_row['service_type'],
                                    port=service_row['port'],
                                    is_default=service_row['is_default'],
                                    is_secure=service_row['is_secure'],
                                    is_enabled=service_row['is_enabled'],
                                    notes=service_row['notes'],
                                    credential_type=service_row['credential_type'],
                                    username=service_row['username'],
                                    password="***" if service_row['password_encrypted'] else None,
                                    private_key="***" if service_row['private_key_encrypted'] else None,
                                    public_key=service_row['public_key'],
                                    api_key="***" if service_row['api_key_encrypted'] else None,
                                    bearer_token="***" if service_row['bearer_token_encrypted'] else None,
                                    certificate="***" if service_row['certificate_encrypted'] else None,
                                    passphrase="***" if service_row['passphrase_encrypted'] else None,
                                    domain=service_row['domain'],
                                    created_at=service_row['created_at'].isoformat()
                                ))
                            
                            import json
                            target = EnhancedTarget(
                                id=target_row['id'],
                                name=target_row['name'],
                                hostname=target_row['hostname'],
                                ip_address=target_row['ip_address'],
                                os_type=target_row['os_type'],
                                os_version=target_row['os_version'],
                                description=target_row['description'],
                                tags=json.loads(target_row['tags']) if target_row['tags'] else [],
                                services=services,
                                created_at=target_row['created_at'].isoformat(),
                                updated_at=target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                            )
                            
                            return {"success": True, "message": "Target updated", "data": target}
                        else:
                            return {"success": True, "message": "No changes made"}
                        
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
            """Delete target (using enhanced system)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if target exists
                    exists = await conn.fetchval("SELECT id FROM assets.enhanced_targets WHERE id = $1", target_id)
                    if not exists:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Target not found"
                        )
                    
                    # Delete target (services will be deleted by CASCADE)
                    await conn.execute("DELETE FROM assets.enhanced_targets WHERE id = $1", target_id)
                    
                    return {"success": True, "message": "Target deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete target"
                )

        @self.app.post("/targets/{target_id}/test-connection", response_model=dict)
        async def test_target_connection(target_id: int):
            """Test connection to target"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get target details
                    target_row = await conn.fetchrow("""
                        SELECT id, name, host, port, target_type
                        FROM assets.enhanced_targets
                        WHERE id = $1 AND is_active = true
                    """, target_id)
                    
                    if not target_row:
                        raise HTTPException(status_code=404, detail="Target not found or inactive")
                    
                    # Determine connection type based on target type and port
                    connection_type = self._determine_connection_type(
                        target_row['target_type'], 
                        target_row['port']
                    )
                    
                    # Test connection based on type
                    test_result = await self._test_connection(
                        host=target_row['host'],
                        port=target_row['port'],
                        connection_type=connection_type
                    )
                    
                    # Update target's last_tested timestamp
                    await conn.execute(
                        "UPDATE assets.enhanced_targets SET metadata = COALESCE(metadata, '{}')::jsonb || $1::jsonb WHERE id = $2",
                        '{"last_tested": "' + datetime.utcnow().isoformat() + '"}',
                        target_id
                    )
                    
                    return {
                        "success": True,
                        "data": {
                            "target_id": target_id,
                            "target_name": target_row['name'],
                            "host": target_row['host'],
                            "port": target_row['port'],
                            "connection_type": connection_type,
                            "status": test_result['status'],
                            "message": test_result['message'],
                            "response_time_ms": test_result.get('response_time_ms'),
                            "tested_at": datetime.utcnow().isoformat()
                        }
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to test target connection", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to test target connection"
                )

        @self.app.post("/targets/services/{service_id}/test-connection", response_model=dict)
        async def test_service_connection(service_id: int):
            """Test connection to a specific service (enhanced system)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get service details with target info (enhanced schema)
                    service_row = await conn.fetchrow("""
                        SELECT s.id, s.target_id, s.service_type, s.port, s.is_enabled,
                               s.credential_type, s.username, s.password_encrypted, 
                               s.private_key_encrypted, s.api_key_encrypted, 
                               s.bearer_token_encrypted, s.certificate_encrypted,
                               s.passphrase_encrypted, s.domain,
                               t.name as target_name, t.hostname, t.ip_address, t.os_type
                        FROM assets.target_services s
                        JOIN assets.enhanced_targets t ON s.target_id = t.id
                        WHERE s.id = $1 AND s.is_enabled = true
                    """, service_id)
                    
                    if not service_row:
                        raise HTTPException(status_code=404, detail="Service not found or disabled")
                    
                    # Determine connection type based on service type and port
                    connection_type = self._determine_connection_type(
                        service_row['service_type'], 
                        service_row['port']
                    )
                    
                    # Build credential data from embedded fields
                    credential_data = None
                    if service_row['credential_type']:
                        import json
                        credential_dict = {
                            'type': service_row['credential_type'],
                            'username': service_row['username'],
                            'password': service_row['password_encrypted'],
                            'private_key': service_row['private_key_encrypted'],
                            'api_key': service_row['api_key_encrypted'],
                            'bearer_token': service_row['bearer_token_encrypted'],
                            'certificate': service_row['certificate_encrypted'],
                            'passphrase': service_row['passphrase_encrypted'],
                            'domain': service_row['domain']
                        }
                        credential_data = json.dumps(credential_dict)
                    
                    # Use hostname or IP address for connection
                    host = service_row['hostname'] or service_row['ip_address']
                    
                    # Test connection based on type
                    test_result = await self._test_connection(
                        host=host,
                        port=service_row['port'],
                        connection_type=connection_type,
                        credential_data=credential_data
                    )
                    
                    # Update service's connection status and last tested timestamp
                    connection_status = 'connected' if test_result['status'] == 'success' else 'failed'
                    
                    from datetime import datetime
                    
                    await conn.execute("""
                        UPDATE assets.target_services 
                        SET connection_status = $1, last_tested_at = $2
                        WHERE id = $3
                    """, connection_status, datetime.utcnow(), service_id)
                    
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
        # DISCOVERY CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.get("/discovery/discovery-jobs", response_model=DiscoveryListResponse)
        async def list_discovery_jobs(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all discovery jobs from automation service"""
            try:
                import httpx
                
                # Get discovery jobs from automation service
                async with httpx.AsyncClient() as client:
                    automation_response = await client.get(
                        f"http://automation-service:3003/jobs?skip={skip}&limit={limit}&job_type=discovery",
                        timeout=30.0
                    )
                    
                    if automation_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch jobs from automation service: {automation_response.text}"
                        )
                    
                    automation_jobs = automation_response.json()
                
                # Convert automation jobs to discovery job format
                discovery_jobs = []
                for job in automation_jobs.get("jobs", []):
                    # All jobs returned are discovery jobs (filtered by job_type)
                    metadata = job.get("metadata", {})
                    
                    # Map automation job status to discovery status
                    status_mapping = {
                        "enabled": "pending",
                        "disabled": "cancelled",
                        "running": "running",
                        "completed": "completed",
                        "failed": "failed"
                    }
                    
                    discovery_job = DiscoveryJob(
                        id=job["id"],
                        name=metadata.get("original_discovery_name", job["name"].replace("Discovery: ", "")),
                        target_range=metadata.get("target_range", ""),
                        scan_type=metadata.get("discovery_config", {}).get("discovery_type", "network_scan"),
                        status=status_mapping.get(job.get("status", "enabled"), "pending"),
                        configuration=metadata.get("discovery_config", {}),
                        results={},  # Would need to get from job execution results
                        started_at=None,  # Would need to get from job executions
                        completed_at=None,  # Would need to get from job executions
                        created_by=job["created_by"],
                        created_at=job["created_at"]
                    )
                    discovery_jobs.append(discovery_job)
                
                return DiscoveryListResponse(
                    discovery_jobs=discovery_jobs,
                    total=automation_jobs.get("total", len(discovery_jobs)),
                    skip=skip,
                    limit=limit
                )
                
            except Exception as e:
                self.logger.error("Failed to fetch discovery jobs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch discovery jobs"
                )

        @self.app.post("/discovery/discovery-jobs", response_model=dict)
        async def create_discovery_job(discovery_data: DiscoveryCreate):
            """Create a new discovery job using the automation engine"""
            try:
                import json
                import ipaddress
                import httpx
                
                # Extract target range from config
                config = discovery_data.config or {}
                cidr_ranges = config.get('cidr_ranges', [])
                target_range = ', '.join(cidr_ranges) if cidr_ranges else ''
                
                # Calculate job size and estimated completion time (same validation as before)
                total_ips = 0
                warnings = []
                
                for cidr_range in cidr_ranges:
                    try:
                        if '/' in cidr_range:  # CIDR notation
                            network = ipaddress.ip_network(cidr_range, strict=False)
                            total_ips += len(list(network.hosts()))
                        elif '-' in cidr_range:  # Range notation
                            start_ip, end_ip = cidr_range.split('-')
                            start = ipaddress.ip_address(start_ip.strip())
                            end = ipaddress.ip_address(end_ip.strip())
                            total_ips += int(end) - int(start) + 1
                        else:  # Single IP or comma-separated IPs
                            ips = [ip.strip() for ip in cidr_range.split(',')]
                            total_ips += len(ips)
                    except Exception as e:
                        warnings.append(f"Invalid range format '{cidr_range}': {str(e)}")
                
                # Calculate estimated completion time
                services_count = len(config.get('services', []))
                
                if total_ips <= 50:
                    estimated_seconds = total_ips * 2.5
                    max_workers = 5
                elif total_ips <= 200:
                    estimated_seconds = total_ips * 1.5
                    max_workers = min(10, total_ips // 5)
                else:
                    estimated_seconds = total_ips * 0.75
                    max_workers = min(20, total_ips // 10)
                
                # HARD LIMITS - Prevent system crashes
                MAX_IPS_PER_JOB = 500
                MAX_TOTAL_OPERATIONS = 5000
                
                total_operations = total_ips * services_count
                
                # Enforce hard limits
                if total_ips > MAX_IPS_PER_JOB:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Discovery job too large: {total_ips} IPs exceeds maximum of {MAX_IPS_PER_JOB}. Please break into smaller ranges."
                    )
                
                if total_operations > MAX_TOTAL_OPERATIONS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Discovery job too complex: {total_operations} total operations (IPs × Services) exceeds maximum of {MAX_TOTAL_OPERATIONS}. Reduce IP range or disable some services."
                    )
                
                # Add warnings for large jobs
                if total_ips > 50:
                    if estimated_seconds > 300:  # > 5 minutes
                        minutes = int(estimated_seconds // 60)
                        warnings.append(f"Large job detected: {total_ips} IPs will take approximately {minutes} minutes to complete")
                    else:
                        warnings.append(f"Medium job detected: {total_ips} IPs will take approximately {int(estimated_seconds)} seconds to complete")
                
                if total_ips > 200:
                    warnings.append("Large job: Consider breaking this into smaller ranges for better performance")
                
                if total_operations > 2000:
                    warnings.append(f"Complex job: {total_operations} total operations may impact system performance")
                
                # Create discovery workflow definition
                discovery_workflow = {
                    "steps": [
                        {
                            "id": "ping_sweep",
                            "name": "Ping Sweep",
                            "library": "discovery-tools",
                            "function": "ping_sweep",
                            "inputs": {
                                "target_range": target_range,
                                "timeout": config.get('ping_timeout', 1)
                            },
                            "outputs": ["active_hosts", "active_count"]
                        },
                        {
                            "id": "port_scan",
                            "name": "Port Scan",
                            "library": "discovery-tools", 
                            "function": "port_scan",
                            "inputs": {
                                "hosts": "{{steps.ping_sweep.outputs.active_hosts}}",
                                "ports": config.get('ports', [21, 22, 23, 25, 53, 80, 135, 139, 443, 3389, 5985, 5986]),
                                "timeout": config.get('port_timeout', 3)
                            },
                            "outputs": ["scan_results", "hosts_with_open_ports"],
                            "depends_on": ["ping_sweep"]
                        },
                        {
                            "id": "service_detection",
                            "name": "Service Detection",
                            "library": "discovery-tools",
                            "function": "service_detection", 
                            "inputs": {
                                "scan_results": "{{steps.port_scan.outputs.scan_results}}"
                            },
                            "outputs": ["enhanced_results"],
                            "depends_on": ["port_scan"]
                        },
                        {
                            "id": "save_assets",
                            "name": "Save Discovered Assets",
                            "library": "discovery-tools",
                            "function": "save_discovered_assets",
                            "inputs": {
                                "discovery_results": "{{steps.service_detection.outputs.enhanced_results}}"
                            },
                            "outputs": ["saved_targets", "targets_saved"],
                            "depends_on": ["service_detection"]
                        }
                    ]
                }
                
                # Create automation job via API call
                automation_job_data = {
                    "name": f"Discovery: {discovery_data.name}",
                    "description": f"Network discovery job for {target_range}",
                    "workflow_definition": discovery_workflow,
                    "is_enabled": True,
                    "tags": ["discovery", "network-scan", discovery_data.discovery_type],
                    "job_type": "discovery",
                    "metadata": {
                        "discovery_config": config,
                        "target_range": target_range,
                        "total_ips": total_ips,
                        "estimated_duration_seconds": int(estimated_seconds),
                        "created_from": "asset-service",
                        "original_discovery_name": discovery_data.name
                    }
                }
                
                # Call automation service to create job
                async with httpx.AsyncClient() as client:
                    automation_response = await client.post(
                        "http://automation-service:3003/jobs",
                        json=automation_job_data,
                        timeout=30.0
                    )
                    
                    if automation_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to create automation job: {automation_response.text}"
                        )
                    
                    automation_job = automation_response.json()
                
                # Create a discovery job record that references the automation job
                discovery_job = DiscoveryJob(
                    id=automation_job["data"]["id"],  # Use automation job ID
                    name=discovery_data.name,
                    target_range=target_range,
                    scan_type=discovery_data.discovery_type,
                    status="pending",
                    configuration=config,
                    results={},
                    started_at=None,
                    completed_at=None,
                    created_by=1,  # TODO: Get from auth context
                    created_at=automation_job["data"]["created_at"]
                )
                
                response = {
                    "success": True,
                    "message": "Discovery job created using automation engine",
                    "data": discovery_job,
                    "automation_job_id": automation_job["data"]["id"],
                    "job_size_info": {
                        "total_ips": total_ips,
                        "estimated_duration_seconds": int(estimated_seconds),
                        "estimated_duration_human": f"{int(estimated_seconds // 60)}m {int(estimated_seconds % 60)}s" if estimated_seconds >= 60 else f"{int(estimated_seconds)}s",
                        "max_workers": max_workers,
                        "services_count": services_count
                    }
                }
                
                if warnings:
                    response["warnings"] = warnings
                
                return response
                
            except Exception as e:
                self.logger.error("Failed to create discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create discovery job"
                )

        @self.app.get("/discovery/discovery-jobs/{discovery_id}", response_model=dict)
        async def get_discovery_job(discovery_id: int):
            """Get discovery job by ID from automation service"""
            try:
                import httpx
                
                # Get job from automation service
                async with httpx.AsyncClient() as client:
                    automation_response = await client.get(
                        f"http://automation-service:3003/jobs/{discovery_id}",
                        timeout=30.0
                    )
                    
                    if automation_response.status_code == 404:
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    elif automation_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch job from automation service: {automation_response.text}"
                        )
                    
                    automation_job = automation_response.json()
                    job = automation_job.get("data", {})
                
                # Check if this is a discovery job
                if job.get("job_type") != "discovery":
                    raise HTTPException(status_code=404, detail="Discovery job not found")
                
                metadata = job.get("metadata", {})
                
                # Map automation job status to discovery status
                status_mapping = {
                    "enabled": "pending",
                    "disabled": "cancelled", 
                    "running": "running",
                    "completed": "completed",
                    "failed": "failed"
                }
                
                # Get job execution status if available
                try:
                    executions_response = await client.get(
                        f"http://automation-service:3003/executions?job_id={discovery_id}&limit=1",
                        timeout=30.0
                    )
                    
                    execution_data = None
                    if executions_response.status_code == 200:
                        executions = executions_response.json()
                        if executions.get("executions"):
                            execution_data = executions["executions"][0]
                except:
                    execution_data = None
                
                discovery_job = DiscoveryJob(
                    id=job["id"],
                    name=metadata.get("original_discovery_name", job["name"].replace("Discovery: ", "")),
                    target_range=metadata.get("target_range", ""),
                    scan_type=metadata.get("discovery_config", {}).get("discovery_type", "network_scan"),
                    status=execution_data.get("status", status_mapping.get(job.get("status", "enabled"), "pending")) if execution_data else status_mapping.get(job.get("status", "enabled"), "pending"),
                    configuration=metadata.get("discovery_config", {}),
                    results=execution_data.get("output_data", {}) if execution_data else {},
                    started_at=execution_data.get("started_at") if execution_data else None,
                    completed_at=execution_data.get("completed_at") if execution_data else None,
                    created_by=job["created_by"],
                    created_at=job["created_at"]
                )
                
                return {"success": True, "data": discovery_job}
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get discovery job"
                )

        @self.app.post("/discovery/discovery-jobs/{discovery_id}/run", response_model=dict)
        async def run_discovery_job(discovery_id: int):
            """Execute/run a discovery job via automation service"""
            try:
                import httpx
                
                # Execute the job via automation service using new direct endpoint
                async with httpx.AsyncClient() as client:
                    execution_response = await client.post(
                        f"http://automation-service:3003/jobs/{discovery_id}/run",
                        json={},
                        timeout=30.0
                    )
                    
                    if execution_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to execute discovery job: {execution_response.text}"
                        )
                    
                    execution_result = execution_response.json()
                    execution_data = execution_result.get("data", {})
                
                return {
                    "success": True,
                    "message": "Discovery job execution started",
                    "execution_id": execution_data.get("execution_id"),
                    "task_id": execution_data.get("task_id"),
                    "automation_job_id": discovery_id,
                    "status_url": f"http://automation-service:3003{execution_data.get('status_url', '')}",
                    "job_status_url": f"http://automation-service:3003{execution_data.get('job_status_url', '')}"
                }
                
            except Exception as e:
                self.logger.error("Failed to run discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to run discovery job"
                )

        @self.app.put("/discovery/discovery-jobs/{discovery_id}", response_model=dict)
        async def update_discovery_job(discovery_id: int, discovery_data: DiscoveryUpdate):
            """Update discovery job"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if discovery_data.status is not None:
                        updates.append(f"status = ${param_count}")
                        values.append(discovery_data.status)
                        param_count += 1
                        
                        # Set started_at if status is running
                        if discovery_data.status == 'running':
                            updates.append(f"started_at = ${param_count}")
                            values.append(datetime.utcnow())
                            param_count += 1
                        # Set completed_at if status is completed or failed
                        elif discovery_data.status in ['completed', 'failed']:
                            updates.append(f"completed_at = ${param_count}")
                            values.append(datetime.utcnow())
                            param_count += 1
                    
                    if discovery_data.configuration is not None:
                        import json
                        updates.append(f"configuration = ${param_count}")
                        values.append(json.dumps(discovery_data.configuration))
                        param_count += 1
                    
                    if discovery_data.results is not None:
                        import json
                        updates.append(f"results = ${param_count}")
                        values.append(json.dumps(discovery_data.results))
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    values.append(discovery_id)
                    
                    query = f"""
                        UPDATE assets.discovery_scans 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, target_range, scan_type, status, configuration, results,
                                  started_at, completed_at, created_by, created_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    
                    import json
                    discovery_job = DiscoveryJob(
                        id=row['id'],
                        name=row['name'],
                        target_range=row['target_range'],
                        scan_type=row['scan_type'],
                        status=row['status'],
                        configuration=row['configuration'] if isinstance(row['configuration'], dict) else (json.loads(row['configuration']) if row['configuration'] else {}),
                        results=row['results'] if isinstance(row['results'], dict) else (json.loads(row['results']) if row['results'] else {}),
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Discovery job updated", "data": discovery_job}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update discovery job"
                )

        @self.app.post("/discovery/discovery-jobs/{discovery_id}/cancel", response_model=dict)
        async def cancel_discovery_job(discovery_id: int):
            """Cancel a running discovery job"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if job exists
                    job = await conn.fetchrow(
                        "SELECT id, status FROM assets.discovery_scans WHERE id = $1", discovery_id
                    )
                    
                    if not job:
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    
                    if job['status'] != 'running':
                        raise HTTPException(status_code=400, detail="Job is not running")
                    
                    # Update job status to cancelled
                    await conn.execute("""
                        UPDATE assets.discovery_scans 
                        SET status = 'cancelled', completed_at = NOW()
                        WHERE id = $1
                    """, discovery_id)
                    
                    return {"success": True, "message": "Discovery job cancelled"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to cancel discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to cancel discovery job"
                )

        @self.app.delete("/discovery/discovery-jobs/{discovery_id}", response_model=dict)
        async def delete_discovery_job(discovery_id: int):
            """Delete discovery job"""
            try:
                import httpx
                
                # First verify this is a discovery job
                async with httpx.AsyncClient() as client:
                    get_response = await client.get(
                        f"http://automation-service:3003/jobs/{discovery_id}",
                        timeout=30.0
                    )
                    
                    if get_response.status_code == 404:
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    elif get_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to verify job: {get_response.text}"
                        )
                    
                    job_data = get_response.json().get("data", {})
                    if job_data.get("job_type") != "discovery":
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    
                    # Delete the job from automation service
                    delete_response = await client.delete(
                        f"http://automation-service:3003/jobs/{discovery_id}",
                        timeout=30.0
                    )
                    
                    if delete_response.status_code == 404:
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    elif delete_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to delete job: {delete_response.text}"
                        )
                    
                    return {"success": True, "message": "Discovery job deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete discovery job"
                )

        # ============================================================================
        # DISCOVERED TARGETS ENDPOINTS
        # ============================================================================
        
        @self.app.get("/discovery/targets", response_model=DiscoveredTargetListResponse)
        async def list_discovered_targets(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            job_id: Optional[int] = Query(None),
            status: Optional[str] = Query(None)
        ):
            """List discovered targets"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build query with filters
                    where_conditions = []
                    params = []
                    param_count = 1
                    
                    if job_id is not None:
                        where_conditions.append(f"discovery_job_id = ${param_count}")
                        params.append(job_id)
                        param_count += 1
                    
                    if status is not None:
                        where_conditions.append(f"import_status = ${param_count}")
                        params.append(status)
                        param_count += 1
                    
                    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM assets.discovered_targets{where_clause}"
                    total = await conn.fetchval(count_query, *params)
                    
                    # Get targets with pagination
                    query = f"""
                        SELECT id, discovery_job_id, hostname, ip_address, os_type, os_version,
                               services, system_info, duplicate_status, existing_target_id,
                               import_status, discovered_at
                        FROM assets.discovered_targets
                        {where_clause}
                        ORDER BY discovered_at DESC 
                        LIMIT ${param_count} OFFSET ${param_count + 1}
                    """
                    params.extend([limit, skip])
                    rows = await conn.fetch(query, *params)
                    
                    targets = []
                    for row in rows:
                        import json
                        services_data = row['services'] if isinstance(row['services'], list) else (json.loads(row['services']) if row['services'] else [])
                        services = [DiscoveredService(**service) for service in services_data]
                        
                        targets.append(DiscoveredTarget(
                            id=row['id'],
                            discovery_job_id=row['discovery_job_id'],
                            hostname=row['hostname'],
                            ip_address=str(row['ip_address']),
                            os_type=row['os_type'],
                            os_version=row['os_version'],
                            services=services,
                            preferred_service=services[0] if services else None,
                            system_info=row['system_info'] if isinstance(row['system_info'], dict) else (json.loads(row['system_info']) if row['system_info'] else {}),
                            duplicate_status=row['duplicate_status'],
                            existing_target_id=row['existing_target_id'],
                            import_status=row['import_status'],
                            discovered_at=row['discovered_at'].isoformat()
                        ))
                    
                    return DiscoveredTargetListResponse(targets=targets, total=total)
            except Exception as e:
                self.logger.error("Failed to fetch discovered targets", error=str(e))
                # Return empty list instead of error for better UX
                return DiscoveredTargetListResponse(targets=[], total=0)

        @self.app.get("/discovery/targets/{target_id}", response_model=dict)
        async def get_discovered_target(target_id: int):
            """Get discovered target by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, discovery_job_id, hostname, ip_address, os_type, os_version,
                               services, system_info, duplicate_status, existing_target_id,
                               import_status, discovered_at
                        FROM assets.discovered_targets WHERE id = $1
                    """, target_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Discovered target not found")
                    
                    import json
                    services_data = row['services'] if isinstance(row['services'], list) else (json.loads(row['services']) if row['services'] else [])
                    services = [DiscoveredService(**service) for service in services_data]
                    
                    target = DiscoveredTarget(
                        id=row['id'],
                        discovery_job_id=row['discovery_job_id'],
                        hostname=row['hostname'],
                        ip_address=str(row['ip_address']),
                        os_type=row['os_type'],
                        os_version=row['os_version'],
                        services=services,
                        preferred_service=services[0] if services else None,
                        system_info=row['system_info'] if isinstance(row['system_info'], dict) else (json.loads(row['system_info']) if row['system_info'] else {}),
                        duplicate_status=row['duplicate_status'],
                        existing_target_id=row['existing_target_id'],
                        import_status=row['import_status'],
                        discovered_at=row['discovered_at'].isoformat()
                    )
                    
                    return {"success": True, "data": target}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get discovered target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get discovered target"
                )

        @self.app.put("/discovery/targets/{target_id}", response_model=dict)
        async def update_discovered_target(target_id: int, target_data: DiscoveredTargetUpdate):
            """Update discovered target"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if target_data.hostname is not None:
                        updates.append(f"hostname = ${param_count}")
                        values.append(target_data.hostname)
                        param_count += 1
                    
                    if target_data.os_type is not None:
                        updates.append(f"os_type = ${param_count}")
                        values.append(target_data.os_type)
                        param_count += 1
                    
                    if target_data.os_version is not None:
                        updates.append(f"os_version = ${param_count}")
                        values.append(target_data.os_version)
                        param_count += 1
                    
                    if target_data.import_status is not None:
                        updates.append(f"import_status = ${param_count}")
                        values.append(target_data.import_status)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    values.append(target_id)
                    
                    query = f"""
                        UPDATE assets.discovered_targets 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, discovery_job_id, hostname, ip_address, os_type, os_version,
                                  services, system_info, duplicate_status, existing_target_id,
                                  import_status, discovered_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Discovered target not found")
                    
                    import json
                    services_data = row['services'] if isinstance(row['services'], list) else (json.loads(row['services']) if row['services'] else [])
                    services = [DiscoveredService(**service) for service in services_data]
                    
                    target = DiscoveredTarget(
                        id=row['id'],
                        discovery_job_id=row['discovery_job_id'],
                        hostname=row['hostname'],
                        ip_address=str(row['ip_address']),
                        os_type=row['os_type'],
                        os_version=row['os_version'],
                        services=services,
                        preferred_service=services[0] if services else None,
                        system_info=row['system_info'] if isinstance(row['system_info'], dict) else (json.loads(row['system_info']) if row['system_info'] else {}),
                        duplicate_status=row['duplicate_status'],
                        existing_target_id=row['existing_target_id'],
                        import_status=row['import_status'],
                        discovered_at=row['discovered_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Target updated", "data": target}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update discovered target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update discovered target"
                )

        @self.app.delete("/discovery/targets/{target_id}", response_model=dict)
        async def delete_discovered_target(target_id: int):
            """Delete discovered target"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM assets.discovered_targets WHERE id = $1", target_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Discovered target not found")
                    
                    return {"success": True, "message": "Target deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete discovered target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete discovered target"
                )

        @self.app.post("/discovery/targets/ignore", response_model=dict)
        async def ignore_targets(request: dict):
            """Mark targets as ignored"""
            try:
                target_ids = request.get('target_ids', [])
                if not target_ids:
                    raise HTTPException(status_code=400, detail="No target IDs provided")
                
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute("""
                        UPDATE assets.discovered_targets 
                        SET import_status = 'ignored'
                        WHERE id = ANY($1)
                    """, target_ids)
                    
                    return {"success": True, "ignored": len(target_ids)}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to ignore targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to ignore targets"
                )

        @self.app.post("/discovery/targets/bulk-delete", response_model=dict)
        async def bulk_delete_targets(request: dict):
            """Bulk delete targets"""
            try:
                target_ids = request.get('target_ids', [])
                if not target_ids:
                    raise HTTPException(status_code=400, detail="No target IDs provided")
                
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute("""
                        DELETE FROM assets.discovered_targets 
                        WHERE id = ANY($1)
                    """, target_ids)
                    
                    # Extract the number of deleted rows from the result
                    deleted_count = int(result.split()[-1]) if result.startswith('DELETE') else 0
                    
                    return {"success": True, "deleted": deleted_count}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to bulk delete targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to bulk delete targets"
                )

        @self.app.post("/discovery/import-targets", response_model=dict)
        async def import_targets(request: dict):
            """Import discovered targets as managed targets"""
            try:
                target_ids = request.get('target_ids', [])
                if not target_ids:
                    raise HTTPException(status_code=400, detail="No target IDs provided")
                
                imported_count = 0
                failed_count = 0
                details = []
                
                async with self.db.pool.acquire() as conn:
                    for target_id in target_ids:
                        try:
                            # Get discovered target
                            discovered = await conn.fetchrow("""
                                SELECT hostname, ip_address, os_type, os_version, services, system_info
                                FROM assets.discovered_targets WHERE id = $1
                            """, target_id)
                            
                            if not discovered:
                                failed_count += 1
                                details.append(f"Target {target_id} not found")
                                continue
                            
                            # Insert into managed targets (mapping to existing schema)
                            target_name = discovered['hostname'] or f"Target-{str(discovered['ip_address'])}"
                            description = f"Imported from discovery - {discovered['os_type']} {discovered['os_version']}"
                            
                            import json
                            metadata = {
                                'os_type': discovered['os_type'],
                                'os_version': discovered['os_version'],
                                'services': discovered['services'] if isinstance(discovered['services'], list) else (json.loads(discovered['services']) if discovered['services'] else []),
                                'system_info': discovered['system_info'] if isinstance(discovered['system_info'], dict) else (json.loads(discovered['system_info']) if discovered['system_info'] else {}),
                                'imported_from_discovery': True
                            }
                            
                            await conn.execute("""
                                INSERT INTO assets.targets (name, description, host, target_type, 
                                                           connection_type, metadata, created_by)
                                VALUES ($1, $2, $3, $4, $5, $6, 1)
                            """, target_name, description, str(discovered['ip_address']), 
                                 'server', 'ssh', json.dumps(metadata))
                            
                            # Update discovered target status
                            await conn.execute("""
                                UPDATE assets.discovered_targets 
                                SET import_status = 'imported'
                                WHERE id = $1
                            """, target_id)
                            
                            imported_count += 1
                            details.append(f"Target {target_id} imported successfully")
                            
                        except Exception as e:
                            failed_count += 1
                            details.append(f"Target {target_id} failed: {str(e)}")
                
                return {
                    "success": True,
                    "imported": imported_count,
                    "failed": failed_count,
                    "details": details
                }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to import targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to import targets"
                )

        @self.app.post("/discovery/validate-network-ranges", response_model=dict)
        async def validate_network_ranges(request: dict):
            """Validate network ranges for discovery"""
            try:
                ranges = request.get('ranges', [])
                if not ranges:
                    raise HTTPException(status_code=400, detail="No ranges provided")
                
                results = []
                for range_str in ranges:
                    try:
                        import ipaddress
                        # Try to parse as CIDR
                        network = ipaddress.ip_network(range_str, strict=False)
                        
                        # Calculate some basic info
                        num_hosts = network.num_addresses
                        if network.version == 4:
                            # For IPv4, subtract network and broadcast addresses if not a single host
                            if network.prefixlen < 31:
                                num_hosts -= 2
                        
                        results.append({
                            "range": range_str,
                            "valid": True,
                            "network": str(network),
                            "num_hosts": num_hosts,
                            "version": network.version,
                            "is_private": network.is_private,
                            "message": f"Valid {network.version} network with {num_hosts} hosts"
                        })
                    except ValueError as e:
                        results.append({
                            "range": range_str,
                            "valid": False,
                            "error": str(e),
                            "message": f"Invalid network range: {str(e)}"
                        })
                
                return {"success": True, "results": results}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to validate network ranges", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to validate network ranges"
                )

        # ============================================================================
        # TARGET GROUPS ENDPOINTS
        # ============================================================================
        
        @self.app.get("/target-groups", response_model=TargetGroupListResponse)
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
                    
                    result_groups = []
                    for group in groups:
                        group_dict = dict(group)
                        group_dict['created_at'] = group_dict['created_at'].isoformat()
                        if group_dict['updated_at']:
                            group_dict['updated_at'] = group_dict['updated_at'].isoformat()
                        
                        # Add target counts if requested
                        if include_counts:
                            # Direct targets in this group
                            direct_count = await conn.fetchval("""
                                SELECT COUNT(*) FROM assets.target_group_memberships 
                                WHERE group_id = $1
                            """, group['id'])
                            
                            # All targets including descendants
                            total_count = await conn.fetchval("""
                                SELECT COUNT(DISTINCT m.target_id) 
                                FROM assets.target_group_memberships m
                                JOIN assets.target_groups g ON m.group_id = g.id
                                WHERE g.path LIKE $1
                            """, group['path'] + '%')
                            
                            group_dict['direct_target_count'] = direct_count
                            group_dict['target_count'] = total_count
                        
                        result_groups.append(group_dict)
                    
                    return TargetGroupListResponse(
                        groups=result_groups,
                        total=total
                    )
            except Exception as e:
                self.logger.error("Failed to list target groups", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to list target groups"
                )

        @self.app.post("/target-groups", response_model=dict)
        async def create_target_group(group_data: TargetGroupCreate):
            """Create a new target group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Validate parent group exists if specified
                    if group_data.parent_group_id:
                        parent = await conn.fetchrow("""
                            SELECT level FROM assets.target_groups WHERE id = $1
                        """, group_data.parent_group_id)
                        
                        if not parent:
                            raise HTTPException(status_code=404, detail="Parent group not found")
                        
                        if parent['level'] >= 3:
                            raise HTTPException(
                                status_code=400, 
                                detail="Cannot create group: maximum depth of 3 levels exceeded"
                            )
                    
                    # Check for duplicate name within same parent
                    existing = await conn.fetchval("""
                        SELECT id FROM assets.target_groups 
                        WHERE name = $1 AND parent_group_id IS NOT DISTINCT FROM $2
                    """, group_data.name, group_data.parent_group_id)
                    
                    if existing:
                        raise HTTPException(
                            status_code=400, 
                            detail="Group name already exists at this level"
                        )
                    
                    # Insert new group (triggers will handle path and level)
                    group_id = await conn.fetchval("""
                        INSERT INTO assets.target_groups (name, description, parent_group_id, color, icon)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                    """, group_data.name, group_data.description, group_data.parent_group_id,
                        group_data.color, group_data.icon)
                    
                    # Get the created group with computed path and level
                    created_group = await conn.fetchrow("""
                        SELECT id, name, description, parent_group_id, path, level, 
                               color, icon, created_at, updated_at
                        FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    result = dict(created_group)
                    result['created_at'] = result['created_at'].isoformat()
                    if result['updated_at']:
                        result['updated_at'] = result['updated_at'].isoformat()
                    
                    return {"success": True, "group": result}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to create target group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create target group"
                )

        @self.app.get("/target-groups/{group_id}", response_model=dict)
        async def get_target_group(group_id: int, include_children: bool = Query(False)):
            """Get target group by ID with optional children"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get the group
                    group = await conn.fetchrow("""
                        SELECT id, name, description, parent_group_id, path, level, 
                               color, icon, created_at, updated_at
                        FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    if not group:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    result = dict(group)
                    result['created_at'] = result['created_at'].isoformat()
                    if result['updated_at']:
                        result['updated_at'] = result['updated_at'].isoformat()
                    
                    # Add target counts
                    direct_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM assets.target_group_memberships 
                        WHERE group_id = $1
                    """, group_id)
                    
                    total_count = await conn.fetchval("""
                        SELECT COUNT(DISTINCT m.target_id) 
                        FROM assets.target_group_memberships m
                        JOIN assets.target_groups g ON m.group_id = g.id
                        WHERE g.path LIKE $1
                    """, group['path'] + '%')
                    
                    result['direct_target_count'] = direct_count
                    result['target_count'] = total_count
                    
                    # Add children if requested
                    if include_children:
                        children = await conn.fetch("""
                            SELECT id, name, description, parent_group_id, path, level, 
                                   color, icon, created_at, updated_at
                            FROM assets.target_groups 
                            WHERE parent_group_id = $1
                            ORDER BY name
                        """, group_id)
                        
                        result['children'] = []
                        for child in children:
                            child_dict = dict(child)
                            child_dict['created_at'] = child_dict['created_at'].isoformat()
                            if child_dict['updated_at']:
                                child_dict['updated_at'] = child_dict['updated_at'].isoformat()
                            result['children'].append(child_dict)
                    
                    return {"success": True, "group": result}
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
                    # Check if group exists
                    existing = await conn.fetchrow("""
                        SELECT id, parent_group_id FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    if not existing:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    # Validate parent group if being changed
                    if group_data.parent_group_id is not None and group_data.parent_group_id != existing['parent_group_id']:
                        if group_data.parent_group_id:
                            parent = await conn.fetchrow("""
                                SELECT level FROM assets.target_groups WHERE id = $1
                            """, group_data.parent_group_id)
                            
                            if not parent:
                                raise HTTPException(status_code=404, detail="Parent group not found")
                            
                            if parent['level'] >= 3:
                                raise HTTPException(
                                    status_code=400, 
                                    detail="Cannot move group: maximum depth of 3 levels exceeded"
                                )
                    
                    # Check for duplicate name if name is being changed
                    if group_data.name:
                        duplicate = await conn.fetchval("""
                            SELECT id FROM assets.target_groups 
                            WHERE name = $1 AND parent_group_id IS NOT DISTINCT FROM $2 AND id != $3
                        """, group_data.name, 
                            group_data.parent_group_id if group_data.parent_group_id is not None else existing['parent_group_id'],
                            group_id)
                        
                        if duplicate:
                            raise HTTPException(
                                status_code=400, 
                                detail="Group name already exists at this level"
                            )
                    
                    # Build update query dynamically
                    update_fields = []
                    update_values = []
                    param_count = 1
                    
                    if group_data.name is not None:
                        update_fields.append(f"name = ${param_count}")
                        update_values.append(group_data.name)
                        param_count += 1
                    
                    if group_data.description is not None:
                        update_fields.append(f"description = ${param_count}")
                        update_values.append(group_data.description)
                        param_count += 1
                    
                    if group_data.parent_group_id is not None:
                        update_fields.append(f"parent_group_id = ${param_count}")
                        update_values.append(group_data.parent_group_id)
                        param_count += 1
                    
                    if group_data.color is not None:
                        update_fields.append(f"color = ${param_count}")
                        update_values.append(group_data.color)
                        param_count += 1
                    
                    if group_data.icon is not None:
                        update_fields.append(f"icon = ${param_count}")
                        update_values.append(group_data.icon)
                        param_count += 1
                    
                    if not update_fields:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    update_fields.append(f"updated_at = ${param_count}")
                    update_values.append("CURRENT_TIMESTAMP")
                    param_count += 1
                    
                    update_values.append(group_id)
                    
                    query = f"""
                        UPDATE assets.target_groups 
                        SET {', '.join(update_fields)}
                        WHERE id = ${param_count}
                    """
                    
                    await conn.execute(query, *update_values[:-1], group_id)
                    
                    # Get updated group
                    updated_group = await conn.fetchrow("""
                        SELECT id, name, description, parent_group_id, path, level, 
                               color, icon, created_at, updated_at
                        FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    result = dict(updated_group)
                    result['created_at'] = result['created_at'].isoformat()
                    if result['updated_at']:
                        result['updated_at'] = result['updated_at'].isoformat()
                    
                    return {"success": True, "group": result}
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
            """Delete target group (and all descendants)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if group exists
                    group = await conn.fetchrow("""
                        SELECT path FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    if not group:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    # First count how many groups will be deleted
                    deleted_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM assets.target_groups 
                        WHERE path LIKE $1
                    """, group['path'] + '%')
                    
                    # Delete all descendants (cascade will handle memberships)
                    await conn.execute("""
                        DELETE FROM assets.target_groups 
                        WHERE path LIKE $1
                    """, group['path'] + '%')
                    
                    return {"success": True, "deleted_groups": deleted_count}
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
            include_descendants: bool = Query(False, description="Include targets from descendant groups"),
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """Get targets in a group, optionally including descendants"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if group exists
                    group = await conn.fetchrow("""
                        SELECT path FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    if not group:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    if include_descendants:
                        # Get targets from this group and all descendants
                        targets_query = """
                            SELECT DISTINCT t.id, t.name, t.hostname, t.ip_address, t.os_type, 
                                   t.os_version, t.description, t.tags, t.created_at, t.updated_at
                            FROM assets.enhanced_targets t
                            JOIN assets.target_group_memberships m ON t.id = m.target_id
                            JOIN assets.target_groups g ON m.group_id = g.id
                            WHERE g.path LIKE $1
                            ORDER BY t.name
                            OFFSET $2 LIMIT $3
                        """
                        targets = await conn.fetch(targets_query, group['path'] + '%', skip, limit)
                        
                        total = await conn.fetchval("""
                            SELECT COUNT(DISTINCT t.id)
                            FROM assets.enhanced_targets t
                            JOIN assets.target_group_memberships m ON t.id = m.target_id
                            JOIN assets.target_groups g ON m.group_id = g.id
                            WHERE g.path LIKE $1
                        """, group['path'] + '%')
                    else:
                        # Get targets only from this specific group
                        targets_query = """
                            SELECT t.id, t.name, t.hostname, t.ip_address, t.os_type, 
                                   t.os_version, t.description, t.tags, t.created_at, t.updated_at
                            FROM assets.enhanced_targets t
                            JOIN assets.target_group_memberships m ON t.id = m.target_id
                            WHERE m.group_id = $1
                            ORDER BY t.name
                            OFFSET $2 LIMIT $3
                        """
                        targets = await conn.fetch(targets_query, group_id, skip, limit)
                        
                        total = await conn.fetchval("""
                            SELECT COUNT(*)
                            FROM assets.target_group_memberships
                            WHERE group_id = $1
                        """, group_id)
                    
                    # Format targets
                    result_targets = []
                    for target in targets:
                        # Get services for this target (summary version)
                        service_rows = await conn.fetch("""
                            SELECT id, service_type, port, is_default, is_secure, is_enabled, notes,
                                   credential_type, connection_status, last_tested_at, created_at
                            FROM assets.target_services
                            WHERE target_id = $1
                            ORDER BY is_default DESC, service_type, port
                        """, target['id'])
                        
                        services = []
                        for service_row in service_rows:
                            services.append(TargetServiceSummary(
                                id=service_row['id'],
                                target_id=target['id'],
                                service_type=service_row['service_type'],
                                port=service_row['port'],
                                is_default=service_row['is_default'],
                                is_secure=service_row['is_secure'],
                                is_enabled=service_row['is_enabled'],
                                notes=service_row['notes'],
                                credential_type=service_row['credential_type'],
                                connection_status=service_row['connection_status'],
                                last_tested_at=service_row['last_tested_at'].isoformat() if service_row['last_tested_at'] else None,
                                created_at=service_row['created_at'].isoformat()
                            ))
                        
                        import json
                        result_targets.append(EnhancedTargetSummary(
                            id=target['id'],
                            name=target['name'],
                            hostname=target['hostname'],
                            ip_address=target['ip_address'],
                            os_type=target['os_type'],
                            os_version=target['os_version'],
                            description=target['description'],
                            tags=json.loads(target['tags']) if target['tags'] else [],
                            services=services,
                            created_at=target['created_at'].isoformat(),
                            updated_at=target['updated_at'].isoformat() if target['updated_at'] else None
                        ))
                    
                    return TargetGroupTargetsResponse(
                        targets=result_targets,
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
        async def add_targets_to_group(group_id: int, membership_data: TargetGroupMembershipCreate):
            """Add targets to a group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if group exists
                    group_exists = await conn.fetchval("""
                        SELECT id FROM assets.target_groups WHERE id = $1
                    """, group_id)
                    
                    if not group_exists:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    # Validate all targets exist
                    existing_targets = await conn.fetch("""
                        SELECT id FROM assets.enhanced_targets WHERE id = ANY($1)
                    """, membership_data.target_ids)
                    
                    existing_ids = {t['id'] for t in existing_targets}
                    missing_ids = set(membership_data.target_ids) - existing_ids
                    
                    if missing_ids:
                        raise HTTPException(
                            status_code=404, 
                            detail=f"Targets not found: {list(missing_ids)}"
                        )
                    
                    # Add memberships (ignore duplicates)
                    added_count = 0
                    for target_id in membership_data.target_ids:
                        try:
                            await conn.execute("""
                                INSERT INTO assets.target_group_memberships (target_id, group_id)
                                VALUES ($1, $2)
                            """, target_id, group_id)
                            added_count += 1
                        except:
                            # Ignore duplicate key errors
                            pass
                    
                    return {
                        "success": True, 
                        "added": added_count,
                        "skipped": len(membership_data.target_ids) - added_count
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
            """Remove a target from a group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Remove membership
                    deleted = await conn.fetchval("""
                        DELETE FROM assets.target_group_memberships 
                        WHERE group_id = $1 AND target_id = $2
                        RETURNING id
                    """, group_id, target_id)
                    
                    if not deleted:
                        raise HTTPException(
                            status_code=404, 
                            detail="Target not found in this group"
                        )
                    
                    return {"success": True, "removed": True}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to remove target from group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to remove target from group"
                )

        @self.app.get("/target-groups-tree", response_model=dict)
        async def get_target_groups_tree():
            """Get target groups as a hierarchical tree structure"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get all groups ordered by path for efficient tree building
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
                        group_dict = dict(group)
                        group_dict['created_at'] = group_dict['created_at'].isoformat()
                        if group_dict['updated_at']:
                            group_dict['updated_at'] = group_dict['updated_at'].isoformat()
                        group_dict['children'] = []
                        
                        # Add target count
                        target_count = await conn.fetchval("""
                            SELECT COUNT(DISTINCT m.target_id) 
                            FROM assets.target_group_memberships m
                            JOIN assets.target_groups g ON m.group_id = g.id
                            WHERE g.path LIKE $1
                        """, group['path'] + '%')
                        group_dict['target_count'] = target_count
                        
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
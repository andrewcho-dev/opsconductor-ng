#!/usr/bin/env python3
"""
OpsConductor Asset Service
Handles targets with embedded credentials
"""

import sys
import os
import json
import base64
from cryptography.fernet import Fernet
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

class TargetServiceSummary(BaseModel):
    id: int
    service_type: str
    port: int
    is_default: bool
    is_secure: bool
    is_enabled: bool
    credential_type: Optional[str]
    has_credentials: bool
    connection_status: Optional[str] = 'unknown'
    last_tested_at: Optional[str] = None

class EnhancedTargetCreate(BaseModel):
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    services: List[TargetServiceCreate] = []

class EnhancedTargetSummary(BaseModel):
    id: int
    name: str
    hostname: str
    ip_address: Optional[str]
    os_type: Optional[str]
    os_version: Optional[str]
    description: Optional[str]
    tags: List[str]
    services: List[TargetServiceSummary]
    created_at: str
    updated_at: Optional[str]

class EnhancedTargetListResponse(BaseModel):
    targets: List[EnhancedTargetSummary]
    total: int
    skip: int
    limit: int

class EnhancedTargetUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

# ============================================================================
# ASSET SERVICE
# ============================================================================

class AssetService(BaseService):
    def __init__(self):
        super().__init__(
            name="asset-service",
            version="1.0.0",
            port=3002
        )
        # Initialize encryption key (in production, this should be from environment/key management)
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        if encryption_key and encryption_key != 'your-encryption-key-here':
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            self.cipher_suite = Fernet(encryption_key)
        else:
            # Generate a new key if none provided or placeholder
            self.cipher_suite = Fernet(Fernet.generate_key())
        self.setup_routes()
    
    def _encrypt_credential(self, credential: str) -> str:
        """Encrypt a credential string"""
        if not credential:
            return None
        return base64.b64encode(self.cipher_suite.encrypt(credential.encode())).decode()
    
    def _decrypt_credential(self, encrypted_credential: str) -> str:
        """Decrypt a credential string"""
        if not encrypted_credential:
            return None
        try:
            return self.cipher_suite.decrypt(base64.b64decode(encrypted_credential.encode())).decode()
        except Exception:
            return None  # Return None if decryption fails
    
    def _get_current_user_id(self) -> int:
        """Get current user ID from authentication context
        For now returns 1, but should be replaced with proper auth"""
        # TODO: Implement proper authentication context
        return 1
    
    async def _resolve_ip_address(self, hostname: str) -> str:
        """Resolve hostname to IP address"""
        import socket
        try:
            # Try to resolve hostname to IP
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except socket.gaierror:
            # If resolution fails, return the hostname as-is
            return hostname
    
    async def _detect_os_version(self, hostname: str, port: int = None) -> str:
        """Attempt to detect OS version through various methods"""
        # This is a simplified implementation
        # In production, you might use nmap, SSH banner detection, etc.
        try:
            # For now, return "Unknown" but this could be enhanced with:
            # - SSH banner detection
            # - HTTP server headers
            # - SNMP queries
            # - nmap OS detection
            return "Unknown"
        except Exception:
            return "Unknown"

    def setup_routes(self):
        """Setup FastAPI routes"""
        
        # ============================================================================
        # TARGET ENDPOINTS
        # ============================================================================
        
        @self.app.get("/targets", response_model=EnhancedTargetListResponse)
        async def list_targets(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            search: Optional[str] = Query(None, description="Search in name, hostname, or description"),
            os_type: Optional[str] = Query(None, description="Filter by OS type"),
            tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)")
        ):
            """List all targets with optional filtering"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build WHERE clause
                    where_conditions = []
                    params = []
                    param_count = 1
                    
                    if search:
                        where_conditions.append(f"(t.name ILIKE ${param_count} OR t.hostname ILIKE ${param_count} OR t.description ILIKE ${param_count})")
                        params.append(f"%{search}%")
                        param_count += 1
                    
                    if os_type:
                        where_conditions.append(f"t.os_type = ${param_count}")
                        params.append(os_type)
                        param_count += 1
                    
                    if tags:
                        tag_list = [tag.strip() for tag in tags.split(',')]
                        where_conditions.append(f"t.tags::jsonb ?| ${param_count}")
                        params.append(tag_list)
                        param_count += 1
                    
                    where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"
                    
                    # Get targets
                    targets_query = f"""
                        SELECT t.id, t.name, t.hostname, t.ip_address, t.os_type, t.os_version, t.description, t.tags, 
                               t.created_at, t.updated_at
                        FROM assets.enhanced_targets t
                        WHERE {where_clause}
                        ORDER BY t.created_at DESC
                        LIMIT ${param_count} OFFSET ${param_count + 1}
                    """
                    params.extend([limit, skip])
                    targets = await conn.fetch(targets_query, *params)
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM assets.enhanced_targets t WHERE {where_clause}"
                    total = await conn.fetchval(count_query, *params[:-2])  # Exclude limit and offset
                    
                    # Build target list with services
                    target_list = []
                    for target_row in targets:
                        # Get services for this target
                        service_rows = await conn.fetch("""
                            SELECT id, target_id, service_type, port, is_default, is_secure, 
                                   is_enabled, notes, credential_type, created_at,
                                   connection_status, last_tested_at
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
                                has_credentials=service_row['credential_type'] is not None,
                                connection_status=service_row['connection_status'],
                                last_tested_at=service_row['last_tested_at'].isoformat() if service_row['last_tested_at'] else None
                            ))
                        
                        # Parse tags
                        tags = target_row['tags']
                        if isinstance(tags, str):
                            tags = json.loads(tags)
                        elif tags is None:
                            tags = []
                        
                        target_list.append(EnhancedTargetSummary(
                            id=target_row['id'],
                            name=target_row['name'],
                            hostname=target_row['hostname'],
                            ip_address=target_row['ip_address'] or await self._resolve_ip_address(target_row['hostname']),
                            os_type=target_row['os_type'],
                            os_version=target_row['os_version'] or "Unknown",
                            description=target_row['description'],
                            tags=tags,
                            services=services,
                            created_at=target_row['created_at'].isoformat(),
                            updated_at=target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                        ))
                    
                    return EnhancedTargetListResponse(
                        targets=target_list,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to list targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to list targets"
                )

        @self.app.post("/targets", response_model=dict)
        async def create_target(target_data: EnhancedTargetCreate):
            """Create a new target with services and credentials"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Insert target into enhanced_targets table
                        target_id = await conn.fetchval("""
                            INSERT INTO assets.enhanced_targets (name, hostname, ip_address, os_type, os_version, description, tags)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id
                        """, target_data.name, target_data.hostname, target_data.ip_address, 
                             target_data.os_type or 'other', target_data.os_version, 
                             target_data.description, json.dumps(target_data.tags))
                        
                        # Insert services with credentials
                        for service in target_data.services:
                            # Prepare encrypted credential fields
                            encrypted_password = self._encrypt_credential(service.password)
                            encrypted_private_key = self._encrypt_credential(service.private_key)
                            encrypted_api_key = self._encrypt_credential(service.api_key)
                            encrypted_bearer_token = self._encrypt_credential(service.bearer_token)
                            encrypted_certificate = self._encrypt_credential(service.certificate)
                            encrypted_passphrase = self._encrypt_credential(service.passphrase)
                            
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
            """Get target by ID with all services and credentials"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get target
                    target_row = await conn.fetchrow("""
                        SELECT id, name, host, target_type, description, tags, created_at, updated_at
                        FROM assets.targets WHERE id = $1
                    """, target_id)
                    
                    if not target_row:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    # Get services
                    service_rows = await conn.fetch("""
                        SELECT id, target_id, service_type, port, is_default, is_secure, is_enabled, notes,
                               credential_type, username, password_encrypted, public_key, domain, created_at, 
                               connection_status, last_tested_at
                        FROM assets.target_services 
                        WHERE target_id = $1 
                        ORDER BY is_default DESC, port ASC
                    """, target_id)
                    
                    services = []
                    for service_row in service_rows:
                        service_dict = {
                            "id": service_row['id'],
                            "target_id": service_row['target_id'],
                            "service_type": service_row['service_type'],
                            "port": service_row['port'],
                            "is_default": service_row['is_default'],
                            "is_secure": service_row['is_secure'],
                            "is_enabled": service_row['is_enabled'],
                            "notes": service_row['notes'],
                            "created_at": service_row['created_at'].isoformat(),
                            "credential_type": service_row['credential_type'],
                            "has_credentials": service_row['credential_type'] is not None,
                            "connection_status": service_row['connection_status'],
                            "last_tested_at": service_row['last_tested_at'].isoformat() if service_row['last_tested_at'] else None
                        }
                        
                        # Add credential fields including decrypted password for automation
                        if service_row['credential_type']:
                            service_dict.update({
                                "username": service_row['username'],
                                "public_key": service_row['public_key'],
                                "domain": service_row['domain']
                            })
                            
                            # Decrypt password for automation purposes
                            if service_row['password_encrypted']:
                                decrypted_password = self._decrypt_credential(service_row['password_encrypted'])
                                if decrypted_password:
                                    service_dict["password"] = decrypted_password
                        
                        services.append(service_dict)
                    
                    # Parse tags
                    tags = target_row['tags']
                    if isinstance(tags, str):
                        tags = json.loads(tags)
                    elif tags is None:
                        tags = []
                    
                    target_dict = {
                        "id": target_row['id'],
                        "name": target_row['name'],
                        "hostname": target_row['host'],
                        "ip_address": await self._resolve_ip_address(target_row['host']),
                        "os_type": target_row['target_type'],
                        "os_version": "Unknown",  # Not available in current schema
                        "description": target_row['description'],
                        "tags": tags,
                        "services": services,
                        "created_at": target_row['created_at'].isoformat(),
                        "updated_at": target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                    }
                    
                    return {"success": True, "data": target_dict}
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
            """Update target information"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if target exists
                    existing = await conn.fetchval("SELECT id FROM assets.targets WHERE id = $1", target_id)
                    if not existing:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    # Build update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if target_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(target_data.name)
                        param_count += 1
                    
                    if target_data.hostname is not None:
                        updates.append(f"host = ${param_count}")
                        values.append(target_data.hostname)
                        param_count += 1
                    
                    if target_data.os_type is not None:
                        updates.append(f"target_type = ${param_count}")
                        values.append(target_data.os_type)
                        param_count += 1
                    
                    if target_data.description is not None:
                        updates.append(f"description = ${param_count}")
                        values.append(target_data.description)
                        param_count += 1
                    
                    if target_data.tags is not None:
                        updates.append(f"tags = ${param_count}")
                        values.append(json.dumps(target_data.tags))
                        param_count += 1
                    
                    if not updates:
                        return {"success": True, "message": "No changes to update"}
                    
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
            """Delete target and all associated services"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Check if target exists
                        existing = await conn.fetchval("SELECT id FROM assets.enhanced_targets WHERE id = $1", target_id)
                        if not existing:
                            raise HTTPException(status_code=404, detail="Target not found")
                        
                        # Delete associated services (will cascade due to foreign key)
                        await conn.execute("DELETE FROM assets.target_services WHERE target_id = $1", target_id)
                        
                        # Delete target
                        result = await conn.execute("DELETE FROM assets.enhanced_targets WHERE id = $1", target_id)
                        
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
                    
                    # Real connection test
                    import time
                    import socket
                    import asyncio
                    
                    start_time = time.time()
                    success = False
                    error_message = None
                    
                    try:
                        # Test basic TCP connectivity
                        port = service_row['port']
                        future = asyncio.open_connection(host, port)
                        reader, writer = await asyncio.wait_for(future, timeout=10.0)
                        writer.close()
                        await writer.wait_closed()
                        success = True
                    except asyncio.TimeoutError:
                        error_message = f"Connection timeout to {host}:{port}"
                    except ConnectionRefusedError:
                        error_message = f"Connection refused to {host}:{port}"
                    except socket.gaierror as e:
                        error_message = f"DNS resolution failed for {host}: {str(e)}"
                    except Exception as e:
                        error_message = f"Connection failed to {host}:{port}: {str(e)}"
                    
                    end_time = time.time()
                    response_time = int((end_time - start_time) * 1000)
                    
                    # Build connection type string
                    connection_type = service_row['service_type']
                    if service_row['credential_type']:
                        connection_type += f" ({service_row['credential_type']})"
                    
                    # Build test result
                    if success:
                        test_result = {
                            "status": "success",
                            "message": f"Successfully connected to {service_row['service_type']} service",
                            "response_time_ms": response_time
                        }
                        connection_status = "connected"
                    else:
                        test_result = {
                            "status": "failed",
                            "message": error_message or f"Failed to connect to {service_row['service_type']} service",
                            "response_time_ms": response_time
                        }
                        connection_status = "failed"
                    
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

        @self.app.put("/targets/{target_id}/services/{service_id}/credentials")
        async def update_service_credentials(target_id: int, service_id: int, credentials: dict):
            """Update service credentials"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if service exists
                    service_exists = await conn.fetchval("""
                        SELECT id FROM assets.target_services 
                        WHERE id = $1 AND target_id = $2
                    """, service_id, target_id)
                    
                    if not service_exists:
                        raise HTTPException(status_code=404, detail="Service not found")
                    
                    # Prepare credential updates
                    updates = []
                    values = []
                    param_count = 1
                    
                    if 'credential_type' in credentials:
                        updates.append(f"credential_type = ${param_count}")
                        values.append(credentials['credential_type'])
                        param_count += 1
                    
                    if 'username' in credentials:
                        updates.append(f"username = ${param_count}")
                        values.append(credentials['username'])
                        param_count += 1
                    
                    if 'password' in credentials and credentials['password']:
                        encrypted_password = self._encrypt_credential(credentials['password'])
                        updates.append(f"password_encrypted = ${param_count}")
                        values.append(encrypted_password)
                        param_count += 1
                    
                    if 'domain' in credentials:
                        updates.append(f"domain = ${param_count}")
                        values.append(credentials['domain'])
                        param_count += 1
                    
                    if not updates:
                        return {"success": True, "message": "No credentials to update"}
                    
                    # Add service_id and target_id as the last parameters
                    values.extend([service_id, target_id])
                    
                    # Build and execute update query
                    query = f"""
                        UPDATE assets.target_services 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count} AND target_id = ${param_count + 1}
                    """
                    
                    await conn.execute(query, *values)
                    
                    return {
                        "success": True,
                        "message": "Service credentials updated successfully"
                    }
                    
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update service credentials", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update service credentials"
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
        async def create_target_group(group_data: dict):
            """Create a new target group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Calculate path and level
                    if group_data.get('parent_group_id'):
                        parent = await conn.fetchrow(
                            "SELECT path, level FROM assets.target_groups WHERE id = $1",
                            group_data['parent_group_id']
                        )
                        if not parent:
                            raise HTTPException(status_code=400, detail="Parent group not found")
                        
                        path = f"{parent['path']}.{group_data['name']}"
                        level = parent['level'] + 1
                    else:
                        path = group_data['name']
                        level = 0
                    
                    # Insert group
                    group_id = await conn.fetchval("""
                        INSERT INTO assets.target_groups (name, description, parent_group_id, path, level, color, icon)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                    """, group_data['name'], group_data.get('description'), group_data.get('parent_group_id'),
                         path, level, group_data.get('color'), group_data.get('icon'))
                    
                    return {"success": True, "message": "Target group created", "group_id": group_id}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to create target group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create target group"
                )

        @self.app.get("/target-groups/{group_id}")
        async def get_target_group(group_id: int):
            """Get target group by ID"""
            try:
                async with self.db.pool.acquire() as conn:
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
                    
                    return {"success": True, "data": group_dict}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get target group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get target group"
                )

        @self.app.get("/target-groups/{group_id}/targets")
        async def get_target_group_targets(group_id: int):
            """Get all targets in a specific target group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Verify group exists
                    group = await conn.fetchrow("SELECT id FROM assets.target_groups WHERE id = $1", group_id)
                    if not group:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    # Get targets in this group
                    targets = await conn.fetch("""
                        SELECT t.id, t.name, t.hostname, t.ip_address, t.os_type, t.os_version, 
                               t.description, t.tags, t.created_at, t.updated_at
                        FROM assets.enhanced_targets t
                        JOIN assets.target_group_memberships tgm ON t.id = tgm.target_id
                        WHERE tgm.group_id = $1
                        ORDER BY t.name
                    """, group_id)
                    
                    targets_list = []
                    for target in targets:
                        targets_list.append({
                            "id": target['id'],
                            "name": target['name'],
                            "hostname": target['hostname'],
                            "ip_address": target['ip_address'],
                            "os_type": target['os_type'],
                            "os_version": target['os_version'],
                            "description": target['description'],
                            "tags": target['tags'],
                            "created_at": target['created_at'].isoformat(),
                            "updated_at": target['updated_at'].isoformat() if target['updated_at'] else None
                        })
                    
                    return {"success": True, "targets": targets_list, "total": len(targets_list)}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get target group targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get target group targets"
                )

        @self.app.get("/target-groups-tree")
        async def get_target_groups_tree():
            """Get target groups as a hierarchical tree structure"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get all groups with counts
                    groups = await conn.fetch("""
                        SELECT id, name, description, parent_group_id, path, level, 
                               color, icon, created_at, updated_at
                        FROM assets.target_groups
                        ORDER BY path
                    """)
                    
                    # Build tree structure
                    group_dict = {}
                    root_groups = []
                    
                    # First pass: create all group objects
                    for group in groups:
                        # Get target count for this group (including descendants)
                        target_count = await conn.fetchval("""
                            SELECT COUNT(DISTINCT tgm.target_id)
                            FROM assets.target_group_memberships tgm
                            JOIN assets.target_groups tg ON tgm.group_id = tg.id
                            WHERE tg.path LIKE $1
                        """, group['path'] + '%')
                        
                        # Get direct target count (only this group)
                        direct_count = await conn.fetchval("""
                            SELECT COUNT(*)
                            FROM assets.target_group_memberships
                            WHERE group_id = $1
                        """, group['id'])
                        
                        group_obj = {
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
                            "updated_at": group['updated_at'].isoformat() if group['updated_at'] else None,
                            "children": []
                        }
                        
                        group_dict[group['id']] = group_obj
                        
                        if group['parent_group_id'] is None:
                            root_groups.append(group_obj)
                    
                    # Second pass: build parent-child relationships
                    for group in groups:
                        if group['parent_group_id'] is not None:
                            parent = group_dict.get(group['parent_group_id'])
                            if parent:
                                parent['children'].append(group_dict[group['id']])
                    
                    return {"tree": root_groups}
            except Exception as e:
                self.logger.error("Failed to get target groups tree", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get target groups tree"
                )

        @self.app.put("/target-groups/{group_id}")
        async def update_target_group(group_id: int, group_data: dict):
            """Update target group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if group exists
                    existing = await conn.fetchval("SELECT id FROM assets.target_groups WHERE id = $1", group_id)
                    if not existing:
                        raise HTTPException(status_code=404, detail="Target group not found")
                    
                    # Build update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if 'name' in group_data:
                        updates.append(f"name = ${param_count}")
                        values.append(group_data['name'])
                        param_count += 1
                    
                    if 'description' in group_data:
                        updates.append(f"description = ${param_count}")
                        values.append(group_data['description'])
                        param_count += 1
                    
                    if 'color' in group_data:
                        updates.append(f"color = ${param_count}")
                        values.append(group_data['color'])
                        param_count += 1
                    
                    if 'icon' in group_data:
                        updates.append(f"icon = ${param_count}")
                        values.append(group_data['icon'])
                        param_count += 1
                    
                    if not updates:
                        return {"success": True, "message": "No changes to update"}
                    
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

        @self.app.delete("/target-groups/{group_id}")
        async def delete_target_group(group_id: int):
            """Delete target group"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Check if group exists
                        existing = await conn.fetchval("SELECT id FROM assets.target_groups WHERE id = $1", group_id)
                        if not existing:
                            raise HTTPException(status_code=404, detail="Target group not found")
                        
                        # Delete group memberships first
                        await conn.execute("DELETE FROM assets.target_group_memberships WHERE group_id = $1", group_id)
                        
                        # Delete the group
                        result = await conn.execute("DELETE FROM assets.target_groups WHERE id = $1", group_id)
                        
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

        @self.app.delete("/target-groups/{group_id}/targets/{target_id}")
        async def remove_target_from_group(group_id: int, target_id: int):
            """Remove target from group"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if membership exists
                    existing = await conn.fetchval("""
                        SELECT EXISTS(SELECT 1 FROM assets.target_group_memberships 
                                     WHERE group_id = $1 AND target_id = $2)
                    """, group_id, target_id)
                    
                    if not existing:
                        raise HTTPException(status_code=404, detail="Target not found in group")
                    
                    # Remove membership
                    await conn.execute("""
                        DELETE FROM assets.target_group_memberships 
                        WHERE group_id = $1 AND target_id = $2
                    """, group_id, target_id)
                    
                    return {"success": True, "message": "Target removed from group"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to remove target from group", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to remove target from group"
                )

        @self.app.post("/target-groups/{group_id}/targets")
        async def add_targets_to_group(group_id: int, request_data: dict):
            """Add targets to a group"""
            try:
                target_ids = request_data.get('target_ids', [])
                if not target_ids:
                    raise HTTPException(status_code=400, detail="No target IDs provided")
                
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

        @self.app.get("/target-groups/{group_id}/targets")
        async def get_group_targets(
            group_id: int,
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            include_descendants: bool = Query(False, description="Include targets from descendant groups")
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
                                   is_enabled, notes, credential_type, created_at,
                                   connection_status, last_tested_at
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
                                has_credentials=service_row['credential_type'] is not None,
                                connection_status=service_row['connection_status'],
                                last_tested_at=service_row['last_tested_at'].isoformat() if service_row['last_tested_at'] else None
                            ))
                        
                        # Parse tags
                        tags = target_row['tags']
                        if isinstance(tags, str):
                            tags = json.loads(tags)
                        elif tags is None:
                            tags = []
                        
                        target_list.append(EnhancedTargetSummary(
                            id=target_row['id'],
                            name=target_row['name'],
                            hostname=target_row['host'],
                            ip_address=await self._resolve_ip_address(target_row['host']),
                            os_type=target_row['target_type'],
                            os_version="Unknown",  # Not available in current schema
                            description=target_row['description'],
                            tags=tags,
                            services=services,
                            created_at=target_row['created_at'].isoformat(),
                            updated_at=target_row['updated_at'].isoformat() if target_row['updated_at'] else None
                        ))
                    
                    return {
                        "targets": target_list,
                        "total": total,
                        "skip": skip,
                        "limit": limit,
                        "group_id": group_id,
                        "include_descendants": include_descendants
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get group targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get group targets"
                )

if __name__ == "__main__":
    service = AssetService()
    service.run()
#!/usr/bin/env python3
"""
OpsConductor Asset Service - Simplified (No Target Groups)
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
    connection_status: Optional[str] = None
    last_tested_at: Optional[str] = None

class EnhancedTargetCreate(BaseModel):
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: str = "other"  # 'windows', 'linux', 'unix', 'macos', 'other'
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    services: List[TargetServiceCreate] = []

class EnhancedTargetSummary(BaseModel):
    id: int
    name: str
    hostname: str
    ip_address: Optional[str]
    os_type: str
    os_version: Optional[str]
    description: Optional[str]
    tags: List[str]
    services: List[TargetServiceSummary]
    created_at: str
    updated_at: Optional[str]

class AssetService(BaseService):
    def __init__(self):
        super().__init__("asset-service", port=3002)
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.setup_routes()

    def _get_encryption_key(self):
        """Get or generate encryption key for credentials"""
        key_file = "/app/data/encryption.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def _encrypt_field(self, value: str) -> str:
        """Encrypt a field value"""
        if not value:
            return None
        return self.fernet.encrypt(value.encode()).decode()

    def _decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a field value"""
        if not encrypted_value:
            return None
        return self.fernet.decrypt(encrypted_value.encode()).decode()

    async def _resolve_ip_address(self, hostname: str) -> Optional[str]:
        """Resolve hostname to IP address"""
        import socket
        try:
            return socket.gethostbyname(hostname)
        except:
            return None

    def setup_routes(self):
        # ============================================================================
        # METADATA ENDPOINTS
        # ============================================================================
        
        @self.app.get("/metadata")
        async def get_metadata():
            """Get metadata for dropdowns and form options"""
            return {
                "success": True,
                "data": {
                    "credential_types": [
                        {"value": "username_password", "label": "Username/Password"},
                        {"value": "ssh_key", "label": "SSH Key"},
                        {"value": "api_key", "label": "API Key"},
                        {"value": "bearer_token", "label": "Bearer Token"}
                    ],
                    "service_types": [
                        {"value": "ssh", "label": "SSH", "default_port": 22},
                        {"value": "winrm_http", "label": "WinRM HTTP", "default_port": 5985},
                        {"value": "winrm_https", "label": "WinRM HTTPS", "default_port": 5986},
                        {"value": "rdp", "label": "RDP", "default_port": 3389},
                        {"value": "vnc", "label": "VNC", "default_port": 5900},
                        {"value": "http", "label": "HTTP", "default_port": 80},
                        {"value": "https", "label": "HTTPS", "default_port": 443},
                        {"value": "ftp", "label": "FTP", "default_port": 21},
                        {"value": "sftp", "label": "SFTP", "default_port": 22},
                        {"value": "telnet", "label": "Telnet", "default_port": 23},
                        {"value": "smtp", "label": "SMTP", "default_port": 25},
                        {"value": "dns", "label": "DNS", "default_port": 53},
                        {"value": "snmp", "label": "SNMP", "default_port": 161},
                        {"value": "ldap", "label": "LDAP", "default_port": 389},
                        {"value": "ldaps", "label": "LDAPS", "default_port": 636}
                    ],
                    "os_types": [
                        {"value": "windows", "label": "Windows"},
                        {"value": "linux", "label": "Linux"},
                        {"value": "unix", "label": "Unix"},
                        {"value": "macos", "label": "macOS"},
                        {"value": "other", "label": "Other"}
                    ]
                }
            }
        
        # ============================================================================
        # ENHANCED TARGETS ENDPOINTS
        # ============================================================================
        
        @self.app.get("/targets")
        async def list_enhanced_targets(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all enhanced targets"""
            try:
                async with self.db.pool.acquire() as conn:
                    targets = await conn.fetch("""
                        SELECT id, name, hostname, ip_address, os_type, os_version, 
                               description, tags, created_at, updated_at
                        FROM assets.enhanced_targets
                        ORDER BY created_at DESC
                        OFFSET $1 LIMIT $2
                    """, skip, limit)
                    
                    total = await conn.fetchval("SELECT COUNT(*) FROM assets.enhanced_targets")
                    
                    target_list = []
                    for target in targets:
                        # Get services for this target
                        services = await conn.fetch("""
                            SELECT id, service_type, port, is_default, is_secure, is_enabled,
                                   credential_type, username, password_encrypted, private_key_encrypted, 
                                   public_key, api_key_encrypted, bearer_token_encrypted, 
                                   certificate_encrypted, passphrase_encrypted, domain,
                                   connection_status, last_tested_at
                            FROM assets.target_services
                            WHERE target_id = $1
                            ORDER BY is_default DESC, port ASC
                        """, target['id'])
                        
                        service_list = []
                        for service in services:
                            has_credentials = any([
                                service['password_encrypted'],
                                service['private_key_encrypted'],
                                service['api_key_encrypted'],
                                service['bearer_token_encrypted'],
                                service['certificate_encrypted']
                            ])
                            
                            service_list.append(TargetServiceSummary(
                                id=service['id'],
                                service_type=service['service_type'],
                                port=service['port'],
                                is_default=service['is_default'],
                                is_secure=service['is_secure'],
                                is_enabled=service['is_enabled'],
                                credential_type=service['credential_type'],
                                has_credentials=has_credentials,
                                connection_status=service['connection_status'],
                                last_tested_at=service['last_tested_at'].isoformat() if service['last_tested_at'] else None
                            ))
                        
                        # Parse tags
                        tags = target['tags']
                        if isinstance(tags, str):
                            tags = json.loads(tags)
                        elif tags is None:
                            tags = []
                        
                        target_list.append(EnhancedTargetSummary(
                            id=target['id'],
                            name=target['name'],
                            hostname=target['hostname'],
                            ip_address=target['ip_address'],
                            os_type=target['os_type'],
                            os_version=target['os_version'],
                            description=target['description'],
                            tags=tags,
                            services=service_list,
                            created_at=target['created_at'].isoformat(),
                            updated_at=target['updated_at'].isoformat() if target['updated_at'] else None
                        ))
                    
                    return {
                        "targets": target_list,
                        "total": total,
                        "skip": skip,
                        "limit": limit
                    }
            except Exception as e:
                self.logger.error("Failed to list enhanced targets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to list enhanced targets"
                )

        @self.app.post("/targets")
        async def create_enhanced_target(target_data: EnhancedTargetCreate):
            """Create a new enhanced target"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Create target
                        target_id = await conn.fetchval("""
                            INSERT INTO assets.enhanced_targets 
                            (name, hostname, ip_address, os_type, os_version, description, tags)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id
                        """, 
                        target_data.name,
                        target_data.hostname,
                        target_data.ip_address,
                        target_data.os_type,
                        target_data.os_version,
                        target_data.description,
                        json.dumps(target_data.tags)
                        )
                        
                        # Create services
                        for service in target_data.services:
                            await self._create_target_service(conn, target_id, service)
                        
                        return {"success": True, "target_id": target_id}
            except Exception as e:
                self.logger.error("Failed to create enhanced target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create enhanced target"
                )

        @self.app.get("/targets/{target_id}")
        async def get_enhanced_target(target_id: int):
            """Get enhanced target by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    target = await conn.fetchrow("""
                        SELECT id, name, hostname, ip_address, os_type, os_version, 
                               description, tags, created_at, updated_at
                        FROM assets.enhanced_targets WHERE id = $1
                    """, target_id)
                    
                    if not target:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    # Get services
                    services = await conn.fetch("""
                        SELECT id, service_type, port, is_default, is_secure, is_enabled,
                               credential_type, username, password_encrypted, private_key_encrypted, 
                               public_key, api_key_encrypted, bearer_token_encrypted, 
                               certificate_encrypted, passphrase_encrypted, domain, notes,
                               connection_status, last_tested_at
                        FROM assets.target_services
                        WHERE target_id = $1
                        ORDER BY is_default DESC, port ASC
                    """, target_id)
                    
                    service_list = []
                    for service in services:
                        has_credentials = any([
                            service['password_encrypted'],
                            service['private_key_encrypted'],
                            service['api_key_encrypted'],
                            service['bearer_token_encrypted'],
                            service['certificate_encrypted']
                        ])
                        
                        service_list.append({
                            "id": service['id'],
                            "service_type": service['service_type'],
                            "port": service['port'],
                            "is_default": service['is_default'],
                            "is_secure": service['is_secure'],
                            "is_enabled": service['is_enabled'],
                            "credential_type": service['credential_type'],
                            "has_credentials": has_credentials,
                            "notes": service['notes'],
                            "connection_status": service['connection_status'],
                            "last_tested_at": service['last_tested_at'].isoformat() if service['last_tested_at'] else None
                        })
                    
                    # Parse tags
                    tags = target['tags']
                    if isinstance(tags, str):
                        tags = json.loads(tags)
                    elif tags is None:
                        tags = []
                    
                    return {
                        "success": True,
                        "data": {
                            "id": target['id'],
                            "name": target['name'],
                            "hostname": target['hostname'],
                            "ip_address": target['ip_address'],
                            "os_type": target['os_type'],
                            "os_version": target['os_version'],
                            "description": target['description'],
                            "tags": tags,
                            "services": service_list,
                            "created_at": target['created_at'].isoformat(),
                            "updated_at": target['updated_at'].isoformat() if target['updated_at'] else None
                        }
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get enhanced target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get enhanced target"
                )

        @self.app.delete("/targets/{target_id}")
        async def delete_enhanced_target(target_id: int):
            """Delete enhanced target"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Check if target exists
                        target = await conn.fetchrow("SELECT id FROM assets.enhanced_targets WHERE id = $1", target_id)
                        if not target:
                            raise HTTPException(status_code=404, detail="Target not found")
                        
                        # Delete services (cascade will handle this, but explicit is better)
                        await conn.execute("DELETE FROM assets.target_services WHERE target_id = $1", target_id)
                        
                        # Delete target
                        await conn.execute("DELETE FROM assets.enhanced_targets WHERE id = $1", target_id)
                        
                        return {"success": True, "message": "Target deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete enhanced target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete enhanced target"
                )

        @self.app.get("/targets/{target_id}/credentials")
        async def get_target_credentials(target_id: int):
            """Get target service credentials for editing (decrypted)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Check if target exists
                    target = await conn.fetchrow("SELECT id FROM assets.enhanced_targets WHERE id = $1", target_id)
                    if not target:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    # Get services with credentials
                    services = await conn.fetch("""
                        SELECT id, service_type, port, is_default, is_secure, is_enabled,
                               credential_type, username, password_encrypted, private_key_encrypted, 
                               public_key, api_key_encrypted, bearer_token_encrypted, 
                               certificate_encrypted, passphrase_encrypted, domain, notes
                        FROM assets.target_services
                        WHERE target_id = $1
                        ORDER BY is_default DESC, port ASC
                    """, target_id)
                    
                    service_list = []
                    for service in services:
                        # Decrypt credentials if they exist
                        decrypted_service = {
                            "id": service['id'],
                            "service_type": service['service_type'],
                            "port": service['port'],
                            "is_default": service['is_default'],
                            "is_secure": service['is_secure'],
                            "is_enabled": service['is_enabled'],
                            "credential_type": service['credential_type'],
                            "username": service['username'],
                            "domain": service['domain'],
                            "notes": service['notes']
                        }
                        
                        # Decrypt encrypted fields
                        try:
                            if service['password_encrypted']:
                                decrypted_service['password'] = self._decrypt_field(service['password_encrypted'])
                        except Exception as e:
                            self.logger.warning(f"Failed to decrypt password for service {service['id']}: {str(e)}")
                            decrypted_service['password'] = ''
                        
                        try:
                            if service['private_key_encrypted']:
                                decrypted_service['private_key'] = self._decrypt_field(service['private_key_encrypted'])
                        except Exception as e:
                            self.logger.warning(f"Failed to decrypt private_key for service {service['id']}: {str(e)}")
                            decrypted_service['private_key'] = ''
                        
                        try:
                            if service['api_key_encrypted']:
                                decrypted_service['api_key'] = self._decrypt_field(service['api_key_encrypted'])
                        except Exception as e:
                            self.logger.warning(f"Failed to decrypt api_key for service {service['id']}: {str(e)}")
                            decrypted_service['api_key'] = ''
                        
                        try:
                            if service['bearer_token_encrypted']:
                                decrypted_service['bearer_token'] = self._decrypt_field(service['bearer_token_encrypted'])
                        except Exception as e:
                            self.logger.warning(f"Failed to decrypt bearer_token for service {service['id']}: {str(e)}")
                            decrypted_service['bearer_token'] = ''
                        
                        try:
                            if service['certificate_encrypted']:
                                decrypted_service['certificate'] = self._decrypt_field(service['certificate_encrypted'])
                        except Exception as e:
                            self.logger.warning(f"Failed to decrypt certificate for service {service['id']}: {str(e)}")
                            decrypted_service['certificate'] = ''
                        
                        try:
                            if service['passphrase_encrypted']:
                                decrypted_service['passphrase'] = self._decrypt_field(service['passphrase_encrypted'])
                        except Exception as e:
                            self.logger.warning(f"Failed to decrypt passphrase for service {service['id']}: {str(e)}")
                            decrypted_service['passphrase'] = ''
                        
                        # Add public key (not encrypted)
                        if service['public_key']:
                            decrypted_service['public_key'] = service['public_key']
                        
                        service_list.append(decrypted_service)
                    
                    return {
                        "success": True,
                        "services": service_list
                    }
            except HTTPException:
                raise
            except Exception as e:
                import traceback
                error_details = f"{str(e)} - {traceback.format_exc()}"
                self.logger.error("Failed to get target credentials", error=error_details)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get target credentials: {str(e)}"
                )

        @self.app.put("/targets/{target_id}")
        async def update_enhanced_target(target_id: int, target_data: EnhancedTargetCreate):
            """Update enhanced target"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Check if target exists
                        existing_target = await conn.fetchrow("SELECT id FROM assets.enhanced_targets WHERE id = $1", target_id)
                        if not existing_target:
                            raise HTTPException(status_code=404, detail="Target not found")
                        
                        # Resolve IP if not provided
                        ip_address = target_data.ip_address
                        if not ip_address and target_data.hostname:
                            ip_address = await self._resolve_ip_address(target_data.hostname)
                        
                        # Update target
                        await conn.execute("""
                            UPDATE assets.enhanced_targets 
                            SET name = $2, hostname = $3, ip_address = $4, os_type = $5, 
                                os_version = $6, description = $7, tags = $8, updated_at = NOW()
                            WHERE id = $1
                        """, 
                        target_id, target_data.name, target_data.hostname, ip_address, 
                        target_data.os_type, target_data.os_version, target_data.description, 
                        json.dumps(target_data.tags or [])
                        )
                        
                        # Get existing services to preserve credentials
                        existing_services = await conn.fetch("""
                            SELECT id, service_type, port, is_default, is_secure, is_enabled,
                                   credential_type, username, password_encrypted, private_key_encrypted, 
                                   public_key, api_key_encrypted, bearer_token_encrypted, 
                                   certificate_encrypted, passphrase_encrypted, domain, notes,
                                   connection_status, last_tested_at
                            FROM assets.target_services
                            WHERE target_id = $1
                        """, target_id)
                        
                        # Create a map of existing services by service_type and port
                        existing_map = {}
                        for existing in existing_services:
                            key = (existing['service_type'], existing['port'])
                            existing_map[key] = existing
                        
                        # Delete existing services
                        await conn.execute("DELETE FROM assets.target_services WHERE target_id = $1", target_id)
                        
                        # Create new services, preserving credentials from existing ones
                        for service in target_data.services:
                            key = (service.service_type, service.port)
                            existing = existing_map.get(key)
                            
                            # If service exists and no credentials provided in update, preserve existing credentials
                            if existing and not any([service.credential_type, service.username, service.password, 
                                                   service.private_key, service.api_key, service.bearer_token, 
                                                   service.certificate, service.passphrase]):
                                # Create service with preserved credentials
                                preserved_service = TargetServiceCreate(
                                    service_type=service.service_type,
                                    port=service.port,
                                    is_default=service.is_default,
                                    is_secure=service.is_secure,
                                    is_enabled=service.is_enabled,
                                    notes=service.notes,
                                    credential_type=existing['credential_type'],
                                    username=existing['username'],
                                    password=self._decrypt_field(existing['password_encrypted']) if existing['password_encrypted'] else None,
                                    private_key=self._decrypt_field(existing['private_key_encrypted']) if existing['private_key_encrypted'] else None,
                                    public_key=existing['public_key'],
                                    api_key=self._decrypt_field(existing['api_key_encrypted']) if existing['api_key_encrypted'] else None,
                                    bearer_token=self._decrypt_field(existing['bearer_token_encrypted']) if existing['bearer_token_encrypted'] else None,
                                    certificate=self._decrypt_field(existing['certificate_encrypted']) if existing['certificate_encrypted'] else None,
                                    passphrase=self._decrypt_field(existing['passphrase_encrypted']) if existing['passphrase_encrypted'] else None,
                                    domain=existing['domain']
                                )
                                await self._create_target_service(conn, target_id, preserved_service, 
                                                                 existing['connection_status'], existing['last_tested_at'])
                            else:
                                # Create service with new/updated credentials
                                await self._create_target_service(conn, target_id, service)
                        
                        # Get updated target with services
                        target = await conn.fetchrow("""
                            SELECT id, name, hostname, ip_address, os_type, os_version, 
                                   description, tags, created_at, updated_at
                            FROM assets.enhanced_targets
                            WHERE id = $1
                        """, target_id)
                        
                        services = await conn.fetch("""
                            SELECT id, service_type, port, is_default, is_secure, is_enabled, 
                                   credential_type, username, password_encrypted, private_key_encrypted, 
                                   public_key, api_key_encrypted, bearer_token_encrypted, 
                                   certificate_encrypted, passphrase_encrypted, domain,
                                   connection_status, last_tested_at
                            FROM assets.target_services
                            WHERE target_id = $1
                            ORDER BY is_default DESC, service_type
                        """, target_id)
                        
                        # Build services summary
                        services_summary = []
                        for service in services:
                            has_credentials = any([
                                service['password_encrypted'],
                                service['private_key_encrypted'],
                                service['api_key_encrypted'],
                                service['bearer_token_encrypted'],
                                service['certificate_encrypted']
                            ])
                            
                            services_summary.append(TargetServiceSummary(
                                id=service['id'],
                                service_type=service['service_type'],
                                port=service['port'],
                                is_default=service['is_default'],
                                is_secure=service['is_secure'],
                                is_enabled=service['is_enabled'],
                                credential_type=service['credential_type'],
                                has_credentials=has_credentials,
                                connection_status=service['connection_status'],
                                last_tested_at=service['last_tested_at'].isoformat() if service['last_tested_at'] else None
                            ))
                        
                        return EnhancedTargetSummary(
                            id=target['id'],
                            name=target['name'],
                            hostname=target['hostname'],
                            ip_address=target['ip_address'],
                            os_type=target['os_type'],
                            os_version=target['os_version'],
                            description=target['description'],
                            tags=json.loads(target['tags']) if target['tags'] else [],
                            services=services_summary,
                            created_at=target['created_at'].isoformat(),
                            updated_at=target['updated_at'].isoformat() if target['updated_at'] else None
                        )
                        
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update enhanced target", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update enhanced target"
                )

        @self.app.post("/targets/{target_id}/services/{service_id}/test")
        async def test_service_connection(target_id: int, service_id: int):
            """Test connection to a specific service"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get service details with target info
                    service_row = await conn.fetchrow("""
                        SELECT ts.*, t.hostname, t.ip_address, t.name as target_name
                        FROM assets.target_services ts
                        JOIN assets.enhanced_targets t ON ts.target_id = t.id
                        WHERE ts.id = $1 AND ts.target_id = $2
                    """, service_id, target_id)
                    
                    if not service_row:
                        raise HTTPException(status_code=404, detail="Service not found")
                    
                    if not service_row['is_enabled']:
                        raise HTTPException(status_code=400, detail="Service is disabled")
                    
                    # Determine connection host (prefer IP, fallback to hostname)
                    host = service_row['ip_address'] or service_row['hostname']
                    if not host:
                        raise HTTPException(status_code=400, detail="No host configured")
                    
                    # Call automation service for connection test
                    import aiohttp
                    import time
                    
                    start_time = time.time()
                    
                    connection_data = {
                        "host": host,
                        "port": service_row['port'],
                        "service_type": service_row['service_type'],
                        "credential_type": service_row['credential_type'],
                        "username": service_row['username'],
                        "service_id": service_id,
                        "target_id": target_id
                    }
                    
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                "http://automation-service:3003/automation/test-connection",
                                json=connection_data,
                                timeout=aiohttp.ClientTimeout(total=30)
                            ) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    success = result.get('success', False)
                                    error_message = result.get('error', '')
                                else:
                                    success = False
                                    error_message = f"Automation service returned status {response.status}"
                    except Exception as e:
                        success = False
                        error_message = f"Failed to call automation service: {str(e)}"
                    
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
                    
                    # Update connection status in database
                    await conn.execute("""
                        UPDATE assets.target_services 
                        SET connection_status = $1, last_tested_at = NOW()
                        WHERE id = $2 AND target_id = $3
                    """, connection_status, service_id, target_id)
                    
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

    async def _create_target_service(self, conn, target_id: int, service: TargetServiceCreate, 
                                   connection_status: str = 'unknown', last_tested_at = None):
        """Create a target service with encrypted credentials"""
        # Encrypt sensitive fields
        password_encrypted = self._encrypt_field(service.password) if service.password else None
        private_key_encrypted = self._encrypt_field(service.private_key) if service.private_key else None
        api_key_encrypted = self._encrypt_field(service.api_key) if service.api_key else None
        bearer_token_encrypted = self._encrypt_field(service.bearer_token) if service.bearer_token else None
        certificate_encrypted = self._encrypt_field(service.certificate) if service.certificate else None
        passphrase_encrypted = self._encrypt_field(service.passphrase) if service.passphrase else None
        
        await conn.execute("""
            INSERT INTO assets.target_services 
            (target_id, service_type, port, is_default, is_secure, is_enabled, notes,
             credential_type, username, password_encrypted, private_key_encrypted, 
             public_key, api_key_encrypted, bearer_token_encrypted, certificate_encrypted, 
             passphrase_encrypted, domain, connection_status, last_tested_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
        """, 
        target_id, service.service_type, service.port, service.is_default, 
        service.is_secure, service.is_enabled, service.notes, service.credential_type,
        service.username, password_encrypted, private_key_encrypted, service.public_key,
        api_key_encrypted, bearer_token_encrypted, certificate_encrypted, 
        passphrase_encrypted, service.domain, connection_status, last_tested_at
        )

if __name__ == "__main__":
    service = AssetService()
    service.run()
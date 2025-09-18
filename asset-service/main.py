#!/usr/bin/env python3
"""
OpsConductor Asset Service - Consolidated
Single table approach for all asset/target information
"""

import sys
import os
import json
import base64
from cryptography.fernet import Fernet
from typing import List, Optional, Dict, Any
from fastapi import Query, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService

# ============================================================================
# MODELS
# ============================================================================

class AdditionalService(BaseModel):
    """Model for additional services in JSON array"""
    service_type: str
    port: int
    is_secure: bool = False
    credential_type: Optional[str] = None
    username: Optional[str] = None
    password_encrypted: Optional[str] = None
    private_key_encrypted: Optional[str] = None
    public_key: Optional[str] = None
    api_key_encrypted: Optional[str] = None
    bearer_token_encrypted: Optional[str] = None
    certificate_encrypted: Optional[str] = None
    passphrase_encrypted: Optional[str] = None
    domain: Optional[str] = None
    notes: Optional[str] = None

class AssetCreate(BaseModel):
    """Model for creating a new asset"""
    name: str
    hostname: str
    ip_address: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    
    # Device/Hardware Information
    device_type: str = "other"
    hardware_make: Optional[str] = None
    hardware_model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Operating System Information
    os_type: str = "other"
    os_version: Optional[str] = None
    
    # Location Information
    physical_address: Optional[str] = None
    data_center: Optional[str] = None
    building: Optional[str] = None
    room: Optional[str] = None
    rack_position: Optional[str] = None
    rack_location: Optional[str] = None
    gps_coordinates: Optional[str] = None
    
    # Status and Management
    status: str = "active"
    environment: str = "production"
    criticality: str = "medium"
    owner: Optional[str] = None
    support_contact: Optional[str] = None
    contract_number: Optional[str] = None
    
    # Primary service
    service_type: str
    port: int
    is_secure: bool = False
    
    # Primary service credentials
    credential_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Will be encrypted
    private_key: Optional[str] = None  # Will be encrypted
    public_key: Optional[str] = None
    api_key: Optional[str] = None  # Will be encrypted
    bearer_token: Optional[str] = None  # Will be encrypted
    certificate: Optional[str] = None  # Will be encrypted
    passphrase: Optional[str] = None  # Will be encrypted
    domain: Optional[str] = None
    
    # Database-specific fields
    database_type: Optional[str] = None
    database_name: Optional[str] = None
    
    # Secondary service
    secondary_service_type: str = "none"
    secondary_port: Optional[int] = None
    ftp_type: Optional[str] = None
    secondary_username: Optional[str] = None
    secondary_password: Optional[str] = None  # Will be encrypted
    
    # Additional services
    additional_services: List[Dict[str, Any]] = []
    notes: Optional[str] = None

class AssetUpdate(BaseModel):
    """Model for updating an asset"""
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Device/Hardware Information
    device_type: Optional[str] = None
    hardware_make: Optional[str] = None
    hardware_model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Operating System Information
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    
    # Location Information
    physical_address: Optional[str] = None
    data_center: Optional[str] = None
    building: Optional[str] = None
    room: Optional[str] = None
    rack_position: Optional[str] = None
    rack_location: Optional[str] = None
    gps_coordinates: Optional[str] = None
    
    # Status and Management
    status: Optional[str] = None
    environment: Optional[str] = None
    criticality: Optional[str] = None
    owner: Optional[str] = None
    support_contact: Optional[str] = None
    contract_number: Optional[str] = None
    
    # Primary service
    service_type: Optional[str] = None
    port: Optional[int] = None
    is_secure: Optional[bool] = None
    
    # Primary service credentials
    credential_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Will be encrypted
    private_key: Optional[str] = None  # Will be encrypted
    public_key: Optional[str] = None
    api_key: Optional[str] = None  # Will be encrypted
    bearer_token: Optional[str] = None  # Will be encrypted
    certificate: Optional[str] = None  # Will be encrypted
    passphrase: Optional[str] = None  # Will be encrypted
    domain: Optional[str] = None
    
    # Database-specific fields
    database_type: Optional[str] = None
    database_name: Optional[str] = None
    
    # Secondary service
    secondary_service_type: Optional[str] = None
    secondary_port: Optional[int] = None
    ftp_type: Optional[str] = None
    secondary_username: Optional[str] = None
    secondary_password: Optional[str] = None  # Will be encrypted
    
    # Additional services
    additional_services: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None

class AssetSummary(BaseModel):
    """Model for asset list view"""
    id: int
    name: str
    hostname: str
    ip_address: Optional[str]
    os_type: str
    os_version: Optional[str]
    description: Optional[str]
    tags: List[str]
    
    # Primary service info
    service_type: str
    port: int
    is_secure: bool
    has_credentials: bool
    
    # Additional services count
    additional_services_count: int
    
    # Status
    is_active: bool
    connection_status: Optional[str]
    last_tested_at: Optional[str]
    
    created_at: str
    updated_at: Optional[str]

class AssetDetail(BaseModel):
    """Model for detailed asset view"""
    id: int
    name: str
    hostname: str
    ip_address: Optional[str]
    description: Optional[str]
    tags: List[str]
    os_type: str
    os_version: Optional[str]
    
    # Primary service
    service_type: str
    port: int
    is_secure: bool
    credential_type: Optional[str]
    username: Optional[str]
    # Note: encrypted fields are not returned in API responses
    domain: Optional[str]
    
    # Additional services (decrypted for display)
    additional_services: List[Dict[str, Any]]
    
    # Status and metadata
    is_active: bool
    connection_status: Optional[str]
    last_tested_at: Optional[str]
    notes: Optional[str]
    
    # Audit
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: str
    updated_at: Optional[str]

class ConsolidatedAssetService(BaseService):
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

    def _encrypt_field(self, value: str) -> Optional[str]:
        """Encrypt a field value"""
        if not value:
            return None
        return self.fernet.encrypt(value.encode()).decode()

    def _decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """Decrypt a field value"""
        if not encrypted_value:
            return None
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except:
            return None

    def _encrypt_additional_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Encrypt credential fields in additional services"""
        encrypted_services = []
        for service in services:
            encrypted_service = service.copy()
            
            # Encrypt credential fields
            if service.get('password'):
                encrypted_service['password_encrypted'] = self._encrypt_field(service['password'])
                del encrypted_service['password']
            
            if service.get('private_key'):
                encrypted_service['private_key_encrypted'] = self._encrypt_field(service['private_key'])
                del encrypted_service['private_key']
            
            if service.get('api_key'):
                encrypted_service['api_key_encrypted'] = self._encrypt_field(service['api_key'])
                del encrypted_service['api_key']
            
            if service.get('bearer_token'):
                encrypted_service['bearer_token_encrypted'] = self._encrypt_field(service['bearer_token'])
                del encrypted_service['bearer_token']
            
            if service.get('certificate'):
                encrypted_service['certificate_encrypted'] = self._encrypt_field(service['certificate'])
                del encrypted_service['certificate']
            
            if service.get('passphrase'):
                encrypted_service['passphrase_encrypted'] = self._encrypt_field(service['passphrase'])
                del encrypted_service['passphrase']
            
            encrypted_services.append(encrypted_service)
        
        return encrypted_services

    def _decrypt_additional_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Decrypt credential fields in additional services for display"""
        decrypted_services = []
        for service in services:
            decrypted_service = service.copy()
            
            # Decrypt and replace encrypted fields (for display only)
            if service.get('password_encrypted'):
                decrypted_service['password'] = self._decrypt_field(service['password_encrypted'])
                # Keep encrypted version for storage
            
            if service.get('private_key_encrypted'):
                decrypted_service['private_key'] = self._decrypt_field(service['private_key_encrypted'])
            
            if service.get('api_key_encrypted'):
                decrypted_service['api_key'] = self._decrypt_field(service['api_key_encrypted'])
            
            if service.get('bearer_token_encrypted'):
                decrypted_service['bearer_token'] = self._decrypt_field(service['bearer_token_encrypted'])
            
            if service.get('certificate_encrypted'):
                decrypted_service['certificate'] = self._decrypt_field(service['certificate_encrypted'])
            
            if service.get('passphrase_encrypted'):
                decrypted_service['passphrase'] = self._decrypt_field(service['passphrase_encrypted'])
            
            decrypted_services.append(decrypted_service)
        
        return decrypted_services

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
                        {"value": "bearer_token", "label": "Bearer Token"},
                        {"value": "certificate", "label": "Certificate"}
                    ],
                    "service_types": [
                        # Remote Access
                        {"value": "ssh", "label": "SSH", "default_port": 22, "category": "Remote Access"},
                        {"value": "rdp", "label": "RDP", "default_port": 3389, "category": "Remote Access"},
                        {"value": "vnc", "label": "VNC", "default_port": 5900, "category": "Remote Access"},
                        {"value": "telnet", "label": "Telnet", "default_port": 23, "category": "Remote Access"},
                        
                        # Windows Management
                        {"value": "winrm", "label": "WinRM HTTP", "default_port": 5985, "category": "Windows Management"},
                        {"value": "winrm_https", "label": "WinRM HTTPS", "default_port": 5986, "category": "Windows Management"},
                        {"value": "wmi", "label": "WMI", "default_port": 135, "category": "Windows Management"},
                        {"value": "smb", "label": "SMB/CIFS", "default_port": 445, "category": "Windows Management"},
                        
                        # Web Services
                        {"value": "http", "label": "HTTP", "default_port": 80, "category": "Web Services"},
                        {"value": "https", "label": "HTTPS", "default_port": 443, "category": "Web Services"},
                        {"value": "http_alt", "label": "HTTP (Alt)", "default_port": 8080, "category": "Web Services"},
                        {"value": "https_alt", "label": "HTTPS (Alt)", "default_port": 8443, "category": "Web Services"},
                        
                        # Database Services
                        {"value": "mysql", "label": "MySQL", "default_port": 3306, "category": "Database Services"},
                        {"value": "postgresql", "label": "PostgreSQL", "default_port": 5432, "category": "Database Services"},
                        {"value": "sql_server", "label": "SQL Server", "default_port": 1433, "category": "Database Services"},
                        {"value": "oracle", "label": "Oracle DB", "default_port": 1521, "category": "Database Services"},
                        {"value": "mongodb", "label": "MongoDB", "default_port": 27017, "category": "Database Services"},
                        {"value": "redis", "label": "Redis", "default_port": 6379, "category": "Database Services"},
                        
                        # Email Services
                        {"value": "smtp", "label": "SMTP", "default_port": 25, "category": "Email Services"},
                        {"value": "smtps", "label": "SMTPS", "default_port": 465, "category": "Email Services"},
                        {"value": "smtp_submission", "label": "SMTP Submission", "default_port": 587, "category": "Email Services"},
                        {"value": "imap", "label": "IMAP", "default_port": 143, "category": "Email Services"},
                        {"value": "imaps", "label": "IMAPS", "default_port": 993, "category": "Email Services"},
                        {"value": "pop3", "label": "POP3", "default_port": 110, "category": "Email Services"},
                        {"value": "pop3s", "label": "POP3S", "default_port": 995, "category": "Email Services"},
                        
                        # File Transfer
                        {"value": "ftp", "label": "FTP", "default_port": 21, "category": "File Transfer"},
                        {"value": "ftps", "label": "FTPS", "default_port": 990, "category": "File Transfer"},
                        {"value": "sftp", "label": "SFTP", "default_port": 22, "category": "File Transfer"},
                        
                        # Network Services
                        {"value": "dns", "label": "DNS", "default_port": 53, "category": "Network Services"},
                        {"value": "snmp", "label": "SNMP", "default_port": 161, "category": "Network Services"},
                        {"value": "ntp", "label": "NTP", "default_port": 123, "category": "Network Services"}
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
        # ASSET ENDPOINTS
        # ============================================================================
        
        @self.app.get("/assets")
        async def list_assets(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            search: Optional[str] = Query(None),
            os_type: Optional[str] = Query(None),
            service_type: Optional[str] = Query(None),
            is_active: Optional[bool] = Query(None)
        ):
            """List all assets with optional filtering"""
            try:
                # Build WHERE clause
                where_conditions = []
                params = []
                param_count = 0
                
                if search:
                    param_count += 1
                    where_conditions.append(f"(name ILIKE ${param_count} OR hostname ILIKE ${param_count} OR description ILIKE ${param_count})")
                    params.append(f"%{search}%")
                
                if os_type:
                    param_count += 1
                    where_conditions.append(f"os_type = ${param_count}")
                    params.append(os_type)
                
                if service_type:
                    param_count += 1
                    where_conditions.append(f"service_type = ${param_count}")
                    params.append(service_type)
                
                if is_active is not None:
                    param_count += 1
                    where_conditions.append(f"is_active = ${param_count}")
                    params.append(is_active)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Add pagination params
                params.extend([skip, limit])
                offset_param = param_count + 1
                limit_param = param_count + 2
                
                async with self.db.pool.acquire() as conn:
                    # Get assets
                    query = f"""
                        SELECT id, name, hostname, ip_address, os_type, os_version, description, tags,
                               service_type, port, is_secure, credential_type, username, password_encrypted,
                               private_key_encrypted, api_key_encrypted, bearer_token_encrypted,
                               certificate_encrypted, additional_services, is_active, connection_status,
                               last_tested_at, created_at, updated_at
                        FROM assets.assets
                        {where_clause}
                        ORDER BY created_at DESC
                        OFFSET ${offset_param} LIMIT ${limit_param}
                    """
                    
                    assets = await conn.fetch(query, *params)
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM assets.assets {where_clause}"
                    total = await conn.fetchval(count_query, *params[:-2])  # Exclude skip/limit params
                    
                    asset_list = []
                    for asset in assets:
                        # Check if has credentials
                        has_credentials = any([
                            asset['password_encrypted'],
                            asset['private_key_encrypted'],
                            asset['api_key_encrypted'],
                            asset['bearer_token_encrypted'],
                            asset['certificate_encrypted']
                        ])
                        
                        # Parse tags
                        tags = asset['tags'] if asset['tags'] else []
                        if isinstance(tags, str):
                            tags = json.loads(tags)
                        
                        # Count additional services
                        additional_services = asset['additional_services'] if asset['additional_services'] else []
                        if isinstance(additional_services, str):
                            additional_services = json.loads(additional_services)
                        
                        asset_list.append(AssetSummary(
                            id=asset['id'],
                            name=asset['name'],
                            hostname=asset['hostname'],
                            ip_address=asset['ip_address'],
                            os_type=asset['os_type'],
                            os_version=asset['os_version'],
                            description=asset['description'],
                            tags=tags,
                            service_type=asset['service_type'],
                            port=asset['port'],
                            is_secure=asset['is_secure'],
                            has_credentials=has_credentials,
                            additional_services_count=len(additional_services),
                            is_active=asset['is_active'],
                            connection_status=asset['connection_status'],
                            last_tested_at=asset['last_tested_at'].isoformat() if asset['last_tested_at'] else None,
                            created_at=asset['created_at'].isoformat(),
                            updated_at=asset['updated_at'].isoformat() if asset['updated_at'] else None
                        ))
                    
                    return {
                        "success": True,
                        "data": {
                            "assets": asset_list,
                            "total": total,
                            "skip": skip,
                            "limit": limit
                        }
                    }
            except Exception as e:
                self.logger.error("Failed to list assets", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to list assets"
                )

        @self.app.post("/assets")
        async def create_asset(asset_data: AssetCreate):
            """Create a new asset"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Encrypt credential fields
                        password_encrypted = self._encrypt_field(asset_data.password)
                        private_key_encrypted = self._encrypt_field(asset_data.private_key)
                        api_key_encrypted = self._encrypt_field(asset_data.api_key)
                        bearer_token_encrypted = self._encrypt_field(asset_data.bearer_token)
                        certificate_encrypted = self._encrypt_field(asset_data.certificate)
                        passphrase_encrypted = self._encrypt_field(asset_data.passphrase)
                        secondary_password_encrypted = self._encrypt_field(asset_data.secondary_password)
                        
                        # Encrypt additional services
                        encrypted_additional_services = self._encrypt_additional_services(asset_data.additional_services)
                        
                        # Create asset
                        asset_id = await conn.fetchval("""
                            INSERT INTO assets.assets (
                                name, hostname, ip_address, description, tags,
                                device_type, hardware_make, hardware_model, serial_number,
                                os_type, os_version,
                                physical_address, data_center, building, room, rack_position, rack_location, gps_coordinates,
                                status, environment, criticality, owner, support_contact, contract_number,
                                service_type, port, is_secure, credential_type, username,
                                password_encrypted, private_key_encrypted, public_key,
                                api_key_encrypted, bearer_token_encrypted, certificate_encrypted,
                                passphrase_encrypted, domain,
                                database_type, database_name,
                                secondary_service_type, secondary_port, ftp_type, secondary_username, secondary_password_encrypted,
                                additional_services, notes, created_by
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18,
                                $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34,
                                $35, $36, $37, $38, $39, $40, $41, $42, $43, $44, $45, $46, $47
                            ) RETURNING id
                        """, 
                        asset_data.name,
                        asset_data.hostname,
                        asset_data.ip_address,
                        asset_data.description,
                        json.dumps(asset_data.tags),
                        asset_data.device_type,
                        asset_data.hardware_make,
                        asset_data.hardware_model,
                        asset_data.serial_number,
                        asset_data.os_type,
                        asset_data.os_version,
                        asset_data.physical_address,
                        asset_data.data_center,
                        asset_data.building,
                        asset_data.room,
                        asset_data.rack_position,
                        asset_data.rack_location,
                        asset_data.gps_coordinates,
                        asset_data.status,
                        asset_data.environment,
                        asset_data.criticality,
                        asset_data.owner,
                        asset_data.support_contact,
                        asset_data.contract_number,
                        asset_data.service_type,
                        asset_data.port,
                        asset_data.is_secure,
                        asset_data.credential_type,
                        asset_data.username,
                        password_encrypted,
                        private_key_encrypted,
                        asset_data.public_key,
                        api_key_encrypted,
                        bearer_token_encrypted,
                        certificate_encrypted,
                        passphrase_encrypted,
                        asset_data.domain,
                        asset_data.database_type,
                        asset_data.database_name,
                        asset_data.secondary_service_type,
                        asset_data.secondary_port,
                        asset_data.ftp_type,
                        asset_data.secondary_username,
                        secondary_password_encrypted,
                        json.dumps(encrypted_additional_services),
                        asset_data.notes,
                        1  # Default to admin user
                        )
                        
                        return {
                            "success": True,
                            "data": {"asset_id": asset_id}
                        }
            except Exception as e:
                self.logger.error("Failed to create asset", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create asset"
                )

        @self.app.get("/assets/{asset_id}")
        async def get_asset(asset_id: int):
            """Get asset by ID with decrypted credentials for display"""
            try:
                async with self.db.pool.acquire() as conn:
                    asset = await conn.fetchrow("""
                        SELECT * FROM assets.assets WHERE id = $1
                    """, asset_id)
                    
                    if not asset:
                        raise HTTPException(status_code=404, detail="Asset not found")
                    
                    # Parse tags
                    tags = asset['tags'] if asset['tags'] else []
                    if isinstance(tags, str):
                        tags = json.loads(tags)
                    
                    # Parse and decrypt additional services
                    additional_services = asset['additional_services'] if asset['additional_services'] else []
                    if isinstance(additional_services, str):
                        additional_services = json.loads(additional_services)
                    
                    decrypted_additional_services = self._decrypt_additional_services(additional_services)
                    
                    return {
                        "success": True,
                        "data": AssetDetail(
                            id=asset['id'],
                            name=asset['name'],
                            hostname=asset['hostname'],
                            ip_address=asset['ip_address'],
                            description=asset['description'],
                            tags=tags,
                            os_type=asset['os_type'],
                            os_version=asset['os_version'],
                            service_type=asset['service_type'],
                            port=asset['port'],
                            is_secure=asset['is_secure'],
                            credential_type=asset['credential_type'],
                            username=asset['username'],
                            domain=asset['domain'],
                            additional_services=decrypted_additional_services,
                            is_active=asset['is_active'],
                            connection_status=asset['connection_status'],
                            last_tested_at=asset['last_tested_at'].isoformat() if asset['last_tested_at'] else None,
                            notes=asset['notes'],
                            created_by=asset['created_by'],
                            updated_by=asset['updated_by'],
                            created_at=asset['created_at'].isoformat(),
                            updated_at=asset['updated_at'].isoformat() if asset['updated_at'] else None
                        )
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get asset", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get asset"
                )

        @self.app.put("/assets/{asset_id}")
        async def update_asset(asset_id: int, asset_data: AssetUpdate):
            """Update an asset"""
            try:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Check if asset exists
                        existing = await conn.fetchrow("SELECT id FROM assets.assets WHERE id = $1", asset_id)
                        if not existing:
                            raise HTTPException(status_code=404, detail="Asset not found")
                        
                        # Build update query dynamically
                        update_fields = []
                        params = []
                        param_count = 0
                        
                        # Basic fields
                        for field in ['name', 'hostname', 'ip_address', 'description', 'os_type', 'os_version',
                                    'device_type', 'hardware_make', 'hardware_model', 'serial_number',
                                    'physical_address', 'data_center', 'building', 'room', 'rack_position', 'rack_location', 'gps_coordinates',
                                    'status', 'environment', 'criticality', 'owner', 'support_contact', 'contract_number',
                                    'service_type', 'port', 'is_secure', 'credential_type', 'username',
                                    'public_key', 'domain', 'database_type', 'database_name',
                                    'secondary_service_type', 'secondary_port', 'ftp_type', 'secondary_username',
                                    'notes']:
                            value = getattr(asset_data, field, None)
                            if value is not None:
                                param_count += 1
                                update_fields.append(f"{field} = ${param_count}")
                                params.append(value)
                        
                        # Tags (JSON)
                        if asset_data.tags is not None:
                            param_count += 1
                            update_fields.append(f"tags = ${param_count}")
                            params.append(json.dumps(asset_data.tags))
                        
                        # Encrypted credential fields
                        if asset_data.password is not None:
                            param_count += 1
                            update_fields.append(f"password_encrypted = ${param_count}")
                            params.append(self._encrypt_field(asset_data.password))
                        
                        if asset_data.private_key is not None:
                            param_count += 1
                            update_fields.append(f"private_key_encrypted = ${param_count}")
                            params.append(self._encrypt_field(asset_data.private_key))
                        
                        if asset_data.api_key is not None:
                            param_count += 1
                            update_fields.append(f"api_key_encrypted = ${param_count}")
                            params.append(self._encrypt_field(asset_data.api_key))
                        
                        if asset_data.bearer_token is not None:
                            param_count += 1
                            update_fields.append(f"bearer_token_encrypted = ${param_count}")
                            params.append(self._encrypt_field(asset_data.bearer_token))
                        
                        if asset_data.certificate is not None:
                            param_count += 1
                            update_fields.append(f"certificate_encrypted = ${param_count}")
                            params.append(self._encrypt_field(asset_data.certificate))
                        
                        if asset_data.passphrase is not None:
                            param_count += 1
                            update_fields.append(f"passphrase_encrypted = ${param_count}")
                            params.append(self._encrypt_field(asset_data.passphrase))
                        
                        if asset_data.secondary_password is not None:
                            param_count += 1
                            update_fields.append(f"secondary_password_encrypted = ${param_count}")
                            params.append(self._encrypt_field(asset_data.secondary_password))
                        
                        # Additional services
                        if asset_data.additional_services is not None:
                            param_count += 1
                            update_fields.append(f"additional_services = ${param_count}")
                            encrypted_services = self._encrypt_additional_services(asset_data.additional_services)
                            params.append(json.dumps(encrypted_services))
                        
                        if not update_fields:
                            return {"success": True, "message": "No fields to update"}
                        
                        # Add updated_by and updated_at
                        param_count += 1
                        update_fields.append(f"updated_by = ${param_count}")
                        params.append(1)  # Default to admin user
                        
                        param_count += 1
                        update_fields.append(f"updated_at = ${param_count}")
                        params.append(datetime.utcnow())
                        
                        # Add asset_id for WHERE clause
                        param_count += 1
                        params.append(asset_id)
                        
                        query = f"""
                            UPDATE assets.assets 
                            SET {', '.join(update_fields)}
                            WHERE id = ${param_count}
                        """
                        
                        await conn.execute(query, *params)
                        
                        return {"success": True, "message": "Asset updated successfully"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update asset", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update asset"
                )

        @self.app.delete("/assets/{asset_id}")
        async def delete_asset(asset_id: int):
            """Delete an asset"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute("DELETE FROM assets.assets WHERE id = $1", asset_id)
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Asset not found")
                    
                    return {"success": True, "message": "Asset deleted successfully"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete asset", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete asset"
                )



if __name__ == "__main__":
    service = ConsolidatedAssetService()
    service.run()
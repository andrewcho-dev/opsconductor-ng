#!/usr/bin/env python3
"""
OpsConductor Asset Service - Consolidated
Single table approach for all asset/target information
"""

import sys
import os
import json
import base64
from typing import List, Optional, Dict, Any
from fastapi import Query, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService
from credential_utils import CredentialManager

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
    """Model for asset list view - includes ALL database fields for AI analysis"""
    # Primary Key
    id: int
    
    # Basic Asset Information
    name: str
    hostname: str
    ip_address: Optional[str]
    description: Optional[str]
    tags: List[str]
    
    # Operating System Information
    os_type: str
    os_version: Optional[str]
    
    # Device/Hardware Information
    device_type: Optional[str]
    hardware_make: Optional[str]
    hardware_model: Optional[str]
    serial_number: Optional[str]
    
    # Location Information
    physical_address: Optional[str]
    data_center: Optional[str]
    building: Optional[str]
    room: Optional[str]
    rack_position: Optional[str]
    rack_location: Optional[str]
    gps_coordinates: Optional[str]
    
    # Primary Connection Service
    service_type: str
    port: int
    is_secure: bool
    
    # Primary Service Credentials
    credential_type: Optional[str]
    username: Optional[str]
    domain: Optional[str]
    has_credentials: bool
    
    # Additional Services
    additional_services: List[dict] = []
    additional_services_count: int
    
    # Database-specific fields
    database_type: Optional[str]
    database_name: Optional[str]
    
    # Secondary Service fields
    secondary_service_type: Optional[str]
    secondary_port: Optional[int]
    ftp_type: Optional[str]
    secondary_username: Optional[str]
    
    # Status and Management Information
    is_active: bool
    connection_status: Optional[str]
    last_tested_at: Optional[str]
    status: Optional[str]
    environment: Optional[str]
    criticality: Optional[str]
    owner: Optional[str]
    support_contact: Optional[str]
    contract_number: Optional[str]
    notes: Optional[str]
    
    # Audit Fields
    created_by: Optional[int]
    updated_by: Optional[int]
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
    
    # Device/Hardware Information
    device_type: Optional[str]
    hardware_make: Optional[str]
    hardware_model: Optional[str]
    serial_number: Optional[str]
    
    # Operating System Information
    os_type: str
    os_version: Optional[str]
    
    # Location Information
    physical_address: Optional[str]
    data_center: Optional[str]
    building: Optional[str]
    room: Optional[str]
    rack_position: Optional[str]
    rack_location: Optional[str]
    gps_coordinates: Optional[str]
    
    # Status and Management
    status: Optional[str]
    environment: Optional[str]
    criticality: Optional[str]
    owner: Optional[str]
    support_contact: Optional[str]
    contract_number: Optional[str]
    
    # Primary service
    service_type: str
    port: int
    is_secure: bool
    credential_type: Optional[str]
    username: Optional[str]
    # Note: encrypted fields are not returned in API responses
    domain: Optional[str]
    
    # Database-specific fields
    database_type: Optional[str]
    database_name: Optional[str]
    
    # Secondary service
    secondary_service_type: Optional[str]
    secondary_port: Optional[int]
    ftp_type: Optional[str]
    secondary_username: Optional[str]
    # Note: secondary_password is encrypted and not returned
    
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
        # Use the shared CredentialManager
        self.credential_manager = CredentialManager()
    
    async def setup_service_dependencies(self):
        """Setup asset service specific dependencies"""
        # Identity service dependency
        identity_url = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:3001")
        self.startup_manager.add_service_dependency(
            "identity-service",
            identity_url,
            endpoint="/ready",
            timeout=60,
            critical=True
        )
    
    async def on_startup(self):
        """Asset service startup logic"""
        self.setup_routes()
        self._setup_execution_routes()
    
    async def _get_current_user_id(self) -> Optional[int]:
        """
        Get current user ID from authentication context
        
        Returns:
            User ID from auth context or None if not available
        """
        try:
            # Get the request from the context
            request = self.app.state.request
            
            # Check for auth header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self.logger.warning("No valid authorization header found")
                return None
                
            # Extract token
            token = auth_header.replace('Bearer ', '')
            
            # Get identity service URL from environment or use default
            identity_service_url = os.environ.get('IDENTITY_SERVICE_URL', 'http://identity-service:3001')
            
            # Call identity service to validate token
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{identity_service_url}/api/v1/auth/validate",
                        json={"token": token},
                        timeout=5  # 5 second timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            user_id = data.get("user_id")
                            if user_id:
                                self.logger.info(f"Authenticated user ID: {user_id}")
                                return user_id
                        else:
                            self.logger.warning(f"Token validation failed: {response.status}")
            except aiohttp.ClientError as e:
                self.logger.error(f"Error connecting to identity service: {str(e)}")
            except asyncio.TimeoutError:
                self.logger.error("Timeout connecting to identity service")
            
            # If we reach here, validation failed
            # For development/testing, return a default user ID
            if os.environ.get('ENVIRONMENT') == 'development':
                self.logger.warning("Using default admin user ID in development mode")
                return 1  # Default to admin user in development
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting current user: {str(e)}")
            return None
    
    # Use the shared credential manager methods
    def _encrypt_field(self, value: str) -> Optional[str]:
        """Encrypt a field value"""
        return self.credential_manager.encrypt_field(value)

    def _decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """Decrypt a field value"""
        return self.credential_manager.decrypt_field(encrypted_value)

    def _encrypt_additional_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Encrypt credential fields in additional services"""
        return self.credential_manager.encrypt_additional_services(services)

    def _decrypt_additional_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Decrypt credential fields in additional services for display"""
        return self.credential_manager.decrypt_additional_services(services)

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
        
        @self.app.get("/")
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
                    # Get assets - SELECT ALL FIELDS for comprehensive AI analysis
                    query = f"""
                        SELECT id, name, hostname, ip_address, description, tags,
                               os_type, os_version,
                               device_type, hardware_make, hardware_model, serial_number,
                               physical_address, data_center, building, room, rack_position, rack_location, gps_coordinates,
                               service_type, port, is_secure,
                               credential_type, username, domain, password_encrypted, private_key_encrypted, 
                               api_key_encrypted, bearer_token_encrypted, certificate_encrypted,
                               additional_services,
                               database_type, database_name,
                               secondary_service_type, secondary_port, ftp_type, secondary_username, secondary_password_encrypted,
                               is_active, connection_status, last_tested_at,
                               status, environment, criticality, owner, support_contact, contract_number, notes,
                               created_by, updated_by, created_at, updated_at
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
                            # Primary Key
                            id=asset['id'],
                            
                            # Basic Asset Information
                            name=asset['name'],
                            hostname=asset['hostname'],
                            ip_address=asset['ip_address'],
                            description=asset['description'],
                            tags=tags,
                            
                            # Operating System Information
                            os_type=asset['os_type'],
                            os_version=asset['os_version'],
                            
                            # Device/Hardware Information
                            device_type=asset['device_type'],
                            hardware_make=asset['hardware_make'],
                            hardware_model=asset['hardware_model'],
                            serial_number=asset['serial_number'],
                            
                            # Location Information
                            physical_address=asset['physical_address'],
                            data_center=asset['data_center'],
                            building=asset['building'],
                            room=asset['room'],
                            rack_position=asset['rack_position'],
                            rack_location=asset['rack_location'],
                            gps_coordinates=asset['gps_coordinates'],
                            
                            # Primary Connection Service
                            service_type=asset['service_type'],
                            port=asset['port'],
                            is_secure=asset['is_secure'],
                            
                            # Primary Service Credentials
                            credential_type=asset['credential_type'],
                            username=asset['username'],
                            domain=asset['domain'],
                            has_credentials=has_credentials,
                            
                            # Additional Services
                            additional_services=additional_services,
                            additional_services_count=len(additional_services),
                            
                            # Database-specific fields
                            database_type=asset['database_type'],
                            database_name=asset['database_name'],
                            
                            # Secondary Service fields
                            secondary_service_type=asset['secondary_service_type'],
                            secondary_port=asset['secondary_port'],
                            ftp_type=asset['ftp_type'],
                            secondary_username=asset['secondary_username'],
                            
                            # Status and Management Information
                            is_active=asset['is_active'],
                            connection_status=asset['connection_status'],
                            last_tested_at=asset['last_tested_at'].isoformat() if asset['last_tested_at'] else None,
                            status=asset['status'],
                            environment=asset['environment'],
                            criticality=asset['criticality'],
                            owner=asset['owner'],
                            support_contact=asset['support_contact'],
                            contract_number=asset['contract_number'],
                            notes=asset['notes'],
                            
                            # Audit Fields
                            created_by=asset['created_by'],
                            updated_by=asset['updated_by'],
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

        @self.app.get("/export/csv")
        async def export_assets_csv(
            search: Optional[str] = Query(None),
            os_type: Optional[str] = Query(None),
            service_type: Optional[str] = Query(None),
            is_active: Optional[bool] = Query(None)
        ):
            """Export all assets as CSV (no pagination - returns ALL matching assets)"""
            try:
                import csv
                import io
                from fastapi.responses import StreamingResponse
                
                # Build WHERE clause (same as list_assets)
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
                
                async with self.db.pool.acquire() as conn:
                    # Get ALL assets (no pagination for CSV export)
                    query = f"""
                        SELECT id, name, hostname, ip_address, description, tags,
                               os_type, os_version,
                               device_type, hardware_make, hardware_model, serial_number,
                               physical_address, data_center, building, room, rack_position, rack_location, gps_coordinates,
                               service_type, port, is_secure,
                               credential_type, username, domain,
                               database_type, database_name,
                               secondary_service_type, secondary_port, ftp_type, secondary_username,
                               is_active, connection_status, last_tested_at,
                               status, environment, criticality, owner, support_contact, contract_number, notes,
                               created_by, updated_by, created_at, updated_at
                        FROM assets.assets
                        {where_clause}
                        ORDER BY id ASC
                    """
                    
                    assets = await conn.fetch(query, *params)
                    
                    # Create CSV in memory
                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # Write header
                    writer.writerow([
                        'ID', 'Name', 'Hostname', 'IP Address', 'Description', 'Tags',
                        'OS Type', 'OS Version',
                        'Device Type', 'Hardware Make', 'Hardware Model', 'Serial Number',
                        'Physical Address', 'Data Center', 'Building', 'Room', 'Rack Position', 'Rack Location', 'GPS Coordinates',
                        'Service Type', 'Port', 'Is Secure',
                        'Credential Type', 'Username', 'Domain',
                        'Database Type', 'Database Name',
                        'Secondary Service Type', 'Secondary Port', 'FTP Type', 'Secondary Username',
                        'Is Active', 'Connection Status', 'Last Tested At',
                        'Status', 'Environment', 'Criticality', 'Owner', 'Support Contact', 'Contract Number', 'Notes',
                        'Created By', 'Updated By', 'Created At', 'Updated At'
                    ])
                    
                    # Write data rows
                    for asset in assets:
                        # Parse tags
                        tags = asset['tags'] if asset['tags'] else []
                        if isinstance(tags, str):
                            tags = json.loads(tags)
                        tags_str = ','.join(tags) if tags else ''
                        
                        writer.writerow([
                            asset['id'],
                            asset['name'],
                            asset['hostname'],
                            asset['ip_address'] or '',
                            asset['description'] or '',
                            tags_str,
                            asset['os_type'],
                            asset['os_version'] or '',
                            asset['device_type'],
                            asset['hardware_make'] or '',
                            asset['hardware_model'] or '',
                            asset['serial_number'] or '',
                            asset['physical_address'] or '',
                            asset['data_center'] or '',
                            asset['building'] or '',
                            asset['room'] or '',
                            asset['rack_position'] or '',
                            asset['rack_location'] or '',
                            asset['gps_coordinates'] or '',
                            asset['service_type'],
                            asset['port'],
                            'Yes' if asset['is_secure'] else 'No',
                            asset['credential_type'] or '',
                            asset['username'] or '',
                            asset['domain'] or '',
                            asset['database_type'] or '',
                            asset['database_name'] or '',
                            asset['secondary_service_type'] or '',
                            asset['secondary_port'] or '',
                            asset['ftp_type'] or '',
                            asset['secondary_username'] or '',
                            'Yes' if asset['is_active'] else 'No',
                            asset['connection_status'] or '',
                            asset['last_tested_at'].isoformat() if asset['last_tested_at'] else '',
                            asset['status'],
                            asset['environment'],
                            asset['criticality'],
                            asset['owner'] or '',
                            asset['support_contact'] or '',
                            asset['contract_number'] or '',
                            asset['notes'] or '',
                            asset['created_by'] or '',
                            asset['updated_by'] or '',
                            asset['created_at'].isoformat() if asset['created_at'] else '',
                            asset['updated_at'].isoformat() if asset['updated_at'] else ''
                        ])
                    
                    # Return CSV as downloadable file
                    output.seek(0)
                    return StreamingResponse(
                        iter([output.getvalue()]),
                        media_type="text/csv",
                        headers={
                            "Content-Disposition": f"attachment; filename=assets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        }
                    )
                    
            except Exception as e:
                self.logger.error("Failed to export assets to CSV", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to export assets to CSV"
                )

        @self.app.post("/")
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

        @self.app.get("/{asset_id}")
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
                            
                            # Device/Hardware Information
                            device_type=asset['device_type'],
                            hardware_make=asset['hardware_make'],
                            hardware_model=asset['hardware_model'],
                            serial_number=asset['serial_number'],
                            
                            # Operating System Information
                            os_type=asset['os_type'],
                            os_version=asset['os_version'],
                            
                            # Location Information
                            physical_address=asset['physical_address'],
                            data_center=asset['data_center'],
                            building=asset['building'],
                            room=asset['room'],
                            rack_position=asset['rack_position'],
                            rack_location=asset['rack_location'],
                            gps_coordinates=asset['gps_coordinates'],
                            
                            # Status and Management
                            status=asset['status'],
                            environment=asset['environment'],
                            criticality=asset['criticality'],
                            owner=asset['owner'],
                            support_contact=asset['support_contact'],
                            contract_number=asset['contract_number'],
                            
                            # Primary service
                            service_type=asset['service_type'],
                            port=asset['port'],
                            is_secure=asset['is_secure'],
                            credential_type=asset['credential_type'],
                            username=asset['username'],
                            domain=asset['domain'],
                            
                            # Database-specific fields
                            database_type=asset['database_type'],
                            database_name=asset['database_name'],
                            
                            # Secondary service
                            secondary_service_type=asset['secondary_service_type'],
                            secondary_port=asset['secondary_port'],
                            ftp_type=asset['ftp_type'],
                            secondary_username=asset['secondary_username'],
                            
                            # Additional services and metadata
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

        @self.app.put("/{asset_id}")
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

        @self.app.delete("/{asset_id}")
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
        
        @self.app.post("/{asset_id}/test")
        async def test_asset_connection(asset_id: int):
            """
            Test connection to an asset
            
            Attempts to connect to the asset using the appropriate protocol
            based on the service type. Updates the connection status in the database.
            """
            try:
                async with self.db.pool.acquire() as conn:
                    # Get asset details
                    asset = await conn.fetchrow("""
                        SELECT id, name, hostname, ip_address, service_type, port, 
                               is_secure, credential_type, username, password_encrypted,
                               private_key_encrypted, api_key_encrypted, bearer_token_encrypted,
                               certificate_encrypted, passphrase_encrypted, domain,
                               database_type, database_name
                        FROM assets.assets
                        WHERE id = $1
                    """, asset_id)
                    
                    if not asset:
                        raise HTTPException(status_code=404, detail="Asset not found")
                    
                    # Decrypt credentials if needed
                    password = None
                    private_key = None
                    api_key = None
                    bearer_token = None
                    certificate = None
                    passphrase = None
                    
                    if asset['password_encrypted']:
                        password = self._decrypt_field(asset['password_encrypted'])
                    
                    if asset['private_key_encrypted']:
                        private_key = self._decrypt_field(asset['private_key_encrypted'])
                    
                    if asset['api_key_encrypted']:
                        api_key = self._decrypt_field(asset['api_key_encrypted'])
                    
                    if asset['bearer_token_encrypted']:
                        bearer_token = self._decrypt_field(asset['bearer_token_encrypted'])
                    
                    if asset['certificate_encrypted']:
                        certificate = self._decrypt_field(asset['certificate_encrypted'])
                    
                    if asset['passphrase_encrypted']:
                        passphrase = self._decrypt_field(asset['passphrase_encrypted'])
                    
                    # Test connection based on service type
                    connection_status = "failed"
                    error_message = None
                    
                    try:
                        # Get connection parameters
                        hostname = asset['hostname']
                        ip_address = asset['ip_address']
                        port = asset['port']
                        service_type = asset['service_type']
                        username = asset['username']
                        domain = asset['domain']
                        is_secure = asset['is_secure']
                        database_type = asset['database_type']
                        database_name = asset['database_name']
                        
                        # Use hostname if available, otherwise IP address
                        host = hostname or ip_address
                        if not host:
                            raise ValueError("No hostname or IP address specified")
                        
                        # Test connection based on service type
                        if service_type in ['http', 'https', 'http_alt', 'https_alt']:
                            # Test HTTP/HTTPS connection
                            connection_status = await self._test_http_connection(
                                host, port, is_secure, username, password, api_key, bearer_token
                            )
                        elif service_type in ['ssh', 'sftp']:
                            # Test SSH/SFTP connection
                            connection_status = await self._test_ssh_connection(
                                host, port, username, password, private_key, passphrase
                            )
                        elif service_type in ['mysql', 'postgresql', 'sql_server', 'oracle', 'mongodb', 'redis']:
                            # Test database connection
                            connection_status = await self._test_database_connection(
                                host, port, service_type, database_name, username, password
                            )
                        elif service_type in ['ftp', 'ftps']:
                            # Test FTP connection
                            connection_status = await self._test_ftp_connection(
                                host, port, is_secure, username, password
                            )
                        elif service_type in ['smtp', 'smtps', 'smtp_submission']:
                            # Test SMTP connection
                            connection_status = await self._test_smtp_connection(
                                host, port, is_secure, username, password
                            )
                        elif service_type in ['winrm', 'winrm_https']:
                            # Test WinRM connection
                            connection_status = await self._test_winrm_connection(
                                host, port, is_secure, username, password, domain
                            )
                        elif service_type == 'rdp':
                            # Test RDP connection
                            connection_status = await self._test_rdp_connection(
                                host, port, username, password, domain
                            )
                        elif service_type == 'smb':
                            # Test SMB/CIFS connection
                            connection_status = await self._test_smb_connection(
                                host, port, username, password, domain
                            )
                        elif service_type == 'snmp':
                            # Test SNMP connection
                            connection_status = await self._test_snmp_connection(
                                host, port, username, password
                            )
                        else:
                            # For other service types, use a basic port check
                            connection_status = await self._test_basic_connection(host, port)
                    
                    except Exception as conn_error:
                        self.logger.error(f"Connection test error: {str(conn_error)}")
                        error_message = str(conn_error)
                        connection_status = "failed"
                    
                    # Update the connection status
                    await conn.execute("""
                        UPDATE assets.assets
                        SET connection_status = $2,
                            last_tested_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """, asset_id, connection_status)
                    
                    response = {
                        "success": connection_status == "connected",
                        "message": "Connection test successful" if connection_status == "connected" else "Connection test failed",
                        "data": {
                            "connection_status": connection_status,
                            "last_tested_at": datetime.now().isoformat()
                        }
                    }
                    
                    if error_message:
                        response["data"]["error"] = error_message
                    
                    return response
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to test asset connection", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to test asset connection"
                )
        
        @self.app.get("/{asset_id}/credentials")
        async def get_asset_credentials(asset_id: int):
            """
            Get decrypted credentials for an asset (internal service-to-service use only)
            
            This endpoint returns decrypted credentials for use by other services
            (e.g., automation-service, ai-pipeline) that need to execute commands
            on the asset.
            
            WARNING: This endpoint should only be accessible to internal services,
            not exposed to external users.
            """
            try:
                async with self.db.pool.acquire() as conn:
                    asset = await conn.fetchrow("""
                        SELECT id, name, hostname, ip_address, os_type, service_type, port,
                               credential_type, username, domain,
                               password_encrypted, private_key_encrypted, api_key_encrypted,
                               bearer_token_encrypted, certificate_encrypted, passphrase_encrypted
                        FROM assets.assets
                        WHERE id = $1
                    """, asset_id)
                    
                    if not asset:
                        raise HTTPException(status_code=404, detail="Asset not found")
                    
                    # Decrypt credentials
                    credentials = {
                        "asset_id": asset['id'],
                        "name": asset['name'],
                        "hostname": asset['hostname'],
                        "ip_address": asset['ip_address'],
                        "os_type": asset['os_type'],
                        "service_type": asset['service_type'],
                        "port": asset['port'],
                        "credential_type": asset['credential_type'],
                        "username": asset['username'],
                        "domain": asset['domain'],
                    }
                    
                    # Decrypt password if available
                    if asset['password_encrypted']:
                        credentials['password'] = self._decrypt_field(asset['password_encrypted'])
                    
                    # Decrypt private key if available
                    if asset['private_key_encrypted']:
                        credentials['private_key'] = self._decrypt_field(asset['private_key_encrypted'])
                    
                    # Decrypt API key if available
                    if asset['api_key_encrypted']:
                        credentials['api_key'] = self._decrypt_field(asset['api_key_encrypted'])
                    
                    # Decrypt bearer token if available
                    if asset['bearer_token_encrypted']:
                        credentials['bearer_token'] = self._decrypt_field(asset['bearer_token_encrypted'])
                    
                    # Decrypt certificate if available
                    if asset['certificate_encrypted']:
                        credentials['certificate'] = self._decrypt_field(asset['certificate_encrypted'])
                    
                    # Decrypt passphrase if available
                    if asset['passphrase_encrypted']:
                        credentials['passphrase'] = self._decrypt_field(asset['passphrase_encrypted'])
                    
                    return {
                        "success": True,
                        "data": credentials
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get asset credentials", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get asset credentials"
                )



    # Connection testing methods
    async def _test_basic_connection(self, host: str, port: int) -> str:
        """
        Test basic TCP connection to a host and port
        
        Args:
            host: Hostname or IP address
            port: Port number
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import socket
        import asyncio
        
        try:
            # Create a socket connection to test if port is open
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return "connected"
        except (socket.error, asyncio.TimeoutError, ConnectionRefusedError) as e:
            self.logger.error(f"Basic connection test failed: {str(e)}")
            return "failed"
    
    async def _test_http_connection(self, host: str, port: int, is_secure: bool, 
                                   username: Optional[str], password: Optional[str],
                                   api_key: Optional[str], bearer_token: Optional[str]) -> str:
        """
        Test HTTP/HTTPS connection
        
        Args:
            host: Hostname or IP address
            port: Port number
            is_secure: Whether to use HTTPS
            username: Optional username for basic auth
            password: Optional password for basic auth
            api_key: Optional API key
            bearer_token: Optional bearer token
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import aiohttp
        
        protocol = "https" if is_secure else "http"
        url = f"{protocol}://{host}:{port}"
        
        try:
            headers = {}
            auth = None
            
            # Add authentication if provided
            if bearer_token:
                headers["Authorization"] = f"Bearer {bearer_token}"
            elif api_key:
                headers["X-API-Key"] = api_key
            elif username and password:
                auth = aiohttp.BasicAuth(username, password)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, auth=auth, 
                                      ssl=None, timeout=10) as response:
                    # Any response means we could connect
                    return "connected"
        except Exception as e:
            self.logger.error(f"HTTP connection test failed: {str(e)}")
            return "failed"
    
    async def _test_ssh_connection(self, host: str, port: int, username: Optional[str],
                                  password: Optional[str], private_key: Optional[str],
                                  passphrase: Optional[str]) -> str:
        """
        Test SSH connection
        
        Args:
            host: Hostname or IP address
            port: Port number
            username: SSH username
            password: Optional SSH password
            private_key: Optional private key
            passphrase: Optional passphrase for private key
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        import asyncssh
        import tempfile
        import os
        
        # If no username is provided, we can't authenticate
        if not username:
            self.logger.warning("No username provided for SSH connection test")
            # Fall back to basic connection test
            return await self._test_basic_connection(host, port)
        
        try:
            # Set up connection parameters
            conn_params = {
                'host': host,
                'port': port,
                'username': username,
                'known_hosts': None  # Don't verify host keys for testing
            }
            
            # Add authentication method
            if private_key:
                # Create a temporary file for the private key
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
                    key_file.write(private_key)
                    key_path = key_file.name
                
                try:
                    # Add private key authentication
                    if passphrase:
                        conn_params['client_keys'] = [(key_path, passphrase)]
                    else:
                        conn_params['client_keys'] = [key_path]
                    
                    # Try to connect with timeout
                    async with asyncio.timeout(10):
                        async with asyncssh.connect(**conn_params):
                            self.logger.info(f"SSH connection successful to {host}:{port} with key authentication")
                            return "connected"
                finally:
                    # Clean up the temporary key file
                    try:
                        os.unlink(key_path)
                    except Exception:
                        pass
            
            elif password:
                # Add password authentication
                conn_params['password'] = password
                
                # Try to connect with timeout
                async with asyncio.timeout(10):
                    async with asyncssh.connect(**conn_params):
                        self.logger.info(f"SSH connection successful to {host}:{port} with password authentication")
                        return "connected"
            else:
                self.logger.warning("No authentication method provided for SSH connection test")
                # Fall back to basic connection test
                return await self._test_basic_connection(host, port)
                
        except (asyncssh.DisconnectError, asyncssh.ProcessError) as e:
            self.logger.error(f"SSH connection error: {str(e)}")
            return "failed"
        except (asyncssh.ChannelOpenError, asyncssh.ConnectionLost) as e:
            self.logger.error(f"SSH channel error: {str(e)}")
            return "failed"
        except asyncssh.PermissionDenied as e:
            self.logger.error(f"SSH authentication failed: {str(e)}")
            return "failed"
        except asyncio.TimeoutError:
            self.logger.error(f"SSH connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"SSH connection test failed: {str(e)}")
            # Fall back to basic connection test if SSH library fails
            return await self._test_basic_connection(host, port)
    
    async def _test_database_connection(self, host: str, port: int, db_type: str,
                                       db_name: Optional[str], username: Optional[str],
                                       password: Optional[str]) -> str:
        """
        Test database connection
        
        Args:
            host: Hostname or IP address
            port: Port number
            db_type: Database type (mysql, postgresql, etc.)
            db_name: Database name
            username: Database username
            password: Database password
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        
        # If no database type is specified, fall back to basic connection
        if not db_type:
            self.logger.warning("No database type specified for connection test")
            return await self._test_basic_connection(host, port)
        
        # Normalize database type
        db_type = db_type.lower()
        
        try:
            # PostgreSQL connection test
            if db_type == 'postgresql':
                return await self._test_postgresql_connection(
                    host, port, db_name, username, password
                )
            
            # MySQL connection test
            elif db_type == 'mysql':
                return await self._test_mysql_connection(
                    host, port, db_name, username, password
                )
            
            # MongoDB connection test
            elif db_type == 'mongodb':
                return await self._test_mongodb_connection(
                    host, port, db_name, username, password
                )
            
            # Redis connection test
            elif db_type == 'redis':
                return await self._test_redis_connection(
                    host, port, password
                )
            
            # For other database types, fall back to basic connection test
            else:
                self.logger.info(f"Using basic connection test for database type: {db_type}")
                return await self._test_basic_connection(host, port)
                
        except asyncio.TimeoutError:
            self.logger.error(f"Database connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            # Fall back to basic connection test if database-specific test fails
            return await self._test_basic_connection(host, port)
    
    async def _test_postgresql_connection(self, host: str, port: int, db_name: Optional[str],
                                         username: Optional[str], password: Optional[str]) -> str:
        """Test PostgreSQL connection"""
        try:
            import asyncpg
            
            # Set default database if not provided
            db_name = db_name or 'postgres'
            
            # Connect with timeout
            import asyncio
            async with asyncio.timeout(10):
                conn = await asyncpg.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=db_name
                )
                await conn.close()
                
            self.logger.info(f"PostgreSQL connection successful to {host}:{port}/{db_name}")
            return "connected"
        except ImportError:
            self.logger.warning("asyncpg library not available, falling back to basic connection test")
            return await self._test_basic_connection(host, port)
        except Exception as e:
            self.logger.error(f"PostgreSQL connection error: {str(e)}")
            return "failed"
    
    async def _test_mysql_connection(self, host: str, port: int, db_name: Optional[str],
                                    username: Optional[str], password: Optional[str]) -> str:
        """Test MySQL connection"""
        try:
            import aiomysql
            
            # Set default database if not provided
            db_name = db_name or 'mysql'
            
            # Connect with timeout
            import asyncio
            async with asyncio.timeout(10):
                conn = await aiomysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    db=db_name
                )
                conn.close()
                
            self.logger.info(f"MySQL connection successful to {host}:{port}/{db_name}")
            return "connected"
        except ImportError:
            self.logger.warning("aiomysql library not available, falling back to basic connection test")
            return await self._test_basic_connection(host, port)
        except Exception as e:
            self.logger.error(f"MySQL connection error: {str(e)}")
            return "failed"
    
    async def _test_mongodb_connection(self, host: str, port: int, db_name: Optional[str],
                                      username: Optional[str], password: Optional[str]) -> str:
        """Test MongoDB connection"""
        try:
            import motor.motor_asyncio
            
            # Build connection string
            if username and password:
                uri = f"mongodb://{username}:{password}@{host}:{port}"
            else:
                uri = f"mongodb://{host}:{port}"
                
            # Add database name if provided
            if db_name:
                uri += f"/{db_name}"
                
            # Connect with timeout
            import asyncio
            async with asyncio.timeout(10):
                client = motor.motor_asyncio.AsyncIOMotorClient(
                    uri, 
                    serverSelectionTimeoutMS=5000
                )
                # Force a connection to verify it works
                await client.admin.command('ping')
                client.close()
                
            self.logger.info(f"MongoDB connection successful to {host}:{port}")
            return "connected"
        except ImportError:
            self.logger.warning("motor library not available, falling back to basic connection test")
            return await self._test_basic_connection(host, port)
        except Exception as e:
            self.logger.error(f"MongoDB connection error: {str(e)}")
            return "failed"
    
    async def _test_redis_connection(self, host: str, port: int, password: Optional[str]) -> str:
        """Test Redis connection"""
        try:
            import aioredis
            
            # Build connection URL
            if password:
                redis_url = f"redis://:{password}@{host}:{port}"
            else:
                redis_url = f"redis://{host}:{port}"
                
            # Connect with timeout
            import asyncio
            async with asyncio.timeout(10):
                redis = aioredis.from_url(redis_url)
                await redis.ping()
                await redis.close()
                
            self.logger.info(f"Redis connection successful to {host}:{port}")
            return "connected"
        except ImportError:
            self.logger.warning("aioredis library not available, falling back to basic connection test")
            return await self._test_basic_connection(host, port)
        except Exception as e:
            self.logger.error(f"Redis connection error: {str(e)}")
            return "failed"
    
    async def _test_ftp_connection(self, host: str, port: int, is_secure: bool,
                                  username: Optional[str], password: Optional[str]) -> str:
        """
        Test FTP connection
        
        Args:
            host: Hostname or IP address
            port: Port number
            is_secure: Whether to use FTPS
            username: FTP username
            password: FTP password
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        from ftplib import FTP, FTP_TLS, error_perm
        import ssl
        
        # Use default port if not specified
        if not port:
            port = 990 if is_secure else 21
        
        # Use anonymous login if credentials not provided
        username = username or 'anonymous'
        password = password or 'anonymous@example.com'
        
        # Create a future to hold the result
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        # Define the FTP connection function to run in a thread
        def connect_ftp():
            try:
                if is_secure:
                    # Use FTPS
                    ftp = FTP_TLS()
                    ftp.connect(host, port, timeout=10)
                    ftp.login(username, password)
                    ftp.prot_p()  # Set up secure data connection
                else:
                    # Use regular FTP
                    ftp = FTP()
                    ftp.connect(host, port, timeout=10)
                    ftp.login(username, password)
                
                # Test if we can list directory contents
                ftp.nlst()
                
                # Close the connection
                ftp.quit()
                return "connected"
            except error_perm as e:
                # Authentication succeeded but permission error on command
                if str(e).startswith('530'):
                    self.logger.error(f"FTP authentication failed: {str(e)}")
                else:
                    self.logger.error(f"FTP permission error: {str(e)}")
                return "failed"
            except ssl.SSLError as e:
                self.logger.error(f"FTP SSL error: {str(e)}")
                return "failed"
            except Exception as e:
                self.logger.error(f"FTP connection error: {str(e)}")
                return "failed"
        
        try:
            # Run the FTP connection in a thread with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, connect_ftp),
                timeout=15
            )
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"FTP connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"FTP connection test failed: {str(e)}")
            # Fall back to basic connection test if FTP test fails
            return await self._test_basic_connection(host, port)
    
    async def _test_smtp_connection(self, host: str, port: int, is_secure: bool,
                                   username: Optional[str], password: Optional[str]) -> str:
        """
        Test SMTP connection
        
        Args:
            host: Hostname or IP address
            port: Port number
            is_secure: Whether to use SSL/TLS
            username: SMTP username
            password: SMTP password
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        import smtplib
        import ssl
        
        # Use default port if not specified
        if not port:
            if is_secure:
                port = 465  # SMTPS
            else:
                port = 587 if username and password else 25  # SMTP with STARTTLS or plain SMTP
        
        # Create a future to hold the result
        loop = asyncio.get_event_loop()
        
        # Define the SMTP connection function to run in a thread
        def connect_smtp():
            try:
                if is_secure:
                    # Use SMTP_SSL for direct SSL connection
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(host, port, context=context, timeout=10)
                else:
                    # Use regular SMTP with optional STARTTLS
                    server = smtplib.SMTP(host, port, timeout=10)
                    
                    # Try STARTTLS if available
                    try:
                        server.ehlo()
                        if server.has_extn('STARTTLS'):
                            context = ssl.create_default_context()
                            server.starttls(context=context)
                            server.ehlo()
                    except Exception as e:
                        self.logger.warning(f"STARTTLS failed, continuing with unencrypted connection: {str(e)}")
                
                # Try to authenticate if credentials are provided
                if username and password:
                    server.login(username, password)
                
                # Close the connection
                server.quit()
                return "connected"
            except smtplib.SMTPAuthenticationError as e:
                self.logger.error(f"SMTP authentication failed: {str(e)}")
                return "failed"
            except smtplib.SMTPException as e:
                self.logger.error(f"SMTP error: {str(e)}")
                return "failed"
            except ssl.SSLError as e:
                self.logger.error(f"SMTP SSL error: {str(e)}")
                return "failed"
            except Exception as e:
                self.logger.error(f"SMTP connection error: {str(e)}")
                return "failed"
        
        try:
            # Run the SMTP connection in a thread with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, connect_smtp),
                timeout=15
            )
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"SMTP connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {str(e)}")
            # Fall back to basic connection test if SMTP test fails
            return await self._test_basic_connection(host, port)
            
    async def _test_winrm_connection(self, host: str, port: int, is_secure: bool,
                                   username: Optional[str], password: Optional[str],
                                   domain: Optional[str]) -> str:
        """
        Test WinRM connection
        
        Args:
            host: Hostname or IP address
            port: Port number (typically 5985 for HTTP or 5986 for HTTPS)
            is_secure: Whether to use HTTPS (WinRM HTTPS)
            username: WinRM username
            password: WinRM password
            domain: Windows domain (optional)
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        
        # If no username or password is provided, we can't authenticate
        if not username or not password:
            self.logger.warning("No username or password provided for WinRM connection test")
            # Fall back to basic connection test
            return await self._test_basic_connection(host, port)
        
        # Define a synchronous function to run in a thread
        def connect_winrm():
            try:
                import winrm
                
                # Build endpoint URL
                protocol = "https" if is_secure else "http"
                endpoint = f"{protocol}://{host}:{port}/wsman"
                
                # Format username with domain if provided
                if domain and username and not username.startswith(f"{domain}\\"):
                    auth_username = f"{domain}\\{username}"
                else:
                    auth_username = username
                
                # Set up session options
                session_options = {
                    'transport': 'ntlm',  # Use NTLM authentication by default
                    'read_timeout_sec': 10,
                    'operation_timeout_sec': 10
                }
                
                # Add SSL verification options for HTTPS
                if is_secure:
                    session_options['server_cert_validation'] = 'ignore'  # For testing purposes
                
                # Create session
                session = winrm.Session(
                    endpoint,
                    auth=(auth_username, password),
                    **session_options
                )
                
                # Execute a simple command to test connectivity
                result = session.run_cmd("hostname")
                if result.status_code == 0:
                    self.logger.info(f"WinRM connection successful to {host}:{port}")
                    return "connected"
                else:
                    self.logger.error(f"WinRM command failed with status {result.status_code}: {result.std_err}")
                    return "failed"
                    
            except ImportError:
                self.logger.warning("winrm library not available, falling back to basic connection test")
                return "import_error"
            except Exception as e:
                self.logger.error(f"WinRM connection error: {str(e)}")
                return "failed"
        
        try:
            # Get event loop
            loop = asyncio.get_event_loop()
            
            # Run the WinRM connection in a thread with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, connect_winrm),
                timeout=15
            )
            
            # If import error occurred, fall back to basic connection test
            if result == "import_error":
                return await self._test_basic_connection(host, port)
                
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"WinRM connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"WinRM connection test failed: {str(e)}")
            # Fall back to basic connection test if WinRM test fails
            return await self._test_basic_connection(host, port)


    async def _test_rdp_connection(self, host: str, port: int, username: Optional[str],
                                  password: Optional[str], domain: Optional[str]) -> str:
        """
        Test RDP connection
        
        Args:
            host: Hostname or IP address
            port: Port number (typically 3389)
            username: RDP username
            password: RDP password
            domain: Windows domain (optional)
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        import socket
        
        # Define a synchronous function to run in a thread
        def connect_rdp():
            try:
                # For RDP, we can use the freerdp-python library if available
                # Otherwise, we'll do a more basic check
                try:
                    import freerdp
                    
                    # Format username with domain if provided
                    if domain and username and not username.startswith(f"{domain}\\"):
                        auth_username = f"{domain}\\{username}"
                    else:
                        auth_username = username
                    
                    # Create RDP client
                    client = freerdp.Client()
                    
                    # Set connection parameters
                    client.hostname = host
                    client.port = port
                    client.username = auth_username
                    client.password = password
                    client.ignore_certificate = True  # For testing purposes
                    
                    # Connect with a timeout
                    result = client.connect()
                    if result:
                        self.logger.info(f"RDP connection successful to {host}:{port}")
                        client.disconnect()
                        return "connected"
                    else:
                        self.logger.error(f"RDP connection failed to {host}:{port}")
                        return "failed"
                        
                except ImportError:
                    # If freerdp-python is not available, fall back to a basic socket check
                    # with an RDP protocol negotiation attempt
                    self.logger.warning("freerdp-python library not available, using basic RDP check")
                    
                    # Create socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    
                    # Connect to the server
                    sock.connect((host, port))
                    
                    # Send RDP connection request (simplified)
                    # This is a basic RDP negotiation packet
                    rdp_neg_req = bytes.fromhex(
                        "0300002b26e00000000000436f6f6b69653a206d737473686173683d757365720d0a0100080001000000"
                    )
                    sock.send(rdp_neg_req)
                    
                    # Try to receive a response
                    response = sock.recv(1024)
                    
                    # Close the socket
                    sock.close()
                    
                    # Check if we got a valid RDP response
                    # A valid response should be at least 19 bytes and start with 0x03 (TPKT header)
                    if len(response) >= 19 and response[0] == 0x03:
                        self.logger.info(f"Basic RDP check successful to {host}:{port}")
                        return "connected"
                    else:
                        self.logger.error(f"Invalid RDP response from {host}:{port}")
                        return "failed"
                    
            except socket.timeout:
                self.logger.error(f"RDP connection timeout to {host}:{port}")
                return "failed"
            except socket.error as e:
                self.logger.error(f"RDP socket error: {str(e)}")
                return "failed"
            except Exception as e:
                self.logger.error(f"RDP connection error: {str(e)}")
                return "failed"
        
        try:
            # Get event loop
            loop = asyncio.get_event_loop()
            
            # Run the RDP connection in a thread with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, connect_rdp),
                timeout=15
            )
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"RDP connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"RDP connection test failed: {str(e)}")
            # Fall back to basic connection test if RDP test fails
            return await self._test_basic_connection(host, port)
            
    async def _test_smb_connection(self, host: str, port: int, username: Optional[str],
                                  password: Optional[str], domain: Optional[str]) -> str:
        """
        Test SMB/CIFS connection
        
        Args:
            host: Hostname or IP address
            port: Port number (typically 445)
            username: SMB username
            password: SMB password
            domain: Windows domain (optional)
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        import uuid
        
        # If no username or password is provided, we can't authenticate
        if not username or not password:
            self.logger.warning("No username or password provided for SMB connection test")
            # Fall back to basic connection test
            return await self._test_basic_connection(host, port)
        
        # Define a synchronous function to run in a thread
        def connect_smb():
            try:
                import smbprotocol.connection
                from smbprotocol.session import Session
                
                # Format username with domain if provided
                if domain:
                    auth_username = f"{domain}\\{username}"
                else:
                    auth_username = username
                
                # Create SMB connection
                connection = smbprotocol.connection.Connection(uuid.uuid4(), host, port)
                
                # Connect to the server
                connection.connect()
                
                # Create session and authenticate
                session = Session(connection, auth_username, password)
                session.connect()
                
                # If we get here, authentication was successful
                self.logger.info(f"SMB connection successful to {host}:{port}")
                
                # Clean up
                connection.disconnect()
                return "connected"
                
            except ImportError:
                self.logger.warning("smbprotocol library not available, falling back to pysmb")
                try:
                    from smb.SMBConnection import SMBConnection
                    
                    # Create SMB connection
                    conn = SMBConnection(
                        username,
                        password,
                        "OpsConductor",  # Client name
                        host,            # Server name
                        domain=domain,
                        use_ntlm_v2=True,
                        is_direct_tcp=(port == 445)
                    )
                    
                    # Connect to the server
                    if conn.connect(host, port):
                        # List shares to verify connection
                        shares = conn.listShares()
                        conn.close()
                        self.logger.info(f"SMB connection successful to {host}:{port}")
                        return "connected"
                    else:
                        self.logger.error(f"SMB connection failed to {host}:{port}")
                        return "failed"
                        
                except ImportError:
                    self.logger.warning("No SMB libraries available, falling back to basic connection test")
                    return "import_error"
                except Exception as e:
                    self.logger.error(f"SMB connection error with pysmb: {str(e)}")
                    return "failed"
                    
            except Exception as e:
                self.logger.error(f"SMB connection error: {str(e)}")
                return "failed"
        
        try:
            # Get event loop
            loop = asyncio.get_event_loop()
            
            # Run the SMB connection in a thread with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, connect_smb),
                timeout=15
            )
            
            # If import error occurred, fall back to basic connection test
            if result == "import_error":
                return await self._test_basic_connection(host, port)
                
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"SMB connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"SMB connection test failed: {str(e)}")
            # Fall back to basic connection test if SMB test fails
            return await self._test_basic_connection(host, port)
            
    async def _test_snmp_connection(self, host: str, port: int, username: Optional[str],
                                   password: Optional[str]) -> str:
        """
        Test SNMP connection
        
        Args:
            host: Hostname or IP address
            port: Port number (typically 161)
            username: SNMP community string or username
            password: SNMP password or auth key
            
        Returns:
            Connection status: "connected" or "failed"
        """
        import asyncio
        
        # Define a synchronous function to run in a thread
        def connect_snmp():
            try:
                from pysnmp.hlapi import (
                    SnmpEngine, CommunityData, UdpTransportTarget,
                    ContextData, ObjectType, ObjectIdentity, getCmd
                )
                
                # Set up SNMP parameters
                # Use username as community string if provided, otherwise use "public"
                community = username or "public"
                
                # Create SNMP engine
                engine = SnmpEngine()
                
                # Send SNMP GET request for system description
                error_indication, error_status, error_index, var_binds = next(
                    getCmd(
                        engine,
                        CommunityData(community),
                        UdpTransportTarget((host, port), timeout=5, retries=1),
                        ContextData(),
                        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
                    )
                )
                
                # Check for errors
                if error_indication:
                    self.logger.error(f"SNMP error: {error_indication}")
                    return "failed"
                elif error_status:
                    self.logger.error(f"SNMP error: {error_status.prettyPrint()} at {var_binds[int(error_index) - 1][0] if error_index else '?'}")
                    return "failed"
                else:
                    # Successfully got a response
                    self.logger.info(f"SNMP connection successful to {host}:{port}")
                    return "connected"
                    
            except ImportError:
                self.logger.warning("pysnmp library not available, falling back to basic connection test")
                return "import_error"
            except Exception as e:
                self.logger.error(f"SNMP connection error: {str(e)}")
                return "failed"
        
        try:
            # Get event loop
            loop = asyncio.get_event_loop()
            
            # Run the SNMP connection in a thread with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, connect_snmp),
                timeout=15
            )
            
            # If import error occurred, fall back to basic connection test
            if result == "import_error":
                return await self._test_basic_connection(host, port)
                
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"SNMP connection timeout to {host}:{port}")
            return "failed"
        except Exception as e:
            self.logger.error(f"SNMP connection test failed: {str(e)}")
            # Fall back to basic connection test if SNMP test fails
            return await self._test_basic_connection(host, port)
    
    def _setup_execution_routes(self):
        """Setup execution routes for AI-pipeline integration"""
        
        @self.app.post("/execute-plan")
        async def execute_plan_from_pipeline(request: Dict[str, Any]):
            """
            Execute an asset management plan from AI-pipeline
            
            Handles asset-specific tools:
            - asset_query: Query asset inventory
            - asset_create: Create new assets
            - asset_update: Update existing assets
            - asset_delete: Delete assets
            - asset_list: List assets
            
            Args:
                request: {
                    "execution_id": str,
                    "plan": dict,
                    "tenant_id": str,
                    "actor_id": int
                }
            
            Returns:
                Execution result with status, output, and timing
            """
            try:
                self.logger.info(f"Received asset execution request from ai-pipeline: {request.get('execution_id')}")
                
                execution_id = request.get("execution_id")
                plan = request.get("plan", {})
                steps = plan.get("steps", [])
                
                # DEBUG: Log the full plan to see what we're receiving
                self.logger.info(f"🔥 PLAN RECEIVED: {plan}")
                self.logger.info(f"📋 STEPS COUNT: {len(steps)}")
                for idx, step in enumerate(steps):
                    self.logger.info(f"  Step {idx}: tool={step.get('tool')}, inputs={step.get('inputs')}")
                
                if not steps:
                    return {
                        "execution_id": execution_id,
                        "status": "failed",
                        "result": {},
                        "step_results": [],
                        "completed_at": datetime.utcnow().isoformat(),
                        "error_message": "No steps in plan"
                    }
                
                # Execute each asset step
                step_results = []
                overall_success = True
                
                for idx, step in enumerate(steps):
                    tool = step.get("tool", "unknown")
                    inputs = step.get("inputs", {})
                    
                    self.logger.info(f"Executing asset step {idx + 1}/{len(steps)}: {tool}")
                    
                    try:
                        # Route to appropriate asset handler
                        if tool in ["asset-query", "asset_query"]:
                            result = await self._execute_asset_query_tool(inputs)
                        elif tool in ["asset-create", "asset_create"]:
                            result = await self._execute_asset_create_tool(inputs)
                        elif tool in ["asset-update", "asset_update"]:
                            result = await self._execute_asset_update_tool(inputs)
                        elif tool in ["asset-delete", "asset_delete"]:
                            result = await self._execute_asset_delete_tool(inputs)
                        elif tool in ["asset-list", "asset_list"]:
                            result = await self._execute_asset_list_tool(inputs)
                        else:
                            result = {
                                "success": False,
                                "message": f"Unknown asset tool: {tool}"
                            }
                        
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "completed" if result.get("success") else "failed",
                            "output": result,
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        
                        if not result.get("success"):
                            overall_success = False
                    
                    except Exception as e:
                        self.logger.error(f"Asset step {idx + 1} failed: {e}", exc_info=True)
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "failed",
                            "error": str(e),
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        overall_success = False
                
                # Return result to ai-pipeline
                return {
                    "execution_id": execution_id,
                    "status": "completed" if overall_success else "failed",
                    "result": {
                        "total_steps": len(steps),
                        "successful_steps": sum(1 for r in step_results if r.get("status") == "completed"),
                        "failed_steps": sum(1 for r in step_results if r.get("status") == "failed")
                    },
                    "step_results": step_results,
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": None if overall_success else "One or more asset steps failed"
                }
            
            except Exception as e:
                self.logger.error(f"Asset plan execution failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _execute_asset_query_tool(self, inputs: dict) -> dict:
        """Execute asset query - Search/filter assets from inventory"""
        try:
            # Handle both direct filters and nested filters format
            # Support: {"tags": ["win10"]} and {"filters": {"tags": ["win10"]}}
            if "filters" in inputs and isinstance(inputs["filters"], dict):
                # Nested format - extract filters
                filters = inputs["filters"]
            else:
                # Direct format - use inputs as filters
                filters = inputs
            
            # Extract query parameters
            asset_id = filters.get("asset_id") or filters.get("id")
            hostname = filters.get("hostname")
            os_type = filters.get("os_type")
            status = filters.get("status")
            environment = filters.get("environment")
            tags = filters.get("tags")
            
            self.logger.info(f"Querying assets with filters: {filters}")
            
            # If specific asset ID provided, get that asset
            if asset_id:
                try:
                    asset_id_int = int(asset_id)
                    async with self.db.pool.acquire() as conn:
                        query = "SELECT * FROM assets.assets WHERE id = $1"
                        result = await conn.fetchrow(query, asset_id_int)
                        
                        if result:
                            asset_dict = dict(result)
                            # Parse tags if they're JSON
                            if asset_dict.get('tags'):
                                if isinstance(asset_dict['tags'], str):
                                    asset_dict['tags'] = json.loads(asset_dict['tags'])
                            
                            return {
                                "success": True,
                                "message": f"Found asset with ID {asset_id}",
                                "assets": [asset_dict],
                                "count": 1
                            }
                        else:
                            return {
                                "success": False,
                                "message": f"Asset with ID {asset_id} not found",
                                "assets": [],
                                "count": 0
                            }
                except ValueError:
                    return {
                        "success": False,
                        "message": f"Invalid asset ID: {asset_id}",
                        "error": "Asset ID must be an integer",
                        "assets": [],
                        "count": 0
                    }
            
            # Build dynamic query based on filters
            where_conditions = []
            params = []
            param_count = 0
            
            if hostname:
                param_count += 1
                where_conditions.append(f"hostname ILIKE ${param_count}")
                params.append(f"%{hostname}%")
            
            if os_type:
                param_count += 1
                where_conditions.append(f"os_type = ${param_count}")
                params.append(os_type)
            
            if status:
                param_count += 1
                where_conditions.append(f"status = ${param_count}")
                params.append(status)
            
            if environment:
                param_count += 1
                where_conditions.append(f"environment = ${param_count}")
                params.append(environment)
            
            if tags:
                # Tags stored as JSONB array, search for specific tag
                # Support both string tag and list of tags
                if isinstance(tags, str):
                    # Single tag - check if it exists in the array
                    param_count += 1
                    where_conditions.append(f"tags @> ${param_count}::jsonb")
                    params.append(json.dumps([tags]))
                elif isinstance(tags, list):
                    # Multiple tags - check if all exist
                    param_count += 1
                    where_conditions.append(f"tags @> ${param_count}::jsonb")
                    params.append(json.dumps(tags))
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f"""
                SELECT id, name, hostname, ip_address, description, tags,
                       os_type, os_version, service_type, port, is_secure,
                       credential_type, username, domain,
                       status, environment, criticality, owner,
                       created_at, updated_at
                FROM assets.assets
                {where_clause}
                ORDER BY id
                LIMIT 100
            """
            
            # Execute query
            async with self.db.pool.acquire() as conn:
                assets_rows = await conn.fetch(query, *params)
                
                # Convert to list of dicts and parse JSON fields
                assets = []
                for row in assets_rows:
                    asset_dict = dict(row)
                    # Parse tags if they're JSON strings
                    if asset_dict.get('tags'):
                        if isinstance(asset_dict['tags'], str):
                            asset_dict['tags'] = json.loads(asset_dict['tags'])
                    # Convert datetime to ISO format
                    if asset_dict.get('created_at'):
                        asset_dict['created_at'] = asset_dict['created_at'].isoformat()
                    if asset_dict.get('updated_at'):
                        asset_dict['updated_at'] = asset_dict['updated_at'].isoformat()
                    assets.append(asset_dict)
                
                self.logger.info(f"Found {len(assets)} assets matching filters")
                
                return {
                    "success": True,
                    "message": f"Found {len(assets)} asset(s)",
                    "assets": assets,
                    "count": len(assets),
                    "filters": inputs
                }
        
        except Exception as e:
            self.logger.error(f"Error querying assets: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error querying assets: {str(e)}",
                "error": str(e),
                "assets": [],
                "count": 0
            }
    
    async def _execute_asset_create_tool(self, inputs: dict) -> dict:
        """Execute asset creation - Add new asset to inventory"""
        try:
            # Extract required fields
            hostname = inputs.get("hostname")
            ip_address = inputs.get("ip_address") or inputs.get("ip")
            asset_type = inputs.get("type") or inputs.get("asset_type", "server")
            
            # Validate required fields
            if not hostname:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'hostname'",
                    "error": "Hostname is required"
                }
            
            # Extract optional fields
            status = inputs.get("status", "active")
            environment = inputs.get("environment", "production")
            location = inputs.get("location")
            owner = inputs.get("owner")
            tags = inputs.get("tags", {})
            metadata = inputs.get("metadata", {})
            
            self.logger.info(f"Creating asset: {hostname}")
            
            # Insert asset into database
            query = """
                INSERT INTO assets (
                    hostname, ip_address, type, status, environment,
                    location, owner, tags, metadata, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id, hostname, ip_address, type, status
            """
            
            params = (
                hostname,
                ip_address,
                asset_type,
                status,
                environment,
                location,
                owner,
                json.dumps(tags) if isinstance(tags, dict) else tags,
                json.dumps(metadata) if isinstance(metadata, dict) else metadata
            )
            
            result = self.db.execute_query(query, params)
            
            if result:
                asset = result[0]
                self.logger.info(f"Asset created successfully: ID {asset.get('id')}")
                return {
                    "success": True,
                    "message": f"Asset '{hostname}' created successfully",
                    "asset": asset,
                    "asset_id": asset.get("id")
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to create asset",
                    "error": "No result returned from database"
                }
        
        except Exception as e:
            self.logger.error(f"Error creating asset: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error creating asset: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_asset_update_tool(self, inputs: dict) -> dict:
        """Execute asset update - Modify existing asset"""
        try:
            # Extract asset identifier
            asset_id = inputs.get("asset_id") or inputs.get("id")
            hostname = inputs.get("hostname")
            
            # Validate identifier
            if not asset_id and not hostname:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'asset_id' or 'hostname'",
                    "error": "Asset identifier required"
                }
            
            # Find asset by ID or hostname
            if asset_id:
                find_query = "SELECT id FROM assets WHERE id = %s"
                find_params = (int(asset_id),)
            else:
                find_query = "SELECT id FROM assets WHERE hostname = %s"
                find_params = (hostname,)
            
            asset_result = self.db.execute_query(find_query, find_params)
            
            if not asset_result:
                return {
                    "success": False,
                    "message": f"Asset not found: {asset_id or hostname}",
                    "error": "Asset not found"
                }
            
            found_id = asset_result[0]["id"]
            
            # Build update query dynamically based on provided fields
            update_fields = []
            update_params = []
            
            updatable_fields = {
                "hostname": "hostname",
                "ip_address": "ip_address",
                "ip": "ip_address",
                "type": "type",
                "asset_type": "type",
                "status": "status",
                "environment": "environment",
                "location": "location",
                "owner": "owner"
            }
            
            for input_key, db_field in updatable_fields.items():
                if input_key in inputs and inputs[input_key] is not None:
                    update_fields.append(f"{db_field} = %s")
                    update_params.append(inputs[input_key])
            
            # Handle tags and metadata (JSONB fields)
            if "tags" in inputs:
                update_fields.append("tags = %s")
                update_params.append(json.dumps(inputs["tags"]) if isinstance(inputs["tags"], dict) else inputs["tags"])
            
            if "metadata" in inputs:
                update_fields.append("metadata = %s")
                update_params.append(json.dumps(inputs["metadata"]) if isinstance(inputs["metadata"], dict) else inputs["metadata"])
            
            if not update_fields:
                return {
                    "success": False,
                    "message": "No fields to update",
                    "error": "No update fields provided"
                }
            
            # Add updated_at timestamp
            update_fields.append("updated_at = NOW()")
            
            # Build and execute update query
            update_query = f"""
                UPDATE assets
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, hostname, ip_address, type, status, updated_at
            """
            update_params.append(found_id)
            
            self.logger.info(f"Updating asset ID {found_id}")
            result = self.db.execute_query(update_query, tuple(update_params))
            
            if result:
                asset = result[0]
                return {
                    "success": True,
                    "message": f"Asset updated successfully",
                    "asset": asset,
                    "asset_id": found_id
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update asset",
                    "error": "No result returned from database"
                }
        
        except Exception as e:
            self.logger.error(f"Error updating asset: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error updating asset: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_asset_delete_tool(self, inputs: dict) -> dict:
        """Execute asset deletion - Remove asset from inventory"""
        try:
            # Extract asset identifier
            asset_id = inputs.get("asset_id") or inputs.get("id")
            hostname = inputs.get("hostname")
            
            # Validate identifier
            if not asset_id and not hostname:
                return {
                    "success": False,
                    "message": "Missing required parameter: 'asset_id' or 'hostname'",
                    "error": "Asset identifier required"
                }
            
            # Find and delete asset
            if asset_id:
                query = "DELETE FROM assets WHERE id = %s RETURNING id, hostname"
                params = (int(asset_id),)
            else:
                query = "DELETE FROM assets WHERE hostname = %s RETURNING id, hostname"
                params = (hostname,)
            
            self.logger.info(f"Deleting asset: {asset_id or hostname}")
            result = self.db.execute_query(query, params)
            
            if result:
                deleted_asset = result[0]
                return {
                    "success": True,
                    "message": f"Asset '{deleted_asset.get('hostname')}' deleted successfully",
                    "deleted_asset_id": deleted_asset.get("id"),
                    "deleted_hostname": deleted_asset.get("hostname")
                }
            else:
                return {
                    "success": False,
                    "message": f"Asset not found: {asset_id or hostname}",
                    "error": "Asset not found"
                }
        
        except Exception as e:
            self.logger.error(f"Error deleting asset: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error deleting asset: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_asset_list_tool(self, inputs: dict) -> dict:
        """Execute asset listing - List all assets with optional filters"""
        try:
            # Extract pagination parameters
            limit = inputs.get("limit", 100)
            offset = inputs.get("offset", 0)
            
            # Extract filter parameters
            asset_type = inputs.get("type") or inputs.get("asset_type")
            status = inputs.get("status")
            environment = inputs.get("environment")
            
            self.logger.info(f"Listing assets with limit={limit}, offset={offset}")
            
            # Build query with filters
            query = "SELECT * FROM assets WHERE 1=1"
            params = []
            
            if asset_type:
                query += " AND type = %s"
                params.append(asset_type)
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            if environment:
                query += " AND environment = %s"
                params.append(environment)
            
            query += " ORDER BY id LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # Execute query
            assets = self.db.execute_query(query, tuple(params))
            
            # Get total count
            count_query = "SELECT COUNT(*) as total FROM assets WHERE 1=1"
            count_params = []
            
            if asset_type:
                count_query += " AND type = %s"
                count_params.append(asset_type)
            
            if status:
                count_query += " AND status = %s"
                count_params.append(status)
            
            if environment:
                count_query += " AND environment = %s"
                count_params.append(environment)
            
            count_result = self.db.execute_query(count_query, tuple(count_params) if count_params else None)
            total_count = count_result[0]["total"] if count_result else 0
            
            return {
                "success": True,
                "message": f"Retrieved {len(assets)} asset(s)",
                "assets": assets,
                "count": len(assets),
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        
        except Exception as e:
            self.logger.error(f"Error listing assets: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error listing assets: {str(e)}",
                "error": str(e)
            }


if __name__ == "__main__":
    service = ConsolidatedAssetService()
    service.run()
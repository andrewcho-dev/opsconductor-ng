#!/usr/bin/env python3
"""
Enhanced Pydantic models for multi-service target architecture
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Service Definition Models
class ServiceDefinition(BaseModel):
    id: int
    service_type: str
    display_name: str
    category: str
    default_port: int
    is_secure_by_default: bool
    description: Optional[str] = None
    is_common: bool = False
    created_at: datetime

class ServiceDefinitionResponse(BaseModel):
    services: List[ServiceDefinition]
    total: int

# Target Service Models
class TargetServiceCreate(BaseModel):
    service_type: str
    port: int
    is_secure: bool = False
    is_enabled: bool = True
    notes: Optional[str] = None

class TargetServiceUpdate(BaseModel):
    port: Optional[int] = None
    is_secure: Optional[bool] = None
    is_enabled: Optional[bool] = None
    notes: Optional[str] = None

class TargetService(BaseModel):
    id: int
    service_type: str
    display_name: str
    category: str
    port: int
    default_port: int
    is_secure: bool
    is_enabled: bool
    is_custom_port: bool
    discovery_method: str = "manual"
    connection_status: str = "unknown"
    last_checked: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

# Target Credential Models
class TargetCredentialCreate(BaseModel):
    credential_id: int
    service_types: List[str] = []
    is_primary: bool = False

class TargetCredential(BaseModel):
    id: int
    credential_id: int
    credential_name: str
    credential_type: str
    service_types: List[str]
    is_primary: bool
    created_at: datetime

# Enhanced Target Models
class TargetCreate(BaseModel):
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = Field(None, pattern="^(windows|linux|unix|macos|other)$")
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    services: List[TargetServiceCreate] = []
    credentials: List[TargetCredentialCreate] = []

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    os_type: Optional[str] = Field(None, pattern="^(windows|linux|unix|macos|other)$")
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class Target(BaseModel):
    id: int
    name: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    services: List[TargetService] = []
    credentials: List[TargetCredential] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

class TargetListResponse(BaseModel):
    targets: List[Target]
    total: int

# Legacy compatibility models
class LegacyTargetCreate(BaseModel):
    name: str
    hostname: str
    port: int
    protocol: str
    credential_ref: str
    os_type: Optional[str] = None
    tags: Optional[List[str]] = []

class LegacyTarget(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    protocol: str
    credential_ref: str
    os_type: Optional[str] = None
    tags: List[str] = []
    created_at: str

class LegacyTargetListResponse(BaseModel):
    targets: List[LegacyTarget]
    total: int

# Bulk operations
class BulkServiceOperation(BaseModel):
    target_id: int
    service_types: List[str]
    operation: str = Field(..., pattern="^(enable|disable)$")

class BulkServiceResponse(BaseModel):
    success: bool
    updated_services: int
    message: str

# Service management
class ServiceBulkUpdate(BaseModel):
    services: List[Dict[str, Any]]  # Array of service updates

# Migration models
class MigrationStatus(BaseModel):
    success: bool
    services_created: int
    credentials_created: int
    message: str
#!/usr/bin/env python3
"""
OpsConductor Asset Service
Handles targets, credentials, and discovery
Consolidates: target-service + credential-service + discovery-service
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

class Credential(BaseModel):
    id: int
    name: str
    credential_type: str
    username: Optional[str] = None
    description: Optional[str] = None
    metadata: dict = {}
    is_active: bool
    created_by: int
    created_at: str
    updated_at: str

class CredentialCreate(BaseModel):
    name: str
    credential_type: str
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    description: Optional[str] = None
    metadata: dict = {}
    is_active: bool = True

class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    credential_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None

class CredentialListResponse(BaseModel):
    credentials: List[Credential]
    total: int
    skip: int
    limit: int

class DiscoveryJob(BaseModel):
    id: int
    name: str
    network_range: str
    scan_type: str
    status: str
    progress: int
    targets_found: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    created_by: int
    created_at: str

class DiscoveryCreate(BaseModel):
    name: str
    network_range: str
    scan_type: str = "ping"

class DiscoveryUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    targets_found: Optional[int] = None
    error_message: Optional[str] = None

class DiscoveryListResponse(BaseModel):
    discovery_jobs: List[DiscoveryJob]
    total: int
    skip: int
    limit: int

class AssetService(BaseService):
    def __init__(self):
        super().__init__("asset-service", "1.0.0", 3002)
        self._setup_routes()

    def _setup_routes(self):
        """Setup all API routes"""
        
        # ============================================================================
        # TARGET CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.get("/targets", response_model=TargetListResponse)
        async def list_targets(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all targets"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM assets.targets")
                    
                    # Get targets with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, host, port, target_type, tags, 
                               metadata, is_active, created_by, created_at, updated_at
                        FROM assets.targets 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    targets = []
                    for row in rows:
                        import json
                        targets.append(Target(
                            id=row['id'],
                            name=row['name'],
                            host=row['host'],
                            port=row['port'],
                            platform=row['target_type'],
                            credential_id=None,
                            group_id=None,
                            tags=json.loads(row['tags']) if row['tags'] else [],
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
                            is_active=row['is_active'],
                            last_seen=None,
                            created_by=row['created_by'],
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return TargetListResponse(
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
        async def create_target(target_data: TargetCreate):
            """Create a new target"""
            try:
                async with self.db.pool.acquire() as conn:
                    import json
                    row = await conn.fetchrow("""
                        INSERT INTO assets.targets (name, host, port, target_type, connection_type, 
                                           tags, metadata, is_active, created_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 1)
                        RETURNING id, name, host, port, target_type, connection_type, tags,
                                  metadata, is_active, created_by, created_at, updated_at
                    """, target_data.name, target_data.host, target_data.port or 22, 
                         target_data.platform or 'linux', 'ssh',
                         json.dumps(target_data.tags or []), json.dumps(target_data.metadata or {}), target_data.is_active)
                    
                    import json
                    target = Target(
                        id=row['id'],
                        name=row['name'],
                        host=row['host'],
                        port=row['port'],
                        platform=row['target_type'],
                        credential_id=None,
                        group_id=None,
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        last_seen=None,
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
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
            """Get target by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, name, host, port, target_type, tags,
                               metadata, is_active, created_by, created_at, updated_at
                        FROM assets.targets WHERE id = $1
                    """, target_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    import json
                    target = Target(
                        id=row['id'],
                        name=row['name'],
                        host=row['host'],
                        port=row['port'],
                        platform=row['target_type'],
                        credential_id=None,
                        group_id=None,
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        last_seen=None,
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
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
        async def update_target(target_id: int, target_data: TargetUpdate):
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
                    if target_data.host is not None:
                        updates.append(f"host = ${param_count}")
                        values.append(target_data.host)
                        param_count += 1
                    if target_data.port is not None:
                        updates.append(f"port = ${param_count}")
                        values.append(target_data.port)
                        param_count += 1
                    if target_data.platform is not None:
                        updates.append(f"target_type = ${param_count}")
                        values.append(target_data.platform)
                        param_count += 1
                    if target_data.credential_id is not None:
                        updates.append(f"credential_id = ${param_count}")
                        values.append(target_data.credential_id)
                        param_count += 1
                    if target_data.group_id is not None:
                        updates.append(f"group_id = ${param_count}")
                        values.append(target_data.group_id)
                        param_count += 1
                    if target_data.tags is not None:
                        import json
                        updates.append(f"tags = ${param_count}")
                        values.append(json.dumps(target_data.tags))
                        param_count += 1
                    if target_data.metadata is not None:
                        import json
                        updates.append(f"metadata = ${param_count}")
                        values.append(json.dumps(target_data.metadata))
                        param_count += 1
                    if target_data.is_active is not None:
                        updates.append(f"is_active = ${param_count}")
                        values.append(target_data.is_active)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(target_id)
                    
                    query = f"""
                        UPDATE assets.targets 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, host, port, target_type, tags,
                                  metadata, is_active, created_by, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Target not found")
                    
                    import json
                    target = Target(
                        id=row['id'],
                        name=row['name'],
                        host=row['host'],
                        port=row['port'],
                        platform=row['target_type'],
                        credential_id=None,
                        group_id=None,
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        last_seen=None,
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Target updated", "data": target}
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

        # ============================================================================
        # CREDENTIAL CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.get("/credentials", response_model=CredentialListResponse)
        async def list_credentials(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all credentials"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM assets.credentials")
                    
                    # Get credentials with pagination (excluding sensitive data)
                    rows = await conn.fetch("""
                        SELECT id, name, credential_type, description, metadata, 
                               is_active, created_by, created_at, updated_at
                        FROM assets.credentials 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    credentials = []
                    for row in rows:
                        import json
                        credentials.append(Credential(
                            id=row['id'],
                            name=row['name'],
                            credential_type=row['credential_type'],
                            username=None,
                            description=row['description'],
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
                            is_active=row['is_active'],
                            created_by=row['created_by'],
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return CredentialListResponse(
                        credentials=credentials,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch credentials", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch credentials"
                )

        @self.app.post("/credentials", response_model=dict)
        async def create_credential(credential_data: CredentialCreate):
            """Create a new credential"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Encrypt sensitive data (simplified for demo)
                    encrypted_password = f"encrypted_{credential_data.password}" if credential_data.password else None
                    encrypted_key = f"encrypted_{credential_data.private_key}" if credential_data.private_key else None
                    
                    import json
                    # Create encrypted data structure
                    encrypted_data = {
                        "password": encrypted_password,
                        "private_key": encrypted_key,
                        "username": getattr(credential_data, 'username', None)
                    }
                    
                    row = await conn.fetchrow("""
                        INSERT INTO assets.credentials (name, credential_type, encrypted_data, 
                                               description, metadata, is_active, created_by)
                        VALUES ($1, $2, $3, $4, $5, $6, 1)
                        RETURNING id, name, credential_type, description, metadata,
                                  is_active, created_by, created_at, updated_at
                    """, credential_data.name, credential_data.credential_type, json.dumps(encrypted_data),
                         credential_data.description, json.dumps(credential_data.metadata or {}), credential_data.is_active)
                    
                    credential = Credential(
                        id=row['id'],
                        name=row['name'],
                        credential_type=row['credential_type'],
                        username=getattr(credential_data, 'username', None),
                        description=row['description'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Credential created", "data": credential}
            except Exception as e:
                self.logger.error("Failed to create credential", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create credential"
                )

        @self.app.get("/credentials/{credential_id}", response_model=dict)
        async def get_credential(credential_id: int):
            """Get credential by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, name, credential_type, encrypted_data, description, metadata,
                               is_active, created_by, created_at, updated_at
                        FROM assets.credentials WHERE id = $1
                    """, credential_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Credential not found")
                    
                    import json
                    # Extract username from encrypted_data if available
                    try:
                        encrypted_data = json.loads(row['encrypted_data']) if row['encrypted_data'] else {}
                    except (json.JSONDecodeError, TypeError):
                        encrypted_data = {}
                    username = encrypted_data.get('username')
                    
                    credential = Credential(
                        id=row['id'],
                        name=row['name'],
                        credential_type=row['credential_type'],
                        username=username,
                        description=row['description'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": credential}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get credential", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get credential"
                )

        @self.app.put("/credentials/{credential_id}", response_model=dict)
        async def update_credential(credential_id: int, credential_data: CredentialUpdate):
            """Update credential"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if credential_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(credential_data.name)
                        param_count += 1
                    if credential_data.credential_type is not None:
                        updates.append(f"credential_type = ${param_count}")
                        values.append(credential_data.credential_type)
                        param_count += 1
                    # Handle encrypted_data field
                    encrypted_data = {}
                    if credential_data.username is not None:
                        encrypted_data['username'] = credential_data.username
                    if credential_data.password is not None:
                        encrypted_data['password'] = f"encrypted_{credential_data.password}"
                    if credential_data.private_key is not None:
                        encrypted_data['private_key'] = f"encrypted_{credential_data.private_key}"
                    
                    if encrypted_data:
                        import json
                        updates.append(f"encrypted_data = ${param_count}")
                        values.append(json.dumps(encrypted_data))
                        param_count += 1
                    if credential_data.description is not None:
                        updates.append(f"description = ${param_count}")
                        values.append(credential_data.description)
                        param_count += 1
                    if credential_data.metadata is not None:
                        import json
                        updates.append(f"metadata = ${param_count}")
                        values.append(json.dumps(credential_data.metadata))
                        param_count += 1
                    if credential_data.is_active is not None:
                        updates.append(f"is_active = ${param_count}")
                        values.append(credential_data.is_active)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(credential_id)
                    
                    query = f"""
                        UPDATE assets.credentials 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, credential_type, encrypted_data, description, metadata,
                                  is_active, created_by, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Credential not found")
                    
                    import json
                    # Extract username from encrypted_data if available
                    try:
                        encrypted_data = json.loads(row['encrypted_data']) if row['encrypted_data'] else {}
                    except (json.JSONDecodeError, TypeError):
                        encrypted_data = {}
                    username = encrypted_data.get('username')
                    
                    credential = Credential(
                        id=row['id'],
                        name=row['name'],
                        credential_type=row['credential_type'],
                        username=username,
                        description=row['description'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        is_active=row['is_active'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Credential updated", "data": credential}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update credential", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update credential"
                )

        @self.app.delete("/credentials/{credential_id}", response_model=dict)
        async def delete_credential(credential_id: int):
            """Delete credential"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM assets.credentials WHERE id = $1", credential_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Credential not found")
                    
                    return {"success": True, "message": "Credential deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete credential", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete credential"
                )

        # ============================================================================
        # DISCOVERY CRUD ENDPOINTS
        # ============================================================================
        
        @self.app.get("/discovery", response_model=DiscoveryListResponse)
        async def list_discovery_jobs(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all discovery jobs"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM discovery_jobs")
                    
                    # Get discovery jobs with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, network_range, scan_type, status, progress, targets_found,
                               started_at, completed_at, error_message, created_by, created_at
                        FROM discovery_jobs 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    discovery_jobs = []
                    for row in rows:
                        discovery_jobs.append(DiscoveryJob(
                            id=row['id'],
                            name=row['name'],
                            network_range=row['network_range'],
                            scan_type=row['scan_type'],
                            status=row['status'],
                            progress=row['progress'],
                            targets_found=row['targets_found'],
                            started_at=row['started_at'].isoformat() if row['started_at'] else None,
                            completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                            error_message=row['error_message'],
                            created_by=row['created_by'],
                            created_at=row['created_at'].isoformat()
                        ))
                    
                    return DiscoveryListResponse(
                        discovery_jobs=discovery_jobs,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch discovery jobs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch discovery jobs"
                )

        @self.app.post("/discovery", response_model=dict)
        async def create_discovery_job(discovery_data: DiscoveryCreate):
            """Create a new discovery job"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        INSERT INTO discovery_jobs (name, network_range, scan_type, status, progress, 
                                                  targets_found, created_by)
                        VALUES ($1, $2, $3, 'pending', 0, 0, 1)
                        RETURNING id, name, network_range, scan_type, status, progress, targets_found,
                                  started_at, completed_at, error_message, created_by, created_at
                    """, discovery_data.name, discovery_data.network_range, discovery_data.scan_type)
                    
                    discovery_job = DiscoveryJob(
                        id=row['id'],
                        name=row['name'],
                        network_range=row['network_range'],
                        scan_type=row['scan_type'],
                        status=row['status'],
                        progress=row['progress'],
                        targets_found=row['targets_found'],
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        error_message=row['error_message'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Discovery job created", "data": discovery_job}
            except Exception as e:
                self.logger.error("Failed to create discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create discovery job"
                )

        @self.app.get("/discovery/{discovery_id}", response_model=dict)
        async def get_discovery_job(discovery_id: int):
            """Get discovery job by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, name, network_range, scan_type, status, progress, targets_found,
                               started_at, completed_at, error_message, created_by, created_at
                        FROM discovery_jobs WHERE id = $1
                    """, discovery_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    
                    discovery_job = DiscoveryJob(
                        id=row['id'],
                        name=row['name'],
                        network_range=row['network_range'],
                        scan_type=row['scan_type'],
                        status=row['status'],
                        progress=row['progress'],
                        targets_found=row['targets_found'],
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        error_message=row['error_message'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat()
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

        @self.app.put("/discovery/{discovery_id}", response_model=dict)
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
                    
                    if discovery_data.progress is not None:
                        updates.append(f"progress = ${param_count}")
                        values.append(discovery_data.progress)
                        param_count += 1
                    
                    if discovery_data.targets_found is not None:
                        updates.append(f"targets_found = ${param_count}")
                        values.append(discovery_data.targets_found)
                        param_count += 1
                    
                    if discovery_data.error_message is not None:
                        updates.append(f"error_message = ${param_count}")
                        values.append(discovery_data.error_message)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    values.append(discovery_id)
                    
                    query = f"""
                        UPDATE discovery_jobs 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, network_range, scan_type, status, progress, targets_found,
                                  started_at, completed_at, error_message, created_by, created_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    
                    discovery_job = DiscoveryJob(
                        id=row['id'],
                        name=row['name'],
                        network_range=row['network_range'],
                        scan_type=row['scan_type'],
                        status=row['status'],
                        progress=row['progress'],
                        targets_found=row['targets_found'],
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        error_message=row['error_message'],
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

        @self.app.delete("/discovery/{discovery_id}", response_model=dict)
        async def delete_discovery_job(discovery_id: int):
            """Delete discovery job"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM discovery_jobs WHERE id = $1", discovery_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Discovery job not found")
                    
                    return {"success": True, "message": "Discovery job deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete discovery job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete discovery job"
                )

if __name__ == "__main__":
    service = AssetService()
    service.run()
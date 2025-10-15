#!/usr/bin/env python3
"""
Asset Routes - Public API for asset queries and connection profiles
Exposed via Kong gateway at /assets/*
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetCountResponse(BaseModel):
    """Response for asset count queries"""
    count: int
    filters: dict


class AssetSearchResponse(BaseModel):
    """Response for asset search queries"""
    items: list
    count: int
    limit: int


class ConnectionProfileResponse(BaseModel):
    """Response for connection profile queries"""
    found: bool
    asset_id: Optional[str] = None
    host: Optional[str] = None
    ip: Optional[str] = None
    hostname: Optional[str] = None
    hostnames: Optional[list] = None
    os: Optional[str] = None
    os_type: Optional[str] = None
    winrm: Optional[dict] = None
    ssh: Optional[dict] = None
    rdp: Optional[dict] = None
    primary_service: Optional[dict] = None
    error: Optional[str] = None
    candidates: Optional[list] = None


# Dependency to get asset façade from app state
def get_asset_facade(request):
    """Get asset façade from app state"""
    return request.app.state.asset_facade


@router.get("/count", response_model=AssetCountResponse)
async def count_assets(
    request: Request,
    os: Optional[str] = Query(None, description="OS type or version filter (e.g., 'Windows 10', 'linux')"),
    hostname: Optional[str] = Query(None, description="Hostname filter (partial match)"),
    ip: Optional[str] = Query(None, description="IP address filter (exact match)"),
    status: Optional[str] = Query(None, description="Status filter (e.g., 'active')"),
    environment: Optional[str] = Query(None, description="Environment filter (e.g., 'production')")
):
    """
    Count assets matching filters
    
    Fast endpoint for answering questions like:
    - "How many Windows 10 assets do we have?"
    - "How many active production servers?"
    
    Performance target: <100ms p50
    """
    try:
        facade = request.app.state.asset_facade
        result = await facade.count_assets(
            os=os,
            hostname=hostname,
            ip=ip,
            status=status,
            environment=environment
        )
        return result
    except Exception as e:
        logger.error(f"Failed to count assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to count assets: {str(e)}")


@router.get("/search", response_model=AssetSearchResponse)
async def search_assets(
    request: Request,
    os: Optional[str] = Query(None, description="OS type or version filter"),
    hostname: Optional[str] = Query(None, description="Hostname filter (partial match)"),
    ip: Optional[str] = Query(None, description="IP address filter (exact match)"),
    status: Optional[str] = Query(None, description="Status filter"),
    environment: Optional[str] = Query(None, description="Environment filter"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results")
):
    """
    Search assets matching filters
    
    Returns detailed asset information for queries like:
    - "List all Windows 10 machines"
    - "Show me production Linux servers"
    
    Performance target: <100ms p50
    """
    try:
        facade = request.app.state.asset_facade
        result = await facade.search_assets(
            os=os,
            hostname=hostname,
            ip=ip,
            status=status,
            environment=environment,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Failed to search assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search assets: {str(e)}")


@router.get("/connection-profile", response_model=ConnectionProfileResponse)
async def get_connection_profile(
    request: Request,
    host: str = Query(..., description="Hostname, IP address, or short hostname"),
    asset_id: Optional[str] = Query(None, description="Optional asset UUID for disambiguation")
):
    """
    Get connection profile for a host
    
    Resolves host by IP, FQDN, or short hostname and returns connection parameters
    with credential references (not plaintext secrets):
    - WinRM port, SSL, domain, credential_ref for Windows hosts
    - SSH port, credential_ref for Linux/Unix hosts
    - Primary service information
    
    Used by tools to auto-configure connection parameters.
    
    Returns 200 with found=false if host not in asset database.
    Returns ambiguous_asset error if multiple matches found.
    
    Performance target: <50ms p50
    """
    try:
        facade = request.app.state.asset_facade
        result = await facade.get_connection_profile(host, asset_id=asset_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get connection profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection profile: {str(e)}")
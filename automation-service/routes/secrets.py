#!/usr/bin/env python3
"""
Secrets Routes - INTERNAL API for credential management
NOT exposed via Kong - requires X-Internal-Key header
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/secrets", tags=["secrets-internal"])

# Internal key for service-to-service authentication
INTERNAL_KEY = os.getenv("INTERNAL_KEY", "")


def verify_internal_key(x_internal_key: Optional[str] = Header(None)):
    """Verify internal key for service-to-service calls"""
    if not INTERNAL_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal key not configured (INTERNAL_KEY env var required)"
        )
    
    if not x_internal_key or x_internal_key != INTERNAL_KEY:
        logger.warning("Unauthorized internal API access attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Internal-Key header"
        )


class CredentialUpsertRequest(BaseModel):
    """Request to create or update a credential"""
    host: str
    purpose: str  # 'winrm', 'ssh', 'rdp', etc.
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class CredentialLookupRequest(BaseModel):
    """Request to lookup a credential"""
    host: str
    purpose: str  # 'winrm', 'ssh', 'rdp', etc.


class CredentialResponse(BaseModel):
    """Response with credential data"""
    host: str
    purpose: str
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class CredentialUpsertResponse(BaseModel):
    """Response for credential upsert"""
    success: bool
    credential_id: int
    host: str
    purpose: str


class CredentialNotFoundResponse(BaseModel):
    """Response when credential not found"""
    reason: str


@router.post("/credential-upsert", response_model=CredentialUpsertResponse)
async def credential_upsert(
    request_data: CredentialUpsertRequest,
    x_internal_key: Optional[str] = Header(None),
    request = None
):
    """
    Create or update a credential (INTERNAL USE ONLY)
    
    Requires X-Internal-Key header matching INTERNAL_KEY env var.
    
    Encrypts password using AES-256-GCM before storage.
    Logs all access to audit table.
    """
    verify_internal_key(x_internal_key)
    
    try:
        secrets_manager = request.app.state.secrets_manager
        
        result = secrets_manager.upsert_credential(
            host=request_data.host,
            purpose=request_data.purpose,
            username=request_data.username,
            password=request_data.password,
            domain=request_data.domain,
            additional_data=request_data.additional_data,
            created_by="automation-service"
        )
        
        logger.info(f"Credential upserted for host={request_data.host}, purpose={request_data.purpose}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to upsert credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upsert credential: {str(e)}"
        )


@router.post("/credential-lookup", response_model=CredentialResponse, responses={404: {"model": CredentialNotFoundResponse}})
async def credential_lookup(
    request_data: CredentialLookupRequest,
    x_internal_key: Optional[str] = Header(None),
    request = None
):
    """
    Lookup and decrypt a credential (INTERNAL USE ONLY)
    
    Requires X-Internal-Key header matching INTERNAL_KEY env var.
    
    Returns decrypted credentials for server-side use.
    NEVER expose this endpoint via Kong gateway.
    
    Returns 404 if credential not found.
    """
    verify_internal_key(x_internal_key)
    
    try:
        secrets_manager = request.app.state.secrets_manager
        
        result = secrets_manager.lookup_credential(
            host=request_data.host,
            purpose=request_data.purpose,
            accessed_by="automation-service"
        )
        
        if not result:
            logger.warning(f"Credential not found for host={request_data.host}, purpose={request_data.purpose}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"reason": "not_found"}
            )
        
        # Mask password in logs
        logger.info(f"Credential retrieved for host={request_data.host}, purpose={request_data.purpose} (password masked)")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to lookup credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lookup credential: {str(e)}"
        )


@router.delete("/credential-delete")
async def credential_delete(
    host: str,
    purpose: str,
    x_internal_key: Optional[str] = Header(None),
    request = None
):
    """
    Delete a credential (INTERNAL USE ONLY)
    
    Requires X-Internal-Key header matching INTERNAL_KEY env var.
    """
    verify_internal_key(x_internal_key)
    
    try:
        secrets_manager = request.app.state.secrets_manager
        
        deleted = secrets_manager.delete_credential(
            host=host,
            purpose=purpose,
            deleted_by="automation-service"
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"reason": "not_found"}
            )
        
        logger.info(f"Credential deleted for host={host}, purpose={purpose}")
        
        return {"success": True, "host": host, "purpose": purpose}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete credential: {str(e)}"
        )
"""
Phase 7: Asset Service Client
HTTP client for interacting with the Asset Service
"""

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================================
# MODELS (matching Asset Service)
# ============================================================================

class AssetCredentials(BaseModel):
    """Asset credentials model"""
    credential_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    certificate: Optional[str] = None
    passphrase: Optional[str] = None
    domain: Optional[str] = None


class AssetDetail(BaseModel):
    """Asset detail model (matching Asset Service response)"""
    id: int
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
    password: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    certificate: Optional[str] = None
    passphrase: Optional[str] = None
    domain: Optional[str] = None
    
    # Database-specific fields
    database_type: Optional[str] = None
    database_name: Optional[str] = None
    
    # Secondary service
    secondary_service_type: str = "none"
    secondary_port: Optional[int] = None
    ftp_type: Optional[str] = None
    secondary_username: Optional[str] = None
    secondary_password: Optional[str] = None
    
    # Additional services
    additional_services: List[Dict[str, Any]] = []
    notes: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ============================================================================
# ASSET SERVICE CLIENT
# ============================================================================

class AssetServiceClient:
    """
    HTTP client for Asset Service
    
    Responsibilities:
    - Fetch asset details by ID or hostname
    - Query assets by filters
    - Retrieve asset credentials (decrypted)
    - Handle connection errors with retry logic
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize Asset Service Client
        
        Args:
            base_url: Base URL for Asset Service (default: from env)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url or os.getenv(
            "ASSET_SERVICE_URL",
            "http://asset-service:3001"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create HTTP client with retry logic
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True
        )
        
        logger.info(f"AssetServiceClient initialized: {self.base_url}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def get_asset_by_id(self, asset_id: int) -> Optional[AssetDetail]:
        """
        Get asset by ID
        
        Args:
            asset_id: Asset ID
        
        Returns:
            AssetDetail or None if not found
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        try:
            logger.info(f"Fetching asset by ID: {asset_id}")
            
            response = await self.client.get(f"/{asset_id}")
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                logger.warning(f"Asset not found: {asset_id}")
                return None
            
            asset_data = data.get("data", {})
            asset = AssetDetail(**asset_data)
            
            logger.info(
                f"Asset fetched: {asset_id}, "
                f"hostname={asset.hostname}, "
                f"service={asset.service_type}"
            )
            
            return asset
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Asset not found: {asset_id}")
                return None
            logger.error(f"HTTP error fetching asset {asset_id}: {e}")
            raise
        
        except httpx.HTTPError as e:
            logger.error(f"Connection error fetching asset {asset_id}: {e}")
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error fetching asset {asset_id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_asset_by_hostname(self, hostname: str) -> Optional[AssetDetail]:
        """
        Get asset by hostname
        
        Args:
            hostname: Asset hostname
        
        Returns:
            AssetDetail or None if not found
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        try:
            logger.info(f"Fetching asset by hostname: {hostname}")
            
            # Query assets with hostname filter
            response = await self.client.get("/", params={"hostname": hostname})
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                logger.warning(f"Asset not found: {hostname}")
                return None
            
            assets = data.get("data", [])
            
            if not assets:
                logger.warning(f"No assets found with hostname: {hostname}")
                return None
            
            # Return first matching asset
            asset_data = assets[0]
            asset = AssetDetail(**asset_data)
            
            logger.info(
                f"Asset fetched: hostname={hostname}, "
                f"id={asset.id}, "
                f"service={asset.service_type}"
            )
            
            return asset
        
        except httpx.HTTPError as e:
            logger.error(f"Connection error fetching asset {hostname}: {e}")
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error fetching asset {hostname}: {e}",
                exc_info=True
            )
            raise
    
    async def query_assets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AssetDetail]:
        """
        Query assets with filters
        
        Args:
            filters: Query filters (e.g., {"environment": "production"})
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of AssetDetail
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        try:
            logger.info(f"Querying assets: filters={filters}, limit={limit}")
            
            params = filters or {}
            params["limit"] = limit
            params["offset"] = offset
            
            response = await self.client.get("/", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                logger.warning("Asset query failed")
                return []
            
            assets_data = data.get("data", [])
            assets = [AssetDetail(**asset_data) for asset_data in assets_data]
            
            logger.info(f"Assets fetched: {len(assets)} results")
            
            return assets
        
        except httpx.HTTPError as e:
            logger.error(f"Connection error querying assets: {e}")
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying assets: {e}",
                exc_info=True
            )
            raise
    
    async def get_asset_credentials(
        self,
        asset_id: int
    ) -> Optional[AssetCredentials]:
        """
        Get asset credentials (decrypted)
        
        Args:
            asset_id: Asset ID
        
        Returns:
            AssetCredentials or None if not found
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        try:
            logger.info(f"Fetching credentials for asset: {asset_id}")
            
            asset = await self.get_asset_by_id(asset_id)
            
            if not asset:
                logger.warning(f"Asset not found: {asset_id}")
                return None
            
            # Extract credentials from asset
            credentials = AssetCredentials(
                credential_type=asset.credential_type,
                username=asset.username,
                password=asset.password,
                private_key=asset.private_key,
                public_key=asset.public_key,
                api_key=asset.api_key,
                bearer_token=asset.bearer_token,
                certificate=asset.certificate,
                passphrase=asset.passphrase,
                domain=asset.domain,
            )
            
            logger.info(
                f"Credentials fetched for asset {asset_id}: "
                f"type={credentials.credential_type}"
            )
            
            return credentials
        
        except Exception as e:
            logger.error(
                f"Error fetching credentials for asset {asset_id}: {e}",
                exc_info=True
            )
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Asset Service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        
        except Exception as e:
            logger.warning(f"Asset Service health check failed: {e}")
            return False
"""
Asset service client for OpsConductor AI Service
Handles communication with the asset service to get assets
"""
import os
import requests
import asyncio
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AssetServiceClient:
    """Client for communicating with the asset service"""
    
    def __init__(self, base_url: str = "http://asset-service:3002"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30.0

    async def get_all_assets(self) -> List[Dict[str, Any]]:
        """Get all assets from asset service"""
        try:
            response = requests.get(f"{self.base_url}/assets", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data.get('success'):
                return data.get('data', {}).get('assets', [])
            return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch assets: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching assets: {e}")
            return []

    async def get_asset_by_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get asset information by IP address"""
        try:
            # Get all assets and filter by IP address
            assets = await self.get_all_assets()
            for asset in assets:
                if asset.get('ip_address') == ip_address:
                    return asset
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching asset by IP {ip_address}: {e}")
            return None

    async def get_asset_by_hostname(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Get asset information by hostname"""
        try:
            # Get all assets and filter by hostname
            assets = await self.get_all_assets()
            for asset in assets:
                if asset.get('hostname', '').lower() == hostname.lower() or asset.get('name', '').lower() == hostname.lower():
                    return asset
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching asset by hostname {hostname}: {e}")
            return None

    async def get_assets_by_os_type(self, os_type: str) -> List[Dict[str, Any]]:
        """Get assets filtered by OS type"""
        try:
            assets = await self.get_all_assets()
            return [asset for asset in assets if os_type.lower() in asset.get('os_type', '').lower()]
        except Exception as e:
            logger.error(f"Unexpected error fetching assets by OS type {os_type}: {e}")
            return []

    async def get_assets_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get assets filtered by tag"""
        try:
            assets = await self.get_all_assets()
            return [asset for asset in assets if tag.lower() in [t.lower() for t in asset.get('tags', [])]]
        except Exception as e:
            logger.error(f"Unexpected error fetching assets by tag {tag}: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if asset service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Asset service health check failed: {e}")
            return False


# Example usage and testing
async def test_asset_client():
    """Test the asset client"""
    # Use environment variable for asset service URL, fallback to Docker service name
    asset_service_url = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
    client = AssetServiceClient(asset_service_url)
    
    print("=== Asset Service Client Test ===")
    
    # Test health check
    healthy = await client.health_check()
    print(f"Asset service healthy: {healthy}")
    
    # Test getting all assets
    assets = await client.get_all_assets()
    print(f"Found {len(assets)} assets")
    
    # Test getting asset by IP
    test_ip = "192.168.50.210"
    asset = await client.get_asset_by_ip(test_ip)
    if asset:
        print(f"Asset for IP {test_ip}: {asset['name']} ({asset['os_type']})")
    else:
        print(f"No asset found for IP {test_ip}")
    
    # Test getting assets by OS type
    windows_assets = await client.get_assets_by_os_type("windows")
    print(f"Found {len(windows_assets)} Windows assets")
    
    # Test getting assets by tag
    win10_assets = await client.get_assets_by_tag("win10")
    print(f"Found {len(win10_assets)} assets with 'win10' tag")


if __name__ == "__main__":
    asyncio.run(test_asset_client())
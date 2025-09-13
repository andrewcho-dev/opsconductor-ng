"""
Asset service client for OpsConductor AI Service
Handles communication with the asset service to get target groups and targets
"""
import httpx
import asyncio
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AssetServiceClient:
    """Client for communicating with the asset service"""
    
    def __init__(self, base_url: str = "http://asset-service:3002"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30.0

    async def get_target_groups(self) -> List[Dict[str, Any]]:
        """Get all target groups from asset service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/target-groups")
                response.raise_for_status()
                data = response.json()
                return data.get('groups', [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch target groups: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching target groups: {e}")
            return []

    async def get_target_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific target group by name"""
        try:
            groups = await self.get_target_groups()
            for group in groups:
                if group.get('name', '').lower() == group_name.lower():
                    return group
            return None
        except Exception as e:
            logger.error(f"Error finding target group '{group_name}': {e}")
            return None

    async def get_targets_in_group(self, group_id: int) -> List[Dict[str, Any]]:
        """Get all targets in a specific group"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/target-groups/{group_id}/targets")
                response.raise_for_status()
                data = response.json()
                return data.get('targets', [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch targets for group {group_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching targets for group {group_id}: {e}")
            return []

    async def get_all_targets(self) -> List[Dict[str, Any]]:
        """Get all targets from asset service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/targets")
                response.raise_for_status()
                data = response.json()
                return data.get('targets', [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch targets: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching targets: {e}")
            return []

    async def resolve_target_group(self, group_name: str) -> List[Dict[str, Any]]:
        """
        Resolve a group name to actual targets
        Returns list of target dictionaries
        """
        if not group_name:
            return []
        
        # Clean up group name
        group_name = group_name.lower().strip()
        
        # Handle common group name variations
        group_mappings = {
            'cis servers': 'cis',
            'cis': 'cis',
            'web servers': 'web',
            'webservers': 'web',
            'database servers': 'database',
            'db servers': 'database',
            'dbservers': 'database',
            'app servers': 'application',
            'application servers': 'application',
            'appservers': 'application',
            'all servers': 'all',
            'production servers': 'production',
            'prod servers': 'production',
            'staging servers': 'staging',
            'stage servers': 'staging',
            'development servers': 'development',
            'dev servers': 'development'
        }
        
        # Map common names to standard names
        standard_name = group_mappings.get(group_name, group_name)
        
        # Try to find the group
        group = await self.get_target_group_by_name(standard_name)
        if group:
            targets = await self.get_targets_in_group(group['id'])
            logger.info(f"Found {len(targets)} targets in group '{standard_name}'")
            return targets
        
        # If no specific group found, return empty list for now
        # In a real implementation, we might create mock data or ask for clarification
        logger.warning(f"No target group found for '{group_name}' (mapped to '{standard_name}')")
        return []

    async def health_check(self) -> bool:
        """Check if asset service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Asset service health check failed: {e}")
            return False

    async def create_mock_targets_for_demo(self, group_name: str) -> List[Dict[str, Any]]:
        """
        Create mock targets for demo purposes when asset service has no data
        This is temporary for prototype phase
        """
        mock_targets = {
            'cis': [
                {
                    'id': 1,
                    'hostname': 'cis-server-01.company.com',
                    'ip_address': '10.1.1.10',
                    'os_type': 'windows',
                    'services': [
                        {'name': 'winrm', 'port': 5985, 'protocol': 'http'},
                        {'name': 'winrm-ssl', 'port': 5986, 'protocol': 'https'}
                    ],
                    'credentials': {
                        'username': 'admin',
                        'password': '***encrypted***'
                    }
                },
                {
                    'id': 2,
                    'hostname': 'cis-server-02.company.com',
                    'ip_address': '10.1.1.11',
                    'os_type': 'windows',
                    'services': [
                        {'name': 'winrm', 'port': 5985, 'protocol': 'http'},
                        {'name': 'winrm-ssl', 'port': 5986, 'protocol': 'https'}
                    ],
                    'credentials': {
                        'username': 'admin',
                        'password': '***encrypted***'
                    }
                }
            ],
            'web': [
                {
                    'id': 3,
                    'hostname': 'web-server-01.company.com',
                    'ip_address': '10.1.2.10',
                    'os_type': 'linux',
                    'services': [
                        {'name': 'ssh', 'port': 22, 'protocol': 'tcp'}
                    ],
                    'credentials': {
                        'username': 'root',
                        'password': '***encrypted***'
                    }
                },
                {
                    'id': 4,
                    'hostname': 'web-server-02.company.com',
                    'ip_address': '10.1.2.11',
                    'os_type': 'linux',
                    'services': [
                        {'name': 'ssh', 'port': 22, 'protocol': 'tcp'}
                    ],
                    'credentials': {
                        'username': 'root',
                        'password': '***encrypted***'
                    }
                }
            ]
        }
        
        group_key = group_name.lower().strip()
        return mock_targets.get(group_key, [])


# Example usage and testing
async def test_asset_client():
    """Test the asset client"""
    client = AssetServiceClient("http://localhost:3002")
    
    print("=== Asset Service Client Test ===")
    
    # Test health check
    healthy = await client.health_check()
    print(f"Asset service healthy: {healthy}")
    
    # Test getting target groups
    groups = await client.get_target_groups()
    print(f"Found {len(groups)} target groups")
    
    # Test resolving group names
    test_groups = ['CIS servers', 'web servers', 'nonexistent group']
    for group_name in test_groups:
        targets = await client.resolve_target_group(group_name)
        print(f"Group '{group_name}': {len(targets)} targets")
        
        # If no targets found, try mock data
        if not targets:
            mock_targets = await client.create_mock_targets_for_demo(group_name)
            print(f"Mock targets for '{group_name}': {len(mock_targets)} targets")
            for target in mock_targets:
                print(f"  - {target['hostname']} ({target['os_type']})")


if __name__ == "__main__":
    asyncio.run(test_asset_client())
#!/usr/bin/env python3
"""
Asset Mapper - Modern asset resolution and management for OpsConductor AI Brain

This module provides intelligent asset mapping and resolution capabilities,
replacing the legacy target-based system with proper asset terminology.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import requests

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Types of resources in OpsConductor"""
    ASSET = "asset"
    GROUP = "group"
    CREDENTIAL = "credential"
    SERVICE_DEFINITION = "service_definition"
    USER = "user"
    ROLE = "role"

class AssetType(Enum):
    """Types of automation assets"""
    LINUX_SERVER = "linux_server"
    WINDOWS_SERVER = "windows_server"
    NETWORK_DEVICE = "network_device"
    DATABASE = "database"
    WEB_SERVICE = "web_service"
    CONTAINER = "container"
    CLOUD_INSTANCE = "cloud_instance"

class CredentialType(Enum):
    """Types of credentials"""
    USERNAME_PASSWORD = "username_password"
    SSH_KEY = "ssh_key"
    API_KEY = "api_key"
    CERTIFICATE = "certificate"
    TOKEN = "token"

@dataclass
class Asset:
    """Represents an automation asset"""
    id: int
    name: str
    host: str
    asset_type: AssetType
    port: Optional[int]
    description: Optional[str]
    tags: List[str]
    group_ids: List[int]
    credential_ids: List[int]
    properties: Dict[str, Any]
    status: str
    last_seen: Optional[str]

@dataclass
class Group:
    """Represents an asset group"""
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    child_ids: List[int]
    asset_ids: List[int]
    properties: Dict[str, Any]

@dataclass
class Credential:
    """Represents authentication credentials"""
    id: int
    name: str
    credential_type: CredentialType
    description: Optional[str]
    properties: Dict[str, Any]  # Encrypted data
    applicable_asset_types: List[AssetType]

@dataclass
class ResourceResolutionResult:
    """Result of resource resolution"""
    resolved_assets: List[Asset]
    resolved_credentials: List[Credential]
    resolution_path: List[str]
    warnings: List[str]
    errors: List[str]

class AssetMapper:
    """Intelligent asset mapping and resolution"""
    
    def __init__(self, asset_service_url: str = "http://asset-service:3002"):
        self.asset_service_url = asset_service_url
        self._cache = {
            "assets": {},
            "groups": {},
            "credentials": {},
            "cache_timestamp": None
        }
        self._cache_ttl = 300  # 5 minutes
        logger.info("Initialized AssetMapper")
    
    def _map_asset_to_asset_type(self, asset_data: Dict[str, Any]) -> AssetType:
        """Map asset device_type and os_type to AssetType"""
        device_type = asset_data.get("device_type", "").lower()
        os_type = asset_data.get("os_type", "").lower()
        
        # Map based on device type and OS
        if device_type == "server":
            if "windows" in os_type:
                return AssetType.WINDOWS_SERVER
            else:
                return AssetType.LINUX_SERVER
        elif device_type == "workstation":
            if "windows" in os_type:
                return AssetType.WINDOWS_SERVER  # Treat workstations as servers for automation
            else:
                return AssetType.LINUX_SERVER
        elif "network" in device_type or "router" in device_type or "switch" in device_type:
            return AssetType.NETWORK_DEVICE
        elif "database" in device_type or "db" in device_type:
            return AssetType.DATABASE
        elif "container" in device_type or "docker" in device_type:
            return AssetType.CONTAINER
        elif "cloud" in device_type or "aws" in device_type or "azure" in device_type:
            return AssetType.CLOUD_INSTANCE
        else:
            # Default based on OS
            if "windows" in os_type:
                return AssetType.WINDOWS_SERVER
            else:
                return AssetType.LINUX_SERVER
    
    def _fetch_from_asset_service(self, endpoint: str) -> Dict[str, Any]:
        """Fetch data from asset service"""
        try:
            response = requests.get(f"{self.asset_service_url}{endpoint}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Asset service returned {response.status_code} for {endpoint}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching from asset service: {e}")
            return {}
    
    def _refresh_cache(self) -> None:
        """Refresh the resource cache"""
        try:
            # Fetch assets from the asset service (using /assets endpoint)
            assets_data = self._fetch_from_asset_service("/assets")
            
            # Process assets and map them to Asset objects
            if isinstance(assets_data, dict) and assets_data.get("success") and "data" in assets_data:
                data = assets_data["data"]
                if "assets" in data:
                    for asset_data in data["assets"]:
                        # Map asset data to Asset structure
                        asset_type = self._map_asset_to_asset_type(asset_data)
                        
                        asset = Asset(
                            id=asset_data.get("id"),
                            name=asset_data.get("name"),
                            host=asset_data.get("ip_address") or asset_data.get("hostname"),  # Use IP as host
                            asset_type=asset_type,
                            port=asset_data.get("port"),
                            description=asset_data.get("description"),
                            tags=asset_data.get("tags", []),
                            group_ids=[],  # Asset service doesn't have groups yet
                            credential_ids=[],  # Asset service doesn't expose credential IDs
                            properties={
                                "hostname": asset_data.get("hostname"),
                                "ip_address": asset_data.get("ip_address"),
                                "os_type": asset_data.get("os_type"),
                                "os_version": asset_data.get("os_version"),
                                "device_type": asset_data.get("device_type"),
                                "service_type": asset_data.get("service_type"),
                                "is_secure": asset_data.get("is_secure"),
                                "has_credentials": asset_data.get("has_credentials"),
                                "is_active": asset_data.get("is_active")
                            },
                            status="active" if asset_data.get("is_active") else "inactive",
                            last_seen=asset_data.get("last_tested_at")
                        )
                        self._cache["assets"][asset.id] = asset
            
            import time
            self._cache["cache_timestamp"] = time.time()
            logger.info("Resource cache refreshed successfully")
            
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
    
    def _ensure_cache_fresh(self) -> None:
        """Ensure cache is fresh, refresh if needed"""
        import time
        current_time = time.time()
        
        if (self._cache["cache_timestamp"] is None or 
            current_time - self._cache["cache_timestamp"] > self._cache_ttl):
            self._refresh_cache()
    
    def resolve_assets(self, asset_specification: str) -> List[Asset]:
        """
        Resolve assets from various specifications:
        - Asset ID: "123"
        - Asset name: "web-server-01"
        - Group name: "group:web-servers"
        - Tag query: "tag:environment=prod"
        - Host pattern: "host:*.example.com"
        - Multiple: "web-server-01,web-server-02"
        """
        self._ensure_cache_fresh()
        resolved_assets = []
        
        # Split multiple specifications
        specifications = [spec.strip() for spec in asset_specification.split(",")]
        
        for spec in specifications:
            if spec.startswith("group:"):
                # Group resolution
                group_name = spec[6:]
                assets = self._resolve_assets_by_group(group_name)
                resolved_assets.extend(assets)
            
            elif spec.startswith("tag:"):
                # Tag-based resolution
                tag_query = spec[4:]
                assets = self._resolve_assets_by_tag(tag_query)
                resolved_assets.extend(assets)
            
            elif spec.startswith("host:"):
                # Host pattern resolution
                host_pattern = spec[5:]
                assets = self._resolve_assets_by_host_pattern(host_pattern)
                resolved_assets.extend(assets)
            
            elif spec.startswith("type:"):
                # Asset type resolution
                asset_type = spec[5:]
                assets = self._resolve_assets_by_type(asset_type)
                resolved_assets.extend(assets)
            
            elif spec.isdigit():
                # Asset ID resolution
                asset_id = int(spec)
                asset = self._cache["assets"].get(asset_id)
                if asset:
                    resolved_assets.append(asset)
            
            else:
                # Asset name resolution
                asset = self._resolve_asset_by_name(spec)
                if asset:
                    resolved_assets.append(asset)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_assets = []
        for asset in resolved_assets:
            if asset.id not in seen:
                seen.add(asset.id)
                unique_assets.append(asset)
        
        return unique_assets
    
    def _resolve_assets_by_group(self, group_name: str) -> List[Asset]:
        """Resolve assets by group name - groups not yet supported in asset service"""
        logger.warning(f"Group resolution not yet supported in asset service: '{group_name}'")
        return []
    
    def _resolve_assets_by_tag(self, tag_query: str) -> List[Asset]:
        """Resolve assets by tag query (e.g., 'environment=prod', 'role=web')"""
        assets = []
        
        # Parse tag query
        if "=" in tag_query:
            key, value = tag_query.split("=", 1)
            key, value = key.strip(), value.strip()
        else:
            key, value = tag_query.strip(), None
        
        # Find matching assets
        for asset in self._cache["assets"].values():
            if self._asset_matches_tag(asset, key, value):
                assets.append(asset)
        
        return assets
    
    def _asset_matches_tag(self, asset: Asset, key: str, value: Optional[str]) -> bool:
        """Check if asset matches tag criteria"""
        # Check in tags list
        for tag in asset.tags:
            if "=" in tag:
                tag_key, tag_value = tag.split("=", 1)
                if tag_key.strip().lower() == key.lower():
                    if value is None or tag_value.strip().lower() == value.lower():
                        return True
            else:
                if tag.strip().lower() == key.lower() and value is None:
                    return True
        
        # Check in properties
        if key.lower() in [k.lower() for k in asset.properties.keys()]:
            prop_value = asset.properties.get(key) or asset.properties.get(key.lower())
            if value is None or str(prop_value).lower() == value.lower():
                return True
        
        return False
    
    def _resolve_assets_by_host_pattern(self, host_pattern: str) -> List[Asset]:
        """Resolve assets by host pattern (supports wildcards)"""
        import fnmatch
        assets = []
        
        for asset in self._cache["assets"].values():
            if fnmatch.fnmatch(asset.host.lower(), host_pattern.lower()):
                assets.append(asset)
        
        return assets
    
    def _resolve_assets_by_type(self, asset_type_str: str) -> List[Asset]:
        """Resolve assets by type"""
        assets = []
        
        try:
            asset_type = AssetType(asset_type_str.lower())
            for asset in self._cache["assets"].values():
                if asset.asset_type == asset_type:
                    assets.append(asset)
        except ValueError:
            logger.warning(f"Invalid asset type: {asset_type_str}")
        
        return assets
    
    def _resolve_asset_by_name(self, asset_name: str) -> Optional[Asset]:
        """Resolve single asset by name"""
        for asset in self._cache["assets"].values():
            if asset.name.lower() == asset_name.lower():
                return asset
        
        logger.warning(f"Asset '{asset_name}' not found")
        return None
    
    def resolve_credentials(self, asset: Asset, credential_hint: Optional[str] = None) -> List[Credential]:
        """Resolve appropriate credentials for an asset - credentials not yet supported in asset service"""
        logger.warning(f"Credential resolution not yet supported in asset service for asset: {asset.name}")
        return []
    
    def resolve_resources(self, 
                          asset_spec: str, 
                          credential_hint: Optional[str] = None) -> ResourceResolutionResult:
        """Comprehensive resource resolution"""
        result = ResourceResolutionResult(
            resolved_assets=[],
            resolved_credentials=[],
            resolution_path=[],
            warnings=[],
            errors=[]
        )
        
        try:
            # Resolve assets
            result.resolution_path.append(f"Resolving assets from: {asset_spec}")
            assets = self.resolve_assets(asset_spec)
            result.resolved_assets = assets
            
            if not assets:
                result.errors.append(f"No assets found for specification: {asset_spec}")
                return result
            
            result.resolution_path.append(f"Found {len(assets)} asset(s)")
            
            # Resolve credentials for each asset
            all_credentials = []
            for asset in assets:
                result.resolution_path.append(f"Resolving credentials for asset: {asset.name}")
                asset_credentials = self.resolve_credentials(asset, credential_hint)
                
                if not asset_credentials:
                    result.warnings.append(f"No credentials found for asset: {asset.name}")
                else:
                    all_credentials.extend(asset_credentials)
                    result.resolution_path.append(f"Found {len(asset_credentials)} credential(s) for {asset.name}")
            
            # Remove duplicate credentials
            seen_creds = set()
            unique_credentials = []
            for cred in all_credentials:
                if cred.id not in seen_creds:
                    seen_creds.add(cred.id)
                    unique_credentials.append(cred)
            
            result.resolved_credentials = unique_credentials
            result.resolution_path.append(f"Total unique credentials: {len(unique_credentials)}")
            
        except Exception as e:
            result.errors.append(f"Error during resource resolution: {str(e)}")
            logger.error(f"Resource resolution error: {e}")
        
        return result
    
    def get_asset_connectivity_info(self, asset: Asset) -> Dict[str, Any]:
        """Get connectivity information for an asset"""
        connectivity_info = {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "host": asset.host,
            "type": asset.asset_type.value,
            "recommended_protocols": [],
            "default_ports": {},
            "connection_requirements": []
        }
        
        # Determine recommended protocols based on asset type
        if asset.asset_type in [AssetType.LINUX_SERVER, AssetType.CONTAINER]:
            connectivity_info["recommended_protocols"] = ["ssh"]
            connectivity_info["default_ports"]["ssh"] = asset.port or 22
            connectivity_info["connection_requirements"] = [
                "SSH daemon running",
                "Valid SSH credentials",
                "Network connectivity on port 22"
            ]
        
        elif asset.asset_type == AssetType.WINDOWS_SERVER:
            connectivity_info["recommended_protocols"] = ["winrm", "powershell"]
            connectivity_info["default_ports"]["winrm"] = asset.port or 5985
            connectivity_info["connection_requirements"] = [
                "WinRM service enabled",
                "Valid Windows credentials",
                "Network connectivity on port 5985/5986"
            ]
        
        elif asset.asset_type == AssetType.NETWORK_DEVICE:
            connectivity_info["recommended_protocols"] = ["snmp", "ssh"]
            connectivity_info["default_ports"]["snmp"] = 161
            connectivity_info["default_ports"]["ssh"] = 22
            connectivity_info["connection_requirements"] = [
                "SNMP enabled (for monitoring)",
                "SSH enabled (for configuration)",
                "Valid SNMP community or credentials"
            ]
        
        elif asset.asset_type == AssetType.WEB_SERVICE:
            connectivity_info["recommended_protocols"] = ["http", "https"]
            connectivity_info["default_ports"]["http"] = asset.port or 80
            connectivity_info["default_ports"]["https"] = asset.port or 443
            connectivity_info["connection_requirements"] = [
                "Web service running",
                "Valid API credentials (if required)",
                "Network connectivity on HTTP/HTTPS ports"
            ]
        
        elif asset.asset_type == AssetType.DATABASE:
            connectivity_info["recommended_protocols"] = ["database"]
            connectivity_info["default_ports"]["database"] = asset.port or 5432  # Default to PostgreSQL
            connectivity_info["connection_requirements"] = [
                "Database service running",
                "Valid database credentials",
                "Network connectivity on database port"
            ]
        
        return connectivity_info
    
    def validate_asset_accessibility(self, asset: Asset) -> Dict[str, Any]:
        """Validate if an asset is accessible"""
        validation_result = {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "accessible": False,
            "checks_performed": [],
            "issues_found": [],
            "recommendations": []
        }
        
        # This would typically perform actual connectivity tests
        # For now, we'll do basic validation based on available information
        
        validation_result["checks_performed"].append("Basic configuration validation")
        
        # Check if asset has host
        if not asset.host:
            validation_result["issues_found"].append("No host specified")
        
        # Check if asset has credentials
        if not asset.credential_ids:
            validation_result["issues_found"].append("No credentials associated")
            validation_result["recommendations"].append("Associate appropriate credentials with asset")
        
        # Check asset status
        if asset.status == "offline":
            validation_result["issues_found"].append("Asset marked as offline")
        elif asset.status == "unknown":
            validation_result["recommendations"].append("Perform connectivity test to determine status")
        
        # Determine accessibility
        validation_result["accessible"] = len(validation_result["issues_found"]) == 0
        
        return validation_result
    
    def get_resource_statistics(self) -> Dict[str, Any]:
        """Get statistics about cached resources"""
        stats = {
            "assets": {
                "total": len(self._cache["assets"]),
                "by_type": {},
                "by_status": {}
            },
            "groups": {
                "total": len(self._cache["groups"]),
                "with_children": 0,
                "root_groups": 0
            },
            "credentials": {
                "total": len(self._cache["credentials"]),
                "by_type": {}
            },
            "cache_info": {
                "last_refresh": self._cache["cache_timestamp"],
                "ttl_seconds": self._cache_ttl
            }
        }
        
        # Asset statistics
        for asset in self._cache["assets"].values():
            asset_type = asset.asset_type.value
            stats["assets"]["by_type"][asset_type] = stats["assets"]["by_type"].get(asset_type, 0) + 1
            
            status = asset.status
            stats["assets"]["by_status"][status] = stats["assets"]["by_status"].get(status, 0) + 1
        
        # Group statistics
        for group in self._cache["groups"].values():
            if group.child_ids:
                stats["groups"]["with_children"] += 1
            if not group.parent_id:
                stats["groups"]["root_groups"] += 1
        
        # Credential statistics
        for credential in self._cache["credentials"].values():
            cred_type = credential.credential_type.value
            stats["credentials"]["by_type"][cred_type] = stats["credentials"]["by_type"].get(cred_type, 0) + 1
        
        return stats

# Global instance
asset_mapper = AssetMapper()
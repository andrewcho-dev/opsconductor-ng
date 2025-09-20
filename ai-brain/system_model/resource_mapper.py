"""
OpsConductor System Model - Resource Mapper Module

This module provides intelligent mapping and resolution of OpsConductor resources
including targets, groups, credentials, and service definitions.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Types of resources in OpsConductor"""
    TARGET = "target"
    GROUP = "group"
    CREDENTIAL = "credential"
    SERVICE_DEFINITION = "service_definition"
    USER = "user"
    ROLE = "role"

class TargetType(Enum):
    """Types of automation targets"""
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
class Target:
    """Represents an automation target"""
    id: int
    name: str
    host: str
    target_type: TargetType
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
    """Represents a target group"""
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    child_ids: List[int]
    target_ids: List[int]
    properties: Dict[str, Any]

@dataclass
class Credential:
    """Represents authentication credentials"""
    id: int
    name: str
    credential_type: CredentialType
    description: Optional[str]
    properties: Dict[str, Any]  # Encrypted data
    applicable_target_types: List[TargetType]

@dataclass
class ResourceResolutionResult:
    """Result of resource resolution"""
    resolved_targets: List[Target]
    resolved_credentials: List[Credential]
    resolution_path: List[str]
    warnings: List[str]
    errors: List[str]

class ResourceMapper:
    """Intelligent resource mapping and resolution"""
    
    def __init__(self, asset_service_url: str = "http://asset-service:3002"):
        self.asset_service_url = asset_service_url
        self._cache = {
            "targets": {},
            "groups": {},
            "credentials": {},
            "cache_timestamp": None
        }
        self._cache_ttl = 300  # 5 minutes
        logger.info("Initialized ResourceMapper")
    
    async def _fetch_from_asset_service(self, endpoint: str) -> Dict[str, Any]:
        """Fetch data from asset service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.asset_service_url}{endpoint}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Asset service returned {response.status} for {endpoint}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching from asset service: {e}")
            return {}
    
    async def _refresh_cache(self) -> None:
        """Refresh the resource cache"""
        try:
            # Fetch all resources in parallel
            targets_data, groups_data, credentials_data = await asyncio.gather(
                self._fetch_from_asset_service("/targets"),
                self._fetch_from_asset_service("/groups"),
                self._fetch_from_asset_service("/credentials"),
                return_exceptions=True
            )
            
            # Process targets
            if isinstance(targets_data, dict) and "targets" in targets_data:
                for target_data in targets_data["targets"]:
                    target = Target(
                        id=target_data.get("id"),
                        name=target_data.get("name"),
                        host=target_data.get("host"),
                        target_type=TargetType(target_data.get("type", "linux_server")),
                        port=target_data.get("port"),
                        description=target_data.get("description"),
                        tags=target_data.get("tags", []),
                        group_ids=target_data.get("group_ids", []),
                        credential_ids=target_data.get("credential_ids", []),
                        properties=target_data.get("properties", {}),
                        status=target_data.get("status", "unknown"),
                        last_seen=target_data.get("last_seen")
                    )
                    self._cache["targets"][target.id] = target
            
            # Process groups
            if isinstance(groups_data, dict) and "groups" in groups_data:
                for group_data in groups_data["groups"]:
                    group = Group(
                        id=group_data.get("id"),
                        name=group_data.get("name"),
                        description=group_data.get("description"),
                        parent_id=group_data.get("parent_id"),
                        child_ids=group_data.get("child_ids", []),
                        target_ids=group_data.get("target_ids", []),
                        properties=group_data.get("properties", {})
                    )
                    self._cache["groups"][group.id] = group
            
            # Process credentials
            if isinstance(credentials_data, dict) and "credentials" in credentials_data:
                for cred_data in credentials_data["credentials"]:
                    credential = Credential(
                        id=cred_data.get("id"),
                        name=cred_data.get("name"),
                        credential_type=CredentialType(cred_data.get("type", "username_password")),
                        description=cred_data.get("description"),
                        properties=cred_data.get("properties", {}),
                        applicable_target_types=[TargetType(t) for t in cred_data.get("applicable_target_types", [])]
                    )
                    self._cache["credentials"][credential.id] = credential
            
            import time
            self._cache["cache_timestamp"] = time.time()
            logger.info("Resource cache refreshed successfully")
            
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
    
    async def _ensure_cache_fresh(self) -> None:
        """Ensure cache is fresh, refresh if needed"""
        import time
        current_time = time.time()
        
        if (self._cache["cache_timestamp"] is None or 
            current_time - self._cache["cache_timestamp"] > self._cache_ttl):
            await self._refresh_cache()
    
    async def resolve_targets(self, target_specification: str) -> List[Target]:
        """
        Resolve targets from various specifications:
        - Target ID: "123"
        - Target name: "web-server-01"
        - Group name: "group:web-servers"
        - Tag query: "tag:environment=prod"
        - Host pattern: "host:*.example.com"
        - Multiple: "web-server-01,web-server-02"
        """
        await self._ensure_cache_fresh()
        resolved_targets = []
        
        # Split multiple specifications
        specifications = [spec.strip() for spec in target_specification.split(",")]
        
        for spec in specifications:
            if spec.startswith("group:"):
                # Group resolution
                group_name = spec[6:]
                targets = await self._resolve_targets_by_group(group_name)
                resolved_targets.extend(targets)
            
            elif spec.startswith("tag:"):
                # Tag-based resolution
                tag_query = spec[4:]
                targets = await self._resolve_targets_by_tag(tag_query)
                resolved_targets.extend(targets)
            
            elif spec.startswith("host:"):
                # Host pattern resolution
                host_pattern = spec[5:]
                targets = await self._resolve_targets_by_host_pattern(host_pattern)
                resolved_targets.extend(targets)
            
            elif spec.startswith("type:"):
                # Target type resolution
                target_type = spec[5:]
                targets = await self._resolve_targets_by_type(target_type)
                resolved_targets.extend(targets)
            
            elif spec.isdigit():
                # Target ID resolution
                target_id = int(spec)
                target = self._cache["targets"].get(target_id)
                if target:
                    resolved_targets.append(target)
            
            else:
                # Target name resolution
                target = await self._resolve_target_by_name(spec)
                if target:
                    resolved_targets.append(target)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_targets = []
        for target in resolved_targets:
            if target.id not in seen:
                seen.add(target.id)
                unique_targets.append(target)
        
        return unique_targets
    
    async def _resolve_targets_by_group(self, group_name: str) -> List[Target]:
        """Resolve targets by group name (with hierarchy traversal)"""
        targets = []
        
        # Find group by name
        group = None
        for g in self._cache["groups"].values():
            if g.name.lower() == group_name.lower():
                group = g
                break
        
        if not group:
            logger.warning(f"Group '{group_name}' not found")
            return targets
        
        # Get all target IDs from group and its children
        target_ids = set(group.target_ids)
        
        # Recursively get targets from child groups
        def get_child_targets(group_id: int, visited: Set[int]) -> Set[int]:
            if group_id in visited:
                return set()  # Prevent infinite loops
            
            visited.add(group_id)
            child_target_ids = set()
            
            current_group = self._cache["groups"].get(group_id)
            if current_group:
                child_target_ids.update(current_group.target_ids)
                
                for child_id in current_group.child_ids:
                    child_target_ids.update(get_child_targets(child_id, visited))
            
            return child_target_ids
        
        child_target_ids = get_child_targets(group.id, set())
        target_ids.update(child_target_ids)
        
        # Resolve target objects
        for target_id in target_ids:
            target = self._cache["targets"].get(target_id)
            if target:
                targets.append(target)
        
        return targets
    
    async def _resolve_targets_by_tag(self, tag_query: str) -> List[Target]:
        """Resolve targets by tag query (e.g., 'environment=prod', 'role=web')"""
        targets = []
        
        # Parse tag query
        if "=" in tag_query:
            key, value = tag_query.split("=", 1)
            key, value = key.strip(), value.strip()
        else:
            key, value = tag_query.strip(), None
        
        # Find matching targets
        for target in self._cache["targets"].values():
            if self._target_matches_tag(target, key, value):
                targets.append(target)
        
        return targets
    
    def _target_matches_tag(self, target: Target, key: str, value: Optional[str]) -> bool:
        """Check if target matches tag criteria"""
        # Check in tags list
        for tag in target.tags:
            if "=" in tag:
                tag_key, tag_value = tag.split("=", 1)
                if tag_key.strip().lower() == key.lower():
                    if value is None or tag_value.strip().lower() == value.lower():
                        return True
            else:
                if tag.strip().lower() == key.lower() and value is None:
                    return True
        
        # Check in properties
        if key.lower() in [k.lower() for k in target.properties.keys()]:
            prop_value = target.properties.get(key) or target.properties.get(key.lower())
            if value is None or str(prop_value).lower() == value.lower():
                return True
        
        return False
    
    async def _resolve_targets_by_host_pattern(self, host_pattern: str) -> List[Target]:
        """Resolve targets by host pattern (supports wildcards)"""
        import fnmatch
        targets = []
        
        for target in self._cache["targets"].values():
            if fnmatch.fnmatch(target.host.lower(), host_pattern.lower()):
                targets.append(target)
        
        return targets
    
    async def _resolve_targets_by_type(self, target_type_str: str) -> List[Target]:
        """Resolve targets by type"""
        targets = []
        
        try:
            target_type = TargetType(target_type_str.lower())
            for target in self._cache["targets"].values():
                if target.target_type == target_type:
                    targets.append(target)
        except ValueError:
            logger.warning(f"Invalid target type: {target_type_str}")
        
        return targets
    
    async def _resolve_target_by_name(self, target_name: str) -> Optional[Target]:
        """Resolve single target by name"""
        for target in self._cache["targets"].values():
            if target.name.lower() == target_name.lower():
                return target
        
        logger.warning(f"Target '{target_name}' not found")
        return None
    
    async def resolve_credentials(self, target: Target, credential_hint: Optional[str] = None) -> List[Credential]:
        """Resolve appropriate credentials for a target"""
        await self._ensure_cache_fresh()
        credentials = []
        
        if credential_hint:
            # Try to resolve specific credential
            if credential_hint.isdigit():
                # Credential ID
                cred_id = int(credential_hint)
                credential = self._cache["credentials"].get(cred_id)
                if credential:
                    credentials.append(credential)
            else:
                # Credential name
                for cred in self._cache["credentials"].values():
                    if cred.name.lower() == credential_hint.lower():
                        credentials.append(cred)
        
        # If no specific credential found, use target's associated credentials
        if not credentials:
            for cred_id in target.credential_ids:
                credential = self._cache["credentials"].get(cred_id)
                if credential:
                    credentials.append(credential)
        
        # Filter credentials by target type compatibility
        compatible_credentials = []
        for credential in credentials:
            if (not credential.applicable_target_types or 
                target.target_type in credential.applicable_target_types):
                compatible_credentials.append(credential)
        
        return compatible_credentials
    
    async def resolve_resources(self, 
                              target_spec: str, 
                              credential_hint: Optional[str] = None) -> ResourceResolutionResult:
        """Comprehensive resource resolution"""
        result = ResourceResolutionResult(
            resolved_targets=[],
            resolved_credentials=[],
            resolution_path=[],
            warnings=[],
            errors=[]
        )
        
        try:
            # Resolve targets
            result.resolution_path.append(f"Resolving targets from: {target_spec}")
            targets = await self.resolve_targets(target_spec)
            result.resolved_targets = targets
            
            if not targets:
                result.errors.append(f"No targets found for specification: {target_spec}")
                return result
            
            result.resolution_path.append(f"Found {len(targets)} target(s)")
            
            # Resolve credentials for each target
            all_credentials = []
            for target in targets:
                result.resolution_path.append(f"Resolving credentials for target: {target.name}")
                target_credentials = await self.resolve_credentials(target, credential_hint)
                
                if not target_credentials:
                    result.warnings.append(f"No credentials found for target: {target.name}")
                else:
                    all_credentials.extend(target_credentials)
                    result.resolution_path.append(f"Found {len(target_credentials)} credential(s) for {target.name}")
            
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
    
    async def get_target_connectivity_info(self, target: Target) -> Dict[str, Any]:
        """Get connectivity information for a target"""
        connectivity_info = {
            "target_id": target.id,
            "target_name": target.name,
            "host": target.host,
            "type": target.target_type.value,
            "recommended_protocols": [],
            "default_ports": {},
            "connection_requirements": []
        }
        
        # Determine recommended protocols based on target type
        if target.target_type in [TargetType.LINUX_SERVER, TargetType.CONTAINER]:
            connectivity_info["recommended_protocols"] = ["ssh"]
            connectivity_info["default_ports"]["ssh"] = target.port or 22
            connectivity_info["connection_requirements"] = [
                "SSH daemon running",
                "Valid SSH credentials",
                "Network connectivity on port 22"
            ]
        
        elif target.target_type == TargetType.WINDOWS_SERVER:
            connectivity_info["recommended_protocols"] = ["winrm", "powershell"]
            connectivity_info["default_ports"]["winrm"] = target.port or 5985
            connectivity_info["connection_requirements"] = [
                "WinRM service enabled",
                "Valid Windows credentials",
                "Network connectivity on port 5985/5986"
            ]
        
        elif target.target_type == TargetType.NETWORK_DEVICE:
            connectivity_info["recommended_protocols"] = ["snmp", "ssh"]
            connectivity_info["default_ports"]["snmp"] = 161
            connectivity_info["default_ports"]["ssh"] = 22
            connectivity_info["connection_requirements"] = [
                "SNMP enabled (for monitoring)",
                "SSH enabled (for configuration)",
                "Valid SNMP community or credentials"
            ]
        
        elif target.target_type == TargetType.WEB_SERVICE:
            connectivity_info["recommended_protocols"] = ["http", "https"]
            connectivity_info["default_ports"]["http"] = target.port or 80
            connectivity_info["default_ports"]["https"] = target.port or 443
            connectivity_info["connection_requirements"] = [
                "Web service running",
                "Valid API credentials (if required)",
                "Network connectivity on HTTP/HTTPS ports"
            ]
        
        elif target.target_type == TargetType.DATABASE:
            connectivity_info["recommended_protocols"] = ["database"]
            connectivity_info["default_ports"]["database"] = target.port or 5432  # Default to PostgreSQL
            connectivity_info["connection_requirements"] = [
                "Database service running",
                "Valid database credentials",
                "Network connectivity on database port"
            ]
        
        return connectivity_info
    
    async def validate_target_accessibility(self, target: Target) -> Dict[str, Any]:
        """Validate if a target is accessible"""
        validation_result = {
            "target_id": target.id,
            "target_name": target.name,
            "accessible": False,
            "checks_performed": [],
            "issues_found": [],
            "recommendations": []
        }
        
        # This would typically perform actual connectivity tests
        # For now, we'll do basic validation based on available information
        
        validation_result["checks_performed"].append("Basic configuration validation")
        
        # Check if target has host
        if not target.host:
            validation_result["issues_found"].append("No host specified")
        
        # Check if target has credentials
        if not target.credential_ids:
            validation_result["issues_found"].append("No credentials associated")
            validation_result["recommendations"].append("Associate appropriate credentials with target")
        
        # Check target status
        if target.status == "offline":
            validation_result["issues_found"].append("Target marked as offline")
        elif target.status == "unknown":
            validation_result["recommendations"].append("Perform connectivity test to determine status")
        
        # Determine accessibility
        validation_result["accessible"] = len(validation_result["issues_found"]) == 0
        
        return validation_result
    
    def get_resource_statistics(self) -> Dict[str, Any]:
        """Get statistics about cached resources"""
        stats = {
            "targets": {
                "total": len(self._cache["targets"]),
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
        
        # Target statistics
        for target in self._cache["targets"].values():
            target_type = target.target_type.value
            stats["targets"]["by_type"][target_type] = stats["targets"]["by_type"].get(target_type, 0) + 1
            
            status = target.status
            stats["targets"]["by_status"][status] = stats["targets"]["by_status"].get(status, 0) + 1
        
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
resource_mapper = ResourceMapper()
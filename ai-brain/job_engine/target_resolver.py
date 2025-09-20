"""
OpsConductor AI Brain - Job Engine: Target Resolver Module

This module intelligently resolves target systems from user input, handles
group expansion, credential matching, and connection testing.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re
import ipaddress
from datetime import datetime

logger = logging.getLogger(__name__)

class TargetType(Enum):
    """Types of targets that can be resolved"""
    INDIVIDUAL = "individual"
    GROUP = "group"
    PATTERN = "pattern"
    SUBNET = "subnet"
    DYNAMIC = "dynamic"

class ConnectionStatus(Enum):
    """Connection status for targets"""
    UNKNOWN = "unknown"
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    AUTHENTICATION_FAILED = "authentication_failed"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"

class TargetPlatform(Enum):
    """Target platform types"""
    LINUX = "linux"
    WINDOWS = "windows"
    NETWORK_DEVICE = "network_device"
    CONTAINER = "container"
    CLOUD_INSTANCE = "cloud_instance"
    UNKNOWN = "unknown"

@dataclass
class TargetCredential:
    """Credential information for a target"""
    credential_id: str
    credential_type: str  # ssh_key, password, token, certificate
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None
    certificate: Optional[str] = None
    token: Optional[str] = None
    port: Optional[int] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResolvedTarget:
    """A resolved target system"""
    target_id: str
    hostname: str
    ip_address: str
    platform: TargetPlatform
    target_type: TargetType
    credentials: Optional[TargetCredential] = None
    connection_status: ConnectionStatus = ConnectionStatus.UNKNOWN
    last_tested: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    risk_level: str = "medium"
    requires_approval: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ResolvedTarget to dictionary for JSON serialization"""
        return {
            "target_id": self.target_id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "platform": self.platform.value if isinstance(self.platform, TargetPlatform) else str(self.platform),
            "target_type": self.target_type.value if isinstance(self.target_type, TargetType) else str(self.target_type),
            "credentials": self.credentials.__dict__ if self.credentials else None,
            "connection_status": self.connection_status.value if isinstance(self.connection_status, ConnectionStatus) else str(self.connection_status),
            "last_tested": self.last_tested.isoformat() if self.last_tested else None,
            "metadata": self.metadata,
            "tags": self.tags,
            "groups": self.groups,
            "capabilities": self.capabilities,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval
        }

@dataclass
class TargetGroup:
    """A group of targets"""
    group_id: str
    name: str
    description: str
    members: List[str]  # target IDs
    selection_criteria: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

@dataclass
class TargetResolutionResult:
    """Result of target resolution"""
    resolved_targets: List[ResolvedTarget]
    unresolved_targets: List[str]
    resolution_errors: List[str]
    total_requested: int
    total_resolved: int
    resolution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class TargetResolver:
    """Intelligently resolves target systems from various input formats"""
    
    def __init__(self):
        self.target_cache = {}
        self.group_cache = {}
        self.credential_cache = {}
        self._initialize_mock_data()
        logger.info("Initialized target resolver")
    
    def resolve_targets(
        self,
        target_input: Any,
        context: Dict[str, Any] = None
    ) -> TargetResolutionResult:
        """
        Resolve targets from various input formats
        
        Args:
            target_input: Target specification (string, list, dict, etc.)
            context: Additional context for resolution
            
        Returns:
            TargetResolutionResult: Resolution results with resolved targets
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Resolving targets from input: {target_input}")
            
            # Normalize input to list of target specifications
            target_specs = self._normalize_target_input(target_input)
            
            resolved_targets = []
            unresolved_targets = []
            resolution_errors = []
            
            for spec in target_specs:
                try:
                    targets = self._resolve_single_spec(spec, context)
                    resolved_targets.extend(targets)
                except Exception as e:
                    logger.error(f"Error resolving target spec '{spec}': {str(e)}")
                    unresolved_targets.append(str(spec))
                    resolution_errors.append(f"Failed to resolve '{spec}': {str(e)}")
            
            # Remove duplicates
            resolved_targets = self._deduplicate_targets(resolved_targets)
            
            # Test connections if requested
            if context and context.get('test_connections', False):
                resolved_targets = self._test_connections(resolved_targets)
            
            # Match credentials
            resolved_targets = self._match_credentials(resolved_targets)
            
            resolution_time = (datetime.now() - start_time).total_seconds()
            
            result = TargetResolutionResult(
                resolved_targets=resolved_targets,
                unresolved_targets=unresolved_targets,
                resolution_errors=resolution_errors,
                total_requested=len(target_specs),
                total_resolved=len(resolved_targets),
                resolution_time=resolution_time,
                metadata={
                    "context": context or {},
                    "resolution_method": "intelligent_resolver"
                }
            )
            
            logger.info(f"Resolved {len(resolved_targets)} targets from {len(target_specs)} specifications")
            return result
            
        except Exception as e:
            logger.error(f"Error in target resolution: {str(e)}")
            raise
    
    def _normalize_target_input(self, target_input: Any) -> List[str]:
        """Normalize various input formats to list of target specifications"""
        
        if isinstance(target_input, str):
            # Handle comma-separated values
            if ',' in target_input:
                return [spec.strip() for spec in target_input.split(',')]
            return [target_input.strip()]
        
        elif isinstance(target_input, list):
            return [str(item).strip() for item in target_input]
        
        elif isinstance(target_input, dict):
            # Handle structured input
            specs = []
            if 'targets' in target_input:
                specs.extend(self._normalize_target_input(target_input['targets']))
            if 'groups' in target_input:
                specs.extend([f"group:{group}" for group in target_input['groups']])
            if 'patterns' in target_input:
                specs.extend([f"pattern:{pattern}" for pattern in target_input['patterns']])
            return specs
        
        else:
            return [str(target_input)]
    
    def _resolve_single_spec(self, spec: str, context: Dict[str, Any] = None) -> List[ResolvedTarget]:
        """Resolve a single target specification"""
        
        spec = spec.strip()
        
        # Group reference
        if spec.startswith('group:'):
            group_name = spec[6:]
            return self._resolve_group(group_name)
        
        # Pattern matching
        elif spec.startswith('pattern:'):
            pattern = spec[8:]
            return self._resolve_pattern(pattern)
        
        # Subnet/CIDR notation
        elif '/' in spec and self._is_cidr(spec):
            return self._resolve_subnet(spec)
        
        # IP address
        elif self._is_ip_address(spec):
            return self._resolve_ip_address(spec)
        
        # Hostname or FQDN
        elif self._is_hostname(spec):
            return self._resolve_hostname(spec)
        
        # Tag-based selection
        elif spec.startswith('tag:'):
            tag = spec[4:]
            return self._resolve_by_tag(tag)
        
        # Platform-based selection
        elif spec.startswith('platform:'):
            platform = spec[9:]
            return self._resolve_by_platform(platform)
        
        # Wildcard patterns
        elif '*' in spec or '?' in spec:
            return self._resolve_wildcard(spec)
        
        # Default: treat as hostname
        else:
            return self._resolve_hostname(spec)
    
    def _resolve_group(self, group_name: str) -> List[ResolvedTarget]:
        """Resolve targets from a group"""
        
        # Check cache first
        if group_name in self.group_cache:
            group = self.group_cache[group_name]
            targets = []
            
            for member_id in group.members:
                if member_id in self.target_cache:
                    target = self.target_cache[member_id]
                    target.groups.append(group_name)
                    targets.append(target)
            
            return targets
        
        logger.warning(f"Group '{group_name}' not found")
        return []
    
    def _resolve_pattern(self, pattern: str) -> List[ResolvedTarget]:
        """Resolve targets matching a pattern"""
        
        targets = []
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        
        for target in self.target_cache.values():
            if re.match(regex_pattern, target.hostname, re.IGNORECASE):
                targets.append(target)
        
        return targets
    
    def _resolve_subnet(self, subnet: str) -> List[ResolvedTarget]:
        """Resolve targets in a subnet"""
        
        try:
            network = ipaddress.ip_network(subnet, strict=False)
            targets = []
            
            for target in self.target_cache.values():
                try:
                    target_ip = ipaddress.ip_address(target.ip_address)
                    if target_ip in network:
                        targets.append(target)
                except ValueError:
                    continue
            
            return targets
            
        except ValueError as e:
            logger.error(f"Invalid subnet specification '{subnet}': {str(e)}")
            return []
    
    def _resolve_ip_address(self, ip: str) -> List[ResolvedTarget]:
        """Resolve target by IP address"""
        
        for target in self.target_cache.values():
            if target.ip_address == ip:
                return [target]
        
        # Create new target if not found
        target = ResolvedTarget(
            target_id=f"ip_{ip.replace('.', '_')}",
            hostname=ip,
            ip_address=ip,
            platform=TargetPlatform.UNKNOWN,
            target_type=TargetType.INDIVIDUAL
        )
        
        return [target]
    
    def _resolve_hostname(self, hostname: str) -> List[ResolvedTarget]:
        """Resolve target by hostname"""
        
        for target in self.target_cache.values():
            if target.hostname.lower() == hostname.lower():
                return [target]
        
        # Create new target if not found
        target = ResolvedTarget(
            target_id=f"host_{hostname.replace('.', '_').replace('-', '_')}",
            hostname=hostname,
            ip_address="0.0.0.0",  # Would resolve via DNS in real implementation
            platform=TargetPlatform.UNKNOWN,
            target_type=TargetType.INDIVIDUAL
        )
        
        return [target]
    
    def _resolve_by_tag(self, tag: str) -> List[ResolvedTarget]:
        """Resolve targets by tag"""
        
        targets = []
        for target in self.target_cache.values():
            if tag.lower() in [t.lower() for t in target.tags]:
                targets.append(target)
        
        return targets
    
    def _resolve_by_platform(self, platform: str) -> List[ResolvedTarget]:
        """Resolve targets by platform"""
        
        try:
            target_platform = TargetPlatform(platform.lower())
            targets = []
            
            for target in self.target_cache.values():
                if target.platform == target_platform:
                    targets.append(target)
            
            return targets
            
        except ValueError:
            logger.error(f"Unknown platform: {platform}")
            return []
    
    def _resolve_wildcard(self, pattern: str) -> List[ResolvedTarget]:
        """Resolve targets using wildcard patterns"""
        
        # Convert shell-style wildcards to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex_pattern = f"^{regex_pattern}$"
        
        targets = []
        for target in self.target_cache.values():
            if re.match(regex_pattern, target.hostname, re.IGNORECASE):
                targets.append(target)
        
        return targets
    
    def _deduplicate_targets(self, targets: List[ResolvedTarget]) -> List[ResolvedTarget]:
        """Remove duplicate targets from the list"""
        
        seen = set()
        unique_targets = []
        
        for target in targets:
            # Use combination of hostname and IP as unique identifier
            identifier = f"{target.hostname}:{target.ip_address}"
            if identifier not in seen:
                seen.add(identifier)
                unique_targets.append(target)
        
        return unique_targets
    
    def _test_connections(self, targets: List[ResolvedTarget]) -> List[ResolvedTarget]:
        """Test connections to targets"""
        
        for target in targets:
            try:
                # Mock connection test - in real implementation would use actual network tests
                if target.ip_address != "0.0.0.0":
                    target.connection_status = ConnectionStatus.REACHABLE
                else:
                    target.connection_status = ConnectionStatus.UNREACHABLE
                
                target.last_tested = datetime.now()
                
            except Exception as e:
                logger.error(f"Connection test failed for {target.hostname}: {str(e)}")
                target.connection_status = ConnectionStatus.TIMEOUT
        
        return targets
    
    def _match_credentials(self, targets: List[ResolvedTarget]) -> List[ResolvedTarget]:
        """Match appropriate credentials to targets"""
        
        for target in targets:
            # Find best matching credential
            best_credential = None
            best_score = 0
            
            for cred_id, credential in self.credential_cache.items():
                score = self._score_credential_match(target, credential)
                if score > best_score:
                    best_score = score
                    best_credential = credential
            
            if best_credential:
                target.credentials = best_credential
        
        return targets
    
    def _score_credential_match(self, target: ResolvedTarget, credential: TargetCredential) -> float:
        """Score how well a credential matches a target"""
        
        score = 0.0
        
        # Platform-specific scoring
        if target.platform == TargetPlatform.LINUX and credential.credential_type == "ssh_key":
            score += 50
        elif target.platform == TargetPlatform.WINDOWS and credential.credential_type == "password":
            score += 50
        
        # Tag-based scoring
        common_tags = set(target.tags) & set(credential.additional_params.get('tags', []))
        score += len(common_tags) * 10
        
        # Group-based scoring
        common_groups = set(target.groups) & set(credential.additional_params.get('groups', []))
        score += len(common_groups) * 15
        
        return score
    
    def _is_cidr(self, spec: str) -> bool:
        """Check if specification is a CIDR notation"""
        try:
            ipaddress.ip_network(spec, strict=False)
            return True
        except ValueError:
            return False
    
    def _is_ip_address(self, spec: str) -> bool:
        """Check if specification is an IP address"""
        try:
            ipaddress.ip_address(spec)
            return True
        except ValueError:
            return False
    
    def _is_hostname(self, spec: str) -> bool:
        """Check if specification looks like a hostname"""
        # Simple hostname validation
        if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', spec):
            return True
        return False
    
    def _initialize_mock_data(self):
        """Initialize mock data for testing"""
        
        # Mock targets
        self.target_cache = {
            "web01": ResolvedTarget(
                target_id="web01",
                hostname="web01.example.com",
                ip_address="192.168.1.10",
                platform=TargetPlatform.LINUX,
                target_type=TargetType.INDIVIDUAL,
                tags=["web", "production", "ubuntu"],
                groups=["web_servers"],
                capabilities=["ssh", "http", "https"]
            ),
            "web02": ResolvedTarget(
                target_id="web02",
                hostname="web02.example.com",
                ip_address="192.168.1.11",
                platform=TargetPlatform.LINUX,
                target_type=TargetType.INDIVIDUAL,
                tags=["web", "production", "ubuntu"],
                groups=["web_servers"],
                capabilities=["ssh", "http", "https"]
            ),
            "db01": ResolvedTarget(
                target_id="db01",
                hostname="db01.example.com",
                ip_address="192.168.1.20",
                platform=TargetPlatform.LINUX,
                target_type=TargetType.INDIVIDUAL,
                tags=["database", "production", "postgresql"],
                groups=["database_servers"],
                capabilities=["ssh", "postgresql"],
                risk_level="high",
                requires_approval=True
            ),
            "app01": ResolvedTarget(
                target_id="app01",
                hostname="app01.example.com",
                ip_address="192.168.1.30",
                platform=TargetPlatform.LINUX,
                target_type=TargetType.INDIVIDUAL,
                tags=["application", "production", "java"],
                groups=["app_servers"],
                capabilities=["ssh", "java", "tomcat"]
            )
        }
        
        # Mock groups
        self.group_cache = {
            "web_servers": TargetGroup(
                group_id="web_servers",
                name="Web Servers",
                description="All web server instances",
                members=["web01", "web02"],
                selection_criteria={"tags": ["web"]},
                tags=["web", "frontend"]
            ),
            "database_servers": TargetGroup(
                group_id="database_servers",
                name="Database Servers",
                description="All database server instances",
                members=["db01"],
                selection_criteria={"tags": ["database"]},
                tags=["database", "backend"]
            ),
            "production": TargetGroup(
                group_id="production",
                name="Production Environment",
                description="All production servers",
                members=["web01", "web02", "db01", "app01"],
                selection_criteria={"tags": ["production"]},
                tags=["production", "critical"]
            )
        }
        
        # Mock credentials
        self.credential_cache = {
            "ssh_key_prod": TargetCredential(
                credential_id="ssh_key_prod",
                credential_type="ssh_key",
                username="ubuntu",
                private_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
                port=22,
                additional_params={
                    "tags": ["production", "linux"],
                    "groups": ["web_servers", "app_servers"]
                }
            ),
            "db_password": TargetCredential(
                credential_id="db_password",
                credential_type="password",
                username="dbadmin",
                password="secure_password",
                port=22,
                additional_params={
                    "tags": ["database"],
                    "groups": ["database_servers"]
                }
            )
        }
    
    def get_target_summary(self, targets: List[ResolvedTarget]) -> Dict[str, Any]:
        """Get summary information about resolved targets"""
        
        if not targets:
            return {"total": 0, "platforms": {}, "risk_levels": {}, "connection_status": {}}
        
        platforms = {}
        risk_levels = {}
        connection_status = {}
        
        for target in targets:
            # Platform distribution
            platform = target.platform.value
            platforms[platform] = platforms.get(platform, 0) + 1
            
            # Risk level distribution
            risk = target.risk_level
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
            
            # Connection status distribution
            status = target.connection_status.value
            connection_status[status] = connection_status.get(status, 0) + 1
        
        return {
            "total": len(targets),
            "platforms": platforms,
            "risk_levels": risk_levels,
            "connection_status": connection_status,
            "requires_approval": sum(1 for t in targets if t.requires_approval),
            "unique_groups": len(set(group for target in targets for group in target.groups)),
            "unique_tags": len(set(tag for target in targets for tag in target.tags))
        }
    
    def export_targets(self, targets: List[ResolvedTarget]) -> List[Dict[str, Any]]:
        """Export targets to dictionary format"""
        
        return [
            {
                "target_id": target.target_id,
                "hostname": target.hostname,
                "ip_address": target.ip_address,
                "platform": target.platform.value,
                "target_type": target.target_type.value,
                "connection_status": target.connection_status.value,
                "last_tested": target.last_tested.isoformat() if target.last_tested else None,
                "metadata": target.metadata,
                "tags": target.tags,
                "groups": target.groups,
                "capabilities": target.capabilities,
                "risk_level": target.risk_level,
                "requires_approval": target.requires_approval,
                "credentials": {
                    "credential_id": target.credentials.credential_id,
                    "credential_type": target.credentials.credential_type,
                    "username": target.credentials.username,
                    "port": target.credentials.port
                } if target.credentials else None
            }
            for target in targets
        ]

# Global instance
target_resolver = TargetResolver()

def resolve_targets(target_input: Any, context: Dict[str, Any] = None) -> TargetResolutionResult:
    """
    High-level function to resolve targets
    
    Args:
        target_input: Target specification in various formats
        context: Additional context for resolution
        
    Returns:
        TargetResolutionResult: Resolution results with resolved targets
    """
    return target_resolver.resolve_targets(target_input, context)
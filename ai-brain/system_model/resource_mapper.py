"""
OpsConductor System Model - Resource Mapper Module

This module provides intelligent mapping between user requests and OpsConductor resources,
enabling the AI to understand which services, assets, and capabilities to use for specific tasks.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Types of resources in OpsConductor"""
    ASSET = "asset"
    SERVICE = "service"
    CREDENTIAL = "credential"
    JOB = "job"
    WORKFLOW = "workflow"
    USER = "user"
    NOTIFICATION = "notification"

class ActionType(Enum):
    """Types of actions that can be performed"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MONITOR = "monitor"
    CONFIGURE = "configure"
    DEPLOY = "deploy"
    BACKUP = "backup"
    RESTORE = "restore"

@dataclass
class ResourceMapping:
    """Maps user intent to specific OpsConductor resources"""
    resource_type: ResourceType
    service_name: str
    action_type: ActionType
    required_capabilities: List[str]
    api_endpoints: List[str]
    parameters: Dict[str, Any]
    dependencies: List[str]

class ResourceMapper:
    """Intelligent resource mapping for OpsConductor AI system"""
    
    def __init__(self):
        self.intent_mappings = self._initialize_intent_mappings()
        self.service_mappings = self._initialize_service_mappings()
        logger.info("Resource mapper initialized with intent and service mappings")
    
    def _initialize_intent_mappings(self) -> Dict[str, List[ResourceMapping]]:
        """Initialize mappings from user intents to resources"""
        mappings = {}
        
        # Server/Asset Management Intents
        mappings["create_server"] = [
            ResourceMapping(
                resource_type=ResourceType.ASSET,
                service_name="asset-service",
                action_type=ActionType.CREATE,
                required_capabilities=["asset_management"],
                api_endpoints=["/assets"],
                parameters={"name": "str", "ip_address": "str", "os_type": "str"},
                dependencies=["postgres"]
            )
        ]
        
        mappings["list_servers"] = [
            ResourceMapping(
                resource_type=ResourceType.ASSET,
                service_name="asset-service",
                action_type=ActionType.READ,
                required_capabilities=["asset_management"],
                api_endpoints=["/assets"],
                parameters={"limit": "int?", "skip": "int?"},
                dependencies=["postgres"]
            )
        ]
        
        mappings["update_server"] = [
            ResourceMapping(
                resource_type=ResourceType.ASSET,
                service_name="asset-service",
                action_type=ActionType.UPDATE,
                required_capabilities=["asset_management"],
                api_endpoints=["/assets/{asset_id}"],
                parameters={"asset_id": "int"},
                dependencies=["postgres"]
            )
        ]
        
        # Job/Automation Intents
        mappings["create_job"] = [
            ResourceMapping(
                resource_type=ResourceType.JOB,
                service_name="automation-service",
                action_type=ActionType.CREATE,
                required_capabilities=["job_management"],
                api_endpoints=["/jobs"],
                parameters={"name": "str", "workflow": "dict", "targets": "list"},
                dependencies=["postgres", "redis", "celery"]
            )
        ]
        
        mappings["execute_job"] = [
            ResourceMapping(
                resource_type=ResourceType.JOB,
                service_name="automation-service",
                action_type=ActionType.EXECUTE,
                required_capabilities=["job_management"],
                api_endpoints=["/jobs/{job_id}/execute"],
                parameters={"job_id": "int"},
                dependencies=["postgres", "redis", "celery"]
            )
        ]
        
        mappings["monitor_job"] = [
            ResourceMapping(
                resource_type=ResourceType.JOB,
                service_name="automation-service",
                action_type=ActionType.MONITOR,
                required_capabilities=["real_time_monitoring"],
                api_endpoints=["/jobs/{job_id}/status", "/jobs/{job_id}/logs"],
                parameters={"job_id": "int"},
                dependencies=["redis", "websocket_manager"]
            )
        ]
        
        # User Management Intents
        mappings["create_user"] = [
            ResourceMapping(
                resource_type=ResourceType.USER,
                service_name="identity-service",
                action_type=ActionType.CREATE,
                required_capabilities=["user_management"],
                api_endpoints=["/users"],
                parameters={"username": "str", "email": "str", "password": "str"},
                dependencies=["postgres"]
            )
        ]
        
        # Credential Management Intents
        mappings["create_credential"] = [
            ResourceMapping(
                resource_type=ResourceType.CREDENTIAL,
                service_name="asset-service",
                action_type=ActionType.CREATE,
                required_capabilities=["credential_management"],
                api_endpoints=["/credentials"],
                parameters={"name": "str", "type": "str", "data": "encrypted"},
                dependencies=["postgres", "encryption_key"]
            )
        ]
        
        # Workflow Intents
        mappings["create_workflow"] = [
            ResourceMapping(
                resource_type=ResourceType.WORKFLOW,
                service_name="automation-service",
                action_type=ActionType.CREATE,
                required_capabilities=["workflow_execution"],
                api_endpoints=["/workflows"],
                parameters={"name": "str", "steps": "list"},
                dependencies=["postgres", "redis", "celery"]
            )
        ]
        
        mappings["execute_workflow"] = [
            ResourceMapping(
                resource_type=ResourceType.WORKFLOW,
                service_name="automation-service",
                action_type=ActionType.EXECUTE,
                required_capabilities=["workflow_execution"],
                api_endpoints=["/workflows/{workflow_id}/execute"],
                parameters={"workflow_id": "int", "parameters": "dict"},
                dependencies=["postgres", "redis", "celery"]
            )
        ]
        
        # Notification Intents
        mappings["send_notification"] = [
            ResourceMapping(
                resource_type=ResourceType.NOTIFICATION,
                service_name="communication-service",
                action_type=ActionType.CREATE,
                required_capabilities=["notification_management"],
                api_endpoints=["/notifications"],
                parameters={"type": "str", "recipients": "list", "message": "str"},
                dependencies=["postgres", "redis"]
            )
        ]
        
        return mappings
    
    def _initialize_service_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize service-specific mappings"""
        return {
            "asset-service": {
                "base_url": "http://asset-service:3002",
                "health_endpoint": "/health",
                "primary_resources": [ResourceType.ASSET, ResourceType.CREDENTIAL],
                "protocols": ["ssh", "winrm", "snmp", "http", "https"]
            },
            "automation-service": {
                "base_url": "http://automation-service:3003",
                "health_endpoint": "/health",
                "primary_resources": [ResourceType.JOB, ResourceType.WORKFLOW],
                "protocols": ["ssh", "winrm", "powershell", "snmp"]
            },
            "identity-service": {
                "base_url": "http://identity-service:3001",
                "health_endpoint": "/health",
                "primary_resources": [ResourceType.USER],
                "protocols": ["https", "rest_api"]
            },
            "communication-service": {
                "base_url": "http://communication-service:3004",
                "health_endpoint": "/health",
                "primary_resources": [ResourceType.NOTIFICATION],
                "protocols": ["https", "rest_api", "email", "slack"]
            }
        }
    
    def map_intent_to_resources(self, intent: str, context: Dict[str, Any] = None) -> List[ResourceMapping]:
        """Map user intent to required OpsConductor resources"""
        context = context or {}
        
        # Direct mapping lookup
        if intent in self.intent_mappings:
            return self.intent_mappings[intent]
        
        # Fuzzy matching for similar intents
        similar_intents = self._find_similar_intents(intent)
        if similar_intents:
            logger.info(f"Using similar intent '{similar_intents[0]}' for '{intent}'")
            return self.intent_mappings[similar_intents[0]]
        
        # Fallback: analyze intent keywords
        return self._analyze_intent_keywords(intent, context)
    
    def _find_similar_intents(self, intent: str) -> List[str]:
        """Find similar intents using keyword matching"""
        intent_lower = intent.lower()
        similar = []
        
        for known_intent in self.intent_mappings.keys():
            # Check for common keywords
            intent_words = set(intent_lower.split())
            known_words = set(known_intent.lower().split('_'))
            
            if intent_words.intersection(known_words):
                similar.append(known_intent)
        
        return similar
    
    def _analyze_intent_keywords(self, intent: str, context: Dict[str, Any]) -> List[ResourceMapping]:
        """Analyze intent keywords to determine resource mappings"""
        intent_lower = intent.lower()
        mappings = []
        
        # Asset/Server related keywords
        if any(word in intent_lower for word in ['server', 'asset', 'machine', 'host', 'target']):
            if any(word in intent_lower for word in ['create', 'add', 'new']):
                mappings.extend(self.intent_mappings.get("create_server", []))
            elif any(word in intent_lower for word in ['list', 'show', 'get', 'view']):
                mappings.extend(self.intent_mappings.get("list_servers", []))
            elif any(word in intent_lower for word in ['update', 'modify', 'change']):
                mappings.extend(self.intent_mappings.get("update_server", []))
        
        # Job/Automation related keywords
        if any(word in intent_lower for word in ['job', 'task', 'automation', 'execute', 'run']):
            if any(word in intent_lower for word in ['create', 'new']):
                mappings.extend(self.intent_mappings.get("create_job", []))
            elif any(word in intent_lower for word in ['execute', 'run', 'start']):
                mappings.extend(self.intent_mappings.get("execute_job", []))
            elif any(word in intent_lower for word in ['monitor', 'status', 'check']):
                mappings.extend(self.intent_mappings.get("monitor_job", []))
        
        # User related keywords
        if any(word in intent_lower for word in ['user', 'account', 'login']):
            if any(word in intent_lower for word in ['create', 'add', 'new']):
                mappings.extend(self.intent_mappings.get("create_user", []))
        
        # Workflow related keywords
        if any(word in intent_lower for word in ['workflow', 'process', 'procedure']):
            if any(word in intent_lower for word in ['create', 'new']):
                mappings.extend(self.intent_mappings.get("create_workflow", []))
            elif any(word in intent_lower for word in ['execute', 'run', 'start']):
                mappings.extend(self.intent_mappings.get("execute_workflow", []))
        
        return mappings
    
    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific service"""
        return self.service_mappings.get(service_name)
    
    def get_required_services(self, resource_mappings: List[ResourceMapping]) -> List[str]:
        """Get list of services required for given resource mappings"""
        services = set()
        for mapping in resource_mappings:
            services.add(mapping.service_name)
        return list(services)
    
    def validate_resource_availability(self, resource_mappings: List[ResourceMapping]) -> Tuple[bool, List[str]]:
        """Validate that required resources are available"""
        missing_services = []
        
        for mapping in resource_mappings:
            service_info = self.get_service_info(mapping.service_name)
            if not service_info:
                missing_services.append(mapping.service_name)
        
        return len(missing_services) == 0, missing_services

# Global instance for import
resource_mapper = ResourceMapper()
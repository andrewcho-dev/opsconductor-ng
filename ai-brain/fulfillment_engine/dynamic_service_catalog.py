#!/usr/bin/env python3
"""
Dynamic Service Catalog System
Scalable, extensible knowledge management for AI reasoning
Supports dynamic API discovery and specialty domain integration
"""

import json
import os
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging
import requests
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class KnowledgeDomainType(Enum):
    """Types of knowledge domains"""
    CORE_SERVICE = "core_service"           # OpsConductor native services
    SPECIALTY_API = "specialty_api"         # External APIs (VAPIX, AWS, etc.)
    LEARNED_CAPABILITY = "learned_capability"  # AI-discovered patterns
    INTEGRATION_PATTERN = "integration_pattern"  # Cross-domain workflows

class ContextPriority(Enum):
    """Priority levels for context loading"""
    CRITICAL = 1    # Always load (core services)
    HIGH = 2        # Load for relevant requests
    MEDIUM = 3      # Load if space permits
    LOW = 4         # Load only if specifically requested

@dataclass
class KnowledgeMetadata:
    """Metadata for knowledge management"""
    domain_id: str
    domain_type: KnowledgeDomainType
    version: str
    last_updated: datetime
    size_bytes: int
    priority: ContextPriority
    keywords: List[str]
    dependencies: List[str]
    performance_metrics: Dict[str, Any]

@dataclass
class APIDiscoveryResult:
    """Result from API discovery process"""
    endpoints: List[Dict[str, Any]]
    capabilities: List[str]
    authentication_methods: List[str]
    rate_limits: Dict[str, Any]
    documentation_urls: List[str]
    examples: List[Dict[str, Any]]

class KnowledgeDomain(ABC):
    """Abstract base class for knowledge domains"""
    
    def __init__(self, domain_id: str, metadata: KnowledgeMetadata):
        self.domain_id = domain_id
        self.metadata = metadata
        self._knowledge_cache = {}
        self._last_loaded = None
    
    @abstractmethod
    async def discover_capabilities(self) -> APIDiscoveryResult:
        """Discover and catalog API capabilities"""
        pass
    
    @abstractmethod
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        """Get relevant context for a specific request"""
        pass
    
    @abstractmethod
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        """Update domain knowledge"""
        pass

class VAPIXDomain(KnowledgeDomain):
    """Axis Camera VAPIX API Knowledge Domain"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="vapix_cameras",
            domain_type=KnowledgeDomainType.SPECIALTY_API,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.HIGH,
            keywords=["camera", "vapix", "axis", "video", "surveillance", "ptz", "stream"],
            dependencies=[],
            performance_metrics={}
        )
        super().__init__("vapix_cameras", metadata)
        self.base_knowledge = self._initialize_vapix_knowledge()
    
    def _initialize_vapix_knowledge(self) -> Dict[str, Any]:
        """Initialize comprehensive VAPIX knowledge"""
        return {
            "service_info": {
                "name": "VAPIX Camera Control",
                "description": "Axis Camera VAPIX API integration for video surveillance and camera control",
                "base_url_pattern": "http://{camera_ip}/axis-cgi/",
                "authentication": ["basic", "digest"],
                "supported_protocols": ["HTTP", "HTTPS", "RTSP"]
            },
            "capabilities": {
                "camera_control": {
                    "description": "Control camera movement, zoom, focus",
                    "endpoints": [
                        {
                            "path": "com/ptz.cgi",
                            "method": "GET",
                            "description": "Pan, tilt, zoom control",
                            "parameters": {
                                "camera": "Camera number (1-4)",
                                "pan": "Pan position (-180 to 180)",
                                "tilt": "Tilt position (-180 to 180)",
                                "zoom": "Zoom level (1-9999)",
                                "speed": "Movement speed (1-100)"
                            },
                            "example_request": "GET /axis-cgi/com/ptz.cgi?camera=1&pan=45&tilt=30&zoom=1000",
                            "use_cases": ["Security patrol", "Object tracking", "Area monitoring"]
                        }
                    ]
                },
                "video_streaming": {
                    "description": "Access live and recorded video streams",
                    "endpoints": [
                        {
                            "path": "mjpg/video.cgi",
                            "method": "GET",
                            "description": "MJPEG video stream",
                            "parameters": {
                                "resolution": "Video resolution (e.g., 1920x1080)",
                                "fps": "Frames per second (1-30)",
                                "compression": "Compression level (0-100)"
                            },
                            "example_request": "GET /axis-cgi/mjpg/video.cgi?resolution=1920x1080&fps=15",
                            "use_cases": ["Live monitoring", "Recording", "Motion detection"]
                        }
                    ]
                },
                "event_management": {
                    "description": "Configure and monitor camera events",
                    "endpoints": [
                        {
                            "path": "admin/param.cgi",
                            "method": "GET/POST",
                            "description": "Configure event parameters",
                            "parameters": {
                                "action": "list, update, remove",
                                "group": "Event group name",
                                "template": "Event template"
                            },
                            "example_request": "GET /axis-cgi/admin/param.cgi?action=list&group=Motion",
                            "use_cases": ["Motion detection setup", "Alarm configuration", "Event logging"]
                        }
                    ]
                }
            },
            "integration_patterns": [
                {
                    "name": "Security Monitoring Workflow",
                    "description": "Automated security patrol with multiple cameras",
                    "steps": [
                        "Query asset service for VAPIX-enabled cameras",
                        "Configure PTZ patrol routes for each camera",
                        "Set up motion detection events",
                        "Configure email notifications for security events",
                        "Schedule automated patrol using celery-beat"
                    ],
                    "services_used": ["asset-service", "automation-service", "communication-service", "celery-beat"]
                }
            ],
            "common_workflows": [
                "Camera discovery and inventory",
                "Live stream monitoring setup",
                "Motion detection configuration",
                "PTZ preset position management",
                "Event-driven recording",
                "Multi-camera coordination"
            ],
            "best_practices": [
                "Always authenticate before API calls",
                "Use HTTPS for secure communication",
                "Implement rate limiting to avoid camera overload",
                "Cache camera capabilities to reduce API calls",
                "Use appropriate video quality for bandwidth constraints"
            ]
        }
    
    async def discover_capabilities(self) -> APIDiscoveryResult:
        """Discover VAPIX capabilities from actual cameras"""
        # This would connect to cameras and discover their actual capabilities
        # For now, return the base knowledge structure
        return APIDiscoveryResult(
            endpoints=[],
            capabilities=list(self.base_knowledge["capabilities"].keys()),
            authentication_methods=self.base_knowledge["service_info"]["authentication"],
            rate_limits={"requests_per_minute": 60},
            documentation_urls=["https://www.axis.com/vapix-library"],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        """Get VAPIX context relevant to the request"""
        relevant_capabilities = []
        
        # Analyze keywords to determine relevant capabilities
        keyword_set = set(word.lower() for word in request_keywords)
        
        if any(word in keyword_set for word in ["camera", "video", "stream", "monitor"]):
            relevant_capabilities.append(self.base_knowledge["capabilities"]["video_streaming"])
        
        if any(word in keyword_set for word in ["pan", "tilt", "zoom", "ptz", "move", "control"]):
            relevant_capabilities.append(self.base_knowledge["capabilities"]["camera_control"])
        
        if any(word in keyword_set for word in ["motion", "event", "alarm", "detect"]):
            relevant_capabilities.append(self.base_knowledge["capabilities"]["event_management"])
        
        return {
            "domain": "VAPIX Camera Control",
            "relevant_capabilities": relevant_capabilities,
            "integration_patterns": self.base_knowledge["integration_patterns"],
            "service_info": self.base_knowledge["service_info"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        """Update VAPIX knowledge with discovered information"""
        try:
            # Merge new knowledge with existing
            if "capabilities" in new_knowledge:
                self.base_knowledge["capabilities"].update(new_knowledge["capabilities"])
            
            if "integration_patterns" in new_knowledge:
                self.base_knowledge["integration_patterns"].extend(new_knowledge["integration_patterns"])
            
            self.metadata.last_updated = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Failed to update VAPIX knowledge: {e}")
            return False

class DynamicServiceCatalog:
    """
    Dynamic, scalable service catalog with intelligent context management
    """
    
    def __init__(self, catalog_dir: str = "/home/opsconductor/opsconductor-ng/ai-brain/knowledge_domains"):
        self.catalog_dir = Path(catalog_dir)
        self.catalog_dir.mkdir(exist_ok=True)
        
        # Knowledge domains registry
        self.domains: Dict[str, KnowledgeDomain] = {}
        self.domain_metadata: Dict[str, KnowledgeMetadata] = {}
        
        # Context management
        self.context_cache = {}
        self.max_context_size = 50000  # Maximum context size in characters
        self.context_ttl = timedelta(hours=1)  # Context cache TTL
        
        # Performance tracking
        self.performance_metrics = {
            "context_generation_time": [],
            "domain_load_time": [],
            "cache_hit_rate": 0.0
        }
        
        # Initialize with core domains
        self._initialize_core_domains()
    
    def _initialize_core_domains(self):
        """Initialize core OpsConductor service domains"""
        try:
            # Load the enhanced service catalog as a core domain
            from enhanced_service_catalog import EnhancedServiceCatalog
            
            core_catalog = EnhancedServiceCatalog()
            self._register_core_services(core_catalog)
        except ImportError:
            logger.warning("Enhanced service catalog not available, skipping")
        
        try:
            # Register core service domains
            from core_knowledge_domains import register_core_domains
            register_core_domains(self)
        except ImportError:
            logger.warning("Core knowledge domains not available, skipping")
        
        try:
            # Register system expertise domains
            from system_expertise_domains import register_system_expertise_domains
            register_system_expertise_domains(self)
        except ImportError:
            logger.warning("System expertise domains not available, skipping")
        
        try:
            # Register PowerShell expertise domain
            from powershell_expertise_domain import register_powershell_expertise_domain
            register_powershell_expertise_domain(self)
        except ImportError:
            logger.warning("PowerShell expertise domain not available, skipping")
        
        # Register specialty domains
        self.register_domain(VAPIXDomain())
    
    def _register_core_services(self, enhanced_catalog):
        """Register core OpsConductor services as knowledge domains"""
        # This integrates our existing enhanced service catalog
        # as the foundation for the dynamic system
        pass
    
    def register_domain(self, domain: KnowledgeDomain):
        """Register a new knowledge domain"""
        self.domains[domain.domain_id] = domain
        self.domain_metadata[domain.domain_id] = domain.metadata
        logger.info(f"Registered knowledge domain: {domain.domain_id}")
    
    async def discover_domain_from_api(self, api_url: str, domain_name: str, 
                                     domain_type: KnowledgeDomainType = KnowledgeDomainType.SPECIALTY_API) -> bool:
        """
        Dynamically discover and register a new API domain
        This is the key method for learning new technical areas
        """
        try:
            # Attempt to discover API capabilities
            discovery_result = await self._perform_api_discovery(api_url)
            
            if discovery_result:
                # Create new domain from discovery
                new_domain = self._create_domain_from_discovery(
                    domain_name, domain_type, discovery_result
                )
                
                # Register the new domain
                self.register_domain(new_domain)
                
                # Persist the domain knowledge
                await self._persist_domain_knowledge(new_domain)
                
                logger.info(f"Successfully discovered and registered domain: {domain_name}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to discover domain {domain_name}: {e}")
        
        return False
    
    async def _perform_api_discovery(self, api_url: str) -> Optional[APIDiscoveryResult]:
        """Perform automated API discovery"""
        try:
            # Try common API discovery endpoints
            discovery_endpoints = [
                f"{api_url}/swagger.json",
                f"{api_url}/openapi.json",
                f"{api_url}/api-docs",
                f"{api_url}/docs",
                f"{api_url}/.well-known/api"
            ]
            
            for endpoint in discovery_endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        api_spec = response.json()
                        return self._parse_api_specification(api_spec)
                except:
                    continue
            
            # If no standard discovery, try basic endpoint enumeration
            return await self._enumerate_api_endpoints(api_url)
            
        except Exception as e:
            logger.error(f"API discovery failed for {api_url}: {e}")
            return None
    
    def _parse_api_specification(self, api_spec: Dict[str, Any]) -> APIDiscoveryResult:
        """Parse OpenAPI/Swagger specification"""
        endpoints = []
        capabilities = []
        
        # Parse OpenAPI 3.0 or Swagger 2.0 format
        if "paths" in api_spec:
            for path, methods in api_spec["paths"].items():
                for method, details in methods.items():
                    if isinstance(details, dict):
                        endpoints.append({
                            "path": path,
                            "method": method.upper(),
                            "description": details.get("description", ""),
                            "parameters": self._extract_parameters(details),
                            "responses": details.get("responses", {})
                        })
                        
                        # Extract capabilities from tags or operation IDs
                        if "tags" in details:
                            capabilities.extend(details["tags"])
        
        return APIDiscoveryResult(
            endpoints=endpoints,
            capabilities=list(set(capabilities)),
            authentication_methods=self._extract_auth_methods(api_spec),
            rate_limits={},
            documentation_urls=[],
            examples=[]
        )
    
    def _extract_parameters(self, endpoint_details: Dict[str, Any]) -> Dict[str, str]:
        """Extract parameter information from endpoint details"""
        parameters = {}
        
        if "parameters" in endpoint_details:
            for param in endpoint_details["parameters"]:
                param_name = param.get("name", "")
                param_desc = param.get("description", "")
                param_type = param.get("type", param.get("schema", {}).get("type", ""))
                parameters[param_name] = f"{param_desc} (type: {param_type})"
        
        return parameters
    
    def _extract_auth_methods(self, api_spec: Dict[str, Any]) -> List[str]:
        """Extract authentication methods from API specification"""
        auth_methods = []
        
        # Check security definitions
        security_defs = api_spec.get("securityDefinitions", api_spec.get("components", {}).get("securitySchemes", {}))
        
        for auth_name, auth_details in security_defs.items():
            auth_type = auth_details.get("type", "")
            if auth_type:
                auth_methods.append(auth_type)
        
        return auth_methods
    
    async def _enumerate_api_endpoints(self, api_url: str) -> APIDiscoveryResult:
        """Basic endpoint enumeration when no API spec is available"""
        # This would implement basic endpoint discovery
        # For now, return empty result
        return APIDiscoveryResult(
            endpoints=[],
            capabilities=[],
            authentication_methods=[],
            rate_limits={},
            documentation_urls=[],
            examples=[]
        )
    
    def _create_domain_from_discovery(self, domain_name: str, domain_type: KnowledgeDomainType, 
                                    discovery: APIDiscoveryResult) -> KnowledgeDomain:
        """Create a new knowledge domain from discovery results"""
        # This would create a dynamic domain class
        # For now, create a generic domain
        class DiscoveredDomain(KnowledgeDomain):
            def __init__(self, name: str, discovery_data: APIDiscoveryResult):
                metadata = KnowledgeMetadata(
                    domain_id=name.lower().replace(" ", "_"),
                    domain_type=domain_type,
                    version="1.0.0",
                    last_updated=datetime.now(),
                    size_bytes=len(str(discovery_data)),
                    priority=ContextPriority.MEDIUM,
                    keywords=discovery_data.capabilities,
                    dependencies=[],
                    performance_metrics={}
                )
                super().__init__(name, metadata)
                self.discovery_data = discovery_data
            
            async def discover_capabilities(self) -> APIDiscoveryResult:
                return self.discovery_data
            
            def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
                return {
                    "domain": self.domain_id,
                    "endpoints": self.discovery_data.endpoints,
                    "capabilities": self.discovery_data.capabilities
                }
            
            def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
                return True
        
        return DiscoveredDomain(domain_name, discovery)
    
    async def _persist_domain_knowledge(self, domain: KnowledgeDomain):
        """Persist domain knowledge to disk"""
        domain_file = self.catalog_dir / f"{domain.domain_id}.json"
        
        try:
            knowledge_data = {
                "metadata": asdict(domain.metadata),
                "knowledge": domain.get_context_for_request([])  # Get all knowledge
            }
            
            with open(domain_file, 'w') as f:
                json.dump(knowledge_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to persist domain {domain.domain_id}: {e}")
    
    def analyze_request_context_needs(self, request: str) -> Dict[str, Any]:
        """
        Analyze a request to determine which knowledge domains are needed
        This is the key intelligence for context optimization
        """
        request_lower = request.lower()
        request_words = request_lower.split()
        
        relevant_domains = []
        confidence_scores = {}
        
        # Analyze each domain for relevance
        for domain_id, domain in self.domains.items():
            metadata = self.domain_metadata[domain_id]
            
            # Calculate relevance score based on keyword matching
            keyword_matches = sum(1 for keyword in metadata.keywords 
                                if keyword.lower() in request_lower)
            
            if keyword_matches > 0:
                confidence = keyword_matches / len(metadata.keywords)
                confidence_scores[domain_id] = confidence
                
                if confidence > 0.1:  # Threshold for inclusion
                    relevant_domains.append({
                        "domain_id": domain_id,
                        "confidence": confidence,
                        "priority": metadata.priority.value,
                        "size_bytes": metadata.size_bytes
                    })
        
        # Sort by confidence and priority
        relevant_domains.sort(key=lambda x: (x["confidence"], -x["priority"]), reverse=True)
        
        return {
            "relevant_domains": relevant_domains,
            "confidence_scores": confidence_scores,
            "estimated_context_size": sum(d["size_bytes"] for d in relevant_domains),
            "request_keywords": request_words
        }
    
    def generate_optimized_context(self, request: str) -> str:
        """
        Generate optimized context for AI reasoning
        Only includes relevant knowledge domains within size limits
        """
        start_time = datetime.now()
        
        # Analyze what context is needed
        context_analysis = self.analyze_request_context_needs(request)
        
        context_parts = []
        current_size = 0
        
        # Always include core services (highest priority)
        core_context = self._get_core_services_context()
        context_parts.append(core_context)
        current_size += len(core_context)
        
        # Add relevant specialty domains within size limits
        for domain_info in context_analysis["relevant_domains"]:
            domain_id = domain_info["domain_id"]
            
            if current_size >= self.max_context_size:
                break
            
            if domain_id in self.domains:
                domain_context = self.domains[domain_id].get_context_for_request(
                    context_analysis["request_keywords"]
                )
                
                context_text = self._format_domain_context(domain_id, domain_context)
                
                if current_size + len(context_text) <= self.max_context_size:
                    context_parts.append(context_text)
                    current_size += len(context_text)
        
        # Track performance
        generation_time = (datetime.now() - start_time).total_seconds()
        self.performance_metrics["context_generation_time"].append(generation_time)
        
        return "\n\n".join(context_parts)
    
    def _get_core_services_context(self) -> str:
        """Get context for core OpsConductor services"""
        # This would integrate with the enhanced service catalog
        return """
CORE OPSCONDUCTOR SERVICES:

ASSET SERVICE (asset-service):
Purpose: Manage infrastructure assets, credentials, and system inventory
Key Capabilities: Asset discovery, credential management, target identification
API: GET /api/v1/assets?os_type=Windows&environment=production

AUTOMATION SERVICE (automation-service):
Purpose: Execute commands and workflows on remote systems
Key Capabilities: Remote command execution, workflow orchestration, multi-platform support
API: POST /api/v1/automation/execute

COMMUNICATION SERVICE (communication-service):
Purpose: Handle notifications, alerts, and communication workflows
Key Capabilities: Email notifications, template management, delivery tracking
API: POST /api/v1/communication/notify

CELERY-BEAT SCHEDULER:
Purpose: Schedule and manage recurring automation tasks
Key Capabilities: Cron scheduling, interval scheduling, task management
API: POST /api/v1/scheduler/schedule
        """
    
    def _format_domain_context(self, domain_id: str, context: Dict[str, Any]) -> str:
        """Format domain context for AI consumption"""
        formatted = f"\n{domain_id.upper().replace('_', ' ')} DOMAIN:\n"
        
        if "domain" in context:
            formatted += f"Purpose: {context['domain']}\n"
        
        if "relevant_capabilities" in context:
            formatted += "Capabilities:\n"
            for capability in context["relevant_capabilities"]:
                if isinstance(capability, dict) and "description" in capability:
                    formatted += f"- {capability['description']}\n"
        
        if "service_info" in context:
            service_info = context["service_info"]
            if "base_url_pattern" in service_info:
                formatted += f"Base URL: {service_info['base_url_pattern']}\n"
            if "authentication" in service_info:
                formatted += f"Authentication: {', '.join(service_info['authentication'])}\n"
        
        return formatted
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring and optimization"""
        return {
            "total_domains": len(self.domains),
            "average_context_generation_time": sum(self.performance_metrics["context_generation_time"]) / 
                                             max(len(self.performance_metrics["context_generation_time"]), 1),
            "cache_hit_rate": self.performance_metrics["cache_hit_rate"],
            "domain_types": {
                domain_type.value: sum(1 for metadata in self.domain_metadata.values() 
                                     if metadata.domain_type == domain_type)
                for domain_type in KnowledgeDomainType
            }
        }

# Global instance
dynamic_catalog = DynamicServiceCatalog()

def get_dynamic_catalog() -> DynamicServiceCatalog:
    """Get the global dynamic service catalog instance"""
    return dynamic_catalog
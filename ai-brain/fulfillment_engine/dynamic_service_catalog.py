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
    dependencies: List[str]
    performance_metrics: Dict[str, Any]
    keywords: List[str] = None

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
    def get_context_for_request(self, request_context: str) -> Dict[str, Any]:
        """Get relevant context for a specific request based on semantic understanding"""
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
                },
                "firmware_management": {
                    "description": "Check and manage camera firmware versions",
                    "endpoints": [
                        {
                            "path": "firmwaremanagement.cgi",
                            "method": "GET",
                            "description": "Get firmware version and status information",
                            "parameters": {
                                "action": "status",
                                "method": "status"
                            },
                            "example_request": "GET /axis-cgi/firmwaremanagement.cgi?action=status",
                            "response_format": {
                                "firmware_version": "Current firmware version",
                                "build_date": "Firmware build date",
                                "product_type": "Camera model information",
                                "serial_number": "Device serial number",
                                "hardware_id": "Hardware identifier"
                            },
                            "use_cases": ["Firmware version audit", "Security compliance", "Update planning", "Device inventory"]
                        }
                    ]
                },
                "device_information": {
                    "description": "Get device and system information",
                    "endpoints": [
                        {
                            "path": "admin/param.cgi",
                            "method": "GET",
                            "description": "Get device parameters and system information",
                            "parameters": {
                                "action": "list",
                                "group": "Properties.System, Properties.Firmware, Brand"
                            },
                            "example_request": "GET /axis-cgi/admin/param.cgi?action=list&group=Properties.System",
                            "response_includes": [
                                "System.SerialNumber",
                                "Properties.Firmware.Version",
                                "Properties.Firmware.BuildDate",
                                "Brand.ProdFullName",
                                "Brand.ProdType"
                            ],
                            "use_cases": ["Device discovery", "Asset inventory", "System monitoring"]
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
    
    def get_context_for_request(self, request_context: str) -> Dict[str, Any]:
        """Get VAPIX context relevant to the request based on semantic understanding"""
        # Return all capabilities - let the AI intelligently choose what's relevant
        return {
            "domain": "VAPIX Camera Control",
            "service_description": self.base_knowledge["service_info"]["description"],
            "capabilities": self.base_knowledge["capabilities"],
            "integration_patterns": self.base_knowledge["integration_patterns"],
            "service_info": self.base_knowledge["service_info"],
            "common_workflows": self.base_knowledge["common_workflows"],
            "best_practices": self.base_knowledge["best_practices"]
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
    
    def __init__(self, catalog_dir: str = None):
        if catalog_dir is None:
            # Use relative path from current working directory
            catalog_dir = os.path.join(os.getcwd(), "knowledge_domains")
        self.catalog_dir = Path(catalog_dir)
        self.catalog_dir.mkdir(exist_ok=True)
        
        # Knowledge domains registry
        self.domains: Dict[str, KnowledgeDomain] = {}
        self.domain_metadata: Dict[str, KnowledgeMetadata] = {}
        
        # Context management
        self.context_cache = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Initialize core domains
        self._initialize_core_domains()
    
    def _initialize_core_domains(self):
        """Initialize core knowledge domains"""
        # Add VAPIX domain
        vapix_domain = VAPIXDomain()
        self.register_domain(vapix_domain)
        
        # Register core OpsConductor service domains
        try:
            import os
            import sys
            # Add the fulfillment_engine directory to path for imports
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            
            from core_knowledge_domains import register_core_domains
            register_core_domains(self)
            logger.info("Registered core OpsConductor service domains")
        except ImportError as e:
            logger.warning(f"Could not load core domains: {e}")
        
        # Register system expertise domains
        try:
            from system_expertise_domains import register_system_expertise_domains
            register_system_expertise_domains(self)
            logger.info("Registered system expertise domains")
        except ImportError as e:
            logger.warning(f"Could not load system expertise domains: {e}")
        
        # Register PowerShell expertise domain
        try:
            from powershell_expertise_domain import register_powershell_expertise_domain
            register_powershell_expertise_domain(self)
            logger.info("Registered PowerShell expertise domain")
        except ImportError as e:
            logger.warning(f"Could not load PowerShell expertise domain: {e}")
        
        logger.info(f"Initialized {len(self.domains)} knowledge domains")
    
    def register_domain(self, domain: KnowledgeDomain):
        """Register a new knowledge domain"""
        self.domains[domain.domain_id] = domain
        self.domain_metadata[domain.domain_id] = domain.metadata
        logger.info(f"Registered domain: {domain.domain_id}")
    
    async def discover_new_capabilities(self, domain_id: str) -> bool:
        """Discover new capabilities for a domain"""
        if domain_id not in self.domains:
            return False
        
        try:
            domain = self.domains[domain_id]
            discovery_result = await domain.discover_capabilities()
            
            # Update domain with discovered capabilities
            new_knowledge = {
                "discovered_endpoints": discovery_result.endpoints,
                "discovered_capabilities": discovery_result.capabilities
            }
            
            return domain.update_knowledge(new_knowledge)
        except Exception as e:
            logger.error(f"Failed to discover capabilities for {domain_id}: {e}")
            return False
    
    def get_relevant_context(self, request_description: str, max_domains: int = 3) -> Dict[str, Any]:
        """
        Get relevant context for a request using intelligent semantic analysis
        """
        # Cache key based on request description
        cache_key = hashlib.md5(request_description.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.context_cache:
            cached_result, timestamp = self.context_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_result
        
        # Analyze request and determine relevant domains
        relevant_domains = self._analyze_request_relevance(request_description)
        
        # Get context from top domains
        context = {
            "request_analysis": {
                "description": request_description,
                "timestamp": datetime.now().isoformat(),
                "relevant_domains": [d["domain_id"] for d in relevant_domains[:max_domains]]
            },
            "domain_contexts": {}
        }
        
        for domain_info in relevant_domains[:max_domains]:
            domain_id = domain_info["domain_id"]
            domain = self.domains[domain_id]
            
            domain_context = domain.get_context_for_request(request_description)
            context["domain_contexts"][domain_id] = domain_context
        
        # Cache result
        self.context_cache[cache_key] = (context, datetime.now())
        
        return context
    
    def _analyze_request_relevance(self, request_description: str) -> List[Dict[str, Any]]:
        """
        Analyze request and determine domain relevance using semantic understanding
        """
        request_lower = request_description.lower()
        domain_scores = []
        
        for domain_id, domain in self.domains.items():
            score = self._calculate_domain_relevance(request_lower, domain)
            
            domain_scores.append({
                "domain_id": domain_id,
                "relevance_score": score,
                "domain_type": domain.metadata.domain_type.value,
                "priority": domain.metadata.priority.value
            })
        
        # Sort by relevance score and priority
        domain_scores.sort(key=lambda x: (x["relevance_score"], -x["priority"]), reverse=True)
        
        return domain_scores
    
    def _calculate_domain_relevance(self, request_text: str, domain: KnowledgeDomain) -> float:
        """
        Calculate domain relevance based on semantic understanding of capabilities
        """
        if isinstance(domain, VAPIXDomain):
            # Check if request relates to cameras, video, surveillance, firmware, etc.
            camera_indicators = [
                "camera", "video", "surveillance", "axis", "vapix", "stream", "monitor",
                "firmware", "version", "device", "ptz", "pan", "tilt", "zoom", "motion",
                "event", "alarm", "recording"
            ]
            
            matches = sum(1 for indicator in camera_indicators if indicator in request_text)
            return matches / len(camera_indicators) if camera_indicators else 0.0
        
        # Default scoring for unknown domains
        return 0.0
    
    def get_domain_list(self) -> List[Dict[str, Any]]:
        """Get list of all registered domains"""
        return [
            {
                "domain_id": domain_id,
                "domain_type": metadata.domain_type.value,
                "version": metadata.version,
                "priority": metadata.priority.value,
                "last_updated": metadata.last_updated.isoformat()
            }
            for domain_id, metadata in self.domain_metadata.items()
        ]
    
    async def refresh_all_domains(self):
        """Refresh capabilities for all domains"""
        tasks = []
        for domain_id in self.domains.keys():
            tasks.append(self.discover_new_capabilities(domain_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for result in results if result is True)
        logger.info(f"Refreshed {successful}/{len(tasks)} domains successfully")
    
    def clear_cache(self):
        """Clear the context cache"""
        self.context_cache.clear()
        logger.info("Context cache cleared")
    
    def generate_intelligent_service_selection_prompt(self) -> str:
        """Generate comprehensive service selection prompt with intelligent decision guidance"""
        prompt = """# OpsConductor Dynamic Service Catalog

You have access to the following specialized services. Analyze the NATURE and COMPLEXITY of each task to choose the OPTIMAL service:

## 🌐 NETWORK-ANALYZER-SERVICE (Port: 3006)
**BEST FOR**: Network diagnostics, connectivity testing, packet analysis
**NETWORK ACCESS**: Direct host network (can reach any IP/port)
**USE FOR**: ping, traceroute, port scanning, packet capture, network monitoring, protocol analysis
**CAPABILITIES**:
- Advanced network diagnostics (ping, traceroute, nmap)
- Real-time packet capture and analysis
- Protocol-specific analysis (TCP, UDP, HTTP, DNS)
- AI-powered network troubleshooting
- Network interface monitoring
**WHEN TO USE**: ANY network-related task
**API**: /api/v1/diagnostics/ping, /api/v1/analysis/start-capture

## 🤖 AUTOMATION-SERVICE (Port: 3003) - FAST & SIMPLE
**BEST FOR**: Immediate execution, simple operations, basic scheduling
**NETWORK ACCESS**: Container network (through nginx proxy)
**EXECUTION STYLE**: Fast response (< 1 second), direct execution, real-time monitoring
**IDEAL FOR**:
- **Single commands**: restart service, check status, run script, file operations
- **Simple sequential workflows**: stop → update → start (linear, predictable steps)
- **System administration**: service management, file operations, user management
- **Basic scheduling**: recurring tasks with simple time-based triggers (cron-like)
- **Remote execution**: SSH/PowerShell commands on target systems
- **Immediate needs**: when you need fast execution without complex orchestration

**SCHEDULING CAPABILITIES**: 
- Simple Celery Beat scheduling for regular maintenance and housekeeping
- Time-based recurring tasks (hourly, daily, weekly)
- Independent tasks that don't require complex coordination

**CHOOSE AUTOMATION-SERVICE WHEN**:
- Task is self-contained and straightforward
- You need immediate execution with fast response
- Simple sequential steps without complex branching
- Basic recurring schedules (like cron jobs)
- System administration and maintenance tasks
- The task doesn't require sophisticated error handling or recovery

**API**: /api/v1/jobs, /api/v1/executions, /api/v1/schedules

## 🔄 PREFECT-FLOW-REGISTRY (Port: 4201) - ENTERPRISE ORCHESTRATION
**BEST FOR**: Complex workflows, enterprise orchestration, sophisticated automation
**EXECUTION STYLE**: Enterprise-grade with advanced features, detailed monitoring, sophisticated coordination
**IDEAL FOR**:
- **Complex workflows**: Multi-step processes with conditional branching and parallel execution
- **Advanced scheduling**: Event-driven triggers, external system integration, conditional scheduling
- **Enterprise orchestration**: Workflows requiring rollback, recovery, and audit trails
- **Sophisticated coordination**: Cross-system workflows with complex dependencies
- **Mission-critical processes**: Workflows requiring guaranteed execution and detailed monitoring

**ORCHESTRATION CAPABILITIES**:
- Conditional branching and dynamic workflow generation
- Parallel execution with coordination and synchronization
- Advanced error handling with automatic retries and custom recovery
- Event-driven triggers and external system integration
- Workflow versioning, templates, and governance
- Comprehensive monitoring and debugging capabilities

**CHOOSE PREFECT-FLOW-REGISTRY WHEN**:
- Workflow has complex conditional logic or branching
- You need sophisticated error handling and recovery
- Tasks have complex dependencies between steps
- Advanced scheduling with event triggers or external conditions
- Enterprise-grade monitoring and audit requirements
- Workflow requires rollback or recovery capabilities
- Visual workflow monitoring and debugging is needed

**API**: /api/v1/flows, /api/v1/flows/{flow_id}/execute, /api/v1/schedules/advanced

## 📦 ASSET-SERVICE (Port: 3002)
**BEST FOR**: Asset management, credential storage, system inventory
**USE FOR**: managing infrastructure assets, storing credentials, system discovery
**CAPABILITIES**:
- Comprehensive asset inventory
- Secure credential management
- Target system management
- Asset discovery and cataloging
**WHEN TO USE**: Asset management, credential operations, system inventory
**API**: /api/v1/assets, /api/v1/credentials

## 📢 COMMUNICATION-SERVICE (Port: 3004)
**BEST FOR**: Notifications, alerts, external integrations
**USE FOR**: sending notifications, alerts, reports, third-party integrations
**CAPABILITIES**:
- Multi-channel notifications (email, SMS, Slack)
- Template-based messaging
- External API integrations
- Delivery tracking
**WHEN TO USE**: Sending notifications or integrating with external systems
**API**: /api/v1/notifications, /api/v1/templates

## 🔐 IDENTITY-SERVICE (Port: 3001)
**BEST FOR**: Authentication and authorization
**USE FOR**: user management, authentication, access control
**CAPABILITIES**:
- User authentication via Keycloak
- Authorization and access control
- JWT token management
- User account management
**WHEN TO USE**: User authentication, access control, identity management
**API**: /api/v1/auth/login, /api/v1/users

## INTELLIGENT SERVICE SELECTION GUIDELINES:

### 🎯 SCHEDULING DECISION MATRIX:

**USE AUTOMATION-SERVICE (Celery Beat) FOR**:
- Simple time-based recurring tasks (every hour, daily, weekly)
- Independent maintenance tasks (log cleanup, health checks)
- Basic housekeeping operations (backup single system, status reports)
- Tasks that run independently without complex coordination
- When you need fast, lightweight scheduling without overhead

**USE PREFECT-FLOW-REGISTRY FOR**:
- Complex scheduling with multiple conditions and dependencies
- Event-driven workflows triggered by external systems
- Workflows requiring coordination between multiple systems
- Advanced scheduling that adapts based on system state
- When you need sophisticated monitoring and workflow visualization

### 🎯 EXECUTION DECISION MATRIX:

**USE AUTOMATION-SERVICE FOR**:
- Single command execution (restart service, check status)
- Simple sequential operations (stop → update → start)
- System administration tasks (file operations, service management)
- When speed and simplicity are priorities
- Self-contained tasks without complex dependencies

**USE PREFECT-FLOW-REGISTRY FOR**:
- Multi-step workflows with conditional logic
- Parallel processing with coordination requirements
- Workflows requiring rollback and recovery capabilities
- Enterprise processes with audit and compliance needs
- Complex orchestration across multiple systems and services

### 🎯 CORE SELECTION RULES:

1. **NETWORK TASKS** → ALWAYS use network-analyzer-service
2. **ASSET DISCOVERY** → ALWAYS start with asset-service for "all [type] systems"
3. **SIMPLE & FAST** → automation-service (immediate execution, basic scheduling)
4. **COMPLEX & SOPHISTICATED** → prefect-flow-registry (enterprise orchestration)
5. **NOTIFICATIONS** → communication-service
6. **AUTHENTICATION** → identity-service

**DECISION PRINCIPLE**: Choose based on COMPLEXITY and REQUIREMENTS, not just keywords!

### 🎯 SPECIALTY DOMAINS:

**VAPIX CAMERAS**: For Axis camera control, video streaming, PTZ operations, firmware management
**SYSTEM EXPERTISE**: Linux, Windows, PowerShell knowledge for platform-specific operations
**LEARNED CAPABILITIES**: AI-discovered patterns and workflows (expandable)
"""
        return prompt

# Global catalog instance
_catalog_instance = None

def get_service_catalog() -> DynamicServiceCatalog:
    """Get the global service catalog instance"""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = DynamicServiceCatalog()
    return _catalog_instance

# Example usage and testing
if __name__ == "__main__":
    async def test_catalog():
        catalog = get_service_catalog()
        
        # Test context retrieval
        context = catalog.get_relevant_context("check firmware version on all axis cameras")
        print(json.dumps(context, indent=2, default=str))
        
        # Test domain discovery
        await catalog.refresh_all_domains()
        
        # List domains
        domains = catalog.get_domain_list()
        print(f"Registered domains: {len(domains)}")
        for domain in domains:
            print(f"  - {domain['domain_id']} ({domain['domain_type']})")
    
    asyncio.run(test_catalog())
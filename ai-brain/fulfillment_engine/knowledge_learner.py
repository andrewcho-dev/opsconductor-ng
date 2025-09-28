#!/usr/bin/env python3
"""
Knowledge Learning Interface
Provides easy methods to teach the AI about new technical domains
"""

import asyncio
import json
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from datetime import datetime

from .dynamic_service_catalog import (
    DynamicServiceCatalog, 
    KnowledgeDomainType, 
    ContextPriority,
    get_dynamic_catalog
)

logger = logging.getLogger(__name__)

class KnowledgeLearner:
    """
    Interface for teaching the AI about new technical domains
    """
    
    def __init__(self):
        self.catalog = get_dynamic_catalog()
        self.learning_templates = self._load_learning_templates()
    
    def _load_learning_templates(self) -> Dict[str, Any]:
        """Load templates for common API types"""
        return {
            "rest_api": {
                "discovery_methods": ["swagger", "openapi", "api-docs"],
                "common_endpoints": ["/api", "/v1", "/docs", "/swagger.json"],
                "authentication_patterns": ["bearer", "basic", "api-key", "oauth2"]
            },
            "device_api": {
                "discovery_methods": ["upnp", "mdns", "snmp"],
                "common_ports": [80, 443, 8080, 8443],
                "protocol_patterns": ["http", "https", "soap", "rest"]
            },
            "cloud_service": {
                "discovery_methods": ["service_discovery", "api_catalog"],
                "authentication_patterns": ["oauth2", "iam", "service_account"],
                "rate_limiting": True
            }
        }
    
    async def learn_from_api_url(self, api_url: str, domain_name: str, 
                                domain_description: str = "", 
                                keywords: List[str] = None) -> bool:
        """
        Learn about a new API from its URL
        
        Args:
            api_url: Base URL of the API
            domain_name: Human-readable name for the domain
            domain_description: Description of what this API does
            keywords: Keywords that should trigger this domain
        
        Returns:
            bool: True if learning was successful
        """
        try:
            logger.info(f"Learning from API: {api_url}")
            
            # Attempt automatic discovery
            success = await self.catalog.discover_domain_from_api(
                api_url, domain_name, KnowledgeDomainType.SPECIALTY_API
            )
            
            if success and keywords:
                # Update domain with additional keywords
                domain_id = domain_name.lower().replace(" ", "_")
                if domain_id in self.catalog.domains:
                    domain = self.catalog.domains[domain_id]
                    domain.metadata.keywords.extend(keywords)
                    domain.metadata.keywords = list(set(domain.metadata.keywords))  # Remove duplicates
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to learn from API {api_url}: {e}")
            return False
    
    def learn_from_documentation(self, domain_name: str, documentation: Dict[str, Any], 
                                keywords: List[str] = None) -> bool:
        """
        Learn about a new domain from structured documentation
        
        Args:
            domain_name: Name of the domain
            documentation: Structured documentation (see example below)
            keywords: Keywords that should trigger this domain
        
        Documentation format:
        {
            "description": "What this API/service does",
            "base_url": "Base URL pattern",
            "authentication": ["method1", "method2"],
            "capabilities": {
                "capability_name": {
                    "description": "What this capability does",
                    "endpoints": [
                        {
                            "path": "/api/endpoint",
                            "method": "GET",
                            "description": "Endpoint description",
                            "parameters": {"param": "description"},
                            "example": "Example usage"
                        }
                    ],
                    "use_cases": ["use case 1", "use case 2"]
                }
            },
            "integration_patterns": [
                {
                    "name": "Pattern name",
                    "description": "How to use this with OpsConductor",
                    "steps": ["step 1", "step 2"],
                    "services_used": ["service1", "service2"]
                }
            ]
        }
        """
        try:
            from .dynamic_service_catalog import KnowledgeDomain, KnowledgeMetadata
            
            # Create a custom domain from documentation
            class DocumentedDomain(KnowledgeDomain):
                def __init__(self, name: str, doc: Dict[str, Any], kw: List[str]):
                    domain_id = name.lower().replace(" ", "_")
                    metadata = KnowledgeMetadata(
                        domain_id=domain_id,
                        domain_type=KnowledgeDomainType.SPECIALTY_API,
                        version="1.0.0",
                        last_updated=datetime.now(),
                        size_bytes=len(str(doc)),
                        priority=ContextPriority.HIGH,
                        keywords=kw or [],
                        dependencies=[],
                        performance_metrics={}
                    )
                    super().__init__(domain_id, metadata)
                    self.documentation = doc
                
                async def discover_capabilities(self):
                    from .dynamic_service_catalog import APIDiscoveryResult
                    return APIDiscoveryResult(
                        endpoints=[],
                        capabilities=list(self.documentation.get("capabilities", {}).keys()),
                        authentication_methods=self.documentation.get("authentication", []),
                        rate_limits={},
                        documentation_urls=[],
                        examples=[]
                    )
                
                def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
                    # Analyze which capabilities are relevant
                    relevant_capabilities = []
                    keyword_set = set(word.lower() for word in request_keywords)
                    
                    for cap_name, cap_info in self.documentation.get("capabilities", {}).items():
                        # Check if any capability keywords match request
                        cap_keywords = cap_info.get("keywords", []) + [cap_name]
                        if any(kw.lower() in keyword_set for kw in cap_keywords):
                            relevant_capabilities.append({
                                "name": cap_name,
                                "info": cap_info
                            })
                    
                    return {
                        "domain": self.documentation.get("description", domain_name),
                        "base_url": self.documentation.get("base_url", ""),
                        "authentication": self.documentation.get("authentication", []),
                        "relevant_capabilities": relevant_capabilities,
                        "integration_patterns": self.documentation.get("integration_patterns", [])
                    }
                
                def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
                    try:
                        # Merge new knowledge
                        if "capabilities" in new_knowledge:
                            if "capabilities" not in self.documentation:
                                self.documentation["capabilities"] = {}
                            self.documentation["capabilities"].update(new_knowledge["capabilities"])
                        
                        self.metadata.last_updated = datetime.now()
                        return True
                    except Exception as e:
                        logger.error(f"Failed to update knowledge: {e}")
                        return False
            
            # Create and register the domain
            domain = DocumentedDomain(domain_name, documentation, keywords or [])
            self.catalog.register_domain(domain)
            
            # Persist the knowledge
            asyncio.create_task(self.catalog._persist_domain_knowledge(domain))
            
            logger.info(f"Successfully learned domain: {domain_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn from documentation: {e}")
            return False
    
    def learn_vapix_cameras(self) -> bool:
        """
        Example: Learn about VAPIX camera APIs
        This demonstrates how to add comprehensive knowledge about a technical domain
        """
        vapix_documentation = {
            "description": "Axis Camera VAPIX API for video surveillance and camera control",
            "base_url": "http://{camera_ip}/axis-cgi/",
            "authentication": ["basic", "digest"],
            "capabilities": {
                "ptz_control": {
                    "description": "Pan, tilt, zoom camera control",
                    "keywords": ["pan", "tilt", "zoom", "ptz", "move", "position"],
                    "endpoints": [
                        {
                            "path": "com/ptz.cgi",
                            "method": "GET",
                            "description": "Control camera movement",
                            "parameters": {
                                "camera": "Camera number (1-4)",
                                "pan": "Pan position (-180 to 180)",
                                "tilt": "Tilt position (-180 to 180)",
                                "zoom": "Zoom level (1-9999)"
                            },
                            "example": "GET /axis-cgi/com/ptz.cgi?camera=1&pan=45&tilt=30&zoom=1000"
                        }
                    ],
                    "use_cases": ["Security patrol", "Object tracking", "Area monitoring"]
                },
                "video_streaming": {
                    "description": "Access live and recorded video streams",
                    "keywords": ["video", "stream", "mjpeg", "rtsp", "live", "recording"],
                    "endpoints": [
                        {
                            "path": "mjpg/video.cgi",
                            "method": "GET",
                            "description": "MJPEG video stream",
                            "parameters": {
                                "resolution": "Video resolution (e.g., 1920x1080)",
                                "fps": "Frames per second (1-30)"
                            },
                            "example": "GET /axis-cgi/mjpg/video.cgi?resolution=1920x1080&fps=15"
                        }
                    ],
                    "use_cases": ["Live monitoring", "Recording", "Motion detection"]
                },
                "event_management": {
                    "description": "Configure and monitor camera events",
                    "keywords": ["motion", "event", "alarm", "detection", "trigger"],
                    "endpoints": [
                        {
                            "path": "admin/param.cgi",
                            "method": "GET/POST",
                            "description": "Configure event parameters",
                            "parameters": {
                                "action": "list, update, remove",
                                "group": "Event group name"
                            },
                            "example": "GET /axis-cgi/admin/param.cgi?action=list&group=Motion"
                        }
                    ],
                    "use_cases": ["Motion detection setup", "Alarm configuration"]
                }
            },
            "integration_patterns": [
                {
                    "name": "Automated Security Patrol",
                    "description": "Set up automated camera patrol with motion detection",
                    "steps": [
                        "Query asset service for VAPIX cameras",
                        "Configure PTZ patrol routes",
                        "Set up motion detection events",
                        "Configure email notifications for events",
                        "Schedule patrol using celery-beat"
                    ],
                    "services_used": ["asset-service", "automation-service", "communication-service", "celery-beat"]
                }
            ]
        }
        
        keywords = ["camera", "vapix", "axis", "video", "surveillance", "ptz", "stream", "motion"]
        
        return self.learn_from_documentation("VAPIX Cameras", vapix_documentation, keywords)
    
    def learn_aws_services(self) -> bool:
        """
        Example: Learn about AWS services
        """
        aws_documentation = {
            "description": "Amazon Web Services cloud platform APIs",
            "base_url": "https://{service}.{region}.amazonaws.com/",
            "authentication": ["aws_signature_v4", "iam_roles", "access_keys"],
            "capabilities": {
                "ec2_management": {
                    "description": "Manage EC2 instances and resources",
                    "keywords": ["ec2", "instance", "server", "vm", "compute"],
                    "endpoints": [
                        {
                            "path": "/",
                            "method": "POST",
                            "description": "EC2 API actions",
                            "parameters": {
                                "Action": "API action (e.g., DescribeInstances)",
                                "Version": "API version"
                            },
                            "example": "Action=DescribeInstances&Version=2016-11-15"
                        }
                    ],
                    "use_cases": ["Instance management", "Auto-scaling", "Resource monitoring"]
                },
                "s3_storage": {
                    "description": "Simple Storage Service for object storage",
                    "keywords": ["s3", "storage", "bucket", "object", "file"],
                    "endpoints": [
                        {
                            "path": "/{bucket}/{key}",
                            "method": "GET/PUT/DELETE",
                            "description": "Object operations",
                            "parameters": {
                                "bucket": "S3 bucket name",
                                "key": "Object key/path"
                            },
                            "example": "GET /my-bucket/path/to/file.txt"
                        }
                    ],
                    "use_cases": ["File storage", "Backup", "Static website hosting"]
                }
            },
            "integration_patterns": [
                {
                    "name": "Cloud Resource Management",
                    "description": "Manage AWS resources through OpsConductor",
                    "steps": [
                        "Configure AWS credentials in asset service",
                        "Use automation service to execute AWS CLI commands",
                        "Set up monitoring for resource changes",
                        "Configure cost alerts via communication service"
                    ],
                    "services_used": ["asset-service", "automation-service", "communication-service"]
                }
            ]
        }
        
        keywords = ["aws", "amazon", "cloud", "ec2", "s3", "lambda", "rds"]
        
        return self.learn_from_documentation("AWS Services", aws_documentation, keywords)
    
    def get_learning_suggestions(self, request: str) -> List[Dict[str, Any]]:
        """
        Analyze a request and suggest what new knowledge domains might be helpful
        """
        suggestions = []
        request_lower = request.lower()
        
        # Common technology patterns that might need learning
        tech_patterns = {
            "docker": {
                "description": "Docker container management APIs",
                "keywords": ["docker", "container", "image", "registry"],
                "learning_method": "api_discovery",
                "api_url": "unix:///var/run/docker.sock"  # Docker daemon socket
            },
            "kubernetes": {
                "description": "Kubernetes cluster management APIs",
                "keywords": ["kubernetes", "k8s", "pod", "deployment", "service"],
                "learning_method": "api_discovery",
                "api_url": "https://kubernetes.default.svc"
            },
            "vmware": {
                "description": "VMware vSphere management APIs",
                "keywords": ["vmware", "vsphere", "vcenter", "esxi"],
                "learning_method": "documentation",
                "documentation_url": "https://developer.vmware.com/apis"
            },
            "cisco": {
                "description": "Cisco network device APIs",
                "keywords": ["cisco", "switch", "router", "ios", "nexus"],
                "learning_method": "snmp_discovery"
            }
        }
        
        for tech, info in tech_patterns.items():
            if any(keyword in request_lower for keyword in info["keywords"]):
                # Check if we already know about this technology
                domain_exists = any(
                    any(keyword in domain.metadata.keywords for keyword in info["keywords"])
                    for domain in self.catalog.domains.values()
                )
                
                if not domain_exists:
                    suggestions.append({
                        "technology": tech,
                        "description": info["description"],
                        "learning_method": info["learning_method"],
                        "confidence": sum(1 for kw in info["keywords"] if kw in request_lower) / len(info["keywords"]),
                        "info": info
                    })
        
        return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)
    
    def list_known_domains(self) -> List[Dict[str, Any]]:
        """List all currently known knowledge domains"""
        domains = []
        
        for domain_id, domain in self.catalog.domains.items():
            metadata = domain.metadata
            domains.append({
                "domain_id": domain_id,
                "type": metadata.domain_type.value,
                "keywords": metadata.keywords,
                "last_updated": metadata.last_updated.isoformat(),
                "size_bytes": metadata.size_bytes,
                "priority": metadata.priority.value
            })
        
        return domains
    
    def export_domain_knowledge(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Export knowledge for a specific domain"""
        if domain_id in self.catalog.domains:
            domain = self.catalog.domains[domain_id]
            return {
                "metadata": {
                    "domain_id": domain.metadata.domain_id,
                    "type": domain.metadata.domain_type.value,
                    "version": domain.metadata.version,
                    "keywords": domain.metadata.keywords
                },
                "knowledge": domain.get_context_for_request([])  # Get all knowledge
            }
        return None

# Global instance
knowledge_learner = KnowledgeLearner()

def get_knowledge_learner() -> KnowledgeLearner:
    """Get the global knowledge learner instance"""
    return knowledge_learner
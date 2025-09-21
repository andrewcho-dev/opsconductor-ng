"""
OpsConductor AI System Capabilities and Self-Awareness Module

This module provides the AI assistant with comprehensive knowledge about:
- Its own capabilities and limitations
- Available tools and services
- System architecture and components
- Supported operations and protocols
"""

import json
import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = structlog.get_logger()

@dataclass
class ServiceCapability:
    """Represents a capability of a service"""
    name: str
    description: str
    endpoints: List[str]
    supported_operations: List[str]
    protocols: List[str] = None
    status: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SystemComponent:
    """Represents a system component"""
    name: str
    type: str  # "service", "database", "cache", "proxy"
    description: str
    port: int
    health_endpoint: str = None
    capabilities: List[ServiceCapability] = None
    dependencies: List[str] = None
    status: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.capabilities:
            result['capabilities'] = [cap.to_dict() for cap in self.capabilities]
        return result

class SystemCapabilitiesManager:
    """Manages system capabilities and self-awareness"""
    
    def __init__(self):
        self.components = {}
        self.capabilities = {}
        self.protocols = {}
        self.tools = {}
        self.last_updated = None
        self.system_status = "unknown"
        
    async def initialize(self):
        """Initialize system capabilities knowledge"""
        logger.info("Initializing system capabilities manager...")
        
        # Define core system components
        await self._define_core_components()
        
        # Define AI capabilities
        await self._define_ai_capabilities()
        
        # Define supported protocols
        await self._define_supported_protocols()
        
        # Define available tools
        await self._define_available_tools()
        
        # Check system health
        await self._check_system_health()
        
        self.last_updated = datetime.now()
        logger.info("System capabilities manager initialized successfully")
    
    async def _define_core_components(self):
        """Define all system components"""
        
        # Frontend
        self.components['frontend'] = SystemComponent(
            name="Frontend Web Interface",
            type="service",
            description="React TypeScript web application with Material-UI",
            port=3100,
            health_endpoint="/",
            capabilities=[
                ServiceCapability(
                    name="Web Interface",
                    description="Modern web interface for system management",
                    endpoints=["/", "/targets", "/jobs", "/automation", "/ai-chat"],
                    supported_operations=["user_interface", "dashboard", "forms", "real_time_updates"]
                )
            ],
            dependencies=["api-gateway"]
        )
        
        # API Gateway
        self.components['api-gateway'] = SystemComponent(
            name="API Gateway",
            type="service",
            description="Central routing, authentication, and rate limiting",
            port=3000,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="API Routing",
                    description="Routes requests to appropriate microservices",
                    endpoints=["/api/v1/*"],
                    supported_operations=["routing", "authentication", "rate_limiting", "load_balancing"]
                )
            ],
            dependencies=["identity-service", "asset-service", "automation-service", "communication-service", "ai-brain"]
        )
        
        # Identity Service
        self.components['identity-service'] = SystemComponent(
            name="Identity Service",
            type="service",
            description="User management, RBAC, JWT authentication",
            port=3001,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Authentication",
                    description="JWT-based user authentication and session management",
                    endpoints=["/auth/login", "/auth/logout", "/auth/refresh"],
                    supported_operations=["login", "logout", "token_refresh", "session_management"]
                ),
                ServiceCapability(
                    name="User Management",
                    description="Complete user lifecycle management",
                    endpoints=["/users", "/users/{id}", "/users/{id}/roles"],
                    supported_operations=["create_user", "update_user", "delete_user", "list_users", "manage_roles"]
                ),
                ServiceCapability(
                    name="RBAC",
                    description="Role-based access control with 5 predefined roles",
                    endpoints=["/roles", "/permissions"],
                    supported_operations=["role_assignment", "permission_check", "access_control"]
                )
            ],
            dependencies=["postgres", "redis"]
        )
        
        # Asset Service
        self.components['asset-service'] = SystemComponent(
            name="Asset Service",
            type="service",
            description="Infrastructure targets with embedded credentials and hierarchical groups",
            port=3002,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Target Management",
                    description="Manage infrastructure targets with embedded credentials",
                    endpoints=["/targets", "/targets/{id}", "/targets/search"],
                    supported_operations=["create_target", "update_target", "delete_target", "list_targets", "search_targets"]
                ),
                ServiceCapability(
                    name="Group Management",
                    description="Hierarchical target organization (3 levels)",
                    endpoints=["/groups", "/groups/{id}/targets"],
                    supported_operations=["create_group", "manage_hierarchy", "group_membership"]
                ),
                ServiceCapability(
                    name="Service Definitions",
                    description="31+ predefined service types (SSH, RDP, HTTP, databases, etc.)",
                    endpoints=["/service-definitions"],
                    supported_operations=["service_discovery", "protocol_mapping", "connection_testing"]
                ),
                ServiceCapability(
                    name="Credential Management",
                    description="Encrypted credential storage with Fernet encryption",
                    endpoints=["/targets/{id}/credentials"],
                    supported_operations=["store_credentials", "retrieve_credentials", "encrypt_decrypt"]
                )
            ],
            dependencies=["postgres", "redis"]
        )
        
        # Automation Service
        self.components['automation-service'] = SystemComponent(
            name="Automation Service",
            type="service",
            description="Job execution with Celery workers and step libraries",
            port=3003,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Job Execution",
                    description="Execute automation jobs with real-time monitoring",
                    endpoints=["/jobs", "/jobs/{id}/execute", "/executions"],
                    supported_operations=["create_job", "execute_job", "monitor_execution", "job_scheduling"]
                ),
                ServiceCapability(
                    name="Workflow Management",
                    description="Multi-step workflow orchestration",
                    endpoints=["/workflows", "/workflows/{id}/steps"],
                    supported_operations=["create_workflow", "step_execution", "workflow_monitoring"]
                ),
                ServiceCapability(
                    name="Step Libraries",
                    description="Reusable automation steps for different protocols",
                    endpoints=["/step-libraries"],
                    supported_operations=["ssh_commands", "powershell_scripts", "http_requests", "database_queries"],
                    protocols=["SSH", "PowerShell", "HTTP", "SNMP", "Database"]
                ),
                ServiceCapability(
                    name="Task Queue",
                    description="Celery-based distributed task processing",
                    endpoints=["/queue/status", "/workers"],
                    supported_operations=["task_queuing", "worker_management", "task_monitoring"]
                )
            ],
            dependencies=["postgres", "redis", "celery"]
        )
        
        # Communication Service
        self.components['communication-service'] = SystemComponent(
            name="Communication Service",
            type="service",
            description="Notifications, templates, and audit logging",
            port=3004,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Notifications",
                    description="Multi-channel notification system",
                    endpoints=["/notifications", "/notifications/send"],
                    supported_operations=["send_email", "send_slack", "send_webhook", "notification_templates"]
                ),
                ServiceCapability(
                    name="Audit Logging",
                    description="Comprehensive system operation tracking",
                    endpoints=["/audit-logs", "/audit-logs/search"],
                    supported_operations=["log_operations", "search_logs", "compliance_reporting"]
                ),
                ServiceCapability(
                    name="Templates",
                    description="Notification and report templates",
                    endpoints=["/templates", "/templates/{id}"],
                    supported_operations=["create_template", "render_template", "template_management"]
                )
            ],
            dependencies=["postgres", "redis"]
        )
        
        # AI Brain Service (Self)
        self.components['ai-brain'] = SystemComponent(
            name="AI Brain Service",
            type="service",
            description="Main AI interface with natural language processing and intent classification",
            port=3005,
            health_endpoint="/health",
            capabilities=[
                ServiceCapability(
                    name="Natural Language Processing",
                    description="Process natural language commands and queries",
                    endpoints=["/ai/chat", "/ai/analyze-text"],
                    supported_operations=["intent_classification", "entity_extraction", "context_awareness"]
                ),
                ServiceCapability(
                    name="Workflow Generation",
                    description="Generate automation workflows from natural language",
                    endpoints=["/ai/create-job", "/ai/execute-job"],
                    supported_operations=["workflow_creation", "script_generation", "job_automation"]
                ),
                ServiceCapability(
                    name="Knowledge Management",
                    description="Vector-based knowledge storage and retrieval",
                    endpoints=["/ai/knowledge-stats", "/ai/store-knowledge"],
                    supported_operations=["knowledge_storage", "semantic_search", "learning_system"]
                ),
                ServiceCapability(
                    name="Protocol Operations",
                    description="Execute operations using various protocols",
                    endpoints=["/ai/protocol/execute", "/ai/protocols/capabilities"],
                    supported_operations=["protocol_execution", "multi_protocol_support"],
                    protocols=["SSH", "SNMP", "SMTP", "HTTP", "PowerShell", "VAPIX"]
                )
            ],
            dependencies=["postgres", "redis", "ollama"]
        )
        
        # Infrastructure Components
        self.components['postgres'] = SystemComponent(
            name="PostgreSQL Database",
            type="database",
            description="Primary database with 4 schemas (identity, assets, automation, communication)",
            port=5432,
            capabilities=[
                ServiceCapability(
                    name="Data Storage",
                    description="Persistent data storage with ACID compliance",
                    endpoints=[],
                    supported_operations=["data_persistence", "transactions", "schema_management", "backup_restore"]
                )
            ]
        )
        
        self.components['redis'] = SystemComponent(
            name="Redis Cache",
            type="cache",
            description="Caching, sessions, and task queues",
            port=6379,
            capabilities=[
                ServiceCapability(
                    name="Caching",
                    description="High-performance in-memory caching",
                    endpoints=[],
                    supported_operations=["session_storage", "task_queuing", "pub_sub", "data_caching"]
                )
            ]
        )
        
        self.components['nginx'] = SystemComponent(
            name="Nginx Reverse Proxy",
            type="proxy",
            description="Reverse proxy and SSL termination",
            port=80,
            capabilities=[
                ServiceCapability(
                    name="Reverse Proxy",
                    description="Load balancing and SSL termination",
                    endpoints=[],
                    supported_operations=["load_balancing", "ssl_termination", "static_serving"]
                )
            ]
        )
    
    async def _define_ai_capabilities(self):
        """Define AI-specific capabilities"""
        self.capabilities['ai'] = {
            "natural_language_processing": {
                "description": "Process and understand natural language commands",
                "features": [
                    "Intent classification with high accuracy",
                    "Entity extraction (IPs, emails, numbers, quoted strings)",
                    "Context awareness and conversation history",
                    "Multi-turn conversation support"
                ],
                "supported_languages": ["English"],
                "confidence_threshold": 0.5
            },
            "workflow_generation": {
                "description": "Generate automation workflows from descriptions",
                "features": [
                    "Multi-step workflow creation",
                    "Protocol-specific script generation",
                    "Target resolution and grouping",
                    "Error handling and validation"
                ],
                "supported_formats": ["JSON", "YAML", "PowerShell", "Bash", "Python"]
            },
            "knowledge_management": {
                "description": "Store and retrieve knowledge using vector embeddings",
                "features": [
                    "Semantic search capabilities",
                    "Continuous learning from interactions",
                    "Knowledge categorization",
                    "Context-aware retrieval"
                ],
                "storage_backend": "ChromaDB",
                "embedding_model": "sentence-transformers"
            },
            "protocol_integration": {
                "description": "Execute operations across multiple protocols",
                "features": [
                    "Multi-protocol command execution",
                    "Credential management integration",
                    "Real-time result processing",
                    "Error handling and retry logic"
                ]
            }
        }
    
    async def _define_supported_protocols(self):
        """Define all supported protocols"""
        self.protocols = {
            "SSH": {
                "description": "Secure Shell for remote command execution",
                "port": 22,
                "supported_operations": [
                    "remote_command_execution",
                    "file_transfer",
                    "tunnel_creation",
                    "key_based_authentication"
                ],
                "authentication_methods": ["password", "key", "certificate"],
                "platforms": ["Linux", "Unix", "macOS", "Windows (OpenSSH)"]
            },
            "SNMP": {
                "description": "Simple Network Management Protocol for device monitoring",
                "port": 161,
                "supported_operations": [
                    "device_monitoring",
                    "oid_queries",
                    "trap_handling",
                    "bulk_operations"
                ],
                "versions": ["v1", "v2c", "v3"],
                "platforms": ["Network devices", "Servers", "IoT devices"]
            },
            "SMTP": {
                "description": "Simple Mail Transfer Protocol for email notifications",
                "port": 25,
                "supported_operations": [
                    "email_sending",
                    "template_rendering",
                    "attachment_support",
                    "html_email"
                ],
                "authentication_methods": ["none", "plain", "login", "oauth2"],
                "platforms": ["Email servers", "Cloud email services"]
            },
            "HTTP/HTTPS": {
                "description": "Web protocols for API interactions",
                "port": 80,
                "supported_operations": [
                    "rest_api_calls",
                    "webhook_handling",
                    "file_download_upload",
                    "authentication_flows"
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "authentication_methods": ["basic", "bearer", "oauth2", "api_key"]
            },
            "PowerShell": {
                "description": "Windows PowerShell for Windows automation",
                "port": 5985,
                "supported_operations": [
                    "windows_administration",
                    "active_directory_management",
                    "registry_operations",
                    "service_management"
                ],
                "versions": ["5.1", "7.x"],
                "platforms": ["Windows", "Linux (PowerShell Core)", "macOS"]
            },
            "VAPIX": {
                "description": "Axis Video API for camera management",
                "port": 80,
                "supported_operations": [
                    "camera_control",
                    "video_streaming",
                    "event_handling",
                    "configuration_management"
                ],
                "authentication_methods": ["digest", "basic"],
                "platforms": ["Axis cameras", "Compatible IP cameras"]
            },
            "Database": {
                "description": "Database connectivity for various database systems",
                "port": "varies",
                "supported_operations": [
                    "query_execution",
                    "data_manipulation",
                    "schema_operations",
                    "transaction_management"
                ],
                "supported_databases": ["PostgreSQL", "MySQL", "SQL Server", "Oracle", "SQLite"],
                "platforms": ["Any database server"]
            }
        }
    
    async def _define_available_tools(self):
        """Define available tools and utilities"""
        self.tools = {
            "database_introspection": {
                "description": "Analyze database schema and structure",
                "capabilities": [
                    "Schema discovery",
                    "Table relationship mapping",
                    "Column analysis",
                    "Index information",
                    "Constraint details"
                ],
                "supported_databases": ["PostgreSQL", "MySQL", "SQL Server"]
            },
            "target_resolution": {
                "description": "Resolve target groups to individual targets",
                "capabilities": [
                    "Group hierarchy traversal",
                    "Tag-based filtering",
                    "Service type filtering",
                    "Connection status checking"
                ]
            },
            "script_generation": {
                "description": "Generate scripts for various platforms",
                "capabilities": [
                    "PowerShell script generation",
                    "Bash script generation",
                    "Python script generation",
                    "SQL query generation"
                ],
                "templates": ["System administration", "Monitoring", "Deployment", "Maintenance"]
            },
            "workflow_orchestration": {
                "description": "Orchestrate complex multi-step workflows",
                "capabilities": [
                    "Step sequencing",
                    "Parallel execution",
                    "Error handling",
                    "Rollback procedures",
                    "Conditional logic"
                ]
            },
            "real_time_monitoring": {
                "description": "Monitor system operations in real-time",
                "capabilities": [
                    "Job execution monitoring",
                    "System health monitoring",
                    "Performance metrics",
                    "Alert generation"
                ]
            }
        }
    
    async def _check_system_health(self):
        """Check health of all system components"""
        # This would normally make actual health check calls
        # For now, we'll simulate the status
        healthy_services = [
            'frontend', 'api-gateway', 'identity-service', 
            'asset-service', 'automation-service', 'communication-service', 
            'ai-brain', 'postgres', 'redis', 'nginx'
        ]
        
        for component_name in self.components:
            if component_name in healthy_services:
                self.components[component_name].status = "healthy"
            else:
                self.components[component_name].status = "unknown"
        
        # Overall system status
        unhealthy_count = sum(1 for comp in self.components.values() if comp.status != "healthy")
        if unhealthy_count == 0:
            self.system_status = "healthy"
        elif unhealthy_count < len(self.components) / 2:
            self.system_status = "degraded"
        else:
            self.system_status = "unhealthy"
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        return {
            "system_status": self.system_status,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "components": {name: comp.to_dict() for name, comp in self.components.items()},
            "total_components": len(self.components),
            "healthy_components": sum(1 for comp in self.components.values() if comp.status == "healthy"),
            "ai_capabilities": self.capabilities.get('ai', {}),
            "supported_protocols": list(self.protocols.keys()),
            "available_tools": list(self.tools.keys())
        }
    
    def get_capabilities_summary(self) -> str:
        """Get human-readable capabilities summary"""
        summary_parts = [
            "🤖 **OpsConductor AI Assistant Capabilities**",
            "",
            "**🏗️ System Architecture:**",
            f"- {len(self.components)} system components",
            f"- System status: {self.system_status}",
            f"- {sum(1 for comp in self.components.values() if comp.status == 'healthy')} healthy services",
            "",
            "**🧠 AI Capabilities:**",
            "- Natural language processing and intent classification",
            "- Workflow generation from text descriptions",
            "- Vector-based knowledge management and learning",
            "- Multi-protocol automation execution",
            "",
            "**🔧 Supported Protocols:**"
        ]
        
        for protocol, details in self.protocols.items():
            summary_parts.append(f"- **{protocol}**: {details['description']}")
        
        summary_parts.extend([
            "",
            "**🛠️ Available Tools:**"
        ])
        
        for tool, details in self.tools.items():
            summary_parts.append(f"- **{tool.replace('_', ' ').title()}**: {details['description']}")
        
        summary_parts.extend([
            "",
            "**📊 Core Services:**"
        ])
        
        service_components = {name: comp for name, comp in self.components.items() if comp.type == "service"}
        for name, comp in service_components.items():
            status_emoji = "✅" if comp.status == "healthy" else "❌"
            summary_parts.append(f"- {status_emoji} **{comp.name}** (Port {comp.port}): {comp.description}")
        
        return "\n".join(summary_parts)
    
    def can_perform_operation(self, operation: str) -> Dict[str, Any]:
        """Check if system can perform a specific operation"""
        operation_lower = operation.lower()
        
        # Search through all capabilities
        matching_capabilities = []
        
        for comp_name, component in self.components.items():
            if component.capabilities:
                for capability in component.capabilities:
                    if any(op.lower() in operation_lower or operation_lower in op.lower() 
                          for op in capability.supported_operations):
                        matching_capabilities.append({
                            "component": comp_name,
                            "capability": capability.name,
                            "description": capability.description,
                            "status": component.status
                        })
        
        # Check protocols
        matching_protocols = []
        for protocol, details in self.protocols.items():
            if any(op.lower() in operation_lower or operation_lower in op.lower() 
                  for op in details['supported_operations']):
                matching_protocols.append({
                    "protocol": protocol,
                    "description": details['description'],
                    "operations": details['supported_operations']
                })
        
        # Check tools
        matching_tools = []
        for tool, details in self.tools.items():
            if tool.lower() in operation_lower or operation_lower in tool.lower():
                matching_tools.append({
                    "tool": tool,
                    "description": details['description'],
                    "capabilities": details['capabilities']
                })
        
        can_perform = len(matching_capabilities) > 0 or len(matching_protocols) > 0 or len(matching_tools) > 0
        
        return {
            "can_perform": can_perform,
            "operation": operation,
            "matching_capabilities": matching_capabilities,
            "matching_protocols": matching_protocols,
            "matching_tools": matching_tools,
            "recommendations": self._get_operation_recommendations(operation_lower) if can_perform else []
        }
    
    def _get_operation_recommendations(self, operation: str) -> List[str]:
        """Get recommendations for performing an operation"""
        recommendations = []
        
        if "target" in operation:
            recommendations.append("Use the Asset Service to manage infrastructure targets")
            recommendations.append("Consider using target groups for bulk operations")
        
        if "job" in operation or "automation" in operation:
            recommendations.append("Use the Automation Service for job execution")
            recommendations.append("Consider creating workflows for complex operations")
        
        if "monitor" in operation or "check" in operation:
            recommendations.append("Use SNMP protocol for network device monitoring")
            recommendations.append("Consider setting up automated monitoring jobs")
        
        if "email" in operation or "notification" in operation:
            recommendations.append("Use the Communication Service for notifications")
            recommendations.append("Create templates for consistent messaging")
        
        return recommendations
    
    def get_protocol_details(self, protocol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific protocol"""
        return self.protocols.get(protocol.upper())
    
    def get_component_details(self, component: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific component"""
        comp = self.components.get(component.lower())
        return comp.to_dict() if comp else None
    
    async def refresh_system_status(self):
        """Refresh system status information"""
        await self._check_system_health()
        self.last_updated = datetime.now()
        logger.info("System status refreshed")

# Global instance
system_capabilities = SystemCapabilitiesManager()
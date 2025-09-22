"""
OpsConductor System Model - Service Capabilities Module

This module provides comprehensive knowledge about all OpsConductor services,
their capabilities, API endpoints, and operational parameters.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Types of services in the OpsConductor ecosystem"""
    CORE_BUSINESS = "core_business"
    AI_INTELLIGENCE = "ai_intelligence"
    INFRASTRUCTURE = "infrastructure"
    GATEWAY = "gateway"

class ProtocolType(Enum):
    """Supported protocols for automation"""
    SSH = "ssh"
    WINRM = "winrm"
    POWERSHELL = "powershell"
    SNMP = "snmp"
    HTTP = "http"
    HTTPS = "https"
    DATABASE = "database"
    REST_API = "rest_api"
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    DNS = "dns"
    FTP = "ftp"
    SMTP = "smtp"

@dataclass
class APIEndpoint:
    """Represents an API endpoint with its capabilities"""
    path: str
    method: str
    description: str
    parameters: Dict[str, Any]
    response_format: str
    authentication_required: bool = True
    
@dataclass
class ServiceCapability:
    """Represents a specific capability of a service"""
    name: str
    description: str
    endpoints: List[APIEndpoint]
    protocols_supported: List[ProtocolType]
    data_models: List[str]
    dependencies: List[str]

@dataclass
class OpsConductorService:
    """Complete service definition"""
    name: str
    container_name: str
    port: int
    service_type: ServiceType
    description: str
    capabilities: List[ServiceCapability]
    health_endpoint: str
    base_url_template: str

class ServiceCapabilitiesManager:
    """Manages knowledge about all OpsConductor services and their capabilities"""
    
    def __init__(self):
        self.services = self._initialize_service_definitions()
        logger.info(f"Initialized service capabilities for {len(self.services)} services")
    
    def _initialize_service_definitions(self) -> Dict[str, OpsConductorService]:
        """Initialize comprehensive service definitions"""
        services = {}
        
        # Identity Service
        services["identity-service"] = OpsConductorService(
            name="identity-service",
            container_name="opsconductor-identity",
            port=3001,
            service_type=ServiceType.CORE_BUSINESS,
            description="Authentication, authorization, and user management",
            health_endpoint="/health",
            base_url_template="http://identity-service:3001",
            capabilities=[
                ServiceCapability(
                    name="user_management",
                    description="Create, update, delete, and manage users",
                    endpoints=[
                        APIEndpoint("/users", "GET", "List all users", {}, "json"),
                        APIEndpoint("/users", "POST", "Create new user", {"username": "str", "email": "str", "password": "str"}, "json"),
                        APIEndpoint("/users/{user_id}", "GET", "Get user details", {"user_id": "int"}, "json"),
                        APIEndpoint("/users/{user_id}", "PUT", "Update user", {"user_id": "int"}, "json"),
                        APIEndpoint("/users/{user_id}", "DELETE", "Delete user", {"user_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["User", "UserProfile", "UserPreferences"],
                    dependencies=["postgres"]
                ),
                ServiceCapability(
                    name="authentication",
                    description="User login, logout, and session management",
                    endpoints=[
                        APIEndpoint("/auth/login", "POST", "User login", {"username": "str", "password": "str"}, "json"),
                        APIEndpoint("/auth/logout", "POST", "User logout", {}, "json"),
                        APIEndpoint("/auth/refresh", "POST", "Refresh token", {"refresh_token": "str"}, "json"),
                        APIEndpoint("/auth/validate", "POST", "Validate token", {"token": "str"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["AuthToken", "Session", "LoginCredentials"],
                    dependencies=["redis"]
                ),
                ServiceCapability(
                    name="authorization",
                    description="Role-based access control and permissions",
                    endpoints=[
                        APIEndpoint("/roles", "GET", "List roles", {}, "json"),
                        APIEndpoint("/roles", "POST", "Create role", {"name": "str", "permissions": "list"}, "json"),
                        APIEndpoint("/permissions", "GET", "List permissions", {}, "json"),
                        APIEndpoint("/users/{user_id}/roles", "GET", "Get user roles", {"user_id": "int"}, "json"),
                        APIEndpoint("/users/{user_id}/roles", "POST", "Assign role to user", {"user_id": "int", "role_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["Role", "Permission", "UserRole"],
                    dependencies=["postgres"]
                )
            ]
        )
        
        # Asset Service
        services["asset-service"] = OpsConductorService(
            name="asset-service",
            container_name="opsconductor-assets",
            port=3002,
            service_type=ServiceType.CORE_BUSINESS,
            description="Target management, credentials, and asset inventory",
            health_endpoint="/health",
            base_url_template="http://asset-service:3002",
            capabilities=[
                ServiceCapability(
                    name="asset_management",
                    description="Manage infrastructure assets (servers, devices, services)",
                    endpoints=[
                        APIEndpoint("/assets", "GET", "List all assets", {"limit": "int?", "skip": "int?"}, "json"),
                        APIEndpoint("/assets", "POST", "Create new asset", {"name": "str", "ip_address": "str", "os_type": "str"}, "json"),
                        APIEndpoint("/assets/{asset_id}", "GET", "Get asset details", {"asset_id": "int"}, "json"),
                        APIEndpoint("/assets/{asset_id}", "PUT", "Update asset", {"asset_id": "int"}, "json"),
                        APIEndpoint("/assets/{asset_id}", "DELETE", "Delete asset", {"asset_id": "int"}, "json"),
                        APIEndpoint("/health", "GET", "Asset service health check", {}, "json"),
                    ],
                    protocols_supported=[ProtocolType.SSH, ProtocolType.WINRM, ProtocolType.SNMP, ProtocolType.HTTP, ProtocolType.HTTPS],
                    data_models=["Asset", "AssetType", "AssetStatus", "DeviceType"],
                    dependencies=["postgres"]
                ),
                ServiceCapability(
                    name="credential_management",
                    description="Secure storage and management of authentication credentials",
                    endpoints=[
                        APIEndpoint("/credentials", "GET", "List credentials", {}, "json"),
                        APIEndpoint("/credentials", "POST", "Create credential", {"name": "str", "type": "str", "data": "encrypted"}, "json"),
                        APIEndpoint("/credentials/{cred_id}", "GET", "Get credential details", {"cred_id": "int"}, "json"),
                        APIEndpoint("/credentials/{cred_id}", "PUT", "Update credential", {"cred_id": "int"}, "json"),
                        APIEndpoint("/credentials/{cred_id}", "DELETE", "Delete credential", {"cred_id": "int"}, "json"),
                        APIEndpoint("/credentials/{cred_id}/test", "POST", "Test credential", {"cred_id": "int", "target_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["Credential", "CredentialType", "EncryptedData"],
                    dependencies=["postgres", "encryption_key"]
                ),
                # Note: Group management not yet implemented in asset service
                # ServiceCapability(
                #     name="group_management", 
                #     description="Organize assets into hierarchical groups - Coming Soon",
                #     endpoints=[],
                #     protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                #     data_models=["Group", "GroupHierarchy", "GroupMembership"],
                #     dependencies=["postgres"]
                # )
            ]
        )
        
        # Automation Service
        services["automation-service"] = OpsConductorService(
            name="automation-service",
            container_name="opsconductor-automation",
            port=3003,
            service_type=ServiceType.CORE_BUSINESS,
            description="Job execution, workflow management, and task automation",
            health_endpoint="/health",
            base_url_template="http://automation-service:3003",
            capabilities=[
                ServiceCapability(
                    name="job_management",
                    description="Create, execute, and manage automation jobs",
                    endpoints=[
                        APIEndpoint("/jobs", "GET", "List all jobs", {"status": "str?", "user_id": "int?"}, "json"),
                        APIEndpoint("/jobs", "POST", "Create new job", {"name": "str", "workflow": "dict", "targets": "list"}, "json"),
                        APIEndpoint("/jobs/{job_id}", "GET", "Get job details", {"job_id": "int"}, "json"),
                        APIEndpoint("/jobs/{job_id}/execute", "POST", "Execute job", {"job_id": "int"}, "json"),
                        APIEndpoint("/jobs/{job_id}/cancel", "POST", "Cancel job", {"job_id": "int"}, "json"),
                        APIEndpoint("/jobs/{job_id}/results", "GET", "Get job results", {"job_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.SSH, ProtocolType.WINRM, ProtocolType.POWERSHELL, ProtocolType.SNMP],
                    data_models=["Job", "JobStatus", "JobResult", "WorkflowStep"],
                    dependencies=["postgres", "redis", "celery"]
                ),
                ServiceCapability(
                    name="workflow_execution",
                    description="Execute complex multi-step workflows",
                    endpoints=[
                        APIEndpoint("/workflows", "GET", "List workflow templates", {}, "json"),
                        APIEndpoint("/workflows", "POST", "Create workflow template", {"name": "str", "steps": "list"}, "json"),
                        APIEndpoint("/workflows/{workflow_id}/execute", "POST", "Execute workflow", {"workflow_id": "int", "parameters": "dict"}, "json"),
                        APIEndpoint("/workflows/{workflow_id}/validate", "POST", "Validate workflow", {"workflow_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.SSH, ProtocolType.WINRM, ProtocolType.POWERSHELL, ProtocolType.SNMP],
                    data_models=["Workflow", "WorkflowTemplate", "WorkflowExecution", "StepResult"],
                    dependencies=["postgres", "redis", "celery"]
                ),
                ServiceCapability(
                    name="real_time_monitoring",
                    description="Real-time job execution monitoring and WebSocket updates",
                    endpoints=[
                        APIEndpoint("/ws/jobs/{job_id}", "WebSocket", "Real-time job updates", {"job_id": "int"}, "websocket"),
                        APIEndpoint("/jobs/{job_id}/logs", "GET", "Get job execution logs", {"job_id": "int"}, "json"),
                        APIEndpoint("/jobs/{job_id}/status", "GET", "Get current job status", {"job_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["JobLog", "JobProgress", "ExecutionStatus"],
                    dependencies=["redis", "websocket_manager"]
                )
            ]
        )
        
        # Communication Service
        services["communication-service"] = OpsConductorService(
            name="communication-service",
            container_name="opsconductor-communication",
            port=3004,
            service_type=ServiceType.CORE_BUSINESS,
            description="Notifications, alerts, and communication management",
            health_endpoint="/health",
            base_url_template="http://communication-service:3004",
            capabilities=[
                ServiceCapability(
                    name="notification_management",
                    description="Send and manage various types of notifications",
                    endpoints=[
                        APIEndpoint("/notifications", "GET", "List notifications", {"user_id": "int?"}, "json"),
                        APIEndpoint("/notifications", "POST", "Send notification", {"type": "str", "recipients": "list", "message": "str"}, "json"),
                        APIEndpoint("/notifications/{notification_id}", "GET", "Get notification details", {"notification_id": "int"}, "json"),
                        APIEndpoint("/notifications/{notification_id}/mark-read", "POST", "Mark as read", {"notification_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["Notification", "NotificationType", "NotificationStatus"],
                    dependencies=["postgres", "redis"]
                ),
                ServiceCapability(
                    name="alert_management",
                    description="System alerts and escalation procedures",
                    endpoints=[
                        APIEndpoint("/alerts", "GET", "List active alerts", {}, "json"),
                        APIEndpoint("/alerts", "POST", "Create alert", {"severity": "str", "message": "str", "source": "str"}, "json"),
                        APIEndpoint("/alerts/{alert_id}/acknowledge", "POST", "Acknowledge alert", {"alert_id": "int"}, "json"),
                        APIEndpoint("/alerts/{alert_id}/resolve", "POST", "Resolve alert", {"alert_id": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["Alert", "AlertSeverity", "AlertStatus"],
                    dependencies=["postgres", "redis"]
                )
            ]
        )
        
        # AI Brain Service (Self-Reference)
        services["ai-brain"] = OpsConductorService(
            name="ai-brain",
            container_name="opsconductor-ai-brain",
            port=3005,
            service_type=ServiceType.AI_INTELLIGENCE,
            description="Unified AI intelligence for natural language processing and intelligent automation",
            health_endpoint="/health",
            base_url_template="http://ai-brain:3005",
            capabilities=[
                ServiceCapability(
                    name="natural_language_processing",
                    description="Process natural language queries and convert to actionable tasks",
                    endpoints=[
                        APIEndpoint("/chat", "POST", "Process natural language query", {"message": "str", "context": "dict?"}, "json"),
                        APIEndpoint("/intent", "POST", "Extract intent from message", {"message": "str"}, "json"),
                        APIEndpoint("/capabilities", "GET", "List AI capabilities", {}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["ChatMessage", "Intent", "AICapability"],
                    dependencies=["ollama", "chromadb"]
                ),
                ServiceCapability(
                    name="intelligent_job_creation",
                    description="Create automation jobs from natural language descriptions",
                    endpoints=[
                        APIEndpoint("/jobs/create-from-text", "POST", "Create job from description", {"description": "str", "context": "dict?"}, "json"),
                        APIEndpoint("/jobs/validate-requirements", "POST", "Validate job requirements", {"requirements": "dict"}, "json"),
                        APIEndpoint("/workflows/generate", "POST", "Generate workflow from requirements", {"requirements": "dict"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["JobRequirements", "GeneratedWorkflow", "ValidationResult"],
                    dependencies=["asset-service", "automation-service", "ollama", "chromadb"]
                ),
                ServiceCapability(
                    name="system_knowledge",
                    description="Deep knowledge about OpsConductor system capabilities and best practices",
                    endpoints=[
                        APIEndpoint("/system/capabilities", "GET", "Get system capabilities", {}, "json"),
                        APIEndpoint("/system/services", "GET", "List all services and their capabilities", {}, "json"),
                        APIEndpoint("/system/protocols", "GET", "List supported protocols", {}, "json"),
                        APIEndpoint("/system/best-practices", "GET", "Get best practices for operations", {"category": "str?"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["SystemCapability", "ServiceInfo", "BestPractice"],
                    dependencies=[]
                ),
                ServiceCapability(
                    name="learning_and_adaptation",
                    description="Learn from job results and improve recommendations",
                    endpoints=[
                        APIEndpoint("/learning/feedback", "POST", "Provide feedback on job results", {"job_id": "int", "feedback": "dict"}, "json"),
                        APIEndpoint("/learning/patterns", "GET", "Get learned patterns", {}, "json"),
                        APIEndpoint("/learning/recommendations", "GET", "Get AI recommendations", {"context": "dict"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["LearningFeedback", "Pattern", "Recommendation"],
                    dependencies=["chromadb", "postgres"]
                )
            ]
        )
        
        # Network Analyzer Service
        services["network-analyzer-service"] = OpsConductorService(
            name="network-analyzer-service",
            container_name="opsconductor-network-analyzer",
            port=3006,
            service_type=ServiceType.CORE_BUSINESS,
            description="Network packet analysis, monitoring, and troubleshooting",
            health_endpoint="/health",
            base_url_template="http://network-analyzer-service:3006",
            capabilities=[
                ServiceCapability(
                    name="packet_analysis",
                    description="Capture and analyze network packets in real-time",
                    endpoints=[
                        APIEndpoint("/api/v1/network/capture", "POST", "Start packet capture", {"interface": "str", "filter": "str?", "duration": "int?", "max_packets": "int?"}, "json"),
                        APIEndpoint("/api/v1/network/capture/{session_id}", "GET", "Get capture results", {"session_id": "str"}, "json"),
                        APIEndpoint("/api/v1/network/capture/{session_id}", "DELETE", "Stop capture session", {"session_id": "str"}, "json"),
                        APIEndpoint("/api/v1/network/interfaces", "GET", "List network interfaces", {}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["PacketCaptureRequest", "PacketCaptureResult", "NetworkInterface", "PacketData"],
                    dependencies=["tcpdump", "tshark", "scapy"]
                ),
                ServiceCapability(
                    name="network_monitoring",
                    description="Real-time network performance monitoring and alerting",
                    endpoints=[
                        APIEndpoint("/api/v1/monitoring/start", "POST", "Start network monitoring", {"interface": "str", "thresholds": "dict?"}, "json"),
                        APIEndpoint("/api/v1/monitoring/status/{session_id}", "GET", "Get monitoring status", {"session_id": "str"}, "json"),
                        APIEndpoint("/api/v1/monitoring/stop/{session_id}", "POST", "Stop monitoring session", {"session_id": "str"}, "json"),
                        APIEndpoint("/ws/monitoring/{session_id}", "WebSocket", "Real-time monitoring updates", {"session_id": "str"}, "websocket"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["MonitoringRequest", "NetworkMetrics", "AlertThreshold", "MonitoringStatus"],
                    dependencies=["psutil", "websocket_manager"]
                ),
                ServiceCapability(
                    name="protocol_analysis",
                    description="Deep analysis of specific network protocols",
                    endpoints=[
                        APIEndpoint("/api/v1/analysis/protocol", "POST", "Analyze specific protocols", {"protocol": "str", "data": "str", "options": "dict?"}, "json"),
                        APIEndpoint("/api/v1/analysis/protocols", "GET", "List supported protocols", {}, "json"),
                        APIEndpoint("/api/v1/analysis/performance", "POST", "Analyze network performance", {"interface": "str", "duration": "int"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.TCP, ProtocolType.UDP, ProtocolType.HTTP, ProtocolType.HTTPS, ProtocolType.DNS, ProtocolType.ICMP, ProtocolType.SSH, ProtocolType.FTP, ProtocolType.SMTP, ProtocolType.SNMP],
                    data_models=["ProtocolAnalysisRequest", "ProtocolAnalysisResult", "PerformanceMetrics", "ProtocolInfo"],
                    dependencies=["scapy", "dpkt", "pyshark"]
                ),
                ServiceCapability(
                    name="ai_network_analysis",
                    description="AI-powered network diagnosis and anomaly detection",
                    endpoints=[
                        APIEndpoint("/api/v1/analysis/ai/diagnose", "POST", "AI-powered network diagnosis", {"symptoms": "list", "network_data": "dict"}, "json"),
                        APIEndpoint("/api/v1/analysis/ai/anomaly", "POST", "Detect network anomalies", {"data": "dict", "baseline": "dict?"}, "json"),
                        APIEndpoint("/api/v1/analysis/ai/suggestions/{analysis_id}", "GET", "Get AI suggestions", {"analysis_id": "str"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["NetworkDiagnosis", "AnomalyDetectionResult", "AIAnalysisRequest", "NetworkSuggestion"],
                    dependencies=["ai-brain", "scikit-learn", "numpy"]
                ),
                ServiceCapability(
                    name="remote_analysis",
                    description="Deploy and manage remote network analysis agents",
                    endpoints=[
                        APIEndpoint("/api/v1/remote/deploy", "POST", "Deploy remote agent", {"target_id": "str", "analysis_type": "str", "duration": "int?"}, "json"),
                        APIEndpoint("/api/v1/remote/agents", "GET", "List active agents", {}, "json"),
                        APIEndpoint("/api/v1/remote/analyze", "POST", "Start remote analysis", {"agent_id": "str", "analysis_config": "dict"}, "json"),
                        APIEndpoint("/api/v1/remote/agent/{agent_id}", "DELETE", "Remove remote agent", {"agent_id": "str"}, "json"),
                    ],
                    protocols_supported=[ProtocolType.SSH, ProtocolType.WINRM, ProtocolType.REST_API],
                    data_models=["RemoteAgent", "AgentDeployment", "RemoteAnalysisRequest", "AgentStatus"],
                    dependencies=["asset-service", "automation-service"]
                )
            ]
        )
        
        # API Gateway
        services["api-gateway"] = OpsConductorService(
            name="api-gateway",
            container_name="opsconductor-gateway",
            port=3000,
            service_type=ServiceType.GATEWAY,
            description="Central API gateway for routing and authentication",
            health_endpoint="/health",
            base_url_template="http://api-gateway:3000",
            capabilities=[
                ServiceCapability(
                    name="request_routing",
                    description="Route requests to appropriate services",
                    endpoints=[
                        APIEndpoint("/health", "GET", "Gateway health check", {}, "json", False),
                        APIEndpoint("/api/v1/*", "ALL", "Route to services", {}, "proxy"),
                    ],
                    protocols_supported=[ProtocolType.REST_API, ProtocolType.HTTPS],
                    data_models=["RouteConfig", "ProxyRequest"],
                    dependencies=["identity-service", "asset-service", "automation-service", "communication-service", "network-analyzer-service", "ai-brain"]
                )
            ]
        )
        
        return services
    
    def get_service(self, service_name: str) -> Optional[OpsConductorService]:
        """Get service definition by name"""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict[str, OpsConductorService]:
        """Get all service definitions"""
        return self.services
    
    def get_all_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get all services with their capabilities in a simplified format"""
        capabilities = {}
        for service_name, service in self.services.items():
            capabilities[service_name] = {
                'name': service.name,
                'description': service.description,
                'capabilities': [cap.name for cap in service.capabilities],
                'service_type': service.service_type.value,
                'port': service.port
            }
        return capabilities
    
    def get_services_by_type(self, service_type: ServiceType) -> List[OpsConductorService]:
        """Get services filtered by type"""
        return [service for service in self.services.values() if service.service_type == service_type]
    
    def get_service_capabilities(self, service_name: str) -> List[ServiceCapability]:
        """Get capabilities for a specific service"""
        service = self.get_service(service_name)
        return service.capabilities if service else []
    
    def find_services_with_capability(self, capability_name: str) -> List[OpsConductorService]:
        """Find services that have a specific capability"""
        matching_services = []
        for service in self.services.values():
            for capability in service.capabilities:
                if capability.name == capability_name:
                    matching_services.append(service)
                    break
        return matching_services
    
    def find_services_supporting_protocol(self, protocol: ProtocolType) -> List[OpsConductorService]:
        """Find services that support a specific protocol"""
        matching_services = []
        for service in self.services.values():
            for capability in service.capabilities:
                if protocol in capability.protocols_supported:
                    matching_services.append(service)
                    break
        return matching_services
    
    def get_service_endpoints(self, service_name: str) -> List[APIEndpoint]:
        """Get all API endpoints for a service"""
        service = self.get_service(service_name)
        if not service:
            return []
        
        endpoints = []
        for capability in service.capabilities:
            endpoints.extend(capability.endpoints)
        return endpoints
    
    def get_service_dependencies(self, service_name: str) -> List[str]:
        """Get all dependencies for a service"""
        service = self.get_service(service_name)
        if not service:
            return []
        
        dependencies = set()
        for capability in service.capabilities:
            dependencies.update(capability.dependencies)
        return list(dependencies)
    
    def validate_service_availability(self, service_name: str) -> Dict[str, Any]:
        """Validate if a service and its dependencies are available"""
        service = self.get_service(service_name)
        if not service:
            return {"available": False, "error": f"Service {service_name} not found"}
        
        dependencies = self.get_service_dependencies(service_name)
        missing_dependencies = []
        
        for dep in dependencies:
            if dep not in self.services and dep not in ["postgres", "redis", "chromadb", "ollama", "celery", "encryption_key", "websocket_manager"]:
                missing_dependencies.append(dep)
        
        return {
            "available": len(missing_dependencies) == 0,
            "service": service.name,
            "dependencies": dependencies,
            "missing_dependencies": missing_dependencies
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        overview = {
            "total_services": len(self.services),
            "services_by_type": {},
            "total_capabilities": 0,
            "supported_protocols": set(),
            "service_summary": []
        }
        
        for service_type in ServiceType:
            services_of_type = self.get_services_by_type(service_type)
            overview["services_by_type"][service_type.value] = len(services_of_type)
        
        for service in self.services.values():
            service_info = {
                "name": service.name,
                "port": service.port,
                "type": service.service_type.value,
                "capabilities": len(service.capabilities),
                "endpoints": len(self.get_service_endpoints(service.name))
            }
            overview["service_summary"].append(service_info)
            overview["total_capabilities"] += len(service.capabilities)
            
            for capability in service.capabilities:
                overview["supported_protocols"].update([p.value for p in capability.protocols_supported])
        
        overview["supported_protocols"] = list(overview["supported_protocols"])
        return overview

# Global instance
service_capabilities = ServiceCapabilitiesManager()
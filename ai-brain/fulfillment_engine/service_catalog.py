#!/usr/bin/env python3
"""
OpsConductor Service Catalog
Provides comprehensive information about available services and their capabilities
for intelligent service selection by the AI brain
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ServiceType(str, Enum):
    """Available service types in the OpsConductor ecosystem"""
    AUTOMATION = "automation-service"
    ASSET = "asset-service"
    COMMUNICATION = "communication-service"
    NETWORK_ANALYZER = "network-analyzer-service"
    NETWORK_PROBE = "network-analytics-probe"
    CELERY_BEAT = "celery-beat"
    IDENTITY = "identity-service"

class TaskCategory(str, Enum):
    """Categories of tasks that can be performed"""
    NETWORK_DIAGNOSTICS = "network_diagnostics"
    NETWORK_MONITORING = "network_monitoring"
    SYSTEM_ADMINISTRATION = "system_administration"
    ASSET_MANAGEMENT = "asset_management"
    SCHEDULING = "scheduling"
    COMMUNICATION = "communication"
    AUTHENTICATION = "authentication"
    AUTOMATION = "automation"

@dataclass
class ServiceCapability:
    """Represents a specific capability of a service"""
    name: str
    description: str
    use_cases: List[str]
    keywords: List[str]  # Keywords that should trigger this capability

@dataclass
class ServiceInfo:
    """Complete information about a service"""
    service_type: ServiceType
    name: str
    description: str
    primary_purpose: str
    capabilities: List[ServiceCapability]
    best_for: List[TaskCategory]
    network_access: str  # "host", "container", "proxy"
    specializations: List[str]
    api_endpoints: List[str]
    when_to_use: str
    when_not_to_use: str

class ServiceCatalog:
    """Comprehensive catalog of all available services and their capabilities"""
    
    def __init__(self):
        self.services = self._build_service_catalog()
    
    def _build_service_catalog(self) -> Dict[ServiceType, ServiceInfo]:
        """Build the complete service catalog"""
        return {
            ServiceType.NETWORK_ANALYZER: ServiceInfo(
                service_type=ServiceType.NETWORK_ANALYZER,
                name="Network Protocol Analyzer Service",
                description="Advanced network analysis, packet capture, and protocol analysis with direct host network access",
                primary_purpose="Network diagnostics, troubleshooting, and deep packet inspection",
                capabilities=[
                    ServiceCapability(
                        name="Packet Capture",
                        description="Real-time packet capture and analysis",
                        use_cases=["Network troubleshooting", "Security analysis", "Performance monitoring"],
                        keywords=["packet", "capture", "tcpdump", "wireshark", "network analysis"]
                    ),
                    ServiceCapability(
                        name="Protocol Analysis",
                        description="Deep analysis of network protocols (TCP, UDP, HTTP, DNS, etc.)",
                        use_cases=["Protocol debugging", "Traffic analysis", "Security inspection"],
                        keywords=["protocol", "tcp", "udp", "http", "dns", "analysis"]
                    ),
                    ServiceCapability(
                        name="Network Monitoring",
                        description="Real-time network interface and traffic monitoring",
                        use_cases=["Bandwidth monitoring", "Interface status", "Traffic patterns"],
                        keywords=["monitor", "interface", "traffic", "bandwidth", "network status"]
                    ),
                    ServiceCapability(
                        name="Network Diagnostics",
                        description="Advanced network diagnostic tools (ping, traceroute, port scanning)",
                        use_cases=["Connectivity testing", "Route analysis", "Port availability"],
                        keywords=["ping", "traceroute", "nmap", "port scan", "connectivity", "network test"]
                    ),
                    ServiceCapability(
                        name="AI Network Analysis",
                        description="AI-powered network issue diagnosis and recommendations",
                        use_cases=["Automated troubleshooting", "Performance optimization", "Anomaly detection"],
                        keywords=["ai analysis", "network diagnosis", "troubleshooting", "anomaly"]
                    )
                ],
                best_for=[TaskCategory.NETWORK_DIAGNOSTICS, TaskCategory.NETWORK_MONITORING],
                network_access="host",
                specializations=[
                    "Direct host network access (no proxy limitations)",
                    "Advanced packet capture tools",
                    "Protocol-specific analysis",
                    "Real-time network monitoring",
                    "AI-powered network diagnosis"
                ],
                api_endpoints=[
                    "/api/v1/analysis/start-capture",
                    "/api/v1/analysis/protocol",
                    "/api/v1/analysis/ai-diagnose",
                    "/api/v1/monitoring/status",
                    "/api/v1/diagnostics/ping",
                    "/api/v1/diagnostics/traceroute",
                    "/api/v1/diagnostics/port-scan"
                ],
                when_to_use="For ANY network-related task: ping, traceroute, port scanning, packet analysis, network monitoring, connectivity testing, protocol analysis",
                when_not_to_use="For non-network tasks like file operations, system administration, or application deployment"
            ),
            
            ServiceType.AUTOMATION: ServiceInfo(
                service_type=ServiceType.AUTOMATION,
                name="Automation Service",
                description="Job execution, workflow management, and system automation",
                primary_purpose="Execute commands, manage workflows, and automate system tasks",
                capabilities=[
                    ServiceCapability(
                        name="Job Execution",
                        description="Execute commands and scripts on target systems",
                        use_cases=["System administration", "Application deployment", "Maintenance tasks"],
                        keywords=["execute", "command", "script", "job", "run", "automation"]
                    ),
                    ServiceCapability(
                        name="Workflow Management",
                        description="Create and manage complex multi-step workflows",
                        use_cases=["Complex deployments", "Multi-system operations", "Orchestration"],
                        keywords=["workflow", "orchestration", "multi-step", "pipeline"]
                    ),
                    ServiceCapability(
                        name="Remote Execution",
                        description="Execute commands on remote systems via SSH/PowerShell",
                        use_cases=["Remote administration", "Distributed operations", "System management"],
                        keywords=["ssh", "remote", "powershell", "remote execution"]
                    ),
                    ServiceCapability(
                        name="System Administration",
                        description="System-level operations and maintenance",
                        use_cases=["Service management", "File operations", "System configuration"],
                        keywords=["systemctl", "service", "restart", "stop", "start", "file", "system"]
                    )
                ],
                best_for=[TaskCategory.SYSTEM_ADMINISTRATION, TaskCategory.AUTOMATION],
                network_access="container",
                specializations=[
                    "Multi-platform execution (Linux/Windows)",
                    "SSH and PowerShell connectivity",
                    "Workflow orchestration",
                    "Job queuing and management",
                    "Real-time execution monitoring"
                ],
                api_endpoints=[
                    "/api/v1/jobs",
                    "/api/v1/jobs/{job_id}/execute",
                    "/api/v1/executions",
                    "/api/v1/workflows"
                ],
                when_to_use="For system administration, command execution, service management, file operations, application deployment",
                when_not_to_use="For network diagnostics (use network-analyzer-service instead) or scheduling (use celery-beat instead)"
            ),
            
            ServiceType.CELERY_BEAT: ServiceInfo(
                service_type=ServiceType.CELERY_BEAT,
                name="Celery Beat Scheduler",
                description="Advanced task scheduling and recurring job management",
                primary_purpose="Schedule recurring tasks, cron-like functionality, and time-based automation",
                capabilities=[
                    ServiceCapability(
                        name="Recurring Task Scheduling",
                        description="Schedule tasks to run at regular intervals",
                        use_cases=["Periodic monitoring", "Regular maintenance", "Automated backups"],
                        keywords=["schedule", "recurring", "periodic", "interval", "repeat"]
                    ),
                    ServiceCapability(
                        name="Cron-like Scheduling",
                        description="Advanced cron expression support for complex scheduling",
                        use_cases=["Complex time-based triggers", "Business hour operations", "Maintenance windows"],
                        keywords=["cron", "schedule expression", "time-based", "daily", "weekly", "monthly"]
                    ),
                    ServiceCapability(
                        name="Future Task Scheduling",
                        description="Schedule one-time tasks for future execution",
                        use_cases=["Delayed operations", "Scheduled maintenance", "Time-delayed actions"],
                        keywords=["future", "delay", "later", "scheduled", "one-time"]
                    ),
                    ServiceCapability(
                        name="Dynamic Schedule Management",
                        description="Modify, pause, and manage scheduled tasks dynamically",
                        use_cases=["Schedule adjustments", "Temporary pausing", "Schedule optimization"],
                        keywords=["modify schedule", "pause", "resume", "dynamic", "adjust"]
                    )
                ],
                best_for=[TaskCategory.SCHEDULING],
                network_access="container",
                specializations=[
                    "Advanced scheduling algorithms",
                    "Persistent schedule storage",
                    "Schedule conflict resolution",
                    "High-precision timing",
                    "Integration with automation service"
                ],
                api_endpoints=[
                    "/api/v1/schedules",
                    "/api/v1/schedules/{schedule_id}",
                    "/api/v1/schedules/{schedule_id}/pause",
                    "/api/v1/schedules/{schedule_id}/resume"
                ],
                when_to_use="For ANY scheduling needs: recurring tasks, periodic execution, cron-like scheduling, future task scheduling",
                when_not_to_use="For immediate execution (use automation-service) or simple one-time commands"
            ),
            
            ServiceType.ASSET: ServiceInfo(
                service_type=ServiceType.ASSET,
                name="Asset Management Service",
                description="Comprehensive asset and target system management",
                primary_purpose="Manage infrastructure assets, credentials, and system inventory",
                capabilities=[
                    ServiceCapability(
                        name="Asset Inventory",
                        description="Maintain comprehensive inventory of all infrastructure assets",
                        use_cases=["Infrastructure management", "Asset tracking", "System discovery"],
                        keywords=["asset", "inventory", "system", "server", "infrastructure"]
                    ),
                    ServiceCapability(
                        name="Credential Management",
                        description="Secure storage and management of system credentials",
                        use_cases=["Secure authentication", "Credential rotation", "Access management"],
                        keywords=["credentials", "password", "ssh key", "certificate", "authentication"]
                    ),
                    ServiceCapability(
                        name="Target System Management",
                        description="Manage target systems for automation and monitoring",
                        use_cases=["Automation targets", "System grouping", "Environment management"],
                        keywords=["target", "system", "group", "environment", "manage"]
                    ),
                    ServiceCapability(
                        name="Asset Discovery",
                        description="Discover and catalog new systems and services",
                        use_cases=["Network scanning", "Service discovery", "Inventory updates"],
                        keywords=["discover", "scan", "find", "catalog", "detect"]
                    )
                ],
                best_for=[TaskCategory.ASSET_MANAGEMENT],
                network_access="container",
                specializations=[
                    "Encrypted credential storage",
                    "Multi-environment support",
                    "Asset relationship mapping",
                    "Automated discovery",
                    "Compliance tracking"
                ],
                api_endpoints=[
                    "/api/v1/assets",
                    "/api/v1/assets/{asset_id}",
                    "/api/v1/assets/search",
                    "/api/v1/credentials"
                ],
                when_to_use="For asset management, credential storage, system inventory, target system configuration",
                when_not_to_use="For task execution (use automation-service) or network analysis (use network-analyzer-service)"
            ),
            
            ServiceType.COMMUNICATION: ServiceInfo(
                service_type=ServiceType.COMMUNICATION,
                name="Communication Service",
                description="Notifications, alerts, and external integrations",
                primary_purpose="Handle notifications, alerts, and communication with external systems",
                capabilities=[
                    ServiceCapability(
                        name="Notification Management",
                        description="Send notifications via multiple channels (email, SMS, Slack, etc.)",
                        use_cases=["Alert notifications", "Status updates", "Report delivery"],
                        keywords=["notify", "notification", "alert", "email", "sms", "slack"]
                    ),
                    ServiceCapability(
                        name="Template Management",
                        description="Manage notification templates and formatting",
                        use_cases=["Standardized messaging", "Dynamic content", "Multi-format notifications"],
                        keywords=["template", "format", "message", "content"]
                    ),
                    ServiceCapability(
                        name="Channel Management",
                        description="Configure and manage communication channels",
                        use_cases=["Channel setup", "Integration configuration", "Delivery management"],
                        keywords=["channel", "integration", "configure", "setup"]
                    ),
                    ServiceCapability(
                        name="External Integrations",
                        description="Integrate with external systems and APIs",
                        use_cases=["Third-party notifications", "API integrations", "Webhook handling"],
                        keywords=["integration", "api", "webhook", "external", "third-party"]
                    )
                ],
                best_for=[TaskCategory.COMMUNICATION],
                network_access="container",
                specializations=[
                    "Multi-channel delivery",
                    "Template-based messaging",
                    "Delivery tracking",
                    "Integration management",
                    "Notification scheduling"
                ],
                api_endpoints=[
                    "/api/v1/notifications",
                    "/api/v1/templates",
                    "/api/v1/channels",
                    "/api/v1/integrations"
                ],
                when_to_use="For sending notifications, alerts, reports, or integrating with external communication systems",
                when_not_to_use="For task execution, network analysis, or system management"
            )
        }
    
    def get_service_for_task(self, task_description: str, keywords: List[str] = None) -> List[ServiceType]:
        """
        Get recommended services for a given task based on description and keywords
        """
        if keywords is None:
            keywords = []
        
        # Combine task description and keywords for analysis
        all_text = (task_description + " " + " ".join(keywords)).lower()
        
        recommendations = []
        
        for service_type, service_info in self.services.items():
            score = 0
            
            # Check capabilities
            for capability in service_info.capabilities:
                for keyword in capability.keywords:
                    if keyword.lower() in all_text:
                        score += 2
                
                for use_case in capability.use_cases:
                    if any(word in all_text for word in use_case.lower().split()):
                        score += 1
            
            # Check specializations
            for specialization in service_info.specializations:
                if any(word in all_text for word in specialization.lower().split()):
                    score += 1
            
            if score > 0:
                recommendations.append((service_type, score))
        
        # Sort by score and return service types
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [service_type for service_type, _ in recommendations]
    
    def get_service_info(self, service_type: ServiceType) -> ServiceInfo:
        """Get detailed information about a specific service"""
        return self.services.get(service_type)
    
    def get_all_services(self) -> Dict[ServiceType, ServiceInfo]:
        """Get information about all available services"""
        return self.services
    
    def get_services_by_category(self, category: TaskCategory) -> List[ServiceType]:
        """Get services that are best for a specific task category"""
        return [
            service_type for service_type, service_info in self.services.items()
            if category in service_info.best_for
        ]
    
    def generate_service_selection_prompt(self) -> str:
        """Generate a comprehensive prompt for LLM service selection"""
        prompt = """# OpsConductor Service Catalog

You have access to the following specialized services. Choose the BEST service for each task:

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

## 🤖 AUTOMATION-SERVICE (Port: 3002)
**BEST FOR**: System administration, command execution, workflows
**NETWORK ACCESS**: Container network (through nginx proxy)
**USE FOR**: service management, file operations, system commands, remote execution
**CAPABILITIES**:
- Execute commands on remote systems (SSH/PowerShell)
- Multi-step workflow orchestration
- System administration tasks
- Job queuing and management
**WHEN TO USE**: System administration, service management, file operations
**API**: /api/v1/jobs, /api/v1/executions

## ⏰ CELERY-BEAT (Scheduler)
**BEST FOR**: Scheduling recurring or future tasks
**USE FOR**: cron-like scheduling, periodic tasks, recurring automation
**CAPABILITIES**:
- Advanced cron expression support
- Recurring task scheduling
- Future task scheduling
- Dynamic schedule management
**WHEN TO USE**: ANY scheduling needs (recurring, periodic, future execution)
**WHEN NOT TO USE**: Immediate execution (use automation-service)

## 📦 ASSET-SERVICE (Port: 3003)
**BEST FOR**: Asset management, credential storage, system inventory
**USE FOR**: managing infrastructure assets, storing credentials, system discovery
**CAPABILITIES**:
- Comprehensive asset inventory
- Secure credential management
- Target system management
- Asset discovery and cataloging
**WHEN TO USE**: Asset management, credential operations, system inventory

## 📢 COMMUNICATION-SERVICE (Port: 3004)
**BEST FOR**: Notifications, alerts, external integrations
**USE FOR**: sending notifications, alerts, reports, third-party integrations
**CAPABILITIES**:
- Multi-channel notifications (email, SMS, Slack)
- Template-based messaging
- External API integrations
- Delivery tracking
**WHEN TO USE**: Sending notifications or integrating with external systems

## 🔐 IDENTITY-SERVICE (Port: 3001)
**BEST FOR**: Authentication and authorization
**USE FOR**: user management, authentication, access control
**WHEN TO USE**: User authentication, access control, identity management

## SERVICE SELECTION RULES:

1. **NETWORK TASKS** → ALWAYS use network-analyzer-service
   - ping, traceroute, port scan, connectivity test, network monitoring
   - Has direct host network access (no proxy limitations)

2. **SCHEDULING** → ALWAYS use celery-beat
   - recurring tasks, periodic execution, cron-like scheduling
   - Don't use basic cron, use celery-beat for advanced scheduling

3. **SYSTEM ADMINISTRATION** → use automation-service
   - service management (restart, stop, start)
   - file operations, command execution

4. **ASSET MANAGEMENT** → use asset-service
   - managing systems, credentials, inventory

5. **NOTIFICATIONS** → use communication-service
   - alerts, reports, external integrations

Choose the RIGHT service for each task based on these capabilities!
"""
        return prompt

# Global instance
service_catalog = ServiceCatalog()
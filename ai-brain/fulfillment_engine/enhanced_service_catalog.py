#!/usr/bin/env python3
"""
Enhanced OpsConductor Service Catalog
Provides comprehensive, detailed knowledge about all OpsConductor services
for intelligent AI reasoning and decision making
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

@dataclass
class APIEndpoint:
    """Detailed API endpoint information"""
    path: str
    method: str
    description: str
    parameters: Dict[str, str]
    example_request: str
    example_response: str
    use_cases: List[str]

@dataclass
class ServiceCapability:
    """Enhanced service capability with detailed examples"""
    name: str
    description: str
    detailed_description: str
    use_cases: List[str]
    keywords: List[str]
    examples: List[str]
    api_endpoints: List[APIEndpoint]
    integration_patterns: List[str]
    best_practices: List[str]
    common_workflows: List[str]

@dataclass
class ServiceIntegration:
    """How this service integrates with other services"""
    service_name: str
    integration_type: str  # "depends_on", "works_with", "triggers", "consumes"
    description: str
    example_workflow: str

@dataclass
class EnhancedServiceInfo:
    """Comprehensive service information for AI reasoning"""
    service_type: str
    name: str
    description: str
    detailed_description: str
    primary_purpose: str
    capabilities: List[ServiceCapability]
    api_endpoints: List[APIEndpoint]
    integrations: List[ServiceIntegration]
    common_use_cases: List[str]
    example_workflows: List[str]
    troubleshooting_scenarios: List[str]
    best_practices: List[str]
    when_to_use: str
    when_not_to_use: str
    performance_characteristics: str
    limitations: List[str]
    security_considerations: List[str]

class EnhancedServiceCatalog:
    """Comprehensive service catalog with detailed knowledge for AI reasoning"""
    
    def __init__(self):
        self.services = self._build_enhanced_catalog()
    
    def _build_enhanced_catalog(self) -> Dict[str, EnhancedServiceInfo]:
        """Build the comprehensive service catalog with detailed knowledge"""
        
        return {
            "asset-service": EnhancedServiceInfo(
                service_type="asset-service",
                name="Asset Management Service",
                description="Comprehensive infrastructure asset and credential management system",
                detailed_description="""
The Asset Service is the central repository for all infrastructure assets, credentials, and system inventory.
It maintains a comprehensive database of all systems, their configurations, connection details, and credentials.
This service is essential for any automation that needs to know about target systems or connect to them.
""",
                primary_purpose="Manage infrastructure assets, credentials, and system inventory for automation and monitoring",
                capabilities=[
                    ServiceCapability(
                        name="Asset Inventory Management",
                        description="Maintain comprehensive inventory of all infrastructure assets",
                        detailed_description="""
Complete asset lifecycle management including discovery, registration, configuration tracking,
and decommissioning. Supports grouping, tagging, and hierarchical organization of assets.
Tracks hardware specifications, software versions, network configurations, and relationships.
""",
                        use_cases=[
                            "Find all Windows servers in production environment",
                            "Get list of database servers with specific OS version",
                            "Identify systems that need security updates",
                            "Track asset compliance and configuration drift",
                            "Manage multi-environment deployments (dev/staging/prod)"
                        ],
                        keywords=["asset", "inventory", "system", "server", "infrastructure", "discovery", "catalog"],
                        examples=[
                            "Query: 'Find all Windows machines' → Returns list of assets with os_type='Windows'",
                            "Query: 'Get production database servers' → Returns assets tagged as 'production' and 'database'",
                            "Query: 'List systems in subnet 192.168.1.0/24' → Returns assets in that network range"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/assets",
                                method="GET",
                                description="Get all assets with optional filtering",
                                parameters={
                                    "os_type": "Filter by operating system (Windows, Linux, macOS)",
                                    "environment": "Filter by environment (production, staging, development)",
                                    "tags": "Filter by tags (comma-separated)",
                                    "hostname": "Filter by hostname pattern",
                                    "ip_address": "Filter by IP address or subnet"
                                },
                                example_request="GET /api/v1/assets?os_type=Windows&environment=production",
                                example_response='[{"id": 1, "hostname": "web01", "os_type": "Windows", "ip_address": "192.168.1.10", "environment": "production"}]',
                                use_cases=["Find target systems for automation", "Asset discovery", "Inventory reporting"]
                            ),
                            APIEndpoint(
                                path="/api/v1/assets/search",
                                method="POST",
                                description="Advanced asset search with complex criteria",
                                parameters={
                                    "query": "Complex search query with multiple criteria",
                                    "fields": "Specific fields to return",
                                    "limit": "Maximum number of results"
                                },
                                example_request='POST /api/v1/assets/search {"query": {"os_type": "Windows", "tags": ["web-server"]}, "fields": ["id", "hostname", "ip_address"]}',
                                example_response='{"results": [{"id": 1, "hostname": "web01", "ip_address": "192.168.1.10"}], "total": 1}',
                                use_cases=["Complex asset queries", "Automation target selection", "Compliance reporting"]
                            )
                        ],
                        integration_patterns=[
                            "Automation Service queries assets to determine target systems",
                            "Network Analyzer uses asset data for network discovery validation",
                            "Communication Service uses asset contact information for notifications"
                        ],
                        best_practices=[
                            "Always query asset service before running automation on 'all systems'",
                            "Use tags and environments to organize assets logically",
                            "Keep asset information up-to-date for accurate automation targeting",
                            "Use asset groups for bulk operations"
                        ],
                        common_workflows=[
                            "1. Query assets by criteria → 2. Extract target IDs → 3. Pass to automation service",
                            "1. Discover new systems → 2. Register in asset service → 3. Configure credentials → 4. Enable automation"
                        ]
                    ),
                    ServiceCapability(
                        name="Credential Management",
                        description="Secure storage and management of system credentials",
                        detailed_description="""
Encrypted storage of credentials including passwords, SSH keys, certificates, and API tokens.
Supports credential rotation, access control, and audit logging. Integrates with external
credential stores and supports multiple authentication methods per asset.
""",
                        use_cases=[
                            "Store SSH keys for Linux server access",
                            "Manage Windows domain credentials",
                            "Store API tokens for service integrations",
                            "Implement credential rotation policies",
                            "Provide secure credential access for automation"
                        ],
                        keywords=["credentials", "password", "ssh key", "certificate", "authentication", "security"],
                        examples=[
                            "Store SSH key for server access: POST /api/v1/credentials with key data",
                            "Retrieve credentials for automation: GET /api/v1/assets/{id}/credentials",
                            "Rotate password: PUT /api/v1/credentials/{id} with new password"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/credentials",
                                method="POST",
                                description="Store new credentials for an asset",
                                parameters={
                                    "asset_id": "ID of the asset these credentials belong to",
                                    "credential_type": "Type: password, ssh_key, certificate, api_token",
                                    "username": "Username for the credential",
                                    "credential_data": "Encrypted credential data"
                                },
                                example_request='POST /api/v1/credentials {"asset_id": 1, "credential_type": "ssh_key", "username": "admin", "credential_data": "-----BEGIN RSA PRIVATE KEY-----..."}',
                                example_response='{"id": 123, "asset_id": 1, "credential_type": "ssh_key", "username": "admin", "created_at": "2024-01-01T00:00:00Z"}',
                                use_cases=["Store automation credentials", "Credential rotation", "Secure access management"]
                            )
                        ],
                        integration_patterns=[
                            "Automation Service retrieves credentials before connecting to target systems",
                            "Identity Service validates credential access permissions"
                        ],
                        best_practices=[
                            "Use least-privilege credentials for automation",
                            "Implement regular credential rotation",
                            "Audit credential access and usage",
                            "Use service accounts for automation rather than personal accounts"
                        ],
                        common_workflows=[
                            "1. Create service account → 2. Store credentials in asset service → 3. Configure automation to use credentials",
                            "1. Detect credential expiry → 2. Generate new credentials → 3. Update asset service → 4. Test connectivity"
                        ]
                    )
                ],
                api_endpoints=[
                    APIEndpoint(
                        path="/api/v1/assets",
                        method="GET",
                        description="List all assets with optional filtering",
                        parameters={"os_type": "Operating system filter", "environment": "Environment filter"},
                        example_request="GET /api/v1/assets?os_type=Windows",
                        example_response='[{"id": 1, "hostname": "web01", "os_type": "Windows"}]',
                        use_cases=["Asset discovery", "Target selection for automation"]
                    )
                ],
                integrations=[
                    ServiceIntegration(
                        service_name="automation-service",
                        integration_type="works_with",
                        description="Provides target systems and credentials for automation jobs",
                        example_workflow="Asset service provides target list → Automation service executes jobs on those targets"
                    ),
                    ServiceIntegration(
                        service_name="communication-service",
                        integration_type="works_with",
                        description="Provides contact information for asset owners and administrators",
                        example_workflow="Asset service provides owner contacts → Communication service sends notifications"
                    )
                ],
                common_use_cases=[
                    "Find all Windows machines for patch management",
                    "Get database servers for backup automation",
                    "Identify systems needing security updates",
                    "Manage credentials for automated deployments",
                    "Track asset compliance and configuration"
                ],
                example_workflows=[
                    "User requests 'patch all Windows servers' → Query asset service for Windows systems → Get credentials → Execute patch automation",
                    "User requests 'backup all databases' → Query asset service for database servers → Retrieve backup credentials → Schedule backup jobs"
                ],
                troubleshooting_scenarios=[
                    "If automation fails to connect: Check if credentials are stored and valid in asset service",
                    "If wrong systems are targeted: Verify asset tags and filters in asset service",
                    "If systems are missing: Check if they're registered in asset inventory"
                ],
                best_practices=[
                    "Always query asset service before running automation on groups of systems",
                    "Keep asset information current and accurate",
                    "Use meaningful tags and groups for asset organization",
                    "Implement proper credential rotation and management"
                ],
                when_to_use="When you need to find target systems, manage credentials, or maintain infrastructure inventory",
                when_not_to_use="For executing commands (use automation-service) or network diagnostics (use network-analyzer-service)",
                performance_characteristics="Fast queries for asset lookup, secure credential storage with encryption",
                limitations=[
                    "Requires manual asset registration for new systems",
                    "Credential storage limited by encryption key management",
                    "Asset discovery depends on network accessibility"
                ],
                security_considerations=[
                    "All credentials are encrypted at rest",
                    "Access control enforced for credential retrieval",
                    "Audit logging for all credential operations",
                    "Secure communication channels required"
                ]
            ),
            
            "automation-service": EnhancedServiceInfo(
                service_type="automation-service",
                name="Automation and Workflow Service",
                description="Advanced job execution, workflow orchestration, and system automation platform",
                detailed_description="""
The Automation Service is the execution engine for all system administration and automation tasks.
It handles command execution, workflow orchestration, job queuing, and result management.
Supports both immediate execution and complex multi-step workflows across multiple systems.
""",
                primary_purpose="Execute commands, manage workflows, and automate system administration tasks",
                capabilities=[
                    ServiceCapability(
                        name="Remote Command Execution",
                        description="Execute commands on remote systems via SSH and PowerShell",
                        detailed_description="""
Secure remote command execution supporting multiple protocols and authentication methods.
Handles both interactive and non-interactive commands, with support for environment variables,
working directory specification, and timeout management. Provides real-time output streaming
and comprehensive error handling.
""",
                        use_cases=[
                            "Execute PowerShell commands on Windows servers",
                            "Run bash scripts on Linux systems",
                            "Perform system administration tasks remotely",
                            "Deploy applications and configurations",
                            "Collect system information and logs"
                        ],
                        keywords=["execute", "command", "ssh", "powershell", "remote", "script", "automation"],
                        examples=[
                            "Windows: Get-ComputerInfo | Select-Object WindowsProductName, TotalPhysicalMemory",
                            "Linux: df -h && free -m && uptime",
                            "Service management: systemctl restart nginx",
                            "File operations: Copy-Item C:\\source\\* C:\\destination\\ -Recurse"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/jobs",
                                method="POST",
                                description="Create and execute a new automation job",
                                parameters={
                                    "name": "Job name for identification",
                                    "description": "Job description",
                                    "target_systems": "List of target system IDs",
                                    "commands": "List of commands to execute",
                                    "timeout": "Execution timeout in seconds"
                                },
                                example_request='POST /api/v1/jobs {"name": "System Info Collection", "target_systems": ["1", "2"], "commands": ["Get-ComputerInfo"]}',
                                example_response='{"job_id": 123, "execution_id": "abc-123", "status": "running", "created_at": "2024-01-01T00:00:00Z"}',
                                use_cases=["System administration", "Information gathering", "Configuration management"]
                            ),
                            APIEndpoint(
                                path="/api/v1/executions/{execution_id}",
                                method="GET",
                                description="Get execution status and results",
                                parameters={
                                    "execution_id": "Unique execution identifier"
                                },
                                example_request="GET /api/v1/executions/abc-123",
                                example_response='{"execution_id": "abc-123", "status": "completed", "results": [{"target": "1", "output": "Windows 10 Pro...", "exit_code": 0}]}',
                                use_cases=["Monitor job progress", "Retrieve results", "Troubleshoot failures"]
                            )
                        ],
                        integration_patterns=[
                            "Asset Service provides target systems and credentials",
                            "Communication Service sends notifications about job completion",
                            "Celery Beat schedules recurring automation jobs"
                        ],
                        best_practices=[
                            "Use idempotent commands when possible",
                            "Implement proper error handling and rollback procedures",
                            "Set appropriate timeouts for long-running operations",
                            "Use service accounts with minimal required privileges"
                        ],
                        common_workflows=[
                            "1. Get targets from asset service → 2. Create job → 3. Monitor execution → 4. Process results",
                            "1. Validate connectivity → 2. Execute commands → 3. Verify results → 4. Send notifications"
                        ]
                    ),
                    ServiceCapability(
                        name="Workflow Orchestration",
                        description="Create and manage complex multi-step workflows",
                        detailed_description="""
Advanced workflow engine supporting conditional logic, parallel execution, error handling,
and rollback procedures. Workflows can span multiple systems and services, with support
for approval gates, manual interventions, and complex dependency management.
""",
                        use_cases=[
                            "Multi-step application deployments",
                            "Complex system maintenance procedures",
                            "Disaster recovery workflows",
                            "Compliance and audit procedures",
                            "Infrastructure provisioning and decommissioning"
                        ],
                        keywords=["workflow", "orchestration", "pipeline", "automation", "multi-step", "deployment"],
                        examples=[
                            "Deployment workflow: Build → Test → Deploy to staging → Approval → Deploy to production",
                            "Maintenance workflow: Stop services → Apply updates → Restart services → Verify functionality",
                            "Backup workflow: Stop database → Create backup → Verify backup → Restart database → Notify completion"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/workflows",
                                method="POST",
                                description="Create and execute a complex workflow",
                                parameters={
                                    "name": "Workflow name",
                                    "description": "Workflow description",
                                    "steps": "List of workflow steps with dependencies",
                                    "rollback_steps": "Steps to execute on failure"
                                },
                                example_request='POST /api/v1/workflows {"name": "App Deployment", "steps": [{"name": "Build", "commands": ["npm run build"]}, {"name": "Deploy", "commands": ["docker deploy"], "depends_on": ["Build"]}]}',
                                example_response='{"workflow_id": 456, "execution_id": "def-456", "status": "running", "current_step": "Build"}',
                                use_cases=["Complex deployments", "System maintenance", "Multi-system operations"]
                            )
                        ],
                        integration_patterns=[
                            "Integrates with all other services for comprehensive automation",
                            "Can trigger communication service notifications at each step",
                            "Uses asset service for multi-system targeting"
                        ],
                        best_practices=[
                            "Design workflows with proper error handling and rollback",
                            "Use checkpoints for long-running workflows",
                            "Implement approval gates for critical operations",
                            "Test workflows in non-production environments first"
                        ],
                        common_workflows=[
                            "CI/CD Pipeline: Code → Build → Test → Deploy → Verify → Notify",
                            "Maintenance Window: Notify → Stop services → Update → Test → Start services → Verify → Report"
                        ]
                    )
                ],
                api_endpoints=[
                    APIEndpoint(
                        path="/api/v1/jobs",
                        method="POST",
                        description="Create and execute automation jobs",
                        parameters={"name": "Job name", "commands": "Commands to execute", "target_systems": "Target system IDs"},
                        example_request='POST /api/v1/jobs {"name": "System Check", "commands": ["systemctl status"], "target_systems": ["1"]}',
                        example_response='{"job_id": 123, "execution_id": "abc-123", "status": "running"}',
                        use_cases=["System administration", "Remote command execution", "Automation tasks"]
                    )
                ],
                integrations=[
                    ServiceIntegration(
                        service_name="asset-service",
                        integration_type="depends_on",
                        description="Requires target systems and credentials from asset service",
                        example_workflow="Asset service provides targets → Automation service executes jobs"
                    ),
                    ServiceIntegration(
                        service_name="celery-beat",
                        integration_type="triggered_by",
                        description="Scheduled jobs are triggered by celery-beat scheduler",
                        example_workflow="Celery-beat triggers scheduled job → Automation service executes"
                    )
                ],
                common_use_cases=[
                    "Execute system administration commands",
                    "Deploy applications and configurations",
                    "Collect system information and metrics",
                    "Perform maintenance and updates",
                    "Automate repetitive operational tasks"
                ],
                example_workflows=[
                    "System Information Collection: Get targets from asset service → Execute system info commands → Collect results → Send via communication service",
                    "Service Restart: Identify target systems → Stop service → Verify stopped → Start service → Verify running → Report status"
                ],
                troubleshooting_scenarios=[
                    "If job fails to start: Check if target systems are reachable and credentials are valid",
                    "If commands fail: Verify command syntax and permissions on target systems",
                    "If job hangs: Check timeout settings and network connectivity"
                ],
                best_practices=[
                    "Always validate target systems before execution",
                    "Use appropriate timeouts for different types of operations",
                    "Implement proper error handling and logging",
                    "Test automation in non-production environments first"
                ],
                when_to_use="For executing commands, managing workflows, and automating system administration tasks",
                when_not_to_use="For network diagnostics (use network-analyzer-service) or scheduling (use celery-beat)",
                performance_characteristics="Concurrent execution across multiple systems, scalable job queuing",
                limitations=[
                    "Requires network connectivity to target systems",
                    "Limited by target system performance and availability",
                    "Command execution subject to target system security policies"
                ],
                security_considerations=[
                    "Secure credential handling and storage",
                    "Encrypted communication channels",
                    "Audit logging for all executed commands",
                    "Role-based access control for job execution"
                ]
            ),
            
            "communication-service": EnhancedServiceInfo(
                service_type="communication-service",
                name="Communication and Notification Service",
                description="Multi-channel notification and external integration platform",
                detailed_description="""
The Communication Service handles all external communications including email notifications,
SMS alerts, Slack integrations, and webhook deliveries. It provides template management,
delivery tracking, and integration with external systems for comprehensive notification workflows.
""",
                primary_purpose="Handle notifications, alerts, and communication with external systems",
                capabilities=[
                    ServiceCapability(
                        name="Email Notifications",
                        description="Send email notifications with rich content and attachments",
                        detailed_description="""
Comprehensive email delivery system supporting HTML templates, attachments, bulk sending,
and delivery tracking. Integrates with multiple email providers and supports both
transactional and marketing email workflows.
""",
                        use_cases=[
                            "Send automation job results via email",
                            "Alert administrators about system issues",
                            "Deliver reports and dashboards",
                            "Send scheduled status updates",
                            "Notify stakeholders about deployments"
                        ],
                        keywords=["email", "notification", "alert", "report", "delivery", "smtp"],
                        examples=[
                            "Send system info report: POST /api/v1/notifications/email with system data",
                            "Alert on job failure: Automated email with error details and logs",
                            "Weekly status report: Scheduled email with system metrics and health"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/notifications/email",
                                method="POST",
                                description="Send email notification",
                                parameters={
                                    "to": "Recipient email addresses",
                                    "subject": "Email subject line",
                                    "body": "Email body content (HTML or text)",
                                    "attachments": "Optional file attachments",
                                    "template": "Optional template name"
                                },
                                example_request='POST /api/v1/notifications/email {"to": ["admin@company.com"], "subject": "System Report", "body": "System information attached", "attachments": ["system_info.txt"]}',
                                example_response='{"notification_id": "email-123", "status": "sent", "delivered_at": "2024-01-01T00:00:00Z"}',
                                use_cases=["Automation results", "Alert notifications", "Report delivery"]
                            )
                        ],
                        integration_patterns=[
                            "Automation Service sends job results via email",
                            "Asset Service provides contact information for notifications",
                            "Celery Beat schedules regular email reports"
                        ],
                        best_practices=[
                            "Use templates for consistent formatting",
                            "Include relevant context and actionable information",
                            "Implement proper error handling for delivery failures",
                            "Respect email frequency limits to avoid spam"
                        ],
                        common_workflows=[
                            "1. Automation completes → 2. Format results → 3. Send email notification → 4. Track delivery",
                            "1. System alert triggered → 2. Gather context → 3. Send alert email → 4. Log notification"
                        ]
                    ),
                    ServiceCapability(
                        name="Template Management",
                        description="Manage notification templates for consistent messaging",
                        detailed_description="""
Template engine supporting dynamic content, conditional logic, and multi-format output.
Templates can include variables, loops, and conditional sections for flexible content generation.
Supports email, SMS, and webhook templates with preview and testing capabilities.
""",
                        use_cases=[
                            "Standardize automation result notifications",
                            "Create branded email templates",
                            "Generate dynamic reports with data",
                            "Implement multi-language notifications",
                            "Maintain consistent messaging across channels"
                        ],
                        keywords=["template", "format", "message", "content", "dynamic", "branding"],
                        examples=[
                            "System report template with dynamic data insertion",
                            "Alert template with severity-based formatting",
                            "Weekly summary template with charts and metrics"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/templates",
                                method="POST",
                                description="Create or update notification template",
                                parameters={
                                    "name": "Template name",
                                    "type": "Template type (email, sms, webhook)",
                                    "content": "Template content with variables",
                                    "variables": "Available template variables"
                                },
                                example_request='POST /api/v1/templates {"name": "system_report", "type": "email", "content": "System {{hostname}} status: {{status}}", "variables": ["hostname", "status"]}',
                                example_response='{"template_id": "tpl-123", "name": "system_report", "created_at": "2024-01-01T00:00:00Z"}',
                                use_cases=["Template creation", "Content standardization", "Dynamic messaging"]
                            )
                        ],
                        integration_patterns=[
                            "All services can use templates for consistent messaging",
                            "Templates can be triggered by automation workflows",
                            "Asset data can be injected into templates dynamically"
                        ],
                        best_practices=[
                            "Use descriptive template names and documentation",
                            "Test templates with sample data before deployment",
                            "Version control template changes",
                            "Include fallback content for missing variables"
                        ],
                        common_workflows=[
                            "1. Create template → 2. Test with sample data → 3. Deploy → 4. Use in notifications",
                            "1. Automation generates data → 2. Select template → 3. Populate variables → 4. Send notification"
                        ]
                    )
                ],
                api_endpoints=[
                    APIEndpoint(
                        path="/api/v1/notifications",
                        method="POST",
                        description="Send notifications via multiple channels",
                        parameters={"channel": "Notification channel", "recipients": "Recipient list", "content": "Message content"},
                        example_request='POST /api/v1/notifications {"channel": "email", "recipients": ["admin@company.com"], "content": "System alert"}',
                        example_response='{"notification_id": "notif-123", "status": "sent", "channel": "email"}',
                        use_cases=["Alert notifications", "Report delivery", "Status updates"]
                    )
                ],
                integrations=[
                    ServiceIntegration(
                        service_name="automation-service",
                        integration_type="consumes",
                        description="Receives automation results and sends notifications",
                        example_workflow="Automation completes → Communication service sends results via email"
                    ),
                    ServiceIntegration(
                        service_name="asset-service",
                        integration_type="works_with",
                        description="Uses asset contact information for notifications",
                        example_workflow="Asset service provides contacts → Communication service sends notifications"
                    )
                ],
                common_use_cases=[
                    "Send automation job results via email",
                    "Alert administrators about system issues",
                    "Deliver scheduled reports and dashboards",
                    "Notify stakeholders about changes",
                    "Integrate with external communication platforms"
                ],
                example_workflows=[
                    "Automation Result Notification: Job completes → Format results → Send email with attachment → Track delivery",
                    "System Alert Workflow: Issue detected → Gather context → Send multi-channel alert → Log notification"
                ],
                troubleshooting_scenarios=[
                    "If emails not delivered: Check SMTP configuration and recipient addresses",
                    "If notifications delayed: Check queue status and processing capacity",
                    "If templates not rendering: Verify template syntax and variable availability"
                ],
                best_practices=[
                    "Use appropriate notification channels for different types of messages",
                    "Implement delivery confirmation and retry logic",
                    "Maintain template consistency and branding",
                    "Respect recipient preferences and frequency limits"
                ],
                when_to_use="When you need to send notifications, alerts, reports, or integrate with external communication systems",
                when_not_to_use="For task execution (use automation-service) or data storage (use asset-service)",
                performance_characteristics="Asynchronous delivery, queue-based processing, delivery tracking",
                limitations=[
                    "Dependent on external email/SMS providers",
                    "Subject to rate limits and delivery policies",
                    "Template complexity may affect rendering performance"
                ],
                security_considerations=[
                    "Secure handling of recipient information",
                    "Encrypted communication with external providers",
                    "Access control for template and notification management",
                    "Audit logging for all notification activities"
                ]
            ),
            
            "celery-beat": EnhancedServiceInfo(
                service_type="celery-beat",
                name="Advanced Task Scheduler",
                description="Sophisticated scheduling system for recurring and future task automation",
                detailed_description="""
Celery Beat is the scheduling engine that handles all time-based automation in OpsConductor.
It supports complex cron expressions, recurring tasks, future scheduling, and dynamic schedule
management. Integrates seamlessly with the automation service for scheduled job execution.
""",
                primary_purpose="Schedule recurring tasks, manage time-based automation, and handle complex scheduling requirements",
                capabilities=[
                    ServiceCapability(
                        name="Recurring Task Scheduling",
                        description="Schedule tasks to run at regular intervals with advanced timing control",
                        detailed_description="""
Comprehensive recurring task scheduling supporting interval-based, cron-based, and custom
scheduling patterns. Handles timezone management, daylight saving time transitions, and
schedule conflict resolution. Supports dynamic schedule modification and pause/resume functionality.
""",
                        use_cases=[
                            "Schedule system health checks every 15 minutes",
                            "Run backup jobs daily at 2 AM",
                            "Collect system metrics every 5 minutes",
                            "Send weekly status reports on Fridays",
                            "Perform maintenance tasks during off-hours"
                        ],
                        keywords=["schedule", "recurring", "periodic", "interval", "cron", "repeat", "automation"],
                        examples=[
                            "Every 15 minutes: interval=15, unit='minutes'",
                            "Daily at 2 AM: cron='0 2 * * *'",
                            "Weekdays at 9 AM: cron='0 9 * * 1-5'",
                            "Every 5 minutes until 11 PM: interval=5, unit='minutes', end_time='23:00'"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/schedules",
                                method="POST",
                                description="Create a new scheduled task",
                                parameters={
                                    "name": "Schedule name for identification",
                                    "task": "Task to execute (automation job)",
                                    "schedule_type": "Type: interval, cron, or one_time",
                                    "schedule_config": "Schedule configuration (interval, cron expression, etc.)",
                                    "start_time": "When to start the schedule",
                                    "end_time": "When to stop the schedule (optional)",
                                    "timezone": "Timezone for schedule execution"
                                },
                                example_request='POST /api/v1/schedules {"name": "System Info Collection", "task": "collect_system_info", "schedule_type": "interval", "schedule_config": {"interval": 15, "unit": "minutes"}, "end_time": "23:00"}',
                                example_response='{"schedule_id": "sched-123", "name": "System Info Collection", "status": "active", "next_run": "2024-01-01T00:15:00Z"}',
                                use_cases=["Recurring automation", "Periodic monitoring", "Scheduled maintenance"]
                            ),
                            APIEndpoint(
                                path="/api/v1/schedules/{schedule_id}/pause",
                                method="POST",
                                description="Pause a scheduled task",
                                parameters={
                                    "schedule_id": "ID of the schedule to pause"
                                },
                                example_request="POST /api/v1/schedules/sched-123/pause",
                                example_response='{"schedule_id": "sched-123", "status": "paused", "paused_at": "2024-01-01T00:00:00Z"}',
                                use_cases=["Temporary schedule suspension", "Maintenance windows", "Schedule management"]
                            )
                        ],
                        integration_patterns=[
                            "Triggers automation service jobs based on schedule",
                            "Can schedule communication service notifications",
                            "Integrates with asset service for scheduled asset operations"
                        ],
                        best_practices=[
                            "Use appropriate intervals to avoid system overload",
                            "Set end times for temporary recurring tasks",
                            "Monitor schedule execution and handle failures gracefully",
                            "Use meaningful schedule names and descriptions"
                        ],
                        common_workflows=[
                            "1. Create schedule → 2. Activate → 3. Monitor execution → 4. Handle results",
                            "1. Define recurring task → 2. Set schedule parameters → 3. Test execution → 4. Deploy schedule"
                        ]
                    ),
                    ServiceCapability(
                        name="Complex Cron Scheduling",
                        description="Advanced cron expression support for sophisticated timing requirements",
                        detailed_description="""
Full cron expression support with extensions for complex scheduling scenarios. Handles
business day scheduling, holiday exclusions, multiple timezone support, and advanced
patterns like 'last Friday of the month' or 'every 3rd Tuesday'. Includes schedule
validation and conflict detection.
""",
                        use_cases=[
                            "Run reports on the last business day of each month",
                            "Schedule maintenance during specific time windows",
                            "Execute tasks only on weekdays during business hours",
                            "Handle timezone-specific scheduling for global operations",
                            "Implement complex business rule-based scheduling"
                        ],
                        keywords=["cron", "expression", "complex", "business", "timezone", "advanced"],
                        examples=[
                            "Business hours only: '0 9-17 * * 1-5' (9 AM to 5 PM, weekdays)",
                            "Last day of month: '0 0 L * *'",
                            "Every 3rd Tuesday: '0 0 * * 2#3'",
                            "Quarterly reports: '0 0 1 1,4,7,10 *' (1st day of quarters)"
                        ],
                        api_endpoints=[
                            APIEndpoint(
                                path="/api/v1/schedules/validate",
                                method="POST",
                                description="Validate cron expression and preview next execution times",
                                parameters={
                                    "cron_expression": "Cron expression to validate",
                                    "timezone": "Timezone for validation",
                                    "preview_count": "Number of next executions to preview"
                                },
                                example_request='POST /api/v1/schedules/validate {"cron_expression": "0 9 * * 1-5", "timezone": "America/New_York", "preview_count": 5}',
                                example_response='{"valid": true, "next_executions": ["2024-01-01T09:00:00-05:00", "2024-01-02T09:00:00-05:00"], "description": "At 9:00 AM, Monday through Friday"}',
                                use_cases=["Schedule validation", "Execution preview", "Cron expression testing"]
                            )
                        ],
                        integration_patterns=[
                            "Validates schedules before activation",
                            "Provides execution previews for planning",
                            "Handles timezone conversions for global scheduling"
                        ],
                        best_practices=[
                            "Validate cron expressions before deployment",
                            "Consider timezone implications for global systems",
                            "Use schedule previews to verify timing",
                            "Document complex cron expressions clearly"
                        ],
                        common_workflows=[
                            "1. Design cron expression → 2. Validate → 3. Preview executions → 4. Deploy schedule",
                            "1. Business requirement → 2. Translate to cron → 3. Test → 4. Implement"
                        ]
                    )
                ],
                api_endpoints=[
                    APIEndpoint(
                        path="/api/v1/schedules",
                        method="GET",
                        description="List all scheduled tasks",
                        parameters={"status": "Filter by status", "task_type": "Filter by task type"},
                        example_request="GET /api/v1/schedules?status=active",
                        example_response='[{"schedule_id": "sched-123", "name": "System Check", "status": "active", "next_run": "2024-01-01T00:15:00Z"}]',
                        use_cases=["Schedule management", "Monitoring", "Status checking"]
                    )
                ],
                integrations=[
                    ServiceIntegration(
                        service_name="automation-service",
                        integration_type="triggers",
                        description="Triggers automation jobs based on schedule",
                        example_workflow="Celery-beat schedule triggers → Automation service executes job"
                    ),
                    ServiceIntegration(
                        service_name="communication-service",
                        integration_type="triggers",
                        description="Can schedule notification delivery",
                        example_workflow="Celery-beat triggers → Communication service sends scheduled notification"
                    )
                ],
                common_use_cases=[
                    "Schedule recurring system health checks",
                    "Automate regular backup and maintenance tasks",
                    "Send periodic status reports and notifications",
                    "Implement time-based compliance and audit procedures",
                    "Coordinate scheduled operations across multiple systems"
                ],
                example_workflows=[
                    "Recurring System Check: Create schedule → Set 15-minute interval → Trigger automation job → Collect results → Send notifications",
                    "Daily Backup: Schedule for 2 AM daily → Trigger backup automation → Verify completion → Send status email"
                ],
                troubleshooting_scenarios=[
                    "If scheduled tasks not running: Check schedule status and celery-beat service health",
                    "If timing is incorrect: Verify timezone settings and cron expression",
                    "If tasks overlap: Review schedule intervals and execution duration"
                ],
                best_practices=[
                    "Use appropriate intervals to avoid system overload",
                    "Set reasonable timeouts for scheduled tasks",
                    "Monitor schedule execution and handle failures",
                    "Use end times for temporary recurring schedules"
                ],
                when_to_use="For any time-based automation: recurring tasks, periodic execution, scheduled operations",
                when_not_to_use="For immediate execution (use automation-service directly) or event-driven automation",
                performance_characteristics="Precise timing, scalable schedule management, persistent schedule storage",
                limitations=[
                    "Dependent on system clock accuracy",
                    "Limited by underlying task execution capacity",
                    "Complex schedules may require careful resource planning"
                ],
                security_considerations=[
                    "Secure schedule configuration and management",
                    "Access control for schedule creation and modification",
                    "Audit logging for all schedule operations",
                    "Protection against schedule-based attacks"
                ]
            )
        }
    
    def get_comprehensive_service_context(self, user_request: str = "") -> str:
        """Generate comprehensive service context for AI reasoning"""
        
        context_parts = []
        
        context_parts.append("=== OPSCONDUCTOR PLATFORM SERVICES - COMPREHENSIVE KNOWLEDGE BASE ===")
        context_parts.append("")
        context_parts.append("You have access to a sophisticated automation platform with the following services:")
        context_parts.append("")
        
        for service_type, service_info in self.services.items():
            context_parts.append(f"## {service_info.name.upper()} ({service_type})")
            context_parts.append(f"**Purpose**: {service_info.primary_purpose}")
            context_parts.append(f"**Description**: {service_info.detailed_description.strip()}")
            context_parts.append("")
            
            context_parts.append("**Key Capabilities:**")
            for capability in service_info.capabilities:
                context_parts.append(f"• **{capability.name}**: {capability.description}")
                context_parts.append(f"  - Use cases: {', '.join(capability.use_cases[:3])}")
                context_parts.append(f"  - Keywords: {', '.join(capability.keywords[:5])}")
                if capability.examples:
                    context_parts.append(f"  - Example: {capability.examples[0]}")
                context_parts.append("")
            
            context_parts.append("**Common Use Cases:**")
            for use_case in service_info.common_use_cases[:3]:
                context_parts.append(f"• {use_case}")
            context_parts.append("")
            
            context_parts.append("**Integration Patterns:**")
            for integration in service_info.integrations[:2]:
                context_parts.append(f"• {integration.description}")
            context_parts.append("")
            
            context_parts.append(f"**When to Use**: {service_info.when_to_use}")
            context_parts.append(f"**When NOT to Use**: {service_info.when_not_to_use}")
            context_parts.append("")
            context_parts.append("---")
            context_parts.append("")
        
        context_parts.append("=== SERVICE INTEGRATION PATTERNS ===")
        context_parts.append("")
        context_parts.append("**Common Integration Workflows:**")
        context_parts.append("1. **Asset Discovery → Automation**: Asset service provides targets → Automation service executes")
        context_parts.append("2. **Scheduled Automation**: Celery-beat triggers → Automation service executes → Communication service notifies")
        context_parts.append("3. **System Monitoring**: Asset service provides systems → Automation collects data → Communication sends reports")
        context_parts.append("4. **Maintenance Workflows**: Celery-beat schedules → Automation performs maintenance → Communication confirms completion")
        context_parts.append("")
        
        context_parts.append("=== REASONING GUIDELINES FOR AI ===")
        context_parts.append("")
        context_parts.append("When analyzing user requests, consider:")
        context_parts.append("1. **Target Identification**: Use asset-service to find specific systems (e.g., 'Windows machines', 'database servers')")
        context_parts.append("2. **Action Execution**: Use automation-service for command execution and system operations")
        context_parts.append("3. **Scheduling**: Use celery-beat for any time-based requirements ('every X minutes', 'daily', 'until Y time')")
        context_parts.append("4. **Communication**: Use communication-service for notifications, emails, alerts, and reporting")
        context_parts.append("5. **Credentials**: Asset-service manages all system credentials and connection information")
        context_parts.append("")
        context_parts.append("**Example Request Analysis:**")
        context_parts.append("'Connect to each Windows machine and get system information and email it every 15 minutes until 11 PM'")
        context_parts.append("• 'each Windows machine' → Asset-service: query for os_type='Windows'")
        context_parts.append("• 'get system information' → Automation-service: execute Get-ComputerInfo commands")
        context_parts.append("• 'email it' → Communication-service: send email notifications with results")
        context_parts.append("• 'every 15 minutes until 11 PM' → Celery-beat: schedule recurring task with end time")
        context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_service_for_keywords(self, keywords: List[str]) -> List[str]:
        """Get recommended services based on keywords"""
        recommendations = []
        
        for service_type, service_info in self.services.items():
            score = 0
            for capability in service_info.capabilities:
                for keyword in capability.keywords:
                    if any(kw.lower() in keyword.lower() for kw in keywords):
                        score += 1
            
            if score > 0:
                recommendations.append((service_type, score))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [service_type for service_type, _ in recommendations]
    
    def analyze_user_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze user request and provide service recommendations"""
        
        request_lower = user_request.lower()
        analysis = {
            "identified_services": [],
            "reasoning": [],
            "suggested_workflow": [],
            "key_insights": []
        }
        
        # Analyze for asset service needs
        if any(term in request_lower for term in ["windows", "linux", "machines", "servers", "systems", "each", "all"]):
            analysis["identified_services"].append("asset-service")
            analysis["reasoning"].append("Request mentions systems/machines - need asset service to identify targets")
            analysis["key_insights"].append("Use asset service to query for specific system types instead of assumptions")
        
        # Analyze for automation service needs
        if any(term in request_lower for term in ["execute", "run", "command", "script", "get", "collect", "install", "update", "restart", "stop", "start"]):
            analysis["identified_services"].append("automation-service")
            analysis["reasoning"].append("Request involves command execution - need automation service")
            analysis["key_insights"].append("Use automation service for all command execution and system operations")
        
        # Analyze for communication service needs
        if any(term in request_lower for term in ["email", "notify", "alert", "send", "report", "message"]):
            analysis["identified_services"].append("communication-service")
            analysis["reasoning"].append("Request involves notifications/communication - need communication service")
            analysis["key_insights"].append("Use communication service for email notifications and alerts")
        
        # Analyze for scheduling needs
        if any(term in request_lower for term in ["every", "minutes", "hours", "daily", "weekly", "schedule", "recurring", "until", "at"]):
            analysis["identified_services"].append("celery-beat")
            analysis["reasoning"].append("Request involves timing/scheduling - need celery-beat scheduler")
            analysis["key_insights"].append("Use celery-beat for any time-based or recurring automation")
        
        # Generate suggested workflow
        if "asset-service" in analysis["identified_services"]:
            analysis["suggested_workflow"].append("1. Query asset service to identify target systems")
        
        if "automation-service" in analysis["identified_services"]:
            analysis["suggested_workflow"].append("2. Use automation service to execute commands on targets")
        
        if "communication-service" in analysis["identified_services"]:
            analysis["suggested_workflow"].append("3. Use communication service to send results/notifications")
        
        if "celery-beat" in analysis["identified_services"]:
            analysis["suggested_workflow"].append("4. Use celery-beat to schedule recurring execution")
        
        return analysis
    
    def get_detailed_service_knowledge(self, service_type: str) -> str:
        """Get detailed knowledge about a specific service for AI reasoning"""
        
        if service_type not in self.services:
            return f"Service {service_type} not found in catalog"
        
        service = self.services[service_type]
        
        knowledge_parts = []
        knowledge_parts.append(f"=== DETAILED KNOWLEDGE: {service.name.upper()} ===")
        knowledge_parts.append(f"Purpose: {service.primary_purpose}")
        knowledge_parts.append(f"Description: {service.detailed_description.strip()}")
        knowledge_parts.append("")
        
        knowledge_parts.append("CAPABILITIES:")
        for capability in service.capabilities:
            knowledge_parts.append(f"• {capability.name}")
            knowledge_parts.append(f"  Description: {capability.detailed_description.strip()}")
            knowledge_parts.append(f"  Use Cases: {', '.join(capability.use_cases)}")
            knowledge_parts.append(f"  Keywords: {', '.join(capability.keywords)}")
            if capability.examples:
                knowledge_parts.append(f"  Examples: {'; '.join(capability.examples)}")
            knowledge_parts.append("")
        
        knowledge_parts.append("COMMON USE CASES:")
        for use_case in service.common_use_cases:
            knowledge_parts.append(f"• {use_case}")
        knowledge_parts.append("")
        
        knowledge_parts.append("EXAMPLE WORKFLOWS:")
        for workflow in service.example_workflows:
            knowledge_parts.append(f"• {workflow}")
        knowledge_parts.append("")
        
        knowledge_parts.append("BEST PRACTICES:")
        for practice in service.best_practices:
            knowledge_parts.append(f"• {practice}")
        knowledge_parts.append("")
        
        knowledge_parts.append(f"WHEN TO USE: {service.when_to_use}")
        knowledge_parts.append(f"WHEN NOT TO USE: {service.when_not_to_use}")
        
        return "\n".join(knowledge_parts)

# Global instance
enhanced_service_catalog = EnhancedServiceCatalog()
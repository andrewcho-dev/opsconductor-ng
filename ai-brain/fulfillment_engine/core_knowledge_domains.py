#!/usr/bin/env python3
"""
Core Knowledge Domains for OpsConductor Foundation
Comprehensive knowledge about core services and system capabilities
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dynamic_service_catalog import (
    KnowledgeDomain, 
    KnowledgeMetadata, 
    KnowledgeDomainType, 
    ContextPriority,
    APIDiscoveryResult
)

class AssetServiceDomain(KnowledgeDomain):
    """Comprehensive Asset Service knowledge domain"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="asset_service",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.CRITICAL,
            keywords=["asset", "target", "system", "inventory", "credential", "connection", "host", "server"],
            dependencies=[],
            performance_metrics={}
        )
        super().__init__("asset_service", metadata)
        self.knowledge = self._initialize_asset_knowledge()
    
    def _initialize_asset_knowledge(self) -> Dict[str, Any]:
        return {
            "service_info": {
                "name": "OpsConductor Asset Service",
                "description": "Centralized asset and credential management for infrastructure automation",
                "base_url": "http://asset-service:3002",
                "database": "PostgreSQL with encrypted credential storage",
                "authentication": "JWT tokens via identity service"
            },
            "capabilities": {
                "asset_management": {
                    "description": "Complete lifecycle management of infrastructure assets",
                    "keywords": ["asset", "inventory", "system", "server", "device"],
                    "endpoints": [
                        {
                            "path": "/assets",
                            "method": "GET",
                            "description": "List all assets with filtering and search",
                            "parameters": {
                                "skip": "Pagination offset (default: 0)",
                                "limit": "Number of results (default: 100, max: 1000)",
                                "search": "Search in name, hostname, description",
                                "os_type": "Filter by OS type (windows, linux, unix, macos, other)",
                                "service_type": "Filter by primary service type",
                                "is_active": "Filter by active status (true/false)"
                            },
                            "example_request": "GET /assets?os_type=windows&search=web&limit=50",
                            "example_response": {
                                "success": True,
                                "data": {
                                    "assets": [
                                        {
                                            "id": 1,
                                            "name": "Web Server 01",
                                            "hostname": "web01.company.com",
                                            "ip_address": "192.168.1.100",
                                            "os_type": "windows",
                                            "service_type": "rdp",
                                            "port": 3389,
                                            "environment": "production",
                                            "status": "active"
                                        }
                                    ],
                                    "total": 1,
                                    "skip": 0,
                                    "limit": 50
                                }
                            }
                        },
                        {
                            "path": "/assets",
                            "method": "POST",
                            "description": "Create a new asset with credentials",
                            "parameters": {
                                "name": "Human-readable asset name",
                                "hostname": "FQDN or hostname",
                                "ip_address": "IP address (optional)",
                                "os_type": "Operating system type",
                                "service_type": "Primary service type",
                                "port": "Primary service port",
                                "credential_type": "Type of credentials (username_password, ssh_key, api_key, etc.)",
                                "username": "Username for authentication",
                                "password": "Password (will be encrypted)",
                                "environment": "Environment (production, staging, development, test)",
                                "tags": "Array of tags for categorization"
                            },
                            "example_request": {
                                "name": "Database Server",
                                "hostname": "db01.company.com",
                                "ip_address": "192.168.1.50",
                                "os_type": "linux",
                                "service_type": "ssh",
                                "port": 22,
                                "credential_type": "username_password",
                                "username": "admin",
                                "password": "secure_password",
                                "environment": "production",
                                "tags": ["database", "mysql", "critical"]
                            }
                        },
                        {
                            "path": "/assets/{asset_id}",
                            "method": "GET",
                            "description": "Get detailed asset information including decrypted credentials",
                            "parameters": {
                                "asset_id": "Unique asset identifier"
                            },
                            "example_request": "GET /assets/1"
                        },
                        {
                            "path": "/assets/{asset_id}/test",
                            "method": "POST",
                            "description": "Test connectivity to an asset using stored credentials",
                            "parameters": {
                                "asset_id": "Asset ID to test"
                            },
                            "example_response": {
                                "success": True,
                                "data": {
                                    "connection_status": "success",
                                    "response_time_ms": 45,
                                    "details": "SSH connection successful"
                                }
                            }
                        }
                    ],
                    "use_cases": [
                        "Infrastructure inventory management",
                        "Target system discovery for automation",
                        "Credential storage and retrieval",
                        "Asset categorization and tagging",
                        "Environment-based asset filtering"
                    ]
                },
                "credential_management": {
                    "description": "Secure storage and management of authentication credentials",
                    "keywords": ["credential", "password", "key", "authentication", "security"],
                    "supported_types": [
                        {
                            "type": "username_password",
                            "description": "Traditional username and password authentication",
                            "fields": ["username", "password"],
                            "use_cases": ["SSH, RDP, database connections"]
                        },
                        {
                            "type": "ssh_key",
                            "description": "SSH public/private key authentication",
                            "fields": ["username", "private_key", "public_key", "passphrase"],
                            "use_cases": ["Passwordless SSH access, Git repositories"]
                        },
                        {
                            "type": "api_key",
                            "description": "API key authentication",
                            "fields": ["api_key"],
                            "use_cases": ["REST APIs, cloud services"]
                        },
                        {
                            "type": "bearer_token",
                            "description": "Bearer token authentication",
                            "fields": ["bearer_token"],
                            "use_cases": ["OAuth2, JWT-based APIs"]
                        },
                        {
                            "type": "certificate",
                            "description": "Certificate-based authentication",
                            "fields": ["certificate", "private_key", "passphrase"],
                            "use_cases": ["TLS client authentication, enterprise PKI"]
                        }
                    ],
                    "security_features": [
                        "AES-256 encryption for sensitive data",
                        "Encrypted storage in PostgreSQL",
                        "Automatic credential rotation support",
                        "Audit logging for credential access",
                        "Role-based access control"
                    ]
                },
                "service_discovery": {
                    "description": "Discovery and cataloging of network services",
                    "keywords": ["service", "port", "protocol", "discovery", "scan"],
                    "supported_services": [
                        {"service": "ssh", "port": 22, "category": "Remote Access"},
                        {"service": "rdp", "port": 3389, "category": "Remote Access"},
                        {"service": "winrm", "port": 5985, "category": "Windows Management"},
                        {"service": "winrm_https", "port": 5986, "category": "Windows Management"},
                        {"service": "http", "port": 80, "category": "Web Services"},
                        {"service": "https", "port": 443, "category": "Web Services"},
                        {"service": "mysql", "port": 3306, "category": "Database Services"},
                        {"service": "postgresql", "port": 5432, "category": "Database Services"},
                        {"service": "smtp", "port": 25, "category": "Email Services"},
                        {"service": "snmp", "port": 161, "category": "Network Services"}
                    ]
                }
            },
            "integration_patterns": [
                {
                    "name": "Target System Discovery",
                    "description": "Find and filter target systems for automation tasks",
                    "steps": [
                        "Query asset service with appropriate filters (os_type, environment, tags)",
                        "Extract target IDs and connection details",
                        "Validate connectivity using test endpoints",
                        "Use target IDs in automation service calls"
                    ],
                    "example_queries": [
                        "GET /assets?os_type=windows&environment=production (find Windows production servers)",
                        "GET /assets?tags=database&status=active (find active database servers)",
                        "GET /assets?search=web&service_type=https (find web servers with HTTPS)"
                    ]
                },
                {
                    "name": "Credential Retrieval for Automation",
                    "description": "Securely retrieve credentials for automation tasks",
                    "steps": [
                        "Get asset details including credentials",
                        "Use decrypted credentials in automation service",
                        "Ensure proper credential type handling",
                        "Log credential usage for audit"
                    ],
                    "security_considerations": [
                        "Credentials are automatically decrypted when retrieved",
                        "Never log or expose credentials in plain text",
                        "Use appropriate credential type for target service",
                        "Implement credential rotation policies"
                    ]
                }
            ],
            "query_patterns": [
                {
                    "pattern": "Find all Windows machines",
                    "query": "GET /assets?os_type=windows",
                    "use_case": "Windows-specific automation tasks"
                },
                {
                    "pattern": "Find production database servers",
                    "query": "GET /assets?tags=database&environment=production",
                    "use_case": "Database maintenance and monitoring"
                },
                {
                    "pattern": "Find systems by hostname pattern",
                    "query": "GET /assets?search=web",
                    "use_case": "Target specific server groups"
                },
                {
                    "pattern": "Find SSH-enabled Linux systems",
                    "query": "GET /assets?os_type=linux&service_type=ssh",
                    "use_case": "Linux system administration"
                }
            ],
            "best_practices": [
                "Always use environment filters to avoid affecting wrong systems",
                "Test connectivity before running automation tasks",
                "Use tags for logical grouping of assets",
                "Implement proper credential rotation policies",
                "Monitor asset inventory for unauthorized changes",
                "Use descriptive names and documentation for assets"
            ]
        }
    
    async def discover_capabilities(self) -> APIDiscoveryResult:
        return APIDiscoveryResult(
            endpoints=[],
            capabilities=list(self.knowledge["capabilities"].keys()),
            authentication_methods=["jwt"],
            rate_limits={},
            documentation_urls=[],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        keyword_set = set(word.lower() for word in request_keywords)
        relevant_capabilities = []
        
        # Always include asset management for any asset-related request
        if any(word in keyword_set for word in ["asset", "system", "server", "machine", "target", "host"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["asset_management"])
        
        if any(word in keyword_set for word in ["credential", "password", "key", "auth"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["credential_management"])
        
        if any(word in keyword_set for word in ["service", "port", "discovery"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["service_discovery"])
        
        return {
            "service_name": "Asset Service",
            "service_info": self.knowledge["service_info"],
            "relevant_capabilities": relevant_capabilities,
            "integration_patterns": self.knowledge["integration_patterns"],
            "query_patterns": self.knowledge["query_patterns"],
            "best_practices": self.knowledge["best_practices"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False

class CommunicationServiceDomain(KnowledgeDomain):
    """Comprehensive Communication Service knowledge domain"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="communication_service",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.CRITICAL,
            keywords=["email", "notification", "alert", "message", "communication", "notify", "send"],
            dependencies=[],
            performance_metrics={}
        )
        super().__init__("communication_service", metadata)
        self.knowledge = self._initialize_communication_knowledge()
    
    def _initialize_communication_knowledge(self) -> Dict[str, Any]:
        return {
            "service_info": {
                "name": "OpsConductor Communication Service",
                "description": "Centralized notification and communication management",
                "base_url": "http://communication-service:3003",
                "supported_channels": ["email", "sms", "slack", "webhook", "teams"],
                "authentication": "JWT tokens via identity service"
            },
            "capabilities": {
                "notification_management": {
                    "description": "Send and manage notifications across multiple channels",
                    "keywords": ["notification", "alert", "message", "send", "notify"],
                    "endpoints": [
                        {
                            "path": "/notifications",
                            "method": "POST",
                            "description": "Send a notification immediately or schedule for later",
                            "parameters": {
                                "recipient": "Email address, phone number, or channel identifier",
                                "subject": "Notification subject (for email)",
                                "message": "Notification content/body",
                                "template_id": "Optional template ID for formatted messages",
                                "channel_id": "Optional specific channel configuration",
                                "scheduled_at": "Optional ISO datetime for scheduled delivery",
                                "metadata": "Additional data for template rendering"
                            },
                            "example_request": {
                                "recipient": "admin@company.com",
                                "subject": "System Alert: High CPU Usage",
                                "message": "Server web01 is experiencing high CPU usage (95%)",
                                "metadata": {
                                    "server_name": "web01",
                                    "cpu_usage": "95%",
                                    "timestamp": "2024-01-15T10:30:00Z"
                                }
                            },
                            "example_response": {
                                "success": True,
                                "data": {
                                    "notification_id": "notif_123456",
                                    "status": "queued",
                                    "scheduled_at": "2024-01-15T10:30:00Z"
                                }
                            }
                        },
                        {
                            "path": "/notifications",
                            "method": "GET",
                            "description": "List notifications with filtering",
                            "parameters": {
                                "skip": "Pagination offset",
                                "limit": "Number of results",
                                "status": "Filter by status (pending, sent, failed, cancelled)",
                                "recipient": "Filter by recipient",
                                "date_from": "Filter notifications from date",
                                "date_to": "Filter notifications to date"
                            }
                        },
                        {
                            "path": "/notifications/{notification_id}",
                            "method": "GET",
                            "description": "Get notification details and delivery status",
                            "example_response": {
                                "success": True,
                                "data": {
                                    "id": 1,
                                    "notification_id": "notif_123456",
                                    "recipient": "admin@company.com",
                                    "subject": "System Alert",
                                    "status": "sent",
                                    "sent_at": "2024-01-15T10:30:15Z",
                                    "attempts": 1,
                                    "error_message": None
                                }
                            }
                        }
                    ],
                    "notification_statuses": [
                        {"status": "pending", "description": "Queued for delivery"},
                        {"status": "sent", "description": "Successfully delivered"},
                        {"status": "failed", "description": "Delivery failed"},
                        {"status": "cancelled", "description": "Cancelled before delivery"}
                    ],
                    "use_cases": [
                        "System alert notifications",
                        "Automation task completion reports",
                        "Security incident alerts",
                        "Scheduled maintenance notifications",
                        "Performance monitoring alerts"
                    ]
                },
                "template_management": {
                    "description": "Create and manage reusable notification templates",
                    "keywords": ["template", "format", "reusable", "standardize"],
                    "endpoints": [
                        {
                            "path": "/templates",
                            "method": "POST",
                            "description": "Create a new notification template",
                            "parameters": {
                                "name": "Template name",
                                "template_type": "Type (email, sms, slack, etc.)",
                                "subject_template": "Subject template with variables",
                                "body_template": "Body template with variables",
                                "metadata": "Template configuration and variables"
                            },
                            "example_request": {
                                "name": "System Alert Template",
                                "template_type": "email",
                                "subject_template": "Alert: {{alert_type}} on {{server_name}}",
                                "body_template": "Server {{server_name}} is experiencing {{alert_type}}.\n\nDetails:\n- Metric: {{metric_name}}\n- Value: {{metric_value}}\n- Threshold: {{threshold}}\n- Time: {{timestamp}}",
                                "metadata": {
                                    "variables": ["alert_type", "server_name", "metric_name", "metric_value", "threshold", "timestamp"]
                                }
                            }
                        },
                        {
                            "path": "/templates",
                            "method": "GET",
                            "description": "List available templates",
                            "parameters": {
                                "template_type": "Filter by template type",
                                "is_active": "Filter by active status"
                            }
                        }
                    ],
                    "template_variables": [
                        "{{server_name}} - Server or asset name",
                        "{{timestamp}} - Current timestamp",
                        "{{alert_type}} - Type of alert or event",
                        "{{metric_value}} - Metric or measurement value",
                        "{{user_name}} - User who triggered the action",
                        "{{job_id}} - Automation job identifier",
                        "{{status}} - Status of operation or task"
                    ]
                },
                "channel_management": {
                    "description": "Configure and manage notification channels",
                    "keywords": ["channel", "configuration", "email", "sms", "slack"],
                    "supported_channels": [
                        {
                            "type": "email",
                            "description": "SMTP email delivery",
                            "configuration": {
                                "smtp_server": "SMTP server hostname",
                                "smtp_port": "SMTP port (25, 587, 465)",
                                "username": "SMTP authentication username",
                                "password": "SMTP authentication password",
                                "use_tls": "Enable TLS encryption",
                                "from_address": "Default sender address"
                            }
                        },
                        {
                            "type": "slack",
                            "description": "Slack webhook integration",
                            "configuration": {
                                "webhook_url": "Slack webhook URL",
                                "channel": "Default channel name",
                                "username": "Bot username",
                                "icon_emoji": "Bot icon emoji"
                            }
                        },
                        {
                            "type": "webhook",
                            "description": "Generic HTTP webhook",
                            "configuration": {
                                "url": "Webhook endpoint URL",
                                "method": "HTTP method (POST, PUT)",
                                "headers": "Custom HTTP headers",
                                "auth_type": "Authentication type"
                            }
                        }
                    ]
                }
            },
            "integration_patterns": [
                {
                    "name": "Automation Task Notifications",
                    "description": "Send notifications when automation tasks complete",
                    "steps": [
                        "Automation service completes a task",
                        "Call communication service with task results",
                        "Use appropriate template for formatting",
                        "Send to configured recipients"
                    ],
                    "example_workflow": "Job completes -> POST /notifications with job results -> Email sent to admin"
                },
                {
                    "name": "System Monitoring Alerts",
                    "description": "Send alerts when system thresholds are exceeded",
                    "steps": [
                        "Monitoring system detects threshold breach",
                        "Format alert using system alert template",
                        "Send immediate notification to operations team",
                        "Log notification for audit trail"
                    ]
                },
                {
                    "name": "Scheduled Maintenance Notifications",
                    "description": "Send scheduled notifications for maintenance windows",
                    "steps": [
                        "Schedule maintenance notification in advance",
                        "Use maintenance template with details",
                        "Send to stakeholder distribution list",
                        "Send follow-up when maintenance completes"
                    ]
                }
            ],
            "common_use_cases": [
                "Email automation task results to administrators",
                "Send SMS alerts for critical system failures",
                "Slack notifications for deployment completions",
                "Webhook integrations with external monitoring systems",
                "Scheduled maintenance window notifications",
                "Security incident alert distribution"
            ],
            "best_practices": [
                "Use templates for consistent message formatting",
                "Configure appropriate retry policies for failed deliveries",
                "Implement rate limiting to prevent notification spam",
                "Use meaningful subjects and clear message content",
                "Test notification channels before production use",
                "Monitor notification delivery success rates"
            ]
        }
    
    async def discover_capabilities(self) -> APIDiscoveryResult:
        return APIDiscoveryResult(
            endpoints=[],
            capabilities=list(self.knowledge["capabilities"].keys()),
            authentication_methods=["jwt"],
            rate_limits={},
            documentation_urls=[],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        keyword_set = set(word.lower() for word in request_keywords)
        relevant_capabilities = []
        
        if any(word in keyword_set for word in ["email", "notify", "alert", "send", "message"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["notification_management"])
        
        if any(word in keyword_set for word in ["template", "format"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["template_management"])
        
        if any(word in keyword_set for word in ["channel", "slack", "sms"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["channel_management"])
        
        return {
            "service_name": "Communication Service",
            "service_info": self.knowledge["service_info"],
            "relevant_capabilities": relevant_capabilities,
            "integration_patterns": self.knowledge["integration_patterns"],
            "common_use_cases": self.knowledge["common_use_cases"],
            "best_practices": self.knowledge["best_practices"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False

class NetworkAnalyzerServiceDomain(KnowledgeDomain):
    """Comprehensive Network Analyzer Service knowledge domain"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="network_analyzer_service",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.HIGH,
            keywords=["network", "packet", "analysis", "protocol", "traffic", "monitor", "capture"],
            dependencies=[],
            performance_metrics={}
        )
        super().__init__("network_analyzer_service", metadata)
        self.knowledge = self._initialize_network_knowledge()
    
    def _initialize_network_knowledge(self) -> Dict[str, Any]:
        return {
            "service_info": {
                "name": "OpsConductor Network Analyzer Service",
                "description": "Comprehensive packet analysis and network troubleshooting capabilities",
                "base_url": "http://network-analyzer-service:3006",
                "capabilities": ["packet_capture", "protocol_analysis", "traffic_monitoring", "ai_analysis"],
                "authentication": "JWT tokens via identity service"
            },
            "capabilities": {
                "packet_analysis": {
                    "description": "Deep packet inspection and analysis capabilities",
                    "keywords": ["packet", "capture", "analysis", "pcap", "wireshark"],
                    "endpoints": [
                        {
                            "path": "/analysis/start",
                            "method": "POST",
                            "description": "Start packet capture and analysis session",
                            "parameters": {
                                "interface": "Network interface to capture on",
                                "filter": "BPF filter expression",
                                "duration": "Capture duration in seconds",
                                "max_packets": "Maximum packets to capture",
                                "analysis_type": "Type of analysis (basic, deep, security)"
                            },
                            "example_request": {
                                "interface": "eth0",
                                "filter": "tcp port 80 or tcp port 443",
                                "duration": 300,
                                "analysis_type": "deep"
                            }
                        },
                        {
                            "path": "/analysis/{session_id}/results",
                            "method": "GET",
                            "description": "Get analysis results for a session",
                            "example_response": {
                                "session_id": "session_123",
                                "status": "completed",
                                "packets_captured": 1500,
                                "protocols_detected": ["HTTP", "HTTPS", "DNS", "TCP"],
                                "summary": {
                                    "total_traffic": "15.2 MB",
                                    "top_protocols": [
                                        {"protocol": "HTTP", "percentage": 45.2},
                                        {"protocol": "HTTPS", "percentage": 35.8}
                                    ]
                                }
                            }
                        }
                    ],
                    "supported_protocols": [
                        "HTTP/HTTPS", "DNS", "TCP/UDP", "ICMP", "ARP", "DHCP", 
                        "SSH", "FTP", "SMTP", "POP3", "IMAP", "SNMP"
                    ]
                },
                "network_monitoring": {
                    "description": "Real-time network traffic monitoring and alerting",
                    "keywords": ["monitor", "traffic", "bandwidth", "utilization", "real-time"],
                    "endpoints": [
                        {
                            "path": "/monitoring/start",
                            "method": "POST",
                            "description": "Start network monitoring session",
                            "parameters": {
                                "interfaces": "List of interfaces to monitor",
                                "metrics": "Metrics to collect (bandwidth, packets, errors)",
                                "interval": "Collection interval in seconds",
                                "thresholds": "Alert thresholds for metrics"
                            }
                        },
                        {
                            "path": "/monitoring/metrics",
                            "method": "GET",
                            "description": "Get current network metrics",
                            "example_response": {
                                "timestamp": "2024-01-15T10:30:00Z",
                                "interfaces": {
                                    "eth0": {
                                        "rx_bytes": 1048576000,
                                        "tx_bytes": 524288000,
                                        "rx_packets": 1000000,
                                        "tx_packets": 500000,
                                        "errors": 0,
                                        "utilization_percent": 25.5
                                    }
                                }
                            }
                        }
                    ],
                    "metrics_available": [
                        "Bandwidth utilization", "Packet rates", "Error rates",
                        "Protocol distribution", "Top talkers", "Connection counts"
                    ]
                },
                "protocol_analysis": {
                    "description": "Deep protocol-specific analysis and troubleshooting",
                    "keywords": ["protocol", "analysis", "troubleshoot", "decode"],
                    "supported_analyses": [
                        {
                            "protocol": "HTTP",
                            "capabilities": ["Request/response analysis", "Performance metrics", "Error detection"]
                        },
                        {
                            "protocol": "DNS",
                            "capabilities": ["Query analysis", "Response time tracking", "Resolution failures"]
                        },
                        {
                            "protocol": "TCP",
                            "capabilities": ["Connection analysis", "Retransmission detection", "Window scaling"]
                        }
                    ]
                },
                "ai_analysis": {
                    "description": "AI-powered network behavior analysis and anomaly detection",
                    "keywords": ["ai", "anomaly", "behavior", "machine learning", "detection"],
                    "endpoints": [
                        {
                            "path": "/ai/analyze",
                            "method": "POST",
                            "description": "Perform AI analysis on network data",
                            "parameters": {
                                "data_source": "Source of network data (live, pcap, logs)",
                                "analysis_type": "Type of AI analysis (anomaly, behavior, security)",
                                "time_window": "Time window for analysis"
                            }
                        }
                    ],
                    "ai_capabilities": [
                        "Anomaly detection in traffic patterns",
                        "Security threat identification",
                        "Performance bottleneck analysis",
                        "Behavioral baseline establishment"
                    ]
                }
            },
            "integration_patterns": [
                {
                    "name": "Network Troubleshooting Workflow",
                    "description": "Automated network issue diagnosis and resolution",
                    "steps": [
                        "Start packet capture on affected interface",
                        "Analyze traffic patterns and protocols",
                        "Identify anomalies or performance issues",
                        "Generate troubleshooting report",
                        "Send findings via communication service"
                    ]
                },
                {
                    "name": "Security Monitoring Integration",
                    "description": "Continuous security monitoring with automated alerts",
                    "steps": [
                        "Enable continuous packet monitoring",
                        "Apply AI analysis for threat detection",
                        "Trigger alerts for suspicious activity",
                        "Coordinate with asset service for affected systems",
                        "Automate response actions via automation service"
                    ]
                }
            ],
            "use_cases": [
                "Network performance troubleshooting",
                "Security incident investigation",
                "Bandwidth utilization monitoring",
                "Protocol-specific issue diagnosis",
                "Compliance monitoring and reporting",
                "Capacity planning and optimization"
            ],
            "best_practices": [
                "Use appropriate capture filters to reduce data volume",
                "Set reasonable capture durations to avoid storage issues",
                "Monitor capture performance impact on network",
                "Implement proper data retention policies",
                "Use AI analysis for large-scale pattern detection",
                "Coordinate with security team for threat analysis"
            ]
        }
    
    async def discover_capabilities(self) -> APIDiscoveryResult:
        return APIDiscoveryResult(
            endpoints=[],
            capabilities=list(self.knowledge["capabilities"].keys()),
            authentication_methods=["jwt"],
            rate_limits={},
            documentation_urls=[],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        keyword_set = set(word.lower() for word in request_keywords)
        relevant_capabilities = []
        
        if any(word in keyword_set for word in ["packet", "capture", "analysis", "pcap"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["packet_analysis"])
        
        if any(word in keyword_set for word in ["monitor", "traffic", "bandwidth"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["network_monitoring"])
        
        if any(word in keyword_set for word in ["protocol", "troubleshoot"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["protocol_analysis"])
        
        if any(word in keyword_set for word in ["ai", "anomaly", "behavior"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["ai_analysis"])
        
        return {
            "service_name": "Network Analyzer Service",
            "service_info": self.knowledge["service_info"],
            "relevant_capabilities": relevant_capabilities,
            "integration_patterns": self.knowledge["integration_patterns"],
            "use_cases": self.knowledge["use_cases"],
            "best_practices": self.knowledge["best_practices"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False

class CeleryServiceDomain(KnowledgeDomain):
    """Comprehensive Celery task queue knowledge domain"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="celery_service",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.CRITICAL,
            keywords=["celery", "task", "queue", "worker", "async", "background", "job", "redis", "broker"],
            dependencies=["redis"],
            performance_metrics={}
        )
        super().__init__("celery_service", metadata)
        self.knowledge = self._initialize_celery_knowledge()
    
    def _initialize_celery_knowledge(self) -> Dict[str, Any]:
        return {
            "service_info": {
                "name": "OpsConductor Celery Task Queue",
                "description": "Distributed task queue system for asynchronous job processing",
                "broker": "Redis (redis://redis:6379/0)",
                "result_backend": "Redis (redis://redis:6379/0)",
                "worker_processes": "Auto-scaling based on load",
                "monitoring": "Flower web interface and Celery events"
            },
            "capabilities": {
                "task_execution": {
                    "description": "Execute background tasks asynchronously",
                    "keywords": ["task", "execute", "async", "background", "job"],
                    "task_types": [
                        {
                            "name": "automation_task",
                            "description": "Execute automation workflows on target systems",
                            "queue": "automation",
                            "priority": "high",
                            "retry_policy": {
                                "max_retries": 3,
                                "retry_delay": 60,
                                "exponential_backoff": True
                            },
                            "example": {
                                "task_name": "execute_automation",
                                "parameters": {
                                    "workflow_id": "system_update",
                                    "target_assets": [1, 2, 3],
                                    "execution_options": {
                                        "parallel": True,
                                        "timeout": 300
                                    }
                                }
                            }
                        },
                        {
                            "name": "system_monitoring",
                            "description": "Collect system metrics and health data",
                            "queue": "monitoring",
                            "priority": "medium",
                            "schedule": "Every 5 minutes",
                            "example": {
                                "task_name": "collect_system_metrics",
                                "parameters": {
                                    "asset_ids": [1, 2, 3],
                                    "metrics": ["cpu", "memory", "disk", "network"]
                                }
                            }
                        },
                        {
                            "name": "notification_delivery",
                            "description": "Send notifications via various channels",
                            "queue": "notifications",
                            "priority": "high",
                            "retry_policy": {
                                "max_retries": 5,
                                "retry_delay": 30
                            },
                            "example": {
                                "task_name": "send_notification",
                                "parameters": {
                                    "channel": "email",
                                    "recipients": ["admin@company.com"],
                                    "subject": "System Alert",
                                    "message": "Critical system issue detected"
                                }
                            }
                        },
                        {
                            "name": "data_processing",
                            "description": "Process large datasets and generate reports",
                            "queue": "data_processing",
                            "priority": "low",
                            "timeout": 3600,
                            "example": {
                                "task_name": "generate_report",
                                "parameters": {
                                    "report_type": "system_health",
                                    "date_range": "last_30_days",
                                    "format": "pdf"
                                }
                            }
                        }
                    ],
                    "queues": [
                        {
                            "name": "automation",
                            "description": "High-priority automation tasks",
                            "routing_key": "automation",
                            "workers": 4,
                            "concurrency": 2
                        },
                        {
                            "name": "monitoring",
                            "description": "System monitoring and health checks",
                            "routing_key": "monitoring",
                            "workers": 2,
                            "concurrency": 4
                        },
                        {
                            "name": "notifications",
                            "description": "Notification delivery tasks",
                            "routing_key": "notifications",
                            "workers": 2,
                            "concurrency": 8
                        },
                        {
                            "name": "data_processing",
                            "description": "Long-running data processing tasks",
                            "routing_key": "data_processing",
                            "workers": 1,
                            "concurrency": 1
                        }
                    ]
                },
                "task_monitoring": {
                    "description": "Monitor task execution status and performance",
                    "keywords": ["monitor", "status", "progress", "performance", "metrics"],
                    "monitoring_endpoints": [
                        {
                            "path": "/celery/tasks",
                            "method": "GET",
                            "description": "List all tasks with status filtering",
                            "parameters": {
                                "status": "Filter by task status (pending, started, success, failure, retry, revoked)",
                                "queue": "Filter by queue name",
                                "worker": "Filter by worker name",
                                "limit": "Number of results (default: 100)",
                                "offset": "Pagination offset"
                            },
                            "example_response": {
                                "tasks": [
                                    {
                                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                                        "name": "execute_automation",
                                        "status": "SUCCESS",
                                        "queue": "automation",
                                        "worker": "worker-1@hostname",
                                        "started": "2024-01-15T10:30:00Z",
                                        "completed": "2024-01-15T10:32:15Z",
                                        "runtime": 135.5,
                                        "result": {"status": "completed", "affected_systems": 3}
                                    }
                                ]
                            }
                        },
                        {
                            "path": "/celery/tasks/{task_id}",
                            "method": "GET",
                            "description": "Get detailed task information and results",
                            "parameters": {
                                "task_id": "Unique task identifier"
                            }
                        },
                        {
                            "path": "/celery/workers",
                            "method": "GET",
                            "description": "List active workers and their status",
                            "example_response": {
                                "workers": [
                                    {
                                        "name": "worker-1@hostname",
                                        "status": "online",
                                        "active_tasks": 2,
                                        "processed_tasks": 1547,
                                        "load_average": [0.5, 0.3, 0.2],
                                        "queues": ["automation", "monitoring"]
                                    }
                                ]
                            }
                        },
                        {
                            "path": "/celery/queues",
                            "method": "GET",
                            "description": "Get queue statistics and pending task counts",
                            "example_response": {
                                "queues": [
                                    {
                                        "name": "automation",
                                        "pending_tasks": 5,
                                        "active_tasks": 2,
                                        "workers": 4,
                                        "messages_per_second": 2.3
                                    }
                                ]
                            }
                        }
                    ],
                    "metrics": [
                        "Task execution time",
                        "Task success/failure rates",
                        "Queue depth and processing rates",
                        "Worker utilization and performance",
                        "Memory and CPU usage per worker"
                    ]
                },
                "task_management": {
                    "description": "Manage task lifecycle and execution control",
                    "keywords": ["cancel", "retry", "revoke", "restart", "control"],
                    "operations": [
                        {
                            "operation": "cancel_task",
                            "endpoint": "POST /celery/tasks/{task_id}/cancel",
                            "description": "Cancel a pending or running task",
                            "parameters": {
                                "task_id": "Task to cancel",
                                "terminate": "Force terminate if running (default: false)"
                            }
                        },
                        {
                            "operation": "retry_task",
                            "endpoint": "POST /celery/tasks/{task_id}/retry",
                            "description": "Retry a failed task with same parameters",
                            "parameters": {
                                "task_id": "Task to retry",
                                "countdown": "Delay before retry in seconds"
                            }
                        },
                        {
                            "operation": "purge_queue",
                            "endpoint": "POST /celery/queues/{queue_name}/purge",
                            "description": "Remove all pending tasks from a queue",
                            "parameters": {
                                "queue_name": "Queue to purge"
                            }
                        },
                        {
                            "operation": "scale_workers",
                            "endpoint": "POST /celery/workers/scale",
                            "description": "Scale worker processes up or down",
                            "parameters": {
                                "queue": "Target queue",
                                "workers": "Number of worker processes",
                                "concurrency": "Tasks per worker"
                            }
                        }
                    ]
                }
            },
            "integration_patterns": [
                {
                    "name": "Async Automation Execution",
                    "description": "Execute automation workflows asynchronously",
                    "steps": [
                        "Submit automation task to Celery queue",
                        "Get task ID for tracking",
                        "Monitor task progress via status endpoints",
                        "Retrieve results when completed",
                        "Handle failures with retry logic"
                    ],
                    "example_workflow": {
                        "step1": "POST /celery/tasks/submit",
                        "step2": "GET /celery/tasks/{task_id}/status",
                        "step3": "GET /celery/tasks/{task_id}/result"
                    }
                },
                {
                    "name": "Bulk System Operations",
                    "description": "Execute operations across multiple systems efficiently",
                    "steps": [
                        "Query asset service for target systems",
                        "Split targets into optimal batch sizes",
                        "Submit parallel tasks to automation queue",
                        "Monitor all task progress",
                        "Aggregate results and handle failures"
                    ],
                    "best_practices": [
                        "Use appropriate batch sizes (10-50 systems per task)",
                        "Implement proper error handling and retries",
                        "Monitor queue depth to avoid overload",
                        "Use task groups for related operations"
                    ]
                }
            ],
            "error_handling": [
                {
                    "error_type": "Task Timeout",
                    "description": "Task exceeded maximum execution time",
                    "resolution": "Increase timeout or optimize task logic",
                    "monitoring": "Track task execution times"
                },
                {
                    "error_type": "Worker Failure",
                    "description": "Worker process crashed or became unresponsive",
                    "resolution": "Restart worker, check system resources",
                    "monitoring": "Monitor worker health and resource usage"
                },
                {
                    "error_type": "Queue Overflow",
                    "description": "Too many pending tasks in queue",
                    "resolution": "Scale workers or optimize task processing",
                    "monitoring": "Set alerts on queue depth"
                },
                {
                    "error_type": "Broker Connection",
                    "description": "Cannot connect to Redis broker",
                    "resolution": "Check Redis service status and connectivity",
                    "monitoring": "Monitor broker availability"
                }
            ],
            "performance_optimization": [
                "Use appropriate task routing to specialized queues",
                "Implement task result expiration to manage memory",
                "Monitor and tune worker concurrency settings",
                "Use task compression for large payloads",
                "Implement circuit breakers for external dependencies",
                "Use task priorities for critical operations",
                "Monitor and optimize serialization overhead"
            ]
        }
    
    def get_api_discovery(self) -> APIDiscoveryResult:
        return APIDiscoveryResult(
            service_name="Celery Task Queue",
            base_url="http://celery-monitor:5555",
            endpoints=[
                "/celery/tasks",
                "/celery/workers", 
                "/celery/queues",
                "/celery/tasks/{task_id}",
                "/celery/tasks/{task_id}/cancel",
                "/celery/tasks/{task_id}/retry"
            ],
            capabilities=list(self.knowledge["capabilities"].keys()),
            authentication_methods=["jwt"],
            rate_limits={},
            documentation_urls=["http://celery-monitor:5555/flower"],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        keyword_set = set(word.lower() for word in request_keywords)
        relevant_capabilities = []
        
        if any(word in keyword_set for word in ["task", "execute", "async", "background", "job"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["task_execution"])
        
        if any(word in keyword_set for word in ["monitor", "status", "progress", "performance"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["task_monitoring"])
        
        if any(word in keyword_set for word in ["cancel", "retry", "control", "manage"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["task_management"])
        
        return {
            "service_name": "Celery Task Queue",
            "service_info": self.knowledge["service_info"],
            "relevant_capabilities": relevant_capabilities,
            "integration_patterns": self.knowledge["integration_patterns"],
            "error_handling": self.knowledge["error_handling"],
            "performance_optimization": self.knowledge["performance_optimization"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False
    
    def discover_capabilities(self) -> List[str]:
        """Discover available capabilities for Celery service"""
        return [
            "task_execution",
            "task_monitoring", 
            "task_management",
            "queue_management",
            "worker_scaling",
            "async_automation",
            "bulk_operations"
        ]


class CeleryBeatDomain(KnowledgeDomain):
    """Comprehensive Celery Beat scheduler knowledge domain"""
    
    def __init__(self):
        metadata = KnowledgeMetadata(
            domain_id="celery_beat",
            domain_type=KnowledgeDomainType.CORE_SERVICE,
            version="1.0.0",
            last_updated=datetime.now(),
            size_bytes=0,
            priority=ContextPriority.CRITICAL,
            keywords=["celery", "beat", "scheduler", "cron", "periodic", "schedule", "interval", "recurring"],
            dependencies=["celery_service", "redis"],
            performance_metrics={}
        )
        super().__init__("celery_beat", metadata)
        self.knowledge = self._initialize_beat_knowledge()
    
    def _initialize_beat_knowledge(self) -> Dict[str, Any]:
        return {
            "service_info": {
                "name": "OpsConductor Celery Beat Scheduler",
                "description": "Periodic task scheduler for automated recurring operations",
                "scheduler_backend": "Redis (redis://redis:6379/1)",
                "timezone": "UTC",
                "precision": "Seconds",
                "persistence": "Redis-backed schedule persistence"
            },
            "capabilities": {
                "periodic_scheduling": {
                    "description": "Schedule tasks to run at regular intervals",
                    "keywords": ["schedule", "periodic", "interval", "recurring", "cron"],
                    "schedule_types": [
                        {
                            "type": "interval",
                            "description": "Run task every N seconds/minutes/hours/days",
                            "examples": [
                                {
                                    "name": "system_health_check",
                                    "task": "monitor_system_health",
                                    "schedule": "every 5 minutes",
                                    "config": {
                                        "task": "tasks.monitor_system_health",
                                        "schedule": 300.0,
                                        "args": [],
                                        "kwargs": {"check_type": "basic"}
                                    }
                                },
                                {
                                    "name": "backup_databases",
                                    "task": "backup_all_databases",
                                    "schedule": "every 6 hours",
                                    "config": {
                                        "task": "tasks.backup_databases",
                                        "schedule": 21600.0,
                                        "options": {"queue": "data_processing"}
                                    }
                                }
                            ]
                        },
                        {
                            "type": "crontab",
                            "description": "Run task based on cron-like schedule",
                            "examples": [
                                {
                                    "name": "daily_report",
                                    "task": "generate_daily_report",
                                    "schedule": "daily at 6:00 AM",
                                    "config": {
                                        "task": "tasks.generate_daily_report",
                                        "schedule": "crontab(hour=6, minute=0)",
                                        "kwargs": {"report_type": "summary"}
                                    }
                                },
                                {
                                    "name": "weekly_maintenance",
                                    "task": "system_maintenance",
                                    "schedule": "every Sunday at 2:00 AM",
                                    "config": {
                                        "task": "tasks.system_maintenance",
                                        "schedule": "crontab(hour=2, minute=0, day_of_week=0)",
                                        "options": {"queue": "automation"}
                                    }
                                },
                                {
                                    "name": "monthly_cleanup",
                                    "task": "cleanup_old_data",
                                    "schedule": "first day of month at midnight",
                                    "config": {
                                        "task": "tasks.cleanup_old_data",
                                        "schedule": "crontab(hour=0, minute=0, day_of_month=1)"
                                    }
                                }
                            ]
                        },
                        {
                            "type": "solar",
                            "description": "Schedule based on solar events (sunrise/sunset)",
                            "examples": [
                                {
                                    "name": "evening_backup",
                                    "task": "evening_system_backup",
                                    "schedule": "30 minutes after sunset",
                                    "config": {
                                        "task": "tasks.evening_backup",
                                        "schedule": "solar('sunset', 30, 60)"
                                    }
                                }
                            ]
                        }
                    ],
                    "management_endpoints": [
                        {
                            "path": "/celery/beat/schedules",
                            "method": "GET",
                            "description": "List all scheduled tasks",
                            "example_response": {
                                "schedules": [
                                    {
                                        "name": "system_health_check",
                                        "task": "tasks.monitor_system_health",
                                        "schedule_type": "interval",
                                        "interval": 300,
                                        "enabled": True,
                                        "last_run": "2024-01-15T10:30:00Z",
                                        "next_run": "2024-01-15T10:35:00Z",
                                        "total_runs": 1547
                                    }
                                ]
                            }
                        },
                        {
                            "path": "/celery/beat/schedules",
                            "method": "POST",
                            "description": "Create new scheduled task",
                            "parameters": {
                                "name": "Unique schedule name",
                                "task": "Task function to execute",
                                "schedule_type": "interval, crontab, or solar",
                                "schedule_config": "Schedule configuration object",
                                "args": "Task arguments array",
                                "kwargs": "Task keyword arguments",
                                "options": "Task execution options"
                            },
                            "example_request": {
                                "name": "disk_space_check",
                                "task": "tasks.check_disk_space",
                                "schedule_type": "interval",
                                "schedule_config": {"seconds": 1800},
                                "kwargs": {"threshold": 85},
                                "options": {"queue": "monitoring"}
                            }
                        },
                        {
                            "path": "/celery/beat/schedules/{schedule_name}",
                            "method": "PUT",
                            "description": "Update existing scheduled task",
                            "parameters": {
                                "schedule_name": "Name of schedule to update"
                            }
                        },
                        {
                            "path": "/celery/beat/schedules/{schedule_name}",
                            "method": "DELETE",
                            "description": "Remove scheduled task",
                            "parameters": {
                                "schedule_name": "Name of schedule to remove"
                            }
                        },
                        {
                            "path": "/celery/beat/schedules/{schedule_name}/enable",
                            "method": "POST",
                            "description": "Enable a disabled scheduled task"
                        },
                        {
                            "path": "/celery/beat/schedules/{schedule_name}/disable",
                            "method": "POST",
                            "description": "Disable a scheduled task temporarily"
                        }
                    ]
                },
                "schedule_monitoring": {
                    "description": "Monitor scheduled task execution and performance",
                    "keywords": ["monitor", "tracking", "performance", "history", "metrics"],
                    "monitoring_features": [
                        {
                            "feature": "Execution History",
                            "description": "Track when scheduled tasks ran and their results",
                            "endpoint": "/celery/beat/history/{schedule_name}",
                            "data_points": [
                                "Execution timestamp",
                                "Task duration",
                                "Success/failure status",
                                "Error messages if failed",
                                "Task result data"
                            ]
                        },
                        {
                            "feature": "Schedule Drift Detection",
                            "description": "Detect when tasks are running behind schedule",
                            "alerts": [
                                "Task missed scheduled execution",
                                "Task taking longer than expected",
                                "Schedule queue backup"
                            ]
                        },
                        {
                            "feature": "Performance Metrics",
                            "description": "Track scheduler and task performance",
                            "metrics": [
                                "Average task execution time",
                                "Schedule accuracy (on-time execution rate)",
                                "Task success/failure rates",
                                "Queue depth for scheduled tasks",
                                "Scheduler loop performance"
                            ]
                        }
                    ]
                },
                "dynamic_scheduling": {
                    "description": "Dynamically create and modify schedules at runtime",
                    "keywords": ["dynamic", "runtime", "modify", "create", "update"],
                    "use_cases": [
                        {
                            "use_case": "Conditional Monitoring",
                            "description": "Create monitoring schedules based on system state",
                            "example": "Increase monitoring frequency during high load periods"
                        },
                        {
                            "use_case": "Maintenance Windows",
                            "description": "Schedule maintenance tasks during approved windows",
                            "example": "Create one-time maintenance schedule for specific date/time"
                        },
                        {
                            "use_case": "Adaptive Scheduling",
                            "description": "Adjust schedule frequency based on results",
                            "example": "Increase backup frequency if failures detected"
                        },
                        {
                            "use_case": "Event-Driven Scheduling",
                            "description": "Create schedules in response to events",
                            "example": "Schedule cleanup tasks after deployment"
                        }
                    ],
                    "api_patterns": [
                        {
                            "pattern": "Create temporary schedule",
                            "steps": [
                                "POST /celery/beat/schedules with end_date",
                                "Monitor execution",
                                "Automatic cleanup after end_date"
                            ]
                        },
                        {
                            "pattern": "Modify schedule frequency",
                            "steps": [
                                "GET current schedule configuration",
                                "PUT updated schedule with new interval",
                                "Verify schedule updated successfully"
                            ]
                        }
                    ]
                }
            },
            "common_schedules": [
                {
                    "category": "System Monitoring",
                    "schedules": [
                        {"name": "health_check", "interval": "5 minutes", "description": "Basic system health monitoring"},
                        {"name": "disk_space_check", "interval": "30 minutes", "description": "Monitor disk space usage"},
                        {"name": "service_status_check", "interval": "2 minutes", "description": "Check critical service status"},
                        {"name": "performance_metrics", "interval": "1 minute", "description": "Collect system performance data"}
                    ]
                },
                {
                    "category": "Data Management",
                    "schedules": [
                        {"name": "database_backup", "cron": "0 2 * * *", "description": "Daily database backup at 2 AM"},
                        {"name": "log_rotation", "cron": "0 0 * * 0", "description": "Weekly log rotation on Sunday"},
                        {"name": "cleanup_temp_files", "cron": "0 3 * * *", "description": "Daily cleanup of temporary files"},
                        {"name": "archive_old_data", "cron": "0 1 1 * *", "description": "Monthly data archival"}
                    ]
                },
                {
                    "category": "Security",
                    "schedules": [
                        {"name": "security_scan", "cron": "0 4 * * 1", "description": "Weekly security scan on Monday"},
                        {"name": "certificate_check", "interval": "24 hours", "description": "Check SSL certificate expiration"},
                        {"name": "vulnerability_scan", "cron": "0 5 * * 3", "description": "Weekly vulnerability assessment"},
                        {"name": "access_log_analysis", "interval": "6 hours", "description": "Analyze access logs for anomalies"}
                    ]
                },
                {
                    "category": "Reporting",
                    "schedules": [
                        {"name": "daily_summary", "cron": "0 6 * * *", "description": "Daily system summary report"},
                        {"name": "weekly_report", "cron": "0 7 * * 1", "description": "Weekly comprehensive report"},
                        {"name": "monthly_metrics", "cron": "0 8 1 * *", "description": "Monthly performance metrics"},
                        {"name": "capacity_planning", "cron": "0 9 1 * *", "description": "Monthly capacity planning report"}
                    ]
                }
            ],
            "integration_patterns": [
                {
                    "name": "Scheduled System Maintenance",
                    "description": "Coordinate scheduled maintenance across multiple systems",
                    "workflow": [
                        "Create maintenance window schedule",
                        "Schedule pre-maintenance health checks",
                        "Schedule maintenance tasks with dependencies",
                        "Schedule post-maintenance validation",
                        "Schedule notification of completion"
                    ]
                },
                {
                    "name": "Adaptive Monitoring",
                    "description": "Adjust monitoring frequency based on system state",
                    "workflow": [
                        "Monitor system metrics via scheduled tasks",
                        "Analyze trends and detect anomalies",
                        "Dynamically adjust monitoring schedules",
                        "Scale back to normal when stable"
                    ]
                }
            ],
            "best_practices": [
                "Use meaningful schedule names for easy identification",
                "Set appropriate timeouts for long-running scheduled tasks",
                "Implement idempotent tasks to handle duplicate executions",
                "Monitor schedule execution and set up alerts for failures",
                "Use task routing to appropriate queues for scheduled tasks",
                "Implement proper error handling and retry logic",
                "Consider timezone implications for cron schedules",
                "Use schedule persistence to survive service restarts",
                "Implement schedule validation before deployment",
                "Monitor scheduler performance and queue depth"
            ],
            "troubleshooting": [
                {
                    "issue": "Scheduled task not running",
                    "causes": ["Schedule disabled", "Beat scheduler not running", "Invalid schedule configuration"],
                    "resolution": ["Check schedule status", "Verify beat service", "Validate schedule syntax"]
                },
                {
                    "issue": "Tasks running behind schedule",
                    "causes": ["High task execution time", "Insufficient workers", "Queue backup"],
                    "resolution": ["Optimize task performance", "Scale workers", "Monitor queue depth"]
                },
                {
                    "issue": "Duplicate task executions",
                    "causes": ["Multiple beat instances", "Clock synchronization issues", "Non-idempotent tasks"],
                    "resolution": ["Ensure single beat instance", "Sync system clocks", "Implement task idempotency"]
                }
            ]
        }
    
    def get_api_discovery(self) -> APIDiscoveryResult:
        return APIDiscoveryResult(
            service_name="Celery Beat Scheduler",
            base_url="http://celery-monitor:5555",
            endpoints=[
                "/celery/beat/schedules",
                "/celery/beat/schedules/{schedule_name}",
                "/celery/beat/schedules/{schedule_name}/enable",
                "/celery/beat/schedules/{schedule_name}/disable",
                "/celery/beat/history/{schedule_name}"
            ],
            capabilities=list(self.knowledge["capabilities"].keys()),
            authentication_methods=["jwt"],
            rate_limits={},
            documentation_urls=["http://celery-monitor:5555/flower"],
            examples=[]
        )
    
    def get_context_for_request(self, request_keywords: List[str]) -> Dict[str, Any]:
        keyword_set = set(word.lower() for word in request_keywords)
        relevant_capabilities = []
        
        if any(word in keyword_set for word in ["schedule", "periodic", "cron", "interval", "recurring"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["periodic_scheduling"])
        
        if any(word in keyword_set for word in ["monitor", "tracking", "history", "performance"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["schedule_monitoring"])
        
        if any(word in keyword_set for word in ["dynamic", "create", "modify", "update"]):
            relevant_capabilities.append(self.knowledge["capabilities"]["dynamic_scheduling"])
        
        return {
            "service_name": "Celery Beat Scheduler",
            "service_info": self.knowledge["service_info"],
            "relevant_capabilities": relevant_capabilities,
            "common_schedules": self.knowledge["common_schedules"],
            "integration_patterns": self.knowledge["integration_patterns"],
            "best_practices": self.knowledge["best_practices"],
            "troubleshooting": self.knowledge["troubleshooting"]
        }
    
    def update_knowledge(self, new_knowledge: Dict[str, Any]) -> bool:
        try:
            if "capabilities" in new_knowledge:
                self.knowledge["capabilities"].update(new_knowledge["capabilities"])
            self.metadata.last_updated = datetime.now()
            return True
        except Exception:
            return False
    
    def discover_capabilities(self) -> List[str]:
        """Discover available capabilities for Celery Beat scheduler"""
        return [
            "periodic_scheduling",
            "schedule_monitoring",
            "dynamic_scheduling",
            "cron_scheduling",
            "interval_scheduling",
            "schedule_management",
            "task_automation"
        ]


def register_core_domains(catalog):
    """Register all core knowledge domains with the catalog"""
    catalog.register_domain(AssetServiceDomain())
    catalog.register_domain(CommunicationServiceDomain())
    catalog.register_domain(NetworkAnalyzerServiceDomain())
    catalog.register_domain(CeleryServiceDomain())
    catalog.register_domain(CeleryBeatDomain())
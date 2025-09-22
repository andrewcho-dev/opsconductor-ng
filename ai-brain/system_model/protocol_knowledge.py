"""
OpsConductor System Model - Protocol Knowledge Module

This module provides deep knowledge about automation protocols, their capabilities,
best practices, common patterns, and troubleshooting procedures.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProtocolCategory(Enum):
    """Categories of automation protocols"""
    REMOTE_EXECUTION = "remote_execution"
    MONITORING = "monitoring"
    CONFIGURATION = "configuration"
    DATABASE = "database"
    WEB_API = "web_api"
    MESSAGING = "messaging"
    NETWORK_ANALYSIS = "network_analysis"

class SecurityLevel(Enum):
    """Security levels for protocols"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ProtocolCapability:
    """Specific capability of a protocol"""
    name: str
    description: str
    parameters: Dict[str, Any]
    examples: List[str]
    limitations: List[str]

@dataclass
class ProtocolBestPractice:
    """Best practice for protocol usage"""
    title: str
    description: str
    category: str
    importance: str  # "critical", "important", "recommended"
    examples: List[str]

@dataclass
class ProtocolTroubleshooting:
    """Troubleshooting information for common protocol issues"""
    issue: str
    symptoms: List[str]
    causes: List[str]
    solutions: List[str]
    prevention: List[str]

@dataclass
class ProtocolDefinition:
    """Complete protocol definition with all knowledge"""
    name: str
    category: ProtocolCategory
    description: str
    default_port: Optional[int]
    security_level: SecurityLevel
    capabilities: List[ProtocolCapability]
    best_practices: List[ProtocolBestPractice]
    troubleshooting: List[ProtocolTroubleshooting]
    common_use_cases: List[str]
    prerequisites: List[str]
    supported_platforms: List[str]

class ProtocolKnowledgeManager:
    """Manages comprehensive knowledge about automation protocols"""
    
    def __init__(self):
        self.protocols = self._initialize_protocol_knowledge()
        logger.info(f"Initialized protocol knowledge for {len(self.protocols)} protocols")
    
    def _initialize_protocol_knowledge(self) -> Dict[str, ProtocolDefinition]:
        """Initialize comprehensive protocol knowledge base"""
        protocols = {}
        
        # SSH Protocol
        protocols["ssh"] = ProtocolDefinition(
            name="SSH",
            category=ProtocolCategory.REMOTE_EXECUTION,
            description="Secure Shell protocol for secure remote command execution and file transfer",
            default_port=22,
            security_level=SecurityLevel.HIGH,
            capabilities=[
                ProtocolCapability(
                    name="remote_command_execution",
                    description="Execute commands on remote systems securely",
                    parameters={
                        "host": "str",
                        "port": "int (default: 22)",
                        "username": "str",
                        "password": "str (optional)",
                        "private_key": "str (optional)",
                        "timeout": "int (default: 30)"
                    },
                    examples=[
                        "ssh user@server 'systemctl status nginx'",
                        "ssh -i ~/.ssh/key user@server 'df -h'",
                        "ssh user@server 'sudo service apache2 restart'"
                    ],
                    limitations=[
                        "Requires SSH daemon running on target",
                        "Firewall must allow SSH traffic",
                        "User must have appropriate permissions"
                    ]
                ),
                ProtocolCapability(
                    name="file_transfer",
                    description="Secure file transfer using SCP/SFTP",
                    parameters={
                        "source": "str",
                        "destination": "str",
                        "recursive": "bool (default: false)",
                        "preserve_permissions": "bool (default: true)"
                    },
                    examples=[
                        "scp file.txt user@server:/tmp/",
                        "scp -r /local/dir user@server:/remote/dir",
                        "sftp user@server"
                    ],
                    limitations=[
                        "Large files may timeout",
                        "Network interruptions can corrupt transfers",
                        "Disk space must be available on target"
                    ]
                ),
                ProtocolCapability(
                    name="port_forwarding",
                    description="Create secure tunnels for accessing remote services",
                    parameters={
                        "local_port": "int",
                        "remote_host": "str",
                        "remote_port": "int",
                        "bind_address": "str (default: localhost)"
                    },
                    examples=[
                        "ssh -L 8080:localhost:80 user@server",
                        "ssh -R 9090:localhost:3000 user@server",
                        "ssh -D 1080 user@server"
                    ],
                    limitations=[
                        "Requires persistent connection",
                        "May impact network performance",
                        "Security implications for exposed ports"
                    ]
                )
            ],
            best_practices=[
                ProtocolBestPractice(
                    title="Use Key-Based Authentication",
                    description="Always prefer SSH keys over passwords for better security",
                    category="security",
                    importance="critical",
                    examples=[
                        "Generate key: ssh-keygen -t rsa -b 4096",
                        "Copy key: ssh-copy-id user@server",
                        "Use agent: ssh-add ~/.ssh/id_rsa"
                    ]
                ),
                ProtocolBestPractice(
                    title="Configure SSH Hardening",
                    description="Secure SSH daemon configuration",
                    category="security",
                    importance="critical",
                    examples=[
                        "Disable root login: PermitRootLogin no",
                        "Change default port: Port 2222",
                        "Limit users: AllowUsers specific_user"
                    ]
                ),
                ProtocolBestPractice(
                    title="Use Connection Multiplexing",
                    description="Reuse SSH connections for better performance",
                    category="performance",
                    importance="recommended",
                    examples=[
                        "ControlMaster auto",
                        "ControlPath ~/.ssh/master-%r@%h:%p",
                        "ControlPersist 10m"
                    ]
                )
            ],
            troubleshooting=[
                ProtocolTroubleshooting(
                    issue="Connection Refused",
                    symptoms=["ssh: connect to host X port 22: Connection refused"],
                    causes=[
                        "SSH daemon not running",
                        "Firewall blocking port 22",
                        "Wrong port number",
                        "Network connectivity issues"
                    ],
                    solutions=[
                        "Check SSH service: systemctl status sshd",
                        "Start SSH service: systemctl start sshd",
                        "Check firewall: ufw status",
                        "Test connectivity: telnet host 22"
                    ],
                    prevention=[
                        "Monitor SSH service health",
                        "Configure firewall rules properly",
                        "Use connection health checks"
                    ]
                ),
                ProtocolTroubleshooting(
                    issue="Permission Denied",
                    symptoms=["Permission denied (publickey,password)"],
                    causes=[
                        "Wrong username or password",
                        "SSH key not authorized",
                        "User account locked",
                        "SSH configuration issues"
                    ],
                    solutions=[
                        "Verify credentials",
                        "Check authorized_keys file",
                        "Verify user account status",
                        "Check SSH daemon logs"
                    ],
                    prevention=[
                        "Test credentials before automation",
                        "Monitor account status",
                        "Regular key rotation"
                    ]
                )
            ],
            common_use_cases=[
                "Remote server administration",
                "Application deployment",
                "Log file analysis",
                "System monitoring",
                "Configuration management",
                "Backup operations"
            ],
            prerequisites=[
                "SSH daemon installed and running on target",
                "Network connectivity to target",
                "Valid user credentials",
                "Appropriate user permissions"
            ],
            supported_platforms=["Linux", "Unix", "macOS", "Windows (with OpenSSH)"]
        )
        
        # PowerShell/WinRM Protocol
        protocols["winrm"] = ProtocolDefinition(
            name="WinRM",
            category=ProtocolCategory.REMOTE_EXECUTION,
            description="Windows Remote Management protocol for Windows system automation",
            default_port=5985,  # HTTP, 5986 for HTTPS
            security_level=SecurityLevel.MEDIUM,
            capabilities=[
                ProtocolCapability(
                    name="powershell_execution",
                    description="Execute PowerShell commands and scripts remotely",
                    parameters={
                        "host": "str",
                        "port": "int (5985 HTTP, 5986 HTTPS)",
                        "username": "str",
                        "password": "str",
                        "domain": "str (optional)",
                        "transport": "str (http/https)"
                    },
                    examples=[
                        "Get-Service | Where-Object {$_.Status -eq 'Running'}",
                        "Restart-Service -Name 'IIS'",
                        "Get-EventLog -LogName System -Newest 10"
                    ],
                    limitations=[
                        "Windows-specific protocol",
                        "Requires WinRM service enabled",
                        "May require domain authentication"
                    ]
                ),
                ProtocolCapability(
                    name="windows_management",
                    description="Comprehensive Windows system management",
                    parameters={
                        "cmdlet": "str",
                        "parameters": "dict",
                        "execution_policy": "str (optional)"
                    },
                    examples=[
                        "Get-Process | Sort-Object CPU -Descending",
                        "Install-WindowsFeature -Name IIS-WebServer",
                        "Set-ExecutionPolicy RemoteSigned"
                    ],
                    limitations=[
                        "Execution policy restrictions",
                        "Administrator privileges may be required",
                        "Some cmdlets require specific modules"
                    ]
                )
            ],
            best_practices=[
                ProtocolBestPractice(
                    title="Enable WinRM Securely",
                    description="Configure WinRM with proper security settings",
                    category="security",
                    importance="critical",
                    examples=[
                        "winrm quickconfig -transport:https",
                        "winrm set winrm/config/service/auth @{Basic=\"false\"}",
                        "winrm set winrm/config/service @{AllowUnencrypted=\"false\"}"
                    ]
                ),
                ProtocolBestPractice(
                    title="Use HTTPS Transport",
                    description="Always use HTTPS for WinRM connections",
                    category="security",
                    importance="critical",
                    examples=[
                        "Configure SSL certificate",
                        "Use port 5986 for HTTPS",
                        "Disable HTTP transport in production"
                    ]
                )
            ],
            troubleshooting=[
                ProtocolTroubleshooting(
                    issue="WinRM Service Not Available",
                    symptoms=["The WinRM client cannot process the request"],
                    causes=[
                        "WinRM service not running",
                        "WinRM not configured",
                        "Firewall blocking WinRM ports"
                    ],
                    solutions=[
                        "Start WinRM: Start-Service WinRM",
                        "Configure WinRM: winrm quickconfig",
                        "Check firewall rules"
                    ],
                    prevention=[
                        "Monitor WinRM service",
                        "Automate WinRM configuration",
                        "Regular connectivity tests"
                    ]
                )
            ],
            common_use_cases=[
                "Windows server management",
                "IIS administration",
                "Windows service management",
                "Registry modifications",
                "Windows feature installation",
                "Event log analysis"
            ],
            prerequisites=[
                "WinRM service enabled",
                "Appropriate firewall rules",
                "Valid Windows credentials",
                "PowerShell execution policy configured"
            ],
            supported_platforms=["Windows Server", "Windows Desktop"]
        )
        
        # SNMP Protocol
        protocols["snmp"] = ProtocolDefinition(
            name="SNMP",
            category=ProtocolCategory.MONITORING,
            description="Simple Network Management Protocol for network device monitoring and management",
            default_port=161,
            security_level=SecurityLevel.LOW,
            capabilities=[
                ProtocolCapability(
                    name="device_monitoring",
                    description="Monitor network devices and collect metrics",
                    parameters={
                        "host": "str",
                        "port": "int (default: 161)",
                        "community": "str (default: public)",
                        "version": "str (1, 2c, 3)",
                        "oid": "str"
                    },
                    examples=[
                        "snmpget -v2c -c public host 1.3.6.1.2.1.1.1.0",
                        "snmpwalk -v2c -c public host 1.3.6.1.2.1.2.2.1.2",
                        "snmpset -v2c -c private host oid type value"
                    ],
                    limitations=[
                        "Limited security in v1/v2c",
                        "UDP protocol - no guaranteed delivery",
                        "Device must support SNMP"
                    ]
                ),
                ProtocolCapability(
                    name="trap_handling",
                    description="Receive and process SNMP traps/notifications",
                    parameters={
                        "trap_port": "int (default: 162)",
                        "community": "str",
                        "trap_oid": "str"
                    },
                    examples=[
                        "Configure trap destination",
                        "Process incoming traps",
                        "Filter traps by OID"
                    ],
                    limitations=[
                        "Traps may be lost (UDP)",
                        "Requires trap receiver configuration",
                        "Device-specific trap formats"
                    ]
                )
            ],
            best_practices=[
                ProtocolBestPractice(
                    title="Use SNMPv3 for Security",
                    description="Always use SNMPv3 with authentication and encryption",
                    category="security",
                    importance="critical",
                    examples=[
                        "Configure user authentication",
                        "Enable encryption (AES/DES)",
                        "Use strong passwords"
                    ]
                ),
                ProtocolBestPractice(
                    title="Change Default Community Strings",
                    description="Never use default community strings like 'public'",
                    category="security",
                    importance="critical",
                    examples=[
                        "Use complex community strings",
                        "Different strings for read/write",
                        "Regular rotation of community strings"
                    ]
                )
            ],
            troubleshooting=[
                ProtocolTroubleshooting(
                    issue="No Response from Device",
                    symptoms=["Timeout waiting for response"],
                    causes=[
                        "Device not responding",
                        "Wrong community string",
                        "SNMP not enabled on device",
                        "Firewall blocking SNMP"
                    ],
                    solutions=[
                        "Verify device connectivity",
                        "Check community string",
                        "Enable SNMP on device",
                        "Check firewall rules"
                    ],
                    prevention=[
                        "Regular connectivity monitoring",
                        "Document community strings",
                        "Monitor SNMP service status"
                    ]
                )
            ],
            common_use_cases=[
                "Network device monitoring",
                "Bandwidth utilization tracking",
                "System performance monitoring",
                "Network topology discovery",
                "Fault detection and alerting",
                "Configuration backup"
            ],
            prerequisites=[
                "SNMP enabled on target device",
                "Valid community string or SNMPv3 credentials",
                "Network connectivity",
                "Knowledge of device MIBs"
            ],
            supported_platforms=["Network devices", "Servers", "Printers", "UPS systems"]
        )
        
        # HTTP/HTTPS Protocol
        protocols["http"] = ProtocolDefinition(
            name="HTTP/HTTPS",
            category=ProtocolCategory.WEB_API,
            description="Hypertext Transfer Protocol for web-based API interactions",
            default_port=80,  # 443 for HTTPS
            security_level=SecurityLevel.MEDIUM,
            capabilities=[
                ProtocolCapability(
                    name="rest_api_interaction",
                    description="Interact with RESTful web APIs",
                    parameters={
                        "url": "str",
                        "method": "str (GET, POST, PUT, DELETE, etc.)",
                        "headers": "dict",
                        "data": "dict/str",
                        "timeout": "int"
                    },
                    examples=[
                        "GET /api/v1/users",
                        "POST /api/v1/users -d '{\"name\":\"John\"}'",
                        "PUT /api/v1/users/123 -d '{\"status\":\"active\"}'"
                    ],
                    limitations=[
                        "Requires API documentation",
                        "Rate limiting may apply",
                        "Authentication requirements vary"
                    ]
                ),
                ProtocolCapability(
                    name="web_scraping",
                    description="Extract data from web pages",
                    parameters={
                        "url": "str",
                        "selectors": "list",
                        "headers": "dict",
                        "cookies": "dict"
                    },
                    examples=[
                        "Parse HTML content",
                        "Extract specific elements",
                        "Handle JavaScript-rendered content"
                    ],
                    limitations=[
                        "Website structure changes",
                        "Anti-scraping measures",
                        "Legal and ethical considerations"
                    ]
                )
            ],
            best_practices=[
                ProtocolBestPractice(
                    title="Always Use HTTPS",
                    description="Use HTTPS for all sensitive communications",
                    category="security",
                    importance="critical",
                    examples=[
                        "Verify SSL certificates",
                        "Use TLS 1.2 or higher",
                        "Implement certificate pinning"
                    ]
                ),
                ProtocolBestPractice(
                    title="Implement Proper Authentication",
                    description="Use secure authentication methods",
                    category="security",
                    importance="critical",
                    examples=[
                        "OAuth 2.0 for APIs",
                        "JWT tokens with expiration",
                        "API key management"
                    ]
                ),
                ProtocolBestPractice(
                    title="Handle Rate Limiting",
                    description="Respect API rate limits and implement backoff",
                    category="performance",
                    importance="important",
                    examples=[
                        "Check rate limit headers",
                        "Implement exponential backoff",
                        "Use connection pooling"
                    ]
                )
            ],
            troubleshooting=[
                ProtocolTroubleshooting(
                    issue="SSL Certificate Errors",
                    symptoms=["SSL certificate verify failed"],
                    causes=[
                        "Expired certificate",
                        "Self-signed certificate",
                        "Certificate chain issues",
                        "Hostname mismatch"
                    ],
                    solutions=[
                        "Update certificates",
                        "Add certificate to trust store",
                        "Verify certificate chain",
                        "Check hostname configuration"
                    ],
                    prevention=[
                        "Monitor certificate expiration",
                        "Automate certificate renewal",
                        "Regular certificate validation"
                    ]
                )
            ],
            common_use_cases=[
                "REST API integration",
                "Web service monitoring",
                "Data synchronization",
                "Webhook handling",
                "File downloads/uploads",
                "Health check endpoints"
            ],
            prerequisites=[
                "Network connectivity",
                "Valid URLs and endpoints",
                "Authentication credentials",
                "SSL certificates (for HTTPS)"
            ],
            supported_platforms=["All platforms with HTTP client support"]
        )
        
        return protocols
    
    def get_protocol(self, protocol_name: str) -> Optional[ProtocolDefinition]:
        """Get protocol definition by name"""
        return self.protocols.get(protocol_name.lower())
    
    def get_all_protocols(self) -> Dict[str, ProtocolDefinition]:
        """Get all protocol definitions"""
        return self.protocols
    
    def get_protocols_by_category(self, category: ProtocolCategory) -> List[ProtocolDefinition]:
        """Get protocols filtered by category"""
        return [protocol for protocol in self.protocols.values() if protocol.category == category]
    
    def get_protocols_by_security_level(self, security_level: SecurityLevel) -> List[ProtocolDefinition]:
        """Get protocols filtered by security level"""
        return [protocol for protocol in self.protocols.values() if protocol.security_level == security_level]
    
    def get_protocol_capabilities(self, protocol_name: str) -> List[ProtocolCapability]:
        """Get capabilities for a specific protocol"""
        protocol = self.get_protocol(protocol_name)
        return protocol.capabilities if protocol else []
    
    def get_protocol_best_practices(self, protocol_name: str, category: Optional[str] = None) -> List[ProtocolBestPractice]:
        """Get best practices for a protocol, optionally filtered by category"""
        protocol = self.get_protocol(protocol_name)
        if not protocol:
            return []
        
        practices = protocol.best_practices
        if category:
            practices = [p for p in practices if p.category == category]
        
        return practices
    
    def get_protocol_troubleshooting(self, protocol_name: str, issue: Optional[str] = None) -> List[ProtocolTroubleshooting]:
        """Get troubleshooting information for a protocol"""
        protocol = self.get_protocol(protocol_name)
        if not protocol:
            return []
        
        troubleshooting = protocol.troubleshooting
        if issue:
            troubleshooting = [t for t in troubleshooting if issue.lower() in t.issue.lower()]
        
        return troubleshooting
    
    def find_protocols_for_use_case(self, use_case: str) -> List[ProtocolDefinition]:
        """Find protocols suitable for a specific use case"""
        matching_protocols = []
        use_case_lower = use_case.lower()
        
        for protocol in self.protocols.values():
            for common_use_case in protocol.common_use_cases:
                if use_case_lower in common_use_case.lower():
                    matching_protocols.append(protocol)
                    break
        
        return matching_protocols
    
    def get_protocol_security_recommendations(self, protocol_name: str) -> List[str]:
        """Get security recommendations for a protocol"""
        protocol = self.get_protocol(protocol_name)
        if not protocol:
            return []
        
        security_practices = self.get_protocol_best_practices(protocol_name, "security")
        recommendations = []
        
        for practice in security_practices:
            if practice.importance in ["critical", "important"]:
                recommendations.append(f"{practice.title}: {practice.description}")
        
        return recommendations
    
    def validate_protocol_parameters(self, protocol_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for a protocol"""
        protocol = self.get_protocol(protocol_name)
        if not protocol:
            return {"valid": False, "error": f"Protocol {protocol_name} not found"}
        
        validation_result = {
            "valid": True,
            "missing_required": [],
            "invalid_parameters": [],
            "recommendations": []
        }
        
        # This is a simplified validation - in practice, you'd have more detailed parameter validation
        for capability in protocol.capabilities:
            for param_name, param_info in capability.parameters.items():
                if param_name not in parameters and "optional" not in param_info:
                    validation_result["missing_required"].append(param_name)
        
        if validation_result["missing_required"]:
            validation_result["valid"] = False
        
        # Add security recommendations
        security_recs = self.get_protocol_security_recommendations(protocol_name)
        validation_result["recommendations"].extend(security_recs)
        
        return validation_result
    
    def get_protocol_overview(self) -> Dict[str, Any]:
        """Get comprehensive protocol overview"""
        overview = {
            "total_protocols": len(self.protocols),
            "protocols_by_category": {},
            "protocols_by_security": {},
            "protocol_summary": []
        }
        
        for category in ProtocolCategory:
            protocols_in_category = self.get_protocols_by_category(category)
            overview["protocols_by_category"][category.value] = len(protocols_in_category)
        
        for security_level in SecurityLevel:
            protocols_with_security = self.get_protocols_by_security_level(security_level)
            overview["protocols_by_security"][security_level.value] = len(protocols_with_security)
        
        for protocol in self.protocols.values():
            protocol_info = {
                "name": protocol.name,
                "category": protocol.category.value,
                "security_level": protocol.security_level.value,
                "default_port": protocol.default_port,
                "capabilities": len(protocol.capabilities),
                "supported_platforms": len(protocol.supported_platforms)
            }
            overview["protocol_summary"].append(protocol_info)
        
        return overview

# Global instance
protocol_knowledge = ProtocolKnowledgeManager()
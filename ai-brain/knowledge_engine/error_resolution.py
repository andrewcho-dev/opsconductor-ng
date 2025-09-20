"""
OpsConductor Knowledge Engine - Error Resolution Module

This module provides intelligent error pattern recognition and resolution
strategies based on historical error data and successful recovery procedures.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Severity levels for errors"""
    CRITICAL = "critical"    # System down, data loss risk
    HIGH = "high"           # Major functionality impacted
    MEDIUM = "medium"       # Partial functionality impacted
    LOW = "low"            # Minor issues, workarounds available
    INFO = "info"          # Informational, no action needed

class ErrorCategory(Enum):
    """Categories of errors"""
    SYSTEM = "system"                    # OS-level errors
    SERVICE = "service"                  # Service-related errors
    NETWORK = "network"                  # Network connectivity errors
    DATABASE = "database"                # Database-related errors
    AUTHENTICATION = "authentication"    # Auth/permission errors
    CONFIGURATION = "configuration"      # Config-related errors
    RESOURCE = "resource"               # Resource exhaustion errors
    APPLICATION = "application"         # Application-specific errors

class ResolutionStatus(Enum):
    """Status of error resolution attempts"""
    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"

@dataclass
class ErrorPattern:
    """Pattern for matching errors"""
    pattern_id: str
    name: str
    regex_patterns: List[str]
    keywords: List[str]
    context_clues: List[str]  # Additional context that helps identify the error
    confidence_threshold: float = 0.7

@dataclass
class ResolutionStep:
    """Individual step in error resolution"""
    step_id: str
    description: str
    command: Optional[str] = None
    script: Optional[str] = None
    manual_action: Optional[str] = None
    expected_result: str = ""
    verification_command: Optional[str] = None
    timeout: Optional[int] = None
    prerequisites: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high

@dataclass
class EscalationProcedure:
    """Escalation procedure when resolution fails"""
    escalation_level: int
    contact_info: str
    escalation_criteria: List[str]
    additional_data_to_collect: List[str]
    estimated_response_time: str

@dataclass
class ErrorResolutionEntry:
    """Complete error resolution entry"""
    error_id: str
    title: str
    description: str
    category: ErrorCategory
    severity: ErrorSeverity
    error_patterns: List[ErrorPattern]
    resolution_steps: List[ResolutionStep]
    escalation_procedures: List[EscalationProcedure]
    prevention_measures: List[str]
    related_errors: List[str]
    applicable_systems: List[str]
    success_rate: float = 0.0
    average_resolution_time: float = 0.0
    total_occurrences: int = 0
    successful_resolutions: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

class ErrorResolutionManager:
    """Manages error patterns and resolution procedures"""
    
    def __init__(self):
        self.error_resolutions = self._initialize_error_resolutions()
        self._build_error_index()
        logger.info(f"Initialized error resolution manager with {len(self.error_resolutions)} error types")
    
    def _initialize_error_resolutions(self) -> Dict[str, ErrorResolutionEntry]:
        """Initialize comprehensive error resolution database"""
        resolutions = {}
        
        # SSH Connection Refused Error
        resolutions["ssh_connection_refused"] = ErrorResolutionEntry(
            error_id="ssh_connection_refused",
            title="SSH Connection Refused",
            description="SSH connection attempts are being refused by the target system",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            error_patterns=[
                ErrorPattern(
                    pattern_id="ssh_conn_refused_1",
                    name="Standard SSH Connection Refused",
                    regex_patterns=[
                        r"ssh: connect to host .* port \d+: Connection refused",
                        r"Connection refused.*port 22",
                        r"ssh_exchange_identification: Connection closed by remote host"
                    ],
                    keywords=["ssh", "connection", "refused", "port", "22"],
                    context_clues=["network", "firewall", "sshd"]
                )
            ],
            resolution_steps=[
                ResolutionStep(
                    step_id="check_target_reachability",
                    description="Verify target system is reachable",
                    command="ping -c 4 {target_host}",
                    expected_result="Ping responses received",
                    verification_command="ping -c 1 {target_host}",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_ssh_port",
                    description="Check if SSH port is open",
                    command="nmap -p 22 {target_host}",
                    expected_result="Port 22 is open",
                    timeout=60,
                    prerequisites=["nmap installed"]
                ),
                ResolutionStep(
                    step_id="check_ssh_service",
                    description="Check SSH service status on target",
                    manual_action="Log into target system via console and check: systemctl status sshd",
                    expected_result="SSH service is running",
                    risk_level="low"
                ),
                ResolutionStep(
                    step_id="start_ssh_service",
                    description="Start SSH service if not running",
                    manual_action="On target system: systemctl start sshd && systemctl enable sshd",
                    expected_result="SSH service started and enabled",
                    verification_command="systemctl is-active sshd",
                    risk_level="low"
                ),
                ResolutionStep(
                    step_id="check_firewall",
                    description="Check firewall rules for SSH",
                    manual_action="Check firewall: ufw status or iptables -L",
                    expected_result="SSH port 22 is allowed",
                    risk_level="medium"
                ),
                ResolutionStep(
                    step_id="configure_firewall",
                    description="Allow SSH through firewall",
                    manual_action="Configure firewall: ufw allow ssh or iptables -A INPUT -p tcp --dport 22 -j ACCEPT",
                    expected_result="SSH traffic allowed through firewall",
                    risk_level="medium",
                    prerequisites=["Firewall access", "Admin privileges"]
                )
            ],
            escalation_procedures=[
                EscalationProcedure(
                    escalation_level=1,
                    contact_info="Network Team",
                    escalation_criteria=["Network connectivity issues persist", "Firewall changes required"],
                    additional_data_to_collect=["Network topology", "Firewall logs", "Target system console access"],
                    estimated_response_time="30 minutes"
                )
            ],
            prevention_measures=[
                "Monitor SSH service health",
                "Implement SSH service auto-restart",
                "Regular firewall rule audits",
                "Network connectivity monitoring"
            ],
            related_errors=["service_failed_start", "network_unreachable", "authentication_failed"],
            applicable_systems=["linux_server", "network_device"],
            tags=["ssh", "connection", "network", "firewall", "service"]
        )
        
        # Service Failed to Start Error
        resolutions["service_failed_start"] = ErrorResolutionEntry(
            error_id="service_failed_start",
            title="Service Failed to Start",
            description="System service fails to start properly",
            category=ErrorCategory.SERVICE,
            severity=ErrorSeverity.HIGH,
            error_patterns=[
                ErrorPattern(
                    pattern_id="service_start_fail_1",
                    name="Systemd Service Start Failure",
                    regex_patterns=[
                        r"Job for .* failed because the control process exited with error code",
                        r"systemctl start .* failed",
                        r"Failed to start .*\.service",
                        r"Unit .* failed to load"
                    ],
                    keywords=["failed", "start", "service", "systemctl", "unit"],
                    context_clues=["systemd", "daemon", "process"]
                )
            ],
            resolution_steps=[
                ResolutionStep(
                    step_id="check_service_status",
                    description="Check detailed service status",
                    command="systemctl status {service_name} --no-pager -l",
                    expected_result="Detailed error information displayed",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_service_logs",
                    description="Examine service logs for errors",
                    command="journalctl -u {service_name} --since '1 hour ago' --no-pager",
                    expected_result="Error details found in logs",
                    timeout=60
                ),
                ResolutionStep(
                    step_id="validate_config",
                    description="Validate service configuration",
                    command="systemd-analyze verify /etc/systemd/system/{service_name}.service",
                    expected_result="No configuration errors",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_dependencies",
                    description="Check service dependencies",
                    command="systemctl list-dependencies {service_name}",
                    expected_result="All dependencies are satisfied",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_resources",
                    description="Check system resources",
                    command="df -h && free -h && ps aux | head -20",
                    expected_result="Adequate system resources available",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="fix_permissions",
                    description="Fix file permissions if needed",
                    command="chown -R {service_user}:{service_group} {service_directory}",
                    expected_result="Correct permissions set",
                    risk_level="medium",
                    prerequisites=["Service user and directory identified"]
                ),
                ResolutionStep(
                    step_id="reload_systemd",
                    description="Reload systemd configuration",
                    command="systemctl daemon-reload",
                    expected_result="Systemd configuration reloaded",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="retry_start",
                    description="Attempt to start service again",
                    command="systemctl start {service_name}",
                    expected_result="Service starts successfully",
                    verification_command="systemctl is-active {service_name}",
                    timeout=60
                )
            ],
            escalation_procedures=[
                EscalationProcedure(
                    escalation_level=1,
                    contact_info="System Administrator",
                    escalation_criteria=["Configuration issues require expertise", "Resource constraints identified"],
                    additional_data_to_collect=["Full system logs", "Configuration files", "Resource usage history"],
                    estimated_response_time="15 minutes"
                )
            ],
            prevention_measures=[
                "Regular configuration validation",
                "Automated service health monitoring",
                "Resource usage monitoring",
                "Configuration change management"
            ],
            related_errors=["disk_space_full", "permission_denied", "dependency_missing"],
            applicable_systems=["linux_server", "container"],
            tags=["service", "systemd", "startup", "configuration"]
        )
        
        # Database Connection Error
        resolutions["database_connection_error"] = ErrorResolutionEntry(
            error_id="database_connection_error",
            title="Database Connection Error",
            description="Unable to establish connection to database server",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.CRITICAL,
            error_patterns=[
                ErrorPattern(
                    pattern_id="db_conn_error_1",
                    name="PostgreSQL Connection Error",
                    regex_patterns=[
                        r"could not connect to server: Connection refused",
                        r"FATAL: database .* does not exist",
                        r"FATAL: password authentication failed",
                        r"server closed the connection unexpectedly"
                    ],
                    keywords=["database", "connection", "postgresql", "fatal", "refused"],
                    context_clues=["postgres", "psql", "pg_", "port 5432"]
                ),
                ErrorPattern(
                    pattern_id="db_conn_error_2",
                    name="MySQL Connection Error",
                    regex_patterns=[
                        r"Can't connect to MySQL server",
                        r"Access denied for user",
                        r"Unknown database",
                        r"Lost connection to MySQL server"
                    ],
                    keywords=["mysql", "connection", "access", "denied", "server"],
                    context_clues=["mysql", "mysqld", "port 3306"]
                )
            ],
            resolution_steps=[
                ResolutionStep(
                    step_id="test_db_connectivity",
                    description="Test database server connectivity",
                    command="pg_isready -h {db_host} -p {db_port} -U {db_user}",
                    expected_result="Database server is accepting connections",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_db_service",
                    description="Check database service status",
                    command="systemctl status postgresql",
                    expected_result="Database service is running",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_db_logs",
                    description="Check database logs for errors",
                    command="tail -50 /var/log/postgresql/postgresql-*.log",
                    expected_result="Error details in database logs",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_db_port",
                    description="Verify database port is listening",
                    command="netstat -tlnp | grep :{db_port}",
                    expected_result="Database port is listening",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="restart_db_service",
                    description="Restart database service",
                    command="systemctl restart postgresql",
                    expected_result="Database service restarted successfully",
                    verification_command="systemctl is-active postgresql",
                    timeout=120,
                    risk_level="high"
                ),
                ResolutionStep(
                    step_id="verify_db_connection",
                    description="Verify database connection is restored",
                    command="pg_isready -h {db_host} -p {db_port} -U {db_user}",
                    expected_result="Connection successful",
                    timeout=60
                ),
                ResolutionStep(
                    step_id="test_db_query",
                    description="Test basic database query",
                    command="psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -c 'SELECT 1;'",
                    expected_result="Query executes successfully",
                    timeout=30
                )
            ],
            escalation_procedures=[
                EscalationProcedure(
                    escalation_level=1,
                    contact_info="Database Administrator",
                    escalation_criteria=["Database corruption suspected", "Performance issues persist"],
                    additional_data_to_collect=["Database logs", "Performance metrics", "Disk usage"],
                    estimated_response_time="10 minutes"
                ),
                EscalationProcedure(
                    escalation_level=2,
                    contact_info="Senior DBA / Vendor Support",
                    escalation_criteria=["Data recovery required", "Major database issues"],
                    additional_data_to_collect=["Full system backup", "Database configuration", "Hardware status"],
                    estimated_response_time="1 hour"
                )
            ],
            prevention_measures=[
                "Database connection monitoring",
                "Regular database health checks",
                "Connection pool configuration",
                "Database backup verification"
            ],
            related_errors=["service_failed_start", "network_unreachable", "authentication_failed"],
            applicable_systems=["database", "linux_server"],
            tags=["database", "connection", "postgresql", "mysql", "critical"]
        )
        
        # Disk Space Full Error
        resolutions["disk_space_full"] = ErrorResolutionEntry(
            error_id="disk_space_full",
            title="Disk Space Full",
            description="File system has run out of available disk space",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.CRITICAL,
            error_patterns=[
                ErrorPattern(
                    pattern_id="disk_full_1",
                    name="No Space Left on Device",
                    regex_patterns=[
                        r"No space left on device",
                        r"Disk full",
                        r"write failed, filesystem is full",
                        r"cannot create.*No space left on device"
                    ],
                    keywords=["space", "disk", "full", "device", "filesystem"],
                    context_clues=["write", "create", "copy", "mv"]
                )
            ],
            resolution_steps=[
                ResolutionStep(
                    step_id="check_disk_usage",
                    description="Check disk usage by filesystem",
                    command="df -h",
                    expected_result="Disk usage information displayed",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="identify_large_files",
                    description="Identify largest files and directories",
                    command="du -sh /* 2>/dev/null | sort -hr | head -10",
                    expected_result="Largest directories identified",
                    timeout=60
                ),
                ResolutionStep(
                    step_id="check_log_files",
                    description="Check for large log files",
                    command="find /var/log -type f -size +100M -exec ls -lh {} \\;",
                    expected_result="Large log files identified",
                    timeout=60
                ),
                ResolutionStep(
                    step_id="clean_temp_files",
                    description="Clean temporary files",
                    command="find /tmp -type f -atime +7 -delete && find /var/tmp -type f -atime +7 -delete",
                    expected_result="Temporary files cleaned",
                    timeout=120,
                    risk_level="low"
                ),
                ResolutionStep(
                    step_id="rotate_logs",
                    description="Force log rotation",
                    command="logrotate -f /etc/logrotate.conf",
                    expected_result="Log files rotated and compressed",
                    timeout=300,
                    risk_level="low"
                ),
                ResolutionStep(
                    step_id="clean_package_cache",
                    description="Clean package manager cache",
                    command="apt-get clean && apt-get autoremove -y",
                    expected_result="Package cache cleaned",
                    timeout=180,
                    risk_level="low"
                ),
                ResolutionStep(
                    step_id="verify_space_freed",
                    description="Verify disk space has been freed",
                    command="df -h",
                    expected_result="Available disk space increased",
                    timeout=30
                )
            ],
            escalation_procedures=[
                EscalationProcedure(
                    escalation_level=1,
                    contact_info="System Administrator",
                    escalation_criteria=["Insufficient space freed", "Critical files need removal"],
                    additional_data_to_collect=["Detailed disk usage report", "Application data locations"],
                    estimated_response_time="15 minutes"
                ),
                EscalationProcedure(
                    escalation_level=2,
                    contact_info="Infrastructure Team",
                    escalation_criteria=["Storage expansion required", "Data migration needed"],
                    additional_data_to_collect=["Storage capacity planning", "Growth projections"],
                    estimated_response_time="2 hours"
                )
            ],
            prevention_measures=[
                "Disk space monitoring and alerting",
                "Automated log rotation",
                "Regular cleanup scripts",
                "Capacity planning and monitoring"
            ],
            related_errors=["service_failed_start", "database_connection_error", "application_crash"],
            applicable_systems=["linux_server", "container", "database"],
            tags=["disk", "space", "storage", "cleanup", "critical"]
        )
        
        # Permission Denied Error
        resolutions["permission_denied"] = ErrorResolutionEntry(
            error_id="permission_denied",
            title="Permission Denied",
            description="Access denied due to insufficient file or directory permissions",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            error_patterns=[
                ErrorPattern(
                    pattern_id="permission_denied_1",
                    name="File Permission Denied",
                    regex_patterns=[
                        r"Permission denied",
                        r"Access denied",
                        r"Operation not permitted",
                        r"cannot access.*Permission denied"
                    ],
                    keywords=["permission", "denied", "access", "operation", "permitted"],
                    context_clues=["file", "directory", "chmod", "chown"]
                )
            ],
            resolution_steps=[
                ResolutionStep(
                    step_id="check_file_permissions",
                    description="Check current file/directory permissions",
                    command="ls -la {file_path}",
                    expected_result="Current permissions displayed",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_ownership",
                    description="Check file ownership",
                    command="stat {file_path}",
                    expected_result="File ownership and permissions displayed",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="check_user_groups",
                    description="Check current user's groups",
                    command="groups && id",
                    expected_result="User group membership displayed",
                    timeout=30
                ),
                ResolutionStep(
                    step_id="fix_permissions",
                    description="Fix file permissions",
                    command="chmod {permissions} {file_path}",
                    expected_result="Permissions updated",
                    verification_command="ls -la {file_path}",
                    risk_level="medium",
                    prerequisites=["Correct permissions identified"]
                ),
                ResolutionStep(
                    step_id="fix_ownership",
                    description="Fix file ownership if needed",
                    command="chown {owner}:{group} {file_path}",
                    expected_result="Ownership updated",
                    verification_command="stat {file_path}",
                    risk_level="medium",
                    prerequisites=["Correct ownership identified", "Admin privileges"]
                ),
                ResolutionStep(
                    step_id="test_access",
                    description="Test file access",
                    command="test -r {file_path} && echo 'Read OK' || echo 'Read Failed'",
                    expected_result="Access test successful",
                    timeout=30
                )
            ],
            escalation_procedures=[
                EscalationProcedure(
                    escalation_level=1,
                    contact_info="System Administrator",
                    escalation_criteria=["Complex permission structure", "Security policy questions"],
                    additional_data_to_collect=["Directory structure", "Security requirements"],
                    estimated_response_time="20 minutes"
                )
            ],
            prevention_measures=[
                "Regular permission audits",
                "Proper file creation procedures",
                "User access management",
                "Security policy enforcement"
            ],
            related_errors=["service_failed_start", "authentication_failed", "file_not_found"],
            applicable_systems=["linux_server", "container"],
            tags=["permission", "access", "security", "filesystem"]
        )
        
        return resolutions
    
    def _build_error_index(self) -> None:
        """Build search index for error patterns"""
        self._error_index = {
            "by_category": {},
            "by_severity": {},
            "by_keyword": {},
            "by_system": {}
        }
        
        for resolution in self.error_resolutions.values():
            # Index by category
            category = resolution.category.value
            if category not in self._error_index["by_category"]:
                self._error_index["by_category"][category] = []
            self._error_index["by_category"][category].append(resolution.error_id)
            
            # Index by severity
            severity = resolution.severity.value
            if severity not in self._error_index["by_severity"]:
                self._error_index["by_severity"][severity] = []
            self._error_index["by_severity"][severity].append(resolution.error_id)
            
            # Index by keywords from all patterns
            all_keywords = set()
            for pattern in resolution.error_patterns:
                all_keywords.update(pattern.keywords)
            
            for keyword in all_keywords:
                if keyword not in self._error_index["by_keyword"]:
                    self._error_index["by_keyword"][keyword] = []
                self._error_index["by_keyword"][keyword].append(resolution.error_id)
            
            # Index by applicable systems
            for system in resolution.applicable_systems:
                if system not in self._error_index["by_system"]:
                    self._error_index["by_system"][system] = []
                self._error_index["by_system"][system].append(resolution.error_id)
    
    def identify_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> List[Tuple[ErrorResolutionEntry, float]]:
        """Identify error type from error message and return matches with confidence scores"""
        matches = []
        
        error_message_lower = error_message.lower()
        
        for resolution in self.error_resolutions.values():
            max_confidence = 0.0
            
            for pattern in resolution.error_patterns:
                confidence = self._calculate_pattern_confidence(error_message, pattern, context)
                max_confidence = max(max_confidence, confidence)
            
            if max_confidence >= 0.3:  # Minimum confidence threshold
                matches.append((resolution, max_confidence))
        
        # Sort by confidence score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _calculate_pattern_confidence(self, 
                                    error_message: str, 
                                    pattern: ErrorPattern, 
                                    context: Optional[Dict[str, Any]] = None) -> float:
        """Calculate confidence score for pattern match"""
        confidence = 0.0
        error_message_lower = error_message.lower()
        
        # Check regex patterns
        regex_matches = 0
        for regex_pattern in pattern.regex_patterns:
            if re.search(regex_pattern, error_message, re.IGNORECASE):
                regex_matches += 1
        
        if regex_matches > 0:
            confidence += 0.6 * (regex_matches / len(pattern.regex_patterns))
        
        # Check keyword matches
        keyword_matches = 0
        for keyword in pattern.keywords:
            if keyword.lower() in error_message_lower:
                keyword_matches += 1
        
        if keyword_matches > 0:
            confidence += 0.3 * (keyword_matches / len(pattern.keywords))
        
        # Check context clues if context provided
        if context:
            context_matches = 0
            context_text = " ".join(str(v).lower() for v in context.values())
            
            for clue in pattern.context_clues:
                if clue.lower() in context_text:
                    context_matches += 1
            
            if context_matches > 0 and pattern.context_clues:
                confidence += 0.1 * (context_matches / len(pattern.context_clues))
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def get_resolution_steps(self, error_id: str) -> List[ResolutionStep]:
        """Get resolution steps for a specific error"""
        resolution = self.error_resolutions.get(error_id)
        return resolution.resolution_steps if resolution else []
    
    def get_escalation_procedures(self, error_id: str) -> List[EscalationProcedure]:
        """Get escalation procedures for a specific error"""
        resolution = self.error_resolutions.get(error_id)
        return resolution.escalation_procedures if resolution else []
    
    def get_prevention_measures(self, error_id: str) -> List[str]:
        """Get prevention measures for a specific error"""
        resolution = self.error_resolutions.get(error_id)
        return resolution.prevention_measures if resolution else []
    
    def search_by_category(self, category: ErrorCategory) -> List[ErrorResolutionEntry]:
        """Search error resolutions by category"""
        category_value = category.value
        if category_value in self._error_index["by_category"]:
            error_ids = self._error_index["by_category"][category_value]
            return [self.error_resolutions[error_id] for error_id in error_ids]
        return []
    
    def search_by_severity(self, severity: ErrorSeverity) -> List[ErrorResolutionEntry]:
        """Search error resolutions by severity"""
        severity_value = severity.value
        if severity_value in self._error_index["by_severity"]:
            error_ids = self._error_index["by_severity"][severity_value]
            return [self.error_resolutions[error_id] for error_id in error_ids]
        return []
    
    def search_by_keywords(self, keywords: List[str]) -> List[ErrorResolutionEntry]:
        """Search error resolutions by keywords"""
        matching_error_ids = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self._error_index["by_keyword"]:
                matching_error_ids.update(self._error_index["by_keyword"][keyword_lower])
        
        return [self.error_resolutions[error_id] for error_id in matching_error_ids]
    
    def get_critical_errors(self) -> List[ErrorResolutionEntry]:
        """Get all critical error resolutions"""
        return self.search_by_severity(ErrorSeverity.CRITICAL)
    
    def record_resolution_attempt(self, 
                                error_id: str, 
                                status: ResolutionStatus, 
                                resolution_time: float,
                                notes: Optional[str] = None) -> None:
        """Record the outcome of a resolution attempt"""
        resolution = self.error_resolutions.get(error_id)
        if not resolution:
            return
        
        resolution.total_occurrences += 1
        
        if status == ResolutionStatus.RESOLVED:
            resolution.successful_resolutions += 1
            
            # Update average resolution time
            if resolution.successful_resolutions == 1:
                resolution.average_resolution_time = resolution_time
            else:
                total_time = (resolution.average_resolution_time * 
                            (resolution.successful_resolutions - 1) + resolution_time)
                resolution.average_resolution_time = total_time / resolution.successful_resolutions
        
        # Update success rate
        resolution.success_rate = (resolution.successful_resolutions / resolution.total_occurrences) * 100
        resolution.last_updated = datetime.now()
        
        logger.info(f"Recorded resolution attempt for {error_id}: {status.value}, time: {resolution_time}s")
    
    def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get statistics about error resolutions"""
        stats = {
            "total_error_types": len(self.error_resolutions),
            "errors_by_category": {},
            "errors_by_severity": {},
            "average_success_rate": 0,
            "most_common_errors": [],
            "most_successful_resolutions": []
        }
        
        total_success_rate = 0
        total_occurrences = 0
        
        for resolution in self.error_resolutions.values():
            # Category statistics
            category = resolution.category.value
            stats["errors_by_category"][category] = stats["errors_by_category"].get(category, 0) + 1
            
            # Severity statistics
            severity = resolution.severity.value
            stats["errors_by_severity"][severity] = stats["errors_by_severity"].get(severity, 0) + 1
            
            # Success rate statistics
            total_success_rate += resolution.success_rate
            total_occurrences += resolution.total_occurrences
        
        if len(self.error_resolutions) > 0:
            stats["average_success_rate"] = total_success_rate / len(self.error_resolutions)
        
        # Most common errors (by occurrence count)
        common_errors = sorted(
            self.error_resolutions.values(),
            key=lambda r: r.total_occurrences,
            reverse=True
        )[:5]
        
        stats["most_common_errors"] = [
            {
                "error_id": r.error_id,
                "title": r.title,
                "total_occurrences": r.total_occurrences,
                "success_rate": r.success_rate
            }
            for r in common_errors if r.total_occurrences > 0
        ]
        
        # Most successful resolutions (by success rate)
        successful_resolutions = sorted(
            [r for r in self.error_resolutions.values() if r.total_occurrences > 0],
            key=lambda r: r.success_rate,
            reverse=True
        )[:5]
        
        stats["most_successful_resolutions"] = [
            {
                "error_id": r.error_id,
                "title": r.title,
                "success_rate": r.success_rate,
                "average_resolution_time": r.average_resolution_time
            }
            for r in successful_resolutions
        ]
        
        return stats
    
    def export_resolution_guide(self, error_id: str, format: str = "markdown") -> Optional[str]:
        """Export resolution guide in specified format"""
        resolution = self.error_resolutions.get(error_id)
        if not resolution:
            return None
        
        if format.lower() == "markdown":
            guide = f"# {resolution.title}\n\n"
            guide += f"**Category:** {resolution.category.value}\n"
            guide += f"**Severity:** {resolution.severity.value}\n"
            guide += f"**Success Rate:** {resolution.success_rate:.1f}%\n\n"
            guide += f"## Description\n{resolution.description}\n\n"
            
            # Error patterns
            guide += "## Error Patterns\n"
            for pattern in resolution.error_patterns:
                guide += f"- {pattern.name}\n"
                for regex in pattern.regex_patterns:
                    guide += f"  - `{regex}`\n"
            guide += "\n"
            
            # Resolution steps
            guide += "## Resolution Steps\n\n"
            for i, step in enumerate(resolution.resolution_steps, 1):
                guide += f"### {i}. {step.description}\n\n"
                if step.command:
                    guide += f"```bash\n{step.command}\n```\n\n"
                if step.manual_action:
                    guide += f"**Manual Action:** {step.manual_action}\n\n"
                guide += f"**Expected Result:** {step.expected_result}\n\n"
                if step.prerequisites:
                    guide += "**Prerequisites:**\n"
                    for prereq in step.prerequisites:
                        guide += f"- {prereq}\n"
                    guide += "\n"
            
            # Prevention measures
            if resolution.prevention_measures:
                guide += "## Prevention Measures\n\n"
                for measure in resolution.prevention_measures:
                    guide += f"- {measure}\n"
                guide += "\n"
            
            # Escalation procedures
            if resolution.escalation_procedures:
                guide += "## Escalation Procedures\n\n"
                for escalation in resolution.escalation_procedures:
                    guide += f"### Level {escalation.escalation_level}: {escalation.contact_info}\n"
                    guide += f"**Response Time:** {escalation.estimated_response_time}\n\n"
                    guide += "**Escalation Criteria:**\n"
                    for criteria in escalation.escalation_criteria:
                        guide += f"- {criteria}\n"
                    guide += "\n"
            
            return guide
        
        return None

# Global instance
error_resolution = ErrorResolutionManager()
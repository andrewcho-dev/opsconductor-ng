"""
OpsConductor Knowledge Engine - IT Knowledge Base Module

This module provides comprehensive IT knowledge including best practices,
troubleshooting procedures, security guidelines, and operational wisdom.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class KnowledgeCategory(Enum):
    """Categories of IT knowledge"""
    BEST_PRACTICES = "best_practices"
    TROUBLESHOOTING = "troubleshooting"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    DISASTER_RECOVERY = "disaster_recovery"
    MONITORING = "monitoring"
    AUTOMATION = "automation"

class Severity(Enum):
    """Severity levels for knowledge items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class KnowledgeType(Enum):
    """Types of knowledge entries"""
    PROCEDURE = "procedure"
    GUIDELINE = "guideline"
    CHECKLIST = "checklist"
    REFERENCE = "reference"
    SOLUTION = "solution"
    WARNING = "warning"

@dataclass
class KnowledgeStep:
    """Individual step in a knowledge procedure"""
    step_number: int
    description: str
    command: Optional[str] = None
    expected_result: Optional[str] = None
    troubleshooting_notes: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

@dataclass
class KnowledgeEntry:
    """Complete knowledge base entry"""
    id: str
    title: str
    category: KnowledgeCategory
    knowledge_type: KnowledgeType
    description: str
    severity: Severity
    tags: List[str]
    applicable_systems: List[str]
    steps: List[KnowledgeStep] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    author: str = "OpsConductor AI"
    version: str = "1.0"

class ITKnowledgeBase:
    """Comprehensive IT knowledge base with search and recommendation capabilities"""
    
    def __init__(self):
        self.knowledge_entries = self._initialize_knowledge_base()
        self._build_search_index()
        logger.info(f"Initialized IT knowledge base with {len(self.knowledge_entries)} entries")
    
    def _initialize_knowledge_base(self) -> Dict[str, KnowledgeEntry]:
        """Initialize comprehensive IT knowledge base"""
        entries = {}
        
        # Linux System Administration Best Practices
        entries["linux_service_management"] = KnowledgeEntry(
            id="linux_service_management",
            title="Linux Service Management Best Practices",
            category=KnowledgeCategory.BEST_PRACTICES,
            knowledge_type=KnowledgeType.GUIDELINE,
            description="Best practices for managing systemd services on Linux systems",
            severity=Severity.HIGH,
            tags=["linux", "systemd", "services", "administration"],
            applicable_systems=["linux_server", "container"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Always check service status before making changes",
                    command="systemctl status <service_name>",
                    expected_result="Service status and recent log entries displayed"
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Use reload instead of restart when possible",
                    command="systemctl reload <service_name>",
                    expected_result="Service configuration reloaded without interruption",
                    troubleshooting_notes=["If reload fails, check if service supports it", "Fall back to restart if reload not supported"]
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Verify service is enabled for automatic startup",
                    command="systemctl is-enabled <service_name>",
                    expected_result="enabled",
                    troubleshooting_notes=["Enable with: systemctl enable <service_name>"]
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Monitor service logs for errors",
                    command="journalctl -u <service_name> -f",
                    expected_result="Real-time log monitoring active"
                )
            ],
            related_entries=["service_troubleshooting", "systemd_security"],
            references=[
                "https://www.freedesktop.org/software/systemd/man/systemctl.html",
                "https://wiki.archlinux.org/title/systemd"
            ]
        )
        
        # Service Troubleshooting Procedures
        entries["service_troubleshooting"] = KnowledgeEntry(
            id="service_troubleshooting",
            title="Service Troubleshooting Procedures",
            category=KnowledgeCategory.TROUBLESHOOTING,
            knowledge_type=KnowledgeType.PROCEDURE,
            description="Step-by-step troubleshooting for failed services",
            severity=Severity.CRITICAL,
            tags=["troubleshooting", "services", "systemd", "debugging"],
            applicable_systems=["linux_server", "container"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Check service status and recent failures",
                    command="systemctl status <service_name> --no-pager -l",
                    expected_result="Detailed service status with error messages"
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Examine service logs for error details",
                    command="journalctl -u <service_name> --since '1 hour ago' --no-pager",
                    expected_result="Recent log entries showing error details"
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Check service configuration file syntax",
                    command="systemd-analyze verify /etc/systemd/system/<service_name>.service",
                    expected_result="No syntax errors reported",
                    troubleshooting_notes=["Fix any syntax errors before proceeding"]
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Verify service dependencies are running",
                    command="systemctl list-dependencies <service_name>",
                    expected_result="All dependencies shown as active",
                    troubleshooting_notes=["Start any failed dependencies first"]
                ),
                KnowledgeStep(
                    step_number=5,
                    description="Check system resources (disk, memory, CPU)",
                    command="df -h && free -h && top -bn1 | head -20",
                    expected_result="Adequate resources available",
                    troubleshooting_notes=["Free up resources if system is constrained"]
                ),
                KnowledgeStep(
                    step_number=6,
                    description="Attempt service restart with detailed logging",
                    command="systemctl restart <service_name> && systemctl status <service_name>",
                    expected_result="Service starts successfully"
                )
            ],
            related_entries=["linux_service_management", "performance_troubleshooting"],
            references=[
                "https://www.freedesktop.org/software/systemd/man/systemd-analyze.html"
            ]
        )
        
        # Security Hardening Guidelines
        entries["ssh_security_hardening"] = KnowledgeEntry(
            id="ssh_security_hardening",
            title="SSH Security Hardening Guidelines",
            category=KnowledgeCategory.SECURITY,
            knowledge_type=KnowledgeType.CHECKLIST,
            description="Essential security configurations for SSH servers",
            severity=Severity.CRITICAL,
            tags=["ssh", "security", "hardening", "authentication"],
            applicable_systems=["linux_server", "network_device"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Disable root login via SSH",
                    command="sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config",
                    expected_result="Root login disabled in SSH configuration",
                    prerequisites=["Ensure non-root user with sudo access exists"]
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Change default SSH port",
                    command="sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config",
                    expected_result="SSH port changed from default 22",
                    troubleshooting_notes=["Update firewall rules for new port", "Inform users of port change"]
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Disable password authentication (use keys only)",
                    command="sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config",
                    expected_result="Password authentication disabled",
                    prerequisites=["Ensure SSH keys are properly configured for all users"]
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Configure SSH key-based authentication",
                    command="ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa",
                    expected_result="SSH key pair generated",
                    troubleshooting_notes=["Copy public key to target: ssh-copy-id user@host"]
                ),
                KnowledgeStep(
                    step_number=5,
                    description="Set up fail2ban for brute force protection",
                    command="apt-get install fail2ban && systemctl enable fail2ban",
                    expected_result="Fail2ban installed and enabled"
                ),
                KnowledgeStep(
                    step_number=6,
                    description="Restart SSH service to apply changes",
                    command="systemctl restart sshd && systemctl status sshd",
                    expected_result="SSH service restarted successfully with new configuration"
                )
            ],
            related_entries=["firewall_configuration", "user_access_control"],
            references=[
                "https://www.ssh.com/academy/ssh/sshd_config",
                "https://www.fail2ban.org/wiki/index.php/Main_Page"
            ]
        )
        
        # Performance Optimization Guidelines
        entries["web_server_performance"] = KnowledgeEntry(
            id="web_server_performance",
            title="Web Server Performance Optimization",
            category=KnowledgeCategory.PERFORMANCE,
            knowledge_type=KnowledgeType.GUIDELINE,
            description="Best practices for optimizing web server performance",
            severity=Severity.MEDIUM,
            tags=["performance", "web_server", "nginx", "apache", "optimization"],
            applicable_systems=["linux_server", "web_service"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Enable gzip compression",
                    command="# For Nginx: add to server block\ngzip on;\ngzip_types text/plain text/css application/json application/javascript;",
                    expected_result="Compression enabled for text-based content"
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Configure appropriate worker processes",
                    command="# Set worker_processes to number of CPU cores\nworker_processes auto;",
                    expected_result="Worker processes optimized for available CPU cores"
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Set up browser caching headers",
                    command="# Add cache headers for static content\nlocation ~* \\.(jpg|jpeg|png|gif|ico|css|js)$ {\n    expires 1y;\n    add_header Cache-Control public;\n}",
                    expected_result="Static content cached by browsers"
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Monitor server performance metrics",
                    command="htop && iotop && nethogs",
                    expected_result="Real-time performance monitoring active",
                    troubleshooting_notes=["Install monitoring tools if not available"]
                )
            ],
            related_entries=["monitoring_setup", "capacity_planning"],
            references=[
                "https://nginx.org/en/docs/http/ngx_http_gzip_module.html"
            ]
        )
        
        # Database Maintenance Procedures
        entries["database_maintenance"] = KnowledgeEntry(
            id="database_maintenance",
            title="Database Maintenance Best Practices",
            category=KnowledgeCategory.BEST_PRACTICES,
            knowledge_type=KnowledgeType.PROCEDURE,
            description="Regular maintenance procedures for database health",
            severity=Severity.HIGH,
            tags=["database", "maintenance", "postgresql", "mysql", "backup"],
            applicable_systems=["database", "linux_server"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Perform regular database backups",
                    command="pg_dump -h localhost -U postgres -d database_name > backup_$(date +%Y%m%d).sql",
                    expected_result="Database backup created successfully",
                    prerequisites=["Sufficient disk space for backup", "Database credentials available"]
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Analyze database performance",
                    command="# PostgreSQL: Check slow queries\nSELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;",
                    expected_result="Slow queries identified for optimization"
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Update database statistics",
                    command="# PostgreSQL: Update table statistics\nANALYZE;",
                    expected_result="Database statistics updated for query optimization"
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Check database integrity",
                    command="# PostgreSQL: Check for corruption\nSELECT datname, pg_database_size(datname) FROM pg_database;",
                    expected_result="Database integrity verified"
                ),
                KnowledgeStep(
                    step_number=5,
                    description="Monitor database connections",
                    command="# PostgreSQL: Check active connections\nSELECT count(*) FROM pg_stat_activity;",
                    expected_result="Connection count within acceptable limits"
                )
            ],
            related_entries=["backup_procedures", "performance_monitoring"],
            references=[
                "https://www.postgresql.org/docs/current/maintenance.html"
            ]
        )
        
        # Monitoring and Alerting Setup
        entries["monitoring_setup"] = KnowledgeEntry(
            id="monitoring_setup",
            title="System Monitoring and Alerting Setup",
            category=KnowledgeCategory.MONITORING,
            knowledge_type=KnowledgeType.PROCEDURE,
            description="Comprehensive system monitoring configuration",
            severity=Severity.HIGH,
            tags=["monitoring", "alerting", "metrics", "logging"],
            applicable_systems=["linux_server", "network_device", "web_service"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Set up system resource monitoring",
                    command="# Install monitoring tools\napt-get install htop iotop nethogs sysstat",
                    expected_result="System monitoring tools installed"
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Configure log rotation",
                    command="# Configure logrotate for application logs\necho '/var/log/app/*.log {\n    daily\n    rotate 30\n    compress\n    missingok\n    notifempty\n}' > /etc/logrotate.d/app",
                    expected_result="Log rotation configured to prevent disk space issues"
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Set up disk space monitoring",
                    command="# Create disk space check script\necho '#!/bin/bash\ndf -h | awk \\'$5 > 80 {print $0}\\' | mail -s \"Disk Space Alert\" admin@company.com' > /usr/local/bin/disk-check.sh",
                    expected_result="Disk space monitoring script created"
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Configure service health checks",
                    command="# Add health check to crontab\necho '*/5 * * * * systemctl is-active nginx || echo \"Nginx down\" | mail -s \"Service Alert\" admin@company.com' | crontab -",
                    expected_result="Automated service health checks configured"
                )
            ],
            related_entries=["log_management", "alerting_procedures"],
            references=[
                "https://linux.die.net/man/8/logrotate"
            ]
        )
        
        # Disaster Recovery Procedures
        entries["disaster_recovery"] = KnowledgeEntry(
            id="disaster_recovery",
            title="Disaster Recovery Procedures",
            category=KnowledgeCategory.DISASTER_RECOVERY,
            knowledge_type=KnowledgeType.PROCEDURE,
            description="Step-by-step disaster recovery and business continuity procedures",
            severity=Severity.CRITICAL,
            tags=["disaster_recovery", "backup", "restore", "business_continuity"],
            applicable_systems=["linux_server", "database", "web_service"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Assess the scope of the disaster",
                    command="# Check system status and identify affected services\nsystemctl --failed && df -h && free -h",
                    expected_result="Clear understanding of system state and failures"
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Activate incident response team",
                    command="# Notify stakeholders and activate response procedures\necho 'Disaster recovery initiated' | mail -s 'URGENT: DR Activated' team@company.com",
                    expected_result="Response team notified and activated"
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Isolate affected systems",
                    command="# Prevent further damage by isolating compromised systems\niptables -A INPUT -j DROP && iptables -A OUTPUT -j DROP",
                    expected_result="Affected systems isolated from network",
                    troubleshooting_notes=["Ensure management access is maintained"]
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Begin data recovery from backups",
                    command="# Restore from most recent backup\ntar -xzf /backup/latest_backup.tar.gz -C /recovery/",
                    expected_result="Data recovery initiated from backup",
                    prerequisites=["Verified backup integrity", "Adequate storage space"]
                ),
                KnowledgeStep(
                    step_number=5,
                    description="Validate recovered systems",
                    command="# Test critical services and data integrity\nsystemctl status critical-service && /usr/local/bin/data-integrity-check.sh",
                    expected_result="Systems validated and functioning correctly"
                )
            ],
            related_entries=["backup_procedures", "incident_response"],
            references=[
                "https://www.ready.gov/business/implementation/IT"
            ]
        )
        
        # Compliance and Audit Procedures
        entries["security_compliance"] = KnowledgeEntry(
            id="security_compliance",
            title="Security Compliance and Audit Procedures",
            category=KnowledgeCategory.COMPLIANCE,
            knowledge_type=KnowledgeType.CHECKLIST,
            description="Security compliance checks and audit procedures",
            severity=Severity.HIGH,
            tags=["compliance", "audit", "security", "governance"],
            applicable_systems=["linux_server", "database", "web_service"],
            steps=[
                KnowledgeStep(
                    step_number=1,
                    description="Review user access and permissions",
                    command="# Audit user accounts and permissions\ncut -d: -f1 /etc/passwd && find / -perm -4000 -type f 2>/dev/null",
                    expected_result="Complete inventory of users and SUID files"
                ),
                KnowledgeStep(
                    step_number=2,
                    description="Check for security updates",
                    command="# Check for available security updates\napt list --upgradable | grep -i security",
                    expected_result="List of available security updates"
                ),
                KnowledgeStep(
                    step_number=3,
                    description="Verify firewall configuration",
                    command="# Review firewall rules\nufw status verbose && iptables -L -n",
                    expected_result="Firewall properly configured with minimal required access"
                ),
                KnowledgeStep(
                    step_number=4,
                    description="Audit log files for security events",
                    command="# Check authentication logs for suspicious activity\ngrep -i 'failed\\|error\\|invalid' /var/log/auth.log | tail -20",
                    expected_result="No suspicious authentication attempts detected"
                ),
                KnowledgeStep(
                    step_number=5,
                    description="Verify backup integrity and encryption",
                    command="# Test backup restoration and verify encryption\ntar -tzf /backup/latest.tar.gz.gpg > /dev/null && echo 'Backup integrity verified'",
                    expected_result="Backups are intact and properly encrypted"
                )
            ],
            related_entries=["ssh_security_hardening", "user_access_control"],
            references=[
                "https://www.cisecurity.org/cis-benchmarks/"
            ]
        )
        
        return entries
    
    def _build_search_index(self) -> None:
        """Build search index for fast knowledge retrieval"""
        self._search_index = {
            "by_tag": {},
            "by_category": {},
            "by_system": {},
            "by_severity": {}
        }
        
        for entry in self.knowledge_entries.values():
            # Index by tags
            for tag in entry.tags:
                if tag not in self._search_index["by_tag"]:
                    self._search_index["by_tag"][tag] = []
                self._search_index["by_tag"][tag].append(entry.id)
            
            # Index by category
            category = entry.category.value
            if category not in self._search_index["by_category"]:
                self._search_index["by_category"][category] = []
            self._search_index["by_category"][category].append(entry.id)
            
            # Index by applicable systems
            for system in entry.applicable_systems:
                if system not in self._search_index["by_system"]:
                    self._search_index["by_system"][system] = []
                self._search_index["by_system"][system].append(entry.id)
            
            # Index by severity
            severity = entry.severity.value
            if severity not in self._search_index["by_severity"]:
                self._search_index["by_severity"][severity] = []
            self._search_index["by_severity"][severity].append(entry.id)
    
    def get_knowledge_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get knowledge entry by ID"""
        return self.knowledge_entries.get(entry_id)
    
    def search_by_tags(self, tags: List[str]) -> List[KnowledgeEntry]:
        """Search knowledge entries by tags"""
        matching_entries = set()
        
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self._search_index["by_tag"]:
                matching_entries.update(self._search_index["by_tag"][tag_lower])
        
        return [self.knowledge_entries[entry_id] for entry_id in matching_entries]
    
    def search_by_category(self, category: KnowledgeCategory) -> List[KnowledgeEntry]:
        """Search knowledge entries by category"""
        category_value = category.value
        if category_value in self._search_index["by_category"]:
            entry_ids = self._search_index["by_category"][category_value]
            return [self.knowledge_entries[entry_id] for entry_id in entry_ids]
        return []
    
    def search_by_system_type(self, system_type: str) -> List[KnowledgeEntry]:
        """Search knowledge entries applicable to a system type"""
        if system_type in self._search_index["by_system"]:
            entry_ids = self._search_index["by_system"][system_type]
            return [self.knowledge_entries[entry_id] for entry_id in entry_ids]
        return []
    
    def search_by_severity(self, severity: Severity) -> List[KnowledgeEntry]:
        """Search knowledge entries by severity level"""
        severity_value = severity.value
        if severity_value in self._search_index["by_severity"]:
            entry_ids = self._search_index["by_severity"][severity_value]
            return [self.knowledge_entries[entry_id] for entry_id in entry_ids]
        return []
    
    def search_by_keywords(self, keywords: List[str]) -> List[KnowledgeEntry]:
        """Search knowledge entries by keywords in title and description"""
        matching_entries = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for entry in self.knowledge_entries.values():
            text_to_search = f"{entry.title} {entry.description}".lower()
            
            # Check if any keyword matches
            for keyword in keywords_lower:
                if keyword in text_to_search:
                    matching_entries.append(entry)
                    break
        
        return matching_entries
    
    def get_related_knowledge(self, entry_id: str) -> List[KnowledgeEntry]:
        """Get knowledge entries related to a specific entry"""
        entry = self.get_knowledge_entry(entry_id)
        if not entry:
            return []
        
        related_entries = []
        for related_id in entry.related_entries:
            related_entry = self.get_knowledge_entry(related_id)
            if related_entry:
                related_entries.append(related_entry)
        
        return related_entries
    
    def get_recommendations_for_issue(self, issue_description: str, system_type: Optional[str] = None) -> List[KnowledgeEntry]:
        """Get knowledge recommendations for a specific issue"""
        # Extract keywords from issue description
        keywords = issue_description.lower().split()
        
        # Search by keywords
        keyword_matches = self.search_by_keywords(keywords)
        
        # Filter by system type if provided
        if system_type:
            system_matches = self.search_by_system_type(system_type)
            # Find intersection
            keyword_matches = [entry for entry in keyword_matches if entry in system_matches]
        
        # Sort by relevance (prioritize troubleshooting and critical entries)
        def relevance_score(entry: KnowledgeEntry) -> int:
            score = 0
            if entry.category == KnowledgeCategory.TROUBLESHOOTING:
                score += 10
            if entry.severity in [Severity.CRITICAL, Severity.HIGH]:
                score += 5
            if entry.knowledge_type == KnowledgeType.PROCEDURE:
                score += 3
            return score
        
        keyword_matches.sort(key=relevance_score, reverse=True)
        return keyword_matches[:10]  # Return top 10 matches
    
    def get_best_practices_for_system(self, system_type: str) -> List[KnowledgeEntry]:
        """Get best practices for a specific system type"""
        system_entries = self.search_by_system_type(system_type)
        best_practices = [entry for entry in system_entries 
                         if entry.category == KnowledgeCategory.BEST_PRACTICES]
        
        # Sort by severity (critical first)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        
        best_practices.sort(key=lambda x: severity_order.get(x.severity, 5))
        return best_practices
    
    def get_security_guidelines(self, system_type: Optional[str] = None) -> List[KnowledgeEntry]:
        """Get security guidelines, optionally filtered by system type"""
        security_entries = self.search_by_category(KnowledgeCategory.SECURITY)
        
        if system_type:
            security_entries = [entry for entry in security_entries 
                              if system_type in entry.applicable_systems]
        
        # Sort by severity (critical first)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        
        security_entries.sort(key=lambda x: severity_order.get(x.severity, 5))
        return security_entries
    
    def get_troubleshooting_procedures(self, issue_keywords: List[str]) -> List[KnowledgeEntry]:
        """Get troubleshooting procedures for specific issues"""
        troubleshooting_entries = self.search_by_category(KnowledgeCategory.TROUBLESHOOTING)
        
        if issue_keywords:
            # Filter by keywords
            keywords_lower = [kw.lower() for kw in issue_keywords]
            filtered_entries = []
            
            for entry in troubleshooting_entries:
                text_to_search = f"{entry.title} {entry.description} {' '.join(entry.tags)}".lower()
                for keyword in keywords_lower:
                    if keyword in text_to_search:
                        filtered_entries.append(entry)
                        break
            
            troubleshooting_entries = filtered_entries
        
        return troubleshooting_entries
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        stats = {
            "total_entries": len(self.knowledge_entries),
            "entries_by_category": {},
            "entries_by_severity": {},
            "entries_by_type": {},
            "entries_by_system": {},
            "total_steps": 0,
            "most_common_tags": {}
        }
        
        tag_counts = {}
        
        for entry in self.knowledge_entries.values():
            # Category statistics
            category = entry.category.value
            stats["entries_by_category"][category] = stats["entries_by_category"].get(category, 0) + 1
            
            # Severity statistics
            severity = entry.severity.value
            stats["entries_by_severity"][severity] = stats["entries_by_severity"].get(severity, 0) + 1
            
            # Type statistics
            knowledge_type = entry.knowledge_type.value
            stats["entries_by_type"][knowledge_type] = stats["entries_by_type"].get(knowledge_type, 0) + 1
            
            # System statistics
            for system in entry.applicable_systems:
                stats["entries_by_system"][system] = stats["entries_by_system"].get(system, 0) + 1
            
            # Step count
            stats["total_steps"] += len(entry.steps)
            
            # Tag statistics
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get most common tags (top 10)
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        stats["most_common_tags"] = dict(sorted_tags[:10])
        
        return stats
    
    def export_knowledge_entry(self, entry_id: str, format: str = "json") -> Optional[str]:
        """Export knowledge entry in specified format"""
        entry = self.get_knowledge_entry(entry_id)
        if not entry:
            return None
        
        if format.lower() == "json":
            import json
            return json.dumps({
                "id": entry.id,
                "title": entry.title,
                "category": entry.category.value,
                "knowledge_type": entry.knowledge_type.value,
                "description": entry.description,
                "severity": entry.severity.value,
                "tags": entry.tags,
                "applicable_systems": entry.applicable_systems,
                "steps": [
                    {
                        "step_number": step.step_number,
                        "description": step.description,
                        "command": step.command,
                        "expected_result": step.expected_result,
                        "troubleshooting_notes": step.troubleshooting_notes,
                        "prerequisites": step.prerequisites
                    }
                    for step in entry.steps
                ],
                "related_entries": entry.related_entries,
                "references": entry.references,
                "author": entry.author,
                "version": entry.version
            }, indent=2)
        
        elif format.lower() == "markdown":
            md_content = f"# {entry.title}\n\n"
            md_content += f"**Category:** {entry.category.value}\n"
            md_content += f"**Type:** {entry.knowledge_type.value}\n"
            md_content += f"**Severity:** {entry.severity.value}\n"
            md_content += f"**Systems:** {', '.join(entry.applicable_systems)}\n\n"
            md_content += f"## Description\n{entry.description}\n\n"
            
            if entry.steps:
                md_content += "## Steps\n\n"
                for step in entry.steps:
                    md_content += f"### {step.step_number}. {step.description}\n\n"
                    if step.command:
                        md_content += f"```bash\n{step.command}\n```\n\n"
                    if step.expected_result:
                        md_content += f"**Expected Result:** {step.expected_result}\n\n"
                    if step.troubleshooting_notes:
                        md_content += "**Troubleshooting Notes:**\n"
                        for note in step.troubleshooting_notes:
                            md_content += f"- {note}\n"
                        md_content += "\n"
            
            if entry.references:
                md_content += "## References\n\n"
                for ref in entry.references:
                    md_content += f"- {ref}\n"
            
            return md_content
        
        return None

# Global instance
it_knowledge_base = ITKnowledgeBase()
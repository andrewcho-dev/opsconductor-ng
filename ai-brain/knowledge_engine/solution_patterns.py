"""
OpsConductor Knowledge Engine - Solution Patterns Module

This module identifies, stores, and applies successful automation patterns
based on historical job executions and outcomes.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Types of solution patterns"""
    WORKFLOW_PATTERN = "workflow_pattern"
    COMMAND_SEQUENCE = "command_sequence"
    ERROR_RESOLUTION = "error_resolution"
    OPTIMIZATION = "optimization"
    CONFIGURATION = "configuration"

class PatternConfidence(Enum):
    """Confidence levels for patterns"""
    HIGH = "high"        # 90%+ success rate, 10+ occurrences
    MEDIUM = "medium"    # 70-89% success rate, 5+ occurrences
    LOW = "low"          # 50-69% success rate, 3+ occurrences
    EXPERIMENTAL = "experimental"  # <50% success rate or <3 occurrences

@dataclass
class PatternContext:
    """Context in which a pattern applies"""
    target_types: List[str]
    protocols: List[str]
    system_conditions: Dict[str, Any]
    prerequisites: List[str]
    constraints: List[str]

@dataclass
class PatternStep:
    """Individual step in a solution pattern"""
    step_id: str
    description: str
    command_template: str
    parameters: Dict[str, Any]
    expected_outcomes: List[str]
    error_handling: Dict[str, Any]
    timeout: Optional[int] = None
    retry_logic: Optional[Dict[str, Any]] = None

@dataclass
class PatternMetrics:
    """Metrics for pattern effectiveness"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    success_rate: float
    last_used: datetime
    first_discovered: datetime
    improvement_over_baseline: Optional[float] = None

@dataclass
class SolutionPattern:
    """Complete solution pattern definition"""
    pattern_id: str
    name: str
    description: str
    pattern_type: PatternType
    confidence: PatternConfidence
    context: PatternContext
    steps: List[PatternStep]
    metrics: PatternMetrics
    tags: List[str]
    related_patterns: List[str] = field(default_factory=list)
    variations: List[str] = field(default_factory=list)
    source_jobs: List[str] = field(default_factory=list)  # Job IDs that contributed to this pattern

class SolutionPatternManager:
    """Manages solution patterns and provides pattern matching capabilities"""
    
    def __init__(self):
        self.patterns = self._initialize_base_patterns()
        self._pattern_index = self._build_pattern_index()
        logger.info(f"Initialized solution pattern manager with {len(self.patterns)} patterns")
    
    def _initialize_base_patterns(self) -> Dict[str, SolutionPattern]:
        """Initialize base solution patterns from common automation scenarios"""
        patterns = {}
        
        # Service Restart Pattern
        patterns["service_restart_pattern"] = SolutionPattern(
            pattern_id="service_restart_pattern",
            name="Safe Service Restart Pattern",
            description="Proven pattern for safely restarting services with validation",
            pattern_type=PatternType.WORKFLOW_PATTERN,
            confidence=PatternConfidence.HIGH,
            context=PatternContext(
                target_types=["linux_server", "container"],
                protocols=["ssh"],
                system_conditions={"systemd_available": True},
                prerequisites=["Service exists", "Appropriate permissions"],
                constraints=["Service supports graceful restart"]
            ),
            steps=[
                PatternStep(
                    step_id="pre_check",
                    description="Verify service status before restart",
                    command_template="systemctl is-active {service_name}",
                    parameters={"service_name": "string"},
                    expected_outcomes=["active", "inactive", "failed"],
                    error_handling={"on_failure": "continue", "log_warning": True}
                ),
                PatternStep(
                    step_id="graceful_stop",
                    description="Stop service gracefully",
                    command_template="systemctl stop {service_name}",
                    parameters={"service_name": "string"},
                    expected_outcomes=["Service stopped successfully"],
                    error_handling={"on_failure": "retry", "max_retries": 2},
                    timeout=60
                ),
                PatternStep(
                    step_id="verify_stop",
                    description="Verify service has stopped",
                    command_template="systemctl is-active {service_name}",
                    parameters={"service_name": "string"},
                    expected_outcomes=["inactive"],
                    error_handling={"on_failure": "force_kill"},
                    timeout=30
                ),
                PatternStep(
                    step_id="start_service",
                    description="Start service",
                    command_template="systemctl start {service_name}",
                    parameters={"service_name": "string"},
                    expected_outcomes=["Service started successfully"],
                    error_handling={"on_failure": "fail", "rollback": True},
                    timeout=60,
                    retry_logic={"max_retries": 3, "backoff": "exponential"}
                ),
                PatternStep(
                    step_id="post_validation",
                    description="Validate service is running correctly",
                    command_template="systemctl is-active {service_name} && systemctl status {service_name}",
                    parameters={"service_name": "string"},
                    expected_outcomes=["active", "Service status shows healthy"],
                    error_handling={"on_failure": "alert", "escalate": True},
                    timeout=30
                )
            ],
            metrics=PatternMetrics(
                total_executions=150,
                successful_executions=142,
                failed_executions=8,
                average_execution_time=45.2,
                success_rate=94.7,
                last_used=datetime.now() - timedelta(hours=2),
                first_discovered=datetime.now() - timedelta(days=30),
                improvement_over_baseline=15.3
            ),
            tags=["service", "restart", "systemd", "validation"],
            source_jobs=["job_001", "job_045", "job_089", "job_123"]
        )
        
        # Log Analysis Pattern
        patterns["log_analysis_pattern"] = SolutionPattern(
            pattern_id="log_analysis_pattern",
            name="Comprehensive Log Analysis Pattern",
            description="Systematic approach to analyzing system and application logs",
            pattern_type=PatternType.WORKFLOW_PATTERN,
            confidence=PatternConfidence.HIGH,
            context=PatternContext(
                target_types=["linux_server", "container"],
                protocols=["ssh"],
                system_conditions={"log_files_accessible": True},
                prerequisites=["Read access to log files"],
                constraints=["Sufficient disk space for log processing"]
            ),
            steps=[
                PatternStep(
                    step_id="identify_logs",
                    description="Identify relevant log files",
                    command_template="find /var/log -name '*{service_name}*' -type f -mtime -{days}",
                    parameters={"service_name": "string", "days": "integer"},
                    expected_outcomes=["List of relevant log files"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="check_errors",
                    description="Search for error patterns",
                    command_template="grep -i 'error\\|fail\\|exception\\|critical' /var/log/{log_file} | tail -50",
                    parameters={"log_file": "string"},
                    expected_outcomes=["Error entries found or no errors"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="analyze_patterns",
                    description="Analyze log patterns and frequency",
                    command_template="awk '{print $1, $2, $3}' /var/log/{log_file} | sort | uniq -c | sort -nr | head -20",
                    parameters={"log_file": "string"},
                    expected_outcomes=["Pattern frequency analysis"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="recent_activity",
                    description="Check recent activity",
                    command_template="tail -100 /var/log/{log_file}",
                    parameters={"log_file": "string"},
                    expected_outcomes=["Recent log entries"],
                    error_handling={"on_failure": "continue"}
                )
            ],
            metrics=PatternMetrics(
                total_executions=89,
                successful_executions=85,
                failed_executions=4,
                average_execution_time=23.7,
                success_rate=95.5,
                last_used=datetime.now() - timedelta(hours=6),
                first_discovered=datetime.now() - timedelta(days=45),
                improvement_over_baseline=22.1
            ),
            tags=["logs", "analysis", "troubleshooting", "monitoring"],
            source_jobs=["job_012", "job_034", "job_067", "job_098"]
        )
        
        # Database Connection Recovery Pattern
        patterns["db_connection_recovery"] = SolutionPattern(
            pattern_id="db_connection_recovery",
            name="Database Connection Recovery Pattern",
            description="Proven steps to recover from database connection issues",
            pattern_type=PatternType.ERROR_RESOLUTION,
            confidence=PatternConfidence.MEDIUM,
            context=PatternContext(
                target_types=["database", "linux_server"],
                protocols=["ssh", "database"],
                system_conditions={"database_service_exists": True},
                prerequisites=["Database credentials available", "Network connectivity"],
                constraints=["Database service manageable"]
            ),
            steps=[
                PatternStep(
                    step_id="test_connection",
                    description="Test database connectivity",
                    command_template="pg_isready -h {db_host} -p {db_port} -U {db_user}",
                    parameters={"db_host": "string", "db_port": "integer", "db_user": "string"},
                    expected_outcomes=["Connection successful", "Connection failed"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="check_service_status",
                    description="Check database service status",
                    command_template="systemctl status {db_service}",
                    parameters={"db_service": "string"},
                    expected_outcomes=["Service active", "Service inactive", "Service failed"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="check_port_listening",
                    description="Verify database port is listening",
                    command_template="netstat -tlnp | grep :{db_port}",
                    parameters={"db_port": "integer"},
                    expected_outcomes=["Port is listening", "Port not listening"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="restart_if_needed",
                    description="Restart database service if not running",
                    command_template="systemctl restart {db_service}",
                    parameters={"db_service": "string"},
                    expected_outcomes=["Service restarted successfully"],
                    error_handling={"on_failure": "escalate"},
                    timeout=120
                ),
                PatternStep(
                    step_id="verify_recovery",
                    description="Verify database connection is restored",
                    command_template="pg_isready -h {db_host} -p {db_port} -U {db_user}",
                    parameters={"db_host": "string", "db_port": "integer", "db_user": "string"},
                    expected_outcomes=["Connection successful"],
                    error_handling={"on_failure": "fail"},
                    timeout=60
                )
            ],
            metrics=PatternMetrics(
                total_executions=34,
                successful_executions=28,
                failed_executions=6,
                average_execution_time=78.4,
                success_rate=82.4,
                last_used=datetime.now() - timedelta(days=3),
                first_discovered=datetime.now() - timedelta(days=20),
                improvement_over_baseline=35.2
            ),
            tags=["database", "connection", "recovery", "postgresql"],
            source_jobs=["job_156", "job_178", "job_203"]
        )
        
        # Disk Space Cleanup Pattern
        patterns["disk_cleanup_pattern"] = SolutionPattern(
            pattern_id="disk_cleanup_pattern",
            name="Safe Disk Space Cleanup Pattern",
            description="Systematic approach to freeing disk space safely",
            pattern_type=PatternType.OPTIMIZATION,
            confidence=PatternConfidence.HIGH,
            context=PatternContext(
                target_types=["linux_server", "container"],
                protocols=["ssh"],
                system_conditions={"disk_space_low": True},
                prerequisites=["Root or sudo access"],
                constraints=["Critical files must be preserved"]
            ),
            steps=[
                PatternStep(
                    step_id="analyze_usage",
                    description="Analyze disk usage by directory",
                    command_template="du -sh /* 2>/dev/null | sort -hr | head -10",
                    parameters={},
                    expected_outcomes=["Disk usage breakdown by directory"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="clean_temp_files",
                    description="Clean temporary files",
                    command_template="find /tmp -type f -atime +7 -delete && find /var/tmp -type f -atime +7 -delete",
                    parameters={},
                    expected_outcomes=["Temporary files cleaned"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="clean_logs",
                    description="Rotate and compress old log files",
                    command_template="logrotate -f /etc/logrotate.conf",
                    parameters={},
                    expected_outcomes=["Log files rotated"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="clean_package_cache",
                    description="Clean package manager cache",
                    command_template="apt-get clean && apt-get autoremove -y",
                    parameters={},
                    expected_outcomes=["Package cache cleaned"],
                    error_handling={"on_failure": "continue"}
                ),
                PatternStep(
                    step_id="verify_space_freed",
                    description="Verify disk space has been freed",
                    command_template="df -h | grep -E '^/dev/'",
                    parameters={},
                    expected_outcomes=["Disk space usage updated"],
                    error_handling={"on_failure": "continue"}
                )
            ],
            metrics=PatternMetrics(
                total_executions=67,
                successful_executions=64,
                failed_executions=3,
                average_execution_time=156.3,
                success_rate=95.5,
                last_used=datetime.now() - timedelta(hours=12),
                first_discovered=datetime.now() - timedelta(days=60),
                improvement_over_baseline=28.7
            ),
            tags=["disk", "cleanup", "optimization", "maintenance"],
            source_jobs=["job_078", "job_134", "job_189", "job_234"]
        )
        
        return patterns
    
    def _build_pattern_index(self) -> Dict[str, Any]:
        """Build search index for patterns"""
        index = {
            "by_type": {},
            "by_confidence": {},
            "by_target_type": {},
            "by_protocol": {},
            "by_tag": {}
        }
        
        for pattern in self.patterns.values():
            # Index by type
            pattern_type = pattern.pattern_type.value
            if pattern_type not in index["by_type"]:
                index["by_type"][pattern_type] = []
            index["by_type"][pattern_type].append(pattern.pattern_id)
            
            # Index by confidence
            confidence = pattern.confidence.value
            if confidence not in index["by_confidence"]:
                index["by_confidence"][confidence] = []
            index["by_confidence"][confidence].append(pattern.pattern_id)
            
            # Index by target types
            for target_type in pattern.context.target_types:
                if target_type not in index["by_target_type"]:
                    index["by_target_type"][target_type] = []
                index["by_target_type"][target_type].append(pattern.pattern_id)
            
            # Index by protocols
            for protocol in pattern.context.protocols:
                if protocol not in index["by_protocol"]:
                    index["by_protocol"][protocol] = []
                index["by_protocol"][protocol].append(pattern.pattern_id)
            
            # Index by tags
            for tag in pattern.tags:
                if tag not in index["by_tag"]:
                    index["by_tag"][tag] = []
                index["by_tag"][tag].append(pattern.pattern_id)
        
        return index
    
    def get_pattern(self, pattern_id: str) -> Optional[SolutionPattern]:
        """Get solution pattern by ID"""
        return self.patterns.get(pattern_id)
    
    def find_patterns_by_context(self, 
                                target_type: str, 
                                protocol: str, 
                                tags: Optional[List[str]] = None) -> List[SolutionPattern]:
        """Find patterns matching specific context"""
        matching_patterns = set()
        
        # Find patterns by target type
        if target_type in self._pattern_index["by_target_type"]:
            matching_patterns.update(self._pattern_index["by_target_type"][target_type])
        
        # Filter by protocol
        if protocol in self._pattern_index["by_protocol"]:
            protocol_patterns = set(self._pattern_index["by_protocol"][protocol])
            matching_patterns = matching_patterns.intersection(protocol_patterns)
        
        # Filter by tags if provided
        if tags:
            tag_patterns = set()
            for tag in tags:
                if tag in self._pattern_index["by_tag"]:
                    tag_patterns.update(self._pattern_index["by_tag"][tag])
            if tag_patterns:
                matching_patterns = matching_patterns.intersection(tag_patterns)
        
        # Convert to pattern objects and sort by confidence and success rate
        patterns = [self.patterns[pid] for pid in matching_patterns]
        patterns.sort(key=lambda p: (
            {"high": 3, "medium": 2, "low": 1, "experimental": 0}[p.confidence.value],
            p.metrics.success_rate
        ), reverse=True)
        
        return patterns
    
    def find_patterns_by_keywords(self, keywords: List[str]) -> List[SolutionPattern]:
        """Find patterns matching keywords in name, description, or tags"""
        matching_patterns = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for pattern in self.patterns.values():
            text_to_search = f"{pattern.name} {pattern.description} {' '.join(pattern.tags)}".lower()
            
            # Check if any keyword matches
            for keyword in keywords_lower:
                if keyword in text_to_search:
                    matching_patterns.append(pattern)
                    break
        
        # Sort by relevance (confidence and success rate)
        matching_patterns.sort(key=lambda p: (
            {"high": 3, "medium": 2, "low": 1, "experimental": 0}[p.confidence.value],
            p.metrics.success_rate
        ), reverse=True)
        
        return matching_patterns
    
    def get_high_confidence_patterns(self) -> List[SolutionPattern]:
        """Get patterns with high confidence levels"""
        high_confidence_ids = self._pattern_index["by_confidence"].get("high", [])
        patterns = [self.patterns[pid] for pid in high_confidence_ids]
        
        # Sort by success rate
        patterns.sort(key=lambda p: p.metrics.success_rate, reverse=True)
        return patterns
    
    def get_patterns_for_error_resolution(self) -> List[SolutionPattern]:
        """Get patterns specifically for error resolution"""
        error_resolution_ids = self._pattern_index["by_type"].get("error_resolution", [])
        patterns = [self.patterns[pid] for pid in error_resolution_ids]
        
        # Sort by success rate and recency
        patterns.sort(key=lambda p: (
            p.metrics.success_rate,
            (datetime.now() - p.metrics.last_used).days * -1  # More recent = higher score
        ), reverse=True)
        
        return patterns
    
    def recommend_patterns_for_job(self, 
                                  job_description: str,
                                  target_type: str,
                                  protocol: str) -> List[Tuple[SolutionPattern, float]]:
        """Recommend patterns for a specific job with confidence scores"""
        # Extract keywords from job description
        keywords = job_description.lower().split()
        
        # Find patterns by context
        context_patterns = self.find_patterns_by_context(target_type, protocol)
        
        # Find patterns by keywords
        keyword_patterns = self.find_patterns_by_keywords(keywords)
        
        # Combine and score patterns
        pattern_scores = {}
        
        # Score context matches
        for pattern in context_patterns:
            score = 0.5  # Base score for context match
            
            # Bonus for confidence level
            confidence_bonus = {
                PatternConfidence.HIGH: 0.3,
                PatternConfidence.MEDIUM: 0.2,
                PatternConfidence.LOW: 0.1,
                PatternConfidence.EXPERIMENTAL: 0.0
            }
            score += confidence_bonus[pattern.confidence]
            
            # Bonus for success rate
            score += (pattern.metrics.success_rate / 100) * 0.2
            
            pattern_scores[pattern.pattern_id] = score
        
        # Additional score for keyword matches
        for pattern in keyword_patterns:
            if pattern.pattern_id in pattern_scores:
                pattern_scores[pattern.pattern_id] += 0.3  # Bonus for keyword match
            else:
                pattern_scores[pattern.pattern_id] = 0.3  # Base score for keyword match only
        
        # Convert to list of tuples and sort by score
        recommendations = [
            (self.patterns[pid], score) 
            for pid, score in pattern_scores.items()
        ]
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def learn_from_job_execution(self, 
                                job_id: str,
                                job_description: str,
                                target_type: str,
                                protocol: str,
                                steps_executed: List[Dict[str, Any]],
                                success: bool,
                                execution_time: float) -> Optional[str]:
        """Learn from job execution and potentially create or update patterns"""
        
        # Check if this execution matches an existing pattern
        matching_patterns = self.find_patterns_by_context(target_type, protocol)
        
        pattern_updated = False
        for pattern in matching_patterns:
            if self._execution_matches_pattern(steps_executed, pattern):
                # Update pattern metrics
                pattern.metrics.total_executions += 1
                if success:
                    pattern.metrics.successful_executions += 1
                else:
                    pattern.metrics.failed_executions += 1
                
                # Update success rate
                pattern.metrics.success_rate = (
                    pattern.metrics.successful_executions / pattern.metrics.total_executions
                ) * 100
                
                # Update average execution time
                total_time = (pattern.metrics.average_execution_time * 
                            (pattern.metrics.total_executions - 1) + execution_time)
                pattern.metrics.average_execution_time = total_time / pattern.metrics.total_executions
                
                pattern.metrics.last_used = datetime.now()
                pattern.source_jobs.append(job_id)
                
                # Update confidence based on new metrics
                pattern.confidence = self._calculate_confidence(pattern.metrics)
                
                pattern_updated = True
                logger.info(f"Updated pattern {pattern.pattern_id} with job {job_id}")
                break
        
        # If no existing pattern matched and the job was successful, consider creating a new pattern
        if not pattern_updated and success and len(steps_executed) >= 3:
            new_pattern_id = self._create_pattern_from_execution(
                job_id, job_description, target_type, protocol, 
                steps_executed, execution_time
            )
            if new_pattern_id:
                logger.info(f"Created new pattern {new_pattern_id} from job {job_id}")
                return new_pattern_id
        
        return None
    
    def _execution_matches_pattern(self, 
                                  steps_executed: List[Dict[str, Any]], 
                                  pattern: SolutionPattern) -> bool:
        """Check if job execution matches a pattern"""
        if len(steps_executed) != len(pattern.steps):
            return False
        
        # Simple matching based on command similarity
        for i, (executed_step, pattern_step) in enumerate(zip(steps_executed, pattern.steps)):
            executed_command = executed_step.get("command", "").lower()
            pattern_command = pattern_step.command_template.lower()
            
            # Remove parameter placeholders for comparison
            import re
            pattern_command_clean = re.sub(r'\{[^}]+\}', '', pattern_command)
            
            # Check if core command structure matches
            if not any(word in executed_command for word in pattern_command_clean.split() if len(word) > 2):
                return False
        
        return True
    
    def _create_pattern_from_execution(self,
                                     job_id: str,
                                     job_description: str,
                                     target_type: str,
                                     protocol: str,
                                     steps_executed: List[Dict[str, Any]],
                                     execution_time: float) -> Optional[str]:
        """Create a new pattern from successful job execution"""
        
        # Generate pattern ID
        import hashlib
        pattern_content = f"{job_description}_{target_type}_{protocol}_{len(steps_executed)}"
        pattern_id = f"learned_pattern_{hashlib.md5(pattern_content.encode()).hexdigest()[:8]}"
        
        # Check if pattern already exists
        if pattern_id in self.patterns:
            return None
        
        # Create pattern steps
        pattern_steps = []
        for i, step in enumerate(steps_executed):
            pattern_step = PatternStep(
                step_id=f"step_{i+1}",
                description=step.get("description", f"Step {i+1}"),
                command_template=step.get("command", ""),
                parameters=step.get("parameters", {}),
                expected_outcomes=step.get("expected_outcomes", ["Success"]),
                error_handling=step.get("error_handling", {"on_failure": "fail"}),
                timeout=step.get("timeout")
            )
            pattern_steps.append(pattern_step)
        
        # Create new pattern
        new_pattern = SolutionPattern(
            pattern_id=pattern_id,
            name=f"Learned Pattern: {job_description[:50]}",
            description=f"Pattern learned from successful execution of job {job_id}",
            pattern_type=PatternType.WORKFLOW_PATTERN,
            confidence=PatternConfidence.EXPERIMENTAL,
            context=PatternContext(
                target_types=[target_type],
                protocols=[protocol],
                system_conditions={},
                prerequisites=[],
                constraints=[]
            ),
            steps=pattern_steps,
            metrics=PatternMetrics(
                total_executions=1,
                successful_executions=1,
                failed_executions=0,
                average_execution_time=execution_time,
                success_rate=100.0,
                last_used=datetime.now(),
                first_discovered=datetime.now()
            ),
            tags=self._extract_tags_from_description(job_description),
            source_jobs=[job_id]
        )
        
        # Add to patterns and rebuild index
        self.patterns[pattern_id] = new_pattern
        self._pattern_index = self._build_pattern_index()
        
        return pattern_id
    
    def _calculate_confidence(self, metrics: PatternMetrics) -> PatternConfidence:
        """Calculate confidence level based on pattern metrics"""
        if metrics.total_executions >= 10 and metrics.success_rate >= 90:
            return PatternConfidence.HIGH
        elif metrics.total_executions >= 5 and metrics.success_rate >= 70:
            return PatternConfidence.MEDIUM
        elif metrics.total_executions >= 3 and metrics.success_rate >= 50:
            return PatternConfidence.LOW
        else:
            return PatternConfidence.EXPERIMENTAL
    
    def _extract_tags_from_description(self, description: str) -> List[str]:
        """Extract relevant tags from job description"""
        common_tags = {
            "service": ["service", "daemon", "process"],
            "restart": ["restart", "reload", "stop", "start"],
            "database": ["database", "db", "sql", "postgres", "mysql"],
            "web": ["web", "http", "nginx", "apache"],
            "backup": ["backup", "archive", "dump"],
            "monitoring": ["monitor", "check", "status", "health"],
            "security": ["security", "firewall", "ssl", "certificate"],
            "network": ["network", "connection", "port", "tcp", "udp"],
            "file": ["file", "directory", "copy", "move", "delete"],
            "user": ["user", "account", "permission", "access"]
        }
        
        description_lower = description.lower()
        extracted_tags = []
        
        for tag, keywords in common_tags.items():
            if any(keyword in description_lower for keyword in keywords):
                extracted_tags.append(tag)
        
        return extracted_tags
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about solution patterns"""
        stats = {
            "total_patterns": len(self.patterns),
            "patterns_by_type": {},
            "patterns_by_confidence": {},
            "average_success_rate": 0,
            "total_executions": 0,
            "most_successful_patterns": [],
            "recently_used_patterns": []
        }
        
        total_success_rate = 0
        total_executions = 0
        
        for pattern in self.patterns.values():
            # Type statistics
            pattern_type = pattern.pattern_type.value
            stats["patterns_by_type"][pattern_type] = stats["patterns_by_type"].get(pattern_type, 0) + 1
            
            # Confidence statistics
            confidence = pattern.confidence.value
            stats["patterns_by_confidence"][confidence] = stats["patterns_by_confidence"].get(confidence, 0) + 1
            
            # Success rate and execution statistics
            total_success_rate += pattern.metrics.success_rate
            total_executions += pattern.metrics.total_executions
        
        if len(self.patterns) > 0:
            stats["average_success_rate"] = total_success_rate / len(self.patterns)
        stats["total_executions"] = total_executions
        
        # Most successful patterns (by success rate and execution count)
        successful_patterns = sorted(
            self.patterns.values(),
            key=lambda p: (p.metrics.success_rate, p.metrics.total_executions),
            reverse=True
        )[:5]
        
        stats["most_successful_patterns"] = [
            {
                "pattern_id": p.pattern_id,
                "name": p.name,
                "success_rate": p.metrics.success_rate,
                "total_executions": p.metrics.total_executions
            }
            for p in successful_patterns
        ]
        
        # Recently used patterns
        recent_patterns = sorted(
            self.patterns.values(),
            key=lambda p: p.metrics.last_used,
            reverse=True
        )[:5]
        
        stats["recently_used_patterns"] = [
            {
                "pattern_id": p.pattern_id,
                "name": p.name,
                "last_used": p.metrics.last_used.isoformat(),
                "success_rate": p.metrics.success_rate
            }
            for p in recent_patterns
        ]
        
        return stats
    
    def export_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Export pattern as JSON for sharing or backup"""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return None
        
        return {
            "pattern_id": pattern.pattern_id,
            "name": pattern.name,
            "description": pattern.description,
            "pattern_type": pattern.pattern_type.value,
            "confidence": pattern.confidence.value,
            "context": {
                "target_types": pattern.context.target_types,
                "protocols": pattern.context.protocols,
                "system_conditions": pattern.context.system_conditions,
                "prerequisites": pattern.context.prerequisites,
                "constraints": pattern.context.constraints
            },
            "steps": [
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "command_template": step.command_template,
                    "parameters": step.parameters,
                    "expected_outcomes": step.expected_outcomes,
                    "error_handling": step.error_handling,
                    "timeout": step.timeout,
                    "retry_logic": step.retry_logic
                }
                for step in pattern.steps
            ],
            "metrics": {
                "total_executions": pattern.metrics.total_executions,
                "successful_executions": pattern.metrics.successful_executions,
                "failed_executions": pattern.metrics.failed_executions,
                "average_execution_time": pattern.metrics.average_execution_time,
                "success_rate": pattern.metrics.success_rate,
                "last_used": pattern.metrics.last_used.isoformat(),
                "first_discovered": pattern.metrics.first_discovered.isoformat(),
                "improvement_over_baseline": pattern.metrics.improvement_over_baseline
            },
            "tags": pattern.tags,
            "related_patterns": pattern.related_patterns,
            "source_jobs": pattern.source_jobs
        }

# Global instance
solution_patterns = SolutionPatternManager()
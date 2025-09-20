"""
OpsConductor System Model - Workflow Templates Module

This module provides pre-built workflow templates for common automation tasks,
with intelligent parameterization and adaptation capabilities.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class WorkflowCategory(Enum):
    """Categories of workflow templates"""
    SYSTEM_ADMINISTRATION = "system_administration"
    SERVICE_MANAGEMENT = "service_management"
    MONITORING = "monitoring"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    BACKUP_RECOVERY = "backup_recovery"
    NETWORK_MANAGEMENT = "network_management"
    DATABASE_OPERATIONS = "database_operations"
    FILE_MANAGEMENT = "file_management"
    USER_MANAGEMENT = "user_management"

class StepType(Enum):
    """Types of workflow steps"""
    COMMAND = "command"
    SCRIPT = "script"
    FILE_TRANSFER = "file_transfer"
    VALIDATION = "validation"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    PARALLEL = "parallel"
    WAIT = "wait"
    NOTIFICATION = "notification"

class ParameterType(Enum):
    """Types of workflow parameters"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    FILE_PATH = "file_path"
    TARGET_SPEC = "target_spec"
    CREDENTIAL_SPEC = "credential_spec"

@dataclass
class WorkflowParameter:
    """Workflow parameter definition"""
    name: str
    parameter_type: ParameterType
    description: str
    required: bool = True
    default_value: Any = None
    validation_rules: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

@dataclass
class WorkflowStep:
    """Individual workflow step"""
    id: str
    name: str
    step_type: StepType
    description: str
    command: Optional[str] = None
    script: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    retry_count: int = 0
    depends_on: List[str] = field(default_factory=list)

@dataclass
class WorkflowTemplate:
    """Complete workflow template definition"""
    id: str
    name: str
    description: str
    category: WorkflowCategory
    version: str
    author: str
    parameters: List[WorkflowParameter]
    steps: List[WorkflowStep]
    target_types: List[str]
    protocols: List[str]
    estimated_duration: Optional[int] = None  # seconds
    risk_level: str = "low"  # low, medium, high
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

class WorkflowTemplateManager:
    """Manages workflow templates and provides intelligent template selection"""
    
    def __init__(self):
        self.templates = self._initialize_workflow_templates()
        logger.info(f"Initialized {len(self.templates)} workflow templates")
    
    def _initialize_workflow_templates(self) -> Dict[str, WorkflowTemplate]:
        """Initialize comprehensive workflow template library"""
        templates = {}
        
        # Service Restart Template
        templates["service_restart"] = WorkflowTemplate(
            id="service_restart",
            name="Service Restart",
            description="Safely restart a system service with validation",
            category=WorkflowCategory.SERVICE_MANAGEMENT,
            version="1.0",
            author="OpsConductor AI",
            parameters=[
                WorkflowParameter(
                    name="service_name",
                    parameter_type=ParameterType.STRING,
                    description="Name of the service to restart",
                    examples=["nginx", "apache2", "mysql", "postgresql"]
                ),
                WorkflowParameter(
                    name="validate_before",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Validate service status before restart",
                    default_value=True
                ),
                WorkflowParameter(
                    name="validate_after",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Validate service status after restart",
                    default_value=True
                ),
                WorkflowParameter(
                    name="wait_time",
                    parameter_type=ParameterType.INTEGER,
                    description="Time to wait after restart (seconds)",
                    default_value=10,
                    validation_rules=["min:1", "max:300"]
                )
            ],
            steps=[
                WorkflowStep(
                    id="pre_validation",
                    name="Pre-restart Validation",
                    step_type=StepType.VALIDATION,
                    description="Check service status before restart",
                    command="systemctl is-active {{service_name}}",
                    conditions=["{{validate_before}} == true"],
                    error_handling={"on_failure": "continue", "log_level": "warning"}
                ),
                WorkflowStep(
                    id="stop_service",
                    name="Stop Service",
                    step_type=StepType.COMMAND,
                    description="Stop the service gracefully",
                    command="systemctl stop {{service_name}}",
                    timeout=60,
                    retry_count=1,
                    depends_on=["pre_validation"]
                ),
                WorkflowStep(
                    id="start_service",
                    name="Start Service",
                    step_type=StepType.COMMAND,
                    description="Start the service",
                    command="systemctl start {{service_name}}",
                    timeout=60,
                    retry_count=2,
                    depends_on=["stop_service"]
                ),
                WorkflowStep(
                    id="wait_stabilization",
                    name="Wait for Stabilization",
                    step_type=StepType.WAIT,
                    description="Wait for service to stabilize",
                    parameters={"duration": "{{wait_time}}"},
                    depends_on=["start_service"]
                ),
                WorkflowStep(
                    id="post_validation",
                    name="Post-restart Validation",
                    step_type=StepType.VALIDATION,
                    description="Verify service is running correctly",
                    command="systemctl is-active {{service_name}} && systemctl status {{service_name}}",
                    conditions=["{{validate_after}} == true"],
                    error_handling={"on_failure": "fail", "log_level": "error"},
                    depends_on=["wait_stabilization"]
                )
            ],
            target_types=["linux_server", "container"],
            protocols=["ssh"],
            estimated_duration=120,
            risk_level="medium",
            prerequisites=[
                "systemctl command available",
                "Appropriate permissions to manage services",
                "Service exists on target system"
            ],
            tags=["service", "restart", "systemd", "linux"]
        )
        
        # System Health Check Template
        templates["system_health_check"] = WorkflowTemplate(
            id="system_health_check",
            name="System Health Check",
            description="Comprehensive system health and performance check",
            category=WorkflowCategory.MONITORING,
            version="1.0",
            author="OpsConductor AI",
            parameters=[
                WorkflowParameter(
                    name="include_disk_usage",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Include disk usage analysis",
                    default_value=True
                ),
                WorkflowParameter(
                    name="include_memory_usage",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Include memory usage analysis",
                    default_value=True
                ),
                WorkflowParameter(
                    name="include_process_list",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Include top processes",
                    default_value=False
                ),
                WorkflowParameter(
                    name="disk_threshold",
                    parameter_type=ParameterType.INTEGER,
                    description="Disk usage warning threshold (%)",
                    default_value=80,
                    validation_rules=["min:1", "max:100"]
                )
            ],
            steps=[
                WorkflowStep(
                    id="system_uptime",
                    name="Check System Uptime",
                    step_type=StepType.COMMAND,
                    description="Get system uptime and load average",
                    command="uptime"
                ),
                WorkflowStep(
                    id="disk_usage",
                    name="Check Disk Usage",
                    step_type=StepType.COMMAND,
                    description="Check disk space usage",
                    command="df -h",
                    conditions=["{{include_disk_usage}} == true"]
                ),
                WorkflowStep(
                    id="memory_usage",
                    name="Check Memory Usage",
                    step_type=StepType.COMMAND,
                    description="Check memory and swap usage",
                    command="free -h",
                    conditions=["{{include_memory_usage}} == true"]
                ),
                WorkflowStep(
                    id="process_list",
                    name="Top Processes",
                    step_type=StepType.COMMAND,
                    description="List top CPU and memory consuming processes",
                    command="ps aux --sort=-%cpu | head -10",
                    conditions=["{{include_process_list}} == true"]
                ),
                WorkflowStep(
                    id="network_status",
                    name="Network Interface Status",
                    step_type=StepType.COMMAND,
                    description="Check network interface status",
                    command="ip addr show"
                ),
                WorkflowStep(
                    id="service_status",
                    name="Critical Services Status",
                    step_type=StepType.COMMAND,
                    description="Check status of critical services",
                    command="systemctl list-units --failed"
                )
            ],
            target_types=["linux_server", "container"],
            protocols=["ssh"],
            estimated_duration=60,
            risk_level="low",
            prerequisites=[
                "Standard Linux utilities available",
                "Read access to system information"
            ],
            tags=["monitoring", "health", "system", "diagnostics"]
        )
        
        # File Backup Template
        templates["file_backup"] = WorkflowTemplate(
            id="file_backup",
            name="File Backup",
            description="Create compressed backup of files or directories",
            category=WorkflowCategory.BACKUP_RECOVERY,
            version="1.0",
            author="OpsConductor AI",
            parameters=[
                WorkflowParameter(
                    name="source_path",
                    parameter_type=ParameterType.FILE_PATH,
                    description="Path to backup (file or directory)",
                    examples=["/etc/nginx", "/var/www/html", "/home/user/documents"]
                ),
                WorkflowParameter(
                    name="backup_destination",
                    parameter_type=ParameterType.FILE_PATH,
                    description="Backup destination directory",
                    examples=["/backup", "/tmp/backups", "/mnt/backup"]
                ),
                WorkflowParameter(
                    name="compression_type",
                    parameter_type=ParameterType.STRING,
                    description="Compression type",
                    default_value="gzip",
                    validation_rules=["in:gzip,bzip2,xz"]
                ),
                WorkflowParameter(
                    name="include_timestamp",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Include timestamp in backup filename",
                    default_value=True
                ),
                WorkflowParameter(
                    name="verify_backup",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Verify backup integrity after creation",
                    default_value=True
                )
            ],
            steps=[
                WorkflowStep(
                    id="validate_source",
                    name="Validate Source Path",
                    step_type=StepType.VALIDATION,
                    description="Ensure source path exists and is accessible",
                    command="test -e '{{source_path}}' && test -r '{{source_path}}'",
                    error_handling={"on_failure": "fail", "message": "Source path does not exist or is not readable"}
                ),
                WorkflowStep(
                    id="create_backup_dir",
                    name="Create Backup Directory",
                    step_type=StepType.COMMAND,
                    description="Ensure backup destination directory exists",
                    command="mkdir -p '{{backup_destination}}'",
                    depends_on=["validate_source"]
                ),
                WorkflowStep(
                    id="create_backup",
                    name="Create Compressed Backup",
                    step_type=StepType.COMMAND,
                    description="Create compressed archive of source",
                    command="tar -czf '{{backup_destination}}/backup_$(date +%Y%m%d_%H%M%S).tar.gz' -C '$(dirname {{source_path}})' '$(basename {{source_path}})'",
                    timeout=3600,  # 1 hour for large backups
                    depends_on=["create_backup_dir"]
                ),
                WorkflowStep(
                    id="verify_backup",
                    name="Verify Backup Integrity",
                    step_type=StepType.VALIDATION,
                    description="Test backup archive integrity",
                    command="tar -tzf '{{backup_destination}}/backup_*.tar.gz' > /dev/null",
                    conditions=["{{verify_backup}} == true"],
                    depends_on=["create_backup"]
                ),
                WorkflowStep(
                    id="backup_summary",
                    name="Backup Summary",
                    step_type=StepType.COMMAND,
                    description="Display backup information",
                    command="ls -lh '{{backup_destination}}/backup_*.tar.gz' | tail -1",
                    depends_on=["verify_backup"]
                )
            ],
            target_types=["linux_server", "container"],
            protocols=["ssh"],
            estimated_duration=1800,  # 30 minutes
            risk_level="low",
            prerequisites=[
                "tar command available",
                "Write access to backup destination",
                "Sufficient disk space for backup"
            ],
            tags=["backup", "archive", "files", "compression"]
        )
        
        # User Account Management Template
        templates["user_management"] = WorkflowTemplate(
            id="user_management",
            name="User Account Management",
            description="Create, modify, or manage user accounts",
            category=WorkflowCategory.USER_MANAGEMENT,
            version="1.0",
            author="OpsConductor AI",
            parameters=[
                WorkflowParameter(
                    name="action",
                    parameter_type=ParameterType.STRING,
                    description="Action to perform",
                    validation_rules=["in:create,delete,modify,lock,unlock"],
                    examples=["create", "delete", "modify", "lock", "unlock"]
                ),
                WorkflowParameter(
                    name="username",
                    parameter_type=ParameterType.STRING,
                    description="Username to manage",
                    validation_rules=["regex:^[a-z][a-z0-9_-]*$"]
                ),
                WorkflowParameter(
                    name="home_directory",
                    parameter_type=ParameterType.FILE_PATH,
                    description="User home directory",
                    required=False,
                    default_value="/home/{{username}}"
                ),
                WorkflowParameter(
                    name="shell",
                    parameter_type=ParameterType.STRING,
                    description="User shell",
                    required=False,
                    default_value="/bin/bash"
                ),
                WorkflowParameter(
                    name="groups",
                    parameter_type=ParameterType.LIST,
                    description="Additional groups for user",
                    required=False,
                    default_value=[]
                )
            ],
            steps=[
                WorkflowStep(
                    id="check_user_exists",
                    name="Check if User Exists",
                    step_type=StepType.VALIDATION,
                    description="Check current user status",
                    command="id {{username}}",
                    error_handling={"on_failure": "continue"}
                ),
                WorkflowStep(
                    id="create_user",
                    name="Create User Account",
                    step_type=StepType.COMMAND,
                    description="Create new user account",
                    command="useradd -m -d '{{home_directory}}' -s '{{shell}}' {{username}}",
                    conditions=["{{action}} == 'create'"],
                    depends_on=["check_user_exists"]
                ),
                WorkflowStep(
                    id="delete_user",
                    name="Delete User Account",
                    step_type=StepType.COMMAND,
                    description="Delete user account and home directory",
                    command="userdel -r {{username}}",
                    conditions=["{{action}} == 'delete'"],
                    depends_on=["check_user_exists"]
                ),
                WorkflowStep(
                    id="lock_user",
                    name="Lock User Account",
                    step_type=StepType.COMMAND,
                    description="Lock user account",
                    command="usermod -L {{username}}",
                    conditions=["{{action}} == 'lock'"],
                    depends_on=["check_user_exists"]
                ),
                WorkflowStep(
                    id="unlock_user",
                    name="Unlock User Account",
                    step_type=StepType.COMMAND,
                    description="Unlock user account",
                    command="usermod -U {{username}}",
                    conditions=["{{action}} == 'unlock'"],
                    depends_on=["check_user_exists"]
                ),
                WorkflowStep(
                    id="add_to_groups",
                    name="Add User to Groups",
                    step_type=StepType.COMMAND,
                    description="Add user to additional groups",
                    command="usermod -a -G {{groups|join(',')}} {{username}}",
                    conditions=["{{groups|length}} > 0", "{{action}} in ['create', 'modify']"],
                    depends_on=["create_user"]
                ),
                WorkflowStep(
                    id="verify_user_status",
                    name="Verify User Status",
                    step_type=StepType.VALIDATION,
                    description="Verify final user status",
                    command="id {{username}} && getent passwd {{username}}",
                    conditions=["{{action}} != 'delete'"]
                )
            ],
            target_types=["linux_server"],
            protocols=["ssh"],
            estimated_duration=60,
            risk_level="high",
            prerequisites=[
                "Root or sudo privileges",
                "User management commands available",
                "Appropriate system policies"
            ],
            tags=["user", "account", "management", "security"]
        )
        
        # Database Backup Template
        templates["database_backup"] = WorkflowTemplate(
            id="database_backup",
            name="Database Backup",
            description="Create backup of PostgreSQL or MySQL database",
            category=WorkflowCategory.DATABASE_OPERATIONS,
            version="1.0",
            author="OpsConductor AI",
            parameters=[
                WorkflowParameter(
                    name="database_type",
                    parameter_type=ParameterType.STRING,
                    description="Type of database",
                    validation_rules=["in:postgresql,mysql"],
                    examples=["postgresql", "mysql"]
                ),
                WorkflowParameter(
                    name="database_name",
                    parameter_type=ParameterType.STRING,
                    description="Name of database to backup"
                ),
                WorkflowParameter(
                    name="backup_path",
                    parameter_type=ParameterType.FILE_PATH,
                    description="Path to store backup file",
                    default_value="/tmp/db_backup_$(date +%Y%m%d_%H%M%S).sql"
                ),
                WorkflowParameter(
                    name="compress_backup",
                    parameter_type=ParameterType.BOOLEAN,
                    description="Compress backup file",
                    default_value=True
                ),
                WorkflowParameter(
                    name="db_host",
                    parameter_type=ParameterType.STRING,
                    description="Database host",
                    default_value="localhost"
                ),
                WorkflowParameter(
                    name="db_port",
                    parameter_type=ParameterType.INTEGER,
                    description="Database port",
                    required=False
                ),
                WorkflowParameter(
                    name="db_username",
                    parameter_type=ParameterType.STRING,
                    description="Database username"
                )
            ],
            steps=[
                WorkflowStep(
                    id="check_db_connection",
                    name="Test Database Connection",
                    step_type=StepType.VALIDATION,
                    description="Verify database connectivity",
                    command="pg_isready -h {{db_host}} -p {{db_port|default(5432)}} -U {{db_username}}",
                    conditions=["{{database_type}} == 'postgresql'"]
                ),
                WorkflowStep(
                    id="postgresql_backup",
                    name="Create PostgreSQL Backup",
                    step_type=StepType.COMMAND,
                    description="Create PostgreSQL database dump",
                    command="pg_dump -h {{db_host}} -p {{db_port|default(5432)}} -U {{db_username}} -d {{database_name}} > {{backup_path}}",
                    conditions=["{{database_type}} == 'postgresql'"],
                    timeout=3600,
                    depends_on=["check_db_connection"]
                ),
                WorkflowStep(
                    id="mysql_backup",
                    name="Create MySQL Backup",
                    step_type=StepType.COMMAND,
                    description="Create MySQL database dump",
                    command="mysqldump -h {{db_host}} -P {{db_port|default(3306)}} -u {{db_username}} -p {{database_name}} > {{backup_path}}",
                    conditions=["{{database_type}} == 'mysql'"],
                    timeout=3600
                ),
                WorkflowStep(
                    id="compress_backup_file",
                    name="Compress Backup",
                    step_type=StepType.COMMAND,
                    description="Compress backup file with gzip",
                    command="gzip {{backup_path}}",
                    conditions=["{{compress_backup}} == true"],
                    depends_on=["postgresql_backup", "mysql_backup"]
                ),
                WorkflowStep(
                    id="verify_backup",
                    name="Verify Backup File",
                    step_type=StepType.VALIDATION,
                    description="Verify backup file was created successfully",
                    command="test -f {{backup_path}}{% if compress_backup %}.gz{% endif %} && ls -lh {{backup_path}}{% if compress_backup %}.gz{% endif %}",
                    depends_on=["compress_backup_file"]
                )
            ],
            target_types=["linux_server", "database"],
            protocols=["ssh"],
            estimated_duration=1800,
            risk_level="medium",
            prerequisites=[
                "Database client tools installed",
                "Database credentials configured",
                "Sufficient disk space for backup"
            ],
            tags=["database", "backup", "postgresql", "mysql"]
        )
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get workflow template by ID"""
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> Dict[str, WorkflowTemplate]:
        """Get all workflow templates"""
        return self.templates
    
    def get_templates_by_category(self, category: WorkflowCategory) -> List[WorkflowTemplate]:
        """Get templates filtered by category"""
        return [template for template in self.templates.values() if template.category == category]
    
    def find_templates_by_keywords(self, keywords: List[str]) -> List[WorkflowTemplate]:
        """Find templates matching keywords in name, description, or tags"""
        matching_templates = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for template in self.templates.values():
            # Check name and description
            text_to_search = f"{template.name} {template.description}".lower()
            
            # Check tags
            tags_text = " ".join(template.tags).lower()
            text_to_search += f" {tags_text}"
            
            # Check if any keyword matches
            for keyword in keywords_lower:
                if keyword in text_to_search:
                    matching_templates.append(template)
                    break
        
        return matching_templates
    
    def find_templates_for_target_type(self, target_type: str) -> List[WorkflowTemplate]:
        """Find templates suitable for a specific target type"""
        return [template for template in self.templates.values() 
                if target_type in template.target_types]
    
    def find_templates_for_protocol(self, protocol: str) -> List[WorkflowTemplate]:
        """Find templates that use a specific protocol"""
        return [template for template in self.templates.values() 
                if protocol in template.protocols]
    
    def get_template_parameters(self, template_id: str) -> List[WorkflowParameter]:
        """Get parameters for a specific template"""
        template = self.get_template(template_id)
        return template.parameters if template else []
    
    def validate_template_parameters(self, template_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for a template"""
        template = self.get_template(template_id)
        if not template:
            return {"valid": False, "error": f"Template {template_id} not found"}
        
        validation_result = {
            "valid": True,
            "missing_required": [],
            "invalid_values": [],
            "warnings": []
        }
        
        # Check required parameters
        for param in template.parameters:
            if param.required and param.name not in parameters:
                validation_result["missing_required"].append(param.name)
        
        # Validate parameter values
        for param in template.parameters:
            if param.name in parameters:
                value = parameters[param.name]
                param_validation = self._validate_parameter_value(param, value)
                if not param_validation["valid"]:
                    validation_result["invalid_values"].append({
                        "parameter": param.name,
                        "error": param_validation["error"]
                    })
        
        if validation_result["missing_required"] or validation_result["invalid_values"]:
            validation_result["valid"] = False
        
        return validation_result
    
    def _validate_parameter_value(self, param: WorkflowParameter, value: Any) -> Dict[str, Any]:
        """Validate a single parameter value"""
        result = {"valid": True, "error": None}
        
        # Type validation
        if param.parameter_type == ParameterType.STRING and not isinstance(value, str):
            result["valid"] = False
            result["error"] = f"Expected string, got {type(value).__name__}"
        elif param.parameter_type == ParameterType.INTEGER and not isinstance(value, int):
            result["valid"] = False
            result["error"] = f"Expected integer, got {type(value).__name__}"
        elif param.parameter_type == ParameterType.BOOLEAN and not isinstance(value, bool):
            result["valid"] = False
            result["error"] = f"Expected boolean, got {type(value).__name__}"
        elif param.parameter_type == ParameterType.LIST and not isinstance(value, list):
            result["valid"] = False
            result["error"] = f"Expected list, got {type(value).__name__}"
        elif param.parameter_type == ParameterType.DICT and not isinstance(value, dict):
            result["valid"] = False
            result["error"] = f"Expected dict, got {type(value).__name__}"
        
        # Validation rules
        if result["valid"] and param.validation_rules:
            for rule in param.validation_rules:
                rule_result = self._apply_validation_rule(rule, value)
                if not rule_result["valid"]:
                    result["valid"] = False
                    result["error"] = rule_result["error"]
                    break
        
        return result
    
    def _apply_validation_rule(self, rule: str, value: Any) -> Dict[str, Any]:
        """Apply a validation rule to a value"""
        result = {"valid": True, "error": None}
        
        if rule.startswith("min:"):
            min_val = int(rule[4:])
            if isinstance(value, (int, float)) and value < min_val:
                result["valid"] = False
                result["error"] = f"Value must be at least {min_val}"
        
        elif rule.startswith("max:"):
            max_val = int(rule[4:])
            if isinstance(value, (int, float)) and value > max_val:
                result["valid"] = False
                result["error"] = f"Value must be at most {max_val}"
        
        elif rule.startswith("in:"):
            allowed_values = rule[3:].split(",")
            if str(value) not in allowed_values:
                result["valid"] = False
                result["error"] = f"Value must be one of: {', '.join(allowed_values)}"
        
        elif rule.startswith("regex:"):
            import re
            pattern = rule[6:]
            if isinstance(value, str) and not re.match(pattern, value):
                result["valid"] = False
                result["error"] = f"Value does not match required pattern"
        
        return result
    
    def generate_workflow_from_template(self, template_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executable workflow from template and parameters"""
        template = self.get_template(template_id)
        if not template:
            return {"error": f"Template {template_id} not found"}
        
        # Validate parameters
        validation = self.validate_template_parameters(template_id, parameters)
        if not validation["valid"]:
            return {"error": "Parameter validation failed", "validation": validation}
        
        # Fill in default values
        final_parameters = {}
        for param in template.parameters:
            if param.name in parameters:
                final_parameters[param.name] = parameters[param.name]
            elif param.default_value is not None:
                final_parameters[param.name] = param.default_value
        
        # Generate workflow
        workflow = {
            "name": template.name,
            "description": template.description,
            "template_id": template_id,
            "template_version": template.version,
            "parameters": final_parameters,
            "steps": [],
            "estimated_duration": template.estimated_duration,
            "risk_level": template.risk_level,
            "target_types": template.target_types,
            "protocols": template.protocols
        }
        
        # Process steps with parameter substitution
        for step in template.steps:
            processed_step = self._process_step_with_parameters(step, final_parameters)
            workflow["steps"].append(processed_step)
        
        return workflow
    
    def _process_step_with_parameters(self, step: WorkflowStep, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process workflow step with parameter substitution"""
        processed_step = {
            "id": step.id,
            "name": step.name,
            "type": step.step_type.value,
            "description": step.description,
            "timeout": step.timeout,
            "retry_count": step.retry_count,
            "depends_on": step.depends_on,
            "error_handling": step.error_handling
        }
        
        # Process command with parameter substitution
        if step.command:
            processed_step["command"] = self._substitute_parameters(step.command, parameters)
        
        # Process script with parameter substitution
        if step.script:
            processed_step["script"] = self._substitute_parameters(step.script, parameters)
        
        # Process conditions
        if step.conditions:
            processed_conditions = []
            for condition in step.conditions:
                processed_condition = self._substitute_parameters(condition, parameters)
                processed_conditions.append(processed_condition)
            processed_step["conditions"] = processed_conditions
        
        # Process step parameters
        if step.parameters:
            processed_params = {}
            for key, value in step.parameters.items():
                if isinstance(value, str):
                    processed_params[key] = self._substitute_parameters(value, parameters)
                else:
                    processed_params[key] = value
            processed_step["parameters"] = processed_params
        
        return processed_step
    
    def _substitute_parameters(self, text: str, parameters: Dict[str, Any]) -> str:
        """Substitute parameters in text using Jinja2-like syntax"""
        import re
        
        # Simple parameter substitution for {{parameter_name}}
        def replace_param(match):
            param_name = match.group(1)
            if param_name in parameters:
                return str(parameters[param_name])
            return match.group(0)  # Return original if parameter not found
        
        # Replace {{parameter}} patterns
        result = re.sub(r'\{\{(\w+)\}\}', replace_param, text)
        
        # Handle more complex expressions like {{parameter|default(value)}}
        # This is a simplified implementation - in practice, you'd use a proper template engine
        
        return result
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get statistics about workflow templates"""
        stats = {
            "total_templates": len(self.templates),
            "templates_by_category": {},
            "templates_by_risk_level": {},
            "templates_by_target_type": {},
            "average_estimated_duration": 0,
            "template_summary": []
        }
        
        total_duration = 0
        duration_count = 0
        
        for template in self.templates.values():
            # Category statistics
            category = template.category.value
            stats["templates_by_category"][category] = stats["templates_by_category"].get(category, 0) + 1
            
            # Risk level statistics
            risk_level = template.risk_level
            stats["templates_by_risk_level"][risk_level] = stats["templates_by_risk_level"].get(risk_level, 0) + 1
            
            # Target type statistics
            for target_type in template.target_types:
                stats["templates_by_target_type"][target_type] = stats["templates_by_target_type"].get(target_type, 0) + 1
            
            # Duration statistics
            if template.estimated_duration:
                total_duration += template.estimated_duration
                duration_count += 1
            
            # Template summary
            template_info = {
                "id": template.id,
                "name": template.name,
                "category": template.category.value,
                "risk_level": template.risk_level,
                "steps": len(template.steps),
                "parameters": len(template.parameters),
                "estimated_duration": template.estimated_duration
            }
            stats["template_summary"].append(template_info)
        
        if duration_count > 0:
            stats["average_estimated_duration"] = total_duration // duration_count
        
        return stats

# Global instance
workflow_templates = WorkflowTemplateManager()
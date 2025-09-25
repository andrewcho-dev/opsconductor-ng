"""
Workflow Planner - Converting Intent to Executable Workflows

Takes user intent from the IntentBrain and creates detailed, executable workflows
that can be processed by the automation service.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Types of workflow steps"""
    INFORMATION_GATHERING = "information_gathering"
    SYSTEM_ANALYSIS = "system_analysis"
    CONFIGURATION_CHANGE = "configuration_change"
    SOFTWARE_INSTALLATION = "software_installation"
    SERVICE_MANAGEMENT = "service_management"
    NETWORK_OPERATION = "network_operation"
    SECURITY_OPERATION = "security_operation"
    MONITORING_SETUP = "monitoring_setup"
    BACKUP_OPERATION = "backup_operation"
    VALIDATION = "validation"


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    step_type: StepType
    name: str
    description: str
    command: Optional[str] = None
    script_content: Optional[str] = None
    target_systems: List[str] = None
    dependencies: List[str] = None  # step_ids this step depends on
    timeout_seconds: int = 300
    retry_count: int = 1
    validation_command: Optional[str] = None
    
    def __post_init__(self):
        if self.target_systems is None:
            self.target_systems = []
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class Workflow:
    """Complete workflow definition"""
    workflow_id: str
    name: str
    description: str
    user_intent: str
    steps: List[WorkflowStep]
    estimated_duration_minutes: int
    risk_level: str  # low, medium, high
    requires_approval: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class WorkflowPlanner:
    """
    Workflow Planner - Converts user intent into executable workflows
    
    Uses LLM intelligence to understand the intent and create detailed
    step-by-step workflows that can be executed by the automation service.
    """
    
    def __init__(self, llm_engine=None, asset_client=None):
        """Initialize the Workflow Planner"""
        self.llm_engine = llm_engine
        self.asset_client = asset_client
        
        # Common workflow templates
        self.workflow_templates = {
            "software_installation": self._create_software_installation_template,
            "service_restart": self._create_service_restart_template,
            "system_update": self._create_system_update_template,
            "network_diagnostics": self._create_network_diagnostics_template,
            "security_scan": self._create_security_scan_template,
            "backup_operation": self._create_backup_template,
            "monitoring_setup": self._create_monitoring_template
        }
        
        logger.info("Workflow Planner initialized")
    
    async def create_workflow(self, user_intent: str, user_message: str, context: Optional[Dict] = None) -> Optional[Workflow]:
        """
        Create a workflow from user intent
        
        Args:
            user_intent: What the user wants to accomplish
            user_message: Original user message
            context: Additional context information
            
        Returns:
            Workflow object or None if unable to create
        """
        try:
            logger.info(f"Creating workflow for intent: {user_intent}")
            
            # Analyze the intent to determine workflow type
            workflow_type = await self._analyze_intent_type(user_intent, user_message)
            
            if not workflow_type:
                logger.warning(f"Could not determine workflow type for intent: {user_intent}")
                return None
            
            # Generate workflow based on type
            if workflow_type in self.workflow_templates:
                workflow = await self.workflow_templates[workflow_type](user_intent, user_message, context)
            else:
                workflow = await self._create_custom_workflow(user_intent, user_message, context)
            
            if workflow:
                logger.info(f"Created workflow '{workflow.name}' with {len(workflow.steps)} steps")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {str(e)}")
            return None
    
    async def _analyze_intent_type(self, user_intent: str, user_message: str) -> Optional[str]:
        """Analyze intent to determine the type of workflow needed"""
        
        # Simple keyword-based analysis (can be enhanced with LLM)
        intent_lower = user_intent.lower()
        message_lower = user_message.lower()
        
        # Software installation keywords
        if any(keyword in intent_lower for keyword in ["install", "setup", "deploy", "package"]):
            return "software_installation"
        
        # Service management keywords
        if any(keyword in intent_lower for keyword in ["restart", "start", "stop", "service", "daemon"]):
            return "service_restart"
        
        # System update keywords
        if any(keyword in intent_lower for keyword in ["update", "upgrade", "patch"]):
            return "system_update"
        
        # Network diagnostics keywords
        if any(keyword in intent_lower for keyword in ["network", "connectivity", "ping", "traceroute", "dns"]):
            return "network_diagnostics"
        
        # Security scan keywords
        if any(keyword in intent_lower for keyword in ["security", "scan", "vulnerability", "audit"]):
            return "security_scan"
        
        # Backup keywords
        if any(keyword in intent_lower for keyword in ["backup", "archive", "snapshot"]):
            return "backup_operation"
        
        # Monitoring keywords
        if any(keyword in intent_lower for keyword in ["monitor", "alert", "watch", "track"]):
            return "monitoring_setup"
        
        # If using LLM, we could do more sophisticated analysis here
        if self.llm_engine:
            return await self._llm_analyze_intent_type(user_intent, user_message)
        
        return None
    
    async def _llm_analyze_intent_type(self, user_intent: str, user_message: str) -> Optional[str]:
        """Use LLM to analyze intent type"""
        try:
            prompt = f"""
            Analyze this user intent and determine the type of IT operation workflow needed.
            
            User Intent: {user_intent}
            Original Message: {user_message}
            
            Available workflow types:
            - software_installation: Installing, setting up, or deploying software
            - service_restart: Starting, stopping, or restarting services
            - system_update: Updating or patching systems
            - network_diagnostics: Network troubleshooting and diagnostics
            - security_scan: Security scanning and auditing
            - backup_operation: Backup and archival operations
            - monitoring_setup: Setting up monitoring and alerts
            
            Respond with just the workflow type name, or "custom" if none fit exactly.
            """
            
            response = await self.llm_engine.generate_response(prompt)
            workflow_type = response.strip().lower()
            
            if workflow_type in self.workflow_templates or workflow_type == "custom":
                return workflow_type
            
        except Exception as e:
            logger.error(f"LLM intent analysis failed: {str(e)}")
        
        return None
    
    async def _create_software_installation_template(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a software installation workflow"""
        workflow_id = f"install_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="check_prerequisites",
                step_type=StepType.SYSTEM_ANALYSIS,
                name="Check Prerequisites",
                description="Verify system requirements and prerequisites",
                command="uname -a && df -h && free -m",
                timeout_seconds=60
            ),
            WorkflowStep(
                step_id="update_package_list",
                step_type=StepType.SYSTEM_ANALYSIS,
                name="Update Package List",
                description="Update system package list",
                command="apt update || yum update || echo 'Package manager not detected'",
                timeout_seconds=120,
                dependencies=["check_prerequisites"]
            ),
            WorkflowStep(
                step_id="install_software",
                step_type=StepType.SOFTWARE_INSTALLATION,
                name="Install Software",
                description=f"Install software based on user request: {user_intent}",
                command="echo 'Installation command will be determined based on specific software'",
                timeout_seconds=600,
                dependencies=["update_package_list"]
            ),
            WorkflowStep(
                step_id="verify_installation",
                step_type=StepType.VALIDATION,
                name="Verify Installation",
                description="Verify that the software was installed correctly",
                command="echo 'Verification command will be determined based on specific software'",
                timeout_seconds=60,
                dependencies=["install_software"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="Software Installation",
            description=f"Install software: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=15,
            risk_level="medium",
            requires_approval=True
        )
    
    async def _create_service_restart_template(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a service restart workflow"""
        workflow_id = f"service_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="check_service_status",
                step_type=StepType.SYSTEM_ANALYSIS,
                name="Check Service Status",
                description="Check current status of the service",
                command="systemctl status SERVICE_NAME || service SERVICE_NAME status",
                timeout_seconds=30
            ),
            WorkflowStep(
                step_id="restart_service",
                step_type=StepType.SERVICE_MANAGEMENT,
                name="Restart Service",
                description=f"Restart service based on user request: {user_intent}",
                command="systemctl restart SERVICE_NAME || service SERVICE_NAME restart",
                timeout_seconds=60,
                dependencies=["check_service_status"]
            ),
            WorkflowStep(
                step_id="verify_service",
                step_type=StepType.VALIDATION,
                name="Verify Service",
                description="Verify that the service is running correctly",
                command="systemctl is-active SERVICE_NAME || service SERVICE_NAME status",
                timeout_seconds=30,
                dependencies=["restart_service"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="Service Management",
            description=f"Manage service: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=5,
            risk_level="low",
            requires_approval=False
        )
    
    async def _create_system_update_template(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a system update workflow"""
        workflow_id = f"update_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="backup_system",
                step_type=StepType.BACKUP_OPERATION,
                name="Backup System",
                description="Create system backup before updates",
                command="echo 'Creating system backup...'",
                timeout_seconds=300
            ),
            WorkflowStep(
                step_id="update_packages",
                step_type=StepType.SYSTEM_ANALYSIS,
                name="Update Packages",
                description="Update system packages",
                command="apt update && apt upgrade -y || yum update -y",
                timeout_seconds=1800,
                dependencies=["backup_system"]
            ),
            WorkflowStep(
                step_id="verify_updates",
                step_type=StepType.VALIDATION,
                name="Verify Updates",
                description="Verify that updates were applied successfully",
                command="apt list --upgradable || yum check-update",
                timeout_seconds=60,
                dependencies=["update_packages"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="System Update",
            description=f"Update system: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=30,
            risk_level="high",
            requires_approval=True
        )
    
    async def _create_network_diagnostics_template(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a network diagnostics workflow"""
        workflow_id = f"netdiag_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="check_interfaces",
                step_type=StepType.NETWORK_OPERATION,
                name="Check Network Interfaces",
                description="Check network interface status",
                command="ip addr show || ifconfig",
                timeout_seconds=30
            ),
            WorkflowStep(
                step_id="test_connectivity",
                step_type=StepType.NETWORK_OPERATION,
                name="Test Connectivity",
                description="Test network connectivity",
                command="ping -c 4 8.8.8.8 && ping -c 4 google.com",
                timeout_seconds=60,
                dependencies=["check_interfaces"]
            ),
            WorkflowStep(
                step_id="check_dns",
                step_type=StepType.NETWORK_OPERATION,
                name="Check DNS Resolution",
                description="Test DNS resolution",
                command="nslookup google.com && dig google.com",
                timeout_seconds=30,
                dependencies=["test_connectivity"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="Network Diagnostics",
            description=f"Network diagnostics: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=5,
            risk_level="low",
            requires_approval=False
        )
    
    async def _create_security_scan_template(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a security scan workflow"""
        workflow_id = f"security_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="system_info",
                step_type=StepType.SECURITY_OPERATION,
                name="Gather System Information",
                description="Collect system information for security assessment",
                command="uname -a && whoami && id",
                timeout_seconds=30
            ),
            WorkflowStep(
                step_id="check_updates",
                step_type=StepType.SECURITY_OPERATION,
                name="Check Security Updates",
                description="Check for available security updates",
                command="apt list --upgradable | grep -i security || yum check-update --security",
                timeout_seconds=60,
                dependencies=["system_info"]
            ),
            WorkflowStep(
                step_id="scan_ports",
                step_type=StepType.SECURITY_OPERATION,
                name="Scan Open Ports",
                description="Scan for open ports and services",
                command="netstat -tuln || ss -tuln",
                timeout_seconds=30,
                dependencies=["check_updates"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="Security Scan",
            description=f"Security scan: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=10,
            risk_level="low",
            requires_approval=False
        )
    
    async def _create_backup_template(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a backup workflow"""
        workflow_id = f"backup_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="check_space",
                step_type=StepType.SYSTEM_ANALYSIS,
                name="Check Disk Space",
                description="Check available disk space for backup",
                command="df -h",
                timeout_seconds=30
            ),
            WorkflowStep(
                step_id="create_backup",
                step_type=StepType.BACKUP_OPERATION,
                name="Create Backup",
                description=f"Create backup: {user_intent}",
                command="echo 'Backup command will be determined based on specific requirements'",
                timeout_seconds=1800,
                dependencies=["check_space"]
            ),
            WorkflowStep(
                step_id="verify_backup",
                step_type=StepType.VALIDATION,
                name="Verify Backup",
                description="Verify backup integrity",
                command="echo 'Backup verification command'",
                timeout_seconds=300,
                dependencies=["create_backup"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="Backup Operation",
            description=f"Backup: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=45,
            risk_level="medium",
            requires_approval=True
        )
    
    async def _create_monitoring_template(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a monitoring setup workflow"""
        workflow_id = f"monitor_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                step_id="check_monitoring",
                step_type=StepType.MONITORING_SETUP,
                name="Check Existing Monitoring",
                description="Check for existing monitoring tools",
                command="ps aux | grep -E '(nagios|zabbix|prometheus|grafana)' || echo 'No monitoring detected'",
                timeout_seconds=30
            ),
            WorkflowStep(
                step_id="setup_monitoring",
                step_type=StepType.MONITORING_SETUP,
                name="Setup Monitoring",
                description=f"Setup monitoring: {user_intent}",
                command="echo 'Monitoring setup command will be determined based on requirements'",
                timeout_seconds=600,
                dependencies=["check_monitoring"]
            ),
            WorkflowStep(
                step_id="test_monitoring",
                step_type=StepType.VALIDATION,
                name="Test Monitoring",
                description="Test monitoring functionality",
                command="echo 'Testing monitoring setup'",
                timeout_seconds=60,
                dependencies=["setup_monitoring"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="Monitoring Setup",
            description=f"Setup monitoring: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=20,
            risk_level="medium",
            requires_approval=True
        )
    
    async def _create_custom_workflow(self, user_intent: str, user_message: str, context: Optional[Dict]) -> Workflow:
        """Create a custom workflow using LLM analysis"""
        workflow_id = f"custom_{int(datetime.now().timestamp())}"
        
        # For now, create a simple analysis workflow
        # This can be enhanced with LLM-generated steps
        steps = [
            WorkflowStep(
                step_id="analyze_request",
                step_type=StepType.INFORMATION_GATHERING,
                name="Analyze Request",
                description=f"Analyze custom request: {user_intent}",
                command="echo 'Analyzing custom request...'",
                timeout_seconds=60
            ),
            WorkflowStep(
                step_id="gather_info",
                step_type=StepType.SYSTEM_ANALYSIS,
                name="Gather System Information",
                description="Gather relevant system information",
                command="uname -a && df -h && ps aux | head -20",
                timeout_seconds=60,
                dependencies=["analyze_request"]
            ),
            WorkflowStep(
                step_id="provide_recommendations",
                step_type=StepType.INFORMATION_GATHERING,
                name="Provide Recommendations",
                description="Provide recommendations based on analysis",
                command="echo 'Based on analysis, here are the recommendations...'",
                timeout_seconds=30,
                dependencies=["gather_info"]
            )
        ]
        
        return Workflow(
            workflow_id=workflow_id,
            name="Custom Analysis",
            description=f"Custom workflow: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=10,
            risk_level="low",
            requires_approval=False
        )
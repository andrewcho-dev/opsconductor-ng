"""
Workflow Planner - Converting Intent to Executable Workflows

Takes user intent from the IntentBrain and creates detailed, executable workflows
that can be processed by the automation service using LLM-powered generation.
"""

import logging
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
    
    Uses LLM intelligence to understand ANY user intent and create detailed
    step-by-step workflows that can be executed by the automation service.
    No templates needed - fully dynamic and adaptable!
    """
    
    def __init__(self, llm_engine=None, asset_client=None):
        """Initialize the Workflow Planner"""
        self.llm_engine = llm_engine
        self.asset_client = asset_client
        
        logger.info("Workflow Planner initialized with LLM-powered generation")
    
    async def create_workflow(self, user_intent: str, user_message: str, context: Optional[Dict] = None) -> Workflow:
        """
        Create a workflow from user intent using LLM-powered generation
        
        Args:
            user_intent: What the user wants to accomplish
            user_message: Original user message
            context: Additional context information
            
        Returns:
            Workflow object
            
        Raises:
            RuntimeError: If workflow generation fails
        """
        logger.info(f"Creating workflow for intent: {user_intent}")
        
        # Use LLM to generate workflow dynamically - NO FALLBACKS
        workflow = await self._create_llm_workflow(user_intent, user_message, context)
        
        logger.info(f"Created workflow '{workflow.name}' with {len(workflow.steps)} steps")
        return workflow
    
    async def _create_llm_workflow(self, user_intent: str, user_message: str, context: Optional[Dict] = None) -> Workflow:
        """
        Create workflow using LLM intelligence - can handle ANY request dynamically
        """
        try:
            logger.info(f"Starting LLM workflow generation for intent: {user_intent}")
            
            # Check if LLM engine is available
            if not self.llm_engine:
                raise RuntimeError("LLM engine not available - cannot generate workflow")
            
            # Get available OpsConductor capabilities
            capabilities = await self._get_opsconductor_capabilities()
            logger.debug("Retrieved OpsConductor capabilities")
            
            # Create comprehensive prompt for workflow generation
            workflow_prompt = f"""
            You are an expert DevOps engineer creating executable workflows for OpsConductor.
            
            USER REQUEST:
            Intent: {user_intent}
            Original Message: {user_message}
            
            AVAILABLE OPSCONDUCTOR SERVICES:
            {capabilities}
            
            TASK: Generate a detailed, executable workflow to fulfill this user request.
            
            IMPORTANT GUIDELINES:
            1. For RECURRING/SCHEDULED tasks (like "ping every 10 minutes"), create steps that:
               - Set up the recurring task using cron or systemd timers
               - Include validation that the schedule is working
               - Use appropriate scheduling syntax (cron format)
            
            2. For ONE-TIME tasks, create immediate execution steps
            
            3. Always include:
               - Validation steps to verify success
               - Error handling considerations
               - Appropriate timeouts
               - Target system identification
            
            4. Use realistic Linux commands that will actually work
            
            5. For network operations like ping:
               - Use proper ping syntax with appropriate options
               - Consider both IPv4 and IPv6 if relevant
               - Include connectivity validation
            
            RESPONSE FORMAT - Describe the workflow in natural language using this exact structure:
            
            WORKFLOW NAME: [descriptive name]
            DESCRIPTION: [what this workflow accomplishes]
            ESTIMATED DURATION: [number] minutes
            RISK LEVEL: [low/medium/high]
            REQUIRES APPROVAL: [yes/no]
            
            STEPS:
            1. STEP: [step name]
               TYPE: [information_gathering/system_analysis/configuration_change/software_installation/service_management/network_operation/security_operation/monitoring_setup/backup_operation/validation]
               DESCRIPTION: [what this step does]
               COMMAND: [actual shell command to execute]
               TARGET SYSTEMS: [system1, system2] or [auto-detect]
               TIMEOUT: [number] seconds
               RETRIES: [number]
               DEPENDENCIES: [step numbers this depends on, if any]
               VALIDATION: [optional command to validate step success]
            
            2. STEP: [next step...]
            
            Provide a clear, structured response following this exact format.
            """
            
            logger.info("Sending prompt to LLM engine")
            llm_response = await self.llm_engine.generate(workflow_prompt)
            response = llm_response["generated_text"]
            logger.info(f"Received LLM response (length: {len(response)})")
            
            # Check if response is empty
            if not response or not response.strip():
                logger.error("LLM returned empty response")
                logger.error(f"Full LLM response object: {llm_response}")
                raise RuntimeError("LLM returned empty response - cannot generate workflow")
            
            # Parse the natural language response
            workflow = self._parse_natural_language_workflow(response, user_intent)
            logger.info(f"Created workflow: {workflow.name} with {len(workflow.steps)} steps")
            return workflow
                
        except Exception as e:
            logger.error(f"LLM workflow generation failed: {str(e)}")
            # NO FALLBACKS - If LLM fails, the system fails gracefully
            raise RuntimeError(f"LLM workflow generation failed: {e}. System requires LLM to function.")
    
    async def _get_opsconductor_capabilities(self) -> str:
        """Get description of available OpsConductor capabilities"""
        return """
        ASSET SERVICE (asset-service:3002):
        - Asset discovery and inventory management
        - Server information and metadata
        - Network topology mapping
        - Credential management and secure access
        
        AUTOMATION SERVICE (automation-service:3003):
        - Celery-based job execution
        - Workflow orchestration
        - Remote command execution on target systems
        - Job scheduling and monitoring
        - Support for shell commands, scripts, and complex workflows
        
        COMMUNICATION SERVICE (communication-service:3004):
        - Notification delivery (email, slack, etc.)
        - Alert management
        - Multi-channel messaging
        - User confirmation requests
        
        NETWORK ANALYZER (network-analyzer-service:3006):
        - Protocol analysis and network monitoring
        - Traffic inspection and analysis
        - Network connectivity testing
        - Security analysis and port scanning
        
        CELERY INFRASTRUCTURE:
        - Distributed task execution across multiple workers
        - Background job processing
        - Scheduled tasks using Celery Beat (supports cron-like scheduling)
        - Real-time monitoring and status tracking
        - Task queuing and priority management
        
        SYSTEM CAPABILITIES:
        - Linux command execution on target systems
        - File system operations and management
        - Service management (systemctl, service commands)
        - Package management (apt, yum, etc.)
        - Network utilities (ping, traceroute, netstat, etc.)
        - Cron job management for recurring tasks
        - Systemd timer management for scheduled operations
        """
    
    def _parse_natural_language_workflow(self, response: str, user_intent: str) -> Workflow:
        """Parse natural language workflow response from LLM"""
        import re
        
        workflow_id = f"llm_{int(datetime.now().timestamp())}"
        
        # Extract workflow metadata
        workflow_name = self._extract_field(response, "WORKFLOW NAME")
        description = self._extract_field(response, "DESCRIPTION")
        duration_str = self._extract_field(response, "ESTIMATED DURATION")
        risk_level = self._extract_field(response, "RISK LEVEL")
        approval_str = self._extract_field(response, "REQUIRES APPROVAL")
        
        # Parse duration (extract number)
        duration_match = re.search(r'(\d+)', duration_str) if duration_str else None
        estimated_duration = int(duration_match.group(1)) if duration_match else 10
        
        # Parse approval (yes/no to boolean)
        requires_approval = approval_str.lower().startswith('yes') if approval_str else False
        
        # Parse steps
        steps = self._parse_workflow_steps(response)
        
        return Workflow(
            workflow_id=workflow_id,
            name=workflow_name or "LLM Generated Workflow",
            description=description or f"Workflow for: {user_intent}",
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=estimated_duration,
            risk_level=risk_level or "medium",
            requires_approval=requires_approval
        )
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from natural language response"""
        import re
        pattern = rf"{field_name}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def _parse_workflow_steps(self, response: str) -> List[WorkflowStep]:
        """Parse workflow steps from natural language response"""
        import re
        
        steps = []
        
        # Find all step blocks
        step_pattern = r'(\d+)\.\s*STEP:\s*(.+?)(?=\d+\.\s*STEP:|$)'
        step_matches = re.findall(step_pattern, response, re.DOTALL | re.IGNORECASE)
        
        for step_num, step_content in step_matches:
            # Extract step details
            step_name = self._extract_step_field(step_content, "STEP")
            step_type = self._extract_step_field(step_content, "TYPE")
            step_description = self._extract_step_field(step_content, "DESCRIPTION")
            command = self._extract_step_field(step_content, "COMMAND")
            target_systems = self._extract_step_field(step_content, "TARGET SYSTEMS")
            timeout_str = self._extract_step_field(step_content, "TIMEOUT")
            retries_str = self._extract_step_field(step_content, "RETRIES")
            dependencies_str = self._extract_step_field(step_content, "DEPENDENCIES")
            validation = self._extract_step_field(step_content, "VALIDATION")
            
            # Parse numeric values
            timeout_match = re.search(r'(\d+)', timeout_str) if timeout_str else None
            timeout = int(timeout_match.group(1)) if timeout_match else 300
            
            retries_match = re.search(r'(\d+)', retries_str) if retries_str else None
            retries = int(retries_match.group(1)) if retries_match else 1
            
            # Parse target systems
            if target_systems:
                if "auto-detect" in target_systems.lower():
                    target_list = ["auto-detect"]
                else:
                    target_list = [t.strip() for t in target_systems.split(',')]
            else:
                target_list = ["auto-detect"]
            
            # Parse dependencies
            dependencies = []
            if dependencies_str and dependencies_str.lower() != "none":
                dep_matches = re.findall(r'(\d+)', dependencies_str)
                dependencies = [f"step_{dep}" for dep in dep_matches]
            
            # Map step type to enum
            step_type_mapping = {
                "information_gathering": StepType.INFORMATION_GATHERING,
                "system_analysis": StepType.SYSTEM_ANALYSIS,
                "configuration_change": StepType.CONFIGURATION_CHANGE,
                "software_installation": StepType.SOFTWARE_INSTALLATION,
                "service_management": StepType.SERVICE_MANAGEMENT,
                "network_operation": StepType.NETWORK_OPERATION,
                "security_operation": StepType.SECURITY_OPERATION,
                "monitoring_setup": StepType.MONITORING_SETUP,
                "backup_operation": StepType.BACKUP_OPERATION,
                "validation": StepType.VALIDATION
            }
            
            step_type_enum = step_type_mapping.get(step_type.lower(), StepType.SYSTEM_ANALYSIS)
            
            step = WorkflowStep(
                step_id=f"step_{step_num}",
                step_type=step_type_enum,
                name=step_name or f"Step {step_num}",
                description=step_description or "",
                command=command,
                target_systems=target_list,
                timeout_seconds=timeout,
                retry_count=retries,
                dependencies=dependencies,
                validation_command=validation if validation and validation.lower() != "none" else None
            )
            steps.append(step)
        
        return steps
    
    def _extract_step_field(self, step_content: str, field_name: str) -> str:
        """Extract a field from step content"""
        import re
        
        # First try to find the field at the beginning of a line
        pattern = rf"^\s*{field_name}:\s*(.+?)(?:\n\s*[A-Z]+:|$)"
        match = re.search(pattern, step_content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # If that fails, try a more flexible pattern
        pattern = rf"{field_name}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, step_content, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    

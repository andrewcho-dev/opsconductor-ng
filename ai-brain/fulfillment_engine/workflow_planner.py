"""
Workflow Planner - Converting Intent to Executable Workflows

Takes user intent from the IntentBrain and creates detailed, executable workflows
that can be processed by the automation service using LLM-powered generation.
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
            
            RESPONSE FORMAT (JSON):
            {{
                "workflow_name": "descriptive name",
                "description": "what this workflow accomplishes",
                "estimated_duration_minutes": number,
                "risk_level": "low|medium|high",
                "requires_approval": boolean,
                "steps": [
                    {{
                        "step_id": "unique_id",
                        "step_type": "information_gathering|system_analysis|configuration_change|software_installation|service_management|network_operation|security_operation|monitoring_setup|backup_operation|validation",
                        "name": "step name",
                        "description": "what this step does",
                        "command": "actual shell command to execute",
                        "target_systems": ["system1", "system2"] or ["auto-detect"],
                        "timeout_seconds": number,
                        "retry_count": number,
                        "dependencies": ["step_id1", "step_id2"],
                        "validation_command": "optional command to validate step success"
                    }}
                ]
            }}
            
            Generate the workflow now:
            """
            
            logger.info("Sending prompt to LLM engine")
            llm_response = await self.llm_engine.generate(workflow_prompt)
            response = llm_response["generated_text"]
            logger.info(f"Received LLM response (length: {len(response)})")
            
            # Parse the JSON response
            try:
                # Clean up the response - sometimes LLM adds extra text
                response_clean = response.strip()
                if response_clean.startswith("```json"):
                    response_clean = response_clean[7:]
                if response_clean.endswith("```"):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()
                
                logger.debug(f"Cleaned LLM response: {response_clean[:200]}...")
                workflow_data = json.loads(response_clean)
                logger.info("Successfully parsed LLM response as JSON")
                
                workflow = self._create_workflow_from_json(workflow_data, user_intent)
                logger.info(f"Created workflow: {workflow.name} with {len(workflow.steps)} steps")
                return workflow
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM workflow response as JSON: {e}")
                logger.error(f"Raw LLM Response: {response}")
                raise RuntimeError(f"LLM returned invalid JSON: {e}")
                
        except Exception as e:
            logger.error(f"LLM workflow generation failed: {str(e)}")
            raise RuntimeError(f"LLM workflow generation failed: {e}")
    
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
    
    def _create_workflow_from_json(self, workflow_data: Dict, user_intent: str) -> Workflow:
        """Create Workflow object from JSON data"""
        workflow_id = f"llm_{int(datetime.now().timestamp())}"
        
        # Create workflow steps
        steps = []
        for step_data in workflow_data.get("steps", []):
            step = WorkflowStep(
                step_id=step_data.get("step_id", f"step_{len(steps)}"),
                step_type=StepType(step_data.get("step_type", "system_analysis")),
                name=step_data.get("name", "Unnamed Step"),
                description=step_data.get("description", ""),
                command=step_data.get("command"),
                target_systems=step_data.get("target_systems", []),
                timeout_seconds=step_data.get("timeout_seconds", 300),
                retry_count=step_data.get("retry_count", 1),
                dependencies=step_data.get("dependencies", []),
                validation_command=step_data.get("validation_command")
            )
            steps.append(step)
        
        return Workflow(
            workflow_id=workflow_id,
            name=workflow_data.get("workflow_name", "LLM Generated Workflow"),
            description=workflow_data.get("description", f"Workflow for: {user_intent}"),
            user_intent=user_intent,
            steps=steps,
            estimated_duration_minutes=workflow_data.get("estimated_duration_minutes", 10),
            risk_level=workflow_data.get("risk_level", "medium"),
            requires_approval=workflow_data.get("requires_approval", False)
        )
    

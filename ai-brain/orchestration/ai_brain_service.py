"""
AI Brain Service - Main orchestration service for AI-driven workflow management.
Integrates with Prefect for workflow orchestration and provides fallback to Celery.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Core integrations
from integrations.prefect_client import PrefectClient
from integrations.llm_service_factory import LLMServiceFactory
from integrations.automation_client import AutomationServiceClient
from integrations.asset_client import AssetServiceClient

# Job engine components
from job_engine.workflow_generator import WorkflowGenerator
from job_engine.execution_planner import ExecutionPlanner
from job_engine.target_resolver import TargetResolver

# Fulfillment engine
from fulfillment_engine.fulfillment_orchestrator import FulfillmentOrchestrator

# Orchestration components
from .prefect_flow_engine import PrefectFlowEngine

logger = logging.getLogger(__name__)

class AIBrainService:
    """
    Main AI Brain service that orchestrates workflow generation and execution.
    Provides hybrid execution strategy with Prefect as primary and Celery as fallback.
    """
    
    def __init__(self):
        """Initialize the AI Brain service with all required components."""
        import os
        
        # Initialize clients with proper configuration
        self.prefect_client = PrefectClient()
        self.llm_client = LLMServiceFactory.create_client(
            ollama_host=os.getenv("OLLAMA_HOST", "http://ollama:11434"),
            default_model=os.getenv("DEFAULT_MODEL", "codellama:7b")
        )
        self.automation_client = AutomationServiceClient(
            automation_service_url=os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")
        )
        self.asset_client = AssetServiceClient(
            base_url=os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
        )
        
        # Core engines
        self.workflow_generator = WorkflowGenerator()
        self.execution_planner = ExecutionPlanner()
        self.target_resolver = TargetResolver()
        self.fulfillment_orchestrator = FulfillmentOrchestrator()
        
        # Prefect flow engine with cross-service orchestration
        self.prefect_flow_engine = PrefectFlowEngine(
            automation_client=self.automation_client,
            asset_client=self.asset_client,
            network_client=None,  # Will be initialized when available
            communication_client=None  # Will be initialized when available
        )
        
        # Service state
        self.prefect_available = False
        self.initialization_complete = False
        
        logger.info("AI Brain Service initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize all service components and check Prefect availability.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Check Prefect availability
            self.prefect_available = await self.prefect_client.is_available()
            
            if self.prefect_available:
                logger.info("Prefect server is available - using Prefect for workflow orchestration")
                await self.prefect_flow_engine.initialize()
            else:
                logger.warning("Prefect server unavailable - will use Celery fallback for execution")
            
            # Initialize other components
            await self.llm_client.initialize()
            if hasattr(self.fulfillment_orchestrator, 'initialize'):
                await self.fulfillment_orchestrator.initialize()
            
            self.initialization_complete = True
            logger.info("AI Brain Service initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Brain Service: {e}")
            return False
    
    async def process_chat_message(self, message: str, user_id: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a chat message and potentially generate workflows.
        
        Args:
            message: User's chat message
            user_id: ID of the user sending the message
            conversation_id: Optional conversation ID for context
            
        Returns:
            Dict containing response and any generated workflows
        """
        try:
            logger.info(f"Processing chat message from user {user_id}: {message[:100]}...")
            
            # Analyze intent and determine if workflow generation is needed
            intent_analysis = await self._analyze_intent(message, user_id)
            
            response = {
                "message_id": f"msg_{datetime.now().isoformat()}",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "intent": intent_analysis,
                "response": "",
                "workflows": [],
                "execution_status": "pending"
            }
            
            if intent_analysis.get("requires_workflow", False):
                # Generate workflow for the request
                workflow_result = await self._generate_and_execute_workflow(
                    message, user_id, intent_analysis
                )
                response.update(workflow_result)
            else:
                # Simple conversational response
                llm_response = await self.llm_client.generate_response(
                    message, context={"user_id": user_id}
                )
                response["response"] = llm_response
                response["execution_status"] = "completed"
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "error": str(e),
                "execution_status": "failed"
            }
    
    async def _analyze_intent(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        🚀 AI-DRIVEN INTENT ANALYSIS
        
        Uses LLM to intelligently analyze user messages and determine if they require
        workflow orchestration, what type of workflow, and the complexity level.
        """
        try:
            intent_analysis_prompt = f"""Analyze this user message to determine if it requires workflow orchestration or is just conversational.

USER MESSAGE: "{message}"
USER ID: {user_id}

WORKFLOW ORCHESTRATION INDICATORS:
✅ Requires Workflow if message contains:
- Action requests (execute, run, deploy, configure, monitor, check, scan, update)
- Multi-step operations (setup and configure, check then restart, scan and report)
- IT operations (server management, network tasks, asset queries, automation)
- Scheduled or recurring tasks (every day, monitor continuously, alert when)
- Complex conditional logic (if X then Y, when condition met do Z)
- Cross-system integration (update asset then notify team)
- Data processing or reporting (generate report, analyze logs, aggregate data)

❌ Conversational if message contains:
- Simple questions (what is, how does, can you explain)
- Greetings or casual conversation
- Status inquiries without action (just asking for info)
- Help requests or documentation queries

ANALYSIS REQUIRED:
1. Determine if this requires workflow orchestration
2. Identify the intent type and complexity
3. Assess confidence level
4. Identify key workflow components if applicable

Respond in this JSON format:
{{
  "requires_workflow": true/false,
  "intent_type": "conversational|simple_action|complex_workflow|automation_request|monitoring_setup|data_processing",
  "confidence": 0.0-1.0,
  "complexity_level": "simple|medium|complex",
  "workflow_components": ["component1", "component2"],
  "reasoning": "explanation of the decision"
}}

IMPORTANT: Return ONLY the JSON, no other text."""

            response = await self.llm_client.generate(intent_analysis_prompt)
            
            if isinstance(response, dict) and "generated_text" in response:
                analysis_text = response["generated_text"].strip()
            else:
                analysis_text = str(response).strip()
            
            # Parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    intent_json = json_match.group(0)
                else:
                    intent_json = analysis_text
                
                intent_analysis = json.loads(intent_json)
                
                logger.info(f"🧠 Intent Analysis: {intent_analysis.get('intent_type')} (confidence: {intent_analysis.get('confidence')})")
                logger.info(f"🧠 Requires Workflow: {intent_analysis.get('requires_workflow')}")
                
                return intent_analysis
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse intent analysis JSON: {e}")
                logger.error(f"❌ Raw response: {analysis_text}")
                
                # Fallback: Simple heuristic analysis
                return self._fallback_intent_analysis(message)
                
        except Exception as e:
            logger.error(f"❌ Intent analysis failed: {e}")
            return self._fallback_intent_analysis(message)
    
    def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback intent analysis using simple heuristics"""
        message_lower = message.lower()
        
        # Simple keyword-based analysis
        action_keywords = ["execute", "run", "deploy", "configure", "monitor", "check", "scan", "update", "setup", "install", "restart", "stop", "start"]
        workflow_keywords = ["and then", "after", "when", "if", "schedule", "every", "continuously", "alert", "notify"]
        
        has_action = any(keyword in message_lower for keyword in action_keywords)
        has_workflow = any(keyword in message_lower for keyword in workflow_keywords)
        
        if has_action or has_workflow:
            return {
                "requires_workflow": True,
                "intent_type": "complex_workflow" if has_workflow else "simple_action",
                "confidence": 0.7,
                "complexity_level": "medium" if has_workflow else "simple",
                "workflow_components": ["automation"] if has_action else [],
                "reasoning": "Fallback heuristic analysis detected action/workflow keywords"
            }
        else:
            return {
                "requires_workflow": False,
                "intent_type": "conversational",
                "confidence": 0.6,
                "complexity_level": "simple",
                "workflow_components": [],
                "reasoning": "Fallback heuristic analysis - no action keywords detected"
            }
    
    async def _generate_and_execute_workflow(self, message: str, user_id: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        🚀 AI-DRIVEN WORKFLOW GENERATION AND EXECUTION
        
        Generates and executes workflows using either Prefect (complex) or direct execution (simple)
        based on the intent analysis and workflow complexity.
        """
        try:
            logger.info(f"🚀 Generating workflow for user {user_id}: {message}")
            
            complexity_level = intent.get("complexity_level", "simple")
            intent_type = intent.get("intent_type", "simple_action")
            
            # Determine execution strategy based on complexity and Prefect availability
            if self.prefect_available and complexity_level in ["medium", "complex"]:
                logger.info("🔥 Using Prefect orchestration for complex workflow")
                return await self._generate_prefect_workflow(message, user_id, intent)
            else:
                logger.info("⚡ Using direct execution for simple workflow")
                return await self._generate_direct_workflow(message, user_id, intent)
                
        except Exception as e:
            logger.error(f"❌ Workflow generation failed: {e}")
            return {
                "response": f"Failed to generate workflow: {str(e)}",
                "workflows": [],
                "execution_status": "failed",
                "error": str(e)
            }
    
    async def _generate_prefect_workflow(self, message: str, user_id: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate and execute complex workflow using Prefect orchestration
        """
        try:
            logger.info("🚀 Creating Prefect workflow from user message...")
            
            # Generate workflow tasks using AI
            workflow_tasks = await self._ai_generate_workflow_tasks(message, intent)
            
            # Create dynamic Prefect flow
            flow_name = f"ai_chat_workflow_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            flow_id = await self.prefect_flow_engine.create_dynamic_flow(
                flow_name=flow_name,
                tasks=workflow_tasks,
                parameters={
                    "user_message": message,
                    "user_id": user_id,
                    "intent": intent,
                    "created_by": "ai_brain_chat"
                }
            )
            
            logger.info(f"✅ Created Prefect flow: {flow_id}")
            
            # Deploy and execute the flow
            deployment_id = await self.prefect_flow_engine.deploy_flow(flow_id)
            flow_run_id = await self.prefect_flow_engine.execute_flow(
                flow_id=flow_id,
                parameters={
                    "user_message": message,
                    "user_id": user_id
                }
            )
            
            logger.info(f"✅ Started Prefect workflow execution: {flow_run_id}")
            
            return {
                "response": f"Complex workflow created and executing using Prefect orchestration. Flow ID: {flow_id}",
                "workflows": [{
                    "type": "prefect_workflow",
                    "flow_id": flow_id,
                    "flow_run_id": flow_run_id,
                    "deployment_id": deployment_id,
                    "tasks": workflow_tasks,
                    "status": "running"
                }],
                "execution_status": "running",
                "execution_method": "prefect_orchestration"
            }
            
        except Exception as e:
            logger.error(f"❌ Prefect workflow generation failed: {e}")
            
            # Fallback to direct execution
            logger.info("🔄 Falling back to direct execution...")
            return await self._generate_direct_workflow(message, user_id, intent)
    
    async def _generate_direct_workflow(self, message: str, user_id: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate and execute simple workflow using direct execution
        """
        try:
            logger.info("⚡ Creating direct execution workflow...")
            
            # Use the fulfillment orchestrator for direct execution
            if hasattr(self.fulfillment_orchestrator, 'execute_user_request'):
                result = await self.fulfillment_orchestrator.execute_user_request(
                    user_message=message,
                    user_context={"user_id": user_id, "intent": intent}
                )
                
                return {
                    "response": result.get("message", "Direct workflow executed"),
                    "workflows": [{
                        "type": "direct_execution",
                        "status": result.get("status", "completed"),
                        "details": result
                    }],
                    "execution_status": result.get("status", "completed"),
                    "execution_method": "direct_execution"
                }
            else:
                # Simple response if fulfillment orchestrator not available
                return {
                    "response": f"Acknowledged your request: {message}. Direct execution workflow would be implemented here.",
                    "workflows": [{
                        "type": "simple_response",
                        "status": "completed",
                        "message": message,
                        "intent": intent
                    }],
                    "execution_status": "completed",
                    "execution_method": "simple_response"
                }
                
        except Exception as e:
            logger.error(f"❌ Direct workflow generation failed: {e}")
            return {
                "response": f"Failed to execute workflow: {str(e)}",
                "workflows": [],
                "execution_status": "failed",
                "error": str(e)
            }
    
    async def _ai_generate_workflow_tasks(self, message: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        🚀 AI-DRIVEN TASK GENERATION
        
        Uses LLM to convert user message and intent into structured Prefect workflow tasks
        """
        try:
            task_generation_prompt = f"""Convert this user request into structured Prefect workflow tasks.

USER MESSAGE: "{message}"
INTENT ANALYSIS: {json.dumps(intent, indent=2)}

AVAILABLE SERVICES:
- automation: Execute commands, run scripts, manage processes
- asset: Query inventory, get asset details, update asset information
- network: Network discovery, connectivity tests, port scanning
- communication: Send notifications, alerts, messages

TASK GENERATION RULES:
1. Break down the user request into logical steps
2. Each step becomes a separate task with clear dependencies
3. Include proper error handling and retry logic
4. Specify service integrations where needed
5. Add parameter passing between tasks
6. Include notifications for important results

Generate tasks in this JSON format:
[
  {{
    "name": "descriptive_task_name",
    "type": "service_call|http_request|data_processing|notification|generic",
    "service": "automation|asset|network|communication",
    "action": "specific_action_to_perform",
    "parameters": {{
      "key": "value"
    }},
    "depends_on": ["previous_task_name"],
    "retry_count": 3,
    "timeout_seconds": 60,
    "description": "What this task does"
  }}
]

EXAMPLES:
- For "check server status": [task to query assets, task to check connectivity, task to send notification]
- For "deploy application": [task to prepare environment, task to deploy code, task to verify deployment, task to notify team]
- For "monitor disk space": [task to check disk usage, task to analyze results, task to alert if threshold exceeded]

IMPORTANT: Return ONLY the JSON array, no other text."""

            response = await self.llm_client.generate(task_generation_prompt)
            
            if isinstance(response, dict) and "generated_text" in response:
                tasks_text = response["generated_text"].strip()
            else:
                tasks_text = str(response).strip()
            
            # Parse JSON tasks
            try:
                import re
                json_match = re.search(r'\[.*\]', tasks_text, re.DOTALL)
                if json_match:
                    tasks_json = json_match.group(0)
                else:
                    tasks_json = tasks_text
                
                workflow_tasks = json.loads(tasks_json)
                
                logger.info(f"✅ Generated {len(workflow_tasks)} workflow tasks from user message")
                return workflow_tasks
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse workflow tasks JSON: {e}")
                logger.error(f"❌ Raw response: {tasks_text}")
                
                # Fallback: Create simple generic tasks
                return self._create_fallback_workflow_tasks(message, intent)
                
        except Exception as e:
            logger.error(f"❌ AI task generation failed: {e}")
            return self._create_fallback_workflow_tasks(message, intent)
    
    def _create_fallback_workflow_tasks(self, message: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create simple fallback tasks when AI generation fails"""
        workflow_components = intent.get("workflow_components", ["automation"])
        
        tasks = []
        
        # Add analysis task
        tasks.append({
            "name": "analyze_request",
            "type": "generic",
            "action": "analyze_user_request",
            "parameters": {
                "user_message": message,
                "intent": intent
            },
            "depends_on": [],
            "retry_count": 1,
            "timeout_seconds": 30,
            "description": "Analyze the user request and prepare for execution"
        })
        
        # Add service-specific tasks based on components
        if "automation" in workflow_components:
            tasks.append({
                "name": "automation_task",
                "type": "service_call",
                "service": "automation",
                "action": "health_check",
                "parameters": {},
                "depends_on": ["analyze_request"],
                "retry_count": 2,
                "timeout_seconds": 60,
                "description": "Execute automation-related operations"
            })
        
        if "asset" in workflow_components:
            tasks.append({
                "name": "asset_query",
                "type": "service_call",
                "service": "asset",
                "action": "health_check",
                "parameters": {},
                "depends_on": ["analyze_request"],
                "retry_count": 2,
                "timeout_seconds": 60,
                "description": "Query asset information"
            })
        
        # Add notification task
        tasks.append({
            "name": "notify_completion",
            "type": "notification",
            "parameters": {
                "message": f"Workflow completed for request: {message}",
                "type": "info"
            },
            "depends_on": [task["name"] for task in tasks if task["name"] != "notify_completion"],
            "retry_count": 1,
            "timeout_seconds": 30,
            "description": "Send completion notification"
        })
        
        return tasks
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the AI Brain service.
        
        Returns:
            Dict containing health status
        """
        health_status = {
            "service": "ai-brain",
            "status": "healthy" if self.initialization_complete else "initializing",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "prefect": "available" if self.prefect_available else "unavailable",
                "llm": "unknown",
                "automation": "unknown",
                "assets": "unknown"
            }
        }
        
        return health_status
    
    async def cleanup(self):
        """
        Cleanup AI Brain service resources.
        """
        try:
            logger.info("Cleaning up AI Brain Service...")
            
            # Cleanup Prefect client
            if hasattr(self.prefect_client, 'cleanup'):
                await self.prefect_client.cleanup()
            
            # Cleanup LLM client
            if hasattr(self.llm_client, 'cleanup'):
                await self.llm_client.cleanup()
            
            # Cleanup other components
            if hasattr(self.fulfillment_orchestrator, 'cleanup'):
                await self.fulfillment_orchestrator.cleanup()
            
            self.initialization_complete = False
            logger.info("AI Brain Service cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during AI Brain Service cleanup: {e}")
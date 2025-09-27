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
from integrations.llm_client import LLMEngine
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
        self.llm_client = LLMEngine(
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
        
        # Prefect flow engine
        self.prefect_flow_engine = PrefectFlowEngine()
        
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
        """Analyze user intent to determine if workflow generation is needed."""
        # Placeholder implementation
        return {
            "requires_workflow": False,
            "intent_type": "conversational",
            "confidence": 0.8
        }
    
    async def _generate_and_execute_workflow(self, message: str, user_id: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and execute workflow based on user message and intent."""
        # Placeholder implementation
        return {
            "response": "Workflow generation not yet implemented",
            "workflows": [],
            "execution_status": "pending"
        }
    
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
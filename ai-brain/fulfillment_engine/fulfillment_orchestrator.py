"""
Fulfillment Orchestrator - Main orchestrator that coordinates the entire fulfillment process

Coordinates the entire process of turning user intent into executed actions.
Works with the simplified IntentBrain architecture to provide seamless
intent-to-execution flow.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .intent_processor import IntentProcessor, ProcessedIntent
from .resource_mapper import ResourceMapper, ResourceMapping
from .information_gatherer import InformationGatherer, EnrichedIntent
from .workflow_planner import WorkflowPlanner
from .execution_coordinator import ExecutionCoordinator
from .status_tracker import StatusTracker
from .fulfillment_engine import FulfillmentRequest, FulfillmentResult, FulfillmentStatus

logger = logging.getLogger(__name__)


class FulfillmentOrchestrator:
    """
    Main orchestrator that coordinates the entire fulfillment process
    
    This is the central component that manages the complete flow from
    AI understanding to executed actions.
    """
    
    def __init__(self, llm_engine=None, automation_client=None, asset_client=None, network_client=None):
        """Initialize the Fulfillment Orchestrator"""
        self.llm_engine = llm_engine
        self.automation_client = automation_client
        self.asset_client = asset_client
        self.network_client = network_client
        
        # Initialize all components
        self.intent_processor = IntentProcessor(llm_engine)
        self.resource_mapper = ResourceMapper(llm_engine)
        self.information_gatherer = InformationGatherer(asset_client, network_client, llm_engine)
        self.workflow_planner = WorkflowPlanner(llm_engine, asset_client)
        self.execution_coordinator = ExecutionCoordinator(automation_client)
        self.status_tracker = StatusTracker()
        
        # Active fulfillment tracking
        self.active_fulfillments: Dict[str, FulfillmentResult] = {}
        
        logger.info("Fulfillment Orchestrator initialized with all components")
    
    async def fulfill_intent(self, ai_understanding: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> FulfillmentResult:
        """
        Main fulfillment entry point
        
        Args:
            ai_understanding: AI understanding output from intent brain
            user_context: Optional user context information
            
        Returns:
            FulfillmentResult with execution status and details
        """
        fulfillment_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Create fulfillment request
        fulfillment_request = FulfillmentRequest(
            request_id=fulfillment_id,
            user_intent=ai_understanding.get("intent", "unknown"),
            user_message=ai_understanding.get("original_message", ""),
            context=user_context,
            user_id=user_context.get("user_id") if user_context else None,
            timestamp=start_time
        )
        
        # Initialize result tracking
        result = FulfillmentResult(
            request_id=fulfillment_id,
            status=FulfillmentStatus.PLANNING,
            start_time=start_time
        )
        
        self.active_fulfillments[fulfillment_id] = result
        
        try:
            logger.info(f"Starting fulfillment orchestration for request {fulfillment_id}")
            
            # Step 1: Process AI understanding into actionable intent
            result.status = FulfillmentStatus.PLANNING
            result.execution_logs.append("Processing AI understanding into actionable intent")
            
            # Add original message to ai_understanding for processing
            ai_understanding["original_message"] = fulfillment_request.user_message
            ai_understanding["user_context"] = user_context
            
            processed_intent = await self.intent_processor.process_intent(ai_understanding)
            result.execution_logs.append(f"Intent processed: {processed_intent.intent_type.value} with {processed_intent.confidence:.2f} confidence")
            
            # Step 2: Map intent to required resources
            result.execution_logs.append("Mapping intent to OpsConductor resources")
            resource_mapping = await self.resource_mapper.map_intent_to_resources(processed_intent)
            result.execution_logs.append(f"Resource mapping completed: {len(resource_mapping.requirements)} requirements identified")
            result.estimated_duration = resource_mapping.estimated_duration
            
            # Step 3: Gather missing information
            result.execution_logs.append("Gathering missing information")
            enriched_intent = await self.information_gatherer.gather_missing_information(processed_intent, resource_mapping)
            
            if not enriched_intent.information_complete:
                result.execution_logs.append(f"Missing information identified: {enriched_intent.missing_information}")
                # For now, continue with available information
                # In future, this could trigger user interaction for missing info
            
            # Step 4: Generate executable workflow
            result.execution_logs.append("Generating executable workflow")
            workflow = await self.workflow_planner.create_workflow(
                user_intent=fulfillment_request.user_intent,
                user_message=fulfillment_request.user_message,
                context={
                    "processed_intent": processed_intent,
                    "resource_mapping": resource_mapping,
                    "enriched_intent": enriched_intent
                }
            )
            
            if not workflow:
                result.status = FulfillmentStatus.FAILED
                result.error_message = "Failed to generate executable workflow"
                result.end_time = datetime.now()
                return result
            
            result.workflow_id = workflow.workflow_id
            result.total_steps = len(workflow.steps)
            result.execution_logs.append(f"Workflow generated with {result.total_steps} steps")
            
            # Step 5: Execute the workflow
            result.status = FulfillmentStatus.EXECUTING
            result.execution_logs.append("Starting workflow execution")
            
            execution_result = await self.execution_coordinator.execute_workflow(
                workflow=workflow,
                progress_callback=lambda step, total: self._update_progress(fulfillment_id, step, total)
            )
            
            # Step 6: Update final status
            if execution_result.success:
                result.status = FulfillmentStatus.COMPLETED
                result.execution_summary = execution_result.summary
                result.execution_logs.extend(execution_result.logs)
                result.execution_logs.append("Fulfillment completed successfully")
            else:
                result.status = FulfillmentStatus.FAILED
                result.error_message = execution_result.error_message
                result.execution_logs.extend(execution_result.logs)
                result.execution_logs.append(f"Fulfillment failed: {execution_result.error_message}")
            
            result.end_time = datetime.now()
            result.steps_completed = execution_result.steps_completed
            
            # Transfer job details from execution result
            if hasattr(execution_result, 'job_details') and execution_result.job_details:
                result.job_details = execution_result.job_details
            
            logger.info(f"Fulfillment orchestration completed for request {fulfillment_id}: {result.status.value}")
            
        except Exception as e:
            logger.error(f"Fulfillment orchestration failed for request {fulfillment_id}: {str(e)}")
            result.status = FulfillmentStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.execution_logs.append(f"Orchestration error: {str(e)}")
        
        return result
    
    async def get_fulfillment_status(self, fulfillment_id: str) -> Optional[FulfillmentResult]:
        """Get current status of a fulfillment request"""
        return self.active_fulfillments.get(fulfillment_id)
    
    async def cancel_fulfillment(self, fulfillment_id: str) -> bool:
        """Cancel an active fulfillment request"""
        if fulfillment_id not in self.active_fulfillments:
            return False
        
        result = self.active_fulfillments[fulfillment_id]
        
        if result.status in [FulfillmentStatus.COMPLETED, FulfillmentStatus.FAILED, FulfillmentStatus.CANCELLED]:
            return False  # Already finished
        
        # Cancel execution if running
        if result.workflow_id:
            await self.execution_coordinator.cancel_workflow(result.workflow_id)
        
        result.status = FulfillmentStatus.CANCELLED
        result.end_time = datetime.now()
        result.execution_logs.append("Fulfillment cancelled by user")
        
        logger.info(f"Fulfillment cancelled for request {fulfillment_id}")
        return True
    
    async def list_active_fulfillments(self) -> List[FulfillmentResult]:
        """List all active fulfillment requests"""
        return [
            result for result in self.active_fulfillments.values()
            if result.status not in [FulfillmentStatus.COMPLETED, FulfillmentStatus.FAILED, FulfillmentStatus.CANCELLED]
        ]
    
    def _update_progress(self, fulfillment_id: str, steps_completed: int, total_steps: int):
        """Update progress for a fulfillment request"""
        if fulfillment_id in self.active_fulfillments:
            result = self.active_fulfillments[fulfillment_id]
            result.steps_completed = steps_completed
            result.total_steps = total_steps
            
            progress_pct = (steps_completed / max(total_steps, 1)) * 100
            logger.debug(f"Fulfillment {fulfillment_id} progress: {progress_pct:.1f}% ({steps_completed}/{total_steps})")
    
    async def cleanup_completed_fulfillments(self, max_age_hours: int = 24):
        """Clean up old completed fulfillments"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for fulfillment_id, result in self.active_fulfillments.items():
            if (result.status in [FulfillmentStatus.COMPLETED, FulfillmentStatus.FAILED, FulfillmentStatus.CANCELLED] 
                and result.end_time 
                and result.end_time.timestamp() < cutoff_time):
                to_remove.append(fulfillment_id)
        
        for fulfillment_id in to_remove:
            del self.active_fulfillments[fulfillment_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old fulfillment requests")
    
    async def get_orchestrator_health(self) -> Dict[str, Any]:
        """Get health status of the fulfillment orchestrator"""
        active_count = len(await self.list_active_fulfillments())
        total_count = len(self.active_fulfillments)
        
        return {
            "orchestrator_id": "fulfillment_orchestrator",
            "status": "healthy",
            "active_fulfillments": active_count,
            "total_tracked_fulfillments": total_count,
            "components": {
                "intent_processor": "healthy",
                "resource_mapper": "healthy",
                "information_gatherer": "healthy",
                "workflow_planner": "healthy",
                "execution_coordinator": "healthy",
                "status_tracker": "healthy"
            },
            "services": {
                "llm_engine": "available" if self.llm_engine else "unavailable",
                "automation_client": "available" if self.automation_client else "unavailable",
                "asset_client": "available" if self.asset_client else "unavailable",
                "network_client": "available" if self.network_client else "unavailable"
            }
        }
    
    async def process_fulfillment_request(self, fulfillment_request: FulfillmentRequest) -> FulfillmentResult:
        """
        Process a fulfillment request (alternative entry point)
        
        Args:
            fulfillment_request: FulfillmentRequest object
            
        Returns:
            FulfillmentResult with execution status and details
        """
        # Convert fulfillment request to AI understanding format
        ai_understanding = {
            "intent": fulfillment_request.user_intent,
            "response": f"Processing request: {fulfillment_request.user_message}",
            "original_message": fulfillment_request.user_message,
            "conversation_id": fulfillment_request.request_id,
            "intent_classification": {
                "intent_type": "automation",  # Default to automation
                "confidence": 0.8,
                "method": "fulfillment_orchestrator",
                "alternatives": [],
                "entities": [],
                "context_analysis": {
                    "confidence_score": 0.8,
                    "risk_level": "MEDIUM",
                    "requirements_count": 1,
                    "recommendations": []
                },
                "reasoning": "Direct fulfillment request processing",
                "metadata": {
                    "engine": "fulfillment_orchestrator",
                    "success": True
                }
            }
        }
        
        return await self.fulfill_intent(ai_understanding, fulfillment_request.context)
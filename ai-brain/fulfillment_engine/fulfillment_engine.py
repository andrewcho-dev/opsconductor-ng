"""
Fulfillment Engine - Main Orchestrator

Coordinates the entire process of turning user intent into executed actions.
Works with the simplified IntentBrain architecture to provide seamless
intent-to-execution flow.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .workflow_planner import WorkflowPlanner
from .execution_coordinator import ExecutionCoordinator
from .status_tracker import StatusTracker

logger = logging.getLogger(__name__)


class FulfillmentStatus(Enum):
    """Fulfillment execution status"""
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FulfillmentRequest:
    """Request for fulfillment of user intent"""
    request_id: str
    user_intent: str
    user_message: str
    context: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, urgent
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class FulfillmentResult:
    """Result of fulfillment execution"""
    request_id: str
    status: FulfillmentStatus
    workflow_id: Optional[str] = None
    execution_summary: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_logs: List[str] = None
    
    def __post_init__(self):
        if self.execution_logs is None:
            self.execution_logs = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "workflow_id": self.workflow_id,
            "execution_summary": self.execution_summary,
            "steps_completed": self.steps_completed,
            "total_steps": self.total_steps,
            "progress_percentage": (self.steps_completed / max(self.total_steps, 1)) * 100,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            "error_message": self.error_message,
            "execution_logs": self.execution_logs
        }


class FulfillmentEngine:
    """
    Main Fulfillment Engine
    
    Orchestrates the complete process of turning user intent into executed actions.
    Designed to work seamlessly with the simplified IntentBrain architecture.
    """
    
    def __init__(self, llm_engine=None, automation_client=None, asset_client=None):
        """Initialize the Fulfillment Engine"""
        self.engine_id = "fulfillment_engine"
        self.version = "1.0.0"
        self.llm_engine = llm_engine
        self.automation_client = automation_client
        self.asset_client = asset_client
        
        # Initialize components
        self.workflow_planner = WorkflowPlanner(llm_engine, asset_client)
        self.execution_coordinator = ExecutionCoordinator(automation_client)
        self.status_tracker = StatusTracker()
        
        # Active fulfillment requests
        self.active_requests: Dict[str, FulfillmentResult] = {}
        
        logger.info(f"Fulfillment Engine v{self.version} initialized")
    
    async def fulfill_intent(self, request: FulfillmentRequest) -> FulfillmentResult:
        """
        Main method to fulfill user intent
        
        Args:
            request: FulfillmentRequest containing user intent and context
            
        Returns:
            FulfillmentResult with execution status and details
        """
        start_time = datetime.now()
        
        # Initialize result tracking
        result = FulfillmentResult(
            request_id=request.request_id,
            status=FulfillmentStatus.PLANNING,
            start_time=start_time
        )
        
        self.active_requests[request.request_id] = result
        
        try:
            logger.info(f"Starting fulfillment for request {request.request_id}: {request.user_intent}")
            
            # Step 1: Plan the workflow
            result.status = FulfillmentStatus.PLANNING
            result.execution_logs.append(f"Planning workflow for: {request.user_intent}")
            
            workflow = await self.workflow_planner.create_workflow(
                user_intent=request.user_intent,
                user_message=request.user_message,
                context=request.context
            )
            
            if not workflow:
                result.status = FulfillmentStatus.FAILED
                result.error_message = "Failed to create workflow from user intent"
                result.end_time = datetime.now()
                return result
            
            result.workflow_id = workflow.workflow_id
            result.total_steps = len(workflow.steps)
            result.execution_logs.append(f"Created workflow with {result.total_steps} steps")
            
            # Step 2: Execute the workflow
            result.status = FulfillmentStatus.EXECUTING
            result.execution_logs.append("Starting workflow execution")
            
            execution_result = await self.execution_coordinator.execute_workflow(
                workflow=workflow,
                progress_callback=lambda step, total: self._update_progress(request.request_id, step, total)
            )
            
            # Step 3: Update final status
            if execution_result.success:
                result.status = FulfillmentStatus.COMPLETED
                result.execution_summary = execution_result.summary
                result.execution_logs.extend(execution_result.logs)
            else:
                result.status = FulfillmentStatus.FAILED
                result.error_message = execution_result.error_message
                result.execution_logs.extend(execution_result.logs)
            
            result.end_time = datetime.now()
            result.steps_completed = execution_result.steps_completed
            
            logger.info(f"Fulfillment completed for request {request.request_id}: {result.status.value}")
            
        except Exception as e:
            logger.error(f"Fulfillment failed for request {request.request_id}: {str(e)}")
            result.status = FulfillmentStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.execution_logs.append(f"Error: {str(e)}")
        
        return result
    
    async def get_fulfillment_status(self, request_id: str) -> Optional[FulfillmentResult]:
        """Get current status of a fulfillment request"""
        return self.active_requests.get(request_id)
    
    async def cancel_fulfillment(self, request_id: str) -> bool:
        """Cancel an active fulfillment request"""
        if request_id not in self.active_requests:
            return False
        
        result = self.active_requests[request_id]
        
        if result.status in [FulfillmentStatus.COMPLETED, FulfillmentStatus.FAILED, FulfillmentStatus.CANCELLED]:
            return False  # Already finished
        
        # Cancel execution if running
        if result.workflow_id:
            await self.execution_coordinator.cancel_workflow(result.workflow_id)
        
        result.status = FulfillmentStatus.CANCELLED
        result.end_time = datetime.now()
        result.execution_logs.append("Fulfillment cancelled by user")
        
        logger.info(f"Fulfillment cancelled for request {request_id}")
        return True
    
    async def list_active_fulfillments(self) -> List[FulfillmentResult]:
        """List all active fulfillment requests"""
        return [
            result for result in self.active_requests.values()
            if result.status not in [FulfillmentStatus.COMPLETED, FulfillmentStatus.FAILED, FulfillmentStatus.CANCELLED]
        ]
    
    def _update_progress(self, request_id: str, steps_completed: int, total_steps: int):
        """Update progress for a fulfillment request"""
        if request_id in self.active_requests:
            result = self.active_requests[request_id]
            result.steps_completed = steps_completed
            result.total_steps = total_steps
            
            progress_pct = (steps_completed / max(total_steps, 1)) * 100
            logger.debug(f"Fulfillment {request_id} progress: {progress_pct:.1f}% ({steps_completed}/{total_steps})")
    
    async def cleanup_completed_requests(self, max_age_hours: int = 24):
        """Clean up old completed requests"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for request_id, result in self.active_requests.items():
            if (result.status in [FulfillmentStatus.COMPLETED, FulfillmentStatus.FAILED, FulfillmentStatus.CANCELLED] 
                and result.end_time 
                and result.end_time.timestamp() < cutoff_time):
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.active_requests[request_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old fulfillment requests")
    
    async def get_engine_health(self) -> Dict[str, Any]:
        """Get health status of the fulfillment engine"""
        active_count = len(await self.list_active_fulfillments())
        total_count = len(self.active_requests)
        
        return {
            "engine_id": self.engine_id,
            "version": self.version,
            "status": "healthy",
            "active_fulfillments": active_count,
            "total_tracked_requests": total_count,
            "components": {
                "workflow_planner": "healthy",
                "execution_coordinator": "healthy", 
                "status_tracker": "healthy"
            }
        }
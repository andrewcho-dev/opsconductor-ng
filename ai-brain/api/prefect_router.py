"""
OpsConductor AI Brain - Prefect API Router

This module provides REST API endpoints for Prefect integration,
allowing external services to interact with Prefect workflows.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from job_engine.workflow_generator import WorkflowGenerator
from job_engine.execution_router import ExecutionRouter, ExecutionEngine
from integrations.prefect_client import PrefectClient

logger = logging.getLogger(__name__)

# Create router
prefect_router = APIRouter(prefix="/prefect", tags=["prefect"])


# Pydantic models for API
class WorkflowRequest(BaseModel):
    """Request model for workflow creation"""
    intent_type: str = Field(..., description="Type of intent for the workflow")
    requirements: Dict[str, Any] = Field(..., description="Workflow requirements and parameters")
    target_systems: List[str] = Field(..., description="Target systems for execution")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ExecutionRequest(BaseModel):
    """Request model for workflow execution"""
    workflow_id: str = Field(..., description="ID of the workflow to execute")
    engine_preference: str = Field("auto", description="Preferred execution engine (auto, celery, prefect)")
    force_engine: bool = Field(False, description="Whether to force the preferred engine")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Execution parameters")


class FlowStatusResponse(BaseModel):
    """Response model for flow status"""
    execution_id: str
    flow_name: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    success: bool
    error_message: Optional[str]
    logs: List[str]


class ExecutionResponse(BaseModel):
    """Response model for workflow execution"""
    workflow_id: str
    engine_used: str
    success: bool
    execution_id: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    steps_completed: int
    total_steps: int
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    logs: List[str]


# Global instances
workflow_generator = None
execution_router = None
prefect_client = None


def get_workflow_generator():
    """Get or create workflow generator instance"""
    global workflow_generator
    if workflow_generator is None:
        workflow_generator = WorkflowGenerator()
    return workflow_generator


def get_execution_router():
    """Get or create execution router instance"""
    global execution_router
    if execution_router is None:
        execution_router = ExecutionRouter()
    return execution_router


def get_prefect_client():
    """Get or create Prefect client instance"""
    global prefect_client
    if prefect_client is None:
        prefect_client = PrefectClient()
    return prefect_client


@prefect_router.get("/health")
async def health_check():
    """Check Prefect integration health"""
    try:
        client = get_prefect_client()
        available = await client.is_available()
        
        return {
            "status": "healthy" if available else "degraded",
            "prefect_available": available,
            "integration_enabled": client.integration_enabled,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@prefect_router.get("/status")
async def get_integration_status():
    """Get detailed Prefect integration status"""
    try:
        client = get_prefect_client()
        router = get_execution_router()
        
        # Check service availability
        prefect_available = await client.is_available()
        
        # Get flow list if available
        flows = []
        if prefect_available:
            flows = await client.list_flows()
        
        return {
            "integration_enabled": client.integration_enabled,
            "prefect_server_available": prefect_available,
            "prefect_api_url": client.prefect_api_url,
            "flow_registry_url": client.flow_registry_url,
            "total_flows": len(flows),
            "flows": flows[:10],  # Limit to first 10 flows
            "execution_engines": [engine.value for engine in ExecutionEngine],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@prefect_router.post("/workflows/generate")
async def generate_workflow(request: WorkflowRequest):
    """Generate a new workflow"""
    try:
        generator = get_workflow_generator()
        
        workflow = generator.generate_workflow(
            intent_type=request.intent_type,
            requirements=request.requirements,
            target_systems=request.target_systems,
            context=request.context
        )
        
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "workflow_type": workflow.workflow_type.value,
            "target_systems": workflow.target_systems,
            "steps": len(workflow.steps),
            "estimated_duration": workflow.estimated_duration,
            "risk_level": workflow.risk_level,
            "requires_approval": workflow.requires_approval,
            "created_at": workflow.created_at.isoformat(),
            "tags": workflow.tags
        }
    except Exception as e:
        logger.error(f"Workflow generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow generation failed: {str(e)}")


@prefect_router.post("/workflows/execute")
async def execute_workflow(request: ExecutionRequest):
    """Execute a workflow using the execution router"""
    try:
        generator = get_workflow_generator()
        
        # For this endpoint, we need to generate the workflow first
        # In a real implementation, you might store workflows and retrieve by ID
        # For now, we'll return an error asking for workflow generation first
        
        raise HTTPException(
            status_code=400,
            detail="Direct workflow execution by ID not implemented. Use /workflows/generate-and-execute instead."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@prefect_router.post("/workflows/generate-and-execute", response_model=ExecutionResponse)
async def generate_and_execute_workflow(
    workflow_request: WorkflowRequest,
    engine_preference: str = "auto",
    force_engine: bool = False
):
    """Generate and execute a workflow in one step"""
    try:
        generator = get_workflow_generator()
        
        # Generate workflow
        workflow = generator.generate_workflow(
            intent_type=workflow_request.intent_type,
            requirements=workflow_request.requirements,
            target_systems=workflow_request.target_systems,
            context=workflow_request.context
        )
        
        # Execute workflow
        result = await generator.execute_workflow(
            workflow=workflow,
            engine_preference=engine_preference,
            force_engine=force_engine
        )
        
        # Convert to response model
        return ExecutionResponse(
            workflow_id=result["workflow_id"],
            engine_used=result["engine_used"],
            success=result["success"],
            execution_id=result.get("execution_id"),
            start_time=datetime.fromisoformat(result["start_time"]) if result.get("start_time") else None,
            end_time=datetime.fromisoformat(result["end_time"]) if result.get("end_time") else None,
            duration_seconds=result.get("duration_seconds"),
            steps_completed=result["steps_completed"],
            total_steps=result["total_steps"],
            result_data=result.get("result_data"),
            error_message=result.get("error_message"),
            logs=result["logs"]
        )
        
    except Exception as e:
        logger.error(f"Generate and execute failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generate and execute failed: {str(e)}")


@prefect_router.get("/executions/{execution_id}", response_model=FlowStatusResponse)
async def get_execution_status(execution_id: str, engine: str = "prefect"):
    """Get the status of a flow execution"""
    try:
        if engine.lower() == "prefect":
            client = get_prefect_client()
            
            async with client as c:
                execution = await c.get_flow_status(execution_id)
                
                return FlowStatusResponse(
                    execution_id=execution.execution_id,
                    flow_name=execution.flow_name,
                    status=execution.status.value,
                    start_time=execution.start_time,
                    end_time=execution.end_time,
                    duration_seconds=execution.duration_seconds,
                    success=execution.success,
                    error_message=execution.error_message,
                    logs=execution.logs
                )
        else:
            raise HTTPException(status_code=400, detail=f"Engine '{engine}' not supported for status queries")
            
    except Exception as e:
        logger.error(f"Failed to get execution status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")


@prefect_router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str, engine: str = "prefect"):
    """Cancel a running execution"""
    try:
        router = get_execution_router()
        
        engine_enum = ExecutionEngine.PREFECT if engine.lower() == "prefect" else ExecutionEngine.CELERY
        success = await router.cancel_execution(execution_id, engine_enum)
        
        return {
            "success": success,
            "execution_id": execution_id,
            "engine": engine,
            "message": "Cancellation requested" if success else "Cancellation failed"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")


@prefect_router.get("/flows")
async def list_flows():
    """List all available Prefect flows"""
    try:
        client = get_prefect_client()
        
        async with client as c:
            flows = await c.list_flows()
            
            return {
                "total_flows": len(flows),
                "flows": flows
            }
            
    except Exception as e:
        logger.error(f"Failed to list flows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list flows: {str(e)}")


@prefect_router.get("/engines")
async def get_available_engines():
    """Get information about available execution engines"""
    try:
        router = get_execution_router()
        client = get_prefect_client()
        
        prefect_available = await client.is_available()
        
        return {
            "engines": [
                {
                    "name": "auto",
                    "description": "Automatically choose the best engine based on workflow complexity",
                    "available": True
                },
                {
                    "name": "celery",
                    "description": "Traditional Celery-based execution for simple workflows",
                    "available": True
                },
                {
                    "name": "prefect",
                    "description": "Advanced Prefect-based execution for complex workflows",
                    "available": prefect_available
                }
            ],
            "default_engine": "auto",
            "prefect_integration_enabled": client.integration_enabled
        }
        
    except Exception as e:
        logger.error(f"Failed to get engine info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get engine info: {str(e)}")


# Background task for async execution
@prefect_router.post("/workflows/execute-async")
async def execute_workflow_async(
    background_tasks: BackgroundTasks,
    workflow_request: WorkflowRequest,
    engine_preference: str = "auto",
    force_engine: bool = False
):
    """Execute a workflow asynchronously in the background"""
    try:
        # Generate a unique execution ID
        import uuid
        execution_id = str(uuid.uuid4())
        
        # Add background task
        background_tasks.add_task(
            _execute_workflow_background,
            execution_id,
            workflow_request,
            engine_preference,
            force_engine
        )
        
        return {
            "execution_id": execution_id,
            "status": "queued",
            "message": "Workflow execution started in background",
            "check_status_url": f"/prefect/executions/{execution_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to queue async execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue async execution: {str(e)}")


async def _execute_workflow_background(
    execution_id: str,
    workflow_request: WorkflowRequest,
    engine_preference: str,
    force_engine: bool
):
    """Background task for workflow execution"""
    try:
        logger.info(f"Starting background execution: {execution_id}")
        
        generator = get_workflow_generator()
        
        # Generate workflow
        workflow = generator.generate_workflow(
            intent_type=workflow_request.intent_type,
            requirements=workflow_request.requirements,
            target_systems=workflow_request.target_systems,
            context=workflow_request.context
        )
        
        # Execute workflow
        result = await generator.execute_workflow(
            workflow=workflow,
            engine_preference=engine_preference,
            force_engine=force_engine
        )
        
        logger.info(f"Background execution completed: {execution_id} - Success: {result['success']}")
        
    except Exception as e:
        logger.error(f"Background execution failed: {execution_id} - {str(e)}")


# Export the router
__all__ = ["prefect_router"]
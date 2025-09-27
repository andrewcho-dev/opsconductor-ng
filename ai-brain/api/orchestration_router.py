"""
Orchestration API Router - Provides endpoints for AI Brain orchestration functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router
orchestration_router = APIRouter(prefix="/orchestration", tags=["orchestration"])

# Pydantic models for API
class ChatMessageRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: Optional[str] = None

class WorkflowRequest(BaseModel):
    workflow_name: str
    tasks: List[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None

class FlowExecutionRequest(BaseModel):
    flow_id: str
    parameters: Optional[Dict[str, Any]] = None
    wait_for_completion: bool = False

# Global reference to AI Brain service (will be set from main.py)
ai_brain_service = None
prefect_flow_engine = None

def get_ai_brain_service():
    """Dependency to get AI Brain service"""
    if ai_brain_service is None:
        raise HTTPException(status_code=503, detail="AI Brain service not initialized")
    return ai_brain_service

def get_prefect_flow_engine():
    """Dependency to get Prefect Flow Engine"""
    if prefect_flow_engine is None:
        raise HTTPException(status_code=503, detail="Prefect Flow Engine not initialized")
    return prefect_flow_engine

@orchestration_router.get("/health")
async def orchestration_health(
    service: Any = Depends(get_ai_brain_service)
):
    """Get orchestration service health status"""
    try:
        health_status = await service.health_check()
        return {
            "success": True,
            "data": health_status
        }
    except Exception as e:
        logger.error(f"Error getting orchestration health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@orchestration_router.post("/chat")
async def process_chat_message(
    request: ChatMessageRequest,
    service: Any = Depends(get_ai_brain_service)
):
    """Process a chat message through the AI Brain orchestration system"""
    try:
        logger.info(f"Processing chat message: {request.message[:100]}...")
        
        result = await service.process_chat_message(
            message=request.message,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@orchestration_router.post("/workflows/create")
async def create_dynamic_workflow(
    request: WorkflowRequest,
    engine: Any = Depends(get_prefect_flow_engine)
):
    """Create a dynamic Prefect workflow"""
    try:
        logger.info(f"Creating dynamic workflow: {request.workflow_name}")
        
        flow_id = await engine.create_dynamic_flow(
            flow_name=request.workflow_name,
            tasks=request.tasks,
            parameters=request.parameters
        )
        
        return {
            "success": True,
            "data": {
                "flow_id": flow_id,
                "workflow_name": request.workflow_name,
                "status": "created"
            }
        }
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@orchestration_router.post("/workflows/{flow_id}/deploy")
async def deploy_workflow(
    flow_id: str,
    deployment_name: Optional[str] = None,
    engine: Any = Depends(get_prefect_flow_engine)
):
    """Deploy a workflow to Prefect server"""
    try:
        logger.info(f"Deploying workflow: {flow_id}")
        
        deployment_id = await engine.deploy_flow(
            flow_id=flow_id,
            deployment_name=deployment_name
        )
        
        return {
            "success": True,
            "data": {
                "flow_id": flow_id,
                "deployment_id": deployment_id,
                "status": "deployed"
            }
        }
    except Exception as e:
        logger.error(f"Error deploying workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@orchestration_router.post("/workflows/execute")
async def execute_workflow(
    request: FlowExecutionRequest,
    engine: Any = Depends(get_prefect_flow_engine)
):
    """Execute a deployed workflow"""
    try:
        logger.info(f"Executing workflow: {request.flow_id}")
        
        flow_run_id = await engine.execute_flow(
            flow_id=request.flow_id,
            parameters=request.parameters
        )
        
        # Get initial status
        if request.wait_for_completion:
            # For now, just return the run ID - full waiting logic can be added later
            pass
        
        return {
            "success": True,
            "data": {
                "flow_id": request.flow_id,
                "flow_run_id": flow_run_id,
                "status": "started",
                "parameters": request.parameters
            }
        }
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@orchestration_router.get("/workflows/runs/{flow_run_id}/status")
async def get_workflow_run_status(
    flow_run_id: str,
    engine: Any = Depends(get_prefect_flow_engine)
):
    """Get the status of a workflow run"""
    try:
        logger.info(f"Getting workflow run status: {flow_run_id}")
        
        status = await engine.get_flow_run_status(flow_run_id)
        
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting workflow run status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@orchestration_router.get("/workflows/flows")
async def list_registered_flows(
    engine: Any = Depends(get_prefect_flow_engine)
):
    """List all registered flows"""
    try:
        flows = list(engine.registered_flows.keys())
        deployments = dict(engine.active_deployments)
        
        return {
            "success": True,
            "data": {
                "registered_flows": flows,
                "active_deployments": deployments,
                "total_flows": len(flows),
                "total_deployments": len(deployments)
            }
        }
    except Exception as e:
        logger.error(f"Error listing flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Function to set service references (called from main.py)
def set_orchestration_services(ai_brain_svc, prefect_engine):
    """Set references to orchestration services"""
    global ai_brain_service, prefect_flow_engine
    ai_brain_service = ai_brain_svc
    prefect_flow_engine = prefect_engine
    logger.info("Orchestration services set for API router")
"""
Modern AI Brain - Clean Prefect-First Architecture
Pure Prefect 3.0 implementation without legacy baggage.
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

# Add shared path
if os.path.exists('/app/shared'):
    sys.path.append('/app/shared')
else:
    sys.path.append('/home/opsconductor/opsconductor-ng/shared')

from base_service import BaseService

# Modern imports
from orchestration.ai_brain_service import AIBrainService, ChatResponse as ServiceChatResponse

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    user_id: str = Field(default="system", description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    intent_type: str
    confidence: float
    flow_id: Optional[str] = None
    run_id: Optional[str] = None
    execution_started: bool = False
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class FlowStatusResponse(BaseModel):
    run_id: str
    deployment_id: Optional[str] = None
    flow_name: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ActiveFlowsResponse(BaseModel):
    flows: List[Dict[str, Any]]
    total_count: int

class ModernAIService(BaseService):
    """Modern AI Service with clean Prefect-first architecture"""
    
    def __init__(self):
        super().__init__(
            name="ai-brain-modern",
            version="3.0.0-PREFECT-FIRST",
            port=3005
        )

# Initialize service
service = ModernAIService()
app = service.app

# Global AI Brain Service instance
ai_brain: Optional[AIBrainService] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the modern AI Brain Service"""
    global ai_brain
    
    try:
        logger.info("🚀 Starting Modern AI Brain Service")
        
        # Initialize AI Brain Service with environment variables
        ai_brain = AIBrainService(
            ollama_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
            asset_service_url=os.getenv("ASSET_SERVICE_URL", "http://asset-service:3001"),
            automation_service_url=os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3002"),
            network_analyzer_url=os.getenv("NETWORK_ANALYZER_URL", "http://network-analyzer:3003")
        )
        
        # Initialize the service
        await ai_brain.initialize()
        logger.info("✅ Modern AI Brain Service initialized successfully")
            
    except Exception as e:
        logger.error("❌ Startup failed", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global ai_brain
    
    try:
        logger.info("✅ Modern AI Brain Service shutdown completed")
    except Exception as e:
        logger.error("❌ Shutdown error", error=str(e))

# API Endpoints

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Modern chat endpoint with intelligent workflow orchestration
    """
    if not ai_brain:
        raise HTTPException(status_code=503, detail="AI Brain Service not initialized")
    
    try:
        logger.info("💬 Processing chat request", 
                   message=request.message[:100],
                   user_id=request.user_id)
        
        # Process the request using the new AI Brain Service
        ai_response = await ai_brain.process_message(
            message=request.message,
            user_id=request.user_id,
            context=request.context
        )
        
        # Convert to API response format
        return ChatResponse(
            message=ai_response.message,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            intent_type=ai_response.intent_type.value,
            confidence=0.95,  # Default confidence
            flow_id=ai_response.flow_created,
            run_id=ai_response.execution_id,
            execution_started=bool(ai_response.execution_id),
            artifacts=ai_response.artifacts
        )
        
    except Exception as e:
        logger.error("❌ Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/flows/status/{run_id}", response_model=FlowStatusResponse)
async def get_flow_status(run_id: str) -> FlowStatusResponse:
    """Get the status of a specific flow run"""
    if not ai_brain:
        raise HTTPException(status_code=503, detail="AI Brain Service not initialized")
    
    try:
        execution = await ai_brain.flow_engine.get_flow_status(run_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail=f"Flow run {run_id} not found")
        
        return FlowStatusResponse(
            run_id=execution.flow_run_id,
            deployment_id=None,  # Not used in our architecture
            flow_name=execution.flow_name,
            status=execution.status,
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            parameters={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get flow status", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get flow status: {str(e)}")

@app.get("/flows/active", response_model=ActiveFlowsResponse)
async def list_active_flows() -> ActiveFlowsResponse:
    """List all active flows"""
    if not ai_brain:
        raise HTTPException(status_code=503, detail="AI Brain Service not initialized")
    
    try:
        # Get all generated flows
        flows = await ai_brain.flow_engine.list_flows()
        
        # Convert to API format
        flow_data = []
        for flow in flows:
            flow_data.append({
                "name": flow.name,
                "description": flow.description,
                "flow_type": flow.flow_type.value,
                "task_count": len(flow.tasks),
                "tags": flow.tags
            })
        
        return ActiveFlowsResponse(
            flows=flow_data,
            total_count=len(flow_data)
        )
        
    except Exception as e:
        logger.error("❌ Failed to list active flows", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list flows: {str(e)}")

@app.post("/flows/cancel/{run_id}")
async def cancel_flow(run_id: str) -> Dict[str, Any]:
    """Cancel a running flow"""
    if not ai_brain:
        raise HTTPException(status_code=503, detail="AI Brain Service not initialized")
    
    try:
        # Check if flow exists
        execution = await ai_brain.flow_engine.get_flow_status(run_id)
        
        if not execution:
            return {
                "success": False,
                "run_id": run_id,
                "message": "Flow not found"
            }
        
        # For now, just mark as cancelled (in production, would use Prefect API)
        execution.status = "CANCELLED"
        
        return {
            "success": True,
            "run_id": run_id,
            "message": "Flow cancellation requested"
        }
        
    except Exception as e:
        logger.error("❌ Failed to cancel flow", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cancel flow: {str(e)}")

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-brain-modern",
        "version": "3.0.0-PREFECT-FIRST",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_brain_initialized": ai_brain is not None
    }

@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get AI Brain capabilities"""
    return {
        "orchestration_engine": "Prefect 3.0",
        "flow_types": [
            "infrastructure",
            "automation", 
            "monitoring",
            "deployment",
            "analysis",
            "remediation"
        ],
        "features": [
            "Natural language to workflow conversion",
            "Intelligent intent analysis",
            "Real-time flow execution",
            "Advanced observability",
            "Conversation context tracking",
            "Dynamic flow generation"
        ],
        "integrations": [
            "Asset Service",
            "Automation Service", 
            "Network Analyzer",
            "LLM Engine (Ollama)"
        ]
    }

# Legacy compatibility endpoint (minimal)
@app.post("/process")
async def legacy_process_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy compatibility endpoint - converts to modern format
    """
    logger.warning("⚠️ Legacy endpoint used - consider migrating to /chat")
    
    # Convert legacy format to modern
    message = request.get("message", "")
    user_id = request.get("user_id", "legacy_user")
    
    chat_request = ChatRequest(
        message=message,
        user_id=user_id,
        context={"legacy_request": True}
    )
    
    response = await chat_endpoint(chat_request)
    
    # Convert back to legacy format
    return {
        "response": response.message,
        "conversation_id": response.conversation_id,
        "intent": response.intent_type,
        "confidence": response.confidence,
        "job_id": response.flow_id,
        "execution_id": response.run_id,
        "execution_started": response.execution_started,
        "timestamp": response.timestamp,
        "_modern_migration_notice": "This endpoint is deprecated. Please use /chat for full functionality."
    }

if __name__ == "__main__":
    # Run the modern AI Brain service
    uvicorn.run(
        "main_modern:app",
        host="0.0.0.0",
        port=3005,
        reload=False,
        log_level="info"
    )
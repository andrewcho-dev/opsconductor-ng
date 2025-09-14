from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import sys
sys.path.append('/app/shared')
from base_service import BaseService
from nlp_processor import SimpleNLPProcessor
from workflow_generator import WorkflowGenerator
from asset_client import AssetServiceClient
from automation_client import AutomationServiceClient

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

class AIService(BaseService):
    def __init__(self):
        super().__init__("ai-service")
        
app = FastAPI(
    title="OpsConductor AI Service",
    description="AI-powered automation and natural language processing service",
    version="1.0.0"
)

# Initialize service components
service = AIService()
nlp_processor = SimpleNLPProcessor()
workflow_generator = WorkflowGenerator()
asset_client = AssetServiceClient(os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002"))
automation_client = AutomationServiceClient(os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003"))

class JobRequest(BaseModel):
    description: str
    user_id: Optional[int] = None
    priority: str = "normal"

class JobResponse(BaseModel):
    job_id: str
    workflow: Dict[str, Any]
    message: str
    confidence: float
    parsed_request: Dict[str, Any]

class TextAnalysisRequest(BaseModel):
    text: str

class TextAnalysisResponse(BaseModel):
    text: str
    parsed_request: Dict[str, Any]
    entities: Dict[str, List[str]]
    confidence: float
    suggestions: List[str]

class ExecuteJobRequest(BaseModel):
    description: str
    execute_immediately: bool = True
    user_id: Optional[int] = None

class ExecuteJobResponse(BaseModel):
    job_id: str
    execution_id: Optional[str] = None
    task_id: Optional[str] = None
    workflow: Dict[str, Any]
    message: str
    confidence: float
    execution_started: bool
    automation_job_id: Optional[int] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "ai-service",
        "version": "1.0.0",
        "description": "AI-powered automation service",
        "capabilities": [
            "Natural language processing",
            "Workflow generation",
            "Intent recognition",
            "Task automation",
            "Asset service integration"
        ],
        "supported_operations": [
            "update", "restart", "stop", "start", "check", "install"
        ],
        "supported_os": [
            "windows", "linux"
        ],
        "automation_integration": True
    }

@app.post("/ai/create-job", response_model=JobResponse)
async def create_job(request: JobRequest):
    """Create a new automation job from natural language description"""
    try:
        logger.info("Processing job creation request", description=request.description)
        
        # Step 1: Parse the natural language request
        parsed_request = nlp_processor.parse_request(request.description)
        logger.info("Parsed request", 
                   operation=parsed_request.operation,
                   target_process=parsed_request.target_process,
                   target_group=parsed_request.target_group,
                   confidence=parsed_request.confidence)
        
        # Step 2: Resolve target groups to actual targets
        target_groups = []
        if parsed_request.target_group:
            targets = await asset_client.resolve_target_group(parsed_request.target_group)
            if not targets:
                # Use mock data for demo
                targets = await asset_client.create_mock_targets_for_demo(parsed_request.target_group)
            
            if targets:
                target_groups = [parsed_request.target_group]
                logger.info(f"Resolved target group '{parsed_request.target_group}' to {len(targets)} targets")
            else:
                logger.warning(f"No targets found for group '{parsed_request.target_group}'")
        
        # Step 3: Generate workflow
        workflow = workflow_generator.generate_workflow(parsed_request, target_groups)
        logger.info("Generated workflow", workflow_id=workflow['id'], steps=len(workflow['steps']))
        
        # Step 4: Create job ID
        job_id = str(uuid.uuid4())
        
        # Step 5: Prepare response
        message = f"Successfully created workflow for: {request.description}"
        if parsed_request.confidence < 0.5:
            message += f" (Low confidence: {parsed_request.confidence:.2f} - please verify)"
        
        return JobResponse(
            job_id=job_id,
            workflow=workflow,
            message=message,
            confidence=parsed_request.confidence,
            parsed_request={
                "operation": parsed_request.operation,
                "target_process": parsed_request.target_process,
                "target_service": parsed_request.target_service,
                "target_group": parsed_request.target_group,
                "target_os": parsed_request.target_os,
                "raw_text": parsed_request.raw_text
            }
        )
        
    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/ai/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """Analyze text for automation intent"""
    try:
        logger.info("Analyzing text", text=request.text)
        
        # Parse the request
        parsed_request = nlp_processor.parse_request(request.text)
        
        # Extract all entities for debugging
        entities = nlp_processor.extract_entities(request.text)
        
        # Generate suggestions
        suggestions = []
        if parsed_request.confidence < 0.5:
            suggestions.append("Consider being more specific about the target group")
            suggestions.append("Specify the exact process or service name")
            
        if not parsed_request.target_group:
            suggestions.append("Add a target group (e.g., 'on CIS servers', 'on web servers')")
            
        if parsed_request.operation == "unknown":
            suggestions.append("Specify the operation (update, restart, stop, start, check)")
        
        return TextAnalysisResponse(
            text=request.text,
            parsed_request={
                "operation": parsed_request.operation,
                "target_process": parsed_request.target_process,
                "target_service": parsed_request.target_service,
                "target_group": parsed_request.target_group,
                "target_os": parsed_request.target_os,
                "confidence": parsed_request.confidence
            },
            entities=entities,
            confidence=parsed_request.confidence,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error("Failed to analyze text", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to analyze text: {str(e)}")

@app.post("/ai/execute-job", response_model=ExecuteJobResponse)
async def execute_job(request: ExecuteJobRequest):
    """Create and execute a job immediately"""
    try:
        logger.info("Processing job execution request", 
                   description=request.description,
                   execute_immediately=request.execute_immediately)
        
        # Step 1: Parse the natural language request
        parsed_request = nlp_processor.parse_request(request.description)
        logger.info("Parsed execution request", 
                   operation=parsed_request.operation,
                   target_process=parsed_request.target_process,
                   target_group=parsed_request.target_group,
                   confidence=parsed_request.confidence)
        
        # Step 2: Resolve target groups to actual targets
        target_groups = []
        if parsed_request.target_group:
            targets = await asset_client.resolve_target_group(parsed_request.target_group)
            if not targets:
                # Use mock data for demo
                targets = await asset_client.create_mock_targets_for_demo(parsed_request.target_group)
            
            if targets:
                target_groups = [parsed_request.target_group]
                logger.info(f"Resolved target group '{parsed_request.target_group}' to {len(targets)} targets")
            else:
                logger.warning(f"No targets found for group '{parsed_request.target_group}'")
        
        # Step 3: Generate workflow
        workflow = workflow_generator.generate_workflow(parsed_request, target_groups)
        logger.info("Generated workflow for execution", 
                   workflow_id=workflow['id'], 
                   steps=len(workflow['steps']))
        
        # Step 4: Create job ID
        job_id = str(uuid.uuid4())
        
        # Step 5: Submit to automation service if requested
        execution_started = False
        automation_job_id = None
        execution_id = None
        task_id = None
        
        if request.execute_immediately:
            try:
                # Check automation service health
                automation_healthy = await automation_client.health_check()
                if not automation_healthy:
                    logger.warning("Automation service not healthy, skipping execution")
                    message = f"Workflow created but automation service unavailable for execution"
                else:
                    # Submit workflow to automation service
                    submission_result = await automation_client.submit_ai_workflow(
                        workflow, 
                        job_name=f"AI: {request.description[:50]}..."
                    )
                    
                    if submission_result.get('success'):
                        execution_started = True
                        automation_job_id = submission_result.get('job_id')
                        execution_id = submission_result.get('execution_id')
                        task_id = submission_result.get('task_id')
                        
                        logger.info("Workflow submitted to automation service",
                                   automation_job_id=automation_job_id,
                                   execution_id=execution_id)
                        
                        message = f"Workflow created and execution started (Job ID: {automation_job_id})"
                    else:
                        logger.error("Failed to submit workflow to automation service",
                                    error=submission_result.get('error'))
                        message = f"Workflow created but execution failed: {submission_result.get('error')}"
                        
            except Exception as e:
                logger.error("Failed to submit workflow for execution", error=str(e))
                message = f"Workflow created but execution failed: {str(e)}"
        else:
            message = f"Workflow created successfully (execution not requested)"
        
        # Add confidence warning if needed
        if parsed_request.confidence < 0.5:
            message += f" (Low confidence: {parsed_request.confidence:.2f} - please verify)"
        
        return ExecuteJobResponse(
            job_id=job_id,
            execution_id=execution_id,
            task_id=task_id,
            workflow=workflow,
            message=message,
            confidence=parsed_request.confidence,
            execution_started=execution_started,
            automation_job_id=automation_job_id
        )
        
    except Exception as e:
        logger.error("Failed to execute job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute job: {str(e)}")

@app.get("/ai/test-nlp")
async def test_nlp():
    """Test endpoint for NLP functionality"""
    test_requests = [
        "update stationcontroller on CIS servers",
        "restart nginx on web servers",
        "stop Apache service on all servers",
        "check status of IIS on production servers"
    ]
    
    results = []
    for test_text in test_requests:
        parsed = nlp_processor.parse_request(test_text)
        entities = nlp_processor.extract_entities(test_text)
        
        results.append({
            "input": test_text,
            "parsed": {
                "operation": parsed.operation,
                "target_process": parsed.target_process,
                "target_service": parsed.target_service,
                "target_group": parsed.target_group,
                "target_os": parsed.target_os,
                "confidence": parsed.confidence
            },
            "entities": entities
        })
    
    return {"test_results": results}

@app.get("/ai/test-workflow")
async def test_workflow():
    """Test endpoint for workflow generation"""
    test_request = "update stationcontroller on CIS servers"
    parsed = nlp_processor.parse_request(test_request)
    workflow = workflow_generator.generate_workflow(parsed, ["CIS"])
    
    return {
        "input": test_request,
        "parsed": {
            "operation": parsed.operation,
            "target_process": parsed.target_process,
            "target_group": parsed.target_group,
            "confidence": parsed.confidence
        },
        "workflow": workflow
    }

@app.get("/ai/test-assets")
async def test_assets():
    """Test endpoint for asset service integration"""
    try:
        # Test health check
        healthy = await asset_client.health_check()
        
        # Test group resolution
        test_groups = ["CIS servers", "web servers"]
        group_results = {}
        
        for group_name in test_groups:
            targets = await asset_client.resolve_target_group(group_name)
            if not targets:
                targets = await asset_client.create_mock_targets_for_demo(group_name)
            group_results[group_name] = {
                "target_count": len(targets),
                "targets": [{"hostname": t.get("hostname"), "os_type": t.get("os_type")} for t in targets]
            }
        
        return {
            "asset_service_healthy": healthy,
            "group_resolution": group_results
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "asset_service_healthy": False
        }

@app.get("/ai/test-automation")
async def test_automation():
    """Test endpoint for automation service integration"""
    try:
        # Test health check
        healthy = await automation_client.health_check()
        
        # Get client info
        client_info = automation_client.get_client_info()
        
        # List AI jobs
        ai_jobs = await automation_client.list_ai_jobs(limit=5)
        
        return {
            "automation_service_healthy": healthy,
            "client_info": client_info,
            "ai_jobs_count": len(ai_jobs),
            "recent_ai_jobs": [
                {
                    "id": job.get("id"),
                    "name": job.get("name"),
                    "created_at": job.get("created_at"),
                    "job_type": job.get("job_type")
                } for job in ai_jobs[:3]
            ]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "automation_service_healthy": False
        }

@app.get("/ai/test-integration")
async def test_integration():
    """Test full AI to Automation integration"""
    try:
        test_request = "check status of nginx on web servers"
        
        logger.info("Testing full integration", request=test_request)
        
        # Step 1: Test AI processing
        parsed = nlp_processor.parse_request(test_request)
        workflow = workflow_generator.generate_workflow(parsed, ["web servers"])
        
        # Step 2: Test automation service health
        automation_healthy = await automation_client.health_check()
        
        # Step 3: Test asset service
        asset_healthy = await asset_client.health_check()
        
        result = {
            "test_request": test_request,
            "ai_processing": {
                "parsed_operation": parsed.operation,
                "parsed_target": parsed.target_process,
                "parsed_group": parsed.target_group,
                "confidence": parsed.confidence,
                "workflow_steps": len(workflow.get('steps', []))
            },
            "service_health": {
                "automation_service": automation_healthy,
                "asset_service": asset_healthy
            },
            "integration_ready": automation_healthy and asset_healthy,
            "workflow_preview": {
                "id": workflow.get('id'),
                "name": workflow.get('name'),
                "description": workflow.get('description'),
                "step_count": len(workflow.get('steps', []))
            }
        }
        
        # Step 4: If services are healthy, test actual submission (without execution)
        if automation_healthy:
            try:
                submission_result = await automation_client.submit_ai_workflow(
                    workflow, 
                    job_name=f"Integration Test: {test_request}"
                )
                result["test_submission"] = {
                    "success": submission_result.get('success'),
                    "job_id": submission_result.get('job_id'),
                    "message": submission_result.get('message', submission_result.get('error'))
                }
            except Exception as e:
                result["test_submission"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return result
        
    except Exception as e:
        logger.error("Integration test failed", error=str(e))
        return {
            "error": str(e),
            "integration_ready": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
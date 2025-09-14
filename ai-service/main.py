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
        ]
    }

@app.post("/create-job", response_model=JobResponse)
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

@app.post("/analyze-text", response_model=TextAnalysisResponse)
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

@app.get("/test-nlp")
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

@app.get("/test-workflow")
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

@app.get("/test-assets")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
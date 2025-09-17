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
from ai_engine import ai_engine
from learning_api import learning_router
from predictive_analytics import predictive_analytics

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
    description="AI-powered automation and natural language processing service with advanced learning capabilities",
    version="1.0.0"
)

# Include learning API routes
app.include_router(learning_router)

# Initialize service components
service = AIService()
nlp_processor = SimpleNLPProcessor()
workflow_generator = WorkflowGenerator()
asset_client = AssetServiceClient(os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002"))
automation_client = AutomationServiceClient(os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003"))

@app.on_event("startup")
async def startup_event():
    """Initialize AI engine on startup"""
    logger.info("Initializing AI engine...")
    try:
        success = await ai_engine.initialize()
        if success:
            logger.info("AI engine initialized successfully")
        else:
            logger.error("Failed to initialize AI engine")
    except Exception as e:
        logger.error(f"Exception during AI engine initialization: {e}")

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

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    intent: str  # "question", "job_creation", "unknown"
    confidence: float
    job_id: Optional[str] = None
    execution_id: Optional[str] = None
    automation_job_id: Optional[int] = None
    workflow: Optional[Dict[str, Any]] = None
    execution_started: bool = False

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
        "version": "2.0.0",
        "description": "Complete AI-powered automation service with protocol integration",
        "capabilities": [
            "Natural language processing",
            "Vector-powered knowledge base",
            "Multi-protocol support (SNMP, SMTP, SSH, VAPIX)",
            "Script generation (PowerShell, Bash, Python)",
            "Intent recognition and context awareness",
            "Real-time system queries",
            "Continuous learning from interactions"
        ],
        "supported_protocols": [
            "SNMP - Network device monitoring",
            "SMTP - Email notifications and alerts",
            "SSH - Remote command execution",
            "VAPIX - Axis camera integration"
        ],
        "supported_operations": [
            "Network monitoring", "Email alerts", "Remote execution", 
            "Camera management", "Script generation", "System queries"
        ],
        "ai_features": [
            "Ollama LLM integration", "ChromaDB vector storage", 
            "Semantic search", "Learning system"
        ],
        "automation_integration": True
    }

@app.post("/ai/chat")
async def chat_endpoint(request: ChatRequest):
    """Enhanced chat interface with complete AI engine"""
    try:
        logger.info("Processing chat request", message=request.message)
        user_id = str(request.user_id) if request.user_id else "system"
        response = await ai_engine.process_message(request.message, user_id)
        
        # Convert to expected ChatResponse format
        return ChatResponse(
            response=response.get("response", ""),
            intent=response.get("intent", "unknown"),
            confidence=0.8,  # Default confidence
            job_id=response.get("data", {}).get("job_id"),
            execution_id=response.get("data", {}).get("execution_id"),
            automation_job_id=response.get("data", {}).get("automation_job_id"),
            workflow=response.get("data", {}).get("workflow"),
            execution_started=response.get("success", False)
        )
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# System queries and script generation are now handled through the main chat interface

@app.get("/ai/knowledge-stats")
async def get_knowledge_stats():
    """Get AI knowledge base statistics"""
    try:
        stats = await ai_engine.get_knowledge_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get knowledge stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/ai/store-knowledge")
async def store_knowledge_endpoint(request: dict):
    """Store new knowledge in the AI system"""
    try:
        content = request.get("content", "")
        category = request.get("category", "general")
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        success = await ai_engine.store_knowledge(content, category)
        
        if success:
            return {
                "status": "success",
                "message": f"Knowledge stored successfully in category '{category}'"
            }
        else:
            raise HTTPException(status_code=503, detail="Failed to store knowledge")
            
    except Exception as e:
        logger.error("Failed to store knowledge", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store knowledge: {str(e)}")

@app.post("/ai/protocol/execute")
async def execute_protocol_operation(request: dict):
    """Execute operation using specified protocol"""
    try:
        protocol = request.get("protocol", "")
        target = request.get("target", {})
        command = request.get("command", "")
        credentials = request.get("credentials", {})
        kwargs = request.get("parameters", {})
        
        if not protocol or not target or not command:
            raise HTTPException(status_code=400, detail="Protocol, target, and command are required")
        
        logger.info("Executing protocol operation", 
                   protocol=protocol, 
                   target=target.get("hostname", "unknown"),
                   command=command)
        
        result = await ai_engine.execute_protocol_command(
            protocol, target, command, credentials, **kwargs
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error("Protocol operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Protocol operation failed: {str(e)}")

# Protocol-specific operations are now handled through the main chat interface and /ai/protocol/execute endpoint

@app.get("/ai/protocols/capabilities")
async def get_protocol_capabilities():
    """Get all supported protocol capabilities"""
    try:
        status = await ai_engine.get_protocol_status()
        return status
        
    except Exception as e:
        logger.error("Failed to get protocol capabilities", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

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

def classify_intent(message: str) -> tuple[str, float]:
    """Classify user message intent"""
    message_lower = message.lower().strip()
    
    # Question patterns
    question_patterns = [
        'what', 'how', 'when', 'where', 'why', 'who', 'which',
        'status', 'show', 'list', 'display', 'tell me', 'get',
        'how many', 'what is', 'what are', 'how much'
    ]
    
    # Job creation patterns  
    job_patterns = [
        'restart', 'stop', 'start', 'update', 'install', 'remove',
        'deploy', 'configure', 'run', 'execute', 'kill', 'reboot',
        'upgrade', 'downgrade', 'backup', 'restore'
    ]
    
    # Check for question patterns
    for pattern in question_patterns:
        if pattern in message_lower:
            return "question", 0.8
    
    # Check for job patterns
    for pattern in job_patterns:
        if pattern in message_lower:
            return "job_creation", 0.9
    
    # Check if it ends with question mark
    if message.strip().endswith('?'):
        return "question", 0.7
    
    return "unknown", 0.3

async def handle_question(message: str) -> str:
    """Handle informational questions"""
    message_lower = message.lower()
    
    # Status-related questions
    if any(word in message_lower for word in ['status', 'health', 'running', 'up', 'down']):
        if any(word in message_lower for word in ['worker', 'job', 'task']):
            return "I can see the system status through the monitoring dashboard. Currently, there are 24 worker processes running across 2 containers, ready to handle automation tasks. You can check the detailed status in the Job Monitoring section."
        elif any(word in message_lower for word in ['server', 'system', 'service']):
            return "To check server status, I would need to run a status check job. Would you like me to create a job to check the status of specific servers or services?"
    
    # Count/list questions
    elif any(word in message_lower for word in ['how many', 'count', 'list', 'show']):
        if any(word in message_lower for word in ['worker', 'job', 'task']):
            return "Currently there are 24 worker processes running across 2 containers. You can see detailed worker information and active tasks in the Job Monitoring dashboard."
        elif any(word in message_lower for word in ['server', 'asset']):
            return "I can help you get a list of servers or assets. Would you like me to create a job to inventory your infrastructure?"
    
    # Help questions
    elif any(word in message_lower for word in ['help', 'what can you do', 'capabilities']):
        return """I can help you with:

**Automation Tasks:**
- Restart services: "restart nginx on web servers"
- Update software: "update stationcontroller on CIS servers" 
- System operations: "stop Apache on production servers"

**Information:**
- System status and monitoring
- Worker and job statistics
- Infrastructure inventory

**Questions:**
- Ask about server status, running services, or system health
- Get help with automation commands

Try asking me to perform a specific task or check on something!"""
    
    # Default response for questions
    return f"I understand you're asking about: '{message}'. I can help with system automation and monitoring. For specific server information, I may need to create a monitoring job. Would you like me to help you with a specific automation task instead?"



# Predictive Analytics Endpoints
@app.get("/ai/predictive/insights")
async def get_predictive_insights():
    """Get comprehensive predictive insights"""
    try:
        insights = await predictive_analytics.get_predictive_insights()
        return {
            "success": True,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get predictive insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/predictive/analyze-performance")
async def analyze_performance(metrics: Dict[str, float]):
    """Analyze system performance and generate insights"""
    try:
        insights = await predictive_analytics.analyze_system_performance(metrics)
        return {
            "success": True,
            "performance_insights": [insight.to_dict() for insight in insights],
            "analysis_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/predictive/detect-anomalies")
async def detect_anomalies(request: Dict[str, Any]):
    """Detect advanced anomalies in system behavior"""
    try:
        metrics = request.get("metrics", {})
        execution_data = request.get("execution_data", {})
        
        anomalies = await predictive_analytics.detect_advanced_anomalies(metrics, execution_data)
        return {
            "success": True,
            "anomalies": anomalies,
            "count": len(anomalies),
            "detection_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/predictive/maintenance-schedule")
async def get_maintenance_schedule():
    """Get predictive maintenance recommendations"""
    try:
        # Get targets from asset service (simplified for demo)
        targets = [
            {"hostname": "server-01", "type": "server", "last_maintenance": "2024-01-01T00:00:00"},
            {"hostname": "server-02", "type": "server", "last_maintenance": "2024-02-01T00:00:00"},
            {"hostname": "switch-01", "type": "network_device", "last_maintenance": "2024-03-01T00:00:00"}
        ]
        
        recommendations = await predictive_analytics.generate_maintenance_schedule(targets)
        return {
            "success": True,
            "maintenance_recommendations": [rec.to_dict() for rec in recommendations],
            "count": len(recommendations),
            "generated_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get maintenance schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/predictive/security-monitor")
async def monitor_security(log_entries: List[Dict[str, Any]]):
    """Monitor log entries for security events"""
    try:
        alerts = await predictive_analytics.monitor_security_events(log_entries)
        return {
            "success": True,
            "security_alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts),
            "analysis_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to monitor security: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)
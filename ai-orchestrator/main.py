from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import os
import sys
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

# Add shared directory to path
sys.path.append('/app/shared')
from base_service import BaseService

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

class AIOrchestrator(BaseService):
    def __init__(self):
        super().__init__("ai-orchestrator")

app = FastAPI(
    title="OpsConductor AI Orchestrator",
    description="AI service orchestrator that coordinates NLP, Vector, and LLM services",
    version="1.0.0"
)

# Initialize service
service = AIOrchestrator()

@app.on_event("startup")
async def startup_event():
    """Initialize knowledge base on startup"""
    try:
        logger.info("Initializing OpsConductor knowledge base...")
        success = await knowledge_manager.initialize_knowledge_base()
        if success:
            logger.info("Knowledge base initialized successfully")
        else:
            logger.error("Failed to initialize knowledge base")
    except Exception as e:
        logger.error("Knowledge base initialization failed", error=str(e))

# Service URLs
NLP_SERVICE_URL = os.getenv("NLP_SERVICE_URL", "http://nlp-service:3000")
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://vector-service:3000")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:3000")
ASSET_SERVICE_URL = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
AUTOMATION_SERVICE_URL = os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")

# Import local modules
from orchestrator import AIServiceOrchestrator
from workflow_generator import WorkflowGenerator
from protocol_manager import ProtocolManager
from knowledge_manager import KnowledgeManager

# Initialize components
orchestrator = AIServiceOrchestrator(NLP_SERVICE_URL, VECTOR_SERVICE_URL, LLM_SERVICE_URL)
workflow_generator = WorkflowGenerator()
protocol_manager = ProtocolManager()
knowledge_manager = KnowledgeManager("http://api-gateway:3000", VECTOR_SERVICE_URL)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    job_id: Optional[str] = None
    execution_id: Optional[str] = None
    automation_job_id: Optional[int] = None
    workflow: Optional[Dict[str, Any]] = None
    execution_started: bool = False

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
        "service": "ai-orchestrator",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "ai-orchestrator",
        "version": "1.0.0",
        "description": "AI service orchestrator coordinating NLP, Vector, and LLM services",
        "capabilities": [
            "Chat interface coordination",
            "Job creation and execution",
            "Protocol operations",
            "Service orchestration"
        ],
        "connected_services": {
            "nlp_service": NLP_SERVICE_URL,
            "vector_service": VECTOR_SERVICE_URL,
            "llm_service": LLM_SERVICE_URL,
            "asset_service": ASSET_SERVICE_URL,
            "automation_service": AUTOMATION_SERVICE_URL
        }
    }

@app.post("/ai/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat interface that orchestrates all AI services"""
    try:
        logger.info("Processing chat request", message=request.message)
        
        # Step 1: Classify intent using NLP service
        async with httpx.AsyncClient() as client:
            nlp_response = await client.post(
                f"{NLP_SERVICE_URL}/nlp/classify",
                json={"text": request.message}
            )
            intent_data = nlp_response.json()
        
        intent = intent_data.get("intent", "unknown")
        confidence = intent_data.get("confidence", 0.5)
        
        logger.info("Intent classified", intent=intent, confidence=confidence)
        
        # Step 2: Use intelligent analysis to determine if this is a system information query
        # Parse the request to get NLP data for analysis
        async with httpx.AsyncClient() as client:
            parse_response = await client.post(
                f"{NLP_SERVICE_URL}/nlp/parse",
                json={"text": request.message}
            )
            parsed_data = parse_response.json()
        
        # Use our intelligent analysis to determine routing
        is_system_query = await _is_system_information_query(request.message, parsed_data)
        
        logger.info("Intelligent routing analysis", 
                   original_intent=intent, 
                   is_system_query=is_system_query,
                   message=request.message)
        
        # Route based on intelligent analysis first, then fall back to NLP intent
        if is_system_query:
            # Use knowledge manager for system information queries
            logger.info("Routing to knowledge manager based on intelligent analysis")
            return await handle_query_request(request, confidence)
        elif intent == "automation":
            # Create and potentially execute job
            return await handle_automation_request(request, confidence)
        elif intent == "question":
            # Use LLM service for questions
            return await handle_question_request(request, confidence)
        elif intent == "query":
            # Use protocol operations for system queries (backup route)
            return await handle_query_request(request, confidence)
        else:
            # Default LLM response
            return await handle_general_request(request, confidence)
            
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

async def handle_automation_request(request: ChatRequest, confidence: float) -> ChatResponse:
    """Handle automation/job creation requests"""
    try:
        # Parse the request using NLP service
        async with httpx.AsyncClient() as client:
            parse_response = await client.post(
                f"{NLP_SERVICE_URL}/nlp/parse",
                json={"text": request.message}
            )
            parsed_data = parse_response.json()
        
        # Generate workflow
        workflow = workflow_generator.generate_workflow_from_parsed(parsed_data)
        job_id = str(uuid.uuid4())
        
        # Store in vector database for learning
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{VECTOR_SERVICE_URL}/vector/store",
                    json={
                        "content": f"User request: {request.message}. Generated workflow: {workflow['name']}",
                        "category": "automation_request"
                    }
                )
        except Exception as e:
            logger.warning("Failed to store in vector database", error=str(e))
        
        return ChatResponse(
            response=f"I've created a workflow to {workflow['name']}. Would you like me to execute it?",
            intent="automation",
            confidence=confidence,
            job_id=job_id,
            workflow=workflow,
            execution_started=False
        )
        
    except Exception as e:
        logger.error("Failed to handle automation request", error=str(e))
        return ChatResponse(
            response=f"I encountered an error creating the automation: {str(e)}",
            intent="automation",
            confidence=0.1,
            execution_started=False
        )

async def handle_question_request(request: ChatRequest, confidence: float) -> ChatResponse:
    """Handle general questions using LLM service with OpsConductor knowledge"""
    try:
        # Get OpsConductor-specific context
        system_context = await knowledge_manager.get_system_context(request.message)
        
        # Also search vector database for additional relevant knowledge
        relevant_context = ""
        try:
            async with httpx.AsyncClient() as client:
                search_response = await client.post(
                    f"{VECTOR_SERVICE_URL}/vector/search",
                    json={"query": request.message, "limit": 3}
                )
                search_data = search_response.json()
                if search_data.get("results"):
                    relevant_context = "\n".join([r.get("content", "") for r in search_data["results"]])
        except Exception as e:
            logger.warning("Failed to search vector database", error=str(e))
        
        # Combine contexts
        full_context = system_context
        if relevant_context:
            full_context += f"\n\nAdditional Context:\n{relevant_context}"
        
        # Generate response using LLM service
        async with httpx.AsyncClient(timeout=60.0) as client:
            llm_response = await client.post(
                f"{LLM_SERVICE_URL}/llm/chat",
                json={
                    "message": request.message,
                    "context": full_context,
                    "system_prompt": "You are OpsConductor AI, an IT operations automation assistant. Use the provided context about the current OpsConductor system to give accurate, helpful answers. Be specific and reference actual system data when available."
                }
            )
            llm_data = llm_response.json()
        
        response_text = llm_data.get("response", "I'm not sure how to answer that question.")
        
        return ChatResponse(
            response=response_text,
            intent="question",
            confidence=confidence,
            execution_started=False
        )
        
    except Exception as e:
        logger.error("Failed to handle question request", error=str(e))
        return ChatResponse(
            response="I encountered an error processing your question. Please try again.",
            intent="question",
            confidence=0.1,
            execution_started=False
        )

async def _is_system_information_query(query: str, parsed_data: Dict[str, Any]) -> bool:
    """Intelligently determine if a query is asking for system information vs automation"""
    try:
        query_lower = query.lower()
        entities = parsed_data.get("entities", [])
        intent = parsed_data.get("intent", "")
        
        # Information-seeking patterns (not action-oriented)
        info_patterns = [
            # Question words
            "what", "which", "where", "when", "who", "how many", "how much", "how about",
            # Information verbs
            "show", "list", "display", "tell", "describe", "explain", "give me", "provide",
            "find", "get", "see", "view", "check", "look at", "examine",
            # Status/state queries
            "status", "state", "health", "overview", "summary", "report", "info", "information",
            "details", "breakdown", "analysis", "statistics", "stats", "metrics",
            # Counting/quantifying
            "count", "number", "total", "amount", "quantity", "sum",
            # Existence queries
            "do we have", "are there", "is there", "exists", "available", "present",
            "do you have", "can you find", "is it possible",
            # Comparison queries
            "compare", "difference", "versus", "vs", "between", "against",
            # Polite/conversational
            "could you", "would you", "please", "can you", "help me", "i need", "i want"
        ]
        
        # System entities that indicate information queries
        system_entities = [
            "target", "targets", "server", "servers", "machine", "machines", 
            "host", "hosts", "system", "systems", "computer", "computers",
            "tag", "tags", "label", "labels", "category", "categories", "group", "groups",
            "job", "jobs", "task", "tasks", "automation", "workflow", "workflows",
            "run", "runs", "execution", "executions", "result", "results", "log", "logs",
            "user", "users", "account", "accounts", "role", "roles", "permission", "permissions",
            "service", "services", "process", "processes", "application", "applications"
        ]
        
        # Action patterns that indicate automation requests
        action_patterns = [
            "run", "execute", "start", "stop", "restart", "kill",
            "deploy", "install", "update", "upgrade", "configure",
            "create", "delete", "remove", "add", "modify",
            "backup", "restore", "sync", "copy", "move",
            "schedule", "automate", "trigger"
        ]
        
        # Check for information-seeking patterns
        has_info_pattern = any(pattern in query_lower for pattern in info_patterns)
        
        # Check for system entities
        has_system_entity = any(entity in query_lower for entity in system_entities)
        
        # Check for action patterns
        has_action_pattern = any(pattern in query_lower for pattern in action_patterns)
        
        # Check NLP entities for system-related terms
        entity_types = [e.get("label", "").lower() for e in entities]
        entity_texts = [e.get("text", "").lower() for e in entities]
        has_system_nlp_entity = any(etype in ["org", "product", "gpe", "facility"] for etype in entity_types)
        
        # Enhanced semantic understanding - check for infrastructure-related terms
        infrastructure_terms = [
            "infrastructure", "environment", "setup", "deployment", "network",
            "datacenter", "cloud", "platform", "architecture", "topology"
        ]
        has_infrastructure_term = any(term in query_lower for term in infrastructure_terms)
        
        # Check for technology/OS terms that indicate system queries
        tech_terms = [
            "windows", "linux", "ubuntu", "centos", "debian", "redhat",
            "vm", "virtual", "container", "docker", "kubernetes",
            "aws", "azure", "gcp", "cloud", "on-premise", "hybrid"
        ]
        has_tech_term = any(term in query_lower for term in tech_terms)
        
        # Check for operational terms
        ops_terms = [
            "monitoring", "alerting", "logging", "metrics", "performance",
            "uptime", "downtime", "availability", "reliability", "maintenance"
        ]
        has_ops_term = any(term in query_lower for term in ops_terms)
        
        # Enhanced decision logic with semantic understanding
        if has_info_pattern and (has_system_entity or has_system_nlp_entity or has_infrastructure_term):
            return True
        
        if has_system_entity and not has_action_pattern:
            return True
        
        if has_infrastructure_term or has_tech_term or has_ops_term:
            return True
            
        # Special cases for common queries with more variations
        common_info_phrases = [
            "how many", "what are", "show me", "list all", "tell me about",
            "what is", "where is", "status of", "health of", "overview of",
            "give me info", "i need to know", "can you tell me", "help me understand",
            "what about", "how about", "details on", "information about"
        ]
        if any(phrase in query_lower for phrase in common_info_phrases):
            return True
        
        # Check for possessive patterns that indicate system ownership
        possessive_patterns = [
            "our", "my", "the", "this", "these", "those"
        ]
        if any(poss in query_lower for poss in possessive_patterns) and has_system_entity:
            return True
        
        # If it's clearly an action request, it's not a system info query
        if has_action_pattern and not has_info_pattern and not has_system_entity:
            return False
        
        # Default to system info query for ambiguous cases
        return True
        
    except Exception as e:
        logger.error("Error in query analysis", error=str(e))
        # Default to system info query on error
        return True

async def handle_query_request(request: ChatRequest, confidence: float) -> ChatResponse:
    """Handle system queries using intelligent analysis and knowledge manager"""
    try:
        # Parse the request to understand what system query is needed
        async with httpx.AsyncClient() as client:
            parse_response = await client.post(
                f"{NLP_SERVICE_URL}/nlp/parse",
                json={"text": request.message}
            )
            parsed_data = parse_response.json()
        
        logger.info("Processing query with intelligent analysis", 
                   query=request.message, 
                   entities=parsed_data.get("entities", []),
                   intent=parsed_data.get("intent"))
        
        # Use intelligent query analysis to determine if this is a system information query
        is_system_query = await _is_system_information_query(request.message, parsed_data)
        
        if is_system_query:
            logger.info("Query identified as system information query, using knowledge manager")
            result = await knowledge_manager.handle_system_query(request.message, parsed_data)
            logger.info("Knowledge manager result", success=result.get("success"), message_preview=result.get("message", "")[:100])
            
            if result.get("success"):
                return ChatResponse(
                    response=result.get("message", "Query completed"),
                    intent="query",
                    confidence=confidence,
                    execution_started=True
                )
        
        # Fall back to protocol operations for automation/execution queries
        logger.info("Query identified as automation/execution query, using protocol manager")
        result = await protocol_manager.execute_query(parsed_data)
        
        return ChatResponse(
            response=result.get("message", "Query completed"),
            intent="query",
            confidence=confidence,
            execution_started=True
        )
        
    except Exception as e:
        logger.error("Failed to handle query request", error=str(e))
        return ChatResponse(
            response=f"I encountered an error executing the query: {str(e)}",
            intent="query",
            confidence=0.1,
            execution_started=False
        )

async def handle_general_request(request: ChatRequest, confidence: float) -> ChatResponse:
    """Handle general requests with LLM fallback"""
    try:
        async with httpx.AsyncClient() as client:
            llm_response = await client.post(
                f"{LLM_SERVICE_URL}/llm/chat",
                json={
                    "message": request.message,
                    "system_prompt": "You are OpsConductor AI. If the user wants to automate something, suggest they be more specific about what they want to do."
                }
            )
            llm_data = llm_response.json()
        
        response_text = llm_data.get("response", "I'm not sure how to help with that. Could you be more specific?")
        
        return ChatResponse(
            response=response_text,
            intent="general",
            confidence=confidence,
            execution_started=False
        )
        
    except Exception as e:
        logger.error("Failed to handle general request", error=str(e))
        return ChatResponse(
            response="I'm having trouble processing your request. Please try again.",
            intent="general",
            confidence=0.1,
            execution_started=False
        )

@app.post("/ai/create-job", response_model=JobResponse)
async def create_job(request: JobRequest):
    """Create a new automation job from natural language description"""
    try:
        logger.info("Processing job creation request", description=request.description)
        
        # Parse the request using NLP service
        async with httpx.AsyncClient() as client:
            parse_response = await client.post(
                f"{NLP_SERVICE_URL}/nlp/parse",
                json={"text": request.description}
            )
            parsed_data = parse_response.json()
        
        # Generate workflow
        workflow = workflow_generator.generate_workflow_from_parsed(parsed_data)
        job_id = str(uuid.uuid4())
        
        return JobResponse(
            job_id=job_id,
            workflow=workflow,
            message=f"Successfully created workflow for: {request.description}",
            confidence=parsed_data.get("confidence", 0.5),
            parsed_request=parsed_data
        )
        
    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/ai/execute-job", response_model=ExecuteJobResponse)
async def execute_job(request: ExecuteJobRequest):
    """Execute a job immediately"""
    try:
        # First create the job
        job_response = await create_job(JobRequest(
            description=request.description,
            user_id=request.user_id
        ))
        
        if request.execute_immediately:
            # Submit to automation service
            async with httpx.AsyncClient() as client:
                automation_response = await client.post(
                    f"{AUTOMATION_SERVICE_URL}/jobs",
                    json={
                        "name": job_response.workflow["name"],
                        "description": job_response.workflow["description"],
                        "workflow": job_response.workflow,
                        "created_by": request.user_id or 1
                    }
                )
                automation_data = automation_response.json()
                automation_job_id = automation_data.get("id")
                
                # Execute the job
                execution_response = await client.post(
                    f"{AUTOMATION_SERVICE_URL}/jobs/{automation_job_id}/execute"
                )
                execution_data = execution_response.json()
                execution_id = execution_data.get("execution_id")
        
        return ExecuteJobResponse(
            job_id=job_response.job_id,
            execution_id=execution_id if request.execute_immediately else None,
            workflow=job_response.workflow,
            message=f"Job created and {'executed' if request.execute_immediately else 'ready for execution'}",
            confidence=job_response.confidence,
            execution_started=request.execute_immediately,
            automation_job_id=automation_job_id if request.execute_immediately else None
        )
        
    except Exception as e:
        logger.error("Failed to execute job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute job: {str(e)}")

@app.post("/ai/protocol/execute")
async def execute_protocol_operation(request: dict):
    """Execute operation using specified protocol"""
    try:
        result = await protocol_manager.execute_protocol_operation(request)
        return result
        
    except Exception as e:
        logger.error("Protocol operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Protocol operation failed: {str(e)}")

@app.get("/ai/protocols/capabilities")
async def get_protocol_capabilities():
    """Get all supported protocol capabilities"""
    try:
        return protocol_manager.get_protocol_capabilities()
        
    except Exception as e:
        logger.error("Failed to get protocol capabilities", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

@app.get("/ai/knowledge-stats")
async def get_knowledge_stats():
    """Get AI knowledge base statistics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{VECTOR_SERVICE_URL}/vector/stats")
            return response.json()
        
    except Exception as e:
        logger.error("Failed to get knowledge stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/ai/store-knowledge")
async def store_knowledge_endpoint(request: dict):
    """Store new knowledge in the AI system"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VECTOR_SERVICE_URL}/vector/store",
                json=request
            )
            return response.json()
        
    except Exception as e:
        logger.error("Failed to store knowledge", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store knowledge: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
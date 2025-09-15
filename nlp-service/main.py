from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any

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

class NLPService(BaseService):
    def __init__(self):
        super().__init__("nlp-service")

app = FastAPI(
    title="OpsConductor NLP Service",
    description="Natural Language Processing service for text analysis and entity extraction",
    version="1.0.0"
)

# Initialize service
service = NLPService()

# Import NLP processor after service initialization
from nlp_processor import SimpleNLPProcessor
nlp_processor = SimpleNLPProcessor()

# Request/Response models
class ParseRequest(BaseModel):
    text: str

class ParseResponse(BaseModel):
    operation: str
    target_process: Optional[str] = None
    target_service: Optional[str] = None
    target_group: Optional[str] = None
    target_os: Optional[str] = None
    package_name: Optional[str] = None
    confidence: float
    raw_text: str

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    entities: Dict[str, List[str]]
    text: str

class ClassifyRequest(BaseModel):
    text: str

class ClassifyResponse(BaseModel):
    intent: str
    confidence: float
    category: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "nlp-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "nlp-service",
        "version": "1.0.0",
        "description": "Natural Language Processing service for text analysis",
        "capabilities": [
            "Text parsing and entity extraction",
            "Intent recognition",
            "Operation classification",
            "Target identification"
        ]
    }

@app.post("/nlp/parse", response_model=ParseResponse)
async def parse_text(request: ParseRequest):
    """Parse natural language text into structured data"""
    try:
        logger.info("Parsing text", text=request.text)
        
        parsed_request = nlp_processor.parse_request(request.text)
        
        return ParseResponse(
            operation=parsed_request.operation,
            target_process=parsed_request.target_process,
            target_service=parsed_request.target_service,
            target_group=parsed_request.target_group,
            target_os=parsed_request.target_os,
            package_name=parsed_request.package_name,
            confidence=parsed_request.confidence,
            raw_text=parsed_request.raw_text
        )
        
    except Exception as e:
        logger.error("Failed to parse text", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to parse text: {str(e)}")

@app.post("/nlp/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Extract entities from text"""
    try:
        logger.info("Analyzing text", text=request.text)
        
        entities = nlp_processor.extract_entities(request.text)
        
        return AnalyzeResponse(
            entities=entities,
            text=request.text
        )
        
    except Exception as e:
        logger.error("Failed to analyze text", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to analyze text: {str(e)}")

@app.post("/nlp/classify", response_model=ClassifyResponse)
async def classify_intent(request: ClassifyRequest):
    """Classify the intent of the text"""
    try:
        logger.info("Classifying intent", text=request.text)
        
        parsed_request = nlp_processor.parse_request(request.text)
        
        # Determine intent based on operation and content
        intent = "unknown"
        confidence = 0.5
        category = "general"
        
        if parsed_request.operation != "unknown":
            if parsed_request.operation in ["check", "status"]:
                intent = "query"
                category = "information"
            else:
                intent = "automation"
                category = "action"
            confidence = parsed_request.confidence
        
        # Check for question patterns
        question_patterns = ["what", "how", "when", "where", "why", "which", "?"]
        if any(pattern in request.text.lower() for pattern in question_patterns):
            intent = "question"
            category = "information"
            confidence = 0.8
        
        return ClassifyResponse(
            intent=intent,
            confidence=confidence,
            category=category
        )
        
    except Exception as e:
        logger.error("Failed to classify intent", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to classify intent: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
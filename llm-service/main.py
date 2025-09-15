from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
import ollama

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

class LLMService(BaseService):
    def __init__(self):
        super().__init__("llm-service")

app = FastAPI(
    title="OpsConductor LLM Service",
    description="Large Language Model service for AI text generation and reasoning",
    version="1.0.0"
)

# Initialize service
service = LLMService()

# Import LLM engine after service initialization
from llm_engine import LLMEngine

# Initialize LLM engine
llm_engine = None

@app.on_event("startup")
async def startup_event():
    """Initialize LLM engine on startup"""
    global llm_engine
    try:
        logger.info("Initializing LLM engine...")
        
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        default_model = os.getenv("DEFAULT_LLM_MODEL", "llama2")
        
        llm_engine = LLMEngine(ollama_host, default_model)
        success = await llm_engine.initialize()
        
        if success:
            logger.info("LLM engine initialized successfully")
        else:
            logger.error("Failed to initialize LLM engine")
            
    except Exception as e:
        logger.error("LLM engine initialization failed", error=str(e))

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    confidence: float
    processing_time: float

class GenerateRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class GenerateResponse(BaseModel):
    generated_text: str
    model_used: str
    tokens_generated: int
    processing_time: float

class SummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 200
    model: Optional[str] = None

class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float

class AnalyzeRequest(BaseModel):
    text: str
    analysis_type: str = "sentiment"  # sentiment, intent, complexity
    model: Optional[str] = None

class AnalyzeResponse(BaseModel):
    analysis_type: str
    result: Dict[str, Any]
    confidence: float

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "llm-service",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_initialized": llm_engine is not None
    }

@app.get("/gpu-status")
async def gpu_status():
    """GPU status and utilization endpoint"""
    if not llm_engine:
        return {"error": "LLM engine not initialized"}
    
    return llm_engine.get_gpu_status()

@app.get("/info")
async def service_info():
    """Service information endpoint"""
    available_models = []
    if llm_engine:
        available_models = await llm_engine.get_available_models()
    
    gpu_info = {}
    if llm_engine:
        gpu_info = llm_engine.get_gpu_status()
    
    return {
        "service": "llm-service",
        "version": "1.0.0",
        "description": "Large Language Model service for AI text generation and reasoning",
        "capabilities": [
            "Chat and conversation",
            "Text generation",
            "Text summarization",
            "Sentiment analysis",
            "Intent analysis",
            "Code generation",
            "Question answering"
        ],
        "available_models": available_models,
        "ollama_host": os.getenv("OLLAMA_HOST", "http://ollama:11434"),
        "gpu_status": gpu_info
    }

@app.post("/llm/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest):
    """Chat with the LLM"""
    try:
        if not llm_engine:
            raise HTTPException(status_code=503, detail="LLM engine not initialized")
        
        logger.info("Processing chat request", message_length=len(request.message))
        
        response = await llm_engine.chat(
            message=request.message,
            context=request.context,
            system_prompt=request.system_prompt,
            model=request.model,
            parsed_data=request.parsed_data
        )
        
        return ChatResponse(
            response=response["response"],
            model_used=response["model_used"],
            confidence=response["confidence"],
            processing_time=response["processing_time"]
        )
        
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/llm/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """Generate text from prompt"""
    try:
        if not llm_engine:
            raise HTTPException(status_code=503, detail="LLM engine not initialized")
        
        logger.info("Processing generation request", prompt_length=len(request.prompt))
        
        response = await llm_engine.generate(
            prompt=request.prompt,
            context=request.context,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return GenerateResponse(
            generated_text=response["generated_text"],
            model_used=response["model_used"],
            tokens_generated=response["tokens_generated"],
            processing_time=response["processing_time"]
        )
        
    except Exception as e:
        logger.error("Generation request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/llm/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """Summarize text"""
    try:
        if not llm_engine:
            raise HTTPException(status_code=503, detail="LLM engine not initialized")
        
        logger.info("Processing summarization request", text_length=len(request.text))
        
        response = await llm_engine.summarize(
            text=request.text,
            max_length=request.max_length,
            model=request.model
        )
        
        return SummarizeResponse(
            summary=response["summary"],
            original_length=len(request.text),
            summary_length=len(response["summary"]),
            compression_ratio=len(response["summary"]) / len(request.text)
        )
        
    except Exception as e:
        logger.error("Summarization request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.post("/llm/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text for sentiment, intent, etc."""
    try:
        if not llm_engine:
            raise HTTPException(status_code=503, detail="LLM engine not initialized")
        
        logger.info("Processing analysis request", 
                   analysis_type=request.analysis_type, 
                   text_length=len(request.text))
        
        response = await llm_engine.analyze(
            text=request.text,
            analysis_type=request.analysis_type,
            model=request.model
        )
        
        return AnalyzeResponse(
            analysis_type=request.analysis_type,
            result=response["result"],
            confidence=response["confidence"]
        )
        
    except Exception as e:
        logger.error("Analysis request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/llm/models")
async def get_available_models():
    """Get list of available LLM models"""
    try:
        if not llm_engine:
            raise HTTPException(status_code=503, detail="LLM engine not initialized")
        
        models = await llm_engine.get_available_models()
        
        return {
            "available_models": models,
            "default_model": llm_engine.default_model,
            "total_models": len(models)
        }
        
    except Exception as e:
        logger.error("Failed to get models", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/llm/models/pull")
async def pull_model(model_name: str):
    """Pull/download a new model"""
    try:
        if not llm_engine:
            raise HTTPException(status_code=503, detail="LLM engine not initialized")
        
        logger.info("Pulling model", model_name=model_name)
        
        success = await llm_engine.pull_model(model_name)
        
        if success:
            return {
                "success": True,
                "message": f"Model '{model_name}' pulled successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to pull model '{model_name}'")
        
    except Exception as e:
        logger.error("Failed to pull model", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
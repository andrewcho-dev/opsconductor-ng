"""
OUIOE Phase 2: Thinking-Aware LLM API Router

This module provides API endpoints for thinking-aware LLM operations,
allowing clients to interact with the enhanced LLM client that provides
real-time thinking visualization and progress updates.

Key Features:
- RESTful API for thinking-aware LLM operations
- Session management for thinking streams
- Debug mode support for detailed thinking visualization
- Backward compatibility with existing LLM endpoints
- Performance monitoring and statistics
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import structlog
import uuid
from datetime import datetime

from integrations.llm_service_factory import LLMServiceFactory, get_default_llm_client
from integrations.thinking_llm_client import ThinkingLLMClient, ThinkingConfig

logger = structlog.get_logger()

# Initialize router
router = APIRouter(prefix="/api/thinking-llm", tags=["Thinking LLM"])

# Global LLM client instance
llm_client = None

# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat operations"""
    message: str = Field(..., description="User message")
    context: Optional[str] = Field(None, description="Additional context")
    system_prompt: Optional[str] = Field(None, description="System prompt override")
    model: Optional[str] = Field(None, description="Model to use")
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="Parsed request data")
    user_id: str = Field("default", description="User identifier")
    debug_mode: bool = Field(False, description="Enable debug mode for detailed thinking")
    session_id: Optional[str] = Field(None, description="Existing session ID")

class GenerateRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., description="Generation prompt")
    context: Optional[str] = Field(None, description="Additional context")
    model: Optional[str] = Field(None, description="Model to use")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, description="Generation temperature")
    user_id: str = Field("default", description="User identifier")
    debug_mode: bool = Field(False, description="Enable debug mode for detailed thinking")
    session_id: Optional[str] = Field(None, description="Existing session ID")

class SummarizeRequest(BaseModel):
    """Request model for text summarization"""
    text: str = Field(..., description="Text to summarize")
    max_length: int = Field(200, description="Maximum summary length")
    model: Optional[str] = Field(None, description="Model to use")
    user_id: str = Field("default", description="User identifier")
    debug_mode: bool = Field(False, description="Enable debug mode for detailed thinking")
    session_id: Optional[str] = Field(None, description="Existing session ID")

class AnalyzeRequest(BaseModel):
    """Request model for text analysis"""
    text: str = Field(..., description="Text to analyze")
    analysis_type: str = Field("sentiment", description="Type of analysis")
    model: Optional[str] = Field(None, description="Model to use")
    user_id: str = Field("default", description="User identifier")
    debug_mode: bool = Field(False, description="Enable debug mode for detailed thinking")
    session_id: Optional[str] = Field(None, description="Existing session ID")

class SessionCreateRequest(BaseModel):
    """Request model for creating thinking sessions"""
    user_id: str = Field(..., description="User identifier")
    operation_type: str = Field(..., description="Type of operation")
    user_request: str = Field(..., description="User request description")
    debug_mode: bool = Field(False, description="Enable debug mode")

class ThinkingConfigRequest(BaseModel):
    """Request model for updating thinking configuration"""
    enable_thinking_stream: Optional[bool] = Field(None, description="Enable thinking stream")
    enable_progress_stream: Optional[bool] = Field(None, description="Enable progress stream")
    thinking_detail_level: Optional[str] = Field(None, description="Detail level")
    progress_update_frequency: Optional[float] = Field(None, description="Update frequency")
    max_thinking_steps: Optional[int] = Field(None, description="Maximum thinking steps")
    thinking_timeout: Optional[float] = Field(None, description="Thinking timeout")

# Startup event
@router.on_event("startup")
async def initialize_llm_client():
    """Initialize the LLM client on startup"""
    global llm_client
    try:
        llm_client = get_default_llm_client()
        await llm_client.initialize()
        logger.info("Thinking LLM client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize thinking LLM client", error=str(e))
        raise

# Health and Status Endpoints
@router.get("/health")
async def health_check():
    """Health check for thinking LLM service"""
    try:
        if llm_client is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "message": "LLM client not initialized"}
            )
        
        # Get client capabilities
        capabilities = LLMServiceFactory.get_client_capabilities(llm_client)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "capabilities": capabilities,
            "thinking_enabled": capabilities["supports_thinking"]
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@router.get("/capabilities")
async def get_capabilities():
    """Get LLM client capabilities"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        capabilities = LLMServiceFactory.get_client_capabilities(llm_client)
        return capabilities
    except Exception as e:
        logger.error("Failed to get capabilities", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_available_models():
    """Get available LLM models"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        models = await llm_client.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error("Failed to get available models", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Thinking-Aware LLM Operations
@router.post("/chat")
async def chat_with_thinking(request: ChatRequest):
    """Chat with thinking visualization"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        # Use thinking-aware method if available
        if isinstance(llm_client, ThinkingLLMClient):
            result = await llm_client.chat_with_thinking(
                message=request.message,
                context=request.context,
                system_prompt=request.system_prompt,
                model=request.model,
                parsed_data=request.parsed_data,
                user_id=request.user_id,
                debug_mode=request.debug_mode,
                session_id=request.session_id
            )
        else:
            # Fallback to standard chat
            result = await llm_client.chat(
                message=request.message,
                context=request.context,
                system_prompt=request.system_prompt,
                model=request.model,
                parsed_data=request.parsed_data
            )
        
        return result
    except Exception as e:
        logger.error("Chat operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_with_thinking(request: GenerateRequest):
    """Generate text with thinking visualization"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        # Use thinking-aware method if available
        if isinstance(llm_client, ThinkingLLMClient):
            result = await llm_client.generate_with_thinking(
                prompt=request.prompt,
                context=request.context,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                user_id=request.user_id,
                debug_mode=request.debug_mode,
                session_id=request.session_id
            )
        else:
            # Fallback to standard generation
            result = await llm_client.generate(
                prompt=request.prompt,
                context=request.context,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
        
        return result
    except Exception as e:
        logger.error("Generation operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize")
async def summarize_with_thinking(request: SummarizeRequest):
    """Summarize text with thinking visualization"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        # Use thinking-aware method if available
        if isinstance(llm_client, ThinkingLLMClient):
            result = await llm_client.summarize_with_thinking(
                text=request.text,
                max_length=request.max_length,
                model=request.model,
                user_id=request.user_id,
                debug_mode=request.debug_mode,
                session_id=request.session_id
            )
        else:
            # Fallback to standard summarization
            result = await llm_client.summarize(
                text=request.text,
                max_length=request.max_length,
                model=request.model
            )
        
        return result
    except Exception as e:
        logger.error("Summarization operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_with_thinking(request: AnalyzeRequest):
    """Analyze text with thinking visualization"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        # Use thinking-aware method if available
        if isinstance(llm_client, ThinkingLLMClient):
            result = await llm_client.analyze_with_thinking(
                text=request.text,
                analysis_type=request.analysis_type,
                model=request.model,
                user_id=request.user_id,
                debug_mode=request.debug_mode,
                session_id=request.session_id
            )
        else:
            # Fallback to standard analysis
            result = await llm_client.analyze(
                text=request.text,
                analysis_type=request.analysis_type,
                model=request.model
            )
        
        return result
    except Exception as e:
        logger.error("Analysis operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@router.post("/sessions")
async def create_thinking_session(request: SessionCreateRequest):
    """Create a new thinking session"""
    try:
        if not isinstance(llm_client, ThinkingLLMClient):
            raise HTTPException(
                status_code=400, 
                detail="Thinking sessions require thinking-aware LLM client"
            )
        
        session_id = await llm_client.create_thinking_session(
            user_id=request.user_id,
            operation_type=request.operation_type,
            user_request=request.user_request,
            debug_mode=request.debug_mode
        )
        
        return {
            "session_id": session_id,
            "user_id": request.user_id,
            "operation_type": request.operation_type,
            "debug_mode": request.debug_mode,
            "created_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to create thinking session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/stats")
async def get_session_stats(session_id: str = Path(..., description="Session ID")):
    """Get statistics for a thinking session"""
    try:
        if not isinstance(llm_client, ThinkingLLMClient):
            raise HTTPException(
                status_code=400, 
                detail="Session stats require thinking-aware LLM client"
            )
        
        stats = await llm_client.get_thinking_session_stats(session_id)
        return stats
    except Exception as e:
        logger.error("Failed to get session stats", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def close_thinking_session(session_id: str = Path(..., description="Session ID")):
    """Close a thinking session"""
    try:
        if not isinstance(llm_client, ThinkingLLMClient):
            raise HTTPException(
                status_code=400, 
                detail="Session management requires thinking-aware LLM client"
            )
        
        stats = await llm_client.close_thinking_session(session_id)
        return {
            "message": "Session closed successfully",
            "session_id": session_id,
            "final_stats": stats
        }
    except Exception as e:
        logger.error("Failed to close session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Endpoints
@router.get("/config")
async def get_thinking_config():
    """Get current thinking configuration"""
    try:
        if not isinstance(llm_client, ThinkingLLMClient):
            return {"message": "Thinking configuration not available for standard LLM client"}
        
        if hasattr(llm_client, 'thinking_config'):
            return llm_client.thinking_config.__dict__
        else:
            return {"message": "No thinking configuration available"}
    except Exception as e:
        logger.error("Failed to get thinking config", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_thinking_config(request: ThinkingConfigRequest):
    """Update thinking configuration"""
    try:
        if not isinstance(llm_client, ThinkingLLMClient):
            raise HTTPException(
                status_code=400, 
                detail="Configuration update requires thinking-aware LLM client"
            )
        
        if not hasattr(llm_client, 'thinking_config'):
            raise HTTPException(status_code=400, detail="No thinking configuration available")
        
        # Update configuration
        config = llm_client.thinking_config
        update_data = request.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return {
            "message": "Configuration updated successfully",
            "updated_config": config.__dict__
        }
    except Exception as e:
        logger.error("Failed to update thinking config", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Legacy Compatibility Endpoints (without thinking)
@router.post("/legacy/chat")
async def legacy_chat(request: ChatRequest):
    """Legacy chat endpoint without thinking (for backward compatibility)"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        result = await llm_client.chat(
            message=request.message,
            context=request.context,
            system_prompt=request.system_prompt,
            model=request.model,
            parsed_data=request.parsed_data
        )
        
        return result
    except Exception as e:
        logger.error("Legacy chat operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/legacy/generate")
async def legacy_generate(request: GenerateRequest):
    """Legacy generation endpoint without thinking (for backward compatibility)"""
    try:
        if llm_client is None:
            raise HTTPException(status_code=503, detail="LLM client not initialized")
        
        result = await llm_client.generate(
            prompt=request.prompt,
            context=request.context,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return result
    except Exception as e:
        logger.error("Legacy generation operation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Testing and Development Endpoints
@router.post("/test/thinking")
async def test_thinking_capabilities():
    """Test thinking capabilities with a simple operation"""
    try:
        if not isinstance(llm_client, ThinkingLLMClient):
            return {
                "message": "Thinking capabilities not available",
                "client_type": "standard",
                "test_result": "skipped"
            }
        
        # Test with a simple chat operation
        result = await llm_client.chat_with_thinking(
            message="Hello, can you tell me about AI thinking?",
            user_id="test-user",
            debug_mode=True
        )
        
        return {
            "message": "Thinking capabilities test completed",
            "client_type": "thinking",
            "test_result": "success",
            "session_id": result.get("session_id"),
            "thinking_enabled": result.get("thinking_enabled", False)
        }
    except Exception as e:
        logger.error("Thinking capabilities test failed", error=str(e))
        return {
            "message": "Thinking capabilities test failed",
            "test_result": "error",
            "error": str(e)
        }
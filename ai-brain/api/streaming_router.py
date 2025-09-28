"""
API router for streaming control and management
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

from ..streaming.stream_manager import get_global_stream_manager
from ..streaming.thinking_data_models import StreamConfig, ThinkingContext

logger = structlog.get_logger()

router = APIRouter(prefix="/api/streaming", tags=["streaming"])


class CreateSessionRequest(BaseModel):
    """Request to create a streaming session"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    debug_mode: bool = Field(default=False, description="Enable debug mode with detailed thinking")
    user_request: str = Field(default="", description="User's original request")
    system_context: Optional[Dict[str, Any]] = Field(default=None, description="System context")


class CreateSessionResponse(BaseModel):
    """Response for session creation"""
    success: bool = Field(..., description="Whether session was created successfully")
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="Status message")
    websocket_urls: Dict[str, str] = Field(..., description="WebSocket URLs for this session")


class StreamThinkingRequest(BaseModel):
    """Request to stream a thinking step"""
    session_id: str = Field(..., description="Session identifier")
    thinking_type: str = Field(..., description="Type of thinking step")
    content: str = Field(..., description="Thinking content")
    reasoning_chain: Optional[List[str]] = Field(default=None, description="Reasoning steps")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence level")
    alternatives: Optional[List[str]] = Field(default=None, description="Alternatives considered")
    decision_factors: Optional[List[str]] = Field(default=None, description="Decision factors")


class StreamProgressRequest(BaseModel):
    """Request to stream a progress update"""
    session_id: str = Field(..., description="Session identifier")
    progress_type: str = Field(..., description="Type of progress update")
    message: str = Field(..., description="Progress message")
    progress_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Progress percentage")
    current_step: Optional[str] = Field(default=None, description="Current step")
    estimated_remaining: Optional[str] = Field(default=None, description="Estimated remaining time")


class StreamResponse(BaseModel):
    """Response for streaming operations"""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Status message")


class SessionStatsResponse(BaseModel):
    """Response with session statistics"""
    session_id: str = Field(..., description="Session identifier")
    total_thinking_steps: int = Field(..., description="Total thinking steps")
    total_progress_updates: int = Field(..., description="Total progress updates")
    session_duration: float = Field(..., description="Session duration in seconds")
    last_updated: datetime = Field(..., description="Last activity timestamp")


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_streaming_session(request: CreateSessionRequest):
    """Create a new streaming session"""
    try:
        stream_manager = get_global_stream_manager()
        if not stream_manager:
            raise HTTPException(status_code=503, detail="Streaming infrastructure not available")
        
        # Create session
        session = await stream_manager.create_thinking_session(
            session_id=request.session_id,
            user_id=request.user_id,
            debug_mode=request.debug_mode,
            user_request=request.user_request,
            system_context=request.system_context
        )
        
        # Generate WebSocket URLs
        base_url = "ws://localhost:3005"  # This should be configurable
        websocket_urls = {
            "thinking": f"{base_url}/ws/thinking/{request.session_id}",
            "progress": f"{base_url}/ws/progress/{request.session_id}"
        }
        
        logger.info("✅ Created streaming session via API", 
                   session_id=request.session_id, debug_mode=request.debug_mode)
        
        return CreateSessionResponse(
            success=True,
            session_id=request.session_id,
            message="Streaming session created successfully",
            websocket_urls=websocket_urls
        )
        
    except Exception as e:
        logger.error("❌ Failed to create streaming session", 
                    session_id=request.session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/thinking", response_model=StreamResponse)
async def stream_thinking_step(request: StreamThinkingRequest):
    """Stream a thinking step"""
    try:
        stream_manager = get_global_stream_manager()
        if not stream_manager:
            raise HTTPException(status_code=503, detail="Streaming infrastructure not available")
        
        # Validate thinking type
        from ..streaming.thinking_data_models import ThinkingType
        try:
            thinking_type = ThinkingType(request.thinking_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid thinking type: {request.thinking_type}")
        
        # Stream thinking step
        success = await stream_manager.stream_thinking(
            session_id=request.session_id,
            thinking_type=thinking_type,
            content=request.content,
            reasoning_chain=request.reasoning_chain,
            confidence=request.confidence,
            alternatives=request.alternatives,
            decision_factors=request.decision_factors
        )
        
        if success:
            return StreamResponse(
                success=True,
                message="Thinking step streamed successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to stream thinking step")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to stream thinking step", 
                    session_id=request.session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stream thinking: {str(e)}")


@router.post("/progress", response_model=StreamResponse)
async def stream_progress_update(request: StreamProgressRequest):
    """Stream a progress update"""
    try:
        stream_manager = get_global_stream_manager()
        if not stream_manager:
            raise HTTPException(status_code=503, detail="Streaming infrastructure not available")
        
        # Validate progress type
        from ..streaming.thinking_data_models import ProgressType
        try:
            progress_type = ProgressType(request.progress_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid progress type: {request.progress_type}")
        
        # Stream progress update
        success = await stream_manager.stream_progress(
            session_id=request.session_id,
            progress_type=progress_type,
            message=request.message,
            progress_percentage=request.progress_percentage,
            current_step=request.current_step,
            estimated_remaining=request.estimated_remaining
        )
        
        if success:
            return StreamResponse(
                success=True,
                message="Progress update streamed successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to stream progress update")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to stream progress update", 
                    session_id=request.session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stream progress: {str(e)}")


@router.get("/sessions/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(session_id: str):
    """Get statistics for a streaming session"""
    try:
        stream_manager = get_global_stream_manager()
        if not stream_manager:
            raise HTTPException(status_code=503, detail="Streaming infrastructure not available")
        
        stats = await stream_manager.get_session_stats(session_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionStatsResponse(
            session_id=stats.session_id,
            total_thinking_steps=stats.total_thinking_steps,
            total_progress_updates=stats.total_progress_updates,
            session_duration=stats.session_duration,
            last_updated=stats.last_updated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get session stats", 
                    session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/sessions/{session_id}")
async def close_streaming_session(session_id: str):
    """Close a streaming session"""
    try:
        stream_manager = get_global_stream_manager()
        if not stream_manager:
            raise HTTPException(status_code=503, detail="Streaming infrastructure not available")
        
        success = await stream_manager.close_session(session_id)
        if success:
            logger.info("✅ Closed streaming session via API", session_id=session_id)
            return {"success": True, "message": "Session closed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to close streaming session", 
                    session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}")


@router.get("/health")
async def streaming_health_check():
    """Health check for streaming infrastructure"""
    try:
        stream_manager = get_global_stream_manager()
        if not stream_manager:
            return {
                "status": "unhealthy",
                "message": "Streaming infrastructure not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Test Redis connection
        redis_healthy = stream_manager.is_initialized
        
        return {
            "status": "healthy" if redis_healthy else "unhealthy",
            "redis_connection": redis_healthy,
            "message": "Streaming infrastructure operational" if redis_healthy else "Redis connection failed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Streaming health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@router.get("/test")
async def test_streaming_infrastructure():
    """Test the streaming infrastructure"""
    try:
        from ..streaming.test_streaming import StreamingTester
        
        tester = StreamingTester()
        success = await tester.test_basic_streaming()
        
        return {
            "success": success,
            "message": "Streaming test completed successfully" if success else "Streaming test failed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Streaming test failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
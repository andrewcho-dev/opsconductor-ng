"""
AI Execution Proxy Router
Proxies execution requests to ai-pipeline service
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import logging
import time
import uuid

from clients.ai_pipeline import (
    AIPipelineClient,
    AIPipelineTimeoutError,
    AIPipelineBadGatewayError,
    AIPipelineError
)
from config import config
from observability.metrics import (
    record_ai_request_success,
    record_ai_request_error
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Execution"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ExecRequest(BaseModel):
    """Request to execute a tool via AI Pipeline"""
    input: str = Field(..., min_length=1, max_length=4000, description="Input text for the tool")
    tool: Optional[str] = Field(default="echo", description="Tool to execute (default: echo)")
    trace_id: Optional[str] = Field(default=None, description="Optional trace ID for request tracking")
    
    @validator('input')
    def validate_input(cls, v):
        if not v or not v.strip():
            raise ValueError("Input cannot be empty")
        return v


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str
    message: str


class ExecResponse(BaseModel):
    """Response from AI execution"""
    success: bool
    output: Optional[str] = None
    error: Optional[ErrorDetail] = None
    trace_id: str
    duration_ms: float
    tool: str


# ============================================================================
# GLOBAL CLIENT INSTANCE
# ============================================================================

_ai_pipeline_client: Optional[AIPipelineClient] = None


def get_ai_pipeline_client() -> AIPipelineClient:
    """Get or create AI Pipeline client singleton"""
    global _ai_pipeline_client
    
    if _ai_pipeline_client is None:
        _ai_pipeline_client = AIPipelineClient(
            base_url=config.AI_PIPELINE_BASE_URL,
            timeout_seconds=config.get_exec_timeout_seconds()
        )
        logger.info(f"[Exec] AI Pipeline client initialized: {config.AI_PIPELINE_BASE_URL}")
    
    return _ai_pipeline_client


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/execute", response_model=ExecResponse)
async def execute_tool(
    request: ExecRequest,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id")
):
    """
    Execute a tool via AI Pipeline proxy
    
    This endpoint proxies execution requests to the ai-pipeline service,
    providing a walking skeleton for end-to-end execution testing.
    
    Args:
        request: Execution request with input and tool
        x_trace_id: Optional trace ID from header
    
    Returns:
        ExecResponse with execution result
    
    Raises:
        HTTPException: On validation or execution errors
    """
    start_time = time.perf_counter()
    
    # Determine trace_id (header > body > generated)
    trace_id = x_trace_id or request.trace_id or str(uuid.uuid4())
    tool = request.tool or "echo"
    
    logger.info(f"[Exec] start input=\"{request.input[:80]}\" tool={tool} trace_id={trace_id}")
    
    try:
        # Get AI Pipeline client
        client = get_ai_pipeline_client()
        
        # Call ai-pipeline /execute
        result = await client.execute(
            tool=tool,
            input_text=request.input,
            trace_id=trace_id
        )
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Check if ai-pipeline reported success
        if result.get("success"):
            # Record success metrics
            record_ai_request_success(tool, duration_ms / 1000)
            
            logger.info(
                f"[Exec] done duration={duration_ms:.2f}ms success=True trace_id={trace_id}"
            )
            
            return ExecResponse(
                success=True,
                output=result.get("output"),
                trace_id=trace_id,
                duration_ms=round(duration_ms, 2),
                tool=tool
            )
        else:
            # AI Pipeline returned success=false
            error_msg = result.get("error", "Unknown error from AI Pipeline")
            
            # Record error metrics
            record_ai_request_error(tool, "upstream_error", duration_ms / 1000)
            
            logger.warning(
                f"[Exec] done duration={duration_ms:.2f}ms success=False trace_id={trace_id} "
                f"error={error_msg}"
            )
            
            return ExecResponse(
                success=False,
                error=ErrorDetail(code="upstream_error", message=error_msg),
                trace_id=trace_id,
                duration_ms=round(duration_ms, 2),
                tool=tool
            )
    
    except AIPipelineTimeoutError as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Record timeout metrics
        record_ai_request_error(tool, "timeout", duration_ms / 1000)
        
        logger.error(f"[Exec] timeout trace_id={trace_id} error={e}")
        
        raise HTTPException(
            status_code=502,
            detail={
                "success": False,
                "error": {
                    "code": "timeout",
                    "message": str(e)
                },
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2),
                "tool": tool
            }
        )
    
    except AIPipelineBadGatewayError as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Record bad gateway metrics
        record_ai_request_error(tool, "bad_gateway", duration_ms / 1000)
        
        logger.error(f"[Exec] bad_gateway trace_id={trace_id} error={e}")
        
        raise HTTPException(
            status_code=502,
            detail={
                "success": False,
                "error": {
                    "code": "bad_gateway",
                    "message": str(e)
                },
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2),
                "tool": tool
            }
        )
    
    except AIPipelineError as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Record unknown error metrics
        record_ai_request_error(tool, "unknown", duration_ms / 1000)
        
        logger.error(f"[Exec] error trace_id={trace_id} error={e}")
        
        raise HTTPException(
            status_code=502,
            detail={
                "success": False,
                "error": {
                    "code": "unknown",
                    "message": str(e)
                },
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2),
                "tool": tool
            }
        )
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Record validation/unknown error
        record_ai_request_error(tool, "validation", duration_ms / 1000)
        
        logger.error(f"[Exec] unexpected_error trace_id={trace_id} error={e}")
        
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "validation",
                    "message": str(e)
                },
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2),
                "tool": tool
            }
        )
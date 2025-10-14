"""
AI Tools Proxy Router
Proxies tool requests to ai-pipeline service
"""
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import time
import uuid
import httpx

from config import config


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/tools", tags=["AI Tools"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ToolListResponse(BaseModel):
    """Response from tool list"""
    success: bool
    tools: List[Dict[str, Any]]
    total: int
    filters: Dict[str, Any]


class ToolExecuteRequest(BaseModel):
    """Request to execute a tool"""
    name: str = Field(..., description="Tool name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    trace_id: Optional[str] = Field(default=None, description="Optional trace ID")


class ToolExecuteResponse(BaseModel):
    """Response from tool execution"""
    success: bool
    tool: str
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float
    trace_id: str
    timestamp: str
    exit_code: Optional[int] = None
    truncated: bool = False
    redacted: bool = False


# ============================================================================
# GLOBAL CLIENT
# ============================================================================

_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client singleton"""
    global _http_client
    
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            follow_redirects=True
        )
        logger.info("[Tools] HTTP client initialized")
    
    return _http_client


# ============================================================================
# ROUTES
# ============================================================================

@router.get("/list", response_model=ToolListResponse)
async def list_tools(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id")
):
    """
    List available tools from ai-pipeline
    
    This endpoint proxies to ai-pipeline /tools/list with optional filtering.
    
    Args:
        platform: Filter by platform (windows, linux, cross-platform)
        category: Filter by category (network, system, database, etc.)
        tags: Comma-separated list of tags
        x_trace_id: Optional trace ID from header
    
    Returns:
        ToolListResponse with list of tools
    """
    start_time = time.perf_counter()
    trace_id = x_trace_id or str(uuid.uuid4())
    
    logger.info(
        f"[Tools] [{trace_id}] List request: "
        f"platform={platform}, category={category}, tags={tags}"
    )
    
    try:
        # Build query parameters
        params = {}
        if platform:
            params['platform'] = platform
        if category:
            params['category'] = category
        if tags:
            params['tags'] = tags
        
        # Call ai-pipeline
        client = get_http_client()
        url = f"{config.AI_PIPELINE_BASE_URL}/tools/list"
        
        response = await client.get(
            url,
            params=params,
            headers={"X-Trace-Id": trace_id}
        )
        
        # Check response
        if response.status_code >= 400:
            logger.error(
                f"[Tools] [{trace_id}] AI Pipeline error: "
                f"status={response.status_code}"
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "success": False,
                    "error": f"AI Pipeline returned {response.status_code}",
                    "trace_id": trace_id
                }
            )
        
        # Parse response
        result = response.json()
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[Tools] [{trace_id}] List success: "
            f"total={result.get('total', 0)}, duration={duration_ms:.2f}ms"
        )
        
        return ToolListResponse(**result)
    
    except httpx.TimeoutException as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"[Tools] [{trace_id}] Timeout: {e}")
        
        raise HTTPException(
            status_code=504,
            detail={
                "success": False,
                "error": "Request timed out",
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2)
            }
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"[Tools] [{trace_id}] Error: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2)
            }
        )


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id")
):
    """
    Execute a tool via ai-pipeline
    
    This endpoint proxies tool execution requests to ai-pipeline with full
    safety controls (timeouts, output limits, redaction).
    
    Args:
        request: Tool execution request
        x_trace_id: Optional trace ID from header
    
    Returns:
        ToolExecuteResponse with execution result
    """
    start_time = time.perf_counter()
    trace_id = x_trace_id or request.trace_id or str(uuid.uuid4())
    
    logger.info(
        f"[Tools] [{trace_id}] Execute request: "
        f"tool={request.name}, params={list(request.params.keys())}"
    )
    
    try:
        # Call ai-pipeline
        client = get_http_client()
        url = f"{config.AI_PIPELINE_BASE_URL}/tools/execute"
        
        payload = {
            "name": request.name,
            "params": request.params,
            "trace_id": trace_id
        }
        
        response = await client.post(
            url,
            json=payload,
            headers={"X-Trace-Id": trace_id}
        )
        
        # Check response
        if response.status_code >= 400:
            error_detail = response.text
            logger.error(
                f"[Tools] [{trace_id}] AI Pipeline error: "
                f"status={response.status_code}, detail={error_detail[:200]}"
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "success": False,
                    "error": f"AI Pipeline returned {response.status_code}",
                    "trace_id": trace_id
                }
            )
        
        # Parse response
        result = response.json()
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[Tools] [{trace_id}] Execute completed: "
            f"success={result.get('success')}, duration={duration_ms:.2f}ms"
        )
        
        return ToolExecuteResponse(**result)
    
    except httpx.TimeoutException as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"[Tools] [{trace_id}] Timeout: {e}")
        
        raise HTTPException(
            status_code=504,
            detail={
                "success": False,
                "tool": request.name,
                "error": "Request timed out",
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"[Tools] [{trace_id}] Error: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "tool": request.name,
                "error": str(e),
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        )
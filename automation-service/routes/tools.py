"""
AI Tools Router v2 - Unified Tool Registry and Execution

Responsibilities:
- List tools from unified registry
- Execute tools via unified runner
- Support hot-reload of tool catalog
- Apply asset intelligence server-side
- Return consistent response format
"""

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import time
import uuid
import os

from tool_registry import get_registry
from tool_runner import ToolRunner
from execution_enricher import ExecutionEnricher

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
    filters: Optional[Dict[str, Any]] = None


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
    metadata: Optional[Dict[str, Any]] = None  # For enrichment errors and additional context


class ToolReloadResponse(BaseModel):
    """Response from tool reload"""
    success: bool
    count: int
    tools: List[str]
    missing_required: Optional[List[str]] = None
    catalog_dirs: Optional[List[str]] = None
    error: Optional[str] = None


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
    List available tools from unified registry
    
    This endpoint returns tools from the merged registry (built-ins + YAML catalog).
    
    Args:
        platform: Filter by platform (windows, linux, cross-platform)
        category: Filter by category (network, system, database, asset, etc.)
        tags: Comma-separated list of tags (not yet implemented)
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
        registry = get_registry()
        tools = registry.list_tools(platform=platform, category=category)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[Tools] [{trace_id}] List success: "
            f"total={len(tools)}, duration={duration_ms:.2f}ms"
        )
        
        return ToolListResponse(
            success=True,
            tools=tools,
            total=len(tools),
            filters={
                'platform': platform,
                'category': category,
                'tags': tags
            }
        )
    
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


@router.post("/reload", response_model=ToolReloadResponse)
async def reload_tools(
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id")
):
    """
    Reload tool registry from catalog directories
    
    This endpoint triggers a hot-reload of the tool catalog without restarting
    the service. Useful for adding/removing tools dynamically.
    
    Args:
        x_trace_id: Optional trace ID from header
    
    Returns:
        ToolReloadResponse with reload status
    """
    start_time = time.perf_counter()
    trace_id = x_trace_id or str(uuid.uuid4())
    
    logger.info(f"[Tools] [{trace_id}] Reload request")
    
    try:
        registry = get_registry()
        result = registry.reload()
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[Tools] [{trace_id}] Reload complete: "
            f"count={result['count']}, duration={duration_ms:.2f}ms"
        )
        
        return ToolReloadResponse(**result)
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"[Tools] [{trace_id}] Reload error: {e}")
        
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
    tool_request: ToolExecuteRequest,
    req: Request,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id")
):
    """
    Execute a tool via unified runner
    
    This endpoint executes tools either locally or via ai-pipeline based on
    the tool's source configuration. For asset-aware tools, it automatically:
    1. Resolves host connection profile from asset database
    2. Fetches credentials server-side (never exposed to client)
    3. Merges parameters and executes
    4. Returns missing_credentials error if credentials not found
    
    Args:
        tool_request: Tool execution request
        req: FastAPI Request object
        x_trace_id: Optional trace ID from header
    
    Returns:
        ToolExecuteResponse with execution result
    """
    start_time = time.perf_counter()
    trace_id = x_trace_id or tool_request.trace_id or str(uuid.uuid4())
    
    logger.info(
        f"[Tools] [{trace_id}] Execute request: "
        f"tool={tool_request.name}, params={list(tool_request.params.keys())}"
    )
    
    try:
        # Get tool definition from registry
        registry = get_registry()
        tool_def = registry.get_tool(tool_request.name)
        
        if not tool_def:
            logger.error(f"[Tools] [{trace_id}] Tool not found: {tool_request.name}")
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return ToolExecuteResponse(
                success=False,
                tool=tool_request.name,
                error=f"Tool not found: {tool_request.name}",
                duration_ms=round(duration_ms, 2),
                trace_id=trace_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )
        
        # Get asset façade and secrets manager from app state
        asset_facade = getattr(req.app.state, 'asset_facade', None)
        secrets_manager = getattr(req.app.state, 'secrets_manager', None)
        internal_key = os.getenv("INTERNAL_KEY", "")
        
        # Apply execution enrichment (auto asset lookup + credential resolution)
        enriched_params = tool_request.params
        if asset_facade and secrets_manager and internal_key:
            enricher = ExecutionEnricher(asset_facade, secrets_manager, internal_key)
            enriched_params, enrichment_error = await enricher.enrich_execution(
                tool_name=tool_request.name,
                tool_def=tool_def,
                parameters=tool_request.params,
                trace_id=trace_id
            )
            
            # If enrichment failed with structured error, return it
            if enrichment_error:
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                logger.warning(
                    f"[Tools] [{trace_id}] Enrichment failed: {enrichment_error.get('error')}"
                )
                
                return ToolExecuteResponse(
                    success=False,
                    tool=tool_request.name,
                    error=enrichment_error.get('error'),
                    duration_ms=round(duration_ms, 2),
                    trace_id=trace_id,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    metadata=enrichment_error  # Include full error details in metadata
                )
        
        # Create runner and execute
        runner = ToolRunner(asset_facade=asset_facade, secrets_manager=secrets_manager)
        
        try:
            result = await runner.execute(
                tool_name=tool_request.name,
                tool_def=tool_def,
                parameters=enriched_params,  # Use enriched parameters
                trace_id=trace_id
            )
            
            return ToolExecuteResponse(**result)
            
        except Exception as e:
            # Check for missing_credentials error
            error_str = str(e)
            if error_str.startswith('missing_credentials:'):
                # Parse error details
                parts = error_str.split(':', 1)[1].split(',')
                error_details = {}
                for part in parts:
                    key, value = part.split('=')
                    error_details[key] = value
                
                logger.warning(
                    f"[Tools] [{trace_id}] Missing credentials: "
                    f"host={error_details.get('host')}, purpose={error_details.get('purpose')}"
                )
                
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                return ToolExecuteResponse(
                    success=False,
                    tool=tool_request.name,
                    error=f"missing_credentials",
                    duration_ms=round(duration_ms, 2),
                    trace_id=trace_id,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                )
            else:
                raise
        
        finally:
            await runner.close()
    
    except HTTPException:
        raise
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"[Tools] [{trace_id}] Error: {e}")
        
        return ToolExecuteResponse(
            success=False,
            tool=tool_request.name,
            error=str(e),
            duration_ms=round(duration_ms, 2),
            trace_id=trace_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
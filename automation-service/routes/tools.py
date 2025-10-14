"""
AI Tools Proxy Router
Proxies tool requests to ai-pipeline service
"""
from fastapi import APIRouter, Header, HTTPException, Query, Request
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
    tool_request: ToolExecuteRequest,
    req: Request,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id")
):
    """
    Execute a tool via ai-pipeline with asset intelligence
    
    This endpoint proxies tool execution requests to ai-pipeline with full
    safety controls (timeouts, output limits, redaction).
    
    For asset-aware tools (windows_list_directory, etc.), this endpoint:
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
        # ====================================================================
        # ASSET INTELLIGENCE: Resolve host profile and credentials
        # ====================================================================
        
        params = tool_request.params.copy()
        
        # Check if this is an asset-aware tool
        if tool_request.name in ['windows_list_directory', 'asset_count', 'asset_search']:
            
            # Handle asset_count and asset_search directly
            if tool_request.name == 'asset_count':
                logger.info(f"[Tools] [{trace_id}] Executing asset_count directly")
                try:
                    facade = req.app.state.asset_facade if hasattr(req.app.state, 'asset_facade') else None
                    if not facade:
                        raise Exception("Asset façade not initialized")
                    
                    result = await facade.count_assets(
                        os=params.get('os'),
                        hostname=params.get('hostname'),
                        ip=params.get('ip'),
                        status=params.get('status'),
                        environment=params.get('environment')
                    )
                    
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    return ToolExecuteResponse(
                        success=True,
                        tool=tool_request.name,
                        output=str(result),
                        duration_ms=duration_ms,
                        trace_id=trace_id,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    )
                except Exception as e:
                    logger.error(f"[Tools] [{trace_id}] asset_count failed: {e}")
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    return ToolExecuteResponse(
                        success=False,
                        tool=tool_request.name,
                        error=str(e),
                        duration_ms=duration_ms,
                        trace_id=trace_id,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    )
            
            elif tool_request.name == 'asset_search':
                logger.info(f"[Tools] [{trace_id}] Executing asset_search directly")
                try:
                    facade = req.app.state.asset_facade if hasattr(req.app.state, 'asset_facade') else None
                    if not facade:
                        raise Exception("Asset façade not initialized")
                    
                    result = await facade.search_assets(
                        os=params.get('os'),
                        hostname=params.get('hostname'),
                        ip=params.get('ip'),
                        status=params.get('status'),
                        environment=params.get('environment'),
                        limit=params.get('limit', 50)
                    )
                    
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    return ToolExecuteResponse(
                        success=True,
                        tool=tool_request.name,
                        output=str(result),
                        duration_ms=duration_ms,
                        trace_id=trace_id,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    )
                except Exception as e:
                    logger.error(f"[Tools] [{trace_id}] asset_search failed: {e}")
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    return ToolExecuteResponse(
                        success=False,
                        tool=tool_request.name,
                        error=str(e),
                        duration_ms=duration_ms,
                        trace_id=trace_id,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    )
            
            # Handle windows_list_directory with asset intelligence
            elif tool_request.name == 'windows_list_directory' and 'host' in params:
                host = params['host']
                logger.info(f"[Tools] [{trace_id}] Resolving asset profile for host: {host}")
                
                try:
                    # Get connection profile
                    facade = req.app.state.asset_facade if req else None
                    if facade:
                        profile = await facade.get_connection_profile(host)
                        
                        if profile.get('found'):
                            logger.info(f"[Tools] [{trace_id}] Asset profile found: {profile.get('hostname')}")
                            
                            # Merge connection parameters from profile
                            if 'winrm' in profile:
                                params.setdefault('port', profile['winrm']['port'])
                                params.setdefault('use_ssl', profile['winrm']['use_ssl'])
                                if profile['winrm'].get('domain'):
                                    params.setdefault('domain', profile['winrm']['domain'])
                            
                            # Try to fetch credentials server-side
                            secrets_manager = req.app.state.secrets_manager if req and hasattr(req.app.state, 'secrets_manager') else None
                            if secrets_manager:
                                try:
                                    creds = secrets_manager.lookup_credential(host, 'winrm', accessed_by='tools-api')
                                    if creds:
                                        logger.info(f"[Tools] [{trace_id}] Credentials found for host (password masked)")
                                        params.setdefault('username', creds['username'])
                                        params.setdefault('password', creds['password'])
                                        if creds.get('domain'):
                                            params.setdefault('domain', creds['domain'])
                                except Exception as e:
                                    logger.warning(f"[Tools] [{trace_id}] Credential lookup failed: {e}")
                        else:
                            logger.info(f"[Tools] [{trace_id}] Host not found in asset database")
                    
                    # Check if we still need credentials
                    if not params.get('username') or not params.get('password'):
                        logger.warning(f"[Tools] [{trace_id}] Missing credentials for windows_list_directory")
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        
                        # Return structured missing_credentials error
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "success": False,
                                "error": "missing_credentials",
                                "missing_params": [
                                    {"name": "username", "type": "string", "secret": False, "description": "Windows username"},
                                    {"name": "password", "type": "string", "secret": True, "description": "Windows password"},
                                    {"name": "domain", "type": "string", "secret": False, "optional": True, "description": "Windows domain (optional)"}
                                ],
                                "hint": f"Credentials not found for host {host}. Please provide username and password.",
                                "trace_id": trace_id,
                                "duration_ms": round(duration_ms, 2)
                            }
                        )
                
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"[Tools] [{trace_id}] Asset intelligence failed: {e}")
                    # Continue with original params if asset intelligence fails
        
        # ====================================================================
        # EXECUTE VIA AI-PIPELINE
        # ====================================================================
        
        # Call ai-pipeline
        client = get_http_client()
        url = f"{config.AI_PIPELINE_BASE_URL}/tools/execute"
        
        payload = {
            "name": tool_request.name,
            "params": params,
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
                "tool": tool_request.name,
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
                "tool": tool_request.name,
                "error": str(e),
                "trace_id": trace_id,
                "duration_ms": round(duration_ms, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        )
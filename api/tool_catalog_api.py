"""
Tool Catalog REST API
Provides CRUD operations for managing tools in the database-backed catalog system.

Endpoints:
- GET    /api/v1/tools                    # List all tools
- GET    /api/v1/tools/{name}             # Get tool by name
- GET    /api/v1/tools/{name}/versions    # Get all versions
- POST   /api/v1/tools                    # Create new tool
- PUT    /api/v1/tools/{name}             # Update tool
- DELETE /api/v1/tools/{name}             # Delete tool
- PATCH  /api/v1/tools/{name}/enable      # Enable tool
- PATCH  /api/v1/tools/{name}/disable     # Disable tool

- GET    /api/v1/tools/search             # Search tools
- GET    /api/v1/tools/platform/{platform} # Get by platform
- GET    /api/v1/tools/category/{category} # Get by category

- POST   /api/v1/tools/{name}/validate    # Validate tool definition
- POST   /api/v1/tools/import             # Bulk import from YAML
- POST   /api/v1/tools/export             # Export to YAML

- GET    /api/v1/capabilities             # List all capabilities
- GET    /api/v1/capabilities/{name}/tools # Get tools by capability
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Path
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime
import yaml
import os

from pipeline.services.tool_catalog_service import ToolCatalogService
from pipeline.services.hot_reload_service import get_hot_reload_service, ReloadTrigger

logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ToolDefaults(BaseModel):
    """Tool default settings"""
    accuracy_level: Optional[str] = "real-time"
    freshness: Optional[str] = "live"
    data_source: Optional[str] = "direct"
    
class ToolDependency(BaseModel):
    """Tool dependency definition"""
    name: str
    type: str  # service, package, binary
    required: bool = True
    version: Optional[str] = None

class PolicyConfig(BaseModel):
    """Policy configuration for a pattern"""
    max_cost: Optional[int] = None
    requires_approval: bool = False
    production_safe: bool = True
    max_execution_time_ms: Optional[int] = None
    allowed_environments: Optional[List[str]] = None

class PreferenceMatchScores(BaseModel):
    """Preference match scores"""
    speed: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    cost: float = Field(ge=0.0, le=1.0)
    complexity: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)

class PatternInput(BaseModel):
    """Pattern input definition"""
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None

class PatternOutput(BaseModel):
    """Pattern output definition"""
    name: str
    type: str
    description: Optional[str] = None

class PatternExample(BaseModel):
    """Pattern usage example"""
    description: str
    input: Dict[str, Any]
    expected_output: Dict[str, Any]

class PatternCreate(BaseModel):
    """Pattern creation request"""
    pattern_name: str
    description: str
    typical_use_cases: List[str] = []
    time_estimate_ms: str  # Expression like "500 + 0.1 * file_size_kb"
    cost_estimate: str     # Expression like "1"
    complexity_score: float = Field(ge=0.0, le=1.0)
    scope: str
    completeness: str
    limitations: List[str] = []
    policy: PolicyConfig
    preference_match: PreferenceMatchScores
    required_inputs: List[PatternInput] = []
    expected_outputs: List[PatternOutput] = []
    examples: List[PatternExample] = []

class CapabilityCreate(BaseModel):
    """Capability creation request"""
    capability_name: str
    description: str
    patterns: List[PatternCreate]

class ToolCreate(BaseModel):
    """Tool creation request"""
    tool_name: str
    version: str = "1.0"
    description: str
    platform: str  # linux, windows, network, scheduler, custom
    category: str  # system, network, automation, monitoring, security
    status: str = "active"
    enabled: bool = True
    defaults: ToolDefaults = ToolDefaults()
    dependencies: List[ToolDependency] = []
    metadata: Dict[str, Any] = {}
    capabilities: List[CapabilityCreate]
    created_by: Optional[str] = None

    @validator('platform')
    def validate_platform(cls, v):
        valid_platforms = ['linux', 'windows', 'network', 'scheduler', 'custom']
        if v not in valid_platforms:
            raise ValueError(f'Platform must be one of: {", ".join(valid_platforms)}')
        return v

    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['system', 'network', 'automation', 'monitoring', 'security']
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'deprecated', 'disabled', 'testing']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

class ToolUpdate(BaseModel):
    """Tool update request"""
    description: Optional[str] = None
    status: Optional[str] = None
    enabled: Optional[bool] = None
    defaults: Optional[ToolDefaults] = None
    dependencies: Optional[List[ToolDependency]] = None
    metadata: Optional[Dict[str, Any]] = None
    updated_by: Optional[str] = None

class ToolResponse(BaseModel):
    """Tool response"""
    id: int
    tool_name: str
    version: str
    description: str
    platform: str
    category: str
    status: str
    enabled: bool
    defaults: Dict[str, Any]
    dependencies: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]

class ToolListResponse(BaseModel):
    """Tool list response"""
    tools: List[ToolResponse]
    total: int
    page: int
    page_size: int

class ValidationResult(BaseModel):
    """Validation result"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []

class BulkImportRequest(BaseModel):
    """Bulk import request"""
    yaml_content: str
    overwrite: bool = False
    validate_only: bool = False

class BulkImportResponse(BaseModel):
    """Bulk import response"""
    success: bool
    imported_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []
    warnings: List[str] = []

class CapabilityResponse(BaseModel):
    """Capability response"""
    capability_name: str
    tool_count: int
    tools: List[str]

# ============================================================================
# API ROUTER
# ============================================================================

router = APIRouter(prefix="/api/v1/tools", tags=["Tool Catalog"])

# Global service instances (will be initialized on startup)
_catalog_service: Optional[ToolCatalogService] = None
_hot_reload_service = None

def get_catalog_service() -> ToolCatalogService:
    """Get or create catalog service instance"""
    global _catalog_service
    if _catalog_service is None:
        database_url = os.getenv('DATABASE_URL', 'postgresql://opsconductor:opsconductor@postgres:5432/opsconductor')
        _catalog_service = ToolCatalogService(database_url)
    return _catalog_service

def get_reload_service():
    """Get or create hot reload service instance"""
    global _hot_reload_service
    if _hot_reload_service is None:
        _hot_reload_service = get_hot_reload_service(
            enable_periodic_refresh=False  # Disabled by default, can be enabled via env var
        )
        # Register ProfileLoader reload handler
        _register_profile_loader_handler()
    return _hot_reload_service

def _register_profile_loader_handler():
    """Register ProfileLoader as a reload handler"""
    from pipeline.stages.stage_b.profile_loader import get_loader
    
    def profile_loader_reload_handler(event):
        """Handler to reload ProfileLoader on tool updates"""
        try:
            loader = get_loader(use_database=True)
            loader.reload(tool_name=event.tool_name)
            logger.info(f"ProfileLoader reloaded for tool: {event.tool_name or 'all'}")
        except Exception as e:
            logger.error(f"ProfileLoader reload failed: {e}")
            raise
    
    reload_service = get_reload_service()
    reload_service.register_reload_handler(profile_loader_reload_handler)
    logger.info("ProfileLoader reload handler registered")

def trigger_tool_reload(tool_name: Optional[str] = None, triggered_by: str = "api"):
    """
    Trigger a hot reload for tool changes
    
    Args:
        tool_name: Specific tool that changed (None = all tools)
        triggered_by: Who triggered the reload
    """
    try:
        reload_service = get_reload_service()
        event = reload_service.trigger_reload(
            trigger=ReloadTrigger.API_UPDATE,
            tool_name=tool_name,
            triggered_by=triggered_by,
            reason=f"Tool {'updated' if tool_name else 'catalog updated'}"
        )
        
        if not event.success:
            logger.warning(f"Reload triggered but had errors: {event.error_message}")
        
        return event
    except Exception as e:
        logger.error(f"Failed to trigger reload: {e}")
        # Don't fail the API call if reload fails
        return None

# ============================================================================
# HEALTH CHECK (must be before dynamic routes)
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the Tool Catalog API.
    """
    try:
        service = get_catalog_service()
        tool_count = len(service.get_all_tools())
        
        return {
            "status": "healthy",
            "service": "Tool Catalog API",
            "version": "1.0.0",
            "tool_count": tool_count,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Tool Catalog API",
            "version": "1.0.0",
            "error": str(e)
        }

# ============================================================================
# TOOL CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=ToolListResponse)
async def list_tools(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status")
):
    """
    List all tools with optional filtering and pagination.
    
    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    - platform: Filter by platform (linux, windows, network, scheduler, custom)
    - category: Filter by category (system, network, automation, monitoring, security)
    - status: Filter by status (active, deprecated, disabled, testing)
    - enabled: Filter by enabled status (true/false)
    """
    try:
        service = get_catalog_service()
        
        # Get all tools (service handles filtering)
        all_tools = service.get_all_tools()
        
        # Apply filters
        filtered_tools = all_tools
        if platform:
            filtered_tools = [t for t in filtered_tools if t.get('platform') == platform]
        if category:
            filtered_tools = [t for t in filtered_tools if t.get('category') == category]
        if status:
            filtered_tools = [t for t in filtered_tools if t.get('status') == status]
        if enabled is not None:
            filtered_tools = [t for t in filtered_tools if t.get('enabled') == enabled]
        
        # Pagination
        total = len(filtered_tools)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_tools = filtered_tools[start_idx:end_idx]
        
        return ToolListResponse(
            tools=[ToolResponse(**tool) for tool in paginated_tools],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# METRICS ENDPOINTS (must be before /{tool_name} to avoid route conflicts)
# ============================================================================

@router.get("/metrics")
async def get_metrics():
    """
    Get system metrics.
    
    Returns comprehensive metrics including:
    - Tool loading performance
    - Cache effectiveness
    - API performance
    - Database performance
    - Hot reload metrics
    """
    try:
        from pipeline.services.metrics_collector import get_metrics_collector
        metrics_collector = get_metrics_collector()
        
        return metrics_collector.get_metrics()
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus format.
    
    Returns metrics in Prometheus exposition format for scraping.
    """
    try:
        from pipeline.services.metrics_collector import get_metrics_collector
        
        metrics_collector = get_metrics_collector()
        
        return PlainTextResponse(
            content=metrics_collector.get_prometheus_metrics(),
            media_type="text/plain; version=0.0.4"
        )
        
    except Exception as e:
        logger.error(f"Error getting Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/stats")
async def get_performance_stats():
    """
    Get performance statistics including cache, connection pool, and database metrics.
    
    Returns detailed performance metrics for monitoring and optimization.
    """
    try:
        service = get_catalog_service()
        stats = service.get_performance_stats()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "performance": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tool_name}", response_model=ToolResponse)
async def get_tool(
    tool_name: str = Path(..., description="Tool name")
):
    """
    Get a specific tool by name (returns latest version).
    """
    try:
        service = get_catalog_service()
        tool = service.get_tool_by_name(tool_name)
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return ToolResponse(**tool)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tool_name}/versions")
async def get_tool_versions(
    tool_name: str = Path(..., description="Tool name")
):
    """
    Get all versions of a specific tool.
    """
    try:
        service = get_catalog_service()
        versions = service.get_tool_versions(tool_name)
        
        if not versions:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return {
            "tool_name": tool_name,
            "versions": versions,
            "total_versions": len(versions)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool versions for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=ToolResponse, status_code=201)
async def create_tool(
    tool: ToolCreate = Body(..., description="Tool definition")
):
    """
    Create a new tool in the catalog.
    
    **Request Body:** Complete tool definition including capabilities and patterns.
    """
    try:
        service = get_catalog_service()
        
        # Check if tool already exists
        existing_tool = service.get_tool_by_name(tool.tool_name, version=tool.version)
        if existing_tool:
            raise HTTPException(
                status_code=409, 
                detail=f"Tool '{tool.tool_name}' version '{tool.version}' already exists"
            )
        
        # Create tool
        tool_id = service.create_tool(
            tool_name=tool.tool_name,
            version=tool.version,
            description=tool.description,
            platform=tool.platform,
            category=tool.category,
            status=tool.status,
            enabled=tool.enabled,
            defaults=tool.defaults.dict(),
            dependencies=[d.dict() for d in tool.dependencies],
            metadata=tool.metadata,
            created_by=tool.created_by
        )
        
        # Add capabilities and patterns
        for capability in tool.capabilities:
            cap_id = service.add_capability(
                tool_id=tool_id,
                capability_name=capability.capability_name,
                description=capability.description
            )
            
            for pattern in capability.patterns:
                service.add_pattern(
                    capability_id=cap_id,
                    pattern_name=pattern.pattern_name,
                    description=pattern.description,
                    typical_use_cases=pattern.typical_use_cases,
                    time_estimate_ms=pattern.time_estimate_ms,
                    cost_estimate=pattern.cost_estimate,
                    complexity_score=pattern.complexity_score,
                    scope=pattern.scope,
                    completeness=pattern.completeness,
                    limitations=pattern.limitations,
                    policy=pattern.policy.dict(),
                    preference_match=pattern.preference_match.dict(),
                    required_inputs=[i.dict() for i in pattern.required_inputs],
                    expected_outputs=[o.dict() for o in pattern.expected_outputs],
                    examples=[e.dict() for e in pattern.examples]
                )
        
        # Trigger hot reload
        trigger_tool_reload(tool_name=tool.tool_name, triggered_by=tool.created_by or "api")
        
        # Return created tool
        created_tool = service.get_tool_by_name(tool.tool_name, version=tool.version)
        return ToolResponse(**created_tool)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tool_name}", response_model=ToolResponse)
async def update_tool(
    tool_name: str = Path(..., description="Tool name"),
    update: ToolUpdate = Body(..., description="Tool updates")
):
    """
    Update an existing tool (creates new version).
    """
    try:
        service = get_catalog_service()
        
        # Check if tool exists
        existing_tool = service.get_tool_by_name(tool_name)
        if not existing_tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Update tool
        success = service.update_tool_by_name(
            tool_name=tool_name,
            description=update.description,
            status=update.status,
            enabled=update.enabled,
            defaults=update.defaults.dict() if update.defaults else None,
            dependencies=[d.dict() for d in update.dependencies] if update.dependencies else None,
            metadata=update.metadata,
            updated_by=update.updated_by
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update tool")
        
        # Trigger hot reload
        trigger_tool_reload(tool_name=tool_name, triggered_by=update.updated_by or "api")
        
        # Return updated tool
        updated_tool = service.get_tool_by_name(tool_name)
        return ToolResponse(**updated_tool)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tool_name}", status_code=204)
async def delete_tool(
    tool_name: str = Path(..., description="Tool name"),
    version: Optional[str] = Query(None, description="Specific version to delete (default: all versions)")
):
    """
    Delete a tool (or specific version).
    
    **Warning:** This is a destructive operation and cannot be undone.
    """
    try:
        service = get_catalog_service()
        
        # Check if tool exists
        existing_tool = service.get_tool_by_name(tool_name, version=version)
        if not existing_tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Delete tool
        success = service.delete_tool_by_name(tool_name, version=version)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete tool")
        
        # Trigger hot reload
        trigger_tool_reload(tool_name=tool_name, triggered_by="api")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{tool_name}/enable", response_model=ToolResponse)
async def enable_tool(
    tool_name: str = Path(..., description="Tool name")
):
    """
    Enable a tool.
    """
    try:
        service = get_catalog_service()
        
        success = service.update_tool_by_name(tool_name=tool_name, enabled=True)
        if not success:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Trigger hot reload
        trigger_tool_reload(tool_name=tool_name, triggered_by="api")
        
        updated_tool = service.get_tool_by_name(tool_name)
        return ToolResponse(**updated_tool)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{tool_name}/disable", response_model=ToolResponse)
async def disable_tool(
    tool_name: str = Path(..., description="Tool name")
):
    """
    Disable a tool.
    """
    try:
        service = get_catalog_service()
        
        success = service.update_tool_by_name(tool_name=tool_name, enabled=False)
        if not success:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Trigger hot reload
        trigger_tool_reload(tool_name=tool_name, triggered_by="api")
        
        updated_tool = service.get_tool_by_name(tool_name)
        return ToolResponse(**updated_tool)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SEARCH & FILTER ENDPOINTS
# ============================================================================

@router.get("/search/query")
async def search_tools(
    q: str = Query(..., description="Search query"),
    fields: List[str] = Query(["tool_name", "description"], description="Fields to search")
):
    """
    Search tools by query string.
    
    **Query Parameters:**
    - q: Search query
    - fields: Fields to search in (tool_name, description, category, platform)
    """
    try:
        service = get_catalog_service()
        all_tools = service.get_all_tools()
        
        # Simple text search
        query_lower = q.lower()
        results = []
        
        for tool in all_tools:
            for field in fields:
                if field in tool and query_lower in str(tool[field]).lower():
                    results.append(tool)
                    break
        
        return {
            "query": q,
            "fields": fields,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platform/{platform}")
async def get_tools_by_platform(
    platform: str = Path(..., description="Platform name")
):
    """
    Get all tools for a specific platform.
    """
    try:
        service = get_catalog_service()
        all_tools = service.get_all_tools()
        
        platform_tools = [t for t in all_tools if t.get('platform') == platform]
        
        return {
            "platform": platform,
            "tools": platform_tools,
            "total": len(platform_tools)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools by platform: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category}")
async def get_tools_by_category(
    category: str = Path(..., description="Category name")
):
    """
    Get all tools for a specific category.
    """
    try:
        service = get_catalog_service()
        all_tools = service.get_all_tools()
        
        category_tools = [t for t in all_tools if t.get('category') == category]
        
        return {
            "category": category,
            "tools": category_tools,
            "total": len(category_tools)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools by category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================

@router.post("/{tool_name}/validate", response_model=ValidationResult)
async def validate_tool(
    tool_name: str = Path(..., description="Tool name")
):
    """
    Validate a tool definition.
    """
    try:
        service = get_catalog_service()
        tool = service.get_tool_by_name(tool_name)
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Perform validation
        errors = []
        warnings = []
        
        # Basic validation
        if not tool.get('description'):
            errors.append("Missing description")
        if not tool.get('platform'):
            errors.append("Missing platform")
        if not tool.get('category'):
            errors.append("Missing category")
        
        # Check for capabilities
        capabilities = service.get_tool_capabilities(tool['id'])
        if not capabilities:
            warnings.append("Tool has no capabilities defined")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/import", response_model=BulkImportResponse)
async def bulk_import_tools(
    request: BulkImportRequest = Body(..., description="Bulk import request")
):
    """
    Bulk import tools from YAML content.
    
    **Request Body:**
    - yaml_content: YAML content containing tool definitions
    - overwrite: Whether to overwrite existing tools (default: false)
    - validate_only: Only validate without importing (default: false)
    """
    try:
        # Parse YAML
        try:
            tool_data = yaml.safe_load(request.yaml_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
        
        # Validate structure
        if not isinstance(tool_data, dict):
            raise HTTPException(status_code=400, detail="YAML must contain a tool definition object")
        
        if request.validate_only:
            # Just validate
            return BulkImportResponse(
                success=True,
                imported_count=0,
                failed_count=0,
                warnings=["Validation only - no tools imported"]
            )
        
        # Import tool
        service = get_catalog_service()
        
        try:
            # Create tool from YAML data
            tool_create = ToolCreate(**tool_data)
            
            # Check if exists
            existing = service.get_tool(tool_create.tool_name, version=tool_create.version)
            if existing and not request.overwrite:
                return BulkImportResponse(
                    success=False,
                    imported_count=0,
                    failed_count=1,
                    errors=[{
                        "tool": tool_create.tool_name,
                        "error": "Tool already exists (use overwrite=true to replace)"
                    }]
                )
            
            # Delete existing if overwrite
            if existing and request.overwrite:
                service.delete_tool(tool_create.tool_name, version=tool_create.version)
            
            # Create tool (reuse create_tool logic)
            tool_id = service.create_tool(
                tool_name=tool_create.tool_name,
                version=tool_create.version,
                description=tool_create.description,
                platform=tool_create.platform,
                category=tool_create.category,
                status=tool_create.status,
                enabled=tool_create.enabled,
                defaults=tool_create.defaults.dict(),
                dependencies=[d.dict() for d in tool_create.dependencies],
                metadata=tool_create.metadata,
                created_by=tool_create.created_by
            )
            
            # Add capabilities
            for capability in tool_create.capabilities:
                cap_id = service.add_capability(
                    tool_id=tool_id,
                    capability_name=capability.capability_name,
                    description=capability.description
                )
                
                for pattern in capability.patterns:
                    service.add_pattern(
                        capability_id=cap_id,
                        pattern_name=pattern.pattern_name,
                        description=pattern.description,
                        typical_use_cases=pattern.typical_use_cases,
                        time_estimate_ms=pattern.time_estimate_ms,
                        cost_estimate=pattern.cost_estimate,
                        complexity_score=pattern.complexity_score,
                        scope=pattern.scope,
                        completeness=pattern.completeness,
                        limitations=pattern.limitations,
                        policy=pattern.policy.dict(),
                        preference_match=pattern.preference_match.dict(),
                        required_inputs=[i.dict() for i in pattern.required_inputs],
                        expected_outputs=[o.dict() for o in pattern.expected_outputs],
                        examples=[e.dict() for e in pattern.examples]
                    )
            
            # Trigger hot reload
            trigger_tool_reload(tool_name=tool_create.tool_name, triggered_by=tool_create.created_by or "api")
            
            return BulkImportResponse(
                success=True,
                imported_count=1,
                failed_count=0
            )
            
        except Exception as e:
            return BulkImportResponse(
                success=False,
                imported_count=0,
                failed_count=1,
                errors=[{
                    "tool": tool_data.get('tool_name', 'unknown'),
                    "error": str(e)
                }]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk import: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def bulk_export_tools(
    tool_names: List[str] = Body(..., description="List of tool names to export")
):
    """
    Export tools to YAML format.
    """
    try:
        service = get_catalog_service()
        
        exported_tools = []
        for tool_name in tool_names:
            tool = service.get_tool(tool_name)
            if tool:
                # Get full tool structure
                tool_structure = service.get_all_tools_with_structure()
                tool_data = tool_structure.get(tool_name)
                if tool_data:
                    exported_tools.append(tool_data)
        
        # Convert to YAML
        yaml_content = yaml.dump(exported_tools, default_flow_style=False, sort_keys=False)
        
        return {
            "success": True,
            "tool_count": len(exported_tools),
            "yaml_content": yaml_content
        }
        
    except Exception as e:
        logger.error(f"Error exporting tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CAPABILITY ENDPOINTS
# ============================================================================

@router.get("/capabilities/list", response_model=List[CapabilityResponse])
async def list_capabilities():
    """
    List all capabilities across all tools.
    """
    try:
        service = get_catalog_service()
        all_tools = service.get_all_tools()
        
        # Group by capability
        capabilities_map = {}
        for tool in all_tools:
            tool_caps = service.get_tool_capabilities(tool['id'])
            for cap in tool_caps:
                cap_name = cap['capability_name']
                if cap_name not in capabilities_map:
                    capabilities_map[cap_name] = []
                capabilities_map[cap_name].append(tool['tool_name'])
        
        # Convert to response format
        capabilities = [
            CapabilityResponse(
                capability_name=cap_name,
                tool_count=len(tools),
                tools=tools
            )
            for cap_name, tools in capabilities_map.items()
        ]
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Error listing capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities/{capability_name}/tools")
async def get_tools_by_capability(
    capability_name: str = Path(..., description="Capability name")
):
    """
    Get all tools that provide a specific capability.
    """
    try:
        service = get_catalog_service()
        tools = service.get_tools_by_capability(capability_name)
        
        return {
            "capability": capability_name,
            "tools": tools,
            "total": len(tools)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools by capability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HOT RELOAD ENDPOINTS
# ============================================================================

@router.post("/reload")
async def manual_reload(
    tool_name: Optional[str] = Query(None, description="Specific tool to reload (None = all tools)"),
    triggered_by: str = Query("admin", description="Who triggered the reload")
):
    """
    Manually trigger a hot reload of tool catalog.
    
    This will invalidate caches and reload tool definitions from the database.
    Useful after direct database modifications or for testing.
    """
    try:
        event = trigger_tool_reload(tool_name=tool_name, triggered_by=triggered_by)
        
        if event is None:
            raise HTTPException(status_code=500, detail="Failed to trigger reload")
        
        return {
            "success": event.success,
            "trigger": event.trigger.value,
            "tool_name": event.tool_name,
            "triggered_by": event.triggered_by,
            "timestamp": event.timestamp.isoformat(),
            "duration_ms": event.duration_ms,
            "error_message": event.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering reload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reload/history")
async def get_reload_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of events to return"),
    trigger: Optional[str] = Query(None, description="Filter by trigger type")
):
    """
    Get reload history.
    
    Shows recent reload events with their status, duration, and any errors.
    """
    try:
        reload_service = get_reload_service()
        
        # Convert trigger string to enum if provided
        trigger_enum = None
        if trigger:
            try:
                trigger_enum = ReloadTrigger(trigger)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid trigger type. Valid values: {[t.value for t in ReloadTrigger]}"
                )
        
        history = reload_service.get_reload_history(limit=limit, trigger=trigger_enum)
        
        return {
            "history": history,
            "total": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reload history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reload/statistics")
async def get_reload_statistics():
    """
    Get reload statistics.
    
    Shows total reloads, success rate, and configuration.
    """
    try:
        reload_service = get_reload_service()
        stats = reload_service.get_statistics()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting reload statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
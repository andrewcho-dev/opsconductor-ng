"""
Tool Registry - Manages tool specifications and metadata

This module provides a centralized registry for tool definitions,
supporting both file-based (YAML) and database-backed storage.

Features:
- CRUD operations for tool specs
- JSONSchema validation
- Platform filtering (Windows/Linux/cross-platform)
- Hot-reload from catalog directory
- Thread-safe operations
"""

import os
import yaml
import logging
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, validator
import threading

from .metrics import update_registry_size, record_registry_operation

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL SPECIFICATION MODELS
# ============================================================================

class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str  # string, integer, boolean, array
    description: str
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None  # For enumerated values
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern for string validation


class ToolSpec(BaseModel):
    """Tool specification"""
    name: str = Field(..., description="Unique tool identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Tool description")
    category: str = Field(..., description="Tool category (network, system, database, etc.)")
    platform: str = Field(default="cross-platform", description="Target platform (windows, linux, cross-platform)")
    version: str = Field(default="1.0.0", description="Tool version")
    
    # Execution configuration
    command_template: str = Field(..., description="Command template with {param} placeholders")
    timeout_seconds: int = Field(default=30, description="Execution timeout")
    requires_admin: bool = Field(default=False, description="Requires admin/root privileges")
    
    # Parameters
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    
    # Safety and output
    max_output_bytes: int = Field(default=16384, description="Maximum output size")
    redact_patterns: List[str] = Field(default_factory=list, description="Regex patterns to redact from output")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Search tags")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Usage examples")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @validator('platform')
    def validate_platform(cls, v):
        allowed = ['windows', 'linux', 'cross-platform']
        if v not in allowed:
            raise ValueError(f"Platform must be one of {allowed}")
        return v
    
    @validator('category')
    def validate_category(cls, v):
        allowed = ['network', 'system', 'database', 'cloud', 'monitoring', 'security', 'custom']
        if v not in allowed:
            raise ValueError(f"Category must be one of {allowed}")
        return v


# ============================================================================
# TOOL REGISTRY
# ============================================================================

class ToolRegistry:
    """
    Centralized tool registry with file-based and in-memory storage
    
    Features:
    - Load tools from YAML catalog directory
    - CRUD operations
    - Platform filtering
    - Thread-safe access
    - Hot-reload support
    """
    
    def __init__(self, catalog_dir: Optional[str] = None):
        """
        Initialize tool registry
        
        Args:
            catalog_dir: Directory containing tool YAML files
        """
        self.catalog_dir = catalog_dir or os.getenv(
            "TOOLS_SEED_DIR",
            "/app/tools/catalog"
        )
        self._tools: Dict[str, ToolSpec] = {}
        self._lock = threading.RLock()
        self._loaded = False
        
        logger.info(f"[ToolRegistry] Initialized with catalog_dir={self.catalog_dir}")
    
    async def initialize(self):
        """Initialize registry and load tools from catalog"""
        if self._loaded:
            logger.info("[ToolRegistry] Already initialized")
            return
        
        try:
            await self.load_from_catalog()
            self._loaded = True
            logger.info(f"[ToolRegistry] Initialized with {len(self._tools)} tools")
        except Exception as e:
            logger.error(f"[ToolRegistry] Initialization failed: {e}")
            # Continue with empty registry
            self._loaded = True
    
    async def load_from_catalog(self):
        """Load all tools from catalog directory"""
        catalog_path = Path(self.catalog_dir)
        
        if not catalog_path.exists():
            logger.warning(f"[ToolRegistry] Catalog directory not found: {self.catalog_dir}")
            return
        
        loaded_count = 0
        error_count = 0
        
        # Find all YAML files
        yaml_files = list(catalog_path.glob("**/*.yaml")) + list(catalog_path.glob("**/*.yml"))
        
        logger.info(f"[ToolRegistry] Loading tools from {len(yaml_files)} files")
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                # Handle both single tool and list of tools
                tools_data = data if isinstance(data, list) else [data]
                
                for tool_data in tools_data:
                    try:
                        # Add timestamps
                        tool_data['created_at'] = tool_data.get('created_at', datetime.utcnow().isoformat() + 'Z')
                        tool_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                        
                        # Parse and validate
                        tool_spec = ToolSpec(**tool_data)
                        
                        # Register tool
                        with self._lock:
                            self._tools[tool_spec.name] = tool_spec
                        
                        loaded_count += 1
                        logger.debug(f"[ToolRegistry] Loaded tool: {tool_spec.name} from {yaml_file.name}")
                    
                    except Exception as e:
                        error_count += 1
                        logger.error(f"[ToolRegistry] Failed to parse tool in {yaml_file.name}: {e}")
            
            except Exception as e:
                error_count += 1
                logger.error(f"[ToolRegistry] Failed to load {yaml_file.name}: {e}")
        
        logger.info(
            f"[ToolRegistry] Loaded {loaded_count} tools, {error_count} errors"
        )
        
        # Update metrics
        update_registry_size(len(self._tools))
        record_registry_operation('load', error_count == 0)
    
    def register(self, tool_spec: ToolSpec) -> bool:
        """
        Register a new tool or update existing
        
        Args:
            tool_spec: Tool specification
        
        Returns:
            True if registered successfully
        """
        try:
            # Update timestamp
            tool_spec.updated_at = datetime.utcnow().isoformat() + 'Z'
            if not tool_spec.created_at:
                tool_spec.created_at = tool_spec.updated_at
            
            with self._lock:
                self._tools[tool_spec.name] = tool_spec
            
            logger.info(f"[ToolRegistry] Registered tool: {tool_spec.name}")
            
            # Update metrics
            update_registry_size(len(self._tools))
            record_registry_operation('register', True)
            
            return True
        
        except Exception as e:
            logger.error(f"[ToolRegistry] Failed to register tool {tool_spec.name}: {e}")
            record_registry_operation('register', False)
            return False
    
    def get(self, name: str) -> Optional[ToolSpec]:
        """
        Get tool by name
        
        Args:
            name: Tool name
        
        Returns:
            ToolSpec if found, None otherwise
        """
        with self._lock:
            return self._tools.get(name)
    
    def list(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ToolSpec]:
        """
        List tools with optional filtering
        
        Args:
            platform: Filter by platform (windows, linux, cross-platform)
            category: Filter by category
            tags: Filter by tags (any match)
        
        Returns:
            List of matching tool specs
        """
        with self._lock:
            tools = list(self._tools.values())
        
        # Apply filters
        if platform:
            tools = [
                t for t in tools
                if t.platform == platform or t.platform == 'cross-platform'
            ]
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if tags:
            tools = [
                t for t in tools
                if any(tag in t.tags for tag in tags)
            ]
        
        return tools
    
    def delete(self, name: str) -> bool:
        """
        Delete tool by name
        
        Args:
            name: Tool name
        
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                logger.info(f"[ToolRegistry] Deleted tool: {name}")
                
                # Update metrics
                update_registry_size(len(self._tools))
                record_registry_operation('delete', True)
                
                return True
            
            record_registry_operation('delete', False)
            return False
    
    def count(self) -> int:
        """Get total number of registered tools"""
        with self._lock:
            return len(self._tools)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        with self._lock:
            tools = list(self._tools.values())
        
        # Count by platform
        platform_counts = {}
        for tool in tools:
            platform_counts[tool.platform] = platform_counts.get(tool.platform, 0) + 1
        
        # Count by category
        category_counts = {}
        for tool in tools:
            category_counts[tool.category] = category_counts.get(tool.category, 0) + 1
        
        return {
            "total_tools": len(tools),
            "by_platform": platform_counts,
            "by_category": category_counts,
            "catalog_dir": self.catalog_dir,
            "loaded": self._loaded
        }


# ============================================================================
# GLOBAL REGISTRY INSTANCE
# ============================================================================

_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry singleton"""
    global _registry
    
    if _registry is None:
        _registry = ToolRegistry()
    
    return _registry


async def initialize_registry():
    """Initialize global registry (call during startup)"""
    registry = get_tool_registry()
    await registry.initialize()
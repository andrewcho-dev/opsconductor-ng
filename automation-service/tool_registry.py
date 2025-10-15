"""
Tool Registry v2 - Single Source of Truth for AI Tools

Responsibilities:
- Load tools from YAML catalog directories
- Merge with built-in code-defined tools
- Provide unified tool list and metadata
- Support hot-reload without service restart
- Emit Prometheus metrics

Design:
- Catalog search paths from AI_TOOL_CATALOG_DIRS env (colon-separated)
- Default: /workspace/automation-service/tools/catalog:/workspace/tools/catalog
- Deduplicate on tool.name (later path wins, WARN on override)
- Required tools: asset_count, asset_search, windows_list_directory
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Prometheus metrics
tools_loaded_total = Counter(
    'ai_tools_loaded_total',
    'Total number of tools loaded into registry'
)
tools_reload_total = Counter(
    'ai_tools_reload_total',
    'Total number of registry reload operations'
)
tools_reload_errors_total = Counter(
    'ai_tools_reload_errors_total',
    'Total number of registry reload errors'
)
tools_count_gauge = Gauge(
    'ai_tools_count',
    'Current number of tools in registry'
)


class ToolRegistry:
    """
    Tool Registry v2 - Unified tool catalog with hot-reload support
    """
    
    def __init__(self, catalog_dirs: Optional[str] = None):
        """
        Initialize tool registry
        
        Args:
            catalog_dirs: Colon-separated list of catalog directories
                         Default: /workspace/automation-service/tools/catalog:/workspace/tools/catalog
        """
        self.catalog_dirs = self._parse_catalog_dirs(catalog_dirs)
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.required_tools = ['asset_count', 'asset_search', 'windows_list_directory']
        
        logger.info(f"[ToolRegistry] Initialized with catalog dirs: {self.catalog_dirs}")
        
        # Load tools on initialization
        self.reload()
    
    def _parse_catalog_dirs(self, catalog_dirs: Optional[str]) -> List[str]:
        """Parse catalog directories from env or use defaults"""
        if catalog_dirs:
            dirs = catalog_dirs.split(':')
        else:
            # Default paths (try multiple locations for dev/prod compatibility)
            dirs = [
                '/app/tools/catalog',
                '/app/tools_shared/catalog',
                '/workspace/automation-service/tools/catalog',
                '/workspace/tools/catalog',
                './tools/catalog'
            ]
        
        # Filter to existing directories
        existing_dirs = []
        for d in dirs:
            if os.path.isdir(d):
                existing_dirs.append(d)
                logger.info(f"[ToolRegistry] Found catalog directory: {d}")
            else:
                logger.debug(f"[ToolRegistry] Catalog directory not found (skipping): {d}")
        
        # If no directories found, log warning but don't fail (built-in tools still work)
        if not existing_dirs:
            logger.warning("[ToolRegistry] No catalog directories found - only built-in tools will be available")
        
        return existing_dirs
    
    def _load_builtin_tools(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in code-defined tools"""
        builtins = {}
        
        # Built-in tools with minimal metadata
        builtin_definitions = [
            {
                'name': 'asset_count',
                'display_name': 'Asset Count',
                'description': 'Count assets matching criteria (OS, platform, etc.)',
                'category': 'asset',
                'platform': 'cross-platform',
                'source': 'local',
                'parameters': [
                    {'name': 'os', 'type': 'string', 'required': False, 'description': 'Filter by OS (e.g., windows 10, ubuntu)'},
                    {'name': 'platform', 'type': 'string', 'required': False, 'description': 'Filter by platform (windows, linux, etc.)'}
                ]
            },
            {
                'name': 'asset_search',
                'display_name': 'Asset Search',
                'description': 'Search for assets by hostname, IP, OS, or other criteria',
                'category': 'asset',
                'platform': 'cross-platform',
                'source': 'local',
                'parameters': [
                    {'name': 'query', 'type': 'string', 'required': False, 'description': 'Search query (hostname, IP, etc.)'},
                    {'name': 'os', 'type': 'string', 'required': False, 'description': 'Filter by OS'},
                    {'name': 'platform', 'type': 'string', 'required': False, 'description': 'Filter by platform'},
                    {'name': 'limit', 'type': 'integer', 'required': False, 'default': 50, 'description': 'Maximum results'}
                ]
            },
            {
                'name': 'dns_lookup',
                'display_name': 'DNS Lookup',
                'description': 'Perform DNS lookup for a domain',
                'category': 'network',
                'platform': 'cross-platform',
                'source': 'local',
                'parameters': [
                    {'name': 'domain', 'type': 'string', 'required': True, 'description': 'Domain to lookup'}
                ]
            },
            {
                'name': 'tcp_port_check',
                'display_name': 'TCP Port Check',
                'description': 'Check if a TCP port is open on a host',
                'category': 'network',
                'platform': 'cross-platform',
                'source': 'local',
                'parameters': [
                    {'name': 'host', 'type': 'string', 'required': True, 'description': 'Target host'},
                    {'name': 'port', 'type': 'integer', 'required': True, 'description': 'TCP port number'}
                ]
            },
            {
                'name': 'http_check',
                'display_name': 'HTTP Check',
                'description': 'Check HTTP/HTTPS endpoint availability',
                'category': 'network',
                'platform': 'cross-platform',
                'source': 'local',
                'parameters': [
                    {'name': 'url', 'type': 'string', 'required': True, 'description': 'URL to check'}
                ]
            },
            {
                'name': 'traceroute',
                'display_name': 'Traceroute',
                'description': 'Trace network route to a host',
                'category': 'network',
                'platform': 'cross-platform',
                'source': 'local',
                'parameters': [
                    {'name': 'host', 'type': 'string', 'required': True, 'description': 'Target host'}
                ]
            },
            {
                'name': 'shell_ping',
                'display_name': 'Ping',
                'description': 'Ping a host to check connectivity',
                'category': 'network',
                'platform': 'cross-platform',
                'source': 'local',
                'parameters': [
                    {'name': 'host', 'type': 'string', 'required': True, 'description': 'Target host'},
                    {'name': 'count', 'type': 'integer', 'required': False, 'default': 4, 'description': 'Number of pings'}
                ]
            },
            {
                'name': 'windows_list_directory',
                'display_name': 'Windows List Directory',
                'description': 'List directory contents on a Windows host via WinRM',
                'category': 'windows',
                'platform': 'windows',
                'source': 'pipeline',
                'parameters': [
                    {'name': 'host', 'type': 'string', 'required': True, 'description': 'Target Windows host'},
                    {'name': 'path', 'type': 'string', 'required': False, 'default': 'C:\\', 'description': 'Directory path'},
                    {'name': 'username', 'type': 'string', 'required': False, 'description': 'WinRM username (auto-resolved)'},
                    {'name': 'password', 'type': 'string', 'required': False, 'secret': True, 'description': 'WinRM password (auto-resolved)'},
                    {'name': 'domain', 'type': 'string', 'required': False, 'description': 'Windows domain (auto-resolved)'},
                    {'name': 'port', 'type': 'integer', 'required': False, 'default': 5985, 'description': 'WinRM port (auto-resolved)'},
                    {'name': 'use_ssl', 'type': 'boolean', 'required': False, 'default': False, 'description': 'Use SSL (auto-resolved)'}
                ]
            }
        ]
        
        for tool_def in builtin_definitions:
            builtins[tool_def['name']] = tool_def
            logger.debug(f"[ToolRegistry] Loaded built-in tool: {tool_def['name']}")
        
        return builtins
    
    def _load_yaml_tool(self, yaml_path: str) -> Optional[Dict[str, Any]]:
        """Load a single tool from YAML file"""
        try:
            with open(yaml_path, 'r') as f:
                tool_def = yaml.safe_load(f)
            
            # Validate required fields
            if not tool_def.get('name'):
                logger.error(f"[ToolRegistry] Tool missing 'name' field: {yaml_path}")
                return None
            
            # Add source if not specified (default to pipeline for YAML tools)
            if 'source' not in tool_def:
                tool_def['source'] = 'pipeline'
            
            # Ensure parameters is a list
            if 'parameters' not in tool_def:
                tool_def['parameters'] = []
            
            logger.debug(f"[ToolRegistry] Loaded YAML tool: {tool_def['name']} from {yaml_path}")
            return tool_def
            
        except Exception as e:
            logger.error(f"[ToolRegistry] Failed to load YAML tool {yaml_path}: {e}")
            tools_reload_errors_total.inc()
            return None
    
    def _scan_catalog_dirs(self) -> Dict[str, Dict[str, Any]]:
        """Scan catalog directories for YAML tools"""
        yaml_tools = {}
        
        for catalog_dir in self.catalog_dirs:
            logger.info(f"[ToolRegistry] Scanning catalog directory: {catalog_dir}")
            
            # Recursively find all .yaml files
            catalog_path = Path(catalog_dir)
            yaml_files = list(catalog_path.rglob('*.yaml')) + list(catalog_path.rglob('*.yml'))
            
            for yaml_file in yaml_files:
                tool_def = self._load_yaml_tool(str(yaml_file))
                if tool_def:
                    tool_name = tool_def['name']
                    
                    # Check for duplicates (later path wins)
                    if tool_name in yaml_tools:
                        logger.warning(
                            f"[ToolRegistry] Tool '{tool_name}' redefined in {yaml_file}, "
                            f"overriding previous definition"
                        )
                    
                    yaml_tools[tool_name] = tool_def
        
        return yaml_tools
    
    def reload(self) -> Dict[str, Any]:
        """
        Reload tool registry from catalog directories
        
        Returns:
            Dict with reload status and tool list
        """
        logger.info("[ToolRegistry] Reloading tool registry...")
        tools_reload_total.inc()
        
        try:
            # Start with built-in tools
            new_tools = self._load_builtin_tools()
            logger.info(f"[ToolRegistry] Loaded {len(new_tools)} built-in tools")
            
            # Load YAML tools (can override built-ins)
            yaml_tools = self._scan_catalog_dirs()
            logger.info(f"[ToolRegistry] Loaded {len(yaml_tools)} YAML tools")
            
            # Merge (YAML tools override built-ins)
            for tool_name, tool_def in yaml_tools.items():
                if tool_name in new_tools:
                    logger.warning(
                        f"[ToolRegistry] YAML tool '{tool_name}' overrides built-in definition"
                    )
                new_tools[tool_name] = tool_def
            
            # Validate required tools are present
            missing_required = []
            for required_tool in self.required_tools:
                if required_tool not in new_tools:
                    missing_required.append(required_tool)
                    logger.error(
                        f"[ToolRegistry] Required tool '{required_tool}' not found in registry!"
                    )
            
            # Update registry atomically
            self.tools = new_tools
            
            # Update metrics
            tools_loaded_total.inc(len(self.tools))
            tools_count_gauge.set(len(self.tools))
            
            # Log final tool list
            tool_names = sorted(self.tools.keys())
            logger.info(f"[ToolRegistry] Registry loaded with {len(self.tools)} tools: {tool_names}")
            
            return {
                'success': True,
                'count': len(self.tools),
                'tools': tool_names,
                'missing_required': missing_required,
                'catalog_dirs': self.catalog_dirs
            }
            
        except Exception as e:
            logger.error(f"[ToolRegistry] Reload failed: {e}")
            tools_reload_errors_total.inc()
            return {
                'success': False,
                'error': str(e),
                'count': len(self.tools),
                'tools': sorted(self.tools.keys())
            }
    
    def list_tools(self, platform: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all tools with optional filtering
        
        Args:
            platform: Filter by platform (windows, linux, cross-platform)
            category: Filter by category (network, system, asset, etc.)
        
        Returns:
            List of tool definitions
        """
        tools_list = []
        
        for tool_name, tool_def in self.tools.items():
            # Apply filters
            if platform and tool_def.get('platform') != platform:
                continue
            if category and tool_def.get('category') != category:
                continue
            
            tools_list.append(tool_def)
        
        return tools_list
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool by name
        
        Args:
            name: Tool name
        
        Returns:
            Tool definition or None if not found
        """
        return self.tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool exists in the registry"""
        return name in self.tools
    
    def get_tool_count(self) -> int:
        """Get total number of tools in registry"""
        return len(self.tools)


# Global registry instance (initialized by main_clean.py)
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    global _registry
    if _registry is None:
        raise RuntimeError("Tool registry not initialized. Call init_registry() first.")
    return _registry


def init_registry(catalog_dirs: Optional[str] = None) -> ToolRegistry:
    """
    Initialize the global tool registry
    
    Args:
        catalog_dirs: Colon-separated list of catalog directories
    
    Returns:
        Initialized ToolRegistry instance
    """
    global _registry
    _registry = ToolRegistry(catalog_dirs)
    return _registry
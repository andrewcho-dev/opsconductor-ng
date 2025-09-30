"""
Tool Registry for Stage B Selector
Manages available tools and their capabilities
"""

import json
from typing import Dict, List, Optional, Set
from pathlib import Path
from pipeline.schemas.selection_v1 import Tool, ToolCapability, PermissionLevel

class ToolRegistry:
    """Registry of available tools and their capabilities"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.tools: Dict[str, Tool] = {}
        self.capabilities_index: Dict[str, Set[str]] = {}  # capability -> tool names
        self.intent_mappings: Dict[str, Set[str]] = {}     # intent -> tool names
        
        if config_path:
            self.load_from_config(config_path)
        else:
            self._load_default_tools()
    
    def register_tool(self, tool: Tool) -> None:
        """Register a new tool in the registry"""
        self.tools[tool.name] = tool
        
        # Update capabilities index
        for capability in tool.capabilities:
            if capability.name not in self.capabilities_index:
                self.capabilities_index[capability.name] = set()
            self.capabilities_index[capability.name].add(tool.name)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_tools_by_capability(self, capability: str) -> List[Tool]:
        """Get all tools that have a specific capability"""
        tool_names = self.capabilities_index.get(capability, set())
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def get_tools_by_intent(self, intent_category: str, intent_action: str) -> List[Tool]:
        """Get tools suitable for a specific intent"""
        # Map intent to capabilities
        capability_mappings = {
            "automation": {
                "restart_service": ["service_control", "process_management"],
                "deploy_application": ["deployment", "file_management"],
                "scale_service": ["container_management", "service_control"],
                "backup_data": ["backup", "file_management"],
                "update_configuration": ["configuration_management", "file_management"]
            },
            "monitoring": {
                "check_status": ["service_status", "system_info"],
                "get_metrics": ["process_monitoring", "system_info"],
                "view_logs": ["log_access", "file_access"],
                "list_processes": ["process_monitoring", "system_info"],
                "check_resources": ["process_monitoring", "system_info"]
            },
            "troubleshooting": {
                "diagnose_issue": ["diagnostics", "log_analysis"],
                "analyze_logs": ["log_analysis", "file_access"],
                "test_connectivity": ["network_testing", "connectivity"],
                "check_dependencies": ["dependency_check", "system_info"],
                "validate_configuration": ["configuration_validation", "file_access"]
            },
            "configuration": {
                "update_config": ["configuration_management", "file_management"],
                "manage_users": ["user_management", "security"],
                "set_permissions": ["permission_management", "security"],
                "configure_network": ["network_configuration", "system_config"],
                "manage_services": ["service_management", "system_config"]
            },
            "information": {
                "get_help": ["documentation", "help_system"],
                "show_status": ["status_display", "information"],
                "list_resources": ["resource_listing", "information"],
                "explain_process": ["documentation", "help_system"],
                "show_configuration": ["configuration_display", "information"]
            }
        }
        
        # Get relevant capabilities for this intent
        capabilities = capability_mappings.get(intent_category, {}).get(intent_action, [])
        
        # Find tools with these capabilities
        relevant_tools = []
        for capability in capabilities:
            relevant_tools.extend(self.get_tools_by_capability(capability))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tools = []
        for tool in relevant_tools:
            if tool.name not in seen:
                seen.add(tool.name)
                unique_tools.append(tool)
        
        return unique_tools
    
    def get_tools_by_permission(self, max_permission: PermissionLevel) -> List[Tool]:
        """Get tools that require at most the specified permission level"""
        permission_order = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.ADMIN: 3
        }
        
        max_level = permission_order[max_permission]
        return [
            tool for tool in self.tools.values()
            if permission_order[tool.permissions] <= max_level
        ]
    
    def get_production_safe_tools(self) -> List[Tool]:
        """Get tools that are safe for production use"""
        return [tool for tool in self.tools.values() if tool.production_safe]
    
    def search_tools(self, query: str) -> List[Tool]:
        """Search tools by name or description"""
        query_lower = query.lower()
        results = []
        
        for tool in self.tools.values():
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                results.append(tool)
        
        return results
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool_count(self) -> int:
        """Get total number of registered tools"""
        return len(self.tools)
    
    def load_from_config(self, config_path: str) -> None:
        """Load tools from a configuration file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for tool_data in config.get('tools', []):
                # Convert capabilities
                capabilities = []
                for cap_data in tool_data.get('capabilities', []):
                    capability = ToolCapability(**cap_data)
                    capabilities.append(capability)
                
                # Create tool
                tool_data['capabilities'] = capabilities
                tool = Tool(**tool_data)
                self.register_tool(tool)
                
        except Exception as e:
            raise RuntimeError(f"Failed to load tool configuration: {e}")
    
    def _load_default_tools(self) -> None:
        """Load default set of tools"""
        
        # System Control Tools
        systemctl_tool = Tool(
            name="systemctl",
            description="System service control utility",
            capabilities=[
                ToolCapability(
                    name="service_control",
                    description="Start, stop, restart, and manage system services",
                    required_inputs=["service_name", "action"],
                    optional_inputs=["timeout"]
                ),
                ToolCapability(
                    name="service_status",
                    description="Check service status and health",
                    required_inputs=["service_name"],
                    optional_inputs=[]
                )
            ],
            required_inputs=["service_name"],
            permissions=PermissionLevel.ADMIN,
            production_safe=True,
            max_execution_time=60,
            dependencies=[]
        )
        self.register_tool(systemctl_tool)
        
        # Process Management
        ps_tool = Tool(
            name="ps",
            description="Process status and monitoring",
            capabilities=[
                ToolCapability(
                    name="process_monitoring",
                    description="List and monitor running processes",
                    required_inputs=[],
                    optional_inputs=["filter", "format"]
                ),
                ToolCapability(
                    name="system_info",
                    description="Get system process information",
                    required_inputs=[],
                    optional_inputs=["detailed"]
                )
            ],
            required_inputs=[],
            permissions=PermissionLevel.READ,
            production_safe=True,
            max_execution_time=10,
            dependencies=[]
        )
        self.register_tool(ps_tool)
        
        # Log Access
        journalctl_tool = Tool(
            name="journalctl",
            description="System journal and log access",
            capabilities=[
                ToolCapability(
                    name="log_access",
                    description="Access system and service logs",
                    required_inputs=[],
                    optional_inputs=["service", "since", "lines", "follow"]
                ),
                ToolCapability(
                    name="log_analysis",
                    description="Analyze log patterns and errors",
                    required_inputs=[],
                    optional_inputs=["service", "priority", "grep"]
                )
            ],
            required_inputs=[],
            permissions=PermissionLevel.READ,
            production_safe=True,
            max_execution_time=30,
            dependencies=[]
        )
        self.register_tool(journalctl_tool)
        
        # File Management
        file_manager_tool = Tool(
            name="file_manager",
            description="File and directory operations",
            capabilities=[
                ToolCapability(
                    name="file_management",
                    description="Create, modify, delete files and directories",
                    required_inputs=["path", "operation"],
                    optional_inputs=["content", "permissions", "backup"]
                ),
                ToolCapability(
                    name="file_access",
                    description="Read and access file contents",
                    required_inputs=["path"],
                    optional_inputs=["lines", "tail", "grep"]
                )
            ],
            required_inputs=["path"],
            permissions=PermissionLevel.WRITE,
            production_safe=False,  # Requires careful handling
            max_execution_time=45,
            dependencies=[]
        )
        self.register_tool(file_manager_tool)
        
        # Network Tools
        network_tool = Tool(
            name="network_tools",
            description="Network connectivity and testing",
            capabilities=[
                ToolCapability(
                    name="network_testing",
                    description="Test network connectivity and performance",
                    required_inputs=["target"],
                    optional_inputs=["protocol", "port", "timeout"]
                ),
                ToolCapability(
                    name="connectivity",
                    description="Check network connectivity status",
                    required_inputs=["target"],
                    optional_inputs=["port"]
                )
            ],
            required_inputs=["target"],
            permissions=PermissionLevel.READ,
            production_safe=True,
            max_execution_time=20,
            dependencies=[]
        )
        self.register_tool(network_tool)
        
        # Docker Management
        docker_tool = Tool(
            name="docker",
            description="Container management and operations",
            capabilities=[
                ToolCapability(
                    name="container_management",
                    description="Manage Docker containers",
                    required_inputs=["container", "action"],
                    optional_inputs=["image", "ports", "volumes"]
                ),
                ToolCapability(
                    name="image_management",
                    description="Manage Docker images",
                    required_inputs=["image", "action"],
                    optional_inputs=["tag", "registry"]
                )
            ],
            required_inputs=["action"],
            permissions=PermissionLevel.ADMIN,
            production_safe=True,
            max_execution_time=120,
            dependencies=["docker_daemon"]
        )
        self.register_tool(docker_tool)
        
        # Configuration Management
        config_tool = Tool(
            name="config_manager",
            description="Configuration file management",
            capabilities=[
                ToolCapability(
                    name="configuration_management",
                    description="Manage application and system configurations",
                    required_inputs=["config_file", "action"],
                    optional_inputs=["key", "value", "backup"]
                ),
                ToolCapability(
                    name="configuration_validation",
                    description="Validate configuration files",
                    required_inputs=["config_file"],
                    optional_inputs=["schema"]
                )
            ],
            required_inputs=["config_file"],
            permissions=PermissionLevel.WRITE,
            production_safe=False,
            max_execution_time=30,
            dependencies=[]
        )
        self.register_tool(config_tool)
        
        # Information Tools
        info_tool = Tool(
            name="info_display",
            description="Information display and help system",
            capabilities=[
                ToolCapability(
                    name="documentation",
                    description="Display documentation and help",
                    required_inputs=["topic"],
                    optional_inputs=["format", "detailed"]
                ),
                ToolCapability(
                    name="status_display",
                    description="Display system and service status",
                    required_inputs=[],
                    optional_inputs=["service", "detailed"]
                ),
                ToolCapability(
                    name="information",
                    description="General information retrieval",
                    required_inputs=["query"],
                    optional_inputs=["format"]
                )
            ],
            required_inputs=[],
            permissions=PermissionLevel.READ,
            production_safe=True,
            max_execution_time=15,
            dependencies=[]
        )
        self.register_tool(info_tool)
    
    def export_config(self, output_path: str) -> None:
        """Export current tool registry to a configuration file"""
        config = {
            "tools": []
        }
        
        for tool in self.tools.values():
            tool_data = tool.model_dump()
            config["tools"].append(tool_data)
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_registry_stats(self) -> Dict[str, any]:
        """Get statistics about the tool registry"""
        permission_counts = {}
        capability_counts = {}
        production_safe_count = 0
        
        for tool in self.tools.values():
            # Count permissions
            perm = tool.permissions.value
            permission_counts[perm] = permission_counts.get(perm, 0) + 1
            
            # Count production safe
            if tool.production_safe:
                production_safe_count += 1
            
            # Count capabilities
            for capability in tool.capabilities:
                cap_name = capability.name
                capability_counts[cap_name] = capability_counts.get(cap_name, 0) + 1
        
        return {
            "total_tools": len(self.tools),
            "permission_distribution": permission_counts,
            "capability_distribution": capability_counts,
            "production_safe_tools": production_safe_count,
            "production_safe_percentage": (production_safe_count / len(self.tools)) * 100 if self.tools else 0
        }
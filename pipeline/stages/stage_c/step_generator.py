"""
Step Generator for Stage C Planner

Generates individual execution steps based on selected tools and requirements.
Implements the core step creation logic with proper input mapping and validation.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...schemas.decision_v1 import DecisionV1
from ...schemas.selection_v1 import SelectionV1, SelectedTool
from ...schemas.plan_v1 import ExecutionStep


class StepGenerator:
    """
    Generates execution steps from selected tools and requirements.
    
    This class is responsible for:
    - Converting selected tools into executable steps
    - Mapping inputs and parameters correctly
    - Setting appropriate preconditions and success criteria
    - Estimating execution times
    - Generating unique step identifiers
    """
    
    def __init__(self):
        """Initialize the step generator"""
        # Remove step_counter to fix concurrency issues
        
        # Tool-specific step templates
        self.tool_templates = {
            "systemctl": self._generate_systemctl_step,
            "ps": self._generate_ps_step,
            "journalctl": self._generate_journalctl_step,
            "file_manager": self._generate_file_manager_step,
            "network_tools": self._generate_network_tools_step,
            "docker": self._generate_docker_step,
            "config_manager": self._generate_config_manager_step,
            "info_display": self._generate_info_display_step,
            "asset-service-query": self._generate_asset_query_step,
            "asset-credentials-read": self._generate_asset_credentials_step
        }
        
        # Default execution time estimates (seconds)
        self.default_durations = {
            "systemctl": 10,
            "ps": 5,
            "journalctl": 15,
            "file_manager": 20,
            "network_tools": 10,
            "docker": 30,
            "config_manager": 25,
            "info_display": 5,
            "asset-service-query": 8,
            "asset-credentials-read": 5
        }
    
    def generate_steps(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List[ExecutionStep]:
        """
        Generate execution steps from decision and selection data.
        
        Args:
            decision: The decision from Stage A
            selection: The selection from Stage B
            
        Returns:
            List of execution steps
        """
        steps = []
        
        # Sort selected tools by execution order
        sorted_tools = sorted(
            selection.selected_tools, 
            key=lambda t: t.execution_order
        )
        
        for selected_tool in sorted_tools:
            step = self._generate_step_for_tool(
                selected_tool, 
                decision, 
                selection
            )
            if step:
                steps.append(step)
        
        return steps
    
    def _generate_step_for_tool(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Optional[ExecutionStep]:
        """
        Generate a step for a specific selected tool.
        
        Args:
            selected_tool: The tool to generate a step for
            decision: The decision context
            selection: The selection context
            
        Returns:
            Generated execution step or None if generation fails
        """
        tool_name = selected_tool.tool_name
        
        if tool_name in self.tool_templates:
            return self.tool_templates[tool_name](
                selected_tool, decision, selection
            )
        else:
            # Generic step generation for unknown tools
            return self._generate_generic_step(
                selected_tool, decision, selection
            )
    
    def _generate_step_id(self, tool_name: str, suffix: str = "") -> str:
        """Generate a unique step ID using UUID to prevent race conditions"""
        # Use UUID4 for thread-safe unique ID generation
        unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars for readability
        base_id = f"step_{unique_id}_{tool_name}"
        if suffix:
            base_id += f"_{suffix}"
        return base_id
    
    def _generate_systemctl_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for systemctl tool"""
        
        # Determine action based on intent
        action = "status"  # default
        if decision.intent.action == "restart_nginx" or decision.intent.category == "restart_service":
            action = "restart"
        elif decision.intent.category == "monitor_system":
            action = "status"
        elif "start" in decision.original_request.lower():
            action = "start"
        elif "stop" in decision.original_request.lower():
            action = "stop"
        
        # Extract service name from entities
        service_name = None
        for entity in decision.entities:
            if entity.type == "service_name":
                service_name = entity.value
                break
        
        if not service_name:
            service_name = "nginx"  # default fallback
        
        inputs = {
            "action": action,
            "service": service_name,
            "check_status": True
        }
        
        preconditions = [
            "systemctl_command_available",
            f"service_{service_name}_exists",
            "sufficient_privileges"
        ]
        
        success_criteria = [
            f"systemctl_{action}_completed_successfully",
            "no_error_messages_in_output"
        ]
        
        if action in ["restart", "start", "stop"]:
            success_criteria.append(f"service_{service_name}_in_expected_state")
        
        failure_handling = f"Log systemctl error, check service configuration, and report status to user"
        
        return ExecutionStep(
            id=self._generate_step_id("systemctl", action),
            description=f"Execute systemctl {action} on {service_name} service",
            tool="systemctl",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["systemctl"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_ps_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for ps tool"""
        
        # Determine format based on intent
        format_type = "detailed"
        if decision.intent.category == "monitor_system":
            format_type = "detailed"
        elif decision.intent.category == "troubleshoot_issue":
            format_type = "full"
        
        inputs = {
            "format": format_type,
            "filter": "all_processes",
            "sort_by": "cpu_usage"
        }
        
        preconditions = [
            "ps_command_available",
            "system_accessible"
        ]
        
        success_criteria = [
            "process_list_retrieved",
            "no_errors_occurred",
            "output_contains_process_information"
        ]
        
        failure_handling = "Log error and attempt alternative process listing method"
        
        return ExecutionStep(
            id=self._generate_step_id("ps", "list"),
            description="List system processes with detailed information",
            tool="ps",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["ps"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_journalctl_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for journalctl tool"""
        
        # Extract service name if available
        service_name = None
        for entity in decision.entities:
            if entity.type == "service_name":
                service_name = entity.value
                break
        
        inputs = {
            "lines": 100,
            "follow": False,
            "priority": "info"
        }
        
        if service_name:
            inputs["unit"] = service_name
        
        # Add time range if troubleshooting
        if decision.intent.category == "troubleshoot_issue":
            inputs["since"] = "1 hour ago"
            inputs["priority"] = "warning"
        
        preconditions = [
            "journalctl_command_available",
            "systemd_available",
            "sufficient_privileges"
        ]
        
        success_criteria = [
            "log_entries_retrieved",
            "no_permission_errors",
            "output_contains_log_data"
        ]
        
        failure_handling = "Check permissions and try alternative log sources"
        
        description = "Retrieve system logs"
        if service_name:
            description += f" for {service_name} service"
        
        return ExecutionStep(
            id=self._generate_step_id("journalctl", "logs"),
            description=description,
            tool="journalctl",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["journalctl"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_file_manager_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for file_manager tool"""
        
        # Determine operation based on intent and entities
        operation = "read"  # default
        file_path = "/etc/nginx/nginx.conf"  # default
        
        for entity in decision.entities:
            if entity.type == "file_path":
                file_path = entity.value
            elif entity.type == "operation" and entity.value in ["read", "write", "backup", "restore"]:
                operation = entity.value
        
        # Adjust operation based on intent
        if decision.intent.category == "modify_config":
            operation = "backup"  # Always backup before modify
        elif decision.intent.category == "troubleshoot_issue":
            operation = "read"
        
        inputs = {
            "operation": operation,
            "path": file_path
        }
        
        if operation == "backup":
            inputs["backup_path"] = f"{file_path}.backup.{int(datetime.now().timestamp())}"
        
        preconditions = [
            f"file_path_exists:{file_path}",
            "sufficient_file_permissions",
            "disk_space_available"
        ]
        
        success_criteria = [
            f"file_operation_{operation}_completed",
            "no_file_system_errors"
        ]
        
        if operation == "backup":
            success_criteria.append("backup_file_created_successfully")
        elif operation == "read":
            success_criteria.append("file_content_retrieved")
        
        failure_handling = f"Check file permissions and path validity for {file_path}"
        
        return ExecutionStep(
            id=self._generate_step_id("file_manager", operation),
            description=f"Perform {operation} operation on {file_path}",
            tool="file_manager",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["file_manager"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_network_tools_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for network_tools tool"""
        
        # Determine tool and target based on entities
        tool_type = "ping"  # default
        target = "localhost"  # default
        
        for entity in decision.entities:
            if entity.type == "hostname":
                target = entity.value
            elif entity.type == "ip_address":
                target = entity.value
            elif entity.type == "port":
                tool_type = "netstat"
        
        # Adjust based on intent
        if decision.intent.category == "troubleshoot_issue":
            tool_type = "netstat"
        elif "connectivity" in decision.original_request.lower():
            tool_type = "ping"
        
        inputs = {
            "tool": tool_type,
            "target": target
        }
        
        if tool_type == "ping":
            inputs["count"] = 4
        elif tool_type == "netstat":
            inputs["show_listening"] = True
            inputs["show_processes"] = True
        
        preconditions = [
            f"{tool_type}_command_available",
            "network_interface_available"
        ]
        
        if tool_type == "ping":
            preconditions.append("target_reachable_or_testable")
        
        success_criteria = [
            f"{tool_type}_command_executed_successfully",
            "network_information_retrieved"
        ]
        
        if tool_type == "ping":
            success_criteria.append("ping_responses_received")
        
        failure_handling = f"Check network connectivity and {tool_type} command availability"
        
        return ExecutionStep(
            id=self._generate_step_id("network_tools", tool_type),
            description=f"Execute {tool_type} network diagnostic on {target}",
            tool="network_tools",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["network_tools"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_docker_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for docker tool"""
        
        # Determine docker operation
        operation = "ps"  # default
        container_name = None
        
        for entity in decision.entities:
            if entity.type == "container_name":
                container_name = entity.value
            elif entity.type == "service_name":
                container_name = entity.value  # services often map to containers
        
        # Adjust operation based on intent
        if decision.intent.category == "restart_service" and container_name:
            operation = "restart"
        elif decision.intent.category == "monitor_system":
            operation = "ps"
        elif "logs" in decision.original_request.lower():
            operation = "logs"
        
        inputs = {
            "operation": operation
        }
        
        if container_name and operation != "ps":
            inputs["container"] = container_name
        
        if operation == "logs":
            inputs["lines"] = 100
            inputs["follow"] = False
        
        preconditions = [
            "docker_command_available",
            "docker_daemon_running",
            "sufficient_docker_permissions"
        ]
        
        if container_name and operation != "ps":
            preconditions.append(f"container_{container_name}_exists")
        
        success_criteria = [
            f"docker_{operation}_completed_successfully",
            "no_docker_errors"
        ]
        
        if operation == "ps":
            success_criteria.append("container_list_retrieved")
        elif operation == "logs":
            success_criteria.append("container_logs_retrieved")
        elif operation == "restart":
            success_criteria.append("container_restarted_successfully")
        
        failure_handling = "Check Docker daemon status and container existence"
        
        description = f"Execute docker {operation}"
        if container_name and operation != "ps":
            description += f" on {container_name} container"
        
        return ExecutionStep(
            id=self._generate_step_id("docker", operation),
            description=description,
            tool="docker",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["docker"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_config_manager_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for config_manager tool"""
        
        # Determine operation and config file
        operation = "read"  # default
        config_file = "/etc/nginx/nginx.conf"  # default
        
        for entity in decision.entities:
            if entity.type == "file_path":
                config_file = entity.value
            elif entity.type == "config_file":
                config_file = entity.value
        
        # Adjust operation based on intent
        if decision.intent.category == "modify_config":
            operation = "validate"  # Always validate before modify
        elif decision.intent.category == "troubleshoot_issue":
            operation = "read"
        
        inputs = {
            "operation": operation,
            "config_file": config_file
        }
        
        if operation == "validate":
            inputs["syntax_check"] = True
            inputs["backup_before_change"] = True
        
        preconditions = [
            f"config_file_exists:{config_file}",
            "config_manager_available",
            "sufficient_file_permissions"
        ]
        
        success_criteria = [
            f"config_{operation}_completed_successfully",
            "no_syntax_errors"
        ]
        
        if operation == "validate":
            success_criteria.append("configuration_is_valid")
        elif operation == "read":
            success_criteria.append("configuration_content_retrieved")
        
        failure_handling = f"Check configuration file syntax and permissions for {config_file}"
        
        return ExecutionStep(
            id=self._generate_step_id("config_manager", operation),
            description=f"Perform {operation} operation on configuration file {config_file}",
            tool="config_manager",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["config_manager"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_info_display_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for info_display tool"""
        
        # Determine what information to display
        info_type = "system_status"  # default
        
        if decision.intent.category == "monitor_system":
            info_type = "system_metrics"
        elif decision.intent.category == "troubleshoot_issue":
            info_type = "diagnostic_info"
        elif "status" in decision.original_request.lower():
            info_type = "system_status"
        
        inputs = {
            "info_type": info_type,
            "format": "detailed",
            "include_metrics": True
        }
        
        preconditions = [
            "system_accessible",
            "info_display_available"
        ]
        
        success_criteria = [
            "information_displayed_successfully",
            "no_display_errors",
            "output_formatted_correctly"
        ]
        
        failure_handling = "Use alternative information gathering methods"
        
        return ExecutionStep(
            id=self._generate_step_id("info_display", info_type),
            description=f"Display {info_type.replace('_', ' ')} information",
            tool="info_display",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["info_display"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_generic_step(
        self, 
        selected_tool: SelectedTool, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate a generic step for unknown tools"""
        
        tool_name = selected_tool.tool_name
        
        inputs = {
            "operation": "default",
            "parameters": {}
        }
        
        # Add any inputs needed from the selected tool
        for input_name in selected_tool.inputs_needed:
            inputs["parameters"][input_name] = f"<{input_name}_value>"
        
        preconditions = [
            f"{tool_name}_available",
            "sufficient_permissions"
        ]
        
        success_criteria = [
            f"{tool_name}_executed_successfully",
            "no_errors_occurred"
        ]
        
        failure_handling = f"Check {tool_name} availability and permissions"
        
        return ExecutionStep(
            id=self._generate_step_id(tool_name, "generic"),
            description=f"Execute {tool_name} tool with default parameters",
            tool=tool_name,
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=30,  # conservative default
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_asset_query_step(
        self,
        selected_tool: SelectedTool,
        decision: DecisionV1,
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for asset-service-query tool"""
        
        # Extract query parameters from entities and request
        query_params = self._extract_asset_query_params(decision, selected_tool)
        
        # Determine query type
        query_type = query_params.get("query_type", "search")
        
        # Build inputs
        inputs = {
            "query_type": query_type,
            "filters": query_params.get("filters", {}),
            "fields": query_params.get("fields", []),
            "limit": query_params.get("limit", 10)
        }
        
        # Add specific parameters based on query type
        if query_type == "get_by_id" and "asset_id" in query_params:
            inputs["asset_id"] = query_params["asset_id"]
        elif query_type == "get_by_hostname" and "hostname" in query_params:
            inputs["hostname"] = query_params["hostname"]
        elif query_type == "search" and "search_term" in query_params:
            inputs["search_term"] = query_params["search_term"]
        
        preconditions = [
            "asset_service_available",
            "network_connectivity",
            "valid_query_parameters"
        ]
        
        success_criteria = [
            "asset_data_retrieved",
            "no_api_errors",
            "results_contain_expected_fields"
        ]
        
        failure_handling = "Log error, check asset-service availability, and report to user"
        
        # Build description
        description = "Query asset-service for infrastructure metadata"
        if query_type == "get_by_id":
            description = f"Get asset by ID: {inputs.get('asset_id', 'unknown')}"
        elif query_type == "get_by_hostname":
            description = f"Get asset by hostname: {inputs.get('hostname', 'unknown')}"
        elif query_type == "search":
            description = f"Search assets: {inputs.get('search_term', 'all')}"
        
        return ExecutionStep(
            id=self._generate_step_id("asset_query", query_type),
            description=description,
            tool="asset-service-query",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["asset-service-query"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _generate_asset_credentials_step(
        self,
        selected_tool: SelectedTool,
        decision: DecisionV1,
        selection: SelectionV1
    ) -> ExecutionStep:
        """Generate step for asset-credentials-read tool (GATED ACCESS)"""
        
        # Extract asset ID and justification
        asset_id = None
        justification = "User requested credential access"
        credential_type = "ssh_key"  # default
        
        # Extract from entities
        for entity in decision.entities:
            if entity.type == "asset_id":
                asset_id = entity.value
            elif entity.type == "hostname":
                # Will need to resolve hostname to asset_id first
                asset_id = f"<resolve_hostname:{entity.value}>"
        
        # Extract from inputs_needed
        for input_name in selected_tool.inputs_needed:
            if "justification" in input_name.lower():
                justification = decision.original_request
            elif "credential_type" in input_name.lower():
                credential_type = "ssh_key"  # default, could be extracted from request
        
        inputs = {
            "asset_id": asset_id or "<asset_id_required>",
            "credential_type": credential_type,
            "justification": justification,
            "requires_approval": True,
            "approval_timeout": 300  # 5 minutes
        }
        
        preconditions = [
            "asset_service_available",
            "user_has_credential_read_permission",
            "valid_justification_provided",
            "asset_id_exists",
            "approval_granted"
        ]
        
        success_criteria = [
            "credential_handle_retrieved",
            "no_permission_errors",
            "audit_log_created"
        ]
        
        failure_handling = "Log access attempt, notify security team if unauthorized, report to user"
        
        description = f"Request credentials for asset {asset_id} (REQUIRES APPROVAL)"
        
        return ExecutionStep(
            id=self._generate_step_id("asset_credentials", "read"),
            description=description,
            tool="asset-credentials-read",
            inputs=inputs,
            preconditions=preconditions,
            success_criteria=success_criteria,
            failure_handling=failure_handling,
            estimated_duration=self.default_durations["asset-credentials-read"],
            depends_on=self._extract_dependencies(selected_tool)
        )
    
    def _extract_asset_query_params(
        self,
        decision: DecisionV1,
        selected_tool: SelectedTool
    ) -> Dict[str, Any]:
        """
        Extract asset query parameters from decision entities and request.
        
        Returns a dictionary with query parameters:
        - query_type: "get_by_id", "get_by_hostname", "search", "list_all", "filter"
        - filters: dict of filter criteria
        - fields: list of fields to return
        - limit: max results
        - asset_id: specific asset ID (if applicable)
        - hostname: specific hostname (if applicable)
        - search_term: search query (if applicable)
        """
        params = {
            "query_type": "search",  # default
            "filters": {},
            "fields": [],
            "limit": 10
        }
        
        # Extract from entities
        for entity in decision.entities:
            if entity.type == "asset_id":
                params["query_type"] = "get_by_id"
                params["asset_id"] = entity.value
            elif entity.type == "hostname":
                params["query_type"] = "get_by_hostname"
                params["hostname"] = entity.value
            elif entity.type == "ip_address":
                params["query_type"] = "search"
                params["search_term"] = entity.value
            elif entity.type == "environment":
                params["filters"]["environment"] = entity.value
            elif entity.type == "service_name":
                params["filters"]["service_type"] = entity.value
        
        # If no specific query type determined, use search with original request
        if params["query_type"] == "search" and "search_term" not in params:
            # Extract key terms from request
            request_lower = decision.original_request.lower()
            
            # Look for specific patterns
            if "ip" in request_lower or "address" in request_lower:
                params["fields"].append("ip_address")
            if "hostname" in request_lower or "server" in request_lower:
                params["fields"].append("hostname")
            if "service" in request_lower:
                params["fields"].append("services")
            if "location" in request_lower:
                params["fields"].append("location")
            
            # Use first hostname/service entity as search term
            for entity in decision.entities:
                if entity.type in ["hostname", "service_name", "application"]:
                    params["search_term"] = entity.value
                    break
            
            # If still no search term, use a generic search
            if "search_term" not in params:
                params["query_type"] = "list_all"
                params["limit"] = 20
        
        return params
    
    def _extract_dependencies(self, selected_tool: SelectedTool) -> List[str]:
        """Extract step dependencies from selected tool"""
        # Convert tool dependencies to step dependencies
        # This is a simplified mapping - in practice, you'd need more sophisticated logic
        dependencies = []
        
        for dep in selected_tool.depends_on:
            # Convert tool names to step IDs (this is simplified)
            # In practice, you'd maintain a mapping of tools to their step IDs
            dependencies.append(f"step_*_{dep}_*")
        
        return dependencies
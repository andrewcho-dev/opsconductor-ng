"""
Capability Matcher for Stage B Selector
Matches decision requirements to available tool capabilities
"""

from typing import List, Dict, Set, Tuple, Optional
from pipeline.schemas.decision_v1 import DecisionV1, EntityV1, IntentV1
from pipeline.schemas.selection_v1 import Tool, SelectedTool, PermissionLevel, RiskLevel
from .tool_registry import ToolRegistry

class CapabilityMatch:
    """Represents a match between decision requirements and tool capabilities"""
    
    def __init__(self, tool: Tool, confidence: float, justification: str, 
                 missing_inputs: List[str] = None, risk_factors: List[str] = None):
        self.tool = tool
        self.confidence = confidence
        self.justification = justification
        self.missing_inputs = missing_inputs or []
        self.risk_factors = risk_factors or []

class CapabilityMatcher:
    """Matches decision requirements to tool capabilities"""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        
        # Entity type to input mapping
        self.entity_input_mapping = {
            "service": ["service_name", "service"],
            "hostname": ["hostname", "host", "target"],
            "command": ["command", "cmd"],
            "file_path": ["path", "file", "config_file"],
            "port": ["port"],
            "environment": ["environment", "env"],
            "application": ["application", "app"],
            "database": ["database", "db"]
        }
    
    def find_matching_tools(self, decision: DecisionV1, 
                          max_tools: int = 5) -> List[CapabilityMatch]:
        """
        Find tools that match the decision requirements
        
        This method provides ALL available tools to the LLM for intelligent selection.
        We do NOT pre-filter based on hardcoded intent mappings - the LLM makes the decision.
        
        Args:
            decision: Decision from Stage A
            max_tools: Maximum number of tools to return
            
        Returns:
            List of capability matches sorted by confidence
        """
        matches = []
        
        # Get ALL tools - let the LLM decide which ones are appropriate
        # This is the correct LLM-first approach per the system charter
        candidate_tools = self.tool_registry.get_all_tools()
        
        # Evaluate each candidate tool
        for tool in candidate_tools:
            match = self._evaluate_tool_match(decision, tool)
            if match.confidence > 0.1:  # Only include reasonable matches
                matches.append(match)
        
        # Sort by confidence (descending) and return top matches
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:max_tools]
    
    def _evaluate_tool_match(self, decision: DecisionV1, tool: Tool) -> CapabilityMatch:
        """Evaluate how well a tool matches the decision requirements"""
        
        confidence_factors = []
        justification_parts = []
        missing_inputs = []
        risk_factors = []
        
        # 1. Intent matching (40% of confidence)
        intent_score = self._calculate_intent_match(decision.intent, tool)
        confidence_factors.append(("intent", intent_score, 0.4))
        
        if intent_score > 0.7:
            justification_parts.append(f"Strong intent match for {decision.intent.category}/{decision.intent.action}")
        elif intent_score > 0.4:
            justification_parts.append(f"Partial intent match for {decision.intent.category}")
        
        # 2. Entity compatibility (30% of confidence)
        entity_score, entity_inputs = self._calculate_entity_compatibility(decision.entities, tool)
        confidence_factors.append(("entities", entity_score, 0.3))
        
        if entity_score > 0.8:
            justification_parts.append("All required entities are compatible")
        elif entity_score > 0.5:
            justification_parts.append("Most entities are compatible")
        
        # 3. Input availability (20% of confidence)
        input_score, missing = self._calculate_input_availability(decision, tool, entity_inputs)
        confidence_factors.append(("inputs", input_score, 0.2))
        missing_inputs.extend(missing)
        
        if input_score > 0.8:
            justification_parts.append("All required inputs are available")
        elif missing:
            justification_parts.append(f"Missing inputs: {', '.join(missing[:3])}")
        
        # 4. Risk and permission compatibility (10% of confidence)
        risk_score, risks = self._calculate_risk_compatibility(decision, tool)
        confidence_factors.append(("risk", risk_score, 0.1))
        risk_factors.extend(risks)
        
        if risk_score > 0.8:
            justification_parts.append("Low risk and appropriate permissions")
        elif risks:
            justification_parts.append(f"Risk factors: {', '.join(risks[:2])}")
        
        # Calculate weighted confidence
        total_confidence = sum(score * weight for _, score, weight in confidence_factors)
        
        # Build justification
        justification = "; ".join(justification_parts) if justification_parts else "Basic compatibility"
        
        return CapabilityMatch(
            tool=tool,
            confidence=total_confidence,
            justification=justification,
            missing_inputs=missing_inputs,
            risk_factors=risk_factors
        )
    
    def _calculate_intent_match(self, intent: IntentV1, tool: Tool) -> float:
        """Calculate how well the tool matches the intent"""
        
        # Direct capability name matching
        intent_key = f"{intent.category}_{intent.action}"
        
        # Check if tool has capabilities that match the intent
        capability_matches = 0
        total_capabilities = len(tool.capabilities)
        
        if total_capabilities == 0:
            return 0.0
        
        # Intent to capability mapping
        intent_capability_map = {
            "automation_restart_service": ["service_control", "process_management"],
            "automation_deploy_application": ["deployment", "file_management", "container_management"],
            "automation_scale_service": ["container_management", "service_control"],
            "automation_backup_data": ["backup", "file_management"],
            "automation_update_configuration": ["configuration_management", "file_management"],
            
            "monitoring_check_status": ["status_check", "health_monitoring", "service_status"],
            "monitoring_get_metrics": ["metrics_collection", "monitoring"],
            "monitoring_view_logs": ["log_access", "file_access"],
            "monitoring_list_processes": ["process_monitoring", "system_info"],
            "monitoring_check_resources": ["resource_monitoring", "system_info"],
            
            "troubleshooting_diagnose_issue": ["diagnostics", "log_analysis"],
            "troubleshooting_analyze_logs": ["log_analysis", "file_access", "log_access"],
            "troubleshooting_test_connectivity": ["network_testing", "connectivity"],
            "troubleshooting_check_dependencies": ["dependency_check", "system_info"],
            "troubleshooting_validate_configuration": ["configuration_validation", "file_access"],
            
            "configuration_update_config": ["configuration_management", "file_management"],
            "configuration_manage_users": ["user_management", "security"],
            "configuration_set_permissions": ["permission_management", "security"],
            "configuration_configure_network": ["network_configuration", "system_config"],
            "configuration_manage_services": ["service_management", "system_config"],
            
            "information_get_help": ["documentation", "help_system"],
            "information_show_status": ["status_display", "information", "service_status"],
            "information_list_resources": ["resource_listing", "information"],
            "information_explain_process": ["documentation", "help_system"],
            "information_show_configuration": ["configuration_display", "information"],
            "information_asset_inventory": ["asset_query", "infrastructure_info", "resource_listing"],
            
            # Asset management category - CRITICAL for asset queries
            "asset_management_list_assets": ["asset_query", "infrastructure_info", "resource_listing"],
            "asset_management_get_asset": ["asset_query", "infrastructure_info"],
            "asset_management_search_assets": ["asset_query", "infrastructure_info", "resource_listing"],
            "asset_management_count_assets": ["asset_query", "infrastructure_info"],
            "asset_management_get_credentials": ["credential_access", "secret_retrieval"],
            "asset_management_list_credentials": ["credential_access", "secret_retrieval"]
        }
        
        expected_capabilities = intent_capability_map.get(intent_key, [])
        
        # Check for exact matches
        tool_capability_names = {cap.name for cap in tool.capabilities}
        exact_matches = len(set(expected_capabilities) & tool_capability_names)
        
        if exact_matches > 0:
            capability_matches = exact_matches
        else:
            # Check for partial matches in capability names and descriptions
            for tool_cap in tool.capabilities:
                for expected_cap in expected_capabilities:
                    if (expected_cap in tool_cap.name.lower() or 
                        expected_cap in tool_cap.description.lower()):
                        capability_matches += 0.5
        
        # Calculate score based on matches
        if capability_matches >= len(expected_capabilities):
            return 1.0
        elif capability_matches > 0:
            return min(capability_matches / len(expected_capabilities), 0.9)
        else:
            # Fallback: check if tool name or description relates to intent
            intent_terms = [intent.category, intent.action.replace("_", " ")]
            for term in intent_terms:
                if (term in tool.name.lower() or 
                    term in tool.description.lower()):
                    return 0.3
            return 0.1
    
    def _calculate_entity_compatibility(self, entities: List[EntityV1], 
                                      tool: Tool) -> Tuple[float, Dict[str, str]]:
        """Calculate entity compatibility and map entities to inputs"""
        
        if not entities:
            return 1.0, {}  # No entities to match
        
        entity_input_map = {}
        compatible_entities = 0
        
        for entity in entities:
            # Find potential input names for this entity type
            potential_inputs = self.entity_input_mapping.get(entity.type, [])
            
            # Check if tool accepts any of these inputs
            tool_inputs = set(tool.required_inputs)
            for cap in tool.capabilities:
                tool_inputs.update(cap.required_inputs)
                tool_inputs.update(cap.optional_inputs)
            
            # Find matching input
            matched_input = None
            for potential_input in potential_inputs:
                if potential_input in tool_inputs:
                    matched_input = potential_input
                    break
            
            if matched_input:
                entity_input_map[entity.value] = matched_input
                compatible_entities += 1
            else:
                # Check for partial matches
                for tool_input in tool_inputs:
                    if any(term in tool_input.lower() for term in potential_inputs):
                        entity_input_map[entity.value] = tool_input
                        compatible_entities += 0.5
                        break
        
        compatibility_score = compatible_entities / len(entities) if entities else 1.0
        return min(compatibility_score, 1.0), entity_input_map
    
    def _calculate_input_availability(self, decision: DecisionV1, tool: Tool, 
                                    entity_inputs: Dict[str, str]) -> Tuple[float, List[str]]:
        """Calculate input availability and identify missing inputs"""
        
        # Collect all required inputs from tool and capabilities
        required_inputs = set(tool.required_inputs)
        for capability in tool.capabilities:
            required_inputs.update(capability.required_inputs)
        
        # Available inputs from decision
        available_inputs = set(entity_inputs.values())
        
        # Add common inputs that can be derived from decision context
        available_inputs.update([
            "user_request",  # original_request
            "timestamp",     # decision timestamp
            "decision_id"    # decision identifier
        ])
        
        # Check for environment-specific inputs
        if decision.context.get("environment"):
            available_inputs.add("environment")
        
        # Calculate missing inputs
        missing_inputs = list(required_inputs - available_inputs)
        
        if not required_inputs:
            return 1.0, []
        
        availability_score = (len(required_inputs) - len(missing_inputs)) / len(required_inputs)
        return max(availability_score, 0.0), missing_inputs
    
    def _calculate_risk_compatibility(self, decision: DecisionV1, 
                                    tool: Tool) -> Tuple[float, List[str]]:
        """Calculate risk and permission compatibility"""
        
        risk_factors = []
        risk_score = 1.0
        
        # Check permission requirements
        if tool.permissions == PermissionLevel.ADMIN:
            if decision.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                risk_factors.append("requires_admin_permissions")
                risk_score -= 0.3
        
        # Check production safety
        if not tool.production_safe:
            # Assume production if not explicitly stated
            is_production = decision.context.get("environment", "production") == "production"
            if is_production:
                risk_factors.append("not_production_safe")
                risk_score -= 0.4
        
        # Check execution time vs risk level
        if tool.max_execution_time > 60:
            if decision.risk_level == RiskLevel.HIGH:
                risk_factors.append("long_execution_time")
                risk_score -= 0.2
        
        # Check if tool has dependencies
        if tool.dependencies:
            risk_factors.append("has_dependencies")
            risk_score -= 0.1
        
        return max(risk_score, 0.0), risk_factors
    
    def select_optimal_tools(self, matches: List[CapabilityMatch], 
                           decision: DecisionV1) -> List[SelectedTool]:
        """Select optimal tools from capability matches"""
        
        if not matches:
            return []
        
        selected_tools = []
        used_capabilities = set()
        
        # Sort matches by confidence
        sorted_matches = sorted(matches, key=lambda x: x.confidence, reverse=True)
        
        for i, match in enumerate(sorted_matches):
            # Check if this tool provides new capabilities
            tool_capabilities = {cap.name for cap in match.tool.capabilities}
            
            if not used_capabilities or not tool_capabilities.issubset(used_capabilities):
                # This tool provides new capabilities
                selected_tool = SelectedTool(
                    tool_name=match.tool.name,
                    justification=match.justification,
                    inputs_needed=match.missing_inputs,
                    execution_order=len(selected_tools) + 1,
                    depends_on=match.tool.dependencies
                )
                
                selected_tools.append(selected_tool)
                used_capabilities.update(tool_capabilities)
                
                # Limit number of tools for complex operations
                if len(selected_tools) >= 3:
                    break
        
        return selected_tools
    
    def validate_tool_selection(self, selected_tools: List[SelectedTool], 
                              decision: DecisionV1) -> Tuple[bool, List[str]]:
        """Validate that selected tools can fulfill the decision requirements"""
        
        validation_errors = []
        
        if not selected_tools:
            validation_errors.append("No tools selected")
            return False, validation_errors
        
        # Check for circular dependencies
        tool_names = {tool.tool_name for tool in selected_tools}
        for tool in selected_tools:
            for dependency in tool.depends_on:
                if dependency not in tool_names:
                    validation_errors.append(f"Missing dependency: {dependency} for {tool.tool_name}")
        
        # Check execution order consistency
        execution_orders = [tool.execution_order for tool in selected_tools]
        if len(set(execution_orders)) != len(execution_orders):
            validation_errors.append("Duplicate execution orders detected")
        
        # Validate against decision requirements
        if decision.intent.category == "automation" and decision.risk_level == RiskLevel.HIGH:
            admin_tools = [
                tool for tool in selected_tools 
                if self.tool_registry.get_tool(tool.tool_name) and 
                self.tool_registry.get_tool(tool.tool_name).permissions == PermissionLevel.ADMIN
            ]
            if not admin_tools:
                validation_errors.append("High-risk automation requires admin-level tools")
        
        return len(validation_errors) == 0, validation_errors
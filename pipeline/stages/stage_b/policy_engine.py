"""
Policy Engine for Stage B Selector
Determines execution policies and approval requirements
"""

from typing import List, Dict, Any, Tuple
from pipeline.schemas.decision_v1 import DecisionV1, RiskLevel, ConfidenceLevel
from pipeline.schemas.selection_v1 import ExecutionPolicy, SelectedTool, Tool, PermissionLevel
from .tool_registry import ToolRegistry

class PolicyEngine:
    """Determines execution policies based on decisions and selected tools"""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        
        # Policy configuration
        self.config = {
            "approval_thresholds": {
                "risk_level": [RiskLevel.HIGH, RiskLevel.CRITICAL],
                "confidence_level": [ConfidenceLevel.LOW],
                "permission_level": [PermissionLevel.ADMIN],
                "production_environment": True,
                "non_production_safe": True
            },
            "execution_time_limits": {
                RiskLevel.LOW: 30,
                RiskLevel.MEDIUM: 60,
                RiskLevel.HIGH: 120,
                RiskLevel.CRITICAL: 300
            },
            "parallel_execution_rules": {
                "max_parallel_tools": 3,
                "allow_admin_parallel": False,
                "require_dependencies_sequential": True
            },
            "rollback_requirements": {
                "risk_levels": [RiskLevel.HIGH, RiskLevel.CRITICAL],
                "permission_levels": [PermissionLevel.ADMIN],
                "production_environment": True,
                "data_modification": True
            }
        }
    
    def determine_execution_policy(self, decision: DecisionV1, 
                                 selected_tools: List[SelectedTool]) -> ExecutionPolicy:
        """
        Determine execution policy based on decision and selected tools
        
        Args:
            decision: Decision from Stage A
            selected_tools: Tools selected for execution
            
        Returns:
            ExecutionPolicy with all policy decisions
        """
        
        # Get tool objects for analysis
        tools = []
        for selected_tool in selected_tools:
            tool = self.tool_registry.get_tool(selected_tool.tool_name)
            if tool:
                tools.append(tool)
        
        # Determine each policy aspect
        requires_approval = self._determine_approval_requirement(decision, tools)
        production_environment = self._detect_production_environment(decision)
        risk_level = self._calculate_overall_risk(decision, tools)
        max_execution_time = self._calculate_max_execution_time(decision, tools, risk_level)
        parallel_execution = self._determine_parallel_execution(selected_tools, tools)
        rollback_required = self._determine_rollback_requirement(decision, tools, production_environment)
        
        return ExecutionPolicy(
            requires_approval=requires_approval,
            production_environment=production_environment,
            risk_level=risk_level,
            max_execution_time=max_execution_time,
            parallel_execution=parallel_execution,
            rollback_required=rollback_required
        )
    
    def _determine_approval_requirement(self, decision: DecisionV1, tools: List[Tool]) -> bool:
        """Determine if approval is required"""
        
        approval_reasons = []
        
        # Check decision risk level
        if decision.risk_level in self.config["approval_thresholds"]["risk_level"]:
            approval_reasons.append(f"High risk level: {decision.risk_level}")
        
        # Check decision confidence
        if decision.confidence_level in self.config["approval_thresholds"]["confidence_level"]:
            approval_reasons.append(f"Low confidence: {decision.confidence_level}")
        
        # Check if already flagged for approval in Stage A
        if decision.requires_approval:
            approval_reasons.append("Stage A flagged for approval")
        
        # Check tool permissions
        for tool in tools:
            if tool.permissions in self.config["approval_thresholds"]["permission_level"]:
                approval_reasons.append(f"Admin tool: {tool.name}")
        
        # Check production safety
        production_env = self._detect_production_environment(decision)
        if production_env:
            for tool in tools:
                if not tool.production_safe:
                    approval_reasons.append(f"Non-production-safe tool in production: {tool.name}")
        
        # Check for data modification operations
        data_modification_intents = [
            "automation_deploy_application",
            "automation_update_configuration",
            "configuration_update_config",
            "configuration_manage_users"
        ]
        
        intent_key = f"{decision.intent.category}_{decision.intent.action}"
        if intent_key in data_modification_intents:
            approval_reasons.append("Data modification operation")
        
        return len(approval_reasons) > 0
    
    def _detect_production_environment(self, decision: DecisionV1) -> bool:
        """Detect if this is targeting a production environment"""
        
        # Check explicit environment context
        env = decision.context.get("environment", "").lower()
        if env in ["production", "prod", "live"]:
            return True
        
        # Check for production indicators in entities
        for entity in decision.entities:
            if entity.type == "environment" and entity.value.lower() in ["production", "prod", "live"]:
                return True
            
            # Check hostname patterns
            if entity.type == "hostname":
                hostname = entity.value.lower()
                if any(indicator in hostname for indicator in ["prod", "live", "www", "api"]):
                    return True
        
        # Default assumption for safety
        return True  # Assume production unless explicitly stated otherwise
    
    def _calculate_overall_risk(self, decision: DecisionV1, tools: List[Tool]) -> RiskLevel:
        """Calculate overall risk level considering decision and tools"""
        
        # Start with decision risk level
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        current_risk_score = risk_scores[decision.risk_level]
        
        # Adjust based on tools
        for tool in tools:
            # Admin tools increase risk
            if tool.permissions == PermissionLevel.ADMIN:
                current_risk_score = max(current_risk_score, 2)  # At least medium
            
            # Non-production-safe tools increase risk
            if not tool.production_safe:
                current_risk_score = max(current_risk_score, 3)  # At least high
            
            # Tools with dependencies increase risk
            if tool.dependencies:
                current_risk_score += 0.5
            
            # Long-running tools increase risk
            if tool.max_execution_time > 120:
                current_risk_score += 0.5
        
        # Convert back to risk level
        final_score = min(int(current_risk_score), 4)
        risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return risk_levels[final_score - 1]
    
    def _calculate_max_execution_time(self, decision: DecisionV1, tools: List[Tool], 
                                    risk_level: RiskLevel) -> int:
        """Calculate maximum execution time"""
        
        # Base time from risk level
        base_time = self.config["execution_time_limits"][risk_level]
        
        # Add time for each tool
        tool_time = sum(tool.max_execution_time for tool in tools)
        
        # Add buffer for coordination overhead
        coordination_buffer = len(tools) * 5  # 5 seconds per tool
        
        # Calculate total with safety margin
        total_time = base_time + tool_time + coordination_buffer
        
        # Apply limits based on risk level
        if risk_level == RiskLevel.CRITICAL:
            return min(total_time, 600)  # Max 10 minutes for critical
        elif risk_level == RiskLevel.HIGH:
            return min(total_time, 300)  # Max 5 minutes for high
        else:
            return min(total_time, 180)  # Max 3 minutes for medium/low
    
    def _determine_parallel_execution(self, selected_tools: List[SelectedTool], 
                                    tools: List[Tool]) -> bool:
        """Determine if tools can be executed in parallel"""
        
        # Check configuration limits
        if len(selected_tools) > self.config["parallel_execution_rules"]["max_parallel_tools"]:
            return False
        
        # Check for admin tools
        if not self.config["parallel_execution_rules"]["allow_admin_parallel"]:
            for tool in tools:
                if tool.permissions == PermissionLevel.ADMIN:
                    return False
        
        # Check for dependencies
        if self.config["parallel_execution_rules"]["require_dependencies_sequential"]:
            for selected_tool in selected_tools:
                if selected_tool.depends_on:
                    return False
        
        # Check for conflicting operations
        conflicting_capabilities = [
            {"service_control", "process_management"},
            {"file_management", "configuration_management"},
            {"container_management", "service_control"}
        ]
        
        tool_capabilities = set()
        for tool in tools:
            for capability in tool.capabilities:
                tool_capabilities.add(capability.name)
        
        for conflict_set in conflicting_capabilities:
            if len(conflict_set & tool_capabilities) > 1:
                return False
        
        return len(selected_tools) > 1  # Only enable if multiple tools
    
    def _determine_rollback_requirement(self, decision: DecisionV1, tools: List[Tool], 
                                      production_environment: bool) -> bool:
        """Determine if rollback capability is required"""
        
        rollback_reasons = []
        
        # Check risk level
        if decision.risk_level in self.config["rollback_requirements"]["risk_levels"]:
            rollback_reasons.append("High risk operation")
        
        # Check tool permissions
        for tool in tools:
            if tool.permissions in self.config["rollback_requirements"]["permission_levels"]:
                rollback_reasons.append("Admin-level tool")
                break
        
        # Check production environment
        if production_environment and self.config["rollback_requirements"]["production_environment"]:
            rollback_reasons.append("Production environment")
        
        # Check for data modification
        data_modification_capabilities = [
            "file_management", "configuration_management", "deployment",
            "user_management", "permission_management"
        ]
        
        for tool in tools:
            for capability in tool.capabilities:
                if capability.name in data_modification_capabilities:
                    rollback_reasons.append("Data modification capability")
                    break
        
        return len(rollback_reasons) > 0
    
    def validate_policy(self, policy: ExecutionPolicy, decision: DecisionV1, 
                       selected_tools: List[SelectedTool]) -> Tuple[bool, List[str]]:
        """Validate the execution policy for consistency"""
        
        validation_errors = []
        
        # Check approval consistency
        if policy.requires_approval and decision.confidence_level == ConfidenceLevel.HIGH:
            if decision.risk_level == RiskLevel.LOW:
                validation_errors.append("High confidence, low risk should not require approval")
        
        # Check execution time consistency
        if policy.max_execution_time < 10:
            validation_errors.append("Execution time too short")
        
        if policy.max_execution_time > 600:
            validation_errors.append("Execution time too long")
        
        # Check parallel execution consistency
        if policy.parallel_execution and len(selected_tools) == 1:
            validation_errors.append("Parallel execution enabled for single tool")
        
        # Check rollback consistency
        if policy.rollback_required and policy.risk_level == RiskLevel.LOW:
            validation_errors.append("Rollback required for low-risk operation")
        
        # Check production environment consistency
        if policy.production_environment and not policy.requires_approval:
            # Production operations should generally require approval
            high_risk_tools = []
            for selected_tool in selected_tools:
                tool = self.tool_registry.get_tool(selected_tool.tool_name)
                if tool and (tool.permissions == PermissionLevel.ADMIN or not tool.production_safe):
                    high_risk_tools.append(tool.name)
            
            if high_risk_tools:
                validation_errors.append(f"Production operation with high-risk tools should require approval: {', '.join(high_risk_tools)}")
        
        return len(validation_errors) == 0, validation_errors
    
    def get_policy_explanation(self, policy: ExecutionPolicy, decision: DecisionV1, 
                             selected_tools: List[SelectedTool]) -> Dict[str, str]:
        """Get human-readable explanation of policy decisions"""
        
        explanations = {}
        
        # Approval explanation
        if policy.requires_approval:
            reasons = []
            if decision.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                reasons.append(f"high risk level ({decision.risk_level})")
            if decision.confidence_level == ConfidenceLevel.LOW:
                reasons.append("low confidence")
            if policy.production_environment:
                reasons.append("production environment")
            
            explanations["approval"] = f"Approval required due to: {', '.join(reasons)}"
        else:
            explanations["approval"] = "No approval required - low risk operation"
        
        # Risk level explanation
        explanations["risk"] = f"Risk level {policy.risk_level} based on decision risk and tool requirements"
        
        # Execution time explanation
        explanations["execution_time"] = f"Maximum execution time of {policy.max_execution_time}s based on tool requirements and risk level"
        
        # Parallel execution explanation
        if policy.parallel_execution:
            explanations["parallel"] = "Parallel execution enabled - tools can run concurrently"
        else:
            explanations["parallel"] = "Sequential execution required due to dependencies or admin tools"
        
        # Rollback explanation
        if policy.rollback_required:
            explanations["rollback"] = "Rollback capability required for data modification operations"
        else:
            explanations["rollback"] = "No rollback required - read-only or low-impact operations"
        
        return explanations
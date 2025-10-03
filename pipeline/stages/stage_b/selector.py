"""
Stage B Selector - Main orchestrator for tool selection
Coordinates capability matching, tool selection, and policy determination
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pipeline.schemas.decision_v1 import DecisionV1
from pipeline.schemas.selection_v1 import SelectionV1, SelectedTool, ExecutionPolicy
from llm.client import LLMClient
from llm.prompt_manager import PromptManager
from llm.response_parser import ResponseParser

from .tool_registry import ToolRegistry
from .capability_matcher import CapabilityMatcher, CapabilityMatch
from .policy_engine import PolicyEngine
from .hybrid_orchestrator import HybridOrchestrator
from .profile_loader import ProfileLoader

class StageBSelector:
    """
    Stage B Selector - Tool and capability selection
    
    Takes Decision v1 from Stage A and produces Selection v1 with:
    - Selected tools with justification
    - Execution policy and constraints
    - Additional input requirements
    """
    
    def __init__(self, llm_client: LLMClient, tool_registry: Optional[ToolRegistry] = None,
                 profile_loader: Optional[ProfileLoader] = None):
        self.llm_client = llm_client
        self.tool_registry = tool_registry or ToolRegistry()
        self.capability_matcher = CapabilityMatcher(self.tool_registry)
        self.policy_engine = PolicyEngine(self.tool_registry)
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
        
        # Initialize Hybrid Orchestrator for optimized tool selection
        self.hybrid_orchestrator = HybridOrchestrator(
            profile_loader=profile_loader,
            llm_client=llm_client,
            telemetry_logger=None  # TODO: Add telemetry integration
        )
        
        # Configuration
        self.config = {
            "max_tools_per_selection": 5,
            "min_selection_confidence": 0.3
        }
    
    async def select_tools(self, decision: DecisionV1, 
                          context: Optional[Dict[str, Any]] = None) -> SelectionV1:
        """
        Main tool selection method using Hybrid Orchestrator
        
        Args:
            decision: Decision v1 from Stage A
            context: Additional context for selection
            
        Returns:
            Selection v1 with selected tools and execution policy
        """
        start_time = time.time()
        
        try:
            # Step 1: Extract required capabilities from decision
            required_capabilities = self._extract_capabilities_from_decision(decision)
            
            # Step 2: Build context for hybrid orchestrator
            orchestrator_context = self._build_orchestrator_context(decision, context)
            
            # Step 3: Use Hybrid Orchestrator for tool selection
            # This uses deterministic scoring + LLM tie-breaking when ambiguous
            tool_result = await self.hybrid_orchestrator.select_tool(
                query=decision.original_request,
                required_capabilities=required_capabilities,
                context=orchestrator_context,
                explicit_mode=context.get('preference_mode') if context else None
            )
            
            # Step 4: Convert HybridOrchestrator result to SelectedTool format
            selected_tools = [
                SelectedTool(
                    tool_name=tool_result.tool_name,
                    justification=tool_result.justification,
                    inputs_needed=self._extract_inputs_from_capability(tool_result.capability_name),
                    execution_order=1,
                    depends_on=[]
                )
            ]
            
            # Step 5: Determine execution policy
            execution_policy = self._build_execution_policy_from_result(tool_result, decision)
            
            # Step 6: Calculate additional inputs needed
            additional_inputs = self._calculate_additional_inputs(decision, selected_tools)
            
            # Step 7: Determine environment requirements
            env_requirements = self._determine_environment_requirements(selected_tools)
            
            # Step 8: Calculate selection confidence
            selection_confidence = self._calculate_confidence_from_result(tool_result)
            
            # Step 9: Determine next stage
            next_stage = self._determine_next_stage(decision, selected_tools, execution_policy)
            
            # Step 10: Build Selection v1 response
            processing_time = int((time.time() - start_time) * 1000)
            
            selection = SelectionV1(
                selection_id=self._generate_selection_id(),
                decision_id=decision.decision_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                selected_tools=selected_tools,
                total_tools=len(selected_tools),
                policy=execution_policy,
                additional_inputs_needed=additional_inputs,
                environment_requirements=env_requirements,
                processing_time_ms=processing_time,
                selection_confidence=selection_confidence,
                next_stage=next_stage,
                ready_for_execution=self._is_ready_for_execution(selected_tools, additional_inputs)
            )
            
            return selection
            
        except Exception as e:
            # Re-raise - NO FALLBACKS per system charter
            raise RuntimeError(f"Tool selection failed: {str(e)}") from e
    
    async def _find_capability_matches(self, decision: DecisionV1) -> List[CapabilityMatch]:
        """Find tools that match the decision requirements"""
        
        matches = self.capability_matcher.find_matching_tools(
            decision, 
            max_tools=self.config["max_tools_per_selection"]
        )
        
        # Filter by minimum confidence
        filtered_matches = [
            match for match in matches 
            if match.confidence >= self.config["min_selection_confidence"]
        ]
        
        return filtered_matches
    
    async def _llm_tool_selection(self, decision: DecisionV1, 
                                matches: List[CapabilityMatch]) -> List[SelectedTool]:
        """Use LLM to make intelligent tool selection"""
        
        try:
            # Prepare tool information for LLM
            tools_info = []
            for match in matches:
                tool_info = {
                    "name": match.tool.name,
                    "description": match.tool.description,
                    "capabilities": [cap.name for cap in match.tool.capabilities],
                    "confidence": match.confidence,
                    "justification": match.justification,
                    "missing_inputs": match.missing_inputs,
                    "permissions": match.tool.permissions.value,
                    "production_safe": match.tool.production_safe
                }
                tools_info.append(tool_info)
            
            # Create LLM prompt
            prompt = self.prompt_manager.get_tool_selection_prompt(
                decision=decision.model_dump(),
                available_tools=tools_info
            )
            
            # Get LLM response
            response = await self.llm_client.generate(prompt)
            
            # Parse LLM response
            selection_data = self.response_parser.parse_tool_selection(response.content)
            
            # Convert to SelectedTool objects
            selected_tools = []
            for i, tool_data in enumerate(selection_data.get("selected_tools", [])):
                selected_tool = SelectedTool(
                    tool_name=tool_data.get("tool_name", ""),
                    justification=tool_data.get("justification", "LLM selection"),
                    inputs_needed=tool_data.get("inputs_needed", []),
                    execution_order=tool_data.get("execution_order", i + 1),
                    depends_on=tool_data.get("depends_on", [])
                )
                selected_tools.append(selected_tool)
            
            # Validate LLM selection
            if self._validate_llm_selection(selected_tools, matches):
                return selected_tools
            else:
                # Fall back to rule-based selection
                return self._rule_based_tool_selection(matches, decision)
                
        except Exception as e:
            # Fall back to rule-based selection on LLM error
            return self._rule_based_tool_selection(matches, decision)
    
    async def _llm_tool_selection_direct(self, decision: DecisionV1, 
                                        tools: List) -> List[SelectedTool]:
        """
        Pure LLM-based tool selection - no pre-filtering or scoring
        This is the ONLY selection method per the system charter
        NO FALLBACKS - if this fails, we fail
        """
        
        # Prepare tool information for LLM - ALL tools with their full descriptions
        tools_info = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "required_inputs": cap.required_inputs,
                        "optional_inputs": cap.optional_inputs
                    }
                    for cap in tool.capabilities
                ],
                "permissions": tool.permissions.value,
                "production_safe": tool.production_safe,
                "required_inputs": tool.required_inputs,
                "dependencies": tool.dependencies
            }
            tools_info.append(tool_info)
        
        # Create LLM prompt with comprehensive tool selection rubric
        prompt = self.prompt_manager.get_tool_selection_prompt(
            decision=decision.model_dump(),
            available_tools=tools_info
        )
        
        # Get LLM response - if this fails, let it fail
        response = await self.llm_client.generate(prompt)
        
        # Parse LLM response - if this fails, let it fail
        selection_data = self.response_parser.parse_tool_selection(response.content)
        
        # Convert to SelectedTool objects
        selected_tools = []
        for i, tool_data in enumerate(selection_data.get("selected_tools", [])):
            selected_tool = SelectedTool(
                tool_name=tool_data.get("tool_name", ""),
                justification=tool_data.get("justification", "LLM selection"),
                inputs_needed=tool_data.get("inputs_needed", []),
                execution_order=tool_data.get("execution_order", i + 1),
                depends_on=tool_data.get("depends_on", [])
            )
            selected_tools.append(selected_tool)
        
        return selected_tools
    
    def _rule_based_tool_selection(self, matches: List[CapabilityMatch], 
                                 decision: DecisionV1) -> List[SelectedTool]:
        """Rule-based tool selection as fallback"""
        
        if not matches:
            return self._create_default_tools(decision)
        
        # Use capability matcher's selection logic
        selected_tools = self.capability_matcher.select_optimal_tools(matches, decision)
        
        # Ensure we have at least one tool
        if not selected_tools and matches:
            # Select the highest confidence match
            best_match = max(matches, key=lambda x: x.confidence)
            selected_tools = [
                SelectedTool(
                    tool_name=best_match.tool.name,
                    justification=best_match.justification,
                    inputs_needed=best_match.missing_inputs,
                    execution_order=1,
                    depends_on=best_match.tool.dependencies
                )
            ]
        
        return selected_tools
    
    def _create_default_tools(self, decision: DecisionV1) -> List[SelectedTool]:
        """Create default tool selection when no matches found"""
        
        # Default tools based on intent category
        default_mappings = {
            "automation": "systemctl",
            "monitoring": "ps",
            "troubleshooting": "journalctl",
            "configuration": "config_manager",
            "information": "info_display"
        }
        
        default_tool_name = default_mappings.get(decision.intent.category, "info_display")
        
        return [
            SelectedTool(
                tool_name=default_tool_name,
                justification=f"Default tool for {decision.intent.category} operations",
                inputs_needed=["user_request"],
                execution_order=1,
                depends_on=[]
            )
        ]
    
    def _calculate_additional_inputs(self, decision: DecisionV1, 
                                   selected_tools: List[SelectedTool]) -> List[str]:
        """Calculate additional inputs needed beyond decision data"""
        
        additional_inputs = set()
        
        # Collect all inputs needed by selected tools
        for selected_tool in selected_tools:
            additional_inputs.update(selected_tool.inputs_needed)
        
        # Remove inputs available from decision
        available_inputs = {
            "user_request",  # original_request
            "timestamp",     # decision timestamp
            "decision_id",   # decision identifier
        }
        
        # Add entity values as available inputs
        for entity in decision.entities:
            if entity.type == "service":
                available_inputs.update(["service_name", "service"])
            elif entity.type == "hostname":
                available_inputs.update(["hostname", "host", "target"])
            elif entity.type == "command":
                available_inputs.update(["command", "cmd"])
            elif entity.type == "file_path":
                available_inputs.update(["path", "file", "config_file"])
            elif entity.type == "port":
                available_inputs.add("port")
            elif entity.type == "environment":
                available_inputs.update(["environment", "env"])
            elif entity.type == "application":
                available_inputs.update(["application", "app"])
            elif entity.type == "database":
                available_inputs.update(["database", "db"])
        
        # Return only truly missing inputs
        missing_inputs = list(additional_inputs - available_inputs)
        return missing_inputs
    
    def _determine_environment_requirements(self, selected_tools: List[SelectedTool]) -> Dict[str, Any]:
        """Determine environment requirements for selected tools"""
        
        requirements = {}
        
        # Check tool requirements
        for selected_tool in selected_tools:
            tool = self.tool_registry.get_tool(selected_tool.tool_name)
            if not tool:
                continue
            
            # OS requirements
            if tool.name in ["systemctl", "journalctl", "ps"]:
                requirements["os"] = "linux"
            
            # Permission requirements
            if tool.permissions.value == "admin":
                requirements["sudo_required"] = True
            
            # Service dependencies
            if tool.dependencies:
                if "dependencies" not in requirements:
                    requirements["dependencies"] = []
                requirements["dependencies"].extend(tool.dependencies)
            
            # Docker requirements
            if tool.name == "docker":
                requirements["docker_available"] = True
        
        return requirements
    
    def _calculate_selection_confidence(self, matches: List[CapabilityMatch], 
                                      selected_tools: List[SelectedTool], 
                                      decision: DecisionV1) -> float:
        """Calculate overall confidence in the tool selection"""
        
        if not selected_tools:
            return 0.1
        
        # Base confidence from capability matches
        if matches:
            match_confidences = [match.confidence for match in matches[:len(selected_tools)]]
            base_confidence = sum(match_confidences) / len(match_confidences)
        else:
            base_confidence = 0.3  # Default selection confidence
        
        # Adjust based on decision confidence
        decision_factor = decision.overall_confidence * 0.3
        
        # Adjust based on missing inputs
        missing_inputs_penalty = 0
        for selected_tool in selected_tools:
            missing_inputs_penalty += len(selected_tool.inputs_needed) * 0.05
        
        # Calculate final confidence
        final_confidence = base_confidence + decision_factor - missing_inputs_penalty
        
        return max(min(final_confidence, 1.0), 0.1)
    
    def _determine_next_stage(self, decision: DecisionV1, selected_tools: List[SelectedTool], 
                            policy: ExecutionPolicy) -> str:
        """Determine the next stage in the pipeline"""
        
        # If no tools selected or high complexity, go to planner
        if not selected_tools or len(selected_tools) > 1:
            return "stage_c"
        
        # If requires approval or high risk, go to planner
        if policy.requires_approval or policy.risk_level.value in ["high", "critical"]:
            return "stage_c"
        
        # Simple, low-risk operations can skip to answerer
        if (len(selected_tools) == 1 and 
            policy.risk_level.value == "low" and 
            not policy.rollback_required):
            return "stage_d"
        
        # Default to planner for safety
        return "stage_c"
    
    def _is_ready_for_execution(self, selected_tools: List[SelectedTool], 
                              additional_inputs: List[str]) -> bool:
        """Check if selection is ready for immediate execution"""
        
        # Not ready if missing inputs
        if additional_inputs:
            return False
        
        # Not ready if no tools selected
        if not selected_tools:
            return False
        
        # Not ready if tools have unresolved dependencies
        tool_names = {tool.tool_name for tool in selected_tools}
        for tool in selected_tools:
            for dependency in tool.depends_on:
                if dependency not in tool_names:
                    return False
        
        return True
    
    def _validate_llm_selection(self, selected_tools: List[SelectedTool], 
                              matches: List[CapabilityMatch]) -> bool:
        """Validate LLM tool selection against available matches"""
        
        if not selected_tools:
            return False
        
        # Check that selected tools exist in matches
        available_tool_names = {match.tool.name for match in matches}
        for selected_tool in selected_tools:
            if selected_tool.tool_name not in available_tool_names:
                return False
        
        # Check for reasonable justifications
        for selected_tool in selected_tools:
            if not selected_tool.justification or len(selected_tool.justification) < 10:
                return False
        
        return True
    
    async def _is_llm_available(self) -> bool:
        """Check if LLM is available for selection"""
        try:
            return await self.llm_client.health_check()
        except:
            return False
    
    def _generate_selection_id(self) -> str:
        """Generate unique selection ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"sel_{timestamp}_{unique_id}"
    
    async def _create_fallback_selection(self, decision: DecisionV1, error: str) -> SelectionV1:
        """Create fallback selection when main selection fails"""
        
        # Create minimal safe selection
        fallback_tools = self._create_default_tools(decision)
        
        # Create conservative policy
        fallback_policy = ExecutionPolicy(
            requires_approval=True,  # Conservative: require approval
            production_environment=True,  # Assume production for safety
            risk_level="medium",  # Conservative risk level
            max_execution_time=60,
            parallel_execution=False,
            rollback_required=True
        )
        
        return SelectionV1(
            selection_id=self._generate_selection_id(),
            decision_id=decision.decision_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            selected_tools=fallback_tools,
            total_tools=len(fallback_tools),
            policy=fallback_policy,
            additional_inputs_needed=["user_confirmation"],
            environment_requirements={"fallback_mode": True},
            processing_time_ms=0,
            selection_confidence=0.2,  # Low confidence for fallback
            next_stage="stage_c",  # Always go to planner for fallback
            ready_for_execution=False
        )
    
    def _extract_capabilities_from_decision(self, decision: DecisionV1) -> List[str]:
        """
        Extract required capabilities from DecisionV1
        
        Maps intent.action to capability names that tools can provide
        """
        # Map intent actions to capability names
        capability_mapping = {
            "restart_service": ["service_control"],
            "check_status": ["service_status"],
            "show_status": ["system_monitoring"],  # For information requests
            "view_logs": ["log_access"],
            "search_files": ["file_search"],
            "read_file": ["file_read"],
            "edit_file": ["file_edit"],
            "list_directory": ["directory_list"],
            "execute_command": ["shell_execution"],
            "monitor_system": ["system_monitoring"],
            "configure_service": ["configuration_management"]
        }
        
        action = decision.intent.action
        capabilities = capability_mapping.get(action, ["system_monitoring"])  # Default to monitoring for unknown actions
        
        return capabilities
    
    def _build_orchestrator_context(self, decision: DecisionV1, 
                                   context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build context dict for HybridOrchestrator from DecisionV1
        
        Includes runtime context like environment, cost limits, etc.
        """
        orchestrator_context = {
            "environment": context.get("environment", "production") if context else "production",
            "require_production_safe": decision.risk_level in ["high", "critical"],
            "decision_confidence": decision.overall_confidence,
            "risk_level": decision.risk_level.value,
        }
        
        # Add cost limit if specified
        if context and "cost_limit" in context:
            orchestrator_context["cost_limit"] = context["cost_limit"]
        
        # Add any additional context from decision
        if decision.context:
            orchestrator_context.update(decision.context)
        
        return orchestrator_context
    
    def _extract_inputs_from_capability(self, capability_name: str) -> List[str]:
        """
        Extract required inputs for a capability
        
        This is a simple mapping - in production, this would come from
        the tool registry or capability definitions
        """
        input_mapping = {
            "service_control": ["service_name"],
            "service_status": ["service_name"],
            "log_access": ["log_file", "service_name"],
            "file_search": ["search_pattern", "directory"],
            "file_read": ["file_path"],
            "file_edit": ["file_path", "edit_content"],
            "directory_list": ["directory_path"],
            "shell_execution": ["command"],
            "system_monitoring": ["metric_type"],
            "configuration_management": ["config_file", "config_values"]
        }
        
        return input_mapping.get(capability_name, ["user_input"])
    
    def _build_execution_policy_from_result(self, tool_result, decision: DecisionV1) -> ExecutionPolicy:
        """
        Build ExecutionPolicy from HybridOrchestrator result
        """
        return ExecutionPolicy(
            requires_approval=decision.requires_approval or decision.risk_level in ["high", "critical"],
            production_environment=decision.context.get("environment") == "production" if decision.context else False,
            risk_level=decision.risk_level,
            max_execution_time=int(tool_result.estimated_time_ms / 1000),  # Convert ms to seconds
            parallel_execution=False,  # Single tool for now
            rollback_required=decision.risk_level in ["high", "critical"]
        )
    
    def _calculate_confidence_from_result(self, tool_result) -> float:
        """
        Calculate selection confidence from HybridOrchestrator result
        
        Higher confidence for deterministic selection, slightly lower for LLM tie-breaking
        """
        if tool_result.selection_method == "deterministic":
            return 0.95
        elif tool_result.selection_method == "llm_tiebreaker":
            return 0.85
        else:
            return 0.75

    async def health_check(self) -> Dict[str, Any]:
        """Health check for Stage B Selector"""
        
        health_status = {
            "stage_b_selector": "healthy",
            "tool_registry": {
                "status": "healthy",
                "total_tools": self.tool_registry.get_tool_count(),
                "stats": self.tool_registry.get_registry_stats()
            },
            "capability_matcher": "healthy",
            "policy_engine": "healthy",
            "llm_client": "unknown",
            "hybrid_orchestrator": "healthy"
        }
        
        # Check LLM client health
        try:
            llm_healthy = await self.llm_client.health_check()
            health_status["llm_client"] = "healthy" if llm_healthy else "unhealthy"
        except:
            health_status["llm_client"] = "unhealthy"
        
        return health_status
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Stage B capabilities and configuration"""
        
        return {
            "stage": "stage_b_selector",
            "version": "1.0.0",
            "capabilities": [
                "tool_selection",
                "capability_matching", 
                "policy_determination",
                "risk_assessment",
                "execution_planning"
            ],
            "supported_intents": [
                "automation",
                "monitoring", 
                "troubleshooting",
                "configuration",
                "information"
            ],
            "tool_registry": {
                "total_tools": self.tool_registry.get_tool_count(),
                "available_tools": [tool.name for tool in self.tool_registry.get_all_tools()]
            },
            "configuration": self.config
        }
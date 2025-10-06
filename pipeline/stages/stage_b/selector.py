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

from .hybrid_orchestrator import HybridOrchestrator
from .profile_loader import ProfileLoader

class StageBSelector:
    """
    Stage B Selector - Tool and capability selection
    
    Takes Decision v1 from Stage A and produces Selection v1 with:
    - Selected tools with justification
    - Execution policy and constraints
    - Additional input requirements
    
    NOTE: This class uses the database-backed HybridOrchestrator for tool selection.
    The old tool_registry, capability_matcher, and policy_engine have been removed
    in favor of the database as the single source of truth.
    """
    
    def __init__(self, llm_client: LLMClient, profile_loader: Optional[ProfileLoader] = None):
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
        
        # Initialize Hybrid Orchestrator for optimized tool selection
        # This uses the database tool catalog as the single source of truth
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
            
            # CAPABILITY-FIRST ARCHITECTURE: Handle information-only requests
            # If Stage A determined no capabilities are needed, this is a pure information request
            # that should be answered by the LLM without tool execution
            if not required_capabilities:
                return self._create_information_only_selection(decision, start_time)
            
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
        """Determine environment requirements for selected tools
        
        Note: This method now uses tool metadata from the database via HybridOrchestrator.
        The tool_registry has been removed - database is the single source of truth.
        """
        
        requirements = {}
        
        # Check tool requirements based on tool names
        # This is a simplified version - full requirements should come from database
        for selected_tool in selected_tools:
            tool_name = selected_tool.tool_name
            
            # OS requirements (based on common tool patterns)
            if tool_name in ["systemctl", "journalctl", "ps", "top", "htop"]:
                requirements["os"] = "linux"
            
            # Permission requirements (based on common patterns)
            if tool_name in ["systemctl", "iptables", "useradd", "usermod"]:
                requirements["sudo_required"] = True
            
            # Docker requirements
            if tool_name == "docker":
                requirements["docker_available"] = True
        
        return requirements
    
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
    
    def _extract_capabilities_from_decision(self, decision: DecisionV1) -> List[str]:
        """
        Extract required capabilities from DecisionV1
        
        Stage A now directly provides capabilities, so we just extract them.
        No more hardcoded action-to-capability mapping!
        """
        # Get capabilities directly from Stage A's intent classification
        capabilities = decision.intent.capabilities
        
        # If Stage A didn't provide capabilities, this is an information request
        # that doesn't require tool execution
        if not capabilities:
            # Log for visibility
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"No capabilities provided by Stage A for action '{decision.intent.action}'. "
                f"This is likely an information/explanation request that doesn't require tools."
            )
        
        return capabilities
    
    def _create_information_only_selection(self, decision: DecisionV1, start_time: float) -> SelectionV1:
        """
        Create a SelectionV1 for information-only requests that don't require tools.
        
        This handles cases where Stage A determined the request can be answered
        without executing any tools (e.g., "what kind of credentials do we use?")
        """
        processing_time = int((time.time() - start_time) * 1000)
        
        return SelectionV1(
            selection_id=self._generate_selection_id(),
            decision_id=decision.decision_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            selected_tools=[],  # No tools needed
            total_tools=0,
            policy=ExecutionPolicy(
                requires_approval=False,
                production_environment=False,
                risk_level=decision.risk_level,
                max_execution_time=0,
                parallel_execution=False,
                rollback_required=False
            ),
            additional_inputs_needed=[],
            environment_requirements={
                "sudo_required": False,
                "dependencies": []
            },
            processing_time_ms=processing_time,
            selection_confidence=decision.overall_confidence,
            next_stage="stage_d",  # Skip Stage C (planning) and go directly to Stage D (response)
            ready_for_execution=True  # Ready to generate response
        )
    
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
        
        This mapping is derived from the database tool catalog.
        Each capability maps to the required inputs needed by tools that provide it.
        
        NOTE: Most capabilities require 'host' parameter, but we extract the most
        specific required inputs. The 'host' parameter is typically added by the
        execution layer based on asset context.
        """
        input_mapping = {
            # API and HTTP
            "api_query": ["endpoint"],
            "http_client": ["host"],
            
            # Asset management
            "asset_management": ["host"],
            "asset_query": ["host"],
            "credential_access": ["asset_id", "justification"],
            "infrastructure_info": [],
            "resource_listing": [],
            "secret_retrieval": ["asset_id", "justification"],
            
            # Disk operations
            "disk_management": ["host"],
            "disk_monitoring": ["host"],
            
            # DNS and network
            "dns_query": ["host"],
            "network_info": ["host"],
            "network_monitoring": ["host"],
            "network_testing": ["host"],
            "packet_capture": ["host"],
            "protocol_analysis": ["host"],
            
            # Logs
            "log_analysis": ["host"],
            
            # Memory
            "memory_monitoring": ["host"],
            
            # Processes
            "process_management": ["host"],
            "process_monitoring": ["host"],
            
            # Services
            "service_management": ["service_name", "host"],
            
            # System
            "system_info": ["host"],
            "system_monitoring": ["metric_type"],
            
            # Text operations
            "text_search": ["pattern", "target"],
            
            # Windows
            "windows_automation": ["command"],
            "windows_service_management": ["service_name"]
        }
        
        # NO FALLBACKS! If capability is not mapped, raise an error
        if capability_name not in input_mapping:
            raise ValueError(
                f"Unknown capability '{capability_name}'. "
                f"This capability must be added to input_mapping in selector.py. "
                f"Available capabilities: {sorted(input_mapping.keys())}"
            )
        
        return input_mapping[capability_name]
    
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
        """Health check for Stage B Selector
        
        Note: tool_registry has been removed - database is the single source of truth.
        """
        
        health_status = {
            "stage_b_selector": "healthy",
            "database": "healthy",  # Database is now the source of truth
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
        """Get Stage B capabilities and configuration
        
        Note: tool_registry has been removed - database is the single source of truth.
        Tool information is now queried from the database via HybridOrchestrator.
        """
        
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
            "tool_source": "database",  # Database is the single source of truth
            "configuration": self.config
        }
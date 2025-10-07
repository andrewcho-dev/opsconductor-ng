"""
Stage C Planner - Main Orchestrator

The main planner that coordinates all planning components to create
comprehensive, safe, executable step-by-step plans.
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ...schemas.decision_v1 import DecisionV1
from ...schemas.selection_v1 import SelectionV1
from ...schemas.plan_v1 import PlanV1, ExecutionPlan, ExecutionMetadata

from .step_generator import StepGenerator
from .dependency_resolver import DependencyResolver, DependencyError
from .safety_planner import SafetyPlanner
from .resource_planner import ResourcePlanner

logger = logging.getLogger(__name__)


class PlanningError(Exception):
    """Raised when planning fails"""
    pass


class StageCPlanner:
    """
    Main Stage C Planner orchestrator.
    
    This class coordinates all planning components to create comprehensive
    execution plans with proper sequencing, safety measures, and resource allocation.
    
    Responsibilities:
    - Orchestrate step generation, dependency resolution, and safety planning
    - Create complete Plan v1 output with all required components
    - Handle planning errors and provide fallback strategies
    - Integrate with LLM for intelligent planning when available
    - Validate and optimize execution plans
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the Stage C Planner.
        
        Args:
            llm_client: Optional LLM client for intelligent planning
        """
        self.llm_client = llm_client
        
        # Initialize planning components
        self.step_generator = StepGenerator()
        self.dependency_resolver = DependencyResolver()
        self.safety_planner = SafetyPlanner()
        self.resource_planner = ResourcePlanner()
        
        # Planning statistics (thread-safe)
        self._stats_lock = threading.Lock()
        self.stats = {
            "plans_created": 0,
            "total_processing_time_ms": 0,
            "average_processing_time_ms": 0,
            "errors_encountered": 0,
            "llm_calls_made": 0,
            "fallback_plans_used": 0
        }
    
    async def create_plan(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1,
        sop_snippets: Optional[List[str]] = None
    ) -> PlanV1:
        """
        Create a comprehensive execution plan.
        
        Args:
            decision: Decision from Stage A
            selection: Selection from Stage B
            sop_snippets: Optional SOP procedure snippets
            
        Returns:
            Complete Plan v1 with execution steps, safety measures, and metadata
            
        Raises:
            PlanningError: If planning fails and no fallback is possible
        """
        start_time = time.time()
        
        try:
            # Generate execution steps
            steps = await self._generate_execution_steps(decision, selection)
            
            # Check if we have any steps to work with
            if not steps:
                raise PlanningError("No execution steps could be generated from the provided selection")
            
            # Resolve dependencies and optimize sequencing
            ordered_steps = self._resolve_dependencies(steps)
            
            # Create safety measures
            safety_checks = self._create_safety_measures(
                ordered_steps, decision, selection
            )
            
            # Plan resources and observability
            observability, metadata = self._plan_resources(
                ordered_steps, decision, selection
            )
            
            # Create execution plan
            execution_plan = ExecutionPlan(
                steps=ordered_steps,
                safety_checks=safety_checks,
                rollback_plan=[],  # Rollback functionality removed
                observability=observability
            )
            
            # Create final plan
            processing_time_ms = max(1, int((time.time() - start_time) * 1000))
            
            plan = PlanV1(
                plan=execution_plan,
                execution_metadata=metadata,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=processing_time_ms
            )
            
            # Update statistics
            self._update_stats(processing_time_ms, success=True)
            
            return plan
            
        except Exception as e:
            # Update error statistics
            self._update_stats(max(1, int((time.time() - start_time) * 1000)), success=False)
            
            # FAIL FAST: No fallbacks! OpsConductor requires AI-BRAIN to function
            raise PlanningError(
                f"Stage C planning failed - OpsConductor requires AI-BRAIN (LLM) to function: {str(e)}"
            )
    
    async def _generate_execution_steps(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List:
        """Generate execution steps from decision and selection"""
        try:
            # ALWAYS use LLM for intelligent step generation if available
            if self.llm_client:
                logger.info("🧠 Stage C using LLM for intelligent planning (NO RULES!)")
                return await self._generate_steps_with_llm(decision, selection)
            else:
                # No LLM available - fail fast
                logger.error("❌ Stage C: No LLM client available - FAILING FAST")
                raise PlanningError("LLM is required for Stage C planning - OpsConductor cannot function without AI-BRAIN")
        
        except Exception as e:
            # FAIL FAST: OpsConductor requires AI-BRAIN to function
            logger.error(f"❌ Stage C: LLM planning failed - {str(e)}")
            raise PlanningError(f"AI-BRAIN (LLM) unavailable for Stage C - OpsConductor cannot function without LLM: {str(e)}")
    
    def _resolve_dependencies(self, steps) -> List:
        """Resolve step dependencies and create proper execution order"""
        try:
            # Validate dependencies first
            is_valid, errors = self.dependency_resolver.validate_dependencies(steps)
            if not is_valid:
                raise DependencyError(f"Dependency validation failed: {'; '.join(errors)}")
            
            # Resolve dependencies and order steps
            ordered_steps = self.dependency_resolver.resolve_dependencies(steps)
            
            return ordered_steps
            
        except DependencyError as e:
            # Try to fix common dependency issues
            fixed_steps = self._fix_dependency_issues(steps)
            return self.dependency_resolver.resolve_dependencies(fixed_steps)
    
    def _create_safety_measures(
        self, 
        steps, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List:
        """Create comprehensive safety checks"""
        return self.safety_planner.create_safety_plan(steps, decision, selection)
    
    def _plan_resources(
        self, 
        steps, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Tuple:
        """Plan resources, observability, and execution metadata"""
        return self.resource_planner.create_resource_plan(steps, decision, selection)
    
    async def _generate_steps_with_llm(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List:
        """Generate steps using LLM for intelligent planning"""
        from ...schemas.plan_v1 import ExecutionStep
        from llm.client import LLMRequest
        import json
        
        self._increment_stat("llm_calls_made")
        
        # Build the system prompt with schema knowledge
        system_prompt = self._build_planning_system_prompt()
        
        # Build the user prompt with decision and selection context
        user_prompt = self._build_planning_user_prompt(decision, selection)
        
        # Create LLM request
        llm_request = LLMRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Low temperature for consistent planning
            max_tokens=2000
        )
        
        # Get response from LLM
        response = await self.llm_client.generate(llm_request)
        
        # Parse the response into execution steps
        steps = self._parse_llm_planning_response(response.content, selection)
        
        return steps
    
    def _fix_dependency_issues(self, steps) -> List:
        """Attempt to fix common dependency issues"""
        fixed_steps = []
        
        for step in steps:
            # Create a copy of the step
            fixed_step = step.model_copy()
            
            # Remove self-dependencies
            fixed_step.depends_on = [
                dep for dep in fixed_step.depends_on 
                if dep != step.id
            ]
            
            # Remove invalid wildcard dependencies that don't match any steps
            valid_deps = []
            for dep in fixed_step.depends_on:
                if '*' in dep:
                    # Check if wildcard matches any step
                    matches = self.dependency_resolver._resolve_wildcard_dependency(dep, steps)
                    if matches:
                        valid_deps.append(dep)
                else:
                    # Keep direct dependencies (will be validated later)
                    valid_deps.append(dep)
            
            fixed_step.depends_on = valid_deps
            fixed_steps.append(fixed_step)
        
        return fixed_steps
    

    def _update_stats(self, processing_time_ms: int, success: bool) -> None:
        """Update planning statistics (thread-safe)"""
        with self._stats_lock:
            self.stats["plans_created"] += 1
            self.stats["total_processing_time_ms"] += processing_time_ms
            self.stats["average_processing_time_ms"] = (
                self.stats["total_processing_time_ms"] // self.stats["plans_created"]
            )
            
            if not success:
                self.stats["errors_encountered"] += 1
    
    def _increment_stat(self, stat_name: str, amount: int = 1) -> None:
        """Thread-safe increment of a specific statistic"""
        with self._stats_lock:
            self.stats[stat_name] += amount
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the planner (thread-safe)"""
        with self._stats_lock:
            stats_copy = self.stats.copy()
        
        return {
            "stage_c_planner": "healthy",
            "component": "stage_c_planner",
            "statistics": stats_copy,
            "components": {
                "step_generator": "operational",
                "dependency_resolver": "operational", 
                "safety_planner": "operational",
                "resource_planner": "operational"
            },
            "llm_integration": "available" if self.llm_client else "disabled"
        }
    
    def validate_plan(self, plan: PlanV1) -> Tuple[bool, List[str]]:
        """
        Validate a generated plan for completeness and safety.
        
        Args:
            plan: Plan to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Validate plan structure
        if not plan.plan.steps:
            issues.append("Plan contains no execution steps")
        
        # Validate step dependencies
        step_ids = {step.id for step in plan.plan.steps}
        for step in plan.plan.steps:
            for dep in step.depends_on:
                if '*' not in dep and dep not in step_ids:
                    issues.append(f"Step {step.id} depends on non-existent step {dep}")
        
        # Validate safety checks
        if not plan.plan.safety_checks:
            issues.append("Plan contains no safety checks")
        
        # Validate rollback procedures for destructive operations
        rollback_step_ids = {rb.step_id for rb in plan.plan.rollback_plan}
        for step in plan.plan.steps:
            if self._is_destructive_operation(step):
                if step.id not in rollback_step_ids:
                    issues.append(f"Destructive step {step.id} has no rollback procedure")
        
        # Validate execution metadata
        if plan.execution_metadata.total_estimated_time <= 0:
            issues.append("Invalid total estimated time")
        
        return len(issues) == 0, issues
    
    def _is_destructive_operation(self, step) -> bool:
        """
        Determine if a step represents a destructive operation that needs rollback.
        
        Args:
            step: ExecutionStep to check
            
        Returns:
            True if the operation is destructive and needs rollback
        """
        tool = step.tool
        
        # Check systemctl operations
        if tool == "systemctl":
            action = step.inputs.get("action", "status")
            # Only start, stop, restart, enable, disable are destructive
            destructive_actions = {"start", "stop", "restart", "enable", "disable", "reload"}
            return action in destructive_actions
        
        # File operations are generally destructive
        if tool in {"file_manager", "config_manager"}:
            return True
        
        # Docker operations can be destructive
        if tool == "docker":
            action = step.inputs.get("action", "list")
            # Only certain docker actions are destructive
            destructive_actions = {"start", "stop", "restart", "remove", "create", "build"}
            return action in destructive_actions
        
        # Network tools can be destructive if they modify configuration
        if tool == "network_tools":
            action = step.inputs.get("action", "status")
            destructive_actions = {"configure", "restart", "modify"}
            return action in destructive_actions
        
        # Read-only tools are not destructive
        readonly_tools = {"ps", "journalctl", "info_display"}
        return tool not in readonly_tools
    
    def optimize_plan(self, plan: PlanV1) -> PlanV1:
        """
        Optimize an execution plan for better performance and safety.
        
        Args:
            plan: Plan to optimize
            
        Returns:
            Optimized plan
        """
        # Create optimized copy
        optimized_plan = plan.model_copy()
        
        # Optimize step ordering for parallel execution
        parallel_groups = self.dependency_resolver.identify_parallel_groups(plan.plan.steps)
        
        # Update execution order based on parallel groups
        execution_order = 1
        for group in parallel_groups:
            for step in group:
                # Find the step in optimized plan and update its order
                for opt_step in optimized_plan.plan.steps:
                    if opt_step.id == step.id:
                        opt_step.execution_order = execution_order
                        break
            execution_order += 1
        
        # Add optimization metadata
        optimized_plan.execution_metadata.risk_factors.append("plan_optimized")
        
        return optimized_plan
    
    def _build_planning_system_prompt(self) -> str:
        """Build the system prompt for LLM-based planning with schema knowledge"""
        return """You are Stage C Planner - the intelligent planning component of OpsConductor.

Your role is to create detailed execution plans based on the user's intent and selected tools.

# ASSET DATABASE SCHEMA
When planning asset queries, you have access to the following fields in the assets database:

**Basic Information:**
- name: Asset name
- hostname: Hostname
- ip_address: IP address
- description: Description
- tags: List of tags

**Device/Hardware:**
- device_type: Type of device (server, router, switch, firewall, load_balancer, storage, other)
- hardware_make: Hardware manufacturer
- hardware_model: Hardware model
- serial_number: Serial number

**Operating System:**
- os_type: OS type (linux, windows, macos, unix, other)
- os_version: OS version

**Location:**
- physical_address: Physical address
- data_center: Data center name
- building: Building name
- room: Room number
- rack_position: Rack position
- rack_location: Rack location
- gps_coordinates: GPS coordinates

**Status and Management:**
- status: Status (active, inactive, maintenance, decommissioned)
- environment: Environment (production, staging, development, testing)
- criticality: Criticality level (low, medium, high, critical)
- owner: Owner name
- support_contact: Support contact
- contract_number: Contract number

**Services:**
- service_type: Primary service type (ssh, rdp, http, https, database, ftp, etc.)
- port: Primary service port
- is_secure: Whether primary service is secure
- database_type: Database type (if applicable: mysql, postgresql, mongodb, oracle, mssql, redis)
- database_name: Database name (if applicable)
- secondary_service_type: Secondary service type
- secondary_port: Secondary service port

# YOUR TASK
For each selected tool, create an execution step with:
1. **Intelligent field selection**: Choose ONLY the fields needed to answer the user's query
   - For "list all" queries: Select key identifying fields (name, hostname, ip_address, os_version, device_type, environment, service_type, database_type, criticality)
   - For specific queries: Select only relevant fields
   - NEVER request all fields unless explicitly needed

2. **Proper parameters**: Extract query parameters from the user's intent
   - query_type: "list_all", "filter", "search", "get_by_id"
   - filters: Dictionary of field filters (e.g., {"environment": "production", "device_type": "server"})
   - fields: List of field names to retrieve (CRITICAL - be selective!)

3. **Clear descriptions**: Describe what each step will do

4. **Dependencies**: Identify if steps depend on each other

Return your response as a JSON array of execution steps with this structure:
[
  {
    "tool": "asset-service-query",
    "description": "Brief description of what this step does",
    "inputs": {
      "query_type": "list_all" | "filter" | "search" | "get_by_id",
      "filters": {},
      "fields": ["field1", "field2", ...],
      "search_term": "optional search term",
      "asset_id": "optional asset ID"
    },
    "preconditions": ["list of preconditions"],
    "success_criteria": ["list of success criteria"],
    "failure_handling": "what to do if this step fails",
    "estimated_duration": 10
  }
]

CRITICAL: Be intelligent about field selection. Don't fetch all 50+ fields when only 5-10 are needed!"""

    def _build_planning_user_prompt(self, decision: DecisionV1, selection: SelectionV1) -> str:
        """Build the user prompt with decision and selection context"""
        import json
        
        # Extract key information
        user_query = decision.original_request
        intent_category = decision.intent.category
        intent_action = decision.intent.action
        # Convert Pydantic EntityV1 objects to dicts for JSON serialization
        entities = [entity.dict() if hasattr(entity, 'dict') else entity for entity in decision.entities]
        selected_tools = [tool.tool_name for tool in selection.selected_tools]
        
        prompt = f"""Create an execution plan for the following request:

**User Query:** {user_query}

**Intent:**
- Category: {intent_category}
- Action: {intent_action}

**Extracted Entities:**
{json.dumps(entities, indent=2)}

**Selected Tools:**
{json.dumps(selected_tools, indent=2)}

**Tool Details:**
"""
        
        for tool in selection.selected_tools:
            prompt += f"\n- {tool.tool_name}: {tool.justification}\n"
        
        prompt += "\nGenerate the execution steps as a JSON array. Remember to be intelligent about field selection!"
        
        return prompt
    
    def _parse_llm_planning_response(self, response_content: str, selection: SelectionV1) -> List:
        """Parse LLM response into execution steps"""
        from ...schemas.plan_v1 import ExecutionStep
        import json
        import uuid
        
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response_content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            steps_data = json.loads(content)
            
            # Convert to ExecutionStep objects
            steps = []
            for idx, step_data in enumerate(steps_data):
                step = ExecutionStep(
                    id=f"step_{uuid.uuid4().hex[:8]}",
                    description=step_data.get("description", "Execute operation"),
                    tool=step_data.get("tool"),
                    inputs=step_data.get("inputs", {}),
                    preconditions=step_data.get("preconditions", []),
                    success_criteria=step_data.get("success_criteria", ["operation_completed"]),
                    failure_handling=step_data.get("failure_handling", "Log error and abort"),
                    estimated_duration=step_data.get("estimated_duration", 10),
                    depends_on=[],
                    execution_order=idx + 1
                )
                steps.append(step)
            
            return steps
            
        except Exception as e:
            # If LLM parsing fails, raise error - no fallback to rules!
            raise PlanningError(f"Failed to parse LLM planning response: {str(e)}\nResponse: {response_content}")
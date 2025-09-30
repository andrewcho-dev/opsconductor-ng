"""
Stage C Planner - Main Orchestrator

The main planner that coordinates all planning components to create
comprehensive, safe, executable step-by-step plans.
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ...schemas.decision_v1 import DecisionV1
from ...schemas.selection_v1 import SelectionV1
from ...schemas.plan_v1 import PlanV1, ExecutionPlan, ExecutionMetadata

from .step_generator import StepGenerator
from .dependency_resolver import DependencyResolver, DependencyError
from .safety_planner import SafetyPlanner
from .resource_planner import ResourcePlanner


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
    
    def create_plan(
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
            steps = self._generate_execution_steps(decision, selection)
            
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
            
            # Try fallback planning
            try:
                return self._create_fallback_plan(decision, selection, str(e))
            except Exception as fallback_error:
                raise PlanningError(
                    f"Planning failed: {str(e)}. Fallback also failed: {str(fallback_error)}"
                )
    
    def _generate_execution_steps(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List:
        """Generate execution steps from decision and selection"""
        try:
            # Use LLM for intelligent step generation if available
            if self.llm_client and self._should_use_llm(decision, selection):
                return self._generate_steps_with_llm(decision, selection)
            else:
                # Use rule-based step generation
                return self.step_generator.generate_steps(decision, selection)
        
        except Exception as e:
            # Fallback to basic step generation
            return self.step_generator.generate_steps(decision, selection)
    
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
    
    def _should_use_llm(self, decision: DecisionV1, selection: SelectionV1) -> bool:
        """Determine if LLM should be used for planning"""
        # Use LLM for complex scenarios
        complex_indicators = [
            len(selection.selected_tools) > 3,  # Multiple tools
            decision.risk_level.value in ["high", "critical"],  # High risk
            selection.policy.requires_approval,  # Requires approval
            len(decision.entities) > 5  # Complex entity extraction
        ]
        
        return any(complex_indicators)
    
    def _generate_steps_with_llm(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List:
        """Generate steps using LLM for intelligent planning"""
        # This would integrate with the LLM client for intelligent step generation
        # For now, fall back to rule-based generation
        self._increment_stat("llm_calls_made")
        return self.step_generator.generate_steps(decision, selection)
    
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
    
    def _create_fallback_plan(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1, 
        error_message: str
    ) -> PlanV1:
        """Create a minimal fallback plan when main planning fails"""
        self._increment_stat("fallback_plans_used")
        
        # Create a single, safe information-gathering step
        from ...schemas.plan_v1 import ExecutionStep, SafetyCheck, RollbackStep, ObservabilityConfig
        
        fallback_step = ExecutionStep(
            id="fallback_001_info_gathering",
            description="Gather basic system information (fallback plan)",
            tool="info_display",
            inputs={"info_type": "system_status", "format": "basic"},
            preconditions=["system_accessible"],
            success_criteria=["information_retrieved"],
            failure_handling="Log error and report to user",
            estimated_duration=10,
            depends_on=[],
            execution_order=1
        )
        
        safety_check = SafetyCheck(
            check="Verify system is accessible for information gathering",
            stage="before",
            failure_action="abort"
        )
        
        observability = ObservabilityConfig(
            metrics_to_collect=["execution_time"],
            logs_to_monitor=["/var/log/syslog"],
            alerts_to_set=["execution_timeout"]
        )
        
        metadata = ExecutionMetadata(
            total_estimated_time=10,
            risk_factors=["fallback", f"original_error: {error_message}"],
            approval_points=[],
            checkpoint_steps=["fallback_001_info_gathering"]
        )
        
        execution_plan = ExecutionPlan(
            steps=[fallback_step],
            safety_checks=[safety_check],
            rollback_plan=[],
            observability=observability
        )
        
        return PlanV1(
            plan=execution_plan,
            execution_metadata=metadata,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=50  # Minimal processing time for fallback
        )
    
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
            "status": "healthy",
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
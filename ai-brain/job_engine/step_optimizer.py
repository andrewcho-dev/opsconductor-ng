"""
OpsConductor AI Brain - Job Engine: Step Optimizer Module

This module optimizes workflow steps for better performance, parallel execution,
resource usage optimization, and overall workflow efficiency.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OptimizationType(Enum):
    """Types of optimizations that can be applied"""
    PARALLEL_EXECUTION = "parallel_execution"
    DEPENDENCY_ORDERING = "dependency_ordering"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    RISK_MINIMIZATION = "risk_minimization"
    TIME_OPTIMIZATION = "time_optimization"
    COST_OPTIMIZATION = "cost_optimization"

class ExecutionStrategy(Enum):
    """Execution strategies for optimized workflows"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    BATCH = "batch"
    ADAPTIVE = "adaptive"

@dataclass
class OptimizationMetrics:
    """Metrics for optimization analysis"""
    original_duration: int
    optimized_duration: int
    parallelization_factor: float
    resource_efficiency: float
    risk_score: float
    cost_reduction: float
    optimization_types: List[OptimizationType]

@dataclass
class ExecutionGroup:
    """Group of steps that can be executed together"""
    group_id: str
    step_ids: List[str]
    execution_strategy: ExecutionStrategy
    estimated_duration: int
    resource_requirements: Dict[str, Any]
    dependencies: List[str]  # Other group IDs this depends on
    risk_level: str

@dataclass
class OptimizedWorkflow:
    """Optimized workflow with execution groups"""
    workflow_id: str
    original_step_count: int
    optimized_step_count: int
    execution_groups: List[ExecutionGroup]
    execution_order: List[str]  # Group IDs in execution order
    optimization_metrics: OptimizationMetrics
    optimization_notes: List[str]
    created_at: datetime = field(default_factory=datetime.now)

class StepOptimizer:
    """Optimizes workflow steps for better performance and efficiency"""
    
    def __init__(self):
        self.optimization_rules = self._initialize_optimization_rules()
        self.resource_profiles = self._initialize_resource_profiles()
        logger.info("Initialized step optimizer")
    
    def optimize_workflow(
        self,
        workflow_steps: List[Any],  # WorkflowStep objects
        optimization_goals: List[OptimizationType] = None,
        constraints: Dict[str, Any] = None
    ) -> OptimizedWorkflow:
        """
        Optimize workflow steps based on goals and constraints
        
        Args:
            workflow_steps: List of workflow steps to optimize
            optimization_goals: List of optimization types to apply
            constraints: Constraints for optimization (resource limits, time limits, etc.)
            
        Returns:
            OptimizedWorkflow: Optimized workflow with execution groups
        """
        try:
            logger.info(f"Optimizing workflow with {len(workflow_steps)} steps")
            
            if not optimization_goals:
                optimization_goals = [
                    OptimizationType.PARALLEL_EXECUTION,
                    OptimizationType.DEPENDENCY_ORDERING,
                    OptimizationType.TIME_OPTIMIZATION
                ]
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(workflow_steps)
            
            # Apply optimizations
            optimized_groups = []
            optimization_notes = []
            
            for goal in optimization_goals:
                if goal == OptimizationType.PARALLEL_EXECUTION:
                    groups, notes = self._optimize_for_parallelization(workflow_steps, dependency_graph)
                    optimized_groups.extend(groups)
                    optimization_notes.extend(notes)
                
                elif goal == OptimizationType.DEPENDENCY_ORDERING:
                    groups, notes = self._optimize_dependency_order(workflow_steps, dependency_graph)
                    optimized_groups.extend(groups)
                    optimization_notes.extend(notes)
                
                elif goal == OptimizationType.RESOURCE_OPTIMIZATION:
                    groups, notes = self._optimize_resource_usage(workflow_steps, constraints)
                    optimized_groups.extend(groups)
                    optimization_notes.extend(notes)
                
                elif goal == OptimizationType.RISK_MINIMIZATION:
                    groups, notes = self._optimize_risk_management(workflow_steps)
                    optimized_groups.extend(groups)
                    optimization_notes.extend(notes)
                
                elif goal == OptimizationType.TIME_OPTIMIZATION:
                    groups, notes = self._optimize_execution_time(workflow_steps, dependency_graph)
                    optimized_groups.extend(groups)
                    optimization_notes.extend(notes)
            
            # Merge and deduplicate groups
            final_groups = self._merge_execution_groups(optimized_groups)
            
            # Calculate execution order
            execution_order = self._calculate_execution_order(final_groups)
            
            # Calculate optimization metrics
            metrics = self._calculate_optimization_metrics(
                workflow_steps, final_groups, optimization_goals
            )
            
            optimized_workflow = OptimizedWorkflow(
                workflow_id=f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                original_step_count=len(workflow_steps),
                optimized_step_count=sum(len(group.step_ids) for group in final_groups),
                execution_groups=final_groups,
                execution_order=execution_order,
                optimization_metrics=metrics,
                optimization_notes=optimization_notes
            )
            
            logger.info(f"Optimization complete: {len(final_groups)} execution groups, "
                       f"{metrics.parallelization_factor:.2f}x parallelization factor")
            
            return optimized_workflow
            
        except Exception as e:
            logger.error(f"Error optimizing workflow: {str(e)}")
            raise
    
    def _build_dependency_graph(self, workflow_steps: List[Any]) -> nx.DiGraph:
        """Build a directed graph of step dependencies"""
        
        graph = nx.DiGraph()
        
        # Add all steps as nodes
        for step in workflow_steps:
            graph.add_node(step.step_id, step=step)
        
        # Add dependency edges
        for step in workflow_steps:
            for dependency in step.dependencies:
                if dependency in [s.step_id for s in workflow_steps]:
                    graph.add_edge(dependency, step.step_id)
            
            # Add prerequisite edges (softer dependencies)
            for prerequisite in step.prerequisites:
                # Find steps that might satisfy this prerequisite
                for other_step in workflow_steps:
                    if prerequisite.lower() in other_step.name.lower() or \
                       prerequisite.lower() in other_step.description.lower():
                        graph.add_edge(other_step.step_id, step.step_id)
        
        return graph
    
    def _optimize_for_parallelization(
        self,
        workflow_steps: List[Any],
        dependency_graph: nx.DiGraph
    ) -> Tuple[List[ExecutionGroup], List[str]]:
        """Identify steps that can be executed in parallel"""
        
        groups = []
        notes = []
        
        # Find independent steps (no dependencies)
        independent_steps = []
        for step in workflow_steps:
            if not list(dependency_graph.predecessors(step.step_id)):
                independent_steps.append(step.step_id)
        
        if len(independent_steps) > 1:
            # Create parallel execution group for independent steps
            group = ExecutionGroup(
                group_id=f"parallel_independent_{len(groups)}",
                step_ids=independent_steps,
                execution_strategy=ExecutionStrategy.PARALLEL,
                estimated_duration=max(
                    next(s.timeout for s in workflow_steps if s.step_id == step_id)
                    for step_id in independent_steps
                ),
                resource_requirements={"cpu": len(independent_steps), "memory": "medium"},
                dependencies=[],
                risk_level=self._calculate_group_risk_level(independent_steps, workflow_steps)
            )
            groups.append(group)
            notes.append(f"Created parallel group with {len(independent_steps)} independent steps")
        
        # Find steps that can run in parallel after dependencies are satisfied
        levels = list(nx.topological_generations(dependency_graph))
        for i, level in enumerate(levels):
            if len(level) > 1:
                group = ExecutionGroup(
                    group_id=f"parallel_level_{i}",
                    step_ids=list(level),
                    execution_strategy=ExecutionStrategy.PARALLEL,
                    estimated_duration=max(
                        next(s.timeout for s in workflow_steps if s.step_id == step_id)
                        for step_id in level
                    ),
                    resource_requirements={"cpu": len(level), "memory": "medium"},
                    dependencies=[f"parallel_level_{j}" for j in range(i)],
                    risk_level=self._calculate_group_risk_level(level, workflow_steps)
                )
                groups.append(group)
                notes.append(f"Created parallel group for dependency level {i} with {len(level)} steps")
        
        return groups, notes
    
    def _optimize_dependency_order(
        self,
        workflow_steps: List[Any],
        dependency_graph: nx.DiGraph
    ) -> Tuple[List[ExecutionGroup], List[str]]:
        """Optimize step order based on dependencies"""
        
        groups = []
        notes = []
        
        try:
            # Get topological order
            topo_order = list(nx.topological_sort(dependency_graph))
            
            # Group sequential steps
            current_group = []
            for step_id in topo_order:
                step = next(s for s in workflow_steps if s.step_id == step_id)
                
                # Start new group if current step has high risk or requires approval
                if (step.risk_level in ['high', 'critical'] or step.requires_approval) and current_group:
                    group = ExecutionGroup(
                        group_id=f"sequential_{len(groups)}",
                        step_ids=current_group,
                        execution_strategy=ExecutionStrategy.SEQUENTIAL,
                        estimated_duration=sum(
                            next(s.timeout for s in workflow_steps if s.step_id == sid)
                            for sid in current_group
                        ),
                        resource_requirements={"cpu": 1, "memory": "low"},
                        dependencies=[],
                        risk_level=self._calculate_group_risk_level(current_group, workflow_steps)
                    )
                    groups.append(group)
                    current_group = []
                
                current_group.append(step_id)
            
            # Add remaining steps
            if current_group:
                group = ExecutionGroup(
                    group_id=f"sequential_{len(groups)}",
                    step_ids=current_group,
                    execution_strategy=ExecutionStrategy.SEQUENTIAL,
                    estimated_duration=sum(
                        next(s.timeout for s in workflow_steps if s.step_id == sid)
                        for sid in current_group
                    ),
                    resource_requirements={"cpu": 1, "memory": "low"},
                    dependencies=[],
                    risk_level=self._calculate_group_risk_level(current_group, workflow_steps)
                )
                groups.append(group)
            
            notes.append(f"Optimized dependency order with {len(groups)} sequential groups")
            
        except nx.NetworkXError as e:
            logger.warning(f"Dependency cycle detected: {str(e)}")
            notes.append("Warning: Dependency cycle detected, using original order")
        
        return groups, notes
    
    def _optimize_resource_usage(
        self,
        workflow_steps: List[Any],
        constraints: Dict[str, Any] = None
    ) -> Tuple[List[ExecutionGroup], List[str]]:
        """Optimize workflow for resource usage"""
        
        groups = []
        notes = []
        
        if not constraints:
            constraints = {"max_parallel": 4, "max_memory": "high", "max_cpu": 8}
        
        # Group steps by resource requirements
        low_resource_steps = []
        medium_resource_steps = []
        high_resource_steps = []
        
        for step in workflow_steps:
            resource_level = self._estimate_step_resource_usage(step)
            if resource_level == "low":
                low_resource_steps.append(step.step_id)
            elif resource_level == "medium":
                medium_resource_steps.append(step.step_id)
            else:
                high_resource_steps.append(step.step_id)
        
        # Create resource-optimized groups
        if low_resource_steps:
            # Low resource steps can run in larger parallel groups
            max_parallel = min(constraints.get("max_parallel", 4), len(low_resource_steps))
            for i in range(0, len(low_resource_steps), max_parallel):
                batch = low_resource_steps[i:i + max_parallel]
                group = ExecutionGroup(
                    group_id=f"low_resource_batch_{i // max_parallel}",
                    step_ids=batch,
                    execution_strategy=ExecutionStrategy.PARALLEL,
                    estimated_duration=max(
                        next(s.timeout for s in workflow_steps if s.step_id == step_id)
                        for step_id in batch
                    ),
                    resource_requirements={"cpu": len(batch), "memory": "low"},
                    dependencies=[],
                    risk_level=self._calculate_group_risk_level(batch, workflow_steps)
                )
                groups.append(group)
        
        # Medium resource steps run in smaller groups
        if medium_resource_steps:
            max_parallel = min(2, len(medium_resource_steps))
            for i in range(0, len(medium_resource_steps), max_parallel):
                batch = medium_resource_steps[i:i + max_parallel]
                group = ExecutionGroup(
                    group_id=f"medium_resource_batch_{i // max_parallel}",
                    step_ids=batch,
                    execution_strategy=ExecutionStrategy.PARALLEL if len(batch) > 1 else ExecutionStrategy.SEQUENTIAL,
                    estimated_duration=max(
                        next(s.timeout for s in workflow_steps if s.step_id == step_id)
                        for step_id in batch
                    ),
                    resource_requirements={"cpu": len(batch) * 2, "memory": "medium"},
                    dependencies=[],
                    risk_level=self._calculate_group_risk_level(batch, workflow_steps)
                )
                groups.append(group)
        
        # High resource steps run sequentially
        for step_id in high_resource_steps:
            group = ExecutionGroup(
                group_id=f"high_resource_{step_id}",
                step_ids=[step_id],
                execution_strategy=ExecutionStrategy.SEQUENTIAL,
                estimated_duration=next(s.timeout for s in workflow_steps if s.step_id == step_id),
                resource_requirements={"cpu": 4, "memory": "high"},
                dependencies=[],
                risk_level=next(s.risk_level for s in workflow_steps if s.step_id == step_id)
            )
            groups.append(group)
        
        notes.append(f"Resource optimization: {len(low_resource_steps)} low, "
                    f"{len(medium_resource_steps)} medium, {len(high_resource_steps)} high resource steps")
        
        return groups, notes
    
    def _optimize_risk_management(
        self,
        workflow_steps: List[Any]
    ) -> Tuple[List[ExecutionGroup], List[str]]:
        """Optimize workflow for risk management"""
        
        groups = []
        notes = []
        
        # Separate steps by risk level
        low_risk_steps = []
        medium_risk_steps = []
        high_risk_steps = []
        critical_risk_steps = []
        
        for step in workflow_steps:
            if step.risk_level == "low":
                low_risk_steps.append(step.step_id)
            elif step.risk_level == "medium":
                medium_risk_steps.append(step.step_id)
            elif step.risk_level == "high":
                high_risk_steps.append(step.step_id)
            else:
                critical_risk_steps.append(step.step_id)
        
        # Low risk steps can run in parallel
        if low_risk_steps:
            group = ExecutionGroup(
                group_id="low_risk_parallel",
                step_ids=low_risk_steps,
                execution_strategy=ExecutionStrategy.PARALLEL,
                estimated_duration=max(
                    next(s.timeout for s in workflow_steps if s.step_id == step_id)
                    for step_id in low_risk_steps
                ),
                resource_requirements={"cpu": len(low_risk_steps), "memory": "medium"},
                dependencies=[],
                risk_level="low"
            )
            groups.append(group)
        
        # Medium risk steps run in smaller batches
        if medium_risk_steps:
            batch_size = 2
            for i in range(0, len(medium_risk_steps), batch_size):
                batch = medium_risk_steps[i:i + batch_size]
                group = ExecutionGroup(
                    group_id=f"medium_risk_batch_{i // batch_size}",
                    step_ids=batch,
                    execution_strategy=ExecutionStrategy.SEQUENTIAL,
                    estimated_duration=sum(
                        next(s.timeout for s in workflow_steps if s.step_id == step_id)
                        for step_id in batch
                    ),
                    resource_requirements={"cpu": 1, "memory": "medium"},
                    dependencies=["low_risk_parallel"] if low_risk_steps else [],
                    risk_level="medium"
                )
                groups.append(group)
        
        # High and critical risk steps run individually with checkpoints
        for step_id in high_risk_steps + critical_risk_steps:
            step = next(s for s in workflow_steps if s.step_id == step_id)
            group = ExecutionGroup(
                group_id=f"high_risk_{step_id}",
                step_ids=[step_id],
                execution_strategy=ExecutionStrategy.SEQUENTIAL,
                estimated_duration=step.timeout,
                resource_requirements={"cpu": 1, "memory": "low"},
                dependencies=[],
                risk_level=step.risk_level
            )
            groups.append(group)
        
        notes.append(f"Risk optimization: {len(low_risk_steps)} low, {len(medium_risk_steps)} medium, "
                    f"{len(high_risk_steps)} high, {len(critical_risk_steps)} critical risk steps")
        
        return groups, notes
    
    def _optimize_execution_time(
        self,
        workflow_steps: List[Any],
        dependency_graph: nx.DiGraph
    ) -> Tuple[List[ExecutionGroup], List[str]]:
        """Optimize workflow for minimum execution time"""
        
        groups = []
        notes = []
        
        # Calculate critical path
        critical_path = self._find_critical_path(workflow_steps, dependency_graph)
        critical_step_ids = set(critical_path)
        
        # Prioritize critical path steps
        critical_groups = []
        non_critical_groups = []
        
        # Group critical path steps
        current_critical = []
        for step_id in critical_path:
            step = next(s for s in workflow_steps if s.step_id == step_id)
            current_critical.append(step_id)
            
            # Create group at checkpoints (high risk or long duration)
            if step.risk_level in ['high', 'critical'] or step.timeout > 600:  # 10 minutes
                if current_critical:
                    group = ExecutionGroup(
                        group_id=f"critical_path_{len(critical_groups)}",
                        step_ids=current_critical,
                        execution_strategy=ExecutionStrategy.SEQUENTIAL,
                        estimated_duration=sum(
                            next(s.timeout for s in workflow_steps if s.step_id == sid)
                            for sid in current_critical
                        ),
                        resource_requirements={"cpu": 2, "memory": "medium"},
                        dependencies=[],
                        risk_level=self._calculate_group_risk_level(current_critical, workflow_steps)
                    )
                    critical_groups.append(group)
                    current_critical = []
        
        # Add remaining critical steps
        if current_critical:
            group = ExecutionGroup(
                group_id=f"critical_path_{len(critical_groups)}",
                step_ids=current_critical,
                execution_strategy=ExecutionStrategy.SEQUENTIAL,
                estimated_duration=sum(
                    next(s.timeout for s in workflow_steps if s.step_id == sid)
                    for sid in current_critical
                ),
                resource_requirements={"cpu": 2, "memory": "medium"},
                dependencies=[],
                risk_level=self._calculate_group_risk_level(current_critical, workflow_steps)
            )
            critical_groups.append(group)
        
        # Group non-critical steps for parallel execution
        non_critical_steps = [s.step_id for s in workflow_steps if s.step_id not in critical_step_ids]
        if non_critical_steps:
            group = ExecutionGroup(
                group_id="non_critical_parallel",
                step_ids=non_critical_steps,
                execution_strategy=ExecutionStrategy.PARALLEL,
                estimated_duration=max(
                    next(s.timeout for s in workflow_steps if s.step_id == step_id)
                    for step_id in non_critical_steps
                ),
                resource_requirements={"cpu": len(non_critical_steps), "memory": "medium"},
                dependencies=[],
                risk_level=self._calculate_group_risk_level(non_critical_steps, workflow_steps)
            )
            non_critical_groups.append(group)
        
        groups.extend(critical_groups)
        groups.extend(non_critical_groups)
        
        notes.append(f"Time optimization: {len(critical_path)} critical path steps, "
                    f"{len(non_critical_steps)} non-critical steps")
        
        return groups, notes
    
    def _find_critical_path(self, workflow_steps: List[Any], dependency_graph: nx.DiGraph) -> List[str]:
        """Find the critical path (longest path) through the workflow"""
        
        # Add weights (durations) to edges
        weighted_graph = dependency_graph.copy()
        for node in weighted_graph.nodes():
            step = next(s for s in workflow_steps if s.step_id == node)
            weighted_graph.nodes[node]['weight'] = step.timeout
        
        # Find longest path (critical path)
        try:
            # Convert to find longest path by negating weights
            for node in weighted_graph.nodes():
                weighted_graph.nodes[node]['weight'] = -weighted_graph.nodes[node]['weight']
            
            # Find shortest path in negated graph (which is longest in original)
            if weighted_graph.nodes():
                source = [n for n in weighted_graph.nodes() if weighted_graph.in_degree(n) == 0]
                sink = [n for n in weighted_graph.nodes() if weighted_graph.out_degree(n) == 0]
                
                if source and sink:
                    try:
                        path = nx.shortest_path(weighted_graph, source[0], sink[0])
                        return path
                    except nx.NetworkXNoPath:
                        pass
            
            # Fallback: return topological order
            return list(nx.topological_sort(dependency_graph))
            
        except Exception as e:
            logger.warning(f"Error finding critical path: {str(e)}")
            return [s.step_id for s in workflow_steps]
    
    def _merge_execution_groups(self, groups: List[ExecutionGroup]) -> List[ExecutionGroup]:
        """Merge and deduplicate execution groups"""
        
        # Simple deduplication by step IDs
        seen_steps = set()
        merged_groups = []
        
        for group in groups:
            # Check if any steps are already in other groups
            if not any(step_id in seen_steps for step_id in group.step_ids):
                merged_groups.append(group)
                seen_steps.update(group.step_ids)
        
        return merged_groups
    
    def _calculate_execution_order(self, groups: List[ExecutionGroup]) -> List[str]:
        """Calculate optimal execution order for groups"""
        
        # Build dependency graph for groups
        group_graph = nx.DiGraph()
        
        for group in groups:
            group_graph.add_node(group.group_id)
        
        for group in groups:
            for dep in group.dependencies:
                if dep in [g.group_id for g in groups]:
                    group_graph.add_edge(dep, group.group_id)
        
        # Return topological order
        try:
            return list(nx.topological_sort(group_graph))
        except nx.NetworkXError:
            # Fallback to original order
            return [group.group_id for group in groups]
    
    def _calculate_optimization_metrics(
        self,
        original_steps: List[Any],
        optimized_groups: List[ExecutionGroup],
        optimization_goals: List[OptimizationType]
    ) -> OptimizationMetrics:
        """Calculate metrics for the optimization"""
        
        # Original duration (sequential execution)
        original_duration = sum(step.timeout for step in original_steps)
        
        # Optimized duration (considering parallelization)
        optimized_duration = 0
        for group in optimized_groups:
            if group.execution_strategy == ExecutionStrategy.PARALLEL:
                optimized_duration += group.estimated_duration
            else:
                optimized_duration += group.estimated_duration
        
        # Calculate metrics
        parallelization_factor = original_duration / max(optimized_duration, 1)
        
        # Resource efficiency (steps per group)
        resource_efficiency = len(original_steps) / max(len(optimized_groups), 1)
        
        # Risk score (average risk level)
        risk_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        avg_risk = sum(risk_scores.get(step.risk_level, 2) for step in original_steps) / len(original_steps)
        
        # Cost reduction (simplified)
        cost_reduction = (original_duration - optimized_duration) / original_duration * 100
        
        return OptimizationMetrics(
            original_duration=original_duration,
            optimized_duration=optimized_duration,
            parallelization_factor=parallelization_factor,
            resource_efficiency=resource_efficiency,
            risk_score=avg_risk,
            cost_reduction=cost_reduction,
            optimization_types=optimization_goals
        )
    
    def _calculate_group_risk_level(self, step_ids: List[str], workflow_steps: List[Any]) -> str:
        """Calculate risk level for a group of steps"""
        
        risk_levels = []
        for step_id in step_ids:
            step = next(s for s in workflow_steps if s.step_id == step_id)
            risk_levels.append(step.risk_level)
        
        # Return highest risk level in group
        if "critical" in risk_levels:
            return "critical"
        elif "high" in risk_levels:
            return "high"
        elif "medium" in risk_levels:
            return "medium"
        else:
            return "low"
    
    def _estimate_step_resource_usage(self, step: Any) -> str:
        """Estimate resource usage for a step"""
        
        # Simple heuristic based on step type and timeout
        if step.step_type.value in ["script", "parallel"]:
            return "high"
        elif step.timeout > 300:  # 5 minutes
            return "medium"
        else:
            return "low"
    
    def _initialize_optimization_rules(self) -> Dict[str, Any]:
        """Initialize optimization rules"""
        
        return {
            "max_parallel_steps": 8,
            "max_group_duration": 3600,  # 1 hour
            "risk_isolation": True,
            "resource_balancing": True,
            "dependency_respect": True
        }
    
    def _initialize_resource_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize resource profiles for different step types"""
        
        return {
            "command": {"cpu": 1, "memory": "low", "io": "low"},
            "script": {"cpu": 2, "memory": "medium", "io": "medium"},
            "validation": {"cpu": 1, "memory": "low", "io": "low"},
            "parallel": {"cpu": 4, "memory": "high", "io": "high"},
            "error_handler": {"cpu": 1, "memory": "low", "io": "low"}
        }
    
    def export_optimization(self, optimized_workflow: OptimizedWorkflow) -> Dict[str, Any]:
        """Export optimized workflow to dictionary format"""
        
        return {
            "workflow_id": optimized_workflow.workflow_id,
            "original_step_count": optimized_workflow.original_step_count,
            "optimized_step_count": optimized_workflow.optimized_step_count,
            "execution_groups": [
                {
                    "group_id": group.group_id,
                    "step_ids": group.step_ids,
                    "execution_strategy": group.execution_strategy.value,
                    "estimated_duration": group.estimated_duration,
                    "resource_requirements": group.resource_requirements,
                    "dependencies": group.dependencies,
                    "risk_level": group.risk_level
                }
                for group in optimized_workflow.execution_groups
            ],
            "execution_order": optimized_workflow.execution_order,
            "optimization_metrics": {
                "original_duration": optimized_workflow.optimization_metrics.original_duration,
                "optimized_duration": optimized_workflow.optimization_metrics.optimized_duration,
                "parallelization_factor": optimized_workflow.optimization_metrics.parallelization_factor,
                "resource_efficiency": optimized_workflow.optimization_metrics.resource_efficiency,
                "risk_score": optimized_workflow.optimization_metrics.risk_score,
                "cost_reduction": optimized_workflow.optimization_metrics.cost_reduction,
                "optimization_types": [ot.value for ot in optimized_workflow.optimization_metrics.optimization_types]
            },
            "optimization_notes": optimized_workflow.optimization_notes,
            "created_at": optimized_workflow.created_at.isoformat()
        }

# Global instance
step_optimizer = StepOptimizer()

def optimize_workflow_steps(
    workflow_steps: List[Any],
    optimization_goals: List[OptimizationType] = None,
    constraints: Dict[str, Any] = None
) -> OptimizedWorkflow:
    """
    High-level function to optimize workflow steps
    
    Args:
        workflow_steps: List of workflow steps to optimize
        optimization_goals: List of optimization types to apply
        constraints: Constraints for optimization
        
    Returns:
        OptimizedWorkflow: Optimized workflow with execution groups
    """
    return step_optimizer.optimize_workflow(workflow_steps, optimization_goals, constraints)
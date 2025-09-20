"""
OpsConductor AI Brain - Job Engine

The Job Engine is responsible for intelligent job creation and workflow management.
It transforms user intents and requirements into executable automation workflows
with optimized execution plans.

Components:
- WorkflowGenerator: Generates executable workflows from requirements
- TargetResolver: Intelligently resolves target systems
- StepOptimizer: Optimizes workflow steps for performance
- ExecutionPlanner: Plans execution strategies and schedules

Usage:
    from ai_brain.job_engine import (
        generate_workflow,
        resolve_targets,
        optimize_workflow_steps,
        create_execution_plan
    )
"""

from .workflow_generator import (
    WorkflowGenerator,
    WorkflowType,
    StepType,
    ExecutionMode,
    WorkflowStep,
    WorkflowTemplate,
    GeneratedWorkflow,
    workflow_generator,
    generate_workflow
)

from .target_resolver import (
    TargetResolver,
    TargetType,
    ConnectionStatus,
    TargetPlatform,
    TargetCredential,
    ResolvedTarget,
    TargetGroup,
    TargetResolutionResult,
    target_resolver,
    resolve_targets
)

from .step_optimizer import (
    StepOptimizer,
    OptimizationType,
    ExecutionStrategy,
    OptimizationMetrics,
    ExecutionGroup,
    OptimizedWorkflow,
    step_optimizer,
    optimize_workflow_steps
)

from .execution_planner import (
    ExecutionPlanner,
    ExecutionPhase,
    ExecutionStatus,
    ResourceType,
    ResourceAllocation,
    ExecutionCheckpoint,
    ExecutionSchedule,
    ExecutionPlan,
    execution_planner,
    create_execution_plan
)

# Global instances for easy access
__all__ = [
    # Classes
    'WorkflowGenerator',
    'TargetResolver', 
    'StepOptimizer',
    'ExecutionPlanner',
    
    # Enums
    'WorkflowType',
    'StepType',
    'ExecutionMode',
    'TargetType',
    'ConnectionStatus',
    'TargetPlatform',
    'OptimizationType',
    'ExecutionPhase',
    'ExecutionStatus',
    'ResourceType',
    
    # Data Classes
    'WorkflowStep',
    'WorkflowTemplate',
    'GeneratedWorkflow',
    'TargetCredential',
    'ResolvedTarget',
    'TargetGroup',
    'TargetResolutionResult',
    'OptimizationMetrics',
    'ExecutionGroup',
    'OptimizedWorkflow',
    'ResourceAllocation',
    'ExecutionCheckpoint',
    'ExecutionSchedule',
    'ExecutionPlan',
    
    # Global instances
    'workflow_generator',
    'target_resolver',
    'step_optimizer',
    'execution_planner',
    
    # High-level functions
    'generate_workflow',
    'resolve_targets',
    'optimize_workflow_steps',
    'create_execution_plan'
]

# Module metadata
__version__ = "1.0.0"
__author__ = "OpsConductor AI Brain"
__description__ = "Intelligent job creation and workflow management engine"
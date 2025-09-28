"""
OUIOE Phase 5: Multi-Step Intelligent Workflows

Revolutionary workflow orchestration system providing:
- Intelligent workflow generation based on context
- Adaptive execution with error handling and recovery
- Multi-service coordination across OpsConductor services
- Dynamic workflow modification based on results
- Real-time workflow monitoring and visualization

This module transforms complex operations into intelligent,
self-adapting workflows that learn and optimize over time.
"""

from .intelligent_workflow_generator import (
    IntelligentWorkflowGenerator, WorkflowTemplate, WorkflowStep, 
    WorkflowDependency, WorkflowContext, WorkflowType, StepType,
    WorkflowPriority, WorkflowStatus
)
from .adaptive_execution_engine import (
    AdaptiveExecutionEngine, ExecutionContext, ExecutionResult,
    ExecutionStatus, AdaptationTrigger, AdaptationStrategy,
    ExecutionMonitor, ExecutionRecovery
)
from .workflow_orchestrator import (
    WorkflowOrchestrator, OrchestrationContext, OrchestrationResult,
    ServiceCoordination, CrossServiceWorkflow,
    OrchestrationStatus, ServiceIntegration
)
from .workflow_models import (
    IntelligentWorkflow, WorkflowNode, WorkflowEdge, WorkflowGraph,
    WorkflowMetrics, WorkflowAnalytics, WorkflowOptimization,
    WorkflowLearning, WorkflowAdaptation
)

__all__ = [
    # Workflow Generator
    'IntelligentWorkflowGenerator',
    'WorkflowTemplate',
    'WorkflowStep',
    'WorkflowDependency',
    'WorkflowContext',
    'WorkflowType',
    'StepType',
    'WorkflowPriority',
    'WorkflowStatus',
    
    # Adaptive Execution
    'AdaptiveExecutionEngine',
    'ExecutionContext',
    'ExecutionResult',
    'ExecutionStatus',
    'AdaptationTrigger',
    'AdaptationStrategy',
    'ExecutionMonitor',
    'ExecutionRecovery',
    
    # Workflow Orchestrator
    'WorkflowOrchestrator',
    'OrchestrationContext',
    'OrchestrationResult',
    'ServiceCoordination',
    'CrossServiceWorkflow',
    'OrchestrationStatus',
    'ServiceIntegration',
    
    # Workflow Models
    'IntelligentWorkflow',
    'WorkflowNode',
    'WorkflowEdge',
    'WorkflowGraph',
    'WorkflowMetrics',
    'WorkflowAnalytics',
    'WorkflowOptimization',
    'WorkflowLearning',
    'WorkflowAdaptation'
]

__version__ = "5.0.0"
__phase__ = "Phase 5: Multi-Step Intelligent Workflows"
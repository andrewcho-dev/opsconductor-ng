"""
OUIOE Phase 5: Workflow Data Models

Comprehensive data models for intelligent workflow management,
providing structured representations for workflow generation,
execution, monitoring, and optimization.
"""

from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import uuid


class WorkflowType(str, Enum):
    """Types of intelligent workflows"""
    SIMPLE = "simple"
    COMPLEX = "complex"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    ADAPTIVE = "adaptive"
    COLLABORATIVE = "collaborative"


class StepType(str, Enum):
    """Types of workflow steps"""
    ACTION = "action"
    DECISION = "decision"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    RECOVERY = "recovery"
    OPTIMIZATION = "optimization"


class WorkflowPriority(str, Enum):
    """Workflow execution priorities"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ADAPTING = "adapting"
    RECOVERING = "recovering"


class ExecutionStatus(str, Enum):
    """Step execution status"""
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    ADAPTED = "adapted"


class AdaptationTrigger(str, Enum):
    """Triggers for workflow adaptation"""
    FAILURE = "failure"
    PERFORMANCE = "performance"
    RESOURCE_CONSTRAINT = "resource_constraint"
    CONTEXT_CHANGE = "context_change"
    USER_REQUEST = "user_request"
    OPTIMIZATION = "optimization"
    LEARNING = "learning"


class AdaptationStrategy(str, Enum):
    """Strategies for workflow adaptation"""
    RETRY = "retry"
    SKIP = "skip"
    ALTERNATIVE_PATH = "alternative_path"
    RESOURCE_REALLOCATION = "resource_reallocation"
    STEP_MODIFICATION = "step_modification"
    WORKFLOW_RESTRUCTURE = "workflow_restructure"
    ROLLBACK = "rollback"
    ESCALATION = "escalation"


@dataclass
class WorkflowContext:
    """Context information for workflow generation and execution"""
    user_id: str
    session_id: str
    request_id: str
    primary_intent: str
    system_context: Dict[str, Any]
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    safety_constraints: List[str] = field(default_factory=list)
    available_services: List[str] = field(default_factory=list)
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    time_constraints: Optional[timedelta] = None
    quality_requirements: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDependency:
    """Dependency between workflow steps"""
    from_step: str
    to_step: str
    dependency_type: str = "completion"  # completion, data, resource, condition
    condition: Optional[str] = None
    data_mapping: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[timedelta] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    name: str
    step_type: StepType
    service: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[timedelta] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    validation_rules: List[str] = field(default_factory=list)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    adaptation_points: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowTemplate:
    """Template for workflow generation"""
    template_id: str
    name: str
    description: str
    workflow_type: WorkflowType
    applicable_intents: List[str]
    required_services: List[str]
    steps: List[WorkflowStep]
    dependencies: List[WorkflowDependency]
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    optimization_hints: List[str] = field(default_factory=list)
    learning_points: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowNode(BaseModel):
    """Node in workflow graph representation"""
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step: WorkflowStep
    position: Dict[str, float] = Field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.WAITING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[timedelta] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    adaptation_history: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    """Edge in workflow graph representation"""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_node: str
    to_node: str
    dependency: WorkflowDependency
    condition_met: bool = False
    data_transferred: Dict[str, Any] = Field(default_factory=dict)
    execution_count: int = 0
    last_execution: Optional[datetime] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class WorkflowGraph(BaseModel):
    """Graph representation of workflow"""
    graph_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    edges: Dict[str, WorkflowEdge] = Field(default_factory=dict)
    entry_points: List[str] = Field(default_factory=list)
    exit_points: List[str] = Field(default_factory=list)
    critical_path: List[str] = Field(default_factory=list)
    parallel_branches: List[List[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowMetrics(BaseModel):
    """Metrics for workflow execution"""
    workflow_id: str
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    retried_steps: int = 0
    adapted_steps: int = 0
    total_execution_time: Optional[timedelta] = None
    average_step_time: Optional[timedelta] = None
    success_rate: float = 0.0
    adaptation_rate: float = 0.0
    resource_utilization: Dict[str, float] = Field(default_factory=dict)
    performance_score: float = 0.0
    quality_score: float = 0.0
    efficiency_score: float = 0.0


class WorkflowAnalytics(BaseModel):
    """Analytics for workflow performance"""
    workflow_id: str
    execution_patterns: Dict[str, Any] = Field(default_factory=dict)
    bottlenecks: List[str] = Field(default_factory=list)
    optimization_opportunities: List[str] = Field(default_factory=list)
    failure_patterns: Dict[str, Any] = Field(default_factory=dict)
    adaptation_patterns: Dict[str, Any] = Field(default_factory=dict)
    resource_usage_patterns: Dict[str, Any] = Field(default_factory=dict)
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class WorkflowOptimization(BaseModel):
    """Optimization suggestions for workflow"""
    workflow_id: str
    optimization_type: str
    current_performance: Dict[str, float]
    target_performance: Dict[str, float]
    optimization_steps: List[str]
    estimated_improvement: Dict[str, float]
    implementation_cost: Dict[str, float]
    risk_assessment: Dict[str, float]
    priority_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowLearning(BaseModel):
    """Learning data from workflow execution"""
    workflow_id: str
    execution_id: str
    learned_patterns: Dict[str, Any] = Field(default_factory=dict)
    successful_adaptations: List[Dict[str, Any]] = Field(default_factory=list)
    failed_adaptations: List[Dict[str, Any]] = Field(default_factory=list)
    performance_insights: Dict[str, Any] = Field(default_factory=dict)
    optimization_insights: Dict[str, Any] = Field(default_factory=dict)
    context_correlations: Dict[str, Any] = Field(default_factory=dict)
    improvement_suggestions: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0


class WorkflowAdaptation(BaseModel):
    """Adaptation applied to workflow"""
    adaptation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    trigger: AdaptationTrigger
    strategy: AdaptationStrategy
    target_step: str
    original_configuration: Dict[str, Any]
    adapted_configuration: Dict[str, Any]
    adaptation_reason: str
    adaptation_time: datetime = Field(default_factory=datetime.now)
    success: bool = False
    impact_metrics: Dict[str, Any] = Field(default_factory=dict)
    learning_value: float = 0.0


class IntelligentWorkflow(BaseModel):
    """Complete intelligent workflow representation"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    workflow_type: WorkflowType
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    # Core workflow structure
    context: WorkflowContext
    template: Optional[WorkflowTemplate] = None
    graph: WorkflowGraph
    
    # Execution tracking
    created_time: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    last_update: datetime = Field(default_factory=datetime.now)
    
    # Performance and analytics
    metrics: WorkflowMetrics
    analytics: Optional[WorkflowAnalytics] = None
    optimizations: List[WorkflowOptimization] = Field(default_factory=list)
    adaptations: List[WorkflowAdaptation] = Field(default_factory=list)
    learning: Optional[WorkflowLearning] = None
    
    # Configuration
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update_status(self, new_status: WorkflowStatus):
        """Update workflow status with timestamp"""
        self.status = new_status
        self.last_update = datetime.now()
        
        if new_status == WorkflowStatus.RUNNING and not self.start_time:
            self.start_time = datetime.now()
        elif new_status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            self.end_time = datetime.now()
    
    def add_adaptation(self, adaptation: WorkflowAdaptation):
        """Add adaptation to workflow history"""
        self.adaptations.append(adaptation)
        self.last_update = datetime.now()
    
    def get_execution_time(self) -> Optional[timedelta]:
        """Get total execution time"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return datetime.now() - self.start_time
        return None
    
    def get_progress_percentage(self) -> float:
        """Get workflow progress as percentage"""
        if self.metrics.total_steps == 0:
            return 0.0
        return (self.metrics.completed_steps / self.metrics.total_steps) * 100.0
    
    def is_completed(self) -> bool:
        """Check if workflow is completed"""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
    
    def needs_adaptation(self) -> bool:
        """Check if workflow needs adaptation"""
        return (
            self.status == WorkflowStatus.RUNNING and
            (self.metrics.failed_steps > 0 or self.metrics.adaptation_rate > 0.1)
        )


# Execution context and results
@dataclass
class ExecutionContext:
    """Context for workflow execution"""
    workflow: IntelligentWorkflow
    current_step: Optional[str] = None
    execution_environment: Dict[str, Any] = field(default_factory=dict)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    service_clients: Dict[str, Any] = field(default_factory=dict)
    monitoring_data: Dict[str, Any] = field(default_factory=dict)
    adaptation_history: List[WorkflowAdaptation] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Result of workflow or step execution"""
    execution_id: str
    workflow_id: str
    step_id: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: Optional[timedelta] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    adaptation_applied: Optional[WorkflowAdaptation] = None
    next_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Service coordination models
@dataclass
class ServiceCoordination:
    """Coordination between services in workflow"""
    coordination_id: str
    involved_services: List[str]
    coordination_type: str  # sequential, parallel, conditional, synchronized
    data_flow: Dict[str, List[str]]  # service -> list of target services
    synchronization_points: List[str]
    timeout_policy: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossServiceWorkflow:
    """Workflow spanning multiple services"""
    workflow_id: str
    service_workflows: Dict[str, IntelligentWorkflow]  # service -> workflow
    coordination: ServiceCoordination
    global_context: Dict[str, Any] = field(default_factory=dict)
    synchronization_state: Dict[str, Any] = field(default_factory=dict)


# Orchestration models
class OrchestrationStatus(str, Enum):
    """Status of workflow orchestration"""
    INITIALIZING = "initializing"
    COORDINATING = "coordinating"
    EXECUTING = "executing"
    SYNCHRONIZING = "synchronizing"
    COMPLETING = "completing"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OrchestrationContext:
    """Context for workflow orchestration"""
    orchestration_id: str
    workflows: List[IntelligentWorkflow]
    coordination_rules: List[ServiceCoordination]
    global_context: Dict[str, Any] = field(default_factory=dict)
    service_registry: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    """Result of workflow orchestration"""
    orchestration_id: str
    status: OrchestrationStatus
    workflow_results: Dict[str, ExecutionResult]  # workflow_id -> result
    coordination_metrics: Dict[str, Any] = field(default_factory=dict)
    global_metrics: Dict[str, Any] = field(default_factory=dict)
    error_summary: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


# Monitoring and recovery models
@dataclass
class ExecutionMonitor:
    """Monitor for workflow execution"""
    monitor_id: str
    workflow_id: str
    monitoring_rules: List[Dict[str, Any]]
    alert_thresholds: Dict[str, Any]
    recovery_policies: Dict[str, Any]
    current_metrics: Dict[str, Any] = field(default_factory=dict)
    alert_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExecutionRecovery:
    """Recovery mechanism for failed executions"""
    recovery_id: str
    workflow_id: str
    failure_point: str
    recovery_strategy: AdaptationStrategy
    recovery_steps: List[str]
    recovery_context: Dict[str, Any] = field(default_factory=dict)
    success_probability: float = 0.0
    estimated_recovery_time: Optional[timedelta] = None


# Integration models
@dataclass
class ServiceIntegration:
    """Integration configuration for services"""
    service_name: str
    integration_type: str  # api, message_queue, database, file_system
    connection_config: Dict[str, Any]
    authentication_config: Dict[str, Any]
    rate_limits: Dict[str, Any] = field(default_factory=dict)
    retry_policies: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    health_check_config: Dict[str, Any] = field(default_factory=dict)
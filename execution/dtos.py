"""
Phase 7: Stage E Execution DTOs (Data Transfer Objects)
Request/Response models for execution API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from execution.models import (
    ActionClass,
    ApprovalState,
    ExecutionMode,
    ExecutionStatus,
    SLAClass,
)


# ============================================================================
# REQUEST DTOs
# ============================================================================

class ExecutionRequest(BaseModel):
    """Request to create a new execution"""
    
    # Plan (from Stage D)
    plan: Dict[str, Any]
    
    # Approval Level
    approval_level: int = Field(ge=0, le=3, default=0)
    
    # Optional Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Observability
    trace_id: Optional[UUID] = None
    parent_execution_id: Optional[UUID] = None


class ApprovalRequest(BaseModel):
    """Request to approve/reject an execution"""
    
    # Approval Decision
    approved: bool
    comment: Optional[str] = None
    
    # Approver (from JWT token)
    approver_id: int


class CancellationRequest(BaseModel):
    """Request to cancel an execution"""
    
    # Cancellation Reason
    reason: Optional[str] = None
    
    # Actor (from JWT token)
    actor_id: int


class RequeueRequest(BaseModel):
    """Request to requeue a DLQ execution"""
    
    # Requeue Options
    reset_retry_count: bool = False
    new_priority: Optional[int] = Field(None, ge=1, le=10)
    
    # Actor (from JWT token)
    actor_id: int


# ============================================================================
# RESPONSE DTOs
# ============================================================================

class ExecutionResponse(BaseModel):
    """Response for execution details"""
    
    # Execution ID
    execution_id: UUID
    
    # Status
    status: ExecutionStatus
    execution_mode: ExecutionMode
    sla_class: SLAClass
    approval_level: int
    
    # Timing
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    # Progress
    total_steps: int
    completed_steps: int
    failed_steps: int
    progress_percentage: float
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Observability
    trace_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ExecutionStepResponse(BaseModel):
    """Response for execution step details"""
    
    # Step ID
    step_id: UUID
    
    # Step Metadata
    step_index: int
    step_name: str
    step_type: str
    target_hostname: Optional[str] = None
    
    # Status
    status: ExecutionStatus
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Results
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Retry
    retry_count: int
    max_retries: int
    
    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):
    """Response for approval details"""
    
    # Approval ID
    approval_id: UUID
    execution_id: UUID
    
    # Approval Metadata
    approval_level: int
    state: ApprovalState
    
    # Approver
    approver_id: Optional[int] = None
    approver_comment: Optional[str] = None
    
    # Timing
    requested_at: datetime
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Response for execution list"""
    
    executions: List[ExecutionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ExecutionProgressUpdate(BaseModel):
    """Real-time progress update (for WebSocket/SSE)"""
    
    # Execution ID
    execution_id: UUID
    
    # Progress
    status: ExecutionStatus
    progress_percentage: float
    current_step_index: Optional[int] = None
    current_step_name: Optional[str] = None
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Message
    message: Optional[str] = None


class ExecutionStepProgressUpdate(BaseModel):
    """Real-time step progress update (for WebSocket/SSE)"""
    
    # Step ID
    step_id: UUID
    execution_id: UUID
    
    # Progress
    step_index: int
    step_name: str
    status: ExecutionStatus
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Message
    message: Optional[str] = None
    output_preview: Optional[str] = None


class ExecutionEventResponse(BaseModel):
    """Response for execution event"""
    
    # Event ID
    event_id: UUID
    execution_id: UUID
    
    # Event Metadata
    event_type: str
    from_status: Optional[ExecutionStatus] = None
    to_status: Optional[ExecutionStatus] = None
    
    # Actor
    actor_id: Optional[int] = None
    actor_type: Optional[str] = None
    
    # Details
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Timing
    created_at: datetime
    
    class Config:
        from_attributes = True


class TimeoutPolicyResponse(BaseModel):
    """Response for timeout policy"""
    
    # Policy Key
    sla_class: SLAClass
    action_class: ActionClass
    
    # Timeout Values (in seconds)
    step_timeout_seconds: int
    execution_timeout_seconds: int
    lease_timeout_seconds: int
    approval_timeout_seconds: Optional[int] = None
    
    # DLQ Thresholds
    max_attempts: int
    
    # Metadata
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExecutionStatsResponse(BaseModel):
    """Response for execution statistics"""
    
    # Counts by Status
    total_executions: int
    pending_approval: int
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int
    
    # Performance Metrics
    avg_execution_time_seconds: Optional[float] = None
    p95_execution_time_seconds: Optional[float] = None
    p99_execution_time_seconds: Optional[float] = None
    
    # Success Rate
    success_rate: Optional[float] = None
    failure_rate: Optional[float] = None
    
    # Queue Metrics
    queue_depth: int
    dlq_depth: int
    
    # Time Range
    from_date: datetime
    to_date: datetime


class HealthCheckResponse(BaseModel):
    """Response for execution service health check"""
    
    # Service Status
    status: str  # 'healthy', 'degraded', 'unhealthy'
    
    # Component Health
    database: bool
    redis: bool
    queue_workers: bool
    
    # Metrics
    active_executions: int
    queue_depth: int
    dlq_depth: int
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# FILTER DTOs
# ============================================================================

class ExecutionFilter(BaseModel):
    """Filter for execution list queries"""
    
    # Status Filter
    status: Optional[List[ExecutionStatus]] = None
    
    # Mode Filter
    execution_mode: Optional[ExecutionMode] = None
    
    # SLA Filter
    sla_class: Optional[SLAClass] = None
    
    # Approval Filter
    approval_level: Optional[int] = Field(None, ge=0, le=3)
    
    # Actor Filter
    actor_id: Optional[int] = None
    
    # Date Range
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    # Tags Filter
    tags: Optional[List[str]] = None
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")  # 'asc' or 'desc'


class ExecutionStepFilter(BaseModel):
    """Filter for execution step queries"""
    
    # Execution Filter
    execution_id: UUID
    
    # Status Filter
    status: Optional[List[ExecutionStatus]] = None
    
    # Target Filter
    target_asset_id: Optional[int] = None
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


# ============================================================================
# INTERNAL DTOs (for service-to-service communication)
# ============================================================================

class ExecutionContext(BaseModel):
    """Internal execution context (passed to workers)"""
    
    # Execution Metadata
    execution_id: UUID
    tenant_id: str
    actor_id: int
    
    # Plan
    plan_snapshot: Dict[str, Any]
    
    # Execution Settings
    execution_mode: ExecutionMode
    sla_class: SLAClass
    approval_level: int
    
    # Timeout Policy
    step_timeout_seconds: int
    execution_timeout_seconds: int
    
    # Observability
    trace_id: Optional[UUID] = None
    
    # Worker Metadata
    worker_id: Optional[str] = None
    lease_token: Optional[UUID] = None


class StepExecutionContext(BaseModel):
    """Internal step execution context"""
    
    # Step Metadata
    step_id: UUID
    execution_id: UUID
    step_index: int
    step_name: str
    step_type: str
    
    # Target
    target_asset_id: Optional[int] = None
    target_hostname: Optional[str] = None
    
    # Input
    input_data: Dict[str, Any]
    
    # Timeout
    step_timeout_seconds: int
    
    # Retry
    retry_count: int
    max_retries: int
    
    # Observability
    trace_id: Optional[UUID] = None


class ExecutionResult(BaseModel):
    """Internal execution result"""
    
    # Execution ID
    execution_id: UUID
    
    # Status
    status: ExecutionStatus
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Step Results
    step_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    started_at: datetime
    completed_at: datetime
    duration_seconds: float


class StepExecutionResult(BaseModel):
    """Internal step execution result"""
    
    # Step ID
    step_id: UUID
    
    # Status
    status: ExecutionStatus
    
    # Output
    output_data: Optional[Dict[str, Any]] = None
    artifacts: Optional[Dict[str, Any]] = None
    
    # Error
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Timing
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    
    # Logs
    logs: Optional[str] = None  # Masked logs
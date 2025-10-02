"""
Phase 7: Stage E Execution Models
Production-hardened execution models with 7 critical safety features
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS (matching database ENUMs)
# ============================================================================

class ExecutionStatus(str, Enum):
    """Execution status with FSM legal transitions"""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


class ExecutionMode(str, Enum):
    """Execution mode (immediate vs background)"""
    IMMEDIATE = "immediate"  # Synchronous execution (<10s)
    BACKGROUND = "background"  # Asynchronous execution (>30s, via queue)


class SLAClass(str, Enum):
    """SLA class for timeout policies"""
    FAST = "fast"      # <10s operations
    MEDIUM = "medium"  # 10-30s operations
    LONG = "long"      # >30s operations


class ApprovalState(str, Enum):
    """Approval state"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActionClass(str, Enum):
    """Action class for timeout policies"""
    READ = "read"
    MODIFY = "modify"
    DEPLOY = "deploy"


# ============================================================================
# FSM STATE MACHINE
# ============================================================================

class ExecutionFSM:
    """Finite State Machine for execution status transitions"""
    
    # Legal state transitions
    LEGAL_TRANSITIONS: Dict[ExecutionStatus, List[ExecutionStatus]] = {
        ExecutionStatus.PENDING_APPROVAL: [
            ExecutionStatus.APPROVED,
            ExecutionStatus.REJECTED,
            ExecutionStatus.CANCELLED,
        ],
        ExecutionStatus.APPROVED: [
            ExecutionStatus.QUEUED,
            ExecutionStatus.RUNNING,  # For immediate execution
            ExecutionStatus.CANCELLED,
        ],
        ExecutionStatus.QUEUED: [
            ExecutionStatus.RUNNING,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
        ],
        ExecutionStatus.RUNNING: [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.PARTIAL,
        ],
        # Terminal states (no transitions)
        ExecutionStatus.COMPLETED: [],
        ExecutionStatus.FAILED: [],
        ExecutionStatus.CANCELLED: [],
        ExecutionStatus.TIMEOUT: [],
        ExecutionStatus.PARTIAL: [],
        ExecutionStatus.REJECTED: [],
    }
    
    @classmethod
    def is_valid_transition(cls, from_status: ExecutionStatus, to_status: ExecutionStatus) -> bool:
        """Check if a state transition is legal"""
        return to_status in cls.LEGAL_TRANSITIONS.get(from_status, [])
    
    @classmethod
    def is_terminal_state(cls, status: ExecutionStatus) -> bool:
        """Check if a status is a terminal state"""
        return len(cls.LEGAL_TRANSITIONS.get(status, [])) == 0


# ============================================================================
# CORE MODELS
# ============================================================================

class ExecutionModel(BaseModel):
    """Main execution record"""
    
    # Primary Key
    id: Optional[int] = None
    execution_id: UUID = Field(default_factory=uuid4)
    
    # Tenant & Actor
    tenant_id: str
    actor_id: int
    
    # Idempotency
    idempotency_key: str  # sha256(canonical_json(plan) + tenant_id + actor_id)
    plan_snapshot: Dict[str, Any]  # Immutable snapshot of the plan
    
    # Execution Metadata
    execution_mode: ExecutionMode
    sla_class: SLAClass
    approval_level: int = Field(ge=0, le=3)
    
    # Status & FSM
    status: ExecutionStatus = ExecutionStatus.PENDING_APPROVAL
    previous_status: Optional[ExecutionStatus] = None
    status_changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Observability
    trace_id: Optional[UUID] = None
    parent_execution_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('approval_level')
    @classmethod
    def validate_approval_level(cls, v: int) -> int:
        """Validate approval level is 0-3"""
        if v not in [0, 1, 2, 3]:
            raise ValueError("approval_level must be 0, 1, 2, or 3")
        return v
    
    def transition_to(self, new_status: ExecutionStatus) -> None:
        """Transition to a new status with FSM validation"""
        if not ExecutionFSM.is_valid_transition(self.status, new_status):
            raise ValueError(
                f"Invalid state transition: {self.status} -> {new_status}"
            )
        self.previous_status = self.status
        self.status = new_status
        self.status_changed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    class Config:
        from_attributes = True


class ExecutionStepModel(BaseModel):
    """Step-level execution tracking"""
    
    # Primary Key
    id: Optional[int] = None
    step_id: UUID = Field(default_factory=uuid4)
    
    # Foreign Key
    execution_id: UUID
    
    # Step Metadata
    step_index: int
    step_name: str
    step_type: str
    target_asset_id: Optional[int] = None
    target_hostname: Optional[str] = None
    
    # Status
    status: ExecutionStatus = ExecutionStatus.QUEUED
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Input/Output
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    artifacts: Optional[Dict[str, Any]] = None  # Limited to 10KB
    
    # Error Handling
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Observability
    trace_id: Optional[UUID] = None
    logs: Optional[str] = None  # Masked logs
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ApprovalModel(BaseModel):
    """Approval workflow record"""
    
    # Primary Key
    id: Optional[int] = None
    approval_id: UUID = Field(default_factory=uuid4)
    
    # Foreign Key
    execution_id: UUID
    
    # Approval Metadata
    approval_level: int = Field(ge=1, le=3)
    plan_hash: str  # Bound to plan snapshot
    
    # Approver
    approver_id: Optional[int] = None
    approver_comment: Optional[str] = None
    
    # State
    state: ApprovalState = ApprovalState.PENDING
    
    # Timing
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ExecutionEventModel(BaseModel):
    """Audit trail for FSM transitions"""
    
    # Primary Key
    id: Optional[int] = None
    event_id: UUID = Field(default_factory=uuid4)
    
    # Foreign Key
    execution_id: UUID
    
    # Event Metadata
    event_type: str
    from_status: Optional[ExecutionStatus] = None
    to_status: Optional[ExecutionStatus] = None
    
    # Actor
    actor_id: Optional[int] = None
    actor_type: Optional[str] = None  # 'user', 'system', 'worker'
    
    # Details
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Observability
    trace_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class ExecutionQueueModel(BaseModel):
    """Background execution queue entry"""
    
    # Primary Key
    id: Optional[int] = None
    queue_id: UUID = Field(default_factory=uuid4)
    
    # Foreign Key
    execution_id: UUID
    
    # Queue Metadata
    priority: int = Field(default=5, ge=1, le=10)
    sla_class: SLAClass
    
    # Lease Management
    lease_token: Optional[UUID] = None
    lease_expires_at: Optional[datetime] = None
    visibility_timeout_seconds: Optional[int] = None
    
    # Retry Logic
    attempt_count: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    
    # Timing
    enqueued_at: datetime = Field(default_factory=datetime.utcnow)
    dequeued_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Status
    status: str = "pending"  # 'pending', 'processing', 'completed', 'failed'
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ExecutionDLQModel(BaseModel):
    """Dead letter queue entry"""
    
    # Primary Key
    id: Optional[int] = None
    dlq_id: UUID = Field(default_factory=uuid4)
    
    # Foreign Key
    execution_id: UUID
    
    # Failure Metadata
    failure_reason: str
    failure_details: Optional[Dict[str, Any]] = None
    attempt_count: int
    last_error: Optional[str] = None
    
    # Original Queue Entry
    original_queue_id: Optional[UUID] = None
    sla_class: SLAClass
    
    # Timing
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Retry/Requeue
    requeued: bool = False
    requeued_at: Optional[datetime] = None
    requeued_by: Optional[int] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ExecutionLockModel(BaseModel):
    """Per-asset mutex lock"""
    
    # Primary Key
    id: Optional[int] = None
    lock_id: UUID = Field(default_factory=uuid4)
    
    # Lock Target
    asset_id: int
    tenant_id: str
    
    # Lock Owner
    execution_id: UUID
    owner_tag: str  # Format: "execution:{execution_id}:worker:{worker_id}"
    
    # Lock Metadata
    acquired_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_heartbeat_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    is_active: bool = True
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class TimeoutPolicyModel(BaseModel):
    """Timeout policy (SLA class × action class matrix)"""
    
    # Primary Key
    id: Optional[int] = None
    
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
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_idempotency_key(
    plan: Dict[str, Any],
    tenant_id: str,
    actor_id: int
) -> str:
    """
    Calculate idempotency key for execution
    Formula: sha256(canonical_json(plan) + tenant_id + actor_id)
    """
    import hashlib
    import json
    
    # Ensure deterministic target ordering
    if "targets" in plan:
        plan["targets"] = sorted(plan["targets"], key=lambda t: t.get("id", 0))
    
    # Create canonical JSON
    canonical_json = json.dumps(plan, sort_keys=True, separators=(',', ':'))
    
    # Combine with tenant_id and actor_id
    combined = f"{canonical_json}:{tenant_id}:{actor_id}"
    
    # Calculate SHA256
    return hashlib.sha256(combined.encode()).hexdigest()


def determine_sla_class(estimated_duration_seconds: float) -> SLAClass:
    """Determine SLA class based on estimated duration"""
    if estimated_duration_seconds < 10:
        return SLAClass.FAST
    elif estimated_duration_seconds < 30:
        return SLAClass.MEDIUM
    else:
        return SLAClass.LONG


def determine_execution_mode(sla_class: SLAClass) -> ExecutionMode:
    """Determine execution mode based on SLA class"""
    if sla_class == SLAClass.FAST:
        return ExecutionMode.IMMEDIATE
    else:
        return ExecutionMode.BACKGROUND


def determine_action_class(step_type: str) -> ActionClass:
    """Determine action class based on step type"""
    read_operations = ["ssh_command_read", "api_get", "file_read", "query"]
    modify_operations = ["ssh_command_write", "api_post", "api_put", "file_write", "update"]
    
    if any(op in step_type.lower() for op in read_operations):
        return ActionClass.READ
    elif any(op in step_type.lower() for op in modify_operations):
        return ActionClass.MODIFY
    else:
        return ActionClass.DEPLOY
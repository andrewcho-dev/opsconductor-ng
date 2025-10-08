"""
Phase 7: Stage E Execution Repository
Database access layer with production-hardened queries
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import psycopg2
from psycopg2.extras import RealDictCursor

from execution.models import (
    ApprovalModel,
    ExecutionDLQModel,
    ExecutionEventModel,
    ExecutionLockModel,
    ExecutionModel,
    ExecutionQueueModel,
    ExecutionStatus,
    ExecutionStepModel,
    SLAClass,
    TimeoutPolicyModel,
)

logger = logging.getLogger(__name__)


class ExecutionRepository:
    """Repository for execution data access"""
    
    def __init__(self, db_connection_string: str):
        """Initialize repository with database connection"""
        self.db_connection_string = db_connection_string
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_connection_string)
    
    # ========================================================================
    # EXECUTIONS
    # ========================================================================
    
    def create_execution(self, execution: ExecutionModel) -> ExecutionModel:
        """Create a new execution"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO execution.executions (
                        execution_id, tenant_id, actor_id, idempotency_key,
                        plan_snapshot, execution_mode, sla_class, approval_level,
                        status, timeout_at, trace_id, parent_execution_id,
                        tags, metadata
                    ) VALUES (
                        %(execution_id)s, %(tenant_id)s, %(actor_id)s, %(idempotency_key)s,
                        %(plan_snapshot)s, %(execution_mode)s, %(sla_class)s, %(approval_level)s,
                        %(status)s, %(timeout_at)s, %(trace_id)s, %(parent_execution_id)s,
                        %(tags)s, %(metadata)s
                    )
                    RETURNING *
                """, {
                    "execution_id": str(execution.execution_id),
                    "tenant_id": execution.tenant_id,
                    "actor_id": execution.actor_id,
                    "idempotency_key": execution.idempotency_key,
                    "plan_snapshot": psycopg2.extras.Json(execution.plan_snapshot),
                    "execution_mode": execution.execution_mode.value,
                    "sla_class": execution.sla_class.value,
                    "approval_level": execution.approval_level,
                    "status": execution.status.value,
                    "timeout_at": execution.timeout_at,
                    "trace_id": str(execution.trace_id) if execution.trace_id else None,
                    "parent_execution_id": str(execution.parent_execution_id) if execution.parent_execution_id else None,
                    "tags": psycopg2.extras.Json(execution.tags),
                    "metadata": psycopg2.extras.Json(execution.metadata),
                })
                row = cur.fetchone()
                conn.commit()
                return ExecutionModel(**dict(row))
    
    def get_execution_by_id(self, execution_id: UUID) -> Optional[ExecutionModel]:
        """Get execution by ID"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM execution.executions
                    WHERE execution_id = %s
                """, (str(execution_id),))
                row = cur.fetchone()
                return ExecutionModel(**dict(row)) if row else None
    
    def get_execution_by_idempotency_key(
        self,
        tenant_id: str,
        idempotency_key: str
    ) -> Optional[ExecutionModel]:
        """Get execution by idempotency key (for duplicate detection)"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM execution.executions
                    WHERE tenant_id = %s AND idempotency_key = %s
                """, (tenant_id, idempotency_key))
                row = cur.fetchone()
                return ExecutionModel(**dict(row)) if row else None
    
    def update_execution_status(
        self,
        execution_id: UUID,
        status: ExecutionStatus,
        previous_status: Optional[ExecutionStatus] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update execution status"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.executions
                    SET status = %s,
                        previous_status = %s,
                        status_changed_at = CURRENT_TIMESTAMP,
                        error_message = %s,
                        error_details = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE execution_id = %s
                """, (
                    status.value,
                    previous_status.value if previous_status else None,
                    error_message,
                    psycopg2.extras.Json(error_details) if error_details else None,
                    str(execution_id)
                ))
                conn.commit()
    
    def update_execution_result(
        self,
        execution_id: UUID,
        result: Dict[str, Any],
        completed_at: datetime
    ) -> None:
        """Update execution result"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.executions
                    SET result = %s,
                        completed_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE execution_id = %s
                """, (
                    psycopg2.extras.Json(result),
                    completed_at,
                    str(execution_id)
                ))
                conn.commit()
    
    def list_executions(
        self,
        tenant_id: str,
        status: Optional[List[ExecutionStatus]] = None,
        actor_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[ExecutionModel]:
        """List executions with filters"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM execution.executions WHERE tenant_id = %s"
                params: List[Any] = [tenant_id]
                
                if status:
                    query += " AND status = ANY(%s)"
                    params.append([s.value for s in status])
                
                if actor_id:
                    query += " AND actor_id = %s"
                    params.append(actor_id)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                rows = cur.fetchall()
                return [ExecutionModel(**dict(row)) for row in rows]
    
    # ========================================================================
    # EXECUTION STEPS
    # ========================================================================
    
    def create_execution_step(self, step: ExecutionStepModel) -> ExecutionStepModel:
        """Create a new execution step"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO execution.execution_steps (
                        step_id, execution_id, step_index, step_name, step_type,
                        target_asset_id, target_hostname, status, input_data,
                        max_retries, trace_id
                    ) VALUES (
                        %(step_id)s, %(execution_id)s, %(step_index)s, %(step_name)s, %(step_type)s,
                        %(target_asset_id)s, %(target_hostname)s, %(status)s, %(input_data)s,
                        %(max_retries)s, %(trace_id)s
                    )
                    RETURNING *
                """, {
                    "step_id": str(step.step_id),
                    "execution_id": str(step.execution_id),
                    "step_index": step.step_index,
                    "step_name": step.step_name,
                    "step_type": step.step_type,
                    "target_asset_id": step.target_asset_id,
                    "target_hostname": step.target_hostname,
                    "status": step.status.value,
                    "input_data": psycopg2.extras.Json(step.input_data) if step.input_data else None,
                    "max_retries": step.max_retries,
                    "trace_id": str(step.trace_id) if step.trace_id else None,
                })
                row = cur.fetchone()
                conn.commit()
                return ExecutionStepModel(**dict(row))
    
    def get_execution_steps(self, execution_id: UUID) -> List[ExecutionStepModel]:
        """Get all steps for an execution"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM execution.execution_steps
                    WHERE execution_id = %s
                    ORDER BY step_index ASC
                """, (str(execution_id),))
                rows = cur.fetchall()
                return [ExecutionStepModel(**dict(row)) for row in rows]
    
    def update_step_status(
        self,
        step_id: UUID,
        status: ExecutionStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Update step status"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.execution_steps
                    SET status = %s,
                        output_data = %s,
                        error_message = %s,
                        duration_ms = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE step_id = %s
                """, (
                    status.value,
                    psycopg2.extras.Json(output_data) if output_data else None,
                    error_message,
                    duration_ms,
                    str(step_id)
                ))
                conn.commit()
    
    # ========================================================================
    # APPROVALS
    # ========================================================================
    
    def create_approval(self, approval: ApprovalModel) -> ApprovalModel:
        """Create a new approval"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO execution.approvals (
                        approval_id, execution_id, approval_level, plan_hash,
                        state, expires_at
                    ) VALUES (
                        %(approval_id)s, %(execution_id)s, %(approval_level)s, %(plan_hash)s,
                        %(state)s, %(expires_at)s
                    )
                    RETURNING *
                """, {
                    "approval_id": str(approval.approval_id),
                    "execution_id": str(approval.execution_id),
                    "approval_level": approval.approval_level,
                    "plan_hash": approval.plan_hash,
                    "state": approval.state.value,
                    "expires_at": approval.expires_at,
                })
                row = cur.fetchone()
                conn.commit()
                return ApprovalModel(**dict(row))
    
    def get_approval_by_execution_id(self, execution_id: UUID) -> Optional[ApprovalModel]:
        """Get approval by execution ID"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM execution.approvals
                    WHERE execution_id = %s
                """, (str(execution_id),))
                row = cur.fetchone()
                return ApprovalModel(**dict(row)) if row else None
    
    def update_approval_state(
        self,
        approval_id: UUID,
        state: str,
        approver_id: int,
        approver_comment: Optional[str] = None
    ) -> None:
        """Update approval state"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.approvals
                    SET state = %s,
                        approver_id = %s,
                        approver_comment = %s,
                        responded_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE approval_id = %s
                """, (state, approver_id, approver_comment, str(approval_id)))
                conn.commit()
    
    # ========================================================================
    # EXECUTION EVENTS
    # ========================================================================
    
    def create_execution_event(self, event: ExecutionEventModel) -> ExecutionEventModel:
        """Create a new execution event"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO execution.execution_events (
                        event_id, execution_id, event_type, from_status, to_status,
                        actor_id, actor_type, details, error_message, trace_id
                    ) VALUES (
                        %(event_id)s, %(execution_id)s, %(event_type)s, %(from_status)s, %(to_status)s,
                        %(actor_id)s, %(actor_type)s, %(details)s, %(error_message)s, %(trace_id)s
                    )
                    RETURNING *
                """, {
                    "event_id": str(event.event_id),
                    "execution_id": str(event.execution_id),
                    "event_type": event.event_type,
                    "from_status": event.from_status.value if event.from_status else None,
                    "to_status": event.to_status.value if event.to_status else None,
                    "actor_id": event.actor_id,
                    "actor_type": event.actor_type,
                    "details": psycopg2.extras.Json(event.details) if event.details else None,
                    "error_message": event.error_message,
                    "trace_id": str(event.trace_id) if event.trace_id else None,
                })
                row = cur.fetchone()
                conn.commit()
                return ExecutionEventModel(**dict(row))
    
    def get_execution_events(self, execution_id: UUID) -> List[ExecutionEventModel]:
        """Get all events for an execution"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM execution.execution_events
                    WHERE execution_id = %s
                    ORDER BY created_at ASC
                """, (str(execution_id),))
                rows = cur.fetchall()
                return [ExecutionEventModel(**dict(row)) for row in rows]
    
    # ========================================================================
    # EXECUTION QUEUE
    # ========================================================================
    
    def enqueue_execution(self, queue_entry: ExecutionQueueModel) -> ExecutionQueueModel:
        """Enqueue an execution for background processing"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO execution.execution_queue (
                        queue_id, execution_id, priority, sla_class,
                        visibility_timeout_seconds, max_attempts
                    ) VALUES (
                        %(queue_id)s, %(execution_id)s, %(priority)s, %(sla_class)s,
                        %(visibility_timeout_seconds)s, %(max_attempts)s
                    )
                    RETURNING *
                """, {
                    "queue_id": str(queue_entry.queue_id),
                    "execution_id": str(queue_entry.execution_id),
                    "priority": queue_entry.priority,
                    "sla_class": queue_entry.sla_class.value,
                    "visibility_timeout_seconds": queue_entry.visibility_timeout_seconds,
                    "max_attempts": queue_entry.max_attempts,
                })
                row = cur.fetchone()
                conn.commit()
                return ExecutionQueueModel(**dict(row))
    
    def dequeue_execution(self, worker_id: str) -> Optional[ExecutionQueueModel]:
        """Dequeue an execution for processing (with lease)"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Use SELECT FOR UPDATE SKIP LOCKED for concurrent workers
                cur.execute("""
                    UPDATE execution.execution_queue
                    SET status = 'processing',
                        lease_token = gen_random_uuid(),
                        lease_expires_at = CURRENT_TIMESTAMP + (visibility_timeout_seconds || ' seconds')::INTERVAL,
                        dequeued_at = CURRENT_TIMESTAMP,
                        attempt_count = attempt_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE queue_id = (
                        SELECT queue_id FROM execution.execution_queue
                        WHERE status = 'pending'
                        AND (lease_expires_at IS NULL OR lease_expires_at < CURRENT_TIMESTAMP)
                        ORDER BY priority ASC, enqueued_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING *
                """)
                row = cur.fetchone()
                conn.commit()
                return ExecutionQueueModel(**dict(row)) if row else None
    
    def complete_queue_entry(self, queue_id: UUID) -> None:
        """Mark queue entry as completed"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.execution_queue
                    SET status = 'completed',
                        completed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE queue_id = %s
                """, (str(queue_id),))
                conn.commit()
    
    def fail_queue_entry(self, queue_id: UUID, error_message: str) -> None:
        """Mark queue entry as failed"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.execution_queue
                    SET status = 'failed',
                        last_error = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE queue_id = %s
                """, (error_message, str(queue_id)))
                conn.commit()
    
    # ========================================================================
    # EXECUTION LOCKS
    # ========================================================================
    
    def acquire_lock(self, lock: ExecutionLockModel) -> bool:
        """Acquire a lock on an asset (returns True if successful)"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        INSERT INTO execution.execution_locks (
                            lock_id, asset_id, tenant_id, execution_id, owner_tag,
                            expires_at, is_active
                        ) VALUES (
                            %(lock_id)s, %(asset_id)s, %(tenant_id)s, %(execution_id)s, %(owner_tag)s,
                            %(expires_at)s, %(is_active)s
                        )
                        ON CONFLICT (asset_id, tenant_id) DO NOTHING
                        RETURNING *
                    """, {
                        "lock_id": str(lock.lock_id),
                        "asset_id": lock.asset_id,
                        "tenant_id": lock.tenant_id,
                        "execution_id": str(lock.execution_id),
                        "owner_tag": lock.owner_tag,
                        "expires_at": lock.expires_at,
                        "is_active": lock.is_active,
                    })
                    row = cur.fetchone()
                    conn.commit()
                    return row is not None
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False
    
    def release_lock(self, asset_id: int, tenant_id: str, execution_id: UUID) -> None:
        """Release a lock on an asset"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.execution_locks
                    SET is_active = false,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE asset_id = %s
                    AND tenant_id = %s
                    AND execution_id = %s
                    AND is_active = true
                """, (asset_id, tenant_id, str(execution_id)))
                conn.commit()
    
    def heartbeat_lock(self, lock_id: UUID) -> None:
        """Update lock heartbeat"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.execution_locks
                    SET last_heartbeat_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE lock_id = %s
                    AND is_active = true
                """, (str(lock_id),))
                conn.commit()
    
    def reap_stale_locks(self) -> int:
        """Reap stale locks (expired and no heartbeat)"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE execution.execution_locks
                    SET is_active = false,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE is_active = true
                    AND expires_at < CURRENT_TIMESTAMP
                    RETURNING lock_id
                """)
                reaped_count = cur.rowcount
                conn.commit()
                return reaped_count
    
    # ========================================================================
    # TIMEOUT POLICIES
    # ========================================================================
    
    def get_timeout_policy(
        self,
        sla_class: SLAClass,
        action_class: str
    ) -> Optional[TimeoutPolicyModel]:
        """Get timeout policy by SLA class and action class"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM execution.timeout_policies
                    WHERE sla_class = %s AND action_class = %s
                """, (sla_class.value, action_class))
                row = cur.fetchone()
                return TimeoutPolicyModel(**dict(row)) if row else None
"""
Idempotency Guard - Safety Feature #1

Prevents duplicate executions caused by:
- Browser refresh (user clicks "Execute" twice)
- Network retries (client retries on timeout)
- Race conditions (multiple workers pick up same task)

Implementation:
- SHA256-based idempotency key: sha256(canonical_json(plan) + tenant_id + actor_id)
- Deterministic target ordering to ensure consistent hashing
- Tenant-scoped to prevent cross-tenant collisions
- Database-level unique constraint on (tenant_id, idempotency_key)

Usage:
    guard = IdempotencyGuard(repository)
    result = await guard.check_and_create(execution_request, tenant_id, actor_id)
    if result.is_duplicate:
        return result.existing_execution
"""

import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from execution.models import ExecutionModel, ExecutionStatus, calculate_idempotency_key
from execution.dtos import ExecutionRequest
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class IdempotencyResult:
    """Result of idempotency check"""
    
    def __init__(
        self,
        is_duplicate: bool,
        existing_execution: Optional[ExecutionModel] = None,
        idempotency_key: Optional[str] = None,
    ):
        self.is_duplicate = is_duplicate
        self.existing_execution = existing_execution
        self.idempotency_key = idempotency_key


class IdempotencyGuard:
    """
    Idempotency guard to prevent duplicate executions.
    
    This is Safety Feature #1 and is critical for production deployment.
    """
    
    def __init__(
        self,
        repository: ExecutionRepository,
        deduplication_window_hours: int = 24,
    ):
        """
        Initialize idempotency guard.
        
        Args:
            repository: Execution repository for database access
            deduplication_window_hours: How long to consider duplicates (default: 24 hours)
        """
        self.repository = repository
        self.deduplication_window_hours = deduplication_window_hours
    
    async def check_and_create(
        self,
        request: ExecutionRequest,
        tenant_id: str,
        actor_id: str,
    ) -> IdempotencyResult:
        """
        Check for duplicate execution and create if not exists.
        
        This is the main entry point for idempotency checking.
        
        Args:
            request: Execution request
            tenant_id: Tenant ID
            actor_id: Actor ID (user who initiated execution)
        
        Returns:
            IdempotencyResult with is_duplicate flag and existing execution if duplicate
        """
        # Calculate idempotency key
        idempotency_key = calculate_idempotency_key(
            plan=request.plan,
            tenant_id=tenant_id,
            actor_id=actor_id,
        )
        
        logger.info(
            f"Checking idempotency for tenant={tenant_id}, actor={actor_id}, "
            f"idempotency_key={idempotency_key[:16]}..."
        )
        
        # Check for existing execution within deduplication window
        existing = await self._find_existing_execution(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
        )
        
        if existing:
            logger.warning(
                f"Duplicate execution detected: execution_id={existing.execution_id}, "
                f"status={existing.status}, created_at={existing.created_at}"
            )
            return IdempotencyResult(
                is_duplicate=True,
                existing_execution=existing,
                idempotency_key=idempotency_key,
            )
        
        logger.info(f"No duplicate found, idempotency check passed")
        return IdempotencyResult(
            is_duplicate=False,
            existing_execution=None,
            idempotency_key=idempotency_key,
        )
    
    async def _find_existing_execution(
        self,
        tenant_id: str,
        idempotency_key: str,
    ) -> Optional[ExecutionModel]:
        """
        Find existing execution by idempotency key within deduplication window.
        
        Args:
            tenant_id: Tenant ID
            idempotency_key: Idempotency key
        
        Returns:
            Existing execution if found, None otherwise
        """
        # Calculate deduplication window
        cutoff_time = datetime.utcnow() - timedelta(hours=self.deduplication_window_hours)
        
        # Query database for existing execution
        # Note: This uses the unique index on (tenant_id, idempotency_key)
        existing = self.repository.get_execution_by_idempotency_key(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
        )
        
        if not existing:
            return None
        
        # Check if within deduplication window
        if existing.created_at < cutoff_time:
            logger.info(
                f"Found execution outside deduplication window: "
                f"execution_id={existing.execution_id}, "
                f"created_at={existing.created_at}, cutoff={cutoff_time}"
            )
            return None
        
        # Check if execution is in a terminal state
        # If terminal and failed, allow retry
        if existing.status in [ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            logger.info(
                f"Found execution in terminal state {existing.status}, "
                f"allowing retry: execution_id={existing.execution_id}"
            )
            return None
        
        return existing
    
    async def mark_duplicate(
        self,
        execution_id: str,
        duplicate_of: str,
    ) -> None:
        """
        Mark an execution as duplicate of another execution.
        
        This is used when a duplicate is detected after execution has started.
        
        Args:
            execution_id: Execution ID to mark as duplicate
            duplicate_of: Execution ID that this is a duplicate of
        """
        logger.warning(
            f"Marking execution as duplicate: execution_id={execution_id}, "
            f"duplicate_of={duplicate_of}"
        )
        
        # Update execution status to CANCELLED with reason
        self.repository.update_execution_status(
            execution_id=execution_id,
            status=ExecutionStatus.CANCELLED,
            error_message=f"Duplicate of execution {duplicate_of}",
        )
        
        # Add event to audit trail
        self.repository.create_execution_event(
            execution_id=execution_id,
            event_type="duplicate_detected",
            event_data={
                "duplicate_of": duplicate_of,
                "reason": "Idempotency check failed after execution started",
            },
        )
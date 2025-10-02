"""
Phase 7: Queue Manager
PostgreSQL-backed queue with lease-based dequeue for background execution
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from execution.models import ExecutionModel, SLAClass
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class QueueItem:
    """Queue item with lease management"""
    
    def __init__(
        self,
        queue_id: UUID,
        execution_id: UUID,
        priority: int,
        sla_class: SLAClass,
        lease_token: Optional[UUID] = None,
        lease_expires_at: Optional[datetime] = None,
        attempt_count: int = 0,
        max_attempts: int = 3,
        last_error: Optional[str] = None,
    ):
        self.queue_id = queue_id
        self.execution_id = execution_id
        self.priority = priority
        self.sla_class = sla_class
        self.lease_token = lease_token
        self.lease_expires_at = lease_expires_at
        self.attempt_count = attempt_count
        self.max_attempts = max_attempts
        self.last_error = last_error


class QueueManager:
    """
    PostgreSQL-backed queue manager for background execution.
    
    Features:
    - Lease-based dequeue (prevents duplicate processing)
    - Priority-based ordering
    - SLA class support
    - Automatic retry with exponential backoff
    - Dead letter queue for failed items
    - Visibility timeout
    """
    
    # Default configuration
    DEFAULT_LEASE_DURATION = 300  # 5 minutes
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_VISIBILITY_TIMEOUT = 300  # 5 minutes
    
    # SLA-based max attempts
    SLA_MAX_ATTEMPTS = {
        SLAClass.FAST: 2,      # Fast operations: 2 attempts
        SLAClass.MEDIUM: 3,    # Medium operations: 3 attempts
        SLAClass.LONG: 5,      # Long operations: 5 attempts
    }
    
    def __init__(
        self,
        repository: ExecutionRepository,
        lease_duration: int = DEFAULT_LEASE_DURATION,
    ):
        """
        Initialize queue manager.
        
        Args:
            repository: Execution repository
            lease_duration: Lease duration in seconds
        """
        self.repository = repository
        self.lease_duration = lease_duration
    
    async def enqueue(
        self,
        execution_id: UUID,
        priority: int = 5,
        sla_class: SLAClass = SLAClass.MEDIUM,
        visibility_timeout: Optional[int] = None,
    ) -> UUID:
        """
        Enqueue execution for background processing.
        
        Args:
            execution_id: Execution ID
            priority: Priority (1=highest, 10=lowest)
            sla_class: SLA class
            visibility_timeout: Visibility timeout in seconds
        
        Returns:
            Queue ID
        """
        queue_id = uuid4()
        max_attempts = self.SLA_MAX_ATTEMPTS.get(sla_class, self.DEFAULT_MAX_ATTEMPTS)
        
        if visibility_timeout is None:
            visibility_timeout = self.DEFAULT_VISIBILITY_TIMEOUT
        
        # Insert into queue
        query = """
            INSERT INTO execution.execution_queue (
                queue_id, execution_id, priority, sla_class,
                max_attempts, visibility_timeout_seconds, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            RETURNING queue_id
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        str(queue_id),
                        str(execution_id),
                        priority,
                        sla_class.value,
                        max_attempts,
                        visibility_timeout,
                    ),
                )
                conn.commit()
        
        logger.info(
            f"Enqueued execution {execution_id} with priority {priority}, "
            f"SLA class {sla_class.value}"
        )
        
        return queue_id
    
    async def dequeue(
        self,
        worker_id: str,
        batch_size: int = 1,
    ) -> List[QueueItem]:
        """
        Dequeue items for processing with lease.
        
        This uses a lease-based approach to prevent duplicate processing:
        1. Find items with no lease or expired lease
        2. Acquire lease with worker ID
        3. Return items to worker
        
        Args:
            worker_id: Worker ID
            batch_size: Number of items to dequeue
        
        Returns:
            List of queue items
        """
        lease_token = uuid4()
        lease_expires_at = datetime.utcnow() + timedelta(seconds=self.lease_duration)
        
        # Dequeue with lease acquisition (atomic operation)
        query = """
            WITH available_items AS (
                SELECT queue_id, execution_id, priority, sla_class,
                       attempt_count, max_attempts, last_error
                FROM execution.execution_queue
                WHERE status = 'pending'
                  AND (lease_expires_at IS NULL OR lease_expires_at < NOW())
                  AND attempt_count < max_attempts
                ORDER BY priority ASC, enqueued_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
            )
            UPDATE execution.execution_queue q
            SET lease_token = %s,
                lease_expires_at = %s,
                status = 'processing',
                dequeued_at = NOW(),
                updated_at = NOW()
            FROM available_items ai
            WHERE q.queue_id = ai.queue_id
            RETURNING q.queue_id, q.execution_id, q.priority, q.sla_class,
                      q.attempt_count, q.max_attempts, q.last_error
        """
        
        items = []
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (batch_size, str(lease_token), lease_expires_at),
                )
                rows = cursor.fetchall()
                conn.commit()
                
                for row in rows:
                    items.append(
                        QueueItem(
                            queue_id=UUID(row[0]),
                            execution_id=UUID(row[1]),
                            priority=row[2],
                            sla_class=SLAClass(row[3]),
                            lease_token=lease_token,
                            lease_expires_at=lease_expires_at,
                            attempt_count=row[4],
                            max_attempts=row[5],
                            last_error=row[6],
                        )
                    )
        
        if items:
            logger.info(
                f"Worker {worker_id} dequeued {len(items)} items "
                f"(lease: {lease_token})"
            )
        
        return items
    
    async def complete(self, queue_id: UUID) -> None:
        """
        Mark queue item as completed.
        
        Args:
            queue_id: Queue ID
        """
        query = """
            UPDATE execution.execution_queue
            SET status = 'completed',
                completed_at = NOW(),
                updated_at = NOW()
            WHERE queue_id = %s
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (str(queue_id),))
                conn.commit()
        
        logger.info(f"Completed queue item {queue_id}")
    
    async def fail(
        self,
        queue_id: UUID,
        error_message: str,
        retry: bool = True,
    ) -> bool:
        """
        Mark queue item as failed and optionally retry.
        
        Args:
            queue_id: Queue ID
            error_message: Error message
            retry: Whether to retry
        
        Returns:
            True if item will be retried, False if moved to DLQ
        """
        # Get current item
        query = """
            SELECT attempt_count, max_attempts
            FROM execution.execution_queue
            WHERE queue_id = %s
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (str(queue_id),))
                row = cursor.fetchone()
                
                if not row:
                    logger.error(f"Queue item {queue_id} not found")
                    return False
                
                attempt_count = row[0]
                max_attempts = row[1]
                
                # Check if we should retry
                will_retry = retry and (attempt_count + 1) < max_attempts
                
                if will_retry:
                    # Increment attempt count and reset lease
                    update_query = """
                        UPDATE execution.execution_queue
                        SET attempt_count = attempt_count + 1,
                            last_error = %s,
                            status = 'pending',
                            lease_token = NULL,
                            lease_expires_at = NULL,
                            updated_at = NOW()
                        WHERE queue_id = %s
                    """
                    cursor.execute(update_query, (error_message, str(queue_id)))
                    logger.info(
                        f"Queue item {queue_id} will be retried "
                        f"(attempt {attempt_count + 1}/{max_attempts})"
                    )
                else:
                    # Move to DLQ
                    update_query = """
                        UPDATE execution.execution_queue
                        SET status = 'failed',
                            last_error = %s,
                            updated_at = NOW()
                        WHERE queue_id = %s
                    """
                    cursor.execute(update_query, (error_message, str(queue_id)))
                    
                    # Insert into DLQ
                    await self._move_to_dlq(queue_id, error_message, cursor)
                    
                    logger.warning(
                        f"Queue item {queue_id} moved to DLQ after "
                        f"{attempt_count + 1} attempts"
                    )
                
                conn.commit()
                return will_retry
    
    async def _move_to_dlq(
        self,
        queue_id: UUID,
        error_message: str,
        cursor,
    ) -> None:
        """
        Move queue item to dead letter queue.
        
        Args:
            queue_id: Queue ID
            error_message: Error message
            cursor: Database cursor
        """
        query = """
            INSERT INTO execution.execution_dlq (
                dlq_id, execution_id, original_queue_id,
                failure_reason, attempt_count, original_priority,
                original_sla_class
            )
            SELECT 
                gen_random_uuid(),
                execution_id,
                queue_id,
                %s,
                attempt_count,
                priority,
                sla_class
            FROM execution.execution_queue
            WHERE queue_id = %s
        """
        
        cursor.execute(query, (error_message, str(queue_id)))
    
    async def renew_lease(
        self,
        queue_id: UUID,
        lease_token: UUID,
    ) -> bool:
        """
        Renew lease for queue item.
        
        Args:
            queue_id: Queue ID
            lease_token: Current lease token
        
        Returns:
            True if lease renewed, False otherwise
        """
        lease_expires_at = datetime.utcnow() + timedelta(seconds=self.lease_duration)
        
        query = """
            UPDATE execution.execution_queue
            SET lease_expires_at = %s,
                updated_at = NOW()
            WHERE queue_id = %s
              AND lease_token = %s
              AND status = 'processing'
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (lease_expires_at, str(queue_id), str(lease_token)),
                )
                rows_affected = cursor.rowcount
                conn.commit()
        
        if rows_affected > 0:
            logger.debug(f"Renewed lease for queue item {queue_id}")
            return True
        else:
            logger.warning(f"Failed to renew lease for queue item {queue_id}")
            return False
    
    async def get_queue_stats(self) -> dict:
        """
        Get queue statistics.
        
        Returns:
            Queue statistics
        """
        query = """
            SELECT 
                status,
                COUNT(*) as count,
                AVG(attempt_count) as avg_attempts
            FROM execution.execution_queue
            GROUP BY status
        """
        
        stats = {}
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    stats[row[0]] = {
                        "count": row[1],
                        "avg_attempts": float(row[2]) if row[2] else 0,
                    }
        
        return stats
    
    async def reap_stale_leases(self) -> int:
        """
        Reap stale leases (expired leases that haven't been renewed).
        
        Returns:
            Number of leases reaped
        """
        query = """
            UPDATE execution.execution_queue
            SET status = 'pending',
                lease_token = NULL,
                lease_expires_at = NULL,
                updated_at = NOW()
            WHERE status = 'processing'
              AND lease_expires_at < NOW()
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows_affected = cursor.rowcount
                conn.commit()
        
        if rows_affected > 0:
            logger.warning(f"Reaped {rows_affected} stale leases")
        
        return rows_affected
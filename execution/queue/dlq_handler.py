"""
Phase 7: Dead Letter Queue Handler
Handles failed executions that exceeded retry limits
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from execution.models import ExecutionStatus
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class DLQItem:
    """Dead letter queue item"""
    
    def __init__(
        self,
        dlq_id: UUID,
        execution_id: UUID,
        original_queue_id: UUID,
        failure_reason: str,
        attempt_count: int,
        original_priority: int,
        original_sla_class: str,
        failed_at: datetime,
        requeued: bool = False,
    ):
        self.dlq_id = dlq_id
        self.execution_id = execution_id
        self.original_queue_id = original_queue_id
        self.failure_reason = failure_reason
        self.attempt_count = attempt_count
        self.original_priority = original_priority
        self.original_sla_class = original_sla_class
        self.failed_at = failed_at
        self.requeued = requeued


class DLQHandler:
    """
    Dead Letter Queue handler for failed executions.
    
    Features:
    - Query DLQ items
    - Requeue items for retry
    - Archive old items
    - DLQ statistics
    """
    
    # Configuration
    DEFAULT_ARCHIVE_AFTER_DAYS = 30
    
    def __init__(
        self,
        repository: ExecutionRepository,
        archive_after_days: int = DEFAULT_ARCHIVE_AFTER_DAYS,
    ):
        """
        Initialize DLQ handler.
        
        Args:
            repository: Execution repository
            archive_after_days: Archive items after N days
        """
        self.repository = repository
        self.archive_after_days = archive_after_days
    
    async def get_items(
        self,
        limit: int = 100,
        offset: int = 0,
        requeued: Optional[bool] = None,
    ) -> List[DLQItem]:
        """
        Get DLQ items.
        
        Args:
            limit: Maximum number of items
            offset: Offset for pagination
            requeued: Filter by requeued status (None = all)
        
        Returns:
            List of DLQ items
        """
        query = """
            SELECT 
                dlq_id, execution_id, original_queue_id,
                failure_reason, attempt_count, original_priority,
                original_sla_class, failed_at, requeued
            FROM execution.execution_dlq
            WHERE 1=1
        """
        params = []
        
        if requeued is not None:
            query += " AND requeued = %s"
            params.append(requeued)
        
        query += " ORDER BY failed_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        items = []
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    items.append(
                        DLQItem(
                            dlq_id=UUID(row[0]),
                            execution_id=UUID(row[1]),
                            original_queue_id=UUID(row[2]),
                            failure_reason=row[3],
                            attempt_count=row[4],
                            original_priority=row[5],
                            original_sla_class=row[6],
                            failed_at=row[7],
                            requeued=row[8],
                        )
                    )
        
        return items
    
    async def get_item(self, dlq_id: UUID) -> Optional[DLQItem]:
        """
        Get DLQ item by ID.
        
        Args:
            dlq_id: DLQ ID
        
        Returns:
            DLQ item or None
        """
        query = """
            SELECT 
                dlq_id, execution_id, original_queue_id,
                failure_reason, attempt_count, original_priority,
                original_sla_class, failed_at, requeued
            FROM execution.execution_dlq
            WHERE dlq_id = %s
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (str(dlq_id),))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return DLQItem(
                    dlq_id=UUID(row[0]),
                    execution_id=UUID(row[1]),
                    original_queue_id=UUID(row[2]),
                    failure_reason=row[3],
                    attempt_count=row[4],
                    original_priority=row[5],
                    original_sla_class=row[6],
                    failed_at=row[7],
                    requeued=row[8],
                )
    
    async def requeue(
        self,
        dlq_id: UUID,
        reset_attempts: bool = True,
    ) -> bool:
        """
        Requeue DLQ item for retry.
        
        Args:
            dlq_id: DLQ ID
            reset_attempts: Reset attempt count
        
        Returns:
            True if requeued, False otherwise
        """
        # Get DLQ item
        item = await self.get_item(dlq_id)
        if not item:
            logger.error(f"DLQ item {dlq_id} not found")
            return False
        
        if item.requeued:
            logger.warning(f"DLQ item {dlq_id} already requeued")
            return False
        
        try:
            with self.repository.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert back into queue
                    insert_query = """
                        INSERT INTO execution.execution_queue (
                            queue_id, execution_id, priority, sla_class,
                            attempt_count, max_attempts, last_error, status
                        )
                        VALUES (
                            gen_random_uuid(), %s, %s, %s,
                            %s, 3, %s, 'pending'
                        )
                    """
                    
                    attempt_count = 0 if reset_attempts else item.attempt_count
                    
                    cursor.execute(
                        insert_query,
                        (
                            str(item.execution_id),
                            item.original_priority,
                            item.original_sla_class,
                            attempt_count,
                            item.failure_reason,
                        ),
                    )
                    
                    # Mark DLQ item as requeued
                    update_query = """
                        UPDATE execution.execution_dlq
                        SET requeued = TRUE,
                            requeued_at = NOW()
                        WHERE dlq_id = %s
                    """
                    cursor.execute(update_query, (str(dlq_id),))
                    
                    # Reset execution status
                    execution_update_query = """
                        UPDATE execution.executions
                        SET status = 'queued',
                            error_message = NULL,
                            updated_at = NOW()
                        WHERE execution_id = %s
                    """
                    cursor.execute(execution_update_query, (str(item.execution_id),))
                    
                    conn.commit()
            
            logger.info(
                f"Requeued DLQ item {dlq_id} (execution {item.execution_id})"
            )
            return True
        
        except Exception as e:
            logger.error(f"Failed to requeue DLQ item {dlq_id}: {e}", exc_info=True)
            return False
    
    async def archive_old_items(self) -> int:
        """
        Archive old DLQ items.
        
        This moves items older than archive_after_days to an archive table
        (or deletes them if no archive table exists).
        
        Returns:
            Number of items archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.archive_after_days)
        
        # For now, just mark as archived (could move to separate table)
        query = """
            UPDATE execution.execution_dlq
            SET archived = TRUE,
                archived_at = NOW()
            WHERE failed_at < %s
              AND archived = FALSE
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cutoff_date,))
                rows_affected = cursor.rowcount
                conn.commit()
        
        if rows_affected > 0:
            logger.info(f"Archived {rows_affected} old DLQ items")
        
        return rows_affected
    
    async def get_stats(self) -> dict:
        """
        Get DLQ statistics.
        
        Returns:
            DLQ statistics
        """
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE requeued = TRUE) as requeued,
                COUNT(*) FILTER (WHERE archived = TRUE) as archived,
                COUNT(*) FILTER (WHERE failed_at > NOW() - INTERVAL '24 hours') as last_24h,
                COUNT(*) FILTER (WHERE failed_at > NOW() - INTERVAL '7 days') as last_7d
            FROM execution.execution_dlq
        """
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                
                return {
                    "total": row[0],
                    "requeued": row[1],
                    "archived": row[2],
                    "last_24h": row[3],
                    "last_7d": row[4],
                }
    
    async def get_failure_reasons(self, limit: int = 10) -> List[dict]:
        """
        Get top failure reasons.
        
        Args:
            limit: Maximum number of reasons
        
        Returns:
            List of failure reasons with counts
        """
        query = """
            SELECT 
                failure_reason,
                COUNT(*) as count
            FROM execution.execution_dlq
            WHERE archived = FALSE
            GROUP BY failure_reason
            ORDER BY count DESC
            LIMIT %s
        """
        
        reasons = []
        
        with self.repository.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                
                for row in rows:
                    reasons.append({
                        "reason": row[0],
                        "count": row[1],
                    })
        
        return reasons
"""
Phase 7: Queue & Worker Tests
Comprehensive tests for background queue and worker system
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from execution.models import ExecutionModel, ExecutionStatus, SLAClass, ExecutionMode
from execution.queue.queue_manager import QueueManager, QueueItem
from execution.queue.worker import Worker
from execution.queue.dlq_handler import DLQHandler, DLQItem
from execution.queue.worker_pool import WorkerPool
from execution.repository import ExecutionRepository


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_repository():
    """Mock execution repository"""
    repo = Mock(spec=ExecutionRepository)
    repo.get_connection = Mock()
    return repo


@pytest.fixture
def sample_execution():
    """Sample execution for testing"""
    return ExecutionModel(
        execution_id=uuid4(),
        tenant_id="tenant-1",
        actor_id=1,
        idempotency_key="test-key",
        plan_id=uuid4(),
        plan_snapshot={},
        status=ExecutionStatus.QUEUED,
        execution_mode=ExecutionMode.BACKGROUND,
        sla_class=SLAClass.MEDIUM,
        approval_level=0,
        priority=5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def queue_manager(mock_repository):
    """Queue manager instance"""
    return QueueManager(repository=mock_repository)


@pytest.fixture
def dlq_handler(mock_repository):
    """DLQ handler instance"""
    return DLQHandler(repository=mock_repository)


# ============================================================================
# QUEUE MANAGER TESTS
# ============================================================================

class TestQueueManager:
    """Test queue manager"""
    
    @pytest.mark.asyncio
    async def test_enqueue(self, queue_manager, mock_repository, sample_execution):
        """Test enqueue execution"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        queue_id = await queue_manager.enqueue(
            execution_id=sample_execution.execution_id,
            priority=5,
            sla_class=SLAClass.MEDIUM,
        )
        
        # Assert
        assert queue_id is not None
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dequeue(self, queue_manager, mock_repository):
        """Test dequeue with lease"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                str(uuid4()),  # queue_id
                str(uuid4()),  # execution_id
                5,  # priority
                "medium",  # sla_class
                0,  # attempt_count
                3,  # max_attempts
                None,  # last_error
            )
        ]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        items = await queue_manager.dequeue(worker_id="worker-1", batch_size=1)
        
        # Assert
        assert len(items) == 1
        assert isinstance(items[0], QueueItem)
        assert items[0].lease_token is not None
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete(self, queue_manager, mock_repository):
        """Test complete queue item"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        queue_id = uuid4()
        
        # Execute
        await queue_manager.complete(queue_id)
        
        # Assert
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fail_with_retry(self, queue_manager, mock_repository):
        """Test fail queue item with retry"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (0, 3)  # attempt_count, max_attempts
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        queue_id = uuid4()
        
        # Execute
        will_retry = await queue_manager.fail(
            queue_id=queue_id,
            error_message="Test error",
            retry=True,
        )
        
        # Assert
        assert will_retry is True
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fail_move_to_dlq(self, queue_manager, mock_repository):
        """Test fail queue item and move to DLQ"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (3, 3)  # attempt_count, max_attempts (exhausted)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        queue_id = uuid4()
        
        # Execute
        will_retry = await queue_manager.fail(
            queue_id=queue_id,
            error_message="Test error",
            retry=True,
        )
        
        # Assert
        assert will_retry is False
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_renew_lease(self, queue_manager, mock_repository):
        """Test renew lease"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        queue_id = uuid4()
        lease_token = uuid4()
        
        # Execute
        success = await queue_manager.renew_lease(
            queue_id=queue_id,
            lease_token=lease_token,
        )
        
        # Assert
        assert success is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reap_stale_leases(self, queue_manager, mock_repository):
        """Test reap stale leases"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 2
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        reaped = await queue_manager.reap_stale_leases()
        
        # Assert
        assert reaped == 2
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


# ============================================================================
# DLQ HANDLER TESTS
# ============================================================================

class TestDLQHandler:
    """Test DLQ handler"""
    
    @pytest.mark.asyncio
    async def test_get_items(self, dlq_handler, mock_repository):
        """Test get DLQ items"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                str(uuid4()),  # dlq_id
                str(uuid4()),  # execution_id
                str(uuid4()),  # original_queue_id
                "Test error",  # failure_reason
                3,  # attempt_count
                5,  # original_priority
                "medium",  # original_sla_class
                datetime.utcnow(),  # failed_at
                False,  # requeued
            )
        ]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        items = await dlq_handler.get_items(limit=10)
        
        # Assert
        assert len(items) == 1
        assert isinstance(items[0], DLQItem)
        mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_requeue(self, dlq_handler, mock_repository):
        """Test requeue DLQ item"""
        # Setup
        dlq_id = uuid4()
        execution_id = uuid4()
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            str(dlq_id),
            str(execution_id),
            str(uuid4()),
            "Test error",
            3,
            5,
            "medium",
            datetime.utcnow(),
            False,
        )
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        success = await dlq_handler.requeue(dlq_id, reset_attempts=True)
        
        # Assert
        assert success is True
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stats(self, dlq_handler, mock_repository):
        """Test get DLQ stats"""
        # Setup
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (10, 2, 1, 5, 8)  # total, requeued, archived, last_24h, last_7d
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_repository.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_repository.get_connection.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        stats = await dlq_handler.get_stats()
        
        # Assert
        assert stats["total"] == 10
        assert stats["requeued"] == 2
        assert stats["archived"] == 1
        assert stats["last_24h"] == 5
        assert stats["last_7d"] == 8


# ============================================================================
# WORKER TESTS
# ============================================================================

class TestWorker:
    """Test worker"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_repository):
        """Test worker health check"""
        # Setup
        queue_manager = Mock(spec=QueueManager)
        execution_engine = Mock()
        cancellation_manager = Mock()
        
        worker = Worker(
            repository=mock_repository,
            queue_manager=queue_manager,
            execution_engine=execution_engine,
            cancellation_manager=cancellation_manager,
            worker_id="test-worker",
        )
        
        # Execute
        health = await worker.health_check()
        
        # Assert
        assert health["worker_id"] == "test-worker"
        assert health["running"] is False
        assert health["current_items"] == 0


# ============================================================================
# WORKER POOL TESTS
# ============================================================================

class TestWorkerPool:
    """Test worker pool"""
    
    @pytest.mark.asyncio
    async def test_start_stop(self, mock_repository):
        """Test worker pool start and stop"""
        # Setup
        queue_manager = Mock(spec=QueueManager)
        queue_manager.dequeue = AsyncMock(return_value=[])
        queue_manager.reap_stale_leases = AsyncMock(return_value=0)
        
        execution_engine = Mock()
        cancellation_manager = Mock()
        
        pool = WorkerPool(
            repository=mock_repository,
            queue_manager=queue_manager,
            execution_engine=execution_engine,
            cancellation_manager=cancellation_manager,
            worker_count=2,
        )
        
        # Execute
        await pool.start()
        
        # Assert
        assert pool.running is True
        assert len(pool.workers) == 2
        assert len(pool.worker_tasks) == 2
        
        # Stop
        await pool.stop()
        
        # Assert
        assert pool.running is False
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_repository):
        """Test worker pool stats"""
        # Setup
        queue_manager = Mock(spec=QueueManager)
        queue_manager.dequeue = AsyncMock(return_value=[])
        queue_manager.reap_stale_leases = AsyncMock(return_value=0)
        queue_manager.get_queue_stats = AsyncMock(return_value={"pending": {"count": 5}})
        
        execution_engine = Mock()
        cancellation_manager = Mock()
        
        pool = WorkerPool(
            repository=mock_repository,
            queue_manager=queue_manager,
            execution_engine=execution_engine,
            cancellation_manager=cancellation_manager,
            worker_count=2,
        )
        
        await pool.start()
        
        # Execute
        stats = await pool.get_stats()
        
        # Assert
        assert stats["worker_count"] == 2
        assert stats["running"] is True
        assert "workers" in stats
        assert "queue" in stats
        
        # Cleanup
        await pool.stop()
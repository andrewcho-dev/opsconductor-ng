"""
Phase 7: Background Worker
Worker that processes queue items with safety features
"""

import asyncio
import logging
import signal
from datetime import datetime
from typing import Optional
from uuid import uuid4

from execution.execution_engine import ExecutionEngine
from execution.models import ExecutionStatus
from execution.queue.queue_manager import QueueManager, QueueItem
from execution.repository import ExecutionRepository
from execution.safety.cancellation import CancellationManager, CancellationReason

logger = logging.getLogger(__name__)


class Worker:
    """
    Background worker for processing execution queue.
    
    Features:
    - Lease-based processing (prevents duplicate work)
    - Automatic lease renewal
    - Graceful shutdown
    - Error handling with retry
    - Integration with all safety features
    """
    
    # Configuration
    DEFAULT_POLL_INTERVAL = 5  # seconds
    DEFAULT_LEASE_RENEWAL_INTERVAL = 60  # seconds
    DEFAULT_BATCH_SIZE = 1
    
    def __init__(
        self,
        repository: ExecutionRepository,
        queue_manager: QueueManager,
        execution_engine: ExecutionEngine,
        cancellation_manager: CancellationManager,
        worker_id: Optional[str] = None,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        lease_renewal_interval: int = DEFAULT_LEASE_RENEWAL_INTERVAL,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """
        Initialize worker.
        
        Args:
            repository: Execution repository
            queue_manager: Queue manager
            execution_engine: Execution engine
            cancellation_manager: Cancellation manager
            worker_id: Worker ID (auto-generated if not provided)
            poll_interval: Queue poll interval in seconds
            lease_renewal_interval: Lease renewal interval in seconds
            batch_size: Number of items to process per batch
        """
        self.repository = repository
        self.queue_manager = queue_manager
        self.execution_engine = execution_engine
        self.cancellation_manager = cancellation_manager
        self.worker_id = worker_id or f"worker-{uuid4()}"
        self.poll_interval = poll_interval
        self.lease_renewal_interval = lease_renewal_interval
        self.batch_size = batch_size
        
        # State
        self.running = False
        self.current_items: dict[str, QueueItem] = {}  # execution_id -> QueueItem
        self.lease_renewal_tasks: dict[str, asyncio.Task] = {}
        
        # Graceful shutdown
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception as e:
            logger.warning(f"Failed to setup signal handlers: {e}")
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self._shutdown_event.set()
    
    async def start(self) -> None:
        """
        Start worker (main loop).
        
        This will:
        1. Poll queue for items
        2. Process items with lease renewal
        3. Handle errors and retries
        4. Graceful shutdown on signal
        """
        self.running = True
        logger.info(f"Worker {self.worker_id} started")
        
        try:
            while self.running and not self._shutdown_event.is_set():
                try:
                    # Dequeue items
                    items = await self.queue_manager.dequeue(
                        worker_id=self.worker_id,
                        batch_size=self.batch_size,
                    )
                    
                    if items:
                        # Process items concurrently
                        tasks = [self._process_item(item) for item in items]
                        await asyncio.gather(*tasks, return_exceptions=True)
                    else:
                        # No items, wait before polling again
                        await asyncio.sleep(self.poll_interval)
                
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} error: {e}", exc_info=True)
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            await self._shutdown()
    
    async def stop(self) -> None:
        """Stop worker gracefully"""
        logger.info(f"Worker {self.worker_id} stopping")
        self.running = False
        self._shutdown_event.set()
    
    async def _shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info(f"Worker {self.worker_id} shutting down")
        
        # Cancel all lease renewal tasks
        for task in self.lease_renewal_tasks.values():
            task.cancel()
        
        # Wait for all tasks to complete
        if self.lease_renewal_tasks:
            await asyncio.gather(
                *self.lease_renewal_tasks.values(),
                return_exceptions=True,
            )
        
        # Cancel all in-progress executions
        for execution_id in list(self.current_items.keys()):
            try:
                await self.cancellation_manager.cancel_execution(
                    execution_id=execution_id,
                    reason=CancellationReason.SYSTEM_SHUTDOWN,
                    message="Worker shutdown",
                    actor_id="system",
                )
            except Exception as e:
                logger.error(
                    f"Failed to cancel execution {execution_id}: {e}",
                    exc_info=True,
                )
        
        logger.info(f"Worker {self.worker_id} shutdown complete")
    
    async def _process_item(self, item: QueueItem) -> None:
        """
        Process queue item.
        
        Args:
            item: Queue item
        """
        execution_id = str(item.execution_id)
        
        try:
            # Track current item
            self.current_items[execution_id] = item
            
            # Start lease renewal task
            renewal_task = asyncio.create_task(
                self._lease_renewal_loop(item)
            )
            self.lease_renewal_tasks[execution_id] = renewal_task
            
            logger.info(
                f"Worker {self.worker_id} processing execution {execution_id} "
                f"(attempt {item.attempt_count + 1}/{item.max_attempts})"
            )
            
            # Get execution
            execution = self.repository.get_execution(item.execution_id)
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            
            # Execute
            result = await self.execution_engine.execute(execution)
            
            # Mark as completed
            await self.queue_manager.complete(item.queue_id)
            
            logger.info(
                f"Worker {self.worker_id} completed execution {execution_id} "
                f"with status {result.status.value}"
            )
        
        except Exception as e:
            logger.error(
                f"Worker {self.worker_id} failed to process execution {execution_id}: {e}",
                exc_info=True,
            )
            
            # Mark as failed (will retry if attempts remaining)
            error_message = f"{type(e).__name__}: {str(e)}"
            will_retry = await self.queue_manager.fail(
                queue_id=item.queue_id,
                error_message=error_message,
                retry=True,
            )
            
            if will_retry:
                logger.info(
                    f"Execution {execution_id} will be retried "
                    f"(attempt {item.attempt_count + 1}/{item.max_attempts})"
                )
            else:
                logger.error(
                    f"Execution {execution_id} moved to DLQ after "
                    f"{item.attempt_count + 1} attempts"
                )
        
        finally:
            # Cleanup
            if execution_id in self.current_items:
                del self.current_items[execution_id]
            
            if execution_id in self.lease_renewal_tasks:
                renewal_task = self.lease_renewal_tasks[execution_id]
                renewal_task.cancel()
                del self.lease_renewal_tasks[execution_id]
    
    async def _lease_renewal_loop(self, item: QueueItem) -> None:
        """
        Lease renewal loop.
        
        This runs in the background while processing an item to keep the lease alive.
        
        Args:
            item: Queue item
        """
        try:
            while True:
                await asyncio.sleep(self.lease_renewal_interval)
                
                # Renew lease
                success = await self.queue_manager.renew_lease(
                    queue_id=item.queue_id,
                    lease_token=item.lease_token,
                )
                
                if not success:
                    logger.error(
                        f"Failed to renew lease for execution {item.execution_id}, "
                        f"cancelling execution"
                    )
                    
                    # Cancel execution
                    await self.cancellation_manager.cancel_execution(
                        execution_id=str(item.execution_id),
                        reason=CancellationReason.ERROR,
                        message="Lease renewal failed",
                        actor_id="system",
                    )
                    break
        
        except asyncio.CancelledError:
            # Task cancelled (normal shutdown)
            pass
        except Exception as e:
            logger.error(
                f"Lease renewal loop error for execution {item.execution_id}: {e}",
                exc_info=True,
            )
    
    async def health_check(self) -> dict:
        """
        Health check.
        
        Returns:
            Health status
        """
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "current_items": len(self.current_items),
            "lease_renewal_tasks": len(self.lease_renewal_tasks),
        }
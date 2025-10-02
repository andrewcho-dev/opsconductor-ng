"""
Phase 7: Worker Pool
Manages multiple workers for parallel execution processing
"""

import asyncio
import logging
from typing import List, Optional

from execution.execution_engine import ExecutionEngine
from execution.queue.queue_manager import QueueManager
from execution.queue.worker import Worker
from execution.repository import ExecutionRepository
from execution.safety.cancellation import CancellationManager

logger = logging.getLogger(__name__)


class WorkerPool:
    """
    Worker pool for managing multiple background workers.
    
    Features:
    - Dynamic worker scaling
    - Health monitoring
    - Graceful shutdown
    - Worker restart on failure
    """
    
    # Configuration
    DEFAULT_WORKER_COUNT = 3
    DEFAULT_HEALTH_CHECK_INTERVAL = 30  # seconds
    
    def __init__(
        self,
        repository: ExecutionRepository,
        queue_manager: QueueManager,
        execution_engine: ExecutionEngine,
        cancellation_manager: CancellationManager,
        worker_count: int = DEFAULT_WORKER_COUNT,
        health_check_interval: int = DEFAULT_HEALTH_CHECK_INTERVAL,
    ):
        """
        Initialize worker pool.
        
        Args:
            repository: Execution repository
            queue_manager: Queue manager
            execution_engine: Execution engine
            cancellation_manager: Cancellation manager
            worker_count: Number of workers
            health_check_interval: Health check interval in seconds
        """
        self.repository = repository
        self.queue_manager = queue_manager
        self.execution_engine = execution_engine
        self.cancellation_manager = cancellation_manager
        self.worker_count = worker_count
        self.health_check_interval = health_check_interval
        
        # State
        self.workers: List[Worker] = []
        self.worker_tasks: List[asyncio.Task] = []
        self.running = False
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start worker pool"""
        if self.running:
            logger.warning("Worker pool already running")
            return
        
        self.running = True
        logger.info(f"Starting worker pool with {self.worker_count} workers")
        
        # Create workers
        for i in range(self.worker_count):
            worker = Worker(
                repository=self.repository,
                queue_manager=self.queue_manager,
                execution_engine=self.execution_engine,
                cancellation_manager=self.cancellation_manager,
                worker_id=f"worker-{i+1}",
            )
            self.workers.append(worker)
            
            # Start worker task
            task = asyncio.create_task(worker.start())
            self.worker_tasks.append(task)
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info(f"Worker pool started with {len(self.workers)} workers")
    
    async def stop(self) -> None:
        """Stop worker pool gracefully"""
        if not self.running:
            logger.warning("Worker pool not running")
            return
        
        logger.info("Stopping worker pool")
        self.running = False
        
        # Stop health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Stop all workers
        stop_tasks = [worker.stop() for worker in self.workers]
        await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        # Wait for worker tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        logger.info("Worker pool stopped")
    
    async def scale(self, new_worker_count: int) -> None:
        """
        Scale worker pool.
        
        Args:
            new_worker_count: New number of workers
        """
        if new_worker_count == self.worker_count:
            logger.info(f"Worker pool already at {new_worker_count} workers")
            return
        
        if new_worker_count > self.worker_count:
            # Scale up
            workers_to_add = new_worker_count - self.worker_count
            logger.info(f"Scaling up worker pool by {workers_to_add} workers")
            
            for i in range(workers_to_add):
                worker = Worker(
                    repository=self.repository,
                    queue_manager=self.queue_manager,
                    execution_engine=self.execution_engine,
                    cancellation_manager=self.cancellation_manager,
                    worker_id=f"worker-{len(self.workers)+1}",
                )
                self.workers.append(worker)
                
                # Start worker task
                task = asyncio.create_task(worker.start())
                self.worker_tasks.append(task)
        
        else:
            # Scale down
            workers_to_remove = self.worker_count - new_worker_count
            logger.info(f"Scaling down worker pool by {workers_to_remove} workers")
            
            # Stop last N workers
            workers_to_stop = self.workers[-workers_to_remove:]
            stop_tasks = [worker.stop() for worker in workers_to_stop]
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            
            # Remove from lists
            self.workers = self.workers[:-workers_to_remove]
            self.worker_tasks = self.worker_tasks[:-workers_to_remove]
        
        self.worker_count = new_worker_count
        logger.info(f"Worker pool scaled to {self.worker_count} workers")
    
    async def _health_check_loop(self) -> None:
        """Health check loop"""
        try:
            while self.running:
                await asyncio.sleep(self.health_check_interval)
                
                # Check worker health
                for i, worker in enumerate(self.workers):
                    try:
                        health = await worker.health_check()
                        
                        if not health["running"]:
                            logger.warning(
                                f"Worker {worker.worker_id} not running, restarting"
                            )
                            
                            # Restart worker
                            await self._restart_worker(i)
                    
                    except Exception as e:
                        logger.error(
                            f"Health check failed for worker {worker.worker_id}: {e}",
                            exc_info=True,
                        )
                        
                        # Restart worker
                        await self._restart_worker(i)
                
                # Reap stale leases
                try:
                    reaped = await self.queue_manager.reap_stale_leases()
                    if reaped > 0:
                        logger.warning(f"Reaped {reaped} stale leases")
                except Exception as e:
                    logger.error(f"Failed to reap stale leases: {e}", exc_info=True)
        
        except asyncio.CancelledError:
            # Task cancelled (normal shutdown)
            pass
        except Exception as e:
            logger.error(f"Health check loop error: {e}", exc_info=True)
    
    async def _restart_worker(self, index: int) -> None:
        """
        Restart worker at index.
        
        Args:
            index: Worker index
        """
        try:
            # Stop old worker
            old_worker = self.workers[index]
            old_task = self.worker_tasks[index]
            
            await old_worker.stop()
            old_task.cancel()
            
            # Create new worker
            new_worker = Worker(
                repository=self.repository,
                queue_manager=self.queue_manager,
                execution_engine=self.execution_engine,
                cancellation_manager=self.cancellation_manager,
                worker_id=f"worker-{index+1}-restarted",
            )
            
            # Start new worker
            new_task = asyncio.create_task(new_worker.start())
            
            # Update lists
            self.workers[index] = new_worker
            self.worker_tasks[index] = new_task
            
            logger.info(f"Restarted worker at index {index}")
        
        except Exception as e:
            logger.error(f"Failed to restart worker at index {index}: {e}", exc_info=True)
    
    async def get_stats(self) -> dict:
        """
        Get worker pool statistics.
        
        Returns:
            Worker pool statistics
        """
        # Get worker health
        worker_health = []
        for worker in self.workers:
            try:
                health = await worker.health_check()
                worker_health.append(health)
            except Exception as e:
                worker_health.append({
                    "worker_id": worker.worker_id,
                    "error": str(e),
                })
        
        # Get queue stats
        queue_stats = await self.queue_manager.get_queue_stats()
        
        return {
            "worker_count": self.worker_count,
            "running": self.running,
            "workers": worker_health,
            "queue": queue_stats,
        }
"""
Mutex Guard - Safety Feature #2

Prevents concurrent modifications to the same asset:
- Multiple executions targeting the same server/database/service
- Race conditions in distributed workers
- Conflicting operations (e.g., restart + deploy)

Implementation:
- Per-asset locking using execution.execution_locks table
- Lease-based with heartbeat to prevent deadlocks
- Automatic stale lock reaping (default: 5 minutes)
- Lock acquisition with timeout and retry

Usage:
    guard = MutexGuard(repository)
    async with guard.acquire_lock(asset_id, execution_id, timeout=30):
        # Execute operation on asset
        await perform_operation()
"""

import logging
import asyncio
from typing import Optional, List, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Raised when lock cannot be acquired"""
    pass


class MutexGuard:
    """
    Mutex guard to prevent concurrent modifications to assets.
    
    This is Safety Feature #2 and is critical for production deployment.
    """
    
    def __init__(
        self,
        repository: ExecutionRepository,
        default_lease_duration_seconds: int = 300,  # 5 minutes
        heartbeat_interval_seconds: int = 30,  # 30 seconds
        stale_lock_threshold_seconds: int = 600,  # 10 minutes
    ):
        """
        Initialize mutex guard.
        
        Args:
            repository: Execution repository for database access
            default_lease_duration_seconds: Default lease duration (default: 5 minutes)
            heartbeat_interval_seconds: Heartbeat interval (default: 30 seconds)
            stale_lock_threshold_seconds: Stale lock threshold (default: 10 minutes)
        """
        self.repository = repository
        self.default_lease_duration_seconds = default_lease_duration_seconds
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self.stale_lock_threshold_seconds = stale_lock_threshold_seconds
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}
    
    @asynccontextmanager
    async def acquire_lock(
        self,
        asset_id: str,
        execution_id: str,
        timeout_seconds: int = 30,
        retry_interval_seconds: int = 1,
    ):
        """
        Acquire lock on asset with automatic release.
        
        This is the main entry point for mutex locking.
        
        Args:
            asset_id: Asset ID to lock
            execution_id: Execution ID acquiring the lock
            timeout_seconds: Timeout for lock acquisition (default: 30 seconds)
            retry_interval_seconds: Retry interval (default: 1 second)
        
        Yields:
            None (lock is held during context)
        
        Raises:
            LockAcquisitionError: If lock cannot be acquired within timeout
        """
        lock_id = None
        heartbeat_task = None
        
        try:
            # Try to acquire lock with retries
            lock_id = await self._acquire_lock_with_retry(
                asset_id=asset_id,
                execution_id=execution_id,
                timeout_seconds=timeout_seconds,
                retry_interval_seconds=retry_interval_seconds,
            )
            
            logger.info(
                f"Lock acquired: lock_id={lock_id}, asset_id={asset_id}, "
                f"execution_id={execution_id}"
            )
            
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(lock_id, asset_id, execution_id)
            )
            self._heartbeat_tasks[lock_id] = heartbeat_task
            
            # Yield control to caller
            yield
            
        finally:
            # Stop heartbeat task
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_tasks.pop(lock_id, None)
            
            # Release lock
            if lock_id:
                await self._release_lock(lock_id, asset_id, execution_id)
    
    async def acquire_locks(
        self,
        asset_ids: List[str],
        execution_id: str,
        timeout_seconds: int = 30,
    ):
        """
        Acquire locks on multiple assets.
        
        This is used for executions that target multiple assets.
        Locks are acquired in sorted order to prevent deadlocks.
        
        Args:
            asset_ids: List of asset IDs to lock
            execution_id: Execution ID acquiring the locks
            timeout_seconds: Timeout for lock acquisition (default: 30 seconds)
        
        Yields:
            None (locks are held during context)
        
        Raises:
            LockAcquisitionError: If any lock cannot be acquired within timeout
        """
        # Sort asset IDs to prevent deadlocks
        sorted_asset_ids = sorted(set(asset_ids))
        
        logger.info(
            f"Acquiring locks on {len(sorted_asset_ids)} assets: "
            f"execution_id={execution_id}"
        )
        
        # Acquire locks one by one
        acquired_locks = []
        try:
            for asset_id in sorted_asset_ids:
                async with self.acquire_lock(
                    asset_id=asset_id,
                    execution_id=execution_id,
                    timeout_seconds=timeout_seconds,
                ):
                    acquired_locks.append(asset_id)
                    yield
        finally:
            logger.info(
                f"Released {len(acquired_locks)} locks: execution_id={execution_id}"
            )
    
    async def _acquire_lock_with_retry(
        self,
        asset_id: str,
        execution_id: str,
        timeout_seconds: int,
        retry_interval_seconds: int,
    ) -> str:
        """
        Acquire lock with retries.
        
        Args:
            asset_id: Asset ID to lock
            execution_id: Execution ID acquiring the lock
            timeout_seconds: Timeout for lock acquisition
            retry_interval_seconds: Retry interval
        
        Returns:
            Lock ID
        
        Raises:
            LockAcquisitionError: If lock cannot be acquired within timeout
        """
        start_time = datetime.utcnow()
        deadline = start_time + timedelta(seconds=timeout_seconds)
        attempt = 0
        
        while datetime.utcnow() < deadline:
            attempt += 1
            
            # Try to acquire lock
            lock_id = self.repository.acquire_lock(
                asset_id=asset_id,
                execution_id=execution_id,
                lease_duration_seconds=self.default_lease_duration_seconds,
            )
            
            if lock_id:
                logger.info(
                    f"Lock acquired on attempt {attempt}: lock_id={lock_id}, "
                    f"asset_id={asset_id}"
                )
                return lock_id
            
            # Check if lock is stale and reap if necessary
            await self._reap_stale_locks_for_asset(asset_id)
            
            # Wait before retry
            remaining_time = (deadline - datetime.utcnow()).total_seconds()
            wait_time = min(retry_interval_seconds, remaining_time)
            
            if wait_time > 0:
                logger.debug(
                    f"Lock acquisition failed, retrying in {wait_time}s: "
                    f"asset_id={asset_id}, attempt={attempt}"
                )
                await asyncio.sleep(wait_time)
        
        # Timeout reached
        raise LockAcquisitionError(
            f"Failed to acquire lock on asset {asset_id} within {timeout_seconds}s "
            f"after {attempt} attempts"
        )
    
    async def _release_lock(
        self,
        lock_id: str,
        asset_id: str,
        execution_id: str,
    ) -> None:
        """
        Release lock.
        
        Args:
            lock_id: Lock ID
            asset_id: Asset ID
            execution_id: Execution ID
        """
        try:
            self.repository.release_lock(lock_id)
            logger.info(
                f"Lock released: lock_id={lock_id}, asset_id={asset_id}, "
                f"execution_id={execution_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to release lock: lock_id={lock_id}, asset_id={asset_id}, "
                f"execution_id={execution_id}, error={e}"
            )
    
    async def _heartbeat_loop(
        self,
        lock_id: str,
        asset_id: str,
        execution_id: str,
    ) -> None:
        """
        Heartbeat loop to keep lock alive.
        
        Args:
            lock_id: Lock ID
            asset_id: Asset ID
            execution_id: Execution ID
        """
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval_seconds)
                
                # Send heartbeat
                success = self.repository.heartbeat_lock(lock_id)
                
                if success:
                    logger.debug(
                        f"Lock heartbeat sent: lock_id={lock_id}, asset_id={asset_id}"
                    )
                else:
                    logger.error(
                        f"Lock heartbeat failed: lock_id={lock_id}, asset_id={asset_id}"
                    )
                    break
        except asyncio.CancelledError:
            logger.debug(f"Heartbeat loop cancelled: lock_id={lock_id}")
            raise
        except Exception as e:
            logger.error(
                f"Heartbeat loop error: lock_id={lock_id}, error={e}"
            )
    
    async def _reap_stale_locks_for_asset(self, asset_id: str) -> None:
        """
        Reap stale locks for a specific asset.
        
        Args:
            asset_id: Asset ID
        """
        try:
            reaped = self.repository.reap_stale_locks(
                threshold_seconds=self.stale_lock_threshold_seconds,
                asset_id=asset_id,
            )
            
            if reaped > 0:
                logger.warning(
                    f"Reaped {reaped} stale locks for asset {asset_id}"
                )
        except Exception as e:
            logger.error(
                f"Failed to reap stale locks for asset {asset_id}: {e}"
            )
    
    async def reap_all_stale_locks(self) -> int:
        """
        Reap all stale locks across all assets.
        
        This should be called periodically by a background task.
        
        Returns:
            Number of locks reaped
        """
        try:
            reaped = self.repository.reap_stale_locks(
                threshold_seconds=self.stale_lock_threshold_seconds,
            )
            
            if reaped > 0:
                logger.warning(f"Reaped {reaped} stale locks")
            
            return reaped
        except Exception as e:
            logger.error(f"Failed to reap stale locks: {e}")
            return 0
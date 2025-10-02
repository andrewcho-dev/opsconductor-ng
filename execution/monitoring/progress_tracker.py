"""
Progress Tracker - Real-time execution progress tracking
Tracks execution progress, step completion, and emits progress events
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

from execution.models import ExecutionStatus
from execution.repository import ExecutionRepository


logger = logging.getLogger(__name__)


# ============================================================================
# MODELS
# ============================================================================

class StepProgress(BaseModel):
    """Progress information for a single step"""
    step_id: UUID
    step_index: int
    step_name: str
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    error_message: Optional[str] = None


class ExecutionProgress(BaseModel):
    """Overall execution progress"""
    execution_id: UUID
    status: ExecutionStatus
    total_steps: int
    completed_steps: int
    failed_steps: int
    running_steps: int
    pending_steps: int
    progress_percent: int = Field(default=0, ge=0, le=100)
    current_step: Optional[StepProgress] = None
    steps: List[StepProgress] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    elapsed_ms: Optional[int] = None
    
    def calculate_progress(self) -> int:
        """Calculate overall progress percentage"""
        if self.total_steps == 0:
            return 0
        return int((self.completed_steps / self.total_steps) * 100)


# ============================================================================
# PROGRESS TRACKER
# ============================================================================

class ProgressTracker:
    """
    Tracks execution progress in real-time
    
    Features:
    - Step-level progress tracking
    - Overall execution progress calculation
    - Progress event emission
    - Estimated completion time
    - Real-time progress updates
    """
    
    def __init__(self, repository: ExecutionRepository):
        self.repository = repository
        self._progress_cache: Dict[UUID, ExecutionProgress] = {}
        self._lock = asyncio.Lock()
        logger.info("ProgressTracker initialized")
    
    async def get_progress(self, execution_id: UUID) -> Optional[ExecutionProgress]:
        """
        Get current execution progress
        
        Args:
            execution_id: Execution ID
            
        Returns:
            ExecutionProgress or None if not found
        """
        try:
            # Check cache first
            if execution_id in self._progress_cache:
                cached = self._progress_cache[execution_id]
                # Return cached if recent (< 5 seconds old)
                if cached.status in [ExecutionStatus.RUNNING, ExecutionStatus.QUEUED]:
                    return cached
            
            # Fetch from database
            execution = await self.repository.get_execution(execution_id)
            if not execution:
                logger.warning(f"Execution not found: {execution_id}")
                return None
            
            steps = await self.repository.get_execution_steps(execution_id)
            
            # Build step progress
            step_progress_list = []
            completed = 0
            failed = 0
            running = 0
            pending = 0
            current_step = None
            
            for step in steps:
                step_prog = StepProgress(
                    step_id=step.step_id,
                    step_index=step.step_index,
                    step_name=step.step_name,
                    status=step.status,
                    started_at=step.started_at,
                    completed_at=step.completed_at,
                    duration_ms=step.duration_ms,
                    progress_percent=self._calculate_step_progress(step.status),
                    error_message=step.error_message,
                )
                step_progress_list.append(step_prog)
                
                # Count by status
                if step.status == ExecutionStatus.COMPLETED:
                    completed += 1
                elif step.status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]:
                    failed += 1
                elif step.status == ExecutionStatus.RUNNING:
                    running += 1
                    current_step = step_prog
                else:
                    pending += 1
            
            # Calculate elapsed time
            elapsed_ms = None
            if execution.started_at:
                if execution.completed_at:
                    elapsed_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
                else:
                    elapsed_ms = int((datetime.utcnow() - execution.started_at).total_seconds() * 1000)
            
            # Build overall progress
            progress = ExecutionProgress(
                execution_id=execution_id,
                status=execution.status,
                total_steps=len(steps),
                completed_steps=completed,
                failed_steps=failed,
                running_steps=running,
                pending_steps=pending,
                steps=step_progress_list,
                current_step=current_step,
                started_at=execution.started_at,
                elapsed_ms=elapsed_ms,
            )
            
            # Calculate progress percentage
            progress.progress_percent = progress.calculate_progress()
            
            # Estimate completion time
            if progress.progress_percent > 0 and progress.elapsed_ms and progress.status == ExecutionStatus.RUNNING:
                estimated_total_ms = (progress.elapsed_ms / progress.progress_percent) * 100
                remaining_ms = estimated_total_ms - progress.elapsed_ms
                from datetime import timedelta
                progress.estimated_completion = datetime.utcnow() + timedelta(milliseconds=remaining_ms)
            
            # Cache the progress
            async with self._lock:
                self._progress_cache[execution_id] = progress
            
            logger.debug(f"Progress for {execution_id}: {progress.progress_percent}% ({completed}/{len(steps)} steps)")
            return progress
            
        except Exception as e:
            logger.error(f"Error getting progress for {execution_id}: {e}", exc_info=True)
            return None
    
    async def update_step_progress(
        self,
        execution_id: UUID,
        step_id: UUID,
        status: ExecutionStatus,
        progress_percent: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update progress for a specific step
        
        Args:
            execution_id: Execution ID
            step_id: Step ID
            status: New status
            progress_percent: Optional progress percentage (0-100)
            error_message: Optional error message
            
        Returns:
            True if updated successfully
        """
        try:
            # Update step in database
            update_data = {"status": status}
            if error_message:
                update_data["error_message"] = error_message
            
            success = await self.repository.update_step(step_id, update_data)
            if not success:
                logger.warning(f"Failed to update step {step_id}")
                return False
            
            # Invalidate cache to force refresh
            async with self._lock:
                if execution_id in self._progress_cache:
                    del self._progress_cache[execution_id]
            
            logger.debug(f"Updated step {step_id} progress: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating step progress: {e}", exc_info=True)
            return False
    
    async def mark_step_started(self, execution_id: UUID, step_id: UUID) -> bool:
        """Mark a step as started"""
        try:
            update_data = {
                "status": ExecutionStatus.RUNNING,
                "started_at": datetime.utcnow(),
            }
            success = await self.repository.update_step(step_id, update_data)
            
            # Invalidate cache
            async with self._lock:
                if execution_id in self._progress_cache:
                    del self._progress_cache[execution_id]
            
            return success
        except Exception as e:
            logger.error(f"Error marking step started: {e}", exc_info=True)
            return False
    
    async def mark_step_completed(
        self,
        execution_id: UUID,
        step_id: UUID,
        status: ExecutionStatus,
        duration_ms: int,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Mark a step as completed (success or failure)"""
        try:
            update_data = {
                "status": status,
                "completed_at": datetime.utcnow(),
                "duration_ms": duration_ms,
            }
            if output_data:
                update_data["output_data"] = output_data
            if error_message:
                update_data["error_message"] = error_message
            
            success = await self.repository.update_step(step_id, update_data)
            
            # Invalidate cache
            async with self._lock:
                if execution_id in self._progress_cache:
                    del self._progress_cache[execution_id]
            
            return success
        except Exception as e:
            logger.error(f"Error marking step completed: {e}", exc_info=True)
            return False
    
    async def get_active_executions(self) -> List[ExecutionProgress]:
        """Get progress for all active executions"""
        try:
            # Get all running/queued executions
            executions = await self.repository.list_executions(
                status=[ExecutionStatus.RUNNING, ExecutionStatus.QUEUED],
                limit=100,
            )
            
            progress_list = []
            for execution in executions:
                progress = await self.get_progress(execution.execution_id)
                if progress:
                    progress_list.append(progress)
            
            return progress_list
            
        except Exception as e:
            logger.error(f"Error getting active executions: {e}", exc_info=True)
            return []
    
    async def clear_cache(self, execution_id: Optional[UUID] = None):
        """Clear progress cache"""
        async with self._lock:
            if execution_id:
                self._progress_cache.pop(execution_id, None)
            else:
                self._progress_cache.clear()
    
    def _calculate_step_progress(self, status: ExecutionStatus) -> int:
        """Calculate progress percentage for a step based on status"""
        if status == ExecutionStatus.COMPLETED:
            return 100
        elif status == ExecutionStatus.RUNNING:
            return 50
        elif status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT, ExecutionStatus.CANCELLED]:
            return 100  # Completed (but not successfully)
        else:
            return 0
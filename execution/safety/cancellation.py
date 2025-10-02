"""
Cancellation Manager - Safety Feature #5

Cooperative cancellation with cleanup:
- User-initiated cancellation (stop button in UI)
- Timeout-based cancellation (SLA exceeded)
- System-initiated cancellation (worker shutdown, resource limits)
- Cleanup of partial state (rollback, resource release)

Implementation:
- Cancellation token pattern for cooperative cancellation
- Cleanup handlers for each step type
- Graceful shutdown with timeout
- Audit trail for all cancellations

Usage:
    manager = CancellationManager(repository)
    token = manager.create_token(execution_id)
    
    # In execution loop:
    if token.is_cancelled():
        await manager.cleanup(execution_id)
        return
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

from execution.models import ExecutionStatus
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class CancellationReason(str, Enum):
    """Cancellation reason types"""
    USER_INITIATED = "user_initiated"
    TIMEOUT = "timeout"
    SYSTEM_SHUTDOWN = "system_shutdown"
    RESOURCE_LIMIT = "resource_limit"
    ERROR = "error"
    DUPLICATE = "duplicate"


class CancellationToken:
    """
    Cancellation token for cooperative cancellation.
    
    This is similar to .NET's CancellationToken pattern.
    """
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self._cancelled = False
        self._reason: Optional[CancellationReason] = None
        self._message: Optional[str] = None
        self._callbacks: List[Callable] = []
    
    def cancel(
        self,
        reason: CancellationReason,
        message: Optional[str] = None,
    ) -> None:
        """
        Cancel the token.
        
        Args:
            reason: Cancellation reason
            message: Optional cancellation message
        """
        if self._cancelled:
            return
        
        self._cancelled = True
        self._reason = reason
        self._message = message
        
        logger.info(
            f"Cancellation token cancelled: execution_id={self.execution_id}, "
            f"reason={reason}, message={message}"
        )
        
        # Invoke callbacks
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(
                    f"Cancellation callback error: execution_id={self.execution_id}, "
                    f"error={e}"
                )
    
    def is_cancelled(self) -> bool:
        """Check if token is cancelled"""
        return self._cancelled
    
    def throw_if_cancelled(self) -> None:
        """Throw exception if token is cancelled"""
        if self._cancelled:
            raise asyncio.CancelledError(
                f"Execution cancelled: {self._reason} - {self._message}"
            )
    
    def register_callback(self, callback: Callable) -> None:
        """
        Register callback to be invoked when token is cancelled.
        
        Args:
            callback: Callback function
        """
        self._callbacks.append(callback)
    
    @property
    def reason(self) -> Optional[CancellationReason]:
        """Get cancellation reason"""
        return self._reason
    
    @property
    def message(self) -> Optional[str]:
        """Get cancellation message"""
        return self._message


class CancellationManager:
    """
    Cancellation manager for cooperative cancellation.
    
    This is Safety Feature #5 and is critical for production deployment.
    """
    
    def __init__(
        self,
        repository: ExecutionRepository,
        cleanup_timeout_seconds: int = 30,
    ):
        """
        Initialize cancellation manager.
        
        Args:
            repository: Execution repository for database access
            cleanup_timeout_seconds: Timeout for cleanup operations (default: 30 seconds)
        """
        self.repository = repository
        self.cleanup_timeout_seconds = cleanup_timeout_seconds
        self._tokens: Dict[str, CancellationToken] = {}
        self._cleanup_handlers: Dict[str, Callable] = {}
    
    def create_token(self, execution_id: str) -> CancellationToken:
        """
        Create cancellation token for execution.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Cancellation token
        """
        if execution_id in self._tokens:
            return self._tokens[execution_id]
        
        token = CancellationToken(execution_id)
        self._tokens[execution_id] = token
        
        logger.debug(f"Created cancellation token: execution_id={execution_id}")
        
        return token
    
    def get_token(self, execution_id: str) -> Optional[CancellationToken]:
        """
        Get cancellation token for execution.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Cancellation token if exists, None otherwise
        """
        return self._tokens.get(execution_id)
    
    async def cancel_execution(
        self,
        execution_id: str,
        reason: CancellationReason,
        message: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> None:
        """
        Cancel execution.
        
        This is the main entry point for cancellation.
        
        Args:
            execution_id: Execution ID
            reason: Cancellation reason
            message: Optional cancellation message
            actor_id: Actor who initiated cancellation (for user-initiated)
        """
        logger.info(
            f"Cancelling execution: execution_id={execution_id}, reason={reason}, "
            f"message={message}, actor_id={actor_id}"
        )
        
        # Get or create token
        token = self.get_token(execution_id)
        if not token:
            token = self.create_token(execution_id)
        
        # Cancel token
        token.cancel(reason=reason, message=message)
        
        # Update execution status
        self.repository.update_execution_status(
            execution_id=execution_id,
            status=ExecutionStatus.CANCELLED,
            error_message=f"{reason}: {message}" if message else str(reason),
        )
        
        # Add event to audit trail
        self.repository.create_execution_event(
            execution_id=execution_id,
            event_type="execution_cancelled",
            event_data={
                "reason": reason,
                "message": message,
                "actor_id": actor_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        # Trigger cleanup
        await self.cleanup(execution_id)
    
    async def cleanup(self, execution_id: str) -> None:
        """
        Cleanup execution resources.
        
        This should be called when execution is cancelled or fails.
        
        Args:
            execution_id: Execution ID
        """
        logger.info(f"Starting cleanup: execution_id={execution_id}")
        
        try:
            # Run cleanup with timeout
            await asyncio.wait_for(
                self._run_cleanup(execution_id),
                timeout=self.cleanup_timeout_seconds,
            )
            
            logger.info(f"Cleanup completed: execution_id={execution_id}")
            
            # Update execution status to CANCELLED
            self.repository.update_execution_status(
                execution_id=execution_id,
                status=ExecutionStatus.CANCELLED,
            )
        except asyncio.TimeoutError:
            logger.error(
                f"Cleanup timeout: execution_id={execution_id}, "
                f"timeout={self.cleanup_timeout_seconds}s"
            )
            
            # Update execution status to FAILED
            self.repository.update_execution_status(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error_message=f"Cleanup timeout after {self.cleanup_timeout_seconds}s",
            )
        except Exception as e:
            logger.error(
                f"Cleanup error: execution_id={execution_id}, error={e}"
            )
            
            # Update execution status to FAILED
            self.repository.update_execution_status(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error_message=f"Cleanup error: {e}",
            )
        finally:
            # Remove token
            self._tokens.pop(execution_id, None)
    
    async def _run_cleanup(self, execution_id: str) -> None:
        """
        Run cleanup handlers.
        
        Args:
            execution_id: Execution ID
        """
        # Get execution
        execution = self.repository.get_execution(execution_id)
        if not execution:
            logger.warning(f"Execution not found: execution_id={execution_id}")
            return
        
        # Get execution steps
        steps = self.repository.get_execution_steps(execution_id)
        
        # Run cleanup for each step in reverse order
        for step in reversed(steps):
            if step.status in [ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING]:
                await self._cleanup_step(execution_id, step.step_id, step.step_data)
        
        # Run custom cleanup handler if registered
        if execution_id in self._cleanup_handlers:
            handler = self._cleanup_handlers[execution_id]
            try:
                await handler()
            except Exception as e:
                logger.error(
                    f"Custom cleanup handler error: execution_id={execution_id}, "
                    f"error={e}"
                )
    
    async def _cleanup_step(
        self,
        execution_id: str,
        step_id: str,
        step_data: Dict[str, Any],
    ) -> None:
        """
        Cleanup a specific step.
        
        Args:
            execution_id: Execution ID
            step_id: Step ID
            step_data: Step data
        """
        logger.debug(
            f"Cleaning up step: execution_id={execution_id}, step_id={step_id}"
        )
        
        # TODO: Implement step-specific cleanup logic
        # This depends on the step type:
        # - For deployments: rollback to previous version
        # - For config changes: revert to previous config
        # - For resource creation: delete created resources
        # - For service restarts: ensure service is running
        
        # Add event to audit trail
        self.repository.create_execution_event(
            execution_id=execution_id,
            event_type="step_cleanup",
            event_data={
                "step_id": step_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    
    def register_cleanup_handler(
        self,
        execution_id: str,
        handler: Callable,
    ) -> None:
        """
        Register custom cleanup handler for execution.
        
        Args:
            execution_id: Execution ID
            handler: Cleanup handler function
        """
        self._cleanup_handlers[execution_id] = handler
        logger.debug(
            f"Registered cleanup handler: execution_id={execution_id}"
        )
    
    async def cancel_all_executions(
        self,
        reason: CancellationReason = CancellationReason.SYSTEM_SHUTDOWN,
        message: str = "System shutdown",
    ) -> None:
        """
        Cancel all running executions.
        
        This should be called during graceful shutdown.
        
        Args:
            reason: Cancellation reason
            message: Cancellation message
        """
        logger.warning(
            f"Cancelling all executions: reason={reason}, message={message}"
        )
        
        # Get all execution IDs with tokens
        execution_ids = list(self._tokens.keys())
        
        # Cancel all executions
        for execution_id in execution_ids:
            try:
                await self.cancel_execution(
                    execution_id=execution_id,
                    reason=reason,
                    message=message,
                )
            except Exception as e:
                logger.error(
                    f"Failed to cancel execution: execution_id={execution_id}, "
                    f"error={e}"
                )
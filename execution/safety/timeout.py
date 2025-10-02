"""
Timeout Enforcer - Safety Feature #6

SLA-based timeout enforcement:
- Prevents runaway executions
- Different timeouts for different SLA classes (fast/medium/long)
- Different timeouts for different action classes (read/write/complex)
- Automatic cancellation when timeout is exceeded

Implementation:
- Timeout policy matrix: 3 SLA classes × 3 action classes = 9 policies
- Per-step timeouts with aggregation
- Execution-level timeout (sum of step timeouts + buffer)
- Automatic cancellation with cleanup

Usage:
    enforcer = TimeoutEnforcer(repository, cancellation_manager)
    await enforcer.enforce_timeout(execution_id, timeout_seconds=300)
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from execution.models import ExecutionModel, SLAClass, TimeoutPolicyModel
from execution.repository import ExecutionRepository
from execution.safety.cancellation import CancellationManager, CancellationReason

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when execution times out"""
    pass


class TimeoutEnforcer:
    """
    Timeout enforcer for SLA-based timeout enforcement.
    
    This is Safety Feature #6 and is critical for production deployment.
    """
    
    def __init__(
        self,
        repository: ExecutionRepository,
        cancellation_manager: CancellationManager,
        buffer_percentage: float = 0.1,  # 10% buffer
    ):
        """
        Initialize timeout enforcer.
        
        Args:
            repository: Execution repository for database access
            cancellation_manager: Cancellation manager for cancellation
            buffer_percentage: Buffer percentage for execution timeout (default: 10%)
        """
        self.repository = repository
        self.cancellation_manager = cancellation_manager
        self.buffer_percentage = buffer_percentage
        self._timeout_tasks: Dict[str, asyncio.Task] = {}
    
    async def enforce_timeout(
        self,
        execution_id: str,
        timeout_seconds: Optional[int] = None,
    ) -> None:
        """
        Enforce timeout for execution.
        
        This starts a background task that monitors execution time.
        
        Args:
            execution_id: Execution ID
            timeout_seconds: Timeout in seconds (if None, calculated from SLA class)
        """
        # Get execution
        execution = self.repository.get_execution(execution_id)
        if not execution:
            logger.error(f"Execution not found: execution_id={execution_id}")
            return
        
        # Calculate timeout if not provided
        if timeout_seconds is None:
            timeout_seconds = await self._calculate_execution_timeout(execution)
        
        logger.info(
            f"Enforcing timeout: execution_id={execution_id}, "
            f"timeout={timeout_seconds}s"
        )
        
        # Start timeout task
        task = asyncio.create_task(
            self._timeout_monitor(execution_id, timeout_seconds)
        )
        self._timeout_tasks[execution_id] = task
    
    async def cancel_timeout(self, execution_id: str) -> None:
        """
        Cancel timeout enforcement for execution.
        
        This should be called when execution completes normally.
        
        Args:
            execution_id: Execution ID
        """
        task = self._timeout_tasks.pop(execution_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            logger.debug(f"Timeout enforcement cancelled: execution_id={execution_id}")
    
    async def _timeout_monitor(
        self,
        execution_id: str,
        timeout_seconds: int,
    ) -> None:
        """
        Monitor execution timeout.
        
        Args:
            execution_id: Execution ID
            timeout_seconds: Timeout in seconds
        """
        try:
            # Wait for timeout
            await asyncio.sleep(timeout_seconds)
            
            # Check if execution is still running
            execution = self.repository.get_execution(execution_id)
            if not execution:
                return
            
            if execution.status in ["running", "pending", "queued"]:
                logger.error(
                    f"Execution timeout: execution_id={execution_id}, "
                    f"timeout={timeout_seconds}s, status={execution.status}"
                )
                
                # Cancel execution
                await self.cancellation_manager.cancel_execution(
                    execution_id=execution_id,
                    reason=CancellationReason.TIMEOUT,
                    message=f"Execution exceeded timeout of {timeout_seconds}s",
                )
        except asyncio.CancelledError:
            logger.debug(f"Timeout monitor cancelled: execution_id={execution_id}")
            raise
        except Exception as e:
            logger.error(
                f"Timeout monitor error: execution_id={execution_id}, error={e}"
            )
        finally:
            self._timeout_tasks.pop(execution_id, None)
    
    async def _calculate_execution_timeout(
        self,
        execution: ExecutionModel,
    ) -> int:
        """
        Calculate execution timeout based on SLA class and steps.
        
        Args:
            execution: Execution model
        
        Returns:
            Timeout in seconds
        """
        # Get steps
        steps = self.repository.get_execution_steps(execution.execution_id)
        
        # Calculate total timeout from steps
        total_timeout = 0
        for step in steps:
            step_timeout = await self._calculate_step_timeout(
                step_data=step.step_data,
                sla_class=execution.sla_class,
            )
            total_timeout += step_timeout
        
        # Add buffer
        buffer = int(total_timeout * self.buffer_percentage)
        total_timeout += buffer
        
        # Ensure minimum timeout
        min_timeout = self._get_min_timeout_for_sla(execution.sla_class)
        total_timeout = max(total_timeout, min_timeout)
        
        logger.debug(
            f"Calculated execution timeout: execution_id={execution.execution_id}, "
            f"timeout={total_timeout}s, sla_class={execution.sla_class}, "
            f"steps={len(steps)}, buffer={buffer}s"
        )
        
        return total_timeout
    
    async def _calculate_step_timeout(
        self,
        step_data: Dict[str, Any],
        sla_class: SLAClass,
    ) -> int:
        """
        Calculate step timeout based on action class and SLA class.
        
        Args:
            step_data: Step data
            sla_class: SLA class
        
        Returns:
            Timeout in seconds
        """
        # Determine action class from step data
        action_class = self._determine_action_class(step_data)
        
        # Get timeout policy
        policy = self.repository.get_timeout_policy(
            sla_class=sla_class,
            action_class=action_class,
        )
        
        if policy:
            return policy.timeout_seconds
        
        # Fallback to default timeout
        return self._get_default_timeout(sla_class, action_class)
    
    def _determine_action_class(self, step_data: Dict[str, Any]) -> str:
        """
        Determine action class from step data.
        
        Args:
            step_data: Step data
        
        Returns:
            Action class (read/write/complex)
        """
        # TODO: Implement actual action class determination
        # This should analyze the step type and parameters
        
        action = step_data.get("action", "")
        
        # Simple heuristic
        if any(keyword in action.lower() for keyword in ["read", "get", "list", "describe"]):
            return "read"
        elif any(keyword in action.lower() for keyword in ["deploy", "migrate", "backup", "restore"]):
            return "complex"
        else:
            return "write"
    
    def _get_min_timeout_for_sla(self, sla_class: SLAClass) -> int:
        """
        Get minimum timeout for SLA class.
        
        Args:
            sla_class: SLA class
        
        Returns:
            Minimum timeout in seconds
        """
        if sla_class == SLAClass.FAST:
            return 10  # 10 seconds
        elif sla_class == SLAClass.MEDIUM:
            return 30  # 30 seconds
        elif sla_class == SLAClass.LONG:
            return 60  # 60 seconds
        else:
            return 30  # Default
    
    def _get_default_timeout(self, sla_class: SLAClass, action_class: str) -> int:
        """
        Get default timeout for SLA class and action class.
        
        Args:
            sla_class: SLA class
            action_class: Action class
        
        Returns:
            Default timeout in seconds
        """
        # Default timeout matrix
        timeouts = {
            (SLAClass.FAST, "read"): 10,
            (SLAClass.FAST, "write"): 30,
            (SLAClass.FAST, "complex"): 60,
            (SLAClass.MEDIUM, "read"): 30,
            (SLAClass.MEDIUM, "write"): 60,
            (SLAClass.MEDIUM, "complex"): 180,
            (SLAClass.LONG, "read"): 60,
            (SLAClass.LONG, "write"): 180,
            (SLAClass.LONG, "complex"): 600,
        }
        
        return timeouts.get((sla_class, action_class), 60)
    
    async def get_remaining_time(self, execution_id: str) -> Optional[int]:
        """
        Get remaining time for execution.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Remaining time in seconds, or None if no timeout is enforced
        """
        # Get execution
        execution = self.repository.get_execution(execution_id)
        if not execution:
            return None
        
        # Calculate elapsed time
        elapsed = (datetime.utcnow() - execution.created_at).total_seconds()
        
        # Calculate total timeout
        total_timeout = await self._calculate_execution_timeout(execution)
        
        # Calculate remaining time
        remaining = int(total_timeout - elapsed)
        
        return max(0, remaining)
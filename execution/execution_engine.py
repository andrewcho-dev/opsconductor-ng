"""
Phase 7: Execution Engine
Core execution logic with step-by-step execution and progress tracking
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from execution.dtos import ExecutionResult, StepExecutionResult
from execution.models import (
    ExecutionModel,
    ExecutionStatus,
    ExecutionStepModel,
)
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Execution Engine - Core execution logic
    
    Responsibilities:
    1. Step-by-step execution
    2. Progress tracking
    3. Error handling and retry logic
    4. Result aggregation
    """
    
    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        redis_url: Optional[str] = None
    ):
        """Initialize Execution Engine"""
        self.db_connection_string = db_connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"
        )
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Initialize repository
        self.repository = ExecutionRepository(self.db_connection_string)
        
        logger.info("ExecutionEngine initialized")
    
    async def execute(self, execution: ExecutionModel) -> ExecutionResult:
        """
        Execute a plan step-by-step
        
        Args:
            execution: Execution model
        
        Returns:
            ExecutionResult with execution details
        """
        started_at = datetime.utcnow()
        step_results: List[Dict[str, Any]] = []
        
        try:
            logger.info(f"Starting execution: {execution.execution_id}")
            
            # Step 1: Create execution steps from plan
            steps = await self._create_execution_steps(execution)
            
            logger.info(
                f"Created {len(steps)} execution steps for {execution.execution_id}"
            )
            
            # Step 2: Execute steps sequentially
            for step in steps:
                try:
                    step_result = await self._execute_step(step, execution)
                    step_results.append({
                        "step_id": str(step.step_id),
                        "step_name": step.step_name,
                        "status": step_result.status.value,
                        "duration_ms": step_result.duration_ms,
                        "output_data": step_result.output_data,
                    })
                    
                    # Check if step failed
                    if step_result.status == ExecutionStatus.FAILED:
                        logger.warning(
                            f"Step failed: {step.step_id}, "
                            f"error={step_result.error_message}"
                        )
                        # Continue to next step (partial execution)
                
                except Exception as e:
                    logger.error(
                        f"Step execution error: {step.step_id}, error={e}",
                        exc_info=True
                    )
                    step_results.append({
                        "step_id": str(step.step_id),
                        "step_name": step.step_name,
                        "status": ExecutionStatus.FAILED.value,
                        "error_message": str(e),
                    })
            
            # Step 3: Determine final status
            final_status = self._determine_final_status(step_results)
            
            # Step 4: Build result
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()
            
            result = ExecutionResult(
                execution_id=execution.execution_id,
                status=final_status,
                result={
                    "total_steps": len(steps),
                    "completed_steps": sum(
                        1 for r in step_results
                        if r.get("status") == ExecutionStatus.COMPLETED.value
                    ),
                    "failed_steps": sum(
                        1 for r in step_results
                        if r.get("status") == ExecutionStatus.FAILED.value
                    ),
                },
                step_results=step_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
            )
            
            logger.info(
                f"Execution completed: {execution.execution_id}, "
                f"status={final_status}, duration={duration_seconds}s"
            )
            
            return result
        
        except Exception as e:
            logger.error(
                f"Execution failed: {execution.execution_id}, error={e}",
                exc_info=True
            )
            
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()
            
            return ExecutionResult(
                execution_id=execution.execution_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                error_details={"exception": type(e).__name__},
                step_results=step_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
            )
    
    async def _create_execution_steps(
        self,
        execution: ExecutionModel
    ) -> List[ExecutionStepModel]:
        """
        Create execution steps from plan
        
        Args:
            execution: Execution model
        
        Returns:
            List of ExecutionStepModel
        """
        steps: List[ExecutionStepModel] = []
        plan_steps = execution.plan_snapshot.get("steps", [])
        
        for index, plan_step in enumerate(plan_steps):
            step = ExecutionStepModel(
                execution_id=execution.execution_id,
                step_index=index,
                step_name=plan_step.get("name", f"Step {index + 1}"),
                step_type=plan_step.get("type", "unknown"),
                target_asset_id=plan_step.get("target_asset_id"),
                target_hostname=plan_step.get("target_hostname"),
                input_data=plan_step.get("input_data", {}),
                trace_id=execution.trace_id,
            )
            
            # Save step to database
            step = self.repository.create_execution_step(step)
            steps.append(step)
        
        return steps
    
    async def _execute_step(
        self,
        step: ExecutionStepModel,
        execution: ExecutionModel
    ) -> StepExecutionResult:
        """
        Execute a single step
        
        Args:
            step: Execution step model
            execution: Execution model
        
        Returns:
            StepExecutionResult
        """
        started_at = datetime.utcnow()
        
        try:
            logger.info(
                f"Executing step: {step.step_id}, "
                f"name={step.step_name}, type={step.step_type}"
            )
            
            # Update step status to running
            self.repository.update_step_status(
                step.step_id,
                ExecutionStatus.RUNNING
            )
            
            # Execute step based on type
            output_data = await self._execute_step_by_type(step, execution)
            
            # Update step status to completed
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            self.repository.update_step_status(
                step.step_id,
                ExecutionStatus.COMPLETED,
                output_data=output_data,
                duration_ms=duration_ms
            )
            
            logger.info(
                f"Step completed: {step.step_id}, duration={duration_ms}ms"
            )
            
            return StepExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.COMPLETED,
                output_data=output_data,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )
        
        except Exception as e:
            logger.error(
                f"Step failed: {step.step_id}, error={e}",
                exc_info=True
            )
            
            # Update step status to failed
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            self.repository.update_step_status(
                step.step_id,
                ExecutionStatus.FAILED,
                error_message=str(e),
                duration_ms=duration_ms
            )
            
            return StepExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                error_details={"exception": type(e).__name__},
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )
    
    async def _execute_step_by_type(
        self,
        step: ExecutionStepModel,
        execution: ExecutionModel
    ) -> Dict[str, Any]:
        """
        Execute step based on step type
        
        Args:
            step: Execution step model
            execution: Execution model
        
        Returns:
            Output data
        """
        # TODO: Implement actual step execution based on step type
        # For now, return mock data
        
        logger.info(
            f"Executing step type: {step.step_type} (mock implementation)"
        )
        
        # Simulate execution delay
        import asyncio
        await asyncio.sleep(0.1)
        
        # Return mock output
        return {
            "status": "success",
            "message": f"Step {step.step_name} executed successfully (mock)",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _determine_final_status(
        self,
        step_results: List[Dict[str, Any]]
    ) -> ExecutionStatus:
        """
        Determine final execution status based on step results
        
        Args:
            step_results: List of step results
        
        Returns:
            Final execution status
        """
        if not step_results:
            return ExecutionStatus.COMPLETED
        
        failed_count = sum(
            1 for r in step_results
            if r.get("status") == ExecutionStatus.FAILED.value
        )
        completed_count = sum(
            1 for r in step_results
            if r.get("status") == ExecutionStatus.COMPLETED.value
        )
        
        if failed_count == 0:
            return ExecutionStatus.COMPLETED
        elif completed_count == 0:
            return ExecutionStatus.FAILED
        else:
            return ExecutionStatus.PARTIAL
"""
Execution Coordinator - Managing Workflow Execution

Coordinates the execution of workflows with the automation service,
handles progress tracking, error handling, and provides real-time feedback.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .workflow_planner import Workflow, WorkflowStep

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status for workflows and steps"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class StepExecutionResult:
    """Result of executing a single workflow step"""
    step_id: str
    status: ExecutionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    exit_code: Optional[int] = None
    execution_id: Optional[str] = None
    job_id: Optional[int] = None
    job_name: Optional[str] = None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class WorkflowExecutionResult:
    """Result of executing a complete workflow"""
    workflow_id: str
    status: ExecutionStatus
    steps_completed: int
    total_steps: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    step_results: List[StepExecutionResult] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    logs: List[str] = None
    job_details: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.step_results is None:
            self.step_results = []
        if self.logs is None:
            self.logs = []
        if self.job_details is None:
            self.job_details = []
    
    @property
    def success(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class ExecutionCoordinator:
    """
    Execution Coordinator - Manages workflow execution
    
    Coordinates with the automation service to execute workflows,
    handles dependencies, progress tracking, and error recovery.
    """
    
    def __init__(self, automation_client=None):
        """Initialize the Execution Coordinator"""
        self.automation_client = automation_client
        self.active_executions: Dict[str, WorkflowExecutionResult] = {}
        
        logger.info("Execution Coordinator initialized")
    
    async def execute_workflow(self, workflow: Workflow, progress_callback: Optional[Callable] = None) -> WorkflowExecutionResult:
        """
        Execute a complete workflow
        
        Args:
            workflow: Workflow to execute
            progress_callback: Optional callback for progress updates
            
        Returns:
            WorkflowExecutionResult with execution details
        """
        start_time = datetime.now()
        
        result = WorkflowExecutionResult(
            workflow_id=workflow.workflow_id,
            status=ExecutionStatus.RUNNING,
            steps_completed=0,
            total_steps=len(workflow.steps),
            start_time=start_time
        )
        
        self.active_executions[workflow.workflow_id] = result
        
        try:
            logger.info(f"Starting execution of workflow {workflow.workflow_id}: {workflow.name}")
            result.logs.append(f"Starting workflow execution: {workflow.name}")
            
            # Execute steps in dependency order
            executed_steps = set()
            
            while len(executed_steps) < len(workflow.steps):
                # Find steps that can be executed (dependencies satisfied)
                ready_steps = [
                    step for step in workflow.steps
                    if step.step_id not in executed_steps
                    and all(dep in executed_steps for dep in step.dependencies)
                ]
                
                if not ready_steps:
                    # Check if we have a dependency deadlock
                    remaining_steps = [step for step in workflow.steps if step.step_id not in executed_steps]
                    if remaining_steps:
                        error_msg = f"Dependency deadlock detected. Remaining steps: {[s.step_id for s in remaining_steps]}"
                        logger.error(error_msg)
                        result.status = ExecutionStatus.FAILED
                        result.error_message = error_msg
                        result.logs.append(error_msg)
                        break
                
                # Execute ready steps (could be parallel in the future)
                for step in ready_steps:
                    step_result = await self._execute_step(step, workflow)
                    result.step_results.append(step_result)
                    
                    if step_result.status == ExecutionStatus.COMPLETED:
                        executed_steps.add(step.step_id)
                        result.steps_completed += 1
                        result.logs.append(f"Step '{step.name}' completed successfully")
                        
                        # Collect job details if available
                        if step_result.job_id or step_result.execution_id:
                            job_detail = {
                                "step_name": step.name,
                                "job_id": step_result.job_id,
                                "job_name": step_result.job_name,
                                "execution_id": step_result.execution_id
                            }
                            result.job_details.append(job_detail)
                        
                        # Update progress
                        if progress_callback:
                            progress_callback(result.steps_completed, result.total_steps)
                    
                    elif step_result.status == ExecutionStatus.FAILED:
                        error_msg = f"Step '{step.name}' failed: {step_result.error_message}"
                        logger.error(error_msg)
                        result.status = ExecutionStatus.FAILED
                        result.error_message = error_msg
                        result.logs.append(error_msg)
                        break
                
                # If any step failed, stop execution
                if result.status == ExecutionStatus.FAILED:
                    break
            
            # Set final status
            if result.status != ExecutionStatus.FAILED:
                result.status = ExecutionStatus.COMPLETED
                result.summary = f"Workflow completed successfully. {result.steps_completed}/{result.total_steps} steps executed."
                result.logs.append("Workflow execution completed successfully")
            
            result.end_time = datetime.now()
            
            logger.info(f"Workflow {workflow.workflow_id} execution finished: {result.status.value}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.logs.append(f"Workflow execution failed: {str(e)}")
        
        return result
    
    async def _execute_step(self, step: WorkflowStep, workflow: Workflow) -> StepExecutionResult:
        """Execute a single workflow step"""
        start_time = datetime.now()
        
        result = StepExecutionResult(
            step_id=step.step_id,
            status=ExecutionStatus.RUNNING,
            start_time=start_time
        )
        
        try:
            logger.info(f"Executing step {step.step_id}: {step.name}")
            
            # Determine execution method based on step type
            if step.command:
                # Execute command
                execution_result = await self._execute_command(step, workflow)
            elif step.script_content:
                # Execute script
                execution_result = await self._execute_script(step, workflow)
            else:
                # Information gathering or analysis step
                execution_result = await self._execute_analysis_step(step, workflow)
            
            result.output = execution_result.get("output", "")
            result.exit_code = execution_result.get("exit_code", 0)
            
            # Capture job execution details
            result.execution_id = execution_result.get("execution_id")
            result.job_id = execution_result.get("job_id")
            result.job_name = execution_result.get("job_name")
            
            if result.exit_code == 0:
                result.status = ExecutionStatus.COMPLETED
            else:
                result.status = ExecutionStatus.FAILED
                result.error_message = execution_result.get("error", "Command failed")
            
        except Exception as e:
            logger.error(f"Step execution failed: {str(e)}")
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
        
        result.end_time = datetime.now()
        return result
    
    async def _execute_command(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Execute a command step"""
        try:
            if self.automation_client:
                # Use automation service to execute command
                job_data = {
                    "name": f"Step: {step.name}",
                    "description": step.description,
                    "steps": [
                        {
                            "id": step.step_id,
                            "name": step.name,
                            "command": step.command,
                            "type": "command",
                            "timeout": step.timeout_seconds,
                            "inputs": {}
                        }
                    ],
                    "target_systems": step.target_systems or ["automation-service"]
                }
                
                # Submit job to automation service
                job_result = await self._submit_automation_job(job_data)
                return job_result
            else:
                # Simulate execution for testing
                logger.warning("No automation client available, simulating execution")
                await asyncio.sleep(1)  # Simulate execution time
                return {
                    "output": f"Simulated execution of: {step.command}",
                    "exit_code": 0
                }
                
        except Exception as e:
            return {
                "output": "",
                "exit_code": 1,
                "error": str(e)
            }
    
    async def _execute_script(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Execute a script step"""
        try:
            if self.automation_client:
                # Use automation service to execute script
                job_data = {
                    "name": f"Script: {step.name}",
                    "description": step.description,
                    "steps": [
                        {
                            "name": step.name,
                            "script_content": step.script_content,
                            "timeout": step.timeout_seconds
                        }
                    ],
                    "target_systems": step.target_systems or ["automation-service"]
                }
                
                job_result = await self._submit_automation_job(job_data)
                return job_result
            else:
                # Simulate execution
                logger.warning("No automation client available, simulating script execution")
                await asyncio.sleep(2)  # Simulate execution time
                return {
                    "output": f"Simulated script execution: {step.name}",
                    "exit_code": 0
                }
                
        except Exception as e:
            return {
                "output": "",
                "exit_code": 1,
                "error": str(e)
            }
    
    async def _execute_analysis_step(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Execute an analysis or information gathering step"""
        try:
            # For analysis steps, we might gather information or perform checks
            logger.info(f"Performing analysis step: {step.name}")
            
            # Simulate analysis
            await asyncio.sleep(0.5)
            
            return {
                "output": f"Analysis completed for: {step.description}",
                "exit_code": 0
            }
            
        except Exception as e:
            return {
                "output": "",
                "exit_code": 1,
                "error": str(e)
            }
    
    async def _submit_automation_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a job to the automation service"""
        try:
            if not self.automation_client:
                logger.error("No automation client available")
                return {
                    "output": "",
                    "exit_code": 1,
                    "error": "No automation client configured"
                }
            
            logger.info(f"Submitting automation job to service: {job_data['name']}")
            
            # Submit workflow to actual automation service
            workflow_result = await self.automation_client.submit_ai_workflow(
                workflow=job_data,
                job_name=job_data.get("name", "AI Generated Job")
            )
            
            if workflow_result and workflow_result.get("success"):
                execution_id = workflow_result.get("execution_id")
                logger.info(f"Workflow submitted successfully with execution ID: {execution_id}")
                
                # Check if we have a valid execution ID
                if not execution_id:
                    logger.error("No execution ID returned from automation service")
                    return {
                        "output": "",
                        "exit_code": 1,
                        "error": "No execution ID returned from automation service"
                    }
                
                # Wait for workflow completion using the client's built-in method
                completion_result = await self.automation_client.wait_for_completion(
                    execution_id=execution_id,
                    timeout=300  # 5 minutes max
                )
                
                if completion_result:
                    return {
                        "output": completion_result.get("output", "Workflow completed successfully"),
                        "exit_code": 0 if completion_result.get("status") == "completed" else 1,
                        "execution_id": execution_id,
                        "job_id": workflow_result.get("job_id"),
                        "job_name": workflow_result.get("job_name")
                    }
                else:
                    return {
                        "output": "Workflow execution timed out",
                        "exit_code": 1,
                        "error": "Workflow execution timeout",
                        "execution_id": execution_id,
                        "job_id": workflow_result.get("job_id"),
                        "job_name": workflow_result.get("job_name")
                    }
            else:
                error_msg = workflow_result.get("error", "Failed to submit workflow") if workflow_result else "No response from automation service"
                logger.error(f"Failed to submit workflow: {error_msg}")
                return {
                    "output": "",
                    "exit_code": 1,
                    "error": error_msg
                }
            
        except Exception as e:
            logger.error(f"Failed to submit automation job: {str(e)}")
            return {
                "output": "",
                "exit_code": 1,
                "error": str(e)
            }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow execution"""
        if workflow_id not in self.active_executions:
            return False
        
        result = self.active_executions[workflow_id]
        
        if result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            return False  # Already finished
        
        result.status = ExecutionStatus.CANCELLED
        result.end_time = datetime.now()
        result.logs.append("Workflow execution cancelled")
        
        logger.info(f"Workflow {workflow_id} execution cancelled")
        return True
    
    async def get_execution_status(self, workflow_id: str) -> Optional[WorkflowExecutionResult]:
        """Get current execution status of a workflow"""
        return self.active_executions.get(workflow_id)
    
    async def list_active_executions(self) -> List[WorkflowExecutionResult]:
        """List all active workflow executions"""
        return [
            result for result in self.active_executions.values()
            if result.status == ExecutionStatus.RUNNING
        ]
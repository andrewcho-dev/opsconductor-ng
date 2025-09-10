"""
Comprehensive Celery tasks for OpsConductor Job Execution System
"""
import os
import sys
import json
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Add project root to path
sys.path.append('/home/opsconductor')

from .celery_config import celery_app
from .database import get_db_cursor
from .logging import get_logger
from .errors import DatabaseError, ValidationError, NotFoundError

logger = get_logger(__name__)

# Import JobExecutor at module level to avoid race conditions during task execution
try:
    # Try to import from executor-service main
    sys.path.insert(0, '/app')
    from main import JobExecutor
    JOBEXECUTOR_AVAILABLE = True
    logger.info("JobExecutor imported successfully at module level")
except Exception as import_exc:
    JOBEXECUTOR_AVAILABLE = False
    logger.warning(f"JobExecutor not available for import: {str(import_exc)}")
    # This is expected for celery-beat which doesn't need JobExecutor

@celery_app.task(bind=True)
def test_task(self, message="Hello from Celery!"):
    """Test task to verify Celery is working"""
    logger.info(f"Executing test task: {message}")
    return {"status": "success", "message": message, "task_id": self.request.id}

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def execute_job_run(self, job_run_id: int, job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a complete job run by orchestrating target-specific subtasks
    
    This task spawns individual Celery subtasks for each target, allowing for:
    - Individual target tracking and reporting
    - Better error isolation
    - Potential parallel execution
    - Proper rollup of results to the parent job
    
    Args:
        job_run_id: ID of the job run to execute
        job_config: Job configuration including definition and parameters
        
    Returns:
        Dict containing execution results and metrics
    """
    execution_start = datetime.now(timezone.utc)
    
    try:
        logger.info(f"Starting job run orchestration: {job_run_id}")
        
        # Update job run status to running
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE job_runs 
                SET status = 'running', 
                    started_at = %s,
                    celery_task_id = %s
                WHERE id = %s
            """, (execution_start, self.request.id, job_run_id))
            
            # Get unique targets for this job run
            cursor.execute("""
                SELECT DISTINCT target_id
                FROM job_run_steps 
                WHERE job_run_id = %s 
                ORDER BY target_id
            """, (job_run_id,))
            
            target_ids = [row['target_id'] for row in cursor.fetchall()]
            
            # Get all steps for verification
            cursor.execute("""
                SELECT id, idx, type, target_id, shell, timeoutsec, status
                FROM job_run_steps 
                WHERE job_run_id = %s 
                ORDER BY target_id, idx
            """, (job_run_id,))
            
            all_steps = cursor.fetchall()
        
        if not target_ids:
            raise ValidationError(f"No targets found for job run {job_run_id}")
        
        if not all_steps:
            raise ValidationError(f"No steps found for job run {job_run_id}")
        
        logger.info(f"Found {len(target_ids)} targets and {len(all_steps)} total steps for job run {job_run_id}")
        
        # Group steps by target
        steps_by_target = {}
        for step in all_steps:
            target_id = step['target_id']
            if target_id not in steps_by_target:
                steps_by_target[target_id] = []
            steps_by_target[target_id].append(step)
        
        # Spawn subtasks for each target
        target_tasks = []
        for target_id in target_ids:
            target_steps = steps_by_target[target_id]
            logger.info(f"Spawning subtask for target {target_id} with {len(target_steps)} steps")
            
            # Create subtask for this target
            subtask = execute_job_target.delay(job_run_id, target_id, target_steps)
            target_tasks.append({
                'target_id': target_id,
                'task_id': subtask.id,
                'task': subtask,
                'step_count': len(target_steps)
            })
            
            logger.info(f"Spawned subtask {subtask.id} for target {target_id}")
        
        # Store subtask information for monitoring, but don't wait synchronously
        # This avoids the Celery deadlock issue with calling .get() within a task
        logger.info(f"Spawned {len(target_tasks)} target subtasks - they will execute independently")
        
        # Instead of waiting, we'll use a different approach:
        # 1. Return immediately with subtask IDs for monitoring
        # 2. Let a separate monitoring task or the frontend poll for completion
        # 3. Or use Celery's callback mechanism
        
        target_results = []
        for target_task in target_tasks:
            target_results.append({
                'status': 'spawned',
                'target_id': target_task['target_id'],
                'task_id': target_task['task_id'],
                'step_count': target_task['step_count']
            })
        
        # Update job status to indicate subtasks are running
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE job_runs 
                SET status = 'running'
                WHERE id = %s
            """, (job_run_id,))
        
        # Calculate orchestration metrics (subtask spawning time)
        execution_end = datetime.now(timezone.utc)
        execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)
        
        # Store orchestration results - subtasks will update their own completion
        result_data = {
            'orchestration_time_ms': execution_time_ms,
            'total_steps': len(all_steps),
            'total_targets': len(target_ids),
            'subtasks_spawned': len(target_tasks),
            'target_subtasks': target_results,
            'subtask_ids': [t['task_id'] for t in target_tasks],
            'worker_info': {
                'hostname': self.request.hostname,
                'task_id': self.request.id,
                'queue': self.request.delivery_info.get('routing_key', 'unknown') if self.request.delivery_info else 'unknown'
            }
        }
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE job_runs 
                SET result_data = %s
                WHERE id = %s
            """, (json.dumps(result_data), job_run_id))
        
        # Spawn monitoring task to track completion
        subtask_ids = [t['task_id'] for t in target_tasks]
        monitor_task = monitor_job_completion.delay(job_run_id, subtask_ids)
        
        logger.info(f"Job run {job_run_id} orchestration completed - {len(target_tasks)} subtasks spawned, monitoring task {monitor_task.id} started")
        
        return {
            'status': 'success',
            'job_run_id': job_run_id,
            'orchestration_status': 'subtasks_spawned',
            'orchestration_time_ms': execution_time_ms,
            'subtasks_spawned': len(target_tasks),
            'subtask_ids': subtask_ids,
            'monitor_task_id': monitor_task.id,
            'task_id': self.request.id
        }
        
    except Exception as exc:
        execution_end = datetime.now(timezone.utc)
        execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)
        
        logger.error(f"Job run {job_run_id} orchestration failed: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update job run status to failed
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE job_runs 
                    SET status = 'failed', 
                        finished_at = %s,
                        error_message = %s,
                        result_data = %s
                    WHERE id = %s
                """, (
                    execution_end, 
                    str(exc),
                    json.dumps({
                        'execution_time_ms': execution_time_ms,
                        'error': str(exc),
                        'traceback': traceback.format_exc(),
                        'worker_info': {
                            'hostname': self.request.hostname,
                            'task_id': self.request.id
                        }
                    }),
                    job_run_id
                ))
        except Exception as db_exc:
            logger.error(f"Failed to update job run status: {str(db_exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            logger.info(f"Retrying job run {job_run_id} in {retry_delay} seconds (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error(f"Job run {job_run_id} failed permanently after {self.max_retries} retries")
            return {
                'status': 'failed',
                'job_run_id': job_run_id,
                'error': str(exc),
                'execution_time_ms': execution_time_ms,
                'task_id': self.request.id
            }

@celery_app.task(bind=True)
def monitor_job_completion(self, job_run_id: int, subtask_ids: List[str]) -> Dict[str, Any]:
    """
    Monitor subtask completion and update final job status
    
    This task periodically checks if all subtasks for a job run have completed,
    then updates the final job status and metrics.
    
    Args:
        job_run_id: ID of the job run to monitor
        subtask_ids: List of Celery task IDs to monitor
        
    Returns:
        Dict containing final job status and results
    """
    from celery.result import AsyncResult
    
    try:
        logger.info(f"Monitoring job run {job_run_id} with {len(subtask_ids)} subtasks")
        
        # Check status of all subtasks
        completed_subtasks = []
        failed_subtasks = []
        pending_subtasks = []
        
        for task_id in subtask_ids:
            result = AsyncResult(task_id, app=celery_app)
            
            if result.ready():
                if result.successful():
                    completed_subtasks.append(task_id)
                    logger.info(f"Subtask {task_id} completed successfully")
                else:
                    failed_subtasks.append(task_id)
                    logger.error(f"Subtask {task_id} failed: {result.result}")
            else:
                pending_subtasks.append(task_id)
        
        # If not all subtasks are complete, retry monitoring
        if pending_subtasks:
            logger.info(f"Job run {job_run_id}: {len(completed_subtasks)} completed, {len(failed_subtasks)} failed, {len(pending_subtasks)} pending")
            # Retry in 10 seconds
            raise self.retry(countdown=10, max_retries=360)  # Monitor for up to 1 hour
        
        # All subtasks completed - update final job status
        logger.info(f"All subtasks completed for job run {job_run_id}")
        
        # Get actual step statuses from database
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, target_id, status 
                FROM job_run_steps 
                WHERE job_run_id = %s 
                ORDER BY target_id, idx
            """, (job_run_id,))
            
            actual_step_statuses = cursor.fetchall()
        
        # Count results
        total_steps = len(actual_step_statuses)
        successful_steps = len([s for s in actual_step_statuses if s['status'] == 'succeeded'])
        failed_steps = len([s for s in actual_step_statuses if s['status'] == 'failed'])
        
        # Determine final status
        final_status = 'succeeded' if successful_steps == total_steps else 'failed'
        
        # Update job run with final status
        completion_time = datetime.now(timezone.utc)
        
        # Get existing result data and update it
        with get_db_cursor() as cursor:
            cursor.execute("SELECT result_data FROM job_runs WHERE id = %s", (job_run_id,))
            existing_data = cursor.fetchone()
            
            # result_data is already a dict when retrieved from JSONB field
            result_data = existing_data['result_data'] if existing_data and existing_data['result_data'] else {}
            
            # Add completion metrics
            result_data.update({
                'final_status': final_status,
                'total_steps': total_steps,
                'steps_succeeded': successful_steps,
                'steps_failed': failed_steps,
                'subtasks_completed': len(completed_subtasks),
                'subtasks_failed': len(failed_subtasks),
                'completion_monitored_by': {
                    'hostname': self.request.hostname,
                    'task_id': self.request.id
                }
            })
            
            cursor.execute("""
                UPDATE job_runs 
                SET status = %s, 
                    finished_at = %s,
                    result_data = %s
                WHERE id = %s
            """, (final_status, completion_time, json.dumps(result_data), job_run_id))
        
        logger.info(f"Job run {job_run_id} final status: {final_status} ({successful_steps}/{total_steps} steps succeeded)")
        
        return {
            'status': 'success',
            'job_run_id': job_run_id,
            'final_status': final_status,
            'total_steps': total_steps,
            'steps_succeeded': successful_steps,
            'steps_failed': failed_steps,
            'subtasks_completed': len(completed_subtasks),
            'subtasks_failed': len(failed_subtasks)
        }
        
    except Exception as exc:
        logger.error(f"Job completion monitoring failed for job run {job_run_id}: {str(exc)}")
        
        # Don't retry on non-retry exceptions
        if not isinstance(exc, self.retry.__class__):
            # Mark job as failed due to monitoring error
            try:
                with get_db_cursor() as cursor:
                    cursor.execute("""
                        UPDATE job_runs 
                        SET status = 'failed', 
                            finished_at = %s,
                            error_message = %s
                        WHERE id = %s
                    """, (datetime.now(timezone.utc), f"Monitoring failed: {str(exc)}", job_run_id))
            except Exception as db_exc:
                logger.error(f"Failed to update job status after monitoring error: {str(db_exc)}")
        
        raise

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def execute_job_target(self, job_run_id: int, target_id: int, target_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute all steps for a specific target within a job run
    
    This task handles all steps for a single target, providing:
    - Individual target tracking and reporting
    - Better error isolation per target
    - Detailed step-by-step execution logging
    - Proper error handling and rollback
    
    Args:
        job_run_id: ID of the job run
        target_id: ID of the target to execute steps on
        target_steps: List of step configurations for this target
        
    Returns:
        Dict containing target execution results
    """
    target_start = datetime.now(timezone.utc)
    
    # Add comprehensive error handling to catch any issues
    try:
        logger.info(f"TASK START: execute_job_target called with job_run_id={job_run_id}, target_id={target_id}, steps={len(target_steps)}")
    except Exception as log_exc:
        print(f"CRITICAL: Failed to log task start: {str(log_exc)}")
        # Continue anyway
    
    try:
        logger.info(f"Starting target execution: job_run_id={job_run_id}, target_id={target_id}, steps={len(target_steps)}")
        
        # Sort steps by index to ensure proper execution order
        sorted_steps = sorted(target_steps, key=lambda x: x['idx'])
        
        # Execute steps sequentially for this target
        step_results = []
        failed_step = None
        executed_step_count = 0
        successful_step_count = 0
        failed_step_count = 0
        
        # Create target-relative indices for proper step execution
        for target_relative_idx, step in enumerate(sorted_steps):
            try:
                logger.info(f"Executing step {step['idx']} (ID: {step['id']}) for target {target_id}")
                
                # Execute step using pre-imported JobExecutor
                logger.info(f"Executing step {step['id']} using JobExecutor")
                
                if not JOBEXECUTOR_AVAILABLE:
                    raise Exception("JobExecutor is not available - import failed at module level")
                
                try:
                    executor = JobExecutor()
                    logger.info(f"JobExecutor instance created for step {step['id']}")
                except Exception as init_exc:
                    logger.error(f"Failed to create JobExecutor instance for step {step['id']}: {str(init_exc)}")
                    logger.error(f"Init traceback: {traceback.format_exc()}")
                    raise init_exc
                
                try:
                    step_result = executor.execute_step(job_run_id, step['id'])
                    logger.info(f"JobExecutor.execute_step completed for step {step['id']}")
                except Exception as exec_exc:
                    logger.error(f"JobExecutor.execute_step failed for step {step['id']}: {str(exec_exc)}")
                    logger.error(f"Execution traceback: {traceback.format_exc()}")
                    raise exec_exc
                
                logger.info(f"Step {step['idx']} result for target {target_id}: {step_result}")
                
                step_results.append({
                    'step_id': step['id'],
                    'step_idx': step['idx'],
                    'step_type': step['type'],
                    'result': step_result
                })
                executed_step_count += 1
                
                # Count success/failure based on step execution result, not database
                if step_result.get('status') == 'success':
                    successful_step_count += 1
                else:
                    failed_step_count += 1
                    failed_step = step
                    logger.error(f"Step {step['idx']} failed for target {target_id}: {step_result.get('error', 'Unknown error')}")
                    break
                    
            except Exception as step_exc:
                logger.error(f"Step {step['idx']} execution failed for target {target_id}: {str(step_exc)}")
                logger.error(f"Exception type: {type(step_exc).__name__}")
                logger.error(f"Exception traceback: {traceback.format_exc()}")
                failed_step = step
                step_results.append({
                    'step_id': step['id'],
                    'step_idx': step['idx'],
                    'step_type': step['type'],
                    'result': {
                        'status': 'failed',
                        'error': str(step_exc)
                    }
                })
                executed_step_count += 1
                failed_step_count += 1
                break
        
        # Mark any remaining unexecuted steps as failed
        if failed_step:
            remaining_steps = sorted_steps[executed_step_count:]
            with get_db_cursor() as cursor:
                for remaining_step in remaining_steps:
                    logger.warning(f"Marking unexecuted step {remaining_step['idx']} (ID: {remaining_step['id']}) as failed for target {target_id}")
                    cursor.execute("""
                        UPDATE job_run_steps 
                        SET status = 'failed', 
                            stderr = 'Step not executed due to previous step failure in target',
                            finished_at = %s
                        WHERE id = %s
                    """, (datetime.now(timezone.utc), remaining_step['id']))
                    
                    step_results.append({
                        'step_id': remaining_step['id'],
                        'step_idx': remaining_step['idx'],
                        'step_type': remaining_step['type'],
                        'result': {
                            'status': 'failed',
                            'error': 'Step not executed due to previous step failure in target'
                        }
                    })
        
        # Calculate execution metrics
        target_end = datetime.now(timezone.utc)
        execution_time_ms = int((target_end - target_start).total_seconds() * 1000)
        
        # Count results based on actual execution results (not database queries)
        total_target_steps = len(sorted_steps)
        
        # Determine target status based on step execution results
        target_status = 'success' if successful_step_count == total_target_steps else 'failed'
        
        logger.info(f"Target {target_id} execution complete: {successful_step_count}/{total_target_steps} steps succeeded (based on execution results)")
        
        return {
            'status': target_status,
            'job_run_id': job_run_id,
            'target_id': target_id,
            'execution_time_ms': execution_time_ms,
            'total_steps': total_target_steps,
            'steps_succeeded': successful_step_count,
            'steps_failed': failed_step_count,
            'steps_executed': executed_step_count,
            'step_results': step_results,
            'worker_info': {
                'hostname': self.request.hostname,
                'task_id': self.request.id,
                'queue': self.request.delivery_info.get('routing_key', 'unknown') if self.request.delivery_info else 'unknown'
            }
        }
        
    except Exception as exc:
        target_end = datetime.now(timezone.utc)
        execution_time_ms = int((target_end - target_start).total_seconds() * 1000)
        
        logger.error(f"Target {target_id} execution failed: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Mark all steps for this target as failed
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE job_run_steps 
                    SET status = 'failed', 
                        stderr = %s,
                        finished_at = %s
                    WHERE job_run_id = %s AND target_id = %s AND status = 'queued'
                """, (f"Target execution failed: {str(exc)}", target_end, job_run_id, target_id))
        except Exception as db_exc:
            logger.error(f"Failed to update step statuses for target {target_id}: {str(db_exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 30 * (2 ** self.request.retries)
            logger.info(f"Retrying target {target_id} execution in {retry_delay} seconds (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error(f"Target {target_id} execution failed permanently after {self.max_retries} retries")
            return {
                'status': 'failed',
                'job_run_id': job_run_id,
                'target_id': target_id,
                'error': str(exc),
                'execution_time_ms': execution_time_ms,
                'task_id': self.request.id
            }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def execute_job_step(self, job_run_id: int, step_id: int, step_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single job step with comprehensive error handling and logging
    
    Args:
        job_run_id: ID of the job run
        step_id: ID of the step to execute
        step_config: Step configuration including type, target, command, etc.
        
    Returns:
        Dict containing step execution results
    """
    step_start = datetime.now(timezone.utc)
    
    try:
        logger.info(f"Starting step execution: job_run_id={job_run_id}, step_id={step_id}")
        
        # Update step status to running
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE job_run_steps 
                SET status = 'running', started_at = %s
                WHERE id = %s
            """, (step_start, step_id))
        
        # Import executor dynamically to avoid circular imports
        # Celery worker runs in /app directory which contains executor service files
        from main import JobExecutor
        executor = JobExecutor()
        step_result = executor.execute_step(job_run_id, step_id)
        
        # Calculate execution time
        step_end = datetime.now(timezone.utc)
        execution_time_ms = int((step_end - step_start).total_seconds() * 1000)
        
        # Update step with success status and results
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE job_run_steps 
                SET status = 'succeeded', 
                    finished_at = %s,
                    stdout = %s,
                    stderr = %s,
                    exit_code = %s,
                    metrics = %s
                WHERE id = %s
            """, (
                step_end,
                step_result.get('stdout', ''),
                step_result.get('stderr', ''),
                step_result.get('exit_code', 0),
                json.dumps({
                    'execution_time_ms': execution_time_ms,
                    'worker_info': {
                        'hostname': self.request.hostname,
                        'task_id': self.request.id
                    }
                }),
                step_id
            ))
        
        logger.info(f"Step {step_id} in job run {job_run_id} completed successfully in {execution_time_ms}ms")
        
        return {
            'status': 'success',
            'job_run_id': job_run_id,
            'step_id': step_id,
            'execution_time_ms': execution_time_ms,
            'exit_code': step_result.get('exit_code', 0),
            'task_id': self.request.id
        }
        
    except Exception as exc:
        step_end = datetime.now(timezone.utc)
        execution_time_ms = int((step_end - step_start).total_seconds() * 1000)
        
        logger.error(f"Step {step_id} in job run {job_run_id} failed: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update step with failed status
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE job_run_steps 
                    SET status = 'failed', 
                        finished_at = %s,
                        stderr = %s,
                        metrics = %s
                    WHERE id = %s
                """, (
                    step_end,
                    str(exc),
                    json.dumps({
                        'execution_time_ms': execution_time_ms,
                        'error': str(exc),
                        'traceback': traceback.format_exc(),
                        'worker_info': {
                            'hostname': self.request.hostname,
                            'task_id': self.request.id
                        }
                    }),
                    step_id
                ))
        except Exception as db_exc:
            logger.error(f"Failed to update step status: {str(db_exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 30 * (2 ** self.request.retries)
            logger.info(f"Retrying step {step_id} in {retry_delay} seconds (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error(f"Step {step_id} failed permanently after {self.max_retries} retries")
            return {
                'status': 'failed',
                'job_run_id': job_run_id,
                'step_id': step_id,
                'error': str(exc),
                'execution_time_ms': execution_time_ms,
                'task_id': self.request.id
            }

@celery_app.task(bind=True, max_retries=1)
def schedule_job_run(self, job_id: int, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule a job run for future execution
    
    Args:
        job_id: ID of the job to schedule
        schedule_config: Scheduling configuration
        
    Returns:
        Dict containing scheduling results
    """
    try:
        logger.info(f"Scheduling job {job_id} with config: {schedule_config}")
        
        # Implementation for job scheduling
        # This will integrate with Celery Beat for recurring schedules
        
        return {
            'status': 'success',
            'job_id': job_id,
            'scheduled': True,
            'task_id': self.request.id
        }
        
    except Exception as exc:
        logger.error(f"Failed to schedule job {job_id}: {str(exc)}")
        return {
            'status': 'failed',
            'job_id': job_id,
            'error': str(exc),
            'task_id': self.request.id
        }

@celery_app.task(bind=True)
def health_check(self) -> Dict[str, Any]:
    """
    Health check task for monitoring Celery workers
    
    Returns:
        Dict containing health status and system metrics
    """
    try:
        # Test database connectivity
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            db_healthy = True
    except Exception:
        db_healthy = False
    
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'worker_id': self.request.hostname,
        'task_id': self.request.id,
        'database_healthy': db_healthy,
        'queue': self.request.delivery_info.get('routing_key', 'unknown')
    }
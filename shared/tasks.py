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

@celery_app.task(bind=True)
def test_task(self, message="Hello from Celery!"):
    """Test task to verify Celery is working"""
    logger.info(f"Executing test task: {message}")
    return {"status": "success", "message": message, "task_id": self.request.id}

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def execute_job_run(self, job_run_id: int, job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a complete job run with orchestration of all steps
    
    Args:
        job_run_id: ID of the job run to execute
        job_config: Job configuration including definition and parameters
        
    Returns:
        Dict containing execution results and metrics
    """
    execution_start = datetime.now(timezone.utc)
    
    try:
        logger.info(f"Starting job run execution: {job_run_id}")
        
        # Update job run status to running
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE job_runs 
                SET status = 'running', 
                    started_at = %s,
                    celery_task_id = %s
                WHERE id = %s
            """, (execution_start, self.request.id, job_run_id))
            
            # Get job run steps
            cursor.execute("""
                SELECT id, idx, type, target_id, shell, timeoutsec, status
                FROM job_run_steps 
                WHERE job_run_id = %s 
                ORDER BY idx
            """, (job_run_id,))
            
            steps = cursor.fetchall()
        
        if not steps:
            raise ValidationError(f"No steps found for job run {job_run_id}")
        
        logger.info(f"Found {len(steps)} steps to execute for job run {job_run_id}")
        
        # Execute steps sequentially
        step_results = []
        failed_step = None
        
        for step in steps:
            try:
                logger.info(f"Executing step {step['idx']} (ID: {step['id']}) for job run {job_run_id}")
                
                # Execute step directly using JobExecutor (avoid Celery deadlock)
                # Import from executor service - Celery worker runs in /app directory
                from main import JobExecutor
                executor = JobExecutor()
                step_result = executor.execute_step(job_run_id, step['id'])
                
                step_results.append(step_result)
                
                if step_result.get('status') != 'success':
                    failed_step = step
                    logger.error(f"Step {step['idx']} failed: {step_result.get('error', 'Unknown error')}")
                    break
                    
            except Exception as step_exc:
                logger.error(f"Step {step['idx']} execution failed: {str(step_exc)}")
                failed_step = step
                step_results.append({
                    'status': 'failed',
                    'step_id': step['id'],
                    'error': str(step_exc)
                })
                break
        
        # Calculate execution metrics
        execution_end = datetime.now(timezone.utc)
        execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)
        
        # Determine final status
        final_status = 'failed' if failed_step else 'succeeded'
        
        # Update job run with final status and results
        result_data = {
            'execution_time_ms': execution_time_ms,
            'steps_executed': len(step_results),
            'steps_succeeded': len([r for r in step_results if r.get('status') == 'success']),
            'steps_failed': len([r for r in step_results if r.get('status') == 'failed']),
            'step_results': step_results,
            'worker_info': {
                'hostname': self.request.hostname,
                'task_id': self.request.id,
                'queue': self.request.delivery_info.get('routing_key', 'unknown')
            }
        }
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE job_runs 
                SET status = %s, 
                    finished_at = %s,
                    result_data = %s
                WHERE id = %s
            """, (final_status, execution_end, json.dumps(result_data), job_run_id))
        
        logger.info(f"Job run {job_run_id} completed with status: {final_status}")
        
        return {
            'status': 'success',
            'job_run_id': job_run_id,
            'final_status': final_status,
            'execution_time_ms': execution_time_ms,
            'steps_executed': len(step_results),
            'task_id': self.request.id
        }
        
    except Exception as exc:
        execution_end = datetime.now(timezone.utc)
        execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)
        
        logger.error(f"Job run {job_run_id} failed: {str(exc)}")
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
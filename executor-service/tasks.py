"""
Celery tasks for job execution
Celery-based job processing tasks
"""
import os
import sys
import json
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.celery_config import celery_app
from shared.database import get_db_cursor
from shared.logging import get_logger
from shared.errors import DatabaseError, ValidationError, NotFoundError

# Import the main executor logic
from main import JobExecutor

# Initialize logger
logger = get_logger(__name__)

# Initialize job executor
job_executor = None

def get_job_executor():
    """Get or create job executor instance"""
    global job_executor
    if job_executor is None:
        job_executor = JobExecutor()
    return job_executor

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def execute_job_run(self, job_run_id: int) -> Dict[str, Any]:
    """
    Execute a complete job run with all steps
    
    Args:
        job_run_id: ID of the job run to execute
        
    Returns:
        Dict containing execution results
        
    Raises:
        Retry: If execution fails and retries are available
    """
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
            """, (datetime.now(timezone.utc), self.request.id, job_run_id))
        
        # Execute the job run
        executor = get_job_executor()
        result = executor.execute_job_run(job_run_id)
        
        logger.info(f"Job run {job_run_id} completed successfully")
        return {
            'status': 'success',
            'job_run_id': job_run_id,
            'result': result,
            'task_id': self.request.id
        }
        
    except Exception as exc:
        logger.error(f"Job run {job_run_id} failed: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update job run status to failed
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE job_runs 
                    SET status = 'failed', 
                        completed_at = %s,
                        error_message = %s
                    WHERE id = %s
                """, (datetime.now(timezone.utc), str(exc), job_run_id))
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
                'task_id': self.request.id
            }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def execute_job_step(self, job_run_id: int, step_id: int) -> Dict[str, Any]:
    """
    Execute a single job step
    
    Args:
        job_run_id: ID of the job run
        step_id: ID of the step to execute
        
    Returns:
        Dict containing step execution results
        
    Raises:
        Retry: If execution fails and retries are available
    """
    try:
        logger.info(f"Starting step execution: job_run_id={job_run_id}, step_id={step_id}")
        
        # Execute the step
        executor = get_job_executor()
        result = executor.execute_step(job_run_id, step_id)
        
        logger.info(f"Step {step_id} in job run {job_run_id} completed successfully")
        return {
            'status': 'success',
            'job_run_id': job_run_id,
            'step_id': step_id,
            'result': result,
            'task_id': self.request.id
        }
        
    except Exception as exc:
        logger.error(f"Step {step_id} in job run {job_run_id} failed: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
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
                'task_id': self.request.id
            }

@celery_app.task(bind=True, max_retries=1)
def test_connection(self, target_id: int, connection_type: str) -> Dict[str, Any]:
    """
    Test connection to a target
    
    Args:
        target_id: ID of the target to test
        connection_type: Type of connection (winrm, ssh)
        
    Returns:
        Dict containing connection test results
    """
    try:
        logger.info(f"Testing {connection_type} connection to target {target_id}")
        
        executor = get_job_executor()
        result = executor.test_target_connection(target_id, connection_type)
        
        logger.info(f"Connection test to target {target_id} completed")
        return {
            'status': 'success',
            'target_id': target_id,
            'connection_type': connection_type,
            'result': result,
            'task_id': self.request.id
        }
        
    except Exception as exc:
        logger.error(f"Connection test to target {target_id} failed: {str(exc)}")
        return {
            'status': 'failed',
            'target_id': target_id,
            'connection_type': connection_type,
            'error': str(exc),
            'task_id': self.request.id
        }

@celery_app.task(bind=True)
def health_check(self) -> Dict[str, Any]:
    """
    Health check task for monitoring
    
    Returns:
        Dict containing health status
    """
    try:
        # Test database connection
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_id': self.request.id
        }
        
    except Exception as exc:
        logger.error(f"Health check failed: {str(exc)}")
        return {
            'status': 'unhealthy',
            'error': str(exc),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_id': self.request.id
        }

# Task for handling scheduled jobs (will be used by Celery Beat)
@celery_app.task(bind=True)
def execute_scheduled_job(self, job_id: int, schedule_id: int) -> Dict[str, Any]:
    """
    Execute a scheduled job (called by Celery Beat)
    
    Args:
        job_id: ID of the job to execute
        schedule_id: ID of the schedule that triggered this execution
        
    Returns:
        Dict containing execution results
    """
    try:
        logger.info(f"Executing scheduled job: job_id={job_id}, schedule_id={schedule_id}")
        
        # Create a new job run for this scheduled execution
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO job_runs (job_id, status, created_at, triggered_by, schedule_id)
                VALUES (%s, 'pending', %s, 'schedule', %s)
                RETURNING id
            """, (job_id, datetime.now(timezone.utc), schedule_id))
            
            job_run_id = cursor.fetchone()[0]
        
        # Execute the job run
        result = execute_job_run.delay(job_run_id)
        
        logger.info(f"Scheduled job {job_id} submitted for execution as job run {job_run_id}")
        return {
            'status': 'submitted',
            'job_id': job_id,
            'job_run_id': job_run_id,
            'schedule_id': schedule_id,
            'execution_task_id': result.id,
            'task_id': self.request.id
        }
        
    except Exception as exc:
        logger.error(f"Scheduled job {job_id} submission failed: {str(exc)}")
        return {
            'status': 'failed',
            'job_id': job_id,
            'schedule_id': schedule_id,
            'error': str(exc),
            'task_id': self.request.id
        }
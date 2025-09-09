"""
Celery utilities for OpsConductor
Provides helper functions for task submission and monitoring
"""
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from celery.result import AsyncResult

from .celery_config import celery_app
from .logging import get_logger

logger = get_logger(__name__)

def submit_job_run(job_run_id: int, scheduled_time: Optional[datetime] = None) -> AsyncResult:
    """
    Submit a job run for execution
    
    Args:
        job_run_id: ID of the job run to execute
        scheduled_time: Optional datetime to schedule execution
        
    Returns:
        AsyncResult object for tracking task
    """
    from executor_service.tasks import execute_job_run
    
    if scheduled_time:
        logger.info(f"Scheduling job run {job_run_id} for {scheduled_time}")
        return execute_job_run.apply_async(
            args=[job_run_id],
            eta=scheduled_time
        )
    else:
        logger.info(f"Submitting job run {job_run_id} for immediate execution")
        return execute_job_run.delay(job_run_id)

def submit_job_step(job_run_id: int, step_id: int, scheduled_time: Optional[datetime] = None) -> AsyncResult:
    """
    Submit a job step for execution
    
    Args:
        job_run_id: ID of the job run
        step_id: ID of the step to execute
        scheduled_time: Optional datetime to schedule execution
        
    Returns:
        AsyncResult object for tracking task
    """
    from executor_service.tasks import execute_job_step
    
    if scheduled_time:
        logger.info(f"Scheduling step {step_id} in job run {job_run_id} for {scheduled_time}")
        return execute_job_step.apply_async(
            args=[job_run_id, step_id],
            eta=scheduled_time
        )
    else:
        logger.info(f"Submitting step {step_id} in job run {job_run_id} for immediate execution")
        return execute_job_step.delay(job_run_id, step_id)

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status and result of a Celery task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Dict containing task status information
    """
    try:
        task = AsyncResult(task_id, app=celery_app)
        
        result = {
            'task_id': task_id,
            'status': task.status,
            'ready': task.ready(),
            'successful': task.successful() if task.ready() else None,
            'failed': task.failed() if task.ready() else None,
        }
        
        if task.ready():
            if task.successful():
                result['result'] = task.result
            elif task.failed():
                result['error'] = str(task.result)
                result['traceback'] = task.traceback
        else:
            result['info'] = task.info
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {str(e)}")
        return {
            'task_id': task_id,
            'status': 'UNKNOWN',
            'error': str(e)
        }

def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a Celery task
    
    Args:
        task_id: Celery task ID to cancel
        
    Returns:
        Dict containing cancellation result
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Task {task_id} cancelled")
        return {
            'task_id': task_id,
            'status': 'cancelled',
            'message': 'Task cancelled successfully'
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {str(e)}")
        return {
            'task_id': task_id,
            'status': 'error',
            'error': str(e)
        }

def get_worker_stats() -> Dict[str, Any]:
    """
    Get statistics about active Celery workers
    
    Returns:
        Dict containing worker statistics
    """
    try:
        inspect = celery_app.control.inspect()
        
        # Get active workers
        stats = inspect.stats()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            'workers': list(stats.keys()) if stats else [],
            'worker_count': len(stats) if stats else 0,
            'stats': stats,
            'active_tasks': active_tasks,
            'scheduled_tasks': scheduled_tasks,
            'reserved_tasks': reserved_tasks,
            'total_active_tasks': sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0,
            'total_scheduled_tasks': sum(len(tasks) for tasks in scheduled_tasks.values()) if scheduled_tasks else 0,
            'total_reserved_tasks': sum(len(tasks) for tasks in reserved_tasks.values()) if reserved_tasks else 0,
        }
        
    except Exception as e:
        logger.error(f"Failed to get worker stats: {str(e)}")
        return {
            'workers': [],
            'worker_count': 0,
            'error': str(e)
        }

def test_celery_connection() -> Dict[str, Any]:
    """
    Test Celery connection and worker availability
    
    Returns:
        Dict containing connection test results
    """
    try:
        # Test basic connection
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            return {
                'status': 'healthy',
                'workers_available': True,
                'worker_count': len(stats),
                'workers': list(stats.keys())
            }
        else:
            return {
                'status': 'unhealthy',
                'workers_available': False,
                'worker_count': 0,
                'error': 'No workers available'
            }
            
    except Exception as e:
        logger.error(f"Celery connection test failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'workers_available': False,
            'error': str(e)
        }

def submit_scheduled_job(job_id: int, schedule_id: int) -> AsyncResult:
    """
    Submit a scheduled job for execution (used by Celery Beat)
    
    Args:
        job_id: ID of the job to execute
        schedule_id: ID of the schedule that triggered this execution
        
    Returns:
        AsyncResult object for tracking task
    """
    from executor_service.tasks import execute_scheduled_job
    
    logger.info(f"Submitting scheduled job {job_id} (schedule {schedule_id})")
    return execute_scheduled_job.delay(job_id, schedule_id)

def get_queue_length(queue_name: str = 'execution') -> int:
    """
    Get the length of a specific queue
    
    Args:
        queue_name: Name of the queue to check
        
    Returns:
        Number of tasks in the queue
    """
    try:
        with celery_app.connection() as conn:
            queue = conn.SimpleQueue(queue_name)
            return queue.qsize()
    except Exception as e:
        logger.error(f"Failed to get queue length for {queue_name}: {str(e)}")
        return -1

def purge_queue(queue_name: str = 'execution') -> Dict[str, Any]:
    """
    Purge all tasks from a specific queue
    
    Args:
        queue_name: Name of the queue to purge
        
    Returns:
        Dict containing purge results
    """
    try:
        purged_count = celery_app.control.purge()
        logger.info(f"Purged {purged_count} tasks from queue {queue_name}")
        return {
            'status': 'success',
            'purged_count': purged_count,
            'queue': queue_name
        }
    except Exception as e:
        logger.error(f"Failed to purge queue {queue_name}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'queue': queue_name
        }
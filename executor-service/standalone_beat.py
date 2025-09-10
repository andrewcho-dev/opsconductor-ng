#!/usr/bin/env python3
"""
Standalone Celery Beat Service
No shared module dependencies - true microservice approach
"""
import os
import logging
from celery import Celery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('celery-beat')

# Redis connection
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app
app = Celery('opsconductor-beat')

# Configure Celery
app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        # Example scheduled task - can be configured via environment or API later
        'heartbeat': {
            'task': 'standalone_beat.heartbeat_task',
            'schedule': 60.0,  # Every minute
        },
    },
    beat_schedule_filename='/app/data/celerybeat-schedule',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_routes={
        'standalone_beat.*': {'queue': 'beat_tasks'},
    }
)

@app.task
def heartbeat_task():
    """Simple heartbeat task to verify beat is working"""
    logger.info("Celery Beat heartbeat - scheduler is working!")
    return {
        'status': 'success',
        'message': 'Beat scheduler is alive',
        'timestamp': str(os.popen('date').read().strip())
    }

@app.task
def schedule_job_execution(job_run_id, job_config):
    """
    Task to schedule job execution
    This will be called by the jobs-service to schedule job runs
    """
    logger.info(f"Scheduling job execution for job_run_id: {job_run_id}")
    
    # Send task to executor service queue
    from celery import current_app
    current_app.send_task(
        'executor.execute_job',
        args=[job_run_id, job_config],
        queue='executor_tasks'
    )
    
    return {
        'status': 'scheduled',
        'job_run_id': job_run_id,
        'message': 'Job execution scheduled successfully'
    }

if __name__ == '__main__':
    logger.info("Starting standalone Celery Beat service...")
    app.start()
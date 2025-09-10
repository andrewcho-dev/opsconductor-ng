"""
Celery configuration for OpsConductor
Redis-based Celery task queue configuration
"""
import os
from celery import Celery
from celery.schedules import crontab

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app
celery_app = Celery(
    'opsconductor',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'shared.tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,
    
    # Task limits
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Worker configuration
    worker_prefetch_multiplier=1,  # One task at a time per worker
    task_acks_late=True,  # Acknowledge after task completion
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    
    # Result backend settings
    result_expires=2592000,  # Results expire after 30 days (30 * 24 * 60 * 60)
    result_persistent=True,  # Persist results to disk
    
    # Task routing
    task_routes={
        'shared.tasks.execute_job_run': {'queue': 'execution'},
        'shared.tasks.execute_job_target': {'queue': 'execution'},
        'shared.tasks.execute_job_step': {'queue': 'execution'},
        'shared.tasks.monitor_job_completion': {'queue': 'jobs'},
        'shared.tasks.process_job_request': {'queue': 'jobs'},
        'shared.tasks.test_task': {'queue': 'celery'},
    },
    
    # Default queue
    task_default_queue='execution',
    
    # Beat schedule (will be populated dynamically)
    beat_schedule={},
    beat_schedule_filename='celerybeat-schedule',
    
    # Monitoring
    worker_send_task_events=True,
)

# Task queues
celery_app.conf.task_routes = {
    'shared.tasks.execute_job_run': {'queue': 'execution'},
    'shared.tasks.execute_job_target': {'queue': 'execution'},
    'shared.tasks.execute_job_step': {'queue': 'execution'},
    'shared.tasks.monitor_job_completion': {'queue': 'jobs'},
    'shared.tasks.process_job_request': {'queue': 'jobs'},
    'shared.tasks.test_task': {'queue': 'celery'},
}

# Configure queues
from kombu import Queue
celery_app.conf.task_queues = (
    Queue('execution', routing_key='execution'),
    Queue('jobs', routing_key='jobs'),
    Queue('celery', routing_key='celery'),  # Default queue
)

# Error handling
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_ignore_result = False

# Retry configuration
celery_app.conf.task_default_retry_delay = 60  # 1 minute
celery_app.conf.task_max_retries = 3

# Worker configuration
celery_app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
celery_app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Beat configuration for scheduled tasks
celery_app.conf.beat_scheduler = 'celery.beat:PersistentScheduler'
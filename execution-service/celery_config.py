"""
Celery configuration for service
Redis-based Celery task queue configuration
Copy this file to your service directory and customize as needed
"""
import os
from celery import Celery
from celery.schedules import crontab

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app - customize app name per service
celery_app = Celery(
    'opsconductor-service',  # Customize this per service
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'tasks'  # Local tasks module
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
    
    # Task routing - customize per service
    task_routes={
        'tasks.*': {'queue': 'default'},
    },
    
    # Periodic tasks (customize per service)
    beat_schedule={
        # Add service-specific periodic tasks here
    },
)
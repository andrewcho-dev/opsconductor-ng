#!/usr/bin/env python3
"""
Completely isolated Celery Beat configuration
"""
import os
import sys

# Remove any shared paths that might cause automatic imports
if '/app/shared' in sys.path:
    sys.path.remove('/app/shared')

from celery import Celery

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app with minimal configuration
celery_app = Celery('isolated_beat')

# Configure broker and backend
celery_app.conf.broker_url = REDIS_URL
celery_app.conf.result_backend = REDIS_URL

# Minimal configuration
celery_app.conf.update(
    timezone='UTC',
    enable_utc=True,
    beat_schedule={},
    beat_schedule_filename='/app/data/celerybeat-schedule',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    worker_send_task_events=False,
    task_send_sent_event=False,
)

# Export the app
app = celery_app
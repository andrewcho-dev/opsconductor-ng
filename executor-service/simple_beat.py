#!/usr/bin/env python3
"""
Simple Celery Beat configuration without heavy imports
"""
import os
from celery import Celery

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app
app = Celery(
    'opsconductor_beat',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Basic configuration
app.conf.update(
    timezone='UTC',
    enable_utc=True,
    beat_schedule={},
    beat_schedule_filename='/app/data/celerybeat-schedule',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

# Simple test task
@app.task
def heartbeat():
    """Simple heartbeat task"""
    return {"status": "alive", "timestamp": "now"}

if __name__ == '__main__':
    app.start()
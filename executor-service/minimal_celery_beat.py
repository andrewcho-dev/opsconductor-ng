#!/usr/bin/env python3
"""
Minimal Celery Beat configuration for testing
"""
import os
import sys
from celery import Celery

# Add the shared directory to the path
sys.path.insert(0, '/app/shared')

# Redis connection URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create minimal Celery app
app = Celery(
    'minimal_beat',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Minimal configuration
app.conf.update(
    timezone='UTC',
    enable_utc=True,
    beat_schedule={},
    beat_schedule_filename='/app/data/celerybeat-schedule'
)

if __name__ == '__main__':
    app.start()
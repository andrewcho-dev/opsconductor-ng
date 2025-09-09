#!/usr/bin/env python3
"""
Celery worker startup script for OpsConductor
Celery worker for job execution
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Import Celery app
from shared.celery_config import celery_app

# Import tasks to register them
import tasks

if __name__ == '__main__':
    # Start the Celery worker
    celery_app.start()
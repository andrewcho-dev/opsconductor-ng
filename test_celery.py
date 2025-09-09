#!/usr/bin/env python3
"""
Test script to verify Celery worker functionality
"""
import sys
import os
sys.path.append('/home/opsconductor')

from shared.celery_config import celery_app
from shared.tasks import test_task

def test_celery_connection():
    """Test basic Celery functionality"""
    print("Testing Celery worker connection...")
    
    try:
        # Send a test task
        result = test_task.delay("Hello from test script!")
        print(f"Task sent with ID: {result.id}")
        
        # Wait for result (with timeout)
        try:
            task_result = result.get(timeout=10)
            print(f"Task completed successfully: {task_result}")
            return True
        except Exception as e:
            print(f"Task execution failed: {e}")
            return False
            
    except Exception as e:
        print(f"Failed to send task: {e}")
        return False

if __name__ == "__main__":
    success = test_celery_connection()
    sys.exit(0 if success else 1)
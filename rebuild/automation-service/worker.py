#!/usr/bin/env python3
"""
Celery Worker for Automation Service
Handles background job execution
"""

import os
from celery import Celery

# Create Celery app
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/3")
app = Celery('automation-worker', broker=redis_url, backend=redis_url)

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True)
def execute_job(self, job_id, workflow_definition, input_data=None):
    """Execute a job workflow"""
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
        
        # Simulate job execution
        import time
        import json
        
        steps = workflow_definition.get('steps', [])
        total_steps = len(steps)
        
        results = []
        for i, step in enumerate(steps):
            # Simulate step execution
            time.sleep(1)  # Simulate work
            
            step_result = {
                'step_id': step.get('id', f'step_{i}'),
                'step_name': step.get('name', f'Step {i+1}'),
                'status': 'completed',
                'output': f'Step {i+1} completed successfully'
            }
            results.append(step_result)
            
            # Update progress
            progress = int((i + 1) / total_steps * 100)
            self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100})
        
        return {
            'status': 'completed',
            'results': results,
            'message': f'Job {job_id} completed successfully'
        }
        
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'job_id': job_id}
        )
        raise

@app.task
def test_task():
    """Simple test task"""
    return "Hello from Celery worker!"

if __name__ == '__main__':
    app.start()
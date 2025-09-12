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

# Configure Celery with resource protection
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=20 * 60,  # 20 minutes max (reduced from 30)
    task_soft_time_limit=18 * 60,  # 18 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (reduced from 1000)
    worker_max_memory_per_child=512000,  # 512MB memory limit per worker
    task_acks_late=True,  # Acknowledge tasks only after completion
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
)

async def process_job_results(job_id, results):
    """Process job results based on job type"""
    import asyncpg
    import json
    
    # Connect to database to get job info
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Get job info including job_type
        job_row = await conn.fetchrow("""
            SELECT job_type, metadata, name 
            FROM automation.jobs 
            WHERE id = $1
        """, job_id)
        
        if not job_row:
            print(f"Job {job_id} not found in database")
            return
        
        job_type = job_row['job_type']
        metadata = json.loads(job_row['metadata']) if job_row['metadata'] else {}
        job_name = job_row['name']
        
        print(f"Processing results for job {job_id} of type '{job_type}'")
        
        # Route results based on job type
        if job_type == 'discovery':
            await process_discovery_results(conn, job_id, results, metadata, job_name)
        else:
            print(f"No specific result processing for job type '{job_type}'")
            
    finally:
        await conn.close()

async def process_discovery_results(conn, job_id, results, metadata, job_name):
    """Process discovery job results and save to assets database"""
    print(f"Processing discovery results for job {job_id}")
    
    # Look for save_assets step results
    discovered_targets = []
    
    for result in results:
        if result.get('step_name') == 'save_assets' and result.get('status') == 'completed':
            # Extract discovered targets from save_assets step
            step_outputs = result.get('outputs', {})
            targets = step_outputs.get('saved_targets', [])
            
            if targets:
                discovered_targets.extend(targets)
                print(f"Found {len(targets)} targets from save_assets step")
    
    if not discovered_targets:
        print("No targets found in discovery results")
        return
    
    # Save discovered targets to assets.targets table
    try:
        for target in discovered_targets:
            # Insert or update target in assets.targets
            await conn.execute("""
                INSERT INTO assets.targets (
                    ip_address, hostname, ports, services, os_info, 
                    discovery_method, last_seen, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), $7, NOW(), NOW())
                ON CONFLICT (ip_address) 
                DO UPDATE SET 
                    hostname = EXCLUDED.hostname,
                    ports = EXCLUDED.ports,
                    services = EXCLUDED.services,
                    os_info = EXCLUDED.os_info,
                    discovery_method = EXCLUDED.discovery_method,
                    last_seen = NOW(),
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """, 
                target.get('ip_address'),
                target.get('hostname'),
                json.dumps(target.get('ports', [])),
                json.dumps(target.get('services', [])),
                json.dumps(target.get('os_info', {})),
                f"automation_job_{job_id}",
                json.dumps({
                    'discovery_job_id': job_id,
                    'discovery_job_name': job_name,
                    'original_metadata': target.get('metadata', {}),
                    'discovered_at': target.get('discovered_at')
                })
            )
        
        print(f"Successfully saved {len(discovered_targets)} targets to assets database")
        
    except Exception as e:
        print(f"Error saving discovery targets: {e}")
        raise

@app.task(bind=True)
def execute_job(self, job_id=None, workflow_definition=None, input_data=None):
    """Execute a job workflow"""
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
        
        import asyncio
        import sys
        import json
        
        # Add libraries to path
        sys.path.append('/app/libraries')
        
        # Parse workflow_definition if it's a string
        if isinstance(workflow_definition, str):
            workflow_definition = json.loads(workflow_definition)
        
        steps = workflow_definition.get('steps', [])
        total_steps = len(steps)
        
        results = []
        step_outputs = {}  # Store outputs for next steps
        
        for i, step in enumerate(steps):
            try:
                step_id = step.get('id')
                step_name = step.get('name', f'Step {i+1}')
                library_name = step.get('library')
                function_name = step.get('function')
                
                print(f"Executing step {step_id}: {step_name}")
                
                # Prepare step inputs
                step_inputs = {}
                for input_def in step.get('inputs', []):
                    input_name = input_def['name']
                    if 'value' in input_def:
                        # Static value
                        step_inputs[input_name] = input_def['value']
                    elif 'template' in input_def:
                        # Template value - resolve from previous step outputs
                        template = input_def['template']
                        if template.startswith('{{') and template.endswith('}}'):
                            # Extract step reference
                            ref = template[2:-2].strip()
                            if '.' in ref:
                                step_ref, output_key = ref.split('.', 1)
                                if step_ref in step_outputs:
                                    step_inputs[input_name] = step_outputs[step_ref].get(output_key)
                
                # Execute the step function
                if library_name and function_name:
                    # Import the library
                    library_module = __import__(library_name)
                    step_function = getattr(library_module, function_name)
                    
                    # Execute the function
                    if asyncio.iscoroutinefunction(step_function):
                        result = asyncio.run(step_function(**step_inputs))
                    else:
                        result = step_function(**step_inputs)
                    
                    # Store outputs for next steps
                    step_outputs[step_id] = result
                    
                    step_result = {
                        'step_id': step_id,
                        'step_name': step_name,
                        'status': 'completed',
                        'output': result,
                        'inputs': step_inputs
                    }
                else:
                    # Fallback for steps without library/function
                    step_result = {
                        'step_id': step_id,
                        'step_name': step_name,
                        'status': 'completed',
                        'output': f'Step {step_name} completed (no function specified)',
                        'inputs': step_inputs
                    }
                
                results.append(step_result)
                print(f"Step {step_id} completed successfully")
                
            except Exception as step_error:
                print(f"Step {step_id} failed: {step_error}")
                step_result = {
                    'step_id': step_id,
                    'step_name': step_name,
                    'status': 'failed',
                    'error': str(step_error),
                    'inputs': step_inputs
                }
                results.append(step_result)
            
            # Update progress
            progress = int((i + 1) / total_steps * 100)
            self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100})
        
        # Process results based on job type
        final_results = {
            'status': 'completed',
            'results': results,
            'message': f'Job {job_id} completed successfully'
        }
        
        # Route results based on job type if job_id is provided
        if job_id:
            try:
                asyncio.run(process_job_results(job_id, results))
            except Exception as e:
                print(f"Warning: Failed to process job results for job {job_id}: {e}")
                # Don't fail the job if result processing fails
        
        return final_results
        
    except Exception as exc:
        print(f"Job execution failed: {exc}")
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
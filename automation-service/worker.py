#!/usr/bin/env python3
"""
Celery Worker for Automation Service
Handles background job execution with enhanced monitoring
"""

import os
import sys
import logging
import subprocess
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_retry, task_revoked

# Add libraries to path at module level
sys.path.append('/app/libraries')

# Import libraries at module level
try:
    from libraries.windows_powershell import WindowsPowerShellLibrary
except ImportError as e:
    print(f"Warning: Could not import WindowsPowerShellLibrary: {e}")
    WindowsPowerShellLibrary = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/3")
app = Celery('automation-worker', broker=redis_url, backend=redis_url)

# Configure Celery with enhanced monitoring and resource protection
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_send_sent_event=True,  # Enable task-sent events
    task_time_limit=20 * 60,  # 20 minutes max
    task_soft_time_limit=18 * 60,  # 18 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    worker_max_memory_per_child=512000,  # 512MB memory limit per worker
    task_acks_late=True,  # Acknowledge tasks only after completion
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
    worker_send_task_events=True,  # Enable worker events
    task_routes={
        'automation-worker.execute_job': {'queue': 'default'},
        'automation-worker.execute_job_high_priority': {'queue': 'high_priority'},
        'automation-worker.execute_job_low_priority': {'queue': 'low_priority'},
    },
    task_default_queue='default',
    task_default_exchange='default',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
)

# Celery signal handlers for enhanced monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handle task start - update database status"""
    logger.info(f"Task {task_id} ({task.name}) starting with args: {args}")
    
    # Update database status to 'running'
    if len(args) >= 2:  # job_id, execution_id expected
        try:
            import asyncio
            asyncio.create_task(update_job_execution_status(args[0], args[1], 'running'))
        except Exception as e:
            logger.error(f"Failed to update task start status: {e}")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Handle task completion"""
    logger.info(f"Task {task_id} ({task.name}) completed with state: {state}")
    
    # Update database status based on completion state
    if len(args) >= 2:  # job_id, execution_id expected
        try:
            import asyncio
            status = 'completed' if state == 'SUCCESS' else 'failed'
            error_msg = str(retval) if state != 'SUCCESS' and retval else None
            asyncio.create_task(update_job_execution_status(args[0], args[1], status, error_msg))
        except Exception as e:
            logger.error(f"Failed to update task completion status: {e}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Handle task failure"""
    logger.error(f"Task {task_id} failed: {exception}")

@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Handle task retry"""
    logger.warning(f"Task {task_id} retrying: {reason}")

@task_revoked.connect
def task_revoked_handler(sender=None, task_id=None, terminated=None, signum=None, expired=None, **kwds):
    """Handle task revocation/cancellation"""
    logger.warning(f"Task {task_id} revoked - terminated: {terminated}, expired: {expired}")
    
    # Try to update database status to cancelled
    try:
        import asyncio
        # We don't have args here, so we'll need to look up by task_id
        asyncio.create_task(update_job_execution_status_by_task_id(task_id, 'cancelled', 'Task was cancelled'))
    except Exception as e:
        logger.error(f"Failed to update task cancellation status: {e}")

async def update_job_execution_status_by_task_id(task_id, status, error_message=None):
    """Update job execution status by Celery task ID"""
    import asyncpg
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Find execution by task ID (stored in execution_id field)
        await conn.execute("""
            UPDATE automation.job_executions 
            SET status = $1, completed_at = NOW(), error_message = $2
            WHERE execution_id::text = $3
        """, status, error_message, task_id)
        
        logger.info(f"Updated job execution with task_id {task_id} status to {status}")
    except Exception as e:
        logger.error(f"Failed to update job execution status by task_id: {e}")
    finally:
        await conn.close()

async def update_job_execution_status(job_id, execution_id, status, error_message=None):
    """Update job execution status in database"""
    import asyncpg
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
    conn = await asyncpg.connect(db_url)
    
    try:
        if status == 'running':
            await conn.execute("""
                UPDATE automation.job_executions 
                SET status = $1, started_at = NOW() 
                WHERE execution_id = $2
            """, status, execution_id)
        elif status in ['completed', 'failed']:
            await conn.execute("""
                UPDATE automation.job_executions 
                SET status = $1, completed_at = NOW(), error_message = $3
                WHERE execution_id = $2
            """, status, execution_id, error_message)
        else:
            await conn.execute("""
                UPDATE automation.job_executions 
                SET status = $1 
                WHERE execution_id = $2
            """, status, execution_id)
        
        print(f"Updated job execution {execution_id} status to {status}")
    except Exception as e:
        print(f"Failed to update job execution status: {e}")
    finally:
        await conn.close()

async def create_step_execution(job_execution_id, step_id, step_name, step_type, execution_order):
    """Create step execution record in database"""
    import asyncpg
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
    conn = await asyncpg.connect(db_url)
    
    try:
        step_exec_id = await conn.fetchval("""
            INSERT INTO automation.step_executions 
            (job_execution_id, step_id, step_name, step_type, status, execution_order, started_at)
            VALUES ($1, $2, $3, $4, 'running', $5, NOW())
            RETURNING id
        """, job_execution_id, step_id, step_name, step_type, execution_order)
        
        print(f"Created step execution {step_exec_id} for step {step_id}")
        return step_exec_id
    except Exception as e:
        print(f"Failed to create step execution: {e}")
        return None
    finally:
        await conn.close()

async def update_step_execution_status(step_exec_id, status, output_data=None, error_message=None):
    """Update step execution status in database"""
    import asyncpg
    import json
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Safely serialize output_data
        output_json = '{}'
        if output_data:
            try:
                output_json = json.dumps(output_data)
            except (TypeError, ValueError) as json_error:
                print(f"Warning: Failed to serialize output_data: {json_error}")
                # Fallback to string representation
                output_json = json.dumps({"raw_output": str(output_data)})
        
        if status == 'completed':
            await conn.execute("""
                UPDATE automation.step_executions 
                SET status = $1, completed_at = NOW(), output_data = $2
                WHERE id = $3
            """, status, output_json, step_exec_id)
        elif status == 'failed':
            await conn.execute("""
                UPDATE automation.step_executions 
                SET status = $1, completed_at = NOW(), error_message = $2, output_data = $3
                WHERE id = $4
            """, status, error_message, output_json, step_exec_id)
        else:
            # Handle other statuses (running, etc.)
            await conn.execute("""
                UPDATE automation.step_executions 
                SET status = $1
                WHERE id = $2
            """, status, step_exec_id)
        
        print(f"Updated step execution {step_exec_id} status to {status}")
    except Exception as e:
        print(f"Failed to update step execution status: {e}")
        print(f"Debug info - step_exec_id: {step_exec_id}, status: {status}, output_data type: {type(output_data)}")
    finally:
        await conn.close()

async def get_job_execution_id_by_task_id(task_id):
    """Get job execution ID by Celery task ID"""
    import asyncpg
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Find execution by task ID (stored as execution_id)
        row = await conn.fetchrow("""
            SELECT id FROM automation.job_executions 
            WHERE execution_id = $1::uuid
        """, task_id)
        
        if row:
            logger.info(f"Found job execution {row['id']} for task_id {task_id}")
            return row['id']
        else:
            logger.warning(f"No job execution found for task_id {task_id}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get job execution by task_id: {e}")
        return None
    finally:
        await conn.close()

async def get_job_execution_id(job_id, task_id):
    """Get job execution ID from database"""
    import asyncpg
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Find the most recent queued execution for this job
        row = await conn.fetchrow("""
            SELECT id, execution_id FROM automation.job_executions 
            WHERE job_id = $1 AND status = 'queued'
            ORDER BY created_at DESC 
            LIMIT 1
        """, job_id)
        
        if row:
            return row['id'], row['execution_id']
        return None, None
    except Exception as e:
        print(f"Failed to get job execution ID: {e}")
        return None, None
    finally:
        await conn.close()

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
        print(f"No specific result processing for job type '{job_type}'")
            
    finally:
        await conn.close()



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
        
        # Use Celery task ID as execution ID for better tracking
        task_id = self.request.id
        execution_id = task_id
        job_execution_id = None
        
        if job_id:
            try:
                # Get the job execution ID from database
                job_execution_id = asyncio.run(get_job_execution_id_by_task_id(task_id))
                if job_execution_id:
                    asyncio.run(update_job_execution_status(job_id, task_id, 'running'))
                    print(f"Updated job execution {task_id} to running status")
            except Exception as e:
                print(f"Warning: Failed to update job execution status: {e}")
        
        # Parse workflow_definition if it's a string
        if isinstance(workflow_definition, str):
            workflow_definition = json.loads(workflow_definition)
        
        # Handle both 'steps' and 'nodes' formats for backward compatibility
        steps = workflow_definition.get('steps', [])
        if not steps:
            steps = workflow_definition.get('nodes', [])
        total_steps = len(steps)
        
        results = []
        step_outputs = {}  # Store outputs for next steps
        
        for i, step in enumerate(steps):
            step_exec_id = None
            try:
                step_id = step.get('id')
                step_name = step.get('name', f'Step {i+1}')
                library_name = step.get('library')
                function_name = step.get('function')
                command = step.get('command')
                step_type = step.get('type', 'execute')
                
                print(f"Executing step {step_id}: {step_name}")
                
                # Create step execution record in database
                if job_execution_id:
                    try:
                        step_exec_id = asyncio.run(create_step_execution(
                            job_execution_id, step_id, step_name, 
                            step_type, i + 1
                        ))
                    except Exception as e:
                        print(f"Warning: Failed to create step execution record: {e}")
                
                # Prepare step inputs
                step_inputs = {}
                inputs_config = step.get('inputs', {})
                
                # Handle inputs as dictionary (current format)
                if isinstance(inputs_config, dict):
                    for input_name, input_value in inputs_config.items():
                        if isinstance(input_value, str) and input_value.startswith('{{') and input_value.endswith('}}'):
                            # Template value - resolve from previous step outputs
                            ref = input_value[2:-2].strip()
                            if '.' in ref:
                                parts = ref.split('.')
                                if len(parts) >= 3 and parts[0] == 'steps':
                                    step_ref = parts[1]
                                    output_key = '.'.join(parts[3:])  # Handle nested keys like outputs.active_hosts
                                    if step_ref in step_outputs:
                                        step_inputs[input_name] = step_outputs[step_ref].get(output_key)
                                    else:
                                        print(f"Warning: Step {step_ref} not found in outputs for template {input_value}")
                        else:
                            # Static value
                            step_inputs[input_name] = input_value
                else:
                    # Handle inputs as list (legacy format)
                    for input_def in inputs_config:
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
                
                # Execute the step function or command
                if library_name and function_name:
                    # Import the library (handle hyphen to underscore conversion)
                    library_import_name = library_name.replace('-', '_')
                    library_module = __import__(library_import_name)
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
                    
                    # Update step execution status in database
                    if step_exec_id:
                        try:
                            asyncio.run(update_step_execution_status(step_exec_id, 'completed', result))
                        except Exception as e:
                            print(f"Warning: Failed to update step execution status: {e}")
                elif command and step_type in ['execute', 'command']:
                    # Execute command (local or remote based on target systems)
                    import time
                    
                    start_time = time.time()
                    
                    # Check if there are target systems specified in workflow definition or step
                    target_systems = workflow_definition.get('target_systems', [])
                    step_target_system = step.get('target_system')
                    
                    try:
                        if target_systems or step_target_system:
                            # Remote execution on target systems
                            target_system = step_target_system or target_systems[0]
                            print(f"Executing command on remote target: {target_system}")
                            step_result = _execute_remote_command(command, target_system)
                            
                            # Format the result to match expected structure
                            execution_time = time.time() - start_time
                            
                            # Determine status based on return code
                            status = 'completed' if step_result['returncode'] == 0 else 'failed'
                            
                            step_result = {
                                'step_id': step_id,
                                'step_name': step_name,
                                'status': status,
                                'command': command,
                                'returncode': step_result['returncode'],
                                'stdout': step_result['stdout'],
                                'stderr': step_result['stderr'],
                                'execution_time': execution_time,
                                'target_system': target_system
                            }
                        else:
                            # Local execution (fallback)
                            print(f"Executing command locally: {command}")
                            result = _execute_local_command(command)
                            execution_time = time.time() - start_time
                            
                            # Determine status based on return code
                            status = 'completed' if result['returncode'] == 0 else 'failed'
                            
                            step_result = {
                                'step_id': step_id,
                                'step_name': step_name,
                                'status': status,
                                'command': command,
                                'returncode': result['returncode'],
                                'stdout': result['stdout'],
                                'stderr': result['stderr'],
                                'execution_time': execution_time
                            }
                    except Exception as e:
                        execution_time = time.time() - start_time
                        error_output = {
                            'error': str(e),
                            'execution_time': execution_time,
                            'command': command
                        }
                        
                        step_result = {
                            'step_id': step_id,
                            'step_name': step_name,
                            'status': 'failed',
                            'output': error_output,
                            'inputs': step_inputs
                        }
                        
                        print(f"Command execution failed: {e}")
                    
                    # Update step execution status in database
                    if step_exec_id:
                        try:
                            # For command executions, create proper output data
                            output_data = {
                                'command': step_result.get('command'),
                                'returncode': step_result.get('returncode'),
                                'stdout': step_result.get('stdout'),
                                'stderr': step_result.get('stderr'),
                                'execution_time': step_result.get('execution_time'),
                                'target_system': step_result.get('target_system')
                            } if step_result['status'] in ['completed', 'failed'] and 'returncode' in step_result else step_result.get('output')
                            
                            asyncio.run(update_step_execution_status(
                                step_exec_id, 
                                step_result['status'], 
                                output_data
                            ))
                        except Exception as e:
                            print(f"Warning: Failed to update step execution status: {e}")
                else:
                    # Fallback for steps without library/function/command
                    step_result = {
                        'step_id': step_id,
                        'step_name': step_name,
                        'status': 'completed',
                        'output': f'Step {step_name} completed (no function or command specified)',
                        'inputs': step_inputs
                    }
                    
                    # Update step execution status in database
                    if step_exec_id:
                        try:
                            asyncio.run(update_step_execution_status(step_exec_id, 'completed', step_result['output']))
                        except Exception as e:
                            print(f"Warning: Failed to update step execution status: {e}")
                
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
                
                # Update step execution status in database
                if step_exec_id:
                    try:
                        # Create output data for failed step
                        error_output = {
                            'error': str(step_error),
                            'step_id': step_id,
                            'step_name': step_name
                        }
                        asyncio.run(update_step_execution_status(
                            step_exec_id, 
                            'failed', 
                            output_data=error_output,
                            error_message=str(step_error)
                        ))
                    except Exception as e:
                        print(f"Warning: Failed to update step execution status: {e}")
                
                results.append(step_result)
            
            # Update progress
            progress = int((i + 1) / total_steps * 100)
            self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100})
        
        # Determine final job status based on step results
        failed_steps = [r for r in results if r.get('status') == 'failed']
        successful_steps = [r for r in results if r.get('status') == 'completed']
        
        if failed_steps:
            final_status = 'completed_with_errors'
            message = f'Job {job_id} completed with {len(failed_steps)} failed step(s) out of {len(results)} total'
        elif successful_steps:
            final_status = 'completed_success'
            message = f'Job {job_id} completed successfully with all {len(results)} step(s) successful'
        else:
            final_status = 'failed'
            message = f'Job {job_id} failed - no steps completed successfully'
        
        # Process results based on job type
        final_results = {
            'status': final_status,
            'results': results,
            'message': message,
            'step_summary': {
                'total_steps': len(results),
                'successful_steps': len(successful_steps),
                'failed_steps': len(failed_steps)
            }
        }
        
        # Route results based on job type if job_id is provided
        if job_id:
            try:
                asyncio.run(process_job_results(job_id, results))
            except Exception as e:
                print(f"Warning: Failed to process job results for job {job_id}: {e}")
                # Don't fail the job if result processing fails
        
        # Update job execution status based on step results
        if execution_id:
            try:
                asyncio.run(update_job_execution_status(job_id, execution_id, final_status))
                print(f"Updated job execution {execution_id} to {final_status} status")
            except Exception as e:
                print(f"Warning: Failed to update job execution completion status: {e}")
        
        return final_results
        
    except Exception as exc:
        print(f"Job execution failed: {exc}")
        
        # Update job execution status to failed
        if 'execution_id' in locals() and execution_id:
            try:
                asyncio.run(update_job_execution_status(job_id, execution_id, 'failed', str(exc)))
                print(f"Updated job execution {execution_id} to failed status")
            except Exception as e:
                print(f"Warning: Failed to update job execution failure status: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'job_id': job_id}
        )
        raise

def _execute_remote_command(command, target_system):
    """Execute command on remote system using appropriate method"""
    try:
        # Get target system details from assets
        import asyncio
        import os
        import base64
        from cryptography.fernet import Fernet
        import asyncpg
        
        async def get_asset_details():
            db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
            conn = await asyncpg.connect(db_url)
            try:
                query = "SELECT * FROM assets.assets WHERE ip_address = $1"
                result = await conn.fetchrow(query, target_system)
                return result
            finally:
                await conn.close()
        
        asset = asyncio.run(get_asset_details())
        if not asset:
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': f'Target system {target_system} not found in assets database'
            }
        
        # Decrypt password if available
        password = None
        if asset.get('password_encrypted'):
            try:
                encryption_key = os.environ.get('ENCRYPTION_KEY')
                print(f"DEBUG: ENCRYPTION_KEY = {encryption_key}")
                if encryption_key and encryption_key != 'your-encryption-key-here':
                    if isinstance(encryption_key, str):
                        encryption_key = encryption_key.encode()
                    cipher_suite = Fernet(encryption_key)
                    # The password is already a Fernet token, decrypt directly
                    password = cipher_suite.decrypt(asset['password_encrypted'].encode()).decode()
                else:
                    return {
                        'returncode': 1,
                        'stdout': '',
                        'stderr': 'Encryption key not configured for credential decryption'
                    }
            except Exception as e:
                print(f"DEBUG: Decryption error details: {type(e).__name__}: {str(e)}")
                print(f"DEBUG: Encrypted password: {asset.get('password_encrypted')}")
                print(f"DEBUG: Encryption key type: {type(encryption_key)}")
                return {
                    'returncode': 1,
                    'stdout': '',
                    'stderr': f'Failed to decrypt password: {type(e).__name__}: {str(e)}'
                }
        
        if not password:
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': f'No password available for target system {target_system}'
            }
        
        # For Windows systems, use WinRM
        if asset['os_type'] and 'windows' in asset['os_type'].lower():
            if WindowsPowerShellLibrary is None:
                return {
                    'returncode': 1,
                    'stdout': '',
                    'stderr': 'WindowsPowerShellLibrary not available - import failed at startup'
                }
            
            # Execute PowerShell command via WinRM
            ps = WindowsPowerShellLibrary()
            result = ps.execute_powershell(
                target_host=target_system,
                username=asset.get('username', 'administrator'),
                password=password,
                script=command,
                timeout=30,
                use_ssl=False,  # Use HTTP for port 5985
                port=asset.get('port', 5985)
            )
            
            return {
                'returncode': result.get('exit_code', 0),
                'stdout': result.get('stdout', ''),
                'stderr': result.get('stderr', '')
            }
        else:
            # For Linux systems, use SSH (to be implemented)
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': f'Remote execution for {asset.get("os_type", "unknown")} systems not yet implemented'
            }
            
    except Exception as e:
        return {
            'returncode': 1,
            'stdout': '',
            'stderr': f'Remote execution failed: {str(e)}'
        }

def _execute_local_command(command):
    """Execute command locally on the worker"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'returncode': 124,
            'stdout': '',
            'stderr': 'Command timed out after 300 seconds'
        }
    except Exception as e:
        return {
            'returncode': 1,
            'stdout': '',
            'stderr': f'Local execution failed: {str(e)}'
        }

@app.task
def test_task():
    """Simple test task"""
    return "Hello from Celery worker!"

if __name__ == '__main__':
    app.start()
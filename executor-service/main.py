#!/usr/bin/env python3
"""
Executor Service - Python WinRM Executor Implementation
Processes job queue and executes WinRM commands with pywinrm
"""

import os
import time
import json
import base64
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional

import psycopg2
import psycopg2.extras
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import winrm
from jinja2 import Template

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Executor Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CREDENTIALS_SERVICE_URL = os.getenv("CREDENTIALS_SERVICE_URL", "http://credentials-service:3004")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:3009")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
WORKER_POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "5"))  # seconds
WORKER_ENABLED = os.getenv("WORKER_ENABLED", "true").lower() == "true"

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

class JobExecutor:
    """Job execution engine with queue processing"""
    
    def __init__(self):
        self.running = False
        self.worker_thread = None
    
    def start_worker(self):
        """Start the worker thread"""
        if WORKER_ENABLED and not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Executor worker started")
    
    def stop_worker(self):
        """Stop the worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Executor worker stopped")
    
    def _worker_loop(self):
        """Main worker loop - processes queued job steps"""
        logger.info("Worker loop started")
        
        while self.running:
            try:
                # Get next queued step using SKIP LOCKED
                conn = get_db_connection()
                if not conn:
                    time.sleep(WORKER_POLL_INTERVAL)
                    continue
                
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT jrs.*, jr.parameters as run_parameters, j.definition as job_definition
                        FROM job_run_steps jrs
                        JOIN job_runs jr ON jrs.job_run_id = jr.id
                        JOIN jobs j ON jr.job_id = j.id
                        WHERE jrs.status = 'queued'
                        ORDER BY jrs.id
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    """)
                    
                    step = cursor.fetchone()
                    if not step:
                        # No queued steps, sleep and continue
                        time.sleep(WORKER_POLL_INTERVAL)
                        continue
                    
                    # Process the step
                    logger.info(f"Processing step {step['id']} (run {step['job_run_id']}, type {step['type']})")
                    self._execute_step(step, cursor, conn)
                    
                except Exception as e:
                    logger.error(f"Worker loop error: {e}")
                    conn.rollback()
                finally:
                    conn.close()
                    
            except Exception as e:
                logger.error(f"Critical worker loop error: {e}")
                time.sleep(WORKER_POLL_INTERVAL)
    
    def _execute_step(self, step: Dict[str, Any], cursor, conn):
        """Execute a single job step"""
        step_id = step['id']
        job_run_id = step['job_run_id']
        
        try:
            # Mark step as running
            cursor.execute(
                "UPDATE job_run_steps SET status = 'running', started_at = %s WHERE id = %s",
                (datetime.utcnow(), step_id)
            )
            
            # Update job run status if this is the first step
            cursor.execute(
                "UPDATE job_runs SET status = 'running', started_at = COALESCE(started_at, %s) WHERE id = %s",
                (datetime.utcnow(), job_run_id)
            )
            
            conn.commit()
            
            # Execute based on step type
            if step['type'] == 'winrm.exec':
                result = self._execute_winrm_exec(step)
            elif step['type'] == 'winrm.copy':
                result = self._execute_winrm_copy(step)
            else:
                result = {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': f"Unknown step type: {step['type']}"
                }
            
            # Update step with results
            cursor.execute("""
                UPDATE job_run_steps 
                SET status = %s, exit_code = %s, stdout = %s, stderr = %s, 
                    finished_at = %s, metrics = %s
                WHERE id = %s
            """, (
                result['status'],
                result.get('exit_code'),
                result.get('stdout'),
                result.get('stderr'),
                datetime.utcnow(),
                json.dumps(result.get('metrics', {})),
                step_id
            ))
            
            # Check if job run is complete and send notifications
            self._update_job_run_status(job_run_id, cursor)
            
            conn.commit()
            logger.info(f"Step {step_id} completed with status: {result['status']}")
            
        except Exception as e:
            # Mark step as failed
            cursor.execute("""
                UPDATE job_run_steps 
                SET status = 'failed', stderr = %s, finished_at = %s
                WHERE id = %s
            """, (str(e), datetime.utcnow(), step_id))
            
            self._update_job_run_status(job_run_id, cursor)
            conn.commit()
            
            logger.error(f"Step {step_id} failed: {e}")
    
    def _execute_winrm_exec(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute winrm.exec step"""
        try:
            # Get target and credential info
            target_info = self._get_target_info(step['target_id'])
            if not target_info:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': 'Target not found or not accessible'
                }
            
            credential_data = self._get_credential_data(target_info['credential_ref'])
            if not credential_data:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': 'Credential not found or not accessible'
                }
            
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Render command template
            command_template = Template(step_definition['command'])
            rendered_command = command_template.render(**run_parameters)
            
            # Create WinRM session
            # Use HTTP for port 5985, HTTPS for port 5986
            protocol = 'https' if target_info['port'] == 5986 else 'http'
            winrm_url = f"{protocol}://{target_info['hostname']}:{target_info['port']}/wsman"
            
            logger.info(f"Connecting to WinRM: {winrm_url} with user: {credential_data['username']}")
            
            session = winrm.Session(
                target=winrm_url,
                auth=(credential_data['username'], credential_data['password']),
                transport='ntlm',
                server_cert_validation='ignore'
            )
            
            # Execute command
            shell_type = step['shell'] or 'powershell'
            timeout = step['timeoutsec'] or 60
            
            if shell_type == 'powershell':
                result = session.run_ps(rendered_command)
            else:
                result = session.run_cmd(rendered_command)
            
            # Process results
            status = 'succeeded' if result.status_code == 0 else 'failed'
            stdout = result.std_out.decode('utf-8', errors='replace') if result.std_out else ''
            stderr = result.std_err.decode('utf-8', errors='replace') if result.std_err else ''
            
            return {
                'status': status,
                'exit_code': result.status_code,
                'stdout': stdout,
                'stderr': stderr,
                'metrics': {
                    'target': target_info['hostname'],
                    'shell': shell_type,
                    'rendered_command': rendered_command
                }
            }
            
        except Exception as e:
            logger.error(f"WinRM execution error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'WinRM execution failed: {str(e)}'
            }
    
    def _execute_winrm_copy(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute winrm.copy step"""
        try:
            # Get target and credential info
            target_info = self._get_target_info(step['target_id'])
            if not target_info:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': 'Target not found or not accessible'
                }
            
            credential_data = self._get_credential_data(target_info['credential_ref'])
            if not credential_data:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': 'Credential not found or not accessible'
                }
            
            # Get job definition and parameters
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Render templates
            dest_path_template = Template(step_definition['destPath'])
            dest_path = dest_path_template.render(**run_parameters)
            
            # Decode base64 content
            content = base64.b64decode(step_definition['contentB64']).decode('utf-8')
            
            # Create WinRM session
            # Use HTTP for port 5985, HTTPS for port 5986
            protocol = 'https' if target_info['port'] == 5986 else 'http'
            winrm_url = f"{protocol}://{target_info['hostname']}:{target_info['port']}/wsman"
            
            logger.info(f"Connecting to WinRM: {winrm_url} with user: {credential_data['username']}")
            
            session = winrm.Session(
                target=winrm_url,
                auth=(credential_data['username'], credential_data['password']),
                transport='ntlm',
                server_cert_validation='ignore'
            )
            
            # Write file using PowerShell
            ps_command = f"""
            $content = @'
{content}
'@
            $content | Out-File -FilePath "{dest_path}" -Encoding UTF8
            Write-Output "File written to {dest_path}"
            """
            
            result = session.run_ps(ps_command)
            
            # Process results
            status = 'succeeded' if result.status_code == 0 else 'failed'
            stdout = result.std_out.decode('utf-8', errors='replace') if result.std_out else ''
            stderr = result.std_err.decode('utf-8', errors='replace') if result.std_err else ''
            
            return {
                'status': status,
                'exit_code': result.status_code,
                'stdout': stdout,
                'stderr': stderr,
                'metrics': {
                    'target': target_info['hostname'],
                    'dest_path': dest_path,
                    'content_size': len(content)
                }
            }
            
        except Exception as e:
            logger.error(f"WinRM copy error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'WinRM copy failed: {str(e)}'
            }
    
    def _get_target_info(self, target_id: int) -> Optional[Dict[str, Any]]:
        """Get target information from database"""
        try:
            conn = get_db_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM targets WHERE id = %s",
                (target_id,)
            )
            
            target = cursor.fetchone()
            conn.close()
            
            return dict(target) if target else None
            
        except Exception as e:
            logger.error(f"Error getting target info: {e}")
            return None
    
    def _get_credential_data(self, credential_ref: int) -> Optional[Dict[str, Any]]:
        """Get decrypted credential data from credentials service"""
        try:
            # Call credentials service internal decrypt endpoint
            response = requests.post(
                f"{CREDENTIALS_SERVICE_URL}/internal/decrypt/{credential_ref}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get credential {credential_ref}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting credential data: {e}")
            return None
    
    def _update_job_run_status(self, job_run_id: int, cursor):
        """Update job run status based on step statuses and send notifications"""
        # Check all step statuses
        cursor.execute(
            "SELECT status FROM job_run_steps WHERE job_run_id = %s",
            (job_run_id,)
        )
        step_statuses = [row['status'] for row in cursor.fetchall()]
        
        if not step_statuses:
            return
        
        # Determine overall status
        if any(status == 'failed' for status in step_statuses):
            overall_status = 'failed'
        elif any(status in ['queued', 'running'] for status in step_statuses):
            overall_status = 'running'
        else:
            overall_status = 'succeeded'
        
        # Get current job run status
        cursor.execute(
            "SELECT status FROM job_runs WHERE id = %s",
            (job_run_id,)
        )
        current_status = cursor.fetchone()['status']
        
        # Update job run if status changed and job is complete
        if overall_status in ['succeeded', 'failed'] and current_status != overall_status:
            cursor.execute(
                "UPDATE job_runs SET status = %s, finished_at = %s WHERE id = %s",
                (overall_status, datetime.utcnow(), job_run_id)
            )
            
            # Send notification for completed job
            self._send_job_completion_notification(job_run_id, overall_status, cursor)
            
        elif overall_status == 'running' and current_status != 'running':
            cursor.execute(
                "UPDATE job_runs SET status = %s WHERE id = %s",
                (overall_status, job_run_id)
            )
    
    def _send_job_completion_notification(self, job_run_id: int, status: str, cursor):
        """Send notification for job completion"""
        try:
            # Get job run details with user information
            cursor.execute("""
                SELECT 
                    jr.id as run_id,
                    jr.job_id,
                    jr.status,
                    jr.queued_at,
                    jr.started_at,
                    jr.finished_at,
                    jr.requested_by,
                    j.name as job_name,
                    u.email as user_email,
                    u.username,
                    COUNT(jrs.id) as total_steps,
                    COUNT(CASE WHEN jrs.status = 'succeeded' THEN 1 END) as succeeded_steps,
                    COUNT(CASE WHEN jrs.status = 'failed' THEN 1 END) as failed_steps
                FROM job_runs jr
                JOIN jobs j ON jr.job_id = j.id
                LEFT JOIN users u ON jr.requested_by = u.id
                LEFT JOIN job_run_steps jrs ON jr.id = jrs.job_run_id
                WHERE jr.id = %s
                GROUP BY jr.id, j.name, u.email, u.username
            """, (job_run_id,))
            
            job_info = cursor.fetchone()
            if not job_info or not job_info['user_email']:
                logger.info(f"No email address found for job run {job_run_id}, skipping notification")
                return
            
            # Calculate duration
            duration = "Unknown"
            if job_info['started_at'] and job_info['finished_at']:
                delta = job_info['finished_at'] - job_info['started_at']
                duration = str(delta).split('.')[0]  # Remove microseconds
            
            # Get error details for failed jobs
            error_details = None
            if status == 'failed':
                cursor.execute("""
                    SELECT stderr, stdout 
                    FROM job_run_steps 
                    WHERE job_run_id = %s AND status = 'failed'
                    ORDER BY idx
                    LIMIT 1
                """, (job_run_id,))
                
                error_step = cursor.fetchone()
                if error_step:
                    error_details = error_step['stderr'] or error_step['stdout'] or "Unknown error"
            
            # Prepare notification payload
            notification_payload = {
                "job_id": job_info['job_id'],
                "job_name": job_info['job_name'],
                "run_id": job_info['run_id'],
                "status": status,
                "started_at": job_info['started_at'].isoformat() if job_info['started_at'] else None,
                "finished_at": job_info['finished_at'].isoformat() if job_info['finished_at'] else None,
                "duration": duration,
                "requested_by": job_info['username'],
                "steps_summary": {
                    "total": job_info['total_steps'],
                    "succeeded": job_info['succeeded_steps'],
                    "failed": job_info['failed_steps']
                }
            }
            
            if error_details:
                notification_payload["error_details"] = error_details[:1000]  # Limit error message length
            
            # Send enhanced notification using new system
            try:
                # Determine event type based on status
                event_type = "job_success" if status == "succeeded" else "job_failure"
                
                response = requests.post(
                    f"{NOTIFICATION_SERVICE_URL}/internal/notifications/enhanced",
                    json={
                        "job_run_id": job_run_id,
                        "user_id": job_info['requested_by'],
                        "event_type": event_type,
                        "payload": notification_payload
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Enhanced notifications created for job run {job_run_id}: {result.get('count', 0)} notifications")
                else:
                    logger.error(f"Failed to create enhanced notifications for job run {job_run_id}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error creating enhanced notifications for job run {job_run_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error preparing notification for job run {job_run_id}: {e}")

# Global executor instance
executor = JobExecutor()

@app.on_event("startup")
async def startup_event():
    """Start the executor worker on startup"""
    executor.start_worker()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the executor worker on shutdown"""
    executor.stop_worker()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "executor-service",
        "worker_running": executor.running,
        "worker_enabled": WORKER_ENABLED
    }

@app.get("/status")
async def get_status():
    """Get executor status and statistics"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        # Get queue statistics
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'queued') as queued_steps,
                COUNT(*) FILTER (WHERE status = 'running') as running_steps,
                COUNT(*) FILTER (WHERE status = 'succeeded') as succeeded_steps,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_steps
            FROM job_run_steps
            WHERE finished_at > NOW() - INTERVAL '24 hours' OR status IN ('queued', 'running')
        """)
        
        stats = cursor.fetchone()
        
        return {
            "worker_running": executor.running,
            "worker_enabled": WORKER_ENABLED,
            "poll_interval": WORKER_POLL_INTERVAL,
            "queue_stats": dict(stats)
        }
        
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve status")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3007)
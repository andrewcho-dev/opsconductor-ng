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
import sys
sys.path.append('/home/opsconductor/shared')
from database import get_db_cursor
import hmac
import hashlib
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import winrm
from jinja2 import Template, Environment, BaseLoader, select_autoescape
from ssh_executor import SSHExecutor, SFTPExecutor, SSHExecutionError
import aiohttp
import asyncio

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

# Database connection handled by shared module

class JobExecutor:
    """Job execution engine with queue processing"""
    
    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.ssh_executor = SSHExecutor()
        self.sftp_executor = SFTPExecutor(self.ssh_executor)
    
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
                try:
                    with get_db_cursor() as cursor:
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
                        self._execute_step(step, cursor)
                    
                except Exception as e:
                    logger.error(f"Worker loop error: {e}")
                    
            except Exception as e:
                logger.error(f"Critical worker loop error: {e}")
                time.sleep(WORKER_POLL_INTERVAL)
    
    def _execute_step(self, step: Dict[str, Any], cursor):
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
            
            # Execute based on step type
            if step['type'] == 'winrm.exec':
                result = self._execute_winrm_exec(step)
            elif step['type'] == 'winrm.copy':
                result = self._execute_winrm_copy(step)
            elif step['type'] == 'windows.command':
                result = self._execute_windows_command(step)
            elif step['type'] == 'ssh.exec':
                result = self._execute_ssh_exec(step)
            elif step['type'] == 'ssh.copy':
                result = self._execute_ssh_copy(step)
            elif step['type'] == 'sftp.upload':
                result = self._execute_sftp_upload(step)
            elif step['type'] == 'sftp.download':
                result = self._execute_sftp_download(step)
            elif step['type'] == 'sftp.sync':
                result = self._execute_sftp_sync(step)
            elif step['type'] == 'http.get':
                result = self._execute_http_get(step)
            elif step['type'] == 'http.post':
                result = self._execute_http_post(step)
            elif step['type'] == 'http.put':
                result = self._execute_http_put(step)
            elif step['type'] == 'http.delete':
                result = self._execute_http_delete(step)
            elif step['type'] == 'http.patch':
                result = self._execute_http_patch(step)
            elif step['type'] == 'webhook.call':
                result = self._execute_webhook_call(step)
            elif step['type'] == 'notify.email':
                result = self._execute_notify_email(step)
            elif step['type'] == 'notify.slack':
                result = self._execute_notify_slack(step)
            elif step['type'] == 'notify.teams':
                result = self._execute_notify_teams(step)
            elif step['type'] == 'notify.webhook':
                result = self._execute_notify_webhook(step)
            elif step['type'] == 'notify.conditional':
                result = self._execute_notify_conditional(step)
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
            
            logger.info(f"Step {step_id} completed with status: {result['status']}")
            
        except Exception as e:
            # Mark step as failed
            cursor.execute("""
                UPDATE job_run_steps 
                SET status = 'failed', stderr = %s, finished_at = %s
                WHERE id = %s
            """, (str(e), datetime.utcnow(), step_id))
            
            self._update_job_run_status(job_run_id, cursor)
            
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
    
    def _execute_windows_command(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute windows.command step"""
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
            
            # Generate PowerShell command based on command type
            command_type = step_definition.get('command_type', 'system_info')
            parameters = step_definition.get('parameters', {})
            
            powershell_command = self._generate_windows_command(command_type, parameters)
            
            # Create WinRM session
            protocol = 'https' if target_info['port'] == 5986 else 'http'
            winrm_url = f"{protocol}://{target_info['hostname']}:{target_info['port']}/wsman"
            
            logger.info(f"Executing Windows command '{command_type}' on {winrm_url}")
            
            session = winrm.Session(
                target=winrm_url,
                auth=(credential_data['username'], credential_data['password']),
                transport='ntlm',
                server_cert_validation='ignore'
            )
            
            # Execute PowerShell command
            timeout = step_definition.get('timeoutSec', 60)
            result = session.run_ps(powershell_command)
            
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
                    'command_type': command_type,
                    'generated_command': powershell_command
                }
            }
            
        except Exception as e:
            logger.error(f"Windows command execution error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Windows command execution failed: {str(e)}'
            }
    
    def _generate_windows_command(self, command_type: str, parameters: Dict[str, Any]) -> str:
        """Generate PowerShell command based on command type and parameters"""
        
        if command_type == 'system_info':
            return """
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory, 
CsProcessors, CsSystemType, TimeZone, LastBootUpTime | Format-List
"""
        
        elif command_type == 'disk_space':
            drive = parameters.get('drive', '')
            if drive:
                return f"Get-WmiObject -Class Win32_LogicalDisk -Filter \"DeviceID='{drive}'\" | Select-Object DeviceID, Size, FreeSpace, @{{Name='UsedSpace';Expression={{$_.Size - $_.FreeSpace}}}}, @{{Name='PercentFree';Expression={{[math]::Round(($_.FreeSpace / $_.Size) * 100, 2)}}}} | Format-Table -AutoSize"
            else:
                return "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace, @{Name='UsedSpace';Expression={$_.Size - $_.FreeSpace}}, @{Name='PercentFree';Expression={[math]::Round(($_.FreeSpace / $_.Size) * 100, 2)}} | Format-Table -AutoSize"
        
        elif command_type == 'running_services':
            service_filter = parameters.get('service_filter', '')
            if service_filter:
                return f"Get-Service | Where-Object {{$_.Name -like '*{service_filter}*' -and $_.Status -eq 'Running'}} | Select-Object Name, Status, StartType | Format-Table -AutoSize"
            else:
                return "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, Status, StartType | Format-Table -AutoSize"
        
        elif command_type == 'installed_programs':
            return """
Get-WmiObject -Class Win32_Product | Select-Object Name, Version, Vendor, InstallDate | 
Sort-Object Name | Format-Table -AutoSize
"""
        
        elif command_type == 'network_config':
            return """
Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv6Address, 
DNSServer | Format-List
"""
        
        elif command_type == 'event_logs':
            log_name = parameters.get('log_name', 'System')
            max_events = parameters.get('max_events', 50)
            level = parameters.get('level', '')
            
            if level:
                return f"Get-WinEvent -LogName '{log_name}' -MaxEvents {max_events} | Where-Object {{$_.LevelDisplayName -eq '{level}'}} | Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-Table -Wrap"
            else:
                return f"Get-WinEvent -LogName '{log_name}' -MaxEvents {max_events} | Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-Table -Wrap"
        
        elif command_type == 'process_list':
            process_filter = parameters.get('process_filter', '')
            if process_filter:
                return f"Get-Process | Where-Object {{$_.ProcessName -like '*{process_filter}*'}} | Select-Object ProcessName, Id, CPU, WorkingSet, StartTime | Format-Table -AutoSize"
            else:
                return "Get-Process | Select-Object ProcessName, Id, CPU, WorkingSet, StartTime | Sort-Object CPU -Descending | Select-Object -First 20 | Format-Table -AutoSize"
        
        elif command_type == 'windows_updates':
            return """
if (Get-Module -ListAvailable -Name PSWindowsUpdate) {
    Get-WUList | Select-Object Title, Size, Status | Format-Table -AutoSize
} else {
    Write-Output "PSWindowsUpdate module not installed. Using alternative method..."
    Get-HotFix | Select-Object Description, HotFixID, InstalledOn | Sort-Object InstalledOn -Descending | Select-Object -First 20 | Format-Table -AutoSize
}
"""
        
        elif command_type == 'user_accounts':
            return """
Get-LocalUser | Select-Object Name, Enabled, LastLogon, PasswordLastSet, 
PasswordExpires | Format-Table -AutoSize
"""
        
        elif command_type == 'system_uptime':
            return """
$bootTime = (Get-CimInstance -ClassName Win32_OperatingSystem).LastBootUpTime
$uptime = (Get-Date) - $bootTime
Write-Output "System Boot Time: $bootTime"
Write-Output "Current Uptime: $($uptime.Days) days, $($uptime.Hours) hours, $($uptime.Minutes) minutes"
"""
        
        elif command_type == 'registry_query':
            registry_path = parameters.get('registry_path', '')
            value_name = parameters.get('value_name', '')
            
            if not registry_path:
                return "Write-Error 'Registry path is required'"
            
            if value_name:
                return f"Get-ItemProperty -Path '{registry_path}' -Name '{value_name}' -ErrorAction SilentlyContinue"
            else:
                return f"Get-ItemProperty -Path '{registry_path}' -ErrorAction SilentlyContinue | Format-List"
        
        elif command_type == 'file_operations':
            operation = parameters.get('operation', 'list')
            path = parameters.get('path', '')
            
            if not path:
                return "Write-Error 'Path is required for file operations'"
            
            if operation == 'list':
                file_filter = parameters.get('filter', '*')
                return f"Get-ChildItem -Path '{path}' -Filter '{file_filter}' | Select-Object Name, Length, LastWriteTime, Attributes | Format-Table -AutoSize"
            elif operation == 'check_exists':
                return f"Test-Path -Path '{path}'"
            elif operation == 'get_size':
                return f"if (Test-Path -Path '{path}') {{ (Get-Item -Path '{path}').Length }} else {{ Write-Output 'File not found' }}"
            elif operation == 'get_info':
                return f"Get-Item -Path '{path}' | Select-Object Name, Length, LastWriteTime, LastAccessTime, CreationTime, Attributes | Format-List"
        
        else:
            return f"Write-Error 'Unknown command type: {command_type}'"
    
    def _execute_ssh_exec(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ssh.exec step"""
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
            
            # Use SSH port from target or default to 22
            ssh_port = target_info.get('ssh_port', 22)
            if ssh_port == 5985:  # Default WinRM port, use SSH default
                ssh_port = 22
            
            logger.info(f"Connecting to SSH: {target_info['hostname']}:{ssh_port} with user: {credential_data['username']}")
            
            # Execute command via SSH
            result = self.ssh_executor.execute_command(
                host=target_info['hostname'],
                port=ssh_port,
                username=credential_data['username'],
                password=credential_data.get('password'),
                private_key=credential_data.get('private_key'),
                passphrase=credential_data.get('passphrase'),
                key_type=credential_data.get('key_type', 'rsa'),
                shell=step_definition.get('shell', 'bash'),
                working_directory=step_definition.get('working_directory'),
                environment=step_definition.get('environment'),
                timeout=step_definition.get('timeout_sec', 300),
                command=rendered_command
            )
            
            return result
        
        except SSHExecutionError as e:
            logger.error(f"SSH execution error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SSH execution failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"SSH execution error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SSH execution failed: {str(e)}'
            }
    
    def _execute_ssh_copy(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ssh.copy step (SCP file transfer)"""
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
            
            # Render paths
            source_template = Template(step_definition['source_path'])
            dest_template = Template(step_definition['dest_path'])
            
            source_path = source_template.render(**run_parameters)
            dest_path = dest_template.render(**run_parameters)
            
            # Use SSH port from target or default to 22
            ssh_port = target_info.get('ssh_port', 22)
            if ssh_port == 5985:  # Default WinRM port, use SSH default
                ssh_port = 22
            
            logger.info(f"SSH copy: {source_path} -> {target_info['hostname']}:{dest_path}")
            
            # Execute file copy via SSH/SCP
            with SSHExecutor() as ssh_executor:
                # Connect to target
                connection_info = ssh_executor.connect(
                    hostname=target_info['hostname'],
                    port=ssh_port,
                    credential_data=credential_data,
                    timeout=30
                )
                
                # Upload file
                result = ssh_executor.upload_file(
                    local_path=source_path,
                    remote_path=dest_path,
                    preserve_permissions=True
                )
                
                return {
                    'status': 'succeeded' if result['success'] else 'failed',
                    'exit_code': 0 if result['success'] else 1,
                    'stdout': f"File uploaded successfully: {result['file_size_bytes']} bytes in {result['transfer_time_ms']}ms",
                    'stderr': '',
                    'metrics': {
                        'target': target_info['hostname'],
                        'port': ssh_port,
                        'auth_method': connection_info['auth_method'],
                        'source_path': source_path,
                        'dest_path': dest_path,
                        'file_size_bytes': result['file_size_bytes'],
                        'transfer_time_ms': result['transfer_time_ms'],
                        'transfer_rate_mbps': result['transfer_rate_mbps']
                    }
                }
                
        except SSHExecutionError as e:
            logger.error(f"SSH copy error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SSH copy failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"SSH copy error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SSH copy failed: {str(e)}'
            }
    
    def _execute_sftp_upload(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sftp.upload step"""
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
            
            # Render paths
            local_template = Template(step_definition['local_path'])
            remote_template = Template(step_definition['remote_path'])
            
            local_path = local_template.render(**run_parameters)
            remote_path = remote_template.render(**run_parameters)
            
            # Use SSH port from target or default to 22
            ssh_port = target_info.get('ssh_port', 22)
            if ssh_port == 5985:  # Default WinRM port, use SSH default
                ssh_port = 22
            
            logger.info(f"SFTP upload: {local_path} -> {target_info['hostname']}:{remote_path}")
            
            # Execute file upload via SFTP
            result = self.sftp_executor.upload_file(
                host=target_info['hostname'],
                port=ssh_port,
                username=credential_data['username'],
                password=credential_data.get('password'),
                private_key=credential_data.get('private_key'),
                passphrase=credential_data.get('passphrase'),
                key_type=credential_data.get('key_type', 'rsa'),
                local_path=local_path,
                remote_path=remote_path,
                preserve_permissions=step_definition.get('preserve_permissions', True),
                preserve_timestamps=step_definition.get('preserve_timestamps', True),
                timeout=step_definition.get('timeout_sec', 300)
            )
            
            return result
        
        except Exception as e:
            logger.error(f"SFTP upload error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SFTP upload failed: {str(e)}'
            }
    
    def _execute_sftp_download(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sftp.download step"""
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
            
            # Render paths
            remote_template = Template(step_definition['remote_path'])
            local_template = Template(step_definition['local_path'])
            
            remote_path = remote_template.render(**run_parameters)
            local_path = local_template.render(**run_parameters)
            
            # Use SSH port from target or default to 22
            ssh_port = target_info.get('ssh_port', 22)
            if ssh_port == 5985:  # Default WinRM port, use SSH default
                ssh_port = 22
            
            logger.info(f"SFTP download: {target_info['hostname']}:{remote_path} -> {local_path}")
            
            # Execute file download via SFTP
            result = self.sftp_executor.download_file(
                host=target_info['hostname'],
                port=ssh_port,
                username=credential_data['username'],
                password=credential_data.get('password'),
                private_key=credential_data.get('private_key'),
                passphrase=credential_data.get('passphrase'),
                key_type=credential_data.get('key_type', 'rsa'),
                remote_path=remote_path,
                local_path=local_path,
                preserve_permissions=step_definition.get('preserve_permissions', True),
                preserve_timestamps=step_definition.get('preserve_timestamps', True),
                timeout=step_definition.get('timeout_sec', 300)
            )
            
            return result
        
        except SSHExecutionError as e:
            logger.error(f"SFTP download error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SFTP download failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"SFTP download error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SFTP download failed: {str(e)}'
            }
    
    def _execute_sftp_sync(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sftp.sync step"""
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
            
            # Render paths
            local_template = Template(step_definition['local_path'])
            remote_template = Template(step_definition['remote_path'])
            
            local_path = local_template.render(**run_parameters)
            remote_path = remote_template.render(**run_parameters)
            direction = step_definition.get('direction', 'upload')  # 'upload' or 'download'
            
            # Use SSH port from target or default to 22
            ssh_port = target_info.get('ssh_port', 22)
            if ssh_port == 5985:  # Default WinRM port, use SSH default
                ssh_port = 22
            
            logger.info(f"SFTP sync ({direction}): {local_path} <-> {target_info['hostname']}:{remote_path}")
            
            # Execute directory sync via SFTP
            with SSHExecutor() as ssh_executor:
                # Connect to target
                connection_info = ssh_executor.connect(
                    hostname=target_info['hostname'],
                    port=ssh_port,
                    credential_data=credential_data,
                    timeout=30
                )
                
                # Sync directory
                result = ssh_executor.sync_directory(
                    local_path=local_path,
                    remote_path=remote_path,
                    direction=direction
                )
                
                status_msg = f"Directory sync completed: {result['files_transferred']} files, {result['total_bytes']} bytes"
                if result['errors']:
                    status_msg += f" with {len(result['errors'])} errors"
                
                return {
                    'status': 'succeeded' if result['success'] else 'failed',
                    'exit_code': 0 if result['success'] else 1,
                    'stdout': status_msg,
                    'stderr': '\n'.join(result['errors']) if result['errors'] else '',
                    'metrics': {
                        'target': target_info['hostname'],
                        'port': ssh_port,
                        'auth_method': connection_info['auth_method'],
                        'local_path': local_path,
                        'remote_path': remote_path,
                        'direction': direction,
                        'files_transferred': result['files_transferred'],
                        'total_bytes': result['total_bytes'],
                        'sync_time_ms': result['sync_time_ms'],
                        'transfer_rate_mbps': result['transfer_rate_mbps'],
                        'error_count': len(result['errors'])
                    }
                }
                
        except SSHExecutionError as e:
            logger.error(f"SFTP sync error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SFTP sync failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"SFTP sync error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SFTP sync failed: {str(e)}'
            }
    
    def _execute_http_get(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP GET request"""
        return self._execute_http_request(step, 'GET')
    
    def _execute_http_post(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP POST request"""
        return self._execute_http_request(step, 'POST')
    
    def _execute_http_put(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP PUT request"""
        return self._execute_http_request(step, 'PUT')
    
    def _execute_http_delete(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP DELETE request"""
        return self._execute_http_request(step, 'DELETE')
    
    def _execute_http_patch(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP PATCH request"""
        return self._execute_http_request(step, 'PATCH')
    
    def _execute_http_request(self, step: Dict[str, Any], method: str) -> Dict[str, Any]:
        """Execute HTTP request with authentication and response handling"""
        try:
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Render URL template
            url_template = Template(step_definition['url'])
            url = url_template.render(**run_parameters)
            
            # Prepare request configuration
            timeout = step_definition.get('timeout_sec', 30)
            ssl_verify = step_definition.get('ssl_verify', True)
            max_redirects = step_definition.get('max_redirects', 5)
            
            # Prepare headers
            headers = step_definition.get('headers', {})
            if isinstance(headers, dict):
                # Render header templates
                rendered_headers = {}
                for key, value in headers.items():
                    if isinstance(value, str):
                        header_template = Template(value)
                        rendered_headers[key] = header_template.render(**run_parameters)
                    else:
                        rendered_headers[key] = str(value)
                headers = rendered_headers
            
            # Prepare request body for POST/PUT/PATCH
            request_body = None
            if method in ['POST', 'PUT', 'PATCH'] and 'body' in step_definition:
                body_data = step_definition['body']
                if isinstance(body_data, str):
                    # Render body template
                    body_template = Template(body_data)
                    request_body = body_template.render(**run_parameters)
                elif isinstance(body_data, dict):
                    # JSON body - render each value
                    rendered_body = {}
                    for key, value in body_data.items():
                        if isinstance(value, str):
                            value_template = Template(value)
                            rendered_body[key] = value_template.render(**run_parameters)
                        else:
                            rendered_body[key] = value
                    request_body = json.dumps(rendered_body)
                    if 'Content-Type' not in headers:
                        headers['Content-Type'] = 'application/json'
                else:
                    request_body = json.dumps(body_data)
                    if 'Content-Type' not in headers:
                        headers['Content-Type'] = 'application/json'
            
            # Handle authentication
            auth = None
            auth_type = step_definition.get('auth_type', 'none')
            
            if auth_type == 'basic' and 'auth_username' in step_definition and 'auth_password' in step_definition:
                username_template = Template(step_definition['auth_username'])
                password_template = Template(step_definition['auth_password'])
                username = username_template.render(**run_parameters)
                password = password_template.render(**run_parameters)
                auth = (username, password)
            
            elif auth_type == 'bearer' and 'auth_token' in step_definition:
                token_template = Template(step_definition['auth_token'])
                token = token_template.render(**run_parameters)
                headers['Authorization'] = f'Bearer {token}'
            
            elif auth_type == 'api_key':
                if 'auth_header' in step_definition and 'auth_token' in step_definition:
                    header_name = step_definition['auth_header']
                    token_template = Template(step_definition['auth_token'])
                    token = token_template.render(**run_parameters)
                    headers[header_name] = token
                elif 'auth_token' in step_definition:
                    token_template = Template(step_definition['auth_token'])
                    token = token_template.render(**run_parameters)
                    headers['X-API-Key'] = token
            
            logger.info(f"HTTP {method} request to: {url}")
            
            # Execute HTTP request
            start_time = datetime.utcnow()
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=request_body,
                auth=auth,
                timeout=timeout,
                verify=ssl_verify,
                allow_redirects=True if max_redirects > 0 else False
            )
            
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Store HTTP request details in database
            self._store_http_request(
                step['id'],
                method,
                url,
                headers,
                request_body,
                response.status_code,
                dict(response.headers),
                response.text,
                response_time_ms,
                ssl_verify,
                timeout,
                max_redirects
            )
            
            # Check expected status code
            expected_status = step_definition.get('expected_status', [200, 201, 202, 204])
            if isinstance(expected_status, int):
                expected_status = [expected_status]
            
            success = response.status_code in expected_status
            
            # Prepare response data
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'response_time_ms': response_time_ms
            }
            
            return {
                'status': 'succeeded' if success else 'failed',
                'exit_code': 0 if success else response.status_code,
                'stdout': f"HTTP {method} {url} -> {response.status_code} ({response_time_ms}ms)",
                'stderr': '' if success else f"Unexpected status code: {response.status_code}",
                'metrics': {
                    'method': method,
                    'url': url,
                    'status_code': response.status_code,
                    'response_time_ms': response_time_ms,
                    'response_size_bytes': len(response.content),
                    'ssl_verify': ssl_verify,
                    'auth_type': auth_type
                },
                'response_data': response_data
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"HTTP {method} request timeout: {url}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'HTTP {method} request timeout after {timeout}s'
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"HTTP {method} connection error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'HTTP {method} connection failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"HTTP {method} request error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'HTTP {method} request failed: {str(e)}'
            }
    
    def _execute_webhook_call(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute webhook call with payload and signature"""
        try:
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Add current timestamp to parameters
            run_parameters['current_timestamp'] = datetime.utcnow().isoformat()
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Render URL template
            url_template = Template(step_definition['url'])
            url = url_template.render(**run_parameters)
            
            # Prepare payload
            payload_data = step_definition.get('payload', {})
            if isinstance(payload_data, dict):
                # Render payload templates
                rendered_payload = {}
                for key, value in payload_data.items():
                    if isinstance(value, str):
                        value_template = Template(value)
                        rendered_payload[key] = value_template.render(**run_parameters)
                    else:
                        rendered_payload[key] = value
                payload = rendered_payload
            else:
                payload = payload_data
            
            # Convert payload to JSON
            payload_json = json.dumps(payload)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'OpsConductor-Webhook/1.0'
            }
            
            # Add custom headers
            custom_headers = step_definition.get('headers', {})
            for key, value in custom_headers.items():
                if isinstance(value, str):
                    header_template = Template(value)
                    headers[key] = header_template.render(**run_parameters)
                else:
                    headers[key] = str(value)
            
            # Handle webhook signature
            signature_method = step_definition.get('signature_method')
            signature_header = step_definition.get('signature_header', 'X-Hub-Signature-256')
            signature_secret = step_definition.get('signature_secret')
            signature_value = None
            
            if signature_method and signature_secret:
                secret_template = Template(signature_secret)
                secret = secret_template.render(**run_parameters)
                
                if signature_method == 'hmac-sha256':
                    signature_value = hmac.new(
                        secret.encode('utf-8'),
                        payload_json.encode('utf-8'),
                        hashlib.sha256
                    ).hexdigest()
                    headers[signature_header] = f'sha256={signature_value}'
                elif signature_method == 'hmac-sha1':
                    signature_value = hmac.new(
                        secret.encode('utf-8'),
                        payload_json.encode('utf-8'),
                        hashlib.sha1
                    ).hexdigest()
                    headers[signature_header] = f'sha1={signature_value}'
            
            # Request configuration
            timeout = step_definition.get('timeout_sec', 30)
            max_retries = step_definition.get('max_retries', 3)
            
            logger.info(f"Webhook call to: {url}")
            
            # Execute webhook with retry logic
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    start_time = datetime.utcnow()
                    
                    response = requests.post(
                        url=url,
                        headers=headers,
                        data=payload_json,
                        timeout=timeout,
                        verify=True
                    )
                    
                    end_time = datetime.utcnow()
                    response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    # Store webhook execution details
                    self._store_webhook_execution(
                        step['id'],
                        url,
                        payload,
                        signature_method,
                        signature_header,
                        signature_value,
                        response.status_code,
                        response.text,
                        response_time_ms,
                        attempt,
                        max_retries
                    )
                    
                    # Check if webhook was successful
                    success = 200 <= response.status_code < 300
                    
                    if success:
                        return {
                            'status': 'succeeded',
                            'exit_code': 0,
                            'stdout': f"Webhook delivered successfully: {response.status_code} ({response_time_ms}ms)",
                            'stderr': '',
                            'metrics': {
                                'url': url,
                                'status_code': response.status_code,
                                'response_time_ms': response_time_ms,
                                'payload_size_bytes': len(payload_json),
                                'retry_count': attempt,
                                'signature_method': signature_method
                            }
                        }
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        if attempt < max_retries:
                            # Wait before retry (exponential backoff)
                            wait_time = 2 ** attempt
                            logger.warning(f"Webhook failed (attempt {attempt + 1}), retrying in {wait_time}s: {last_error}")
                            time.sleep(wait_time)
                        continue
                        
                except requests.exceptions.Timeout:
                    last_error = f"Timeout after {timeout}s"
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"Webhook timeout (attempt {attempt + 1}), retrying in {wait_time}s")
                        time.sleep(wait_time)
                    continue
                except requests.exceptions.ConnectionError as e:
                    last_error = f"Connection error: {str(e)}"
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"Webhook connection error (attempt {attempt + 1}), retrying in {wait_time}s: {last_error}")
                        time.sleep(wait_time)
                    continue
            
            # All retries failed
            logger.error(f"Webhook failed after {max_retries + 1} attempts: {last_error}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Webhook failed after {max_retries + 1} attempts: {last_error}'
            }
            
        except Exception as e:
            logger.error(f"Webhook execution error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Webhook execution failed: {str(e)}'
            }
    
    def _store_http_request(self, step_id: int, method: str, url: str, request_headers: dict,
                           request_body: str, status_code: int, response_headers: dict,
                           response_body: str, response_time_ms: int, ssl_verify: bool,
                           timeout_seconds: int, max_redirects: int):
        """Store HTTP request details in database"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO http_requests (
                        job_run_step_id, method, url, request_headers, request_body,
                        response_status_code, response_headers, response_body,
                        response_time_ms, ssl_verify, timeout_seconds, max_redirects
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    step_id, method, url, json.dumps(request_headers), request_body,
                    status_code, json.dumps(response_headers), response_body,
                    response_time_ms, ssl_verify, timeout_seconds, max_redirects
                ))
            
        except Exception as e:
            logger.error(f"Error storing HTTP request details: {e}")
    
    def _store_webhook_execution(self, step_id: int, webhook_url: str, payload: dict,
                                signature_method: str, signature_header: str, signature_value: str,
                                status_code: int, response_body: str, response_time_ms: int,
                                retry_count: int, max_retries: int):
        """Store webhook execution details in database"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO webhook_executions (
                        job_run_step_id, webhook_url, payload, signature_method,
                        signature_header, signature_value, response_status_code,
                        response_body, response_time_ms, retry_count, max_retries
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    step_id, webhook_url, json.dumps(payload), signature_method,
                    signature_header, signature_value, status_code,
                    response_body, response_time_ms, retry_count, max_retries
                ))
            
        except Exception as e:
            logger.error(f"Error storing webhook execution details: {e}")
    
    def _get_target_info(self, target_id: int) -> Optional[Dict[str, Any]]:
        """Get target information from database"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT * FROM targets WHERE id = %s AND deleted_at IS NULL",
                    (target_id,)
                )
                
                target = cursor.fetchone()
                
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
    
    def _execute_notify_email(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notify.email step"""
        try:
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Check send_on condition
            if not self._should_send_notification(step, step_definition):
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': 'Notification skipped based on send_on condition',
                    'stderr': ''
                }
            
            # Get context for template rendering
            context = self._get_notification_context(step)
            
            # Render templates
            subject = self._render_template(
                step_definition.get('subject_template', 'OpsConductor: Job {{ job.name }} - Notification'),
                context
            )
            
            body = self._render_template(
                step_definition.get('body_template', 'Job {{ job.name }} notification from OpsConductor'),
                context
            )
            
            # Store notification execution
            self._store_notification_execution(
                step['id'],
                'email',
                step_definition['recipients'],
                subject,
                body
            )
            
            # Send via notification service
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/internal/notifications/send",
                json={
                    "channel": "email",
                    "recipients": step_definition['recipients'],
                    "subject": subject,
                    "content": body,
                    "metadata": {
                        "job_run_id": step['job_run_id'],
                        "step_id": step['id'],
                        "notification_type": "step_notification"
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': f'Email notification sent to {len(step_definition["recipients"])} recipients',
                    'stderr': ''
                }
            else:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': f'Failed to send email notification: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Email notification error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Email notification failed: {str(e)}'
            }
    
    def _execute_notify_slack(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notify.slack step"""
        try:
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Check send_on condition
            if not self._should_send_notification(step, step_definition):
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': 'Notification skipped based on send_on condition',
                    'stderr': ''
                }
            
            # Get context for template rendering
            context = self._get_notification_context(step)
            
            # Render message template
            message = self._render_template(
                step_definition.get('message_template', 'Job {{ job.name }} notification from OpsConductor'),
                context
            )
            
            # Prepare Slack payload
            payload = {
                "text": message,
                "channel": step_definition.get('channel')
            }
            
            # Store notification execution
            self._store_notification_execution(
                step['id'],
                'slack',
                [step_definition['webhook_url']],
                None,
                json.dumps(payload)
            )
            
            # Send to Slack webhook
            response = requests.post(
                step_definition['webhook_url'],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': 'Slack notification sent successfully',
                    'stderr': ''
                }
            else:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': f'Failed to send Slack notification: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Slack notification failed: {str(e)}'
            }
    
    def _execute_notify_teams(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notify.teams step"""
        try:
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Check send_on condition
            if not self._should_send_notification(step, step_definition):
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': 'Notification skipped based on send_on condition',
                    'stderr': ''
                }
            
            # Get context for template rendering
            context = self._get_notification_context(step)
            
            # Render message template
            message = self._render_template(
                step_definition.get('message_template', 'Job {{ job.name }} notification from OpsConductor'),
                context
            )
            
            # Prepare Teams payload
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "summary": f"Job {context['job']['name']} notification",
                "text": message
            }
            
            # Store notification execution
            self._store_notification_execution(
                step['id'],
                'teams',
                [step_definition['webhook_url']],
                None,
                json.dumps(payload)
            )
            
            # Send to Teams webhook
            response = requests.post(
                step_definition['webhook_url'],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': 'Teams notification sent successfully',
                    'stderr': ''
                }
            else:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': f'Failed to send Teams notification: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Teams notification error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Teams notification failed: {str(e)}'
            }
    
    def _execute_notify_webhook(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notify.webhook step"""
        try:
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Check send_on condition
            if not self._should_send_notification(step, step_definition):
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': 'Notification skipped based on send_on condition',
                    'stderr': ''
                }
            
            # Get context for template rendering
            context = self._get_notification_context(step)
            
            # Render payload template
            payload_str = self._render_template(
                step_definition.get('payload_template', '{"message": "Job {{ job.name }} notification"}'),
                context
            )
            
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = {"message": payload_str}
            
            # Store notification execution
            self._store_notification_execution(
                step['id'],
                'webhook',
                [step_definition['webhook_url']],
                None,
                json.dumps(payload)
            )
            
            # Prepare headers
            headers = {'Content-Type': 'application/json'}
            if 'headers' in step_definition:
                headers.update(step_definition['headers'])
            
            # Send webhook
            response = requests.post(
                step_definition['webhook_url'],
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': 'Webhook notification sent successfully',
                    'stderr': ''
                }
            else:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': f'Failed to send webhook notification: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Webhook notification error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Webhook notification failed: {str(e)}'
            }
    
    def _execute_notify_conditional(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notify.conditional step"""
        try:
            # Get job definition and parameters for template rendering
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Find the step definition in job
            step_definition = job_definition['steps'][step['idx']]
            
            # Get context for condition evaluation
            context = self._get_notification_context(step)
            
            # Evaluate condition
            condition = step_definition['condition']
            if not self._evaluate_condition(condition, context):
                return {
                    'status': 'succeeded',
                    'exit_code': 0,
                    'stdout': f'Conditional notification skipped: condition "{condition}" evaluated to false',
                    'stderr': ''
                }
            
            # Execute the nested notification
            notification_config = step_definition['notification_config']
            
            # Create a temporary step for the nested notification
            temp_step = step.copy()
            temp_job_definition = job_definition.copy()
            temp_job_definition['steps'][step['idx']] = notification_config
            temp_step['job_definition'] = json.dumps(temp_job_definition)
            
            # Execute based on notification type
            if notification_config['type'] == 'notify.email':
                return self._execute_notify_email(temp_step)
            elif notification_config['type'] == 'notify.slack':
                return self._execute_notify_slack(temp_step)
            elif notification_config['type'] == 'notify.teams':
                return self._execute_notify_teams(temp_step)
            elif notification_config['type'] == 'notify.webhook':
                return self._execute_notify_webhook(temp_step)
            else:
                return {
                    'status': 'failed',
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': f'Unknown nested notification type: {notification_config["type"]}'
                }
                
        except Exception as e:
            logger.error(f"Conditional notification error: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'Conditional notification failed: {str(e)}'
            }
    
    def _should_send_notification(self, step: Dict[str, Any], step_definition: Dict[str, Any]) -> bool:
        """Check if notification should be sent based on send_on condition"""
        send_on = step_definition.get('send_on', ['always'])
        
        if 'always' in send_on:
            return True
        
        # Get job run status
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT status FROM job_runs WHERE id = %s",
                    (step['job_run_id'],)
                )
                result = cursor.fetchone()
                
                if not result:
                    return True
                
                job_status = result['status']
                
                if job_status == 'succeeded' and 'success' in send_on:
                    return True
                elif job_status == 'failed' and 'failure' in send_on:
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking send_on condition: {e}")
            return True  # Default to sending on error
    
    def _get_notification_context(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for notification template rendering"""
        try:
            with get_db_cursor(commit=False) as cursor:
                
                # Get job run info with user details
                cursor.execute("""
                    SELECT jr.id as run_id, jr.job_id, jr.status, jr.started_at, jr.finished_at,
                           jr.parameters, j.name as job_name, j.definition,
                           u.username, u.email, u.id as user_id
                    FROM job_runs jr
                    JOIN jobs j ON jr.job_id = j.id
                    LEFT JOIN users u ON jr.requested_by = u.id
                    WHERE jr.id = %s
                """, (step['job_run_id'],))
                
                job_info = cursor.fetchone()
                if not job_info:
                    return {}
                
                # Get target info if step has target_id
                target_info = None
                if step.get('target_id'):
                    cursor.execute("""
                        SELECT id, name, hostname, protocol, port, tags, metadata
                        FROM targets WHERE id = %s
                    """, (step['target_id'],))
                    target_info = cursor.fetchone()
                
                # Get step statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_steps,
                        COUNT(*) FILTER (WHERE status = 'succeeded') as completed_steps,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_steps
                    FROM job_run_steps
                    WHERE job_run_id = %s
                """, (step['job_run_id'],))
                
                step_stats = cursor.fetchone()
                
                # Calculate execution time
                execution_time_ms = 0
                if job_info['started_at'] and job_info['finished_at']:
                    execution_time_ms = int((job_info['finished_at'] - job_info['started_at']).total_seconds() * 1000)
                
                # Build context
                context = {
                    'job': {
                        'id': job_info['job_id'],
                        'name': job_info['job_name'],
                        'status': job_info['status'],
                        'execution_time_ms': execution_time_ms,
                        'total_steps': step_stats['total_steps'],
                        'completed_steps': step_stats['completed_steps'],
                        'failed_steps': step_stats['failed_steps']
                    },
                    'user': {
                        'id': job_info['user_id'],
                        'username': job_info['username'],
                        'email': job_info['email']
                    },
                    'system': {
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
                
                if target_info:
                    context['target'] = dict(target_info)
                
                # Add job parameters
                if job_info['parameters']:
                    context.update(job_info['parameters'])
                
                return context
            
        except Exception as e:
            logger.error(f"Error getting notification context: {e}")
            return {}
    
    def _render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template with context"""
        try:
            env = Environment(
                loader=BaseLoader(),
                autoescape=select_autoescape(['html', 'xml'])
            )
            template = env.from_string(template_str)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_str  # Return original if rendering fails
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a simple condition string"""
        try:
            # Simple condition evaluation - can be extended
            # For now, support basic comparisons like "job.status == 'failed'"
            
            # Replace context variables
            env = Environment(loader=BaseLoader())
            template = env.from_string(f"{{{{ {condition} }}}}")
            result = template.render(**context)
            
            # Convert to boolean
            return result.lower() in ('true', '1', 'yes')
            
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False
    
    def _store_notification_execution(self, step_id: int, notification_type: str, 
                                    recipients: list, subject: str, content: str):
        """Store notification execution in database"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO notification_step_executions 
                    (job_run_step_id, notification_type, recipients, subject, content, delivery_status)
                    VALUES (%s, %s, %s, %s, %s, 'sent')
                """, (step_id, notification_type, json.dumps(recipients), subject, content))
            
        except Exception as e:
            logger.error(f"Error storing notification execution: {e}")

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
    try:
        with get_db_cursor(commit=False) as cursor:
            
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3007)
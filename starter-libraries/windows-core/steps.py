"""
Windows Core Operations Step Library
Provides essential Windows system operations
"""

import subprocess
import os
import shutil
import time
import winreg
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional


class WindowsCoreSteps:
    """Windows Core Operations step implementations"""
    
    def run_powershell(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PowerShell commands on Windows targets"""
        command = params.get('command', '')
        execution_policy = params.get('execution_policy', 'Bypass')
        timeout = params.get('timeout', 300)
        
        if not command:
            return {
                'success': False,
                'error': 'No PowerShell command provided',
                'output': '',
                'exit_code': 1
            }
        
        try:
            # Construct PowerShell command with execution policy
            ps_cmd = [
                'powershell.exe',
                '-ExecutionPolicy', execution_policy,
                '-Command', command
            ]
            
            # Execute command with timeout
            result = subprocess.run(
                ps_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'exit_code': result.returncode,
                'command': command,
                'execution_policy': execution_policy
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'PowerShell command timed out after {timeout} seconds',
                'output': '',
                'exit_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to execute PowerShell command: {str(e)}',
                'output': '',
                'exit_code': -1
            }
    
    def file_copy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Copy files or folders on Windows systems"""
        source_path = params.get('source_path', '')
        destination_path = params.get('destination_path', '')
        overwrite = params.get('overwrite', False)
        recursive = params.get('recursive', True)
        
        if not source_path or not destination_path:
            return {
                'success': False,
                'error': 'Source and destination paths are required',
                'files_copied': 0
            }
        
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not source.exists():
                return {
                    'success': False,
                    'error': f'Source path does not exist: {source_path}',
                    'files_copied': 0
                }
            
            # Check if destination exists and overwrite setting
            if destination.exists() and not overwrite:
                return {
                    'success': False,
                    'error': f'Destination already exists and overwrite is disabled: {destination_path}',
                    'files_copied': 0
                }
            
            files_copied = 0
            
            if source.is_file():
                # Copy single file
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                files_copied = 1
            elif source.is_dir():
                # Copy directory
                if recursive:
                    if destination.exists() and overwrite:
                        shutil.rmtree(destination)
                    shutil.copytree(source, destination, dirs_exist_ok=overwrite)
                    files_copied = sum(1 for _ in destination.rglob('*') if _.is_file())
                else:
                    destination.mkdir(parents=True, exist_ok=True)
                    for item in source.iterdir():
                        if item.is_file():
                            shutil.copy2(item, destination / item.name)
                            files_copied += 1
            
            return {
                'success': True,
                'message': f'Successfully copied {files_copied} files from {source_path} to {destination_path}',
                'files_copied': files_copied,
                'source_path': source_path,
                'destination_path': destination_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to copy files: {str(e)}',
                'files_copied': 0
            }
    
    def service_control(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start, stop, restart, or check status of Windows services"""
        service_name = params.get('service_name', '')
        action = params.get('action', 'status')
        wait_for_status = params.get('wait_for_status', True)
        timeout = params.get('timeout', 60)
        
        if not service_name:
            return {
                'success': False,
                'error': 'Service name is required'
            }
        
        try:
            if action == 'status':
                # Get service status
                cmd = f'Get-Service -Name "{service_name}" | Select-Object Name, Status, StartType'
                result = subprocess.run(
                    ['powershell.exe', '-Command', cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'service_name': service_name,
                        'action': action,
                        'output': result.stdout.strip(),
                        'status': 'Retrieved'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to get service status: {result.stderr}',
                        'service_name': service_name
                    }
            
            elif action in ['start', 'stop', 'restart']:
                # Control service
                if action == 'restart':
                    cmd = f'Restart-Service -Name "{service_name}" -Force'
                elif action == 'start':
                    cmd = f'Start-Service -Name "{service_name}"'
                elif action == 'stop':
                    cmd = f'Stop-Service -Name "{service_name}" -Force'
                
                if wait_for_status:
                    cmd += f'; Wait-Service -Name "{service_name}" -Timeout {timeout}'
                
                result = subprocess.run(
                    ['powershell.exe', '-Command', cmd],
                    capture_output=True,
                    text=True,
                    timeout=timeout + 10
                )
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'service_name': service_name,
                        'action': action,
                        'message': f'Service {service_name} {action} completed successfully',
                        'output': result.stdout.strip()
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to {action} service: {result.stderr}',
                        'service_name': service_name,
                        'action': action
                    }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'service_name': service_name
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Service {action} operation timed out after {timeout} seconds',
                'service_name': service_name,
                'action': action
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to control service: {str(e)}',
                'service_name': service_name,
                'action': action
            }
    
    def registry_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read values from Windows Registry"""
        key_path = params.get('key_path', '')
        value_name = params.get('value_name', '')
        default_value = params.get('default_value', 'Not Found')
        
        if not key_path or not value_name:
            return {
                'success': False,
                'error': 'Registry key path and value name are required'
            }
        
        try:
            # Parse registry path
            if key_path.startswith('HKLM:'):
                root_key = winreg.HKEY_LOCAL_MACHINE
                sub_key = key_path[5:].lstrip('\\')
            elif key_path.startswith('HKCU:'):
                root_key = winreg.HKEY_CURRENT_USER
                sub_key = key_path[5:].lstrip('\\')
            elif key_path.startswith('HKCR:'):
                root_key = winreg.HKEY_CLASSES_ROOT
                sub_key = key_path[5:].lstrip('\\')
            else:
                return {
                    'success': False,
                    'error': 'Registry path must start with HKLM:, HKCU:, or HKCR:'
                }
            
            # Open registry key and read value
            with winreg.OpenKey(root_key, sub_key) as key:
                value, reg_type = winreg.QueryValueEx(key, value_name)
                
                return {
                    'success': True,
                    'key_path': key_path,
                    'value_name': value_name,
                    'value': value,
                    'type': reg_type,
                    'message': f'Successfully read registry value: {value}'
                }
                
        except FileNotFoundError:
            return {
                'success': True,
                'key_path': key_path,
                'value_name': value_name,
                'value': default_value,
                'message': f'Registry key or value not found, returned default: {default_value}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to read registry value: {str(e)}',
                'key_path': key_path,
                'value_name': value_name
            }
    
    def process_control(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start, stop, or monitor Windows processes"""
        action = params.get('action', 'list')
        process_name = params.get('process_name', '')
        arguments = params.get('arguments', '')
        working_directory = params.get('working_directory', '')
        
        try:
            if action == 'list':
                # List processes
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                    try:
                        if not process_name or process_name.lower() in proc.info['name'].lower():
                            processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 2)
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return {
                    'success': True,
                    'action': action,
                    'processes': processes,
                    'count': len(processes),
                    'filter': process_name or 'All processes'
                }
            
            elif action == 'start':
                if not process_name:
                    return {
                        'success': False,
                        'error': 'Process name/path is required for start action'
                    }
                
                # Start process
                cmd = [process_name]
                if arguments:
                    cmd.extend(arguments.split())
                
                cwd = working_directory if working_directory else None
                
                process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                return {
                    'success': True,
                    'action': action,
                    'process_name': process_name,
                    'pid': process.pid,
                    'message': f'Process started successfully with PID {process.pid}'
                }
            
            elif action in ['stop', 'kill']:
                if not process_name:
                    return {
                        'success': False,
                        'error': 'Process name is required for stop/kill action'
                    }
                
                # Find and terminate processes
                terminated = []
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if process_name.lower() in proc.info['name'].lower():
                            if action == 'stop':
                                proc.terminate()
                            else:  # kill
                                proc.kill()
                            terminated.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name']
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return {
                    'success': True,
                    'action': action,
                    'process_name': process_name,
                    'terminated_processes': terminated,
                    'count': len(terminated),
                    'message': f'Successfully {action}ped {len(terminated)} processes'
                }
            
            elif action == 'check':
                if not process_name:
                    return {
                        'success': False,
                        'error': 'Process name is required for check action'
                    }
                
                # Check if process is running
                running_processes = []
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if process_name.lower() in proc.info['name'].lower():
                            running_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name']
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                is_running = len(running_processes) > 0
                
                return {
                    'success': True,
                    'action': action,
                    'process_name': process_name,
                    'is_running': is_running,
                    'running_processes': running_processes,
                    'count': len(running_processes),
                    'message': f'Process {process_name} is {"running" if is_running else "not running"}'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to control process: {str(e)}',
                'action': action,
                'process_name': process_name
            }


# Export step implementations
def get_step_implementations():
    """Return dictionary of step implementations"""
    steps = WindowsCoreSteps()
    return {
        'run_powershell': steps.run_powershell,
        'file_copy': steps.file_copy,
        'service_control': steps.service_control,
        'registry_read': steps.registry_read,
        'process_control': steps.process_control
    }
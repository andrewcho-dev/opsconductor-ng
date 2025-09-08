"""
Generic Block Executor
Handles execution of generic blocks with different connection methods
"""

import asyncio
from typing import Dict, Any, Optional
from .connection_manager import connection_manager, CommandResult, FileOperationResult

class GenericBlockExecutor:
    """Executes generic blocks with appropriate connection methods"""
    
    async def execute_command_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.command block"""
        try:
            # Extract configuration
            target_id = block_config['target']
            connection_method = block_config.get('connection_method', 'auto')
            command = input_data.get('command') or block_config['command']
            shell = block_config.get('shell', 'auto')
            timeout = block_config.get('timeout_seconds', 60)
            working_dir = block_config.get('working_directory', '')
            env_vars = block_config.get('environment_variables', {})
            
            # Connection-specific options
            ssh_options = block_config.get('ssh_options', {})
            winrm_options = block_config.get('winrm_options', {})
            
            # Execute command
            result = await connection_manager.execute_command(
                target_id=target_id,
                command=command,
                connection_method=connection_method,
                shell=shell,
                timeout_seconds=timeout,
                working_directory=working_dir,
                environment_variables=env_vars,
                **ssh_options,
                **winrm_options
            )
            
            # Return structured result
            if result.success:
                return {
                    "success": True,
                    "result": {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.exit_code,
                        "execution_time": result.execution_time_ms,
                        "target": result.target,
                        "connection_type": result.connection_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message or result.stderr,
                    "result": {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.exit_code,
                        "execution_time": result.execution_time_ms,
                        "target": result.target,
                        "connection_type": result.connection_type
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_file_operation_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.file_operation block"""
        try:
            # Extract configuration
            target_id = block_config['target']
            connection_method = block_config.get('connection_method', 'auto')
            operation = block_config['operation']
            source_path = input_data.get('source_path') or block_config.get('source_path', '')
            destination_path = input_data.get('destination_path') or block_config.get('destination_path', '')
            
            # Operation-specific options
            kwargs = {
                'source_path': source_path,
                'destination_path': destination_path,
                'create_directories': block_config.get('create_directories', False),
                'overwrite_existing': block_config.get('overwrite_existing', False),
                'recursive': block_config.get('recursive', False),
                'encoding': block_config.get('encoding', 'utf-8')
            }
            
            # Add file content if provided
            if 'file_content' in input_data:
                kwargs['file_content'] = input_data['file_content']
            
            # Execute file operation
            result = await connection_manager.file_operation(
                target_id=target_id,
                operation=operation,
                connection_method=connection_method,
                **kwargs
            )
            
            # Return structured result
            if result.success:
                return {
                    "success": True,
                    "result": {
                        "operation": result.operation,
                        "path": result.path,
                        "data": result.result,
                        "target": result.target,
                        "connection_type": result.connection_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message,
                    "result": {
                        "operation": result.operation,
                        "path": result.path,
                        "target": result.target,
                        "connection_type": result.connection_type
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_service_control_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.service_control block"""
        try:
            # Extract configuration
            target_id = block_config['target']
            connection_method = block_config.get('connection_method', 'auto')
            service_name = input_data.get('service_name') or block_config['service_name']
            action = block_config['action']
            service_manager = block_config.get('service_manager', 'auto')
            timeout = block_config.get('timeout_seconds', 30)
            
            # Build service command based on connection type and service manager
            handler = connection_manager.get_handler(target_id, connection_method)
            
            if connection_method in ['winrm', 'auto'] and hasattr(handler, 'target_config'):
                os_type = handler.target_config.get('os_type', 'auto')
                if os_type == 'windows' or connection_method == 'winrm':
                    # Windows service commands
                    command_map = {
                        'start': f'net start "{service_name}"',
                        'stop': f'net stop "{service_name}"',
                        'restart': f'net stop "{service_name}" && net start "{service_name}"',
                        'status': f'sc query "{service_name}"',
                        'enable': f'sc config "{service_name}" start= auto',
                        'disable': f'sc config "{service_name}" start= disabled'
                    }
                    shell = 'cmd'
                else:
                    # Linux service commands (systemd)
                    command_map = {
                        'start': f'systemctl start {service_name}',
                        'stop': f'systemctl stop {service_name}',
                        'restart': f'systemctl restart {service_name}',
                        'status': f'systemctl status {service_name}',
                        'enable': f'systemctl enable {service_name}',
                        'disable': f'systemctl disable {service_name}'
                    }
                    shell = 'bash'
            else:
                # Default to Linux commands
                command_map = {
                    'start': f'systemctl start {service_name}',
                    'stop': f'systemctl stop {service_name}',
                    'restart': f'systemctl restart {service_name}',
                    'status': f'systemctl status {service_name}',
                    'enable': f'systemctl enable {service_name}',
                    'disable': f'systemctl disable {service_name}'
                }
                shell = 'bash'
            
            if action not in command_map:
                return {
                    "success": False,
                    "error": f"Unsupported service action: {action}",
                    "result": None
                }
            
            command = command_map[action]
            
            # Execute service command
            result = await connection_manager.execute_command(
                target_id=target_id,
                command=command,
                connection_method=connection_method,
                shell=shell,
                timeout_seconds=timeout
            )
            
            # Parse service status from output
            service_status = self._parse_service_status(result.stdout, result.stderr, action, connection_method)
            
            # Return structured result
            if result.success:
                return {
                    "success": True,
                    "service_status": service_status,
                    "result": {
                        "action": action,
                        "service_name": service_name,
                        "status": service_status,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "target": result.target,
                        "connection_type": result.connection_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message or result.stderr,
                    "service_status": service_status,
                    "result": {
                        "action": action,
                        "service_name": service_name,
                        "status": service_status,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "target": result.target,
                        "connection_type": result.connection_type
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def _parse_service_status(self, stdout: str, stderr: str, action: str, connection_method: str) -> Dict[str, Any]:
        """Parse service status from command output"""
        status = {
            "status": "unknown",
            "enabled": None,
            "pid": None,
            "uptime": None
        }
        
        try:
            if connection_method == 'winrm' or 'sc query' in stdout:
                # Parse Windows service status
                if 'RUNNING' in stdout:
                    status["status"] = "running"
                elif 'STOPPED' in stdout:
                    status["status"] = "stopped"
                elif 'START_PENDING' in stdout:
                    status["status"] = "starting"
                elif 'STOP_PENDING' in stdout:
                    status["status"] = "stopping"
            else:
                # Parse Linux systemctl status
                if 'active (running)' in stdout:
                    status["status"] = "running"
                elif 'inactive (dead)' in stdout:
                    status["status"] = "stopped"
                elif 'failed' in stdout:
                    status["status"] = "failed"
                elif 'activating' in stdout:
                    status["status"] = "starting"
                
                # Extract enabled status
                if 'enabled' in stdout:
                    status["enabled"] = True
                elif 'disabled' in stdout:
                    status["enabled"] = False
        except:
            pass
        
        return status

# Global executor instance
generic_block_executor = GenericBlockExecutor()

# Example usage functions
async def example_windows_dir_listing():
    """Example: Get Windows directory listing via WinRM"""
    
    # Register target
    connection_manager.register_target('win-server-01', {
        'hostname': '192.168.1.100',
        'os_type': 'windows',
        'default_connection': 'winrm',
        'username': 'administrator',
        'password': 'password123',
        'winrm_port': 5985,
        'winrm_use_ssl': False,
        'winrm_transport': 'ntlm'
    })
    
    # Execute command block
    block_config = {
        'target': 'win-server-01',
        'connection_method': 'winrm',
        'command': 'dir C:\\ /B',
        'shell': 'cmd',
        'timeout_seconds': 30
    }
    
    result = await generic_block_executor.execute_command_block(block_config, {})
    print("Windows Directory Listing Result:")
    print(result)
    
    # Execute PowerShell version
    block_config_ps = {
        'target': 'win-server-01',
        'connection_method': 'winrm',
        'command': 'Get-ChildItem -Path C:\\ | Select-Object Name, Length, LastWriteTime | ConvertTo-Json',
        'shell': 'powershell',
        'timeout_seconds': 30
    }
    
    result_ps = await generic_block_executor.execute_command_block(block_config_ps, {})
    print("\nPowerShell Directory Listing Result:")
    print(result_ps)

async def example_file_operations():
    """Example: File operations via WinRM"""
    
    # Check if file exists
    block_config = {
        'target': 'win-server-01',
        'connection_method': 'winrm',
        'operation': 'exists',
        'source_path': 'C:\\Windows\\System32\\notepad.exe'
    }
    
    result = await generic_block_executor.execute_file_operation_block(block_config, {})
    print("File Exists Check:")
    print(result)
    
    # Get file info
    block_config = {
        'target': 'win-server-01',
        'connection_method': 'winrm',
        'operation': 'get_info',
        'source_path': 'C:\\Windows\\System32\\notepad.exe'
    }
    
    result = await generic_block_executor.execute_file_operation_block(block_config, {})
    print("\nFile Info:")
    print(result)

if __name__ == "__main__":
    # Run examples
    asyncio.run(example_windows_dir_listing())
    asyncio.run(example_file_operations())
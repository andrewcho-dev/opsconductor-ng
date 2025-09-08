"""
Connection Manager for Generic Blocks
Handles SSH, WinRM, local, and other connection types
"""

import asyncio
import json
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class ConnectionType(Enum):
    SSH = "ssh"
    WINRM = "winrm"
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    target: str
    connection_type: str
    error_message: Optional[str] = None

@dataclass
class FileOperationResult:
    """Result of file operation"""
    success: bool
    operation: str
    path: str
    result: Any
    target: str
    connection_type: str
    error_message: Optional[str] = None

class ConnectionHandler(ABC):
    """Abstract base class for connection handlers"""
    
    @abstractmethod
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        pass
    
    @abstractmethod
    async def file_operation(self, operation: str, **kwargs) -> FileOperationResult:
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        pass

class WinRMConnectionHandler(ConnectionHandler):
    """Handles WinRM connections to Windows systems"""
    
    def __init__(self, target_config: Dict[str, Any]):
        self.target_config = target_config
        self.hostname = target_config['hostname']
        self.username = target_config.get('username')
        self.password = target_config.get('password')
        self.port = target_config.get('winrm_port', 5985)
        self.ssl_port = target_config.get('winrm_ssl_port', 5986)
        self.use_ssl = target_config.get('winrm_use_ssl', False)
        self.transport = target_config.get('winrm_transport', 'ntlm')
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute command via WinRM"""
        import time
        start_time = time.time()
        
        try:
            # Import winrm library (would need to be installed)
            # from winrm.protocol import Protocol
            
            # For demo purposes, simulate WinRM execution
            # In real implementation, you'd use python-winrm or similar
            
            shell = kwargs.get('shell', 'cmd')
            timeout = kwargs.get('timeout_seconds', 60)
            
            # Simulate WinRM command execution
            if shell == 'powershell':
                # PowerShell command execution
                full_command = f"powershell.exe -Command \"{command}\""
            else:
                # CMD command execution
                full_command = command
            
            # This would be the actual WinRM execution:
            # protocol = Protocol(
            #     endpoint=f'http{"s" if self.use_ssl else ""}://{self.hostname}:{self.port}/wsman',
            #     transport=self.transport,
            #     username=self.username,
            #     password=self.password,
            #     server_cert_validation='ignore'
            # )
            # shell_id = protocol.open_shell()
            # command_id = protocol.run_command(shell_id, full_command)
            # std_out, std_err, status_code = protocol.get_command_output(shell_id, command_id)
            # protocol.cleanup_command(shell_id, command_id)
            # protocol.close_shell(shell_id)
            
            # Simulated response for demo
            if "dir C:\\" in command:
                stdout = """Program Files
Program Files (x86)
Windows
Users
PerfLogs
$Recycle.Bin
System Volume Information"""
                stderr = ""
                exit_code = 0
            elif "Get-ChildItem" in command:
                stdout = json.dumps([
                    {"Name": "Program Files", "Length": None, "LastWriteTime": "2023-01-15T10:30:00", "Attributes": "Directory"},
                    {"Name": "Windows", "Length": None, "LastWriteTime": "2023-01-10T08:15:00", "Attributes": "Directory"},
                    {"Name": "pagefile.sys", "Length": 4294967296, "LastWriteTime": "2023-01-20T12:00:00", "Attributes": "Archive, System, Hidden"}
                ])
                stderr = ""
                exit_code = 0
            else:
                stdout = f"Executed: {full_command}"
                stderr = ""
                exit_code = 0
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return CommandResult(
                success=exit_code == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time_ms=execution_time,
                target=self.hostname,
                connection_type="winrm"
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=execution_time,
                target=self.hostname,
                connection_type="winrm",
                error_message=str(e)
            )
    
    async def file_operation(self, operation: str, **kwargs) -> FileOperationResult:
        """Perform file operation via WinRM"""
        try:
            source_path = kwargs.get('source_path', '')
            
            if operation == "exists":
                # Check if file exists using PowerShell
                command = f"Test-Path '{source_path}'"
                result = await self.execute_command(command, shell='powershell')
                exists = result.stdout.strip().lower() == 'true'
                
                return FileOperationResult(
                    success=result.success,
                    operation=operation,
                    path=source_path,
                    result={"exists": exists},
                    target=self.hostname,
                    connection_type="winrm"
                )
            
            elif operation == "get_info":
                # Get file information using PowerShell
                command = f"Get-Item '{source_path}' | Select-Object Name, Length, LastWriteTime, Attributes | ConvertTo-Json"
                result = await self.execute_command(command, shell='powershell')
                
                if result.success:
                    try:
                        file_info = json.loads(result.stdout)
                        return FileOperationResult(
                            success=True,
                            operation=operation,
                            path=source_path,
                            result=file_info,
                            target=self.hostname,
                            connection_type="winrm"
                        )
                    except json.JSONDecodeError:
                        return FileOperationResult(
                            success=False,
                            operation=operation,
                            path=source_path,
                            result=None,
                            target=self.hostname,
                            connection_type="winrm",
                            error_message="Failed to parse file info JSON"
                        )
                else:
                    return FileOperationResult(
                        success=False,
                        operation=operation,
                        path=source_path,
                        result=None,
                        target=self.hostname,
                        connection_type="winrm",
                        error_message=result.error_message
                    )
            
            elif operation == "list":
                # List directory contents
                directory = source_path or "C:\\"
                command = f"Get-ChildItem '{directory}' | Select-Object Name, Length, LastWriteTime, Attributes | ConvertTo-Json"
                result = await self.execute_command(command, shell='powershell')
                
                if result.success:
                    try:
                        items = json.loads(result.stdout)
                        if not isinstance(items, list):
                            items = [items]  # Single item case
                        
                        return FileOperationResult(
                            success=True,
                            operation=operation,
                            path=directory,
                            result={"items": items, "count": len(items)},
                            target=self.hostname,
                            connection_type="winrm"
                        )
                    except json.JSONDecodeError:
                        return FileOperationResult(
                            success=False,
                            operation=operation,
                            path=directory,
                            result=None,
                            target=self.hostname,
                            connection_type="winrm",
                            error_message="Failed to parse directory listing JSON"
                        )
            
            # Add more file operations as needed...
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation=operation,
                path=kwargs.get('source_path', ''),
                result=None,
                target=self.hostname,
                connection_type="winrm",
                error_message=str(e)
            )
    
    async def test_connection(self) -> bool:
        """Test WinRM connection"""
        try:
            result = await self.execute_command("echo test", timeout_seconds=10)
            return result.success
        except:
            return False

class SSHConnectionHandler(ConnectionHandler):
    """Handles SSH connections to Linux/Unix systems"""
    
    def __init__(self, target_config: Dict[str, Any]):
        self.target_config = target_config
        self.hostname = target_config['hostname']
        self.username = target_config.get('username')
        self.password = target_config.get('password')
        self.private_key = target_config.get('private_key')
        self.port = target_config.get('ssh_port', 22)
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute command via SSH"""
        import time
        start_time = time.time()
        
        try:
            # In real implementation, you'd use paramiko or asyncssh
            # For demo, simulate SSH execution
            
            timeout = kwargs.get('timeout_seconds', 60)
            working_dir = kwargs.get('working_directory', '')
            env_vars = kwargs.get('environment_variables', {})
            
            # Build full command with environment and working directory
            full_command = command
            if working_dir:
                full_command = f"cd {working_dir} && {command}"
            
            if env_vars:
                env_string = " ".join([f"{k}={v}" for k, v in env_vars.items()])
                full_command = f"{env_string} {full_command}"
            
            # Simulated SSH execution
            if "ls" in command or "dir" in command:
                stdout = "file1.txt\nfile2.log\ndirectory1\ndirectory2"
                stderr = ""
                exit_code = 0
            else:
                stdout = f"SSH executed: {full_command}"
                stderr = ""
                exit_code = 0
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return CommandResult(
                success=exit_code == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time_ms=execution_time,
                target=self.hostname,
                connection_type="ssh"
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=execution_time,
                target=self.hostname,
                connection_type="ssh",
                error_message=str(e)
            )
    
    async def file_operation(self, operation: str, **kwargs) -> FileOperationResult:
        """Perform file operation via SSH/SFTP"""
        # Implementation would use SFTP for file operations
        # Similar structure to WinRM but using Unix commands
        pass
    
    async def test_connection(self) -> bool:
        """Test SSH connection"""
        try:
            result = await self.execute_command("echo test", timeout_seconds=10)
            return result.success
        except:
            return False

class LocalConnectionHandler(ConnectionHandler):
    """Handles local command execution"""
    
    def __init__(self, target_config: Dict[str, Any]):
        self.target_config = target_config
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute command locally"""
        import time
        start_time = time.time()
        
        try:
            timeout = kwargs.get('timeout_seconds', 60)
            working_dir = kwargs.get('working_directory')
            env_vars = kwargs.get('environment_variables', {})
            shell = kwargs.get('shell', 'auto')
            
            # Determine shell based on OS if auto
            if shell == 'auto':
                import platform
                if platform.system() == 'Windows':
                    shell = 'cmd'
                else:
                    shell = 'bash'
            
            # Build environment
            import os
            env = os.environ.copy()
            env.update(env_vars)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return CommandResult(
                success=process.returncode == 0,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                exit_code=process.returncode,
                execution_time_ms=execution_time,
                target="localhost",
                connection_type="local"
            )
            
        except asyncio.TimeoutError:
            execution_time = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                stdout="",
                stderr="Command timed out",
                exit_code=-1,
                execution_time_ms=execution_time,
                target="localhost",
                connection_type="local",
                error_message="Command execution timed out"
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=execution_time,
                target="localhost",
                connection_type="local",
                error_message=str(e)
            )
    
    async def file_operation(self, operation: str, **kwargs) -> FileOperationResult:
        """Perform local file operation"""
        # Implementation for local file operations
        pass
    
    async def test_connection(self) -> bool:
        """Test local connection (always true)"""
        return True

class ConnectionManager:
    """Manages connections to different target systems"""
    
    def __init__(self):
        self.handlers: Dict[str, ConnectionHandler] = {}
        self.target_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_target(self, target_id: str, target_config: Dict[str, Any]):
        """Register a target system configuration"""
        self.target_configs[target_id] = target_config
    
    def get_handler(self, target_id: str, connection_method: str = "auto") -> ConnectionHandler:
        """Get connection handler for target"""
        if target_id not in self.target_configs:
            raise ValueError(f"Target {target_id} not found")
        
        target_config = self.target_configs[target_id]
        
        # Determine connection method
        if connection_method == "auto":
            connection_method = target_config.get('default_connection', 'auto')
            
            if connection_method == "auto":
                # Auto-detect based on OS type
                os_type = target_config.get('os_type', 'auto')
                if os_type == 'windows':
                    connection_method = 'winrm'
                elif os_type in ['linux', 'macos']:
                    connection_method = 'ssh'
                else:
                    # Try to detect from hostname
                    if target_config.get('hostname') in ['localhost', '127.0.0.1']:
                        connection_method = 'local'
                    else:
                        connection_method = 'ssh'  # Default fallback
        
        # Create handler if not cached
        handler_key = f"{target_id}_{connection_method}"
        if handler_key not in self.handlers:
            if connection_method == 'winrm':
                self.handlers[handler_key] = WinRMConnectionHandler(target_config)
            elif connection_method == 'ssh':
                self.handlers[handler_key] = SSHConnectionHandler(target_config)
            elif connection_method == 'local':
                self.handlers[handler_key] = LocalConnectionHandler(target_config)
            else:
                raise ValueError(f"Unsupported connection method: {connection_method}")
        
        return self.handlers[handler_key]
    
    async def execute_command(self, target_id: str, command: str, connection_method: str = "auto", **kwargs) -> CommandResult:
        """Execute command on target system"""
        handler = self.get_handler(target_id, connection_method)
        return await handler.execute_command(command, **kwargs)
    
    async def file_operation(self, target_id: str, operation: str, connection_method: str = "auto", **kwargs) -> FileOperationResult:
        """Perform file operation on target system"""
        handler = self.get_handler(target_id, connection_method)
        return await handler.file_operation(operation, **kwargs)
    
    async def test_connection(self, target_id: str, connection_method: str = "auto") -> bool:
        """Test connection to target system"""
        try:
            handler = self.get_handler(target_id, connection_method)
            return await handler.test_connection()
        except:
            return False

# Global connection manager instance
connection_manager = ConnectionManager()
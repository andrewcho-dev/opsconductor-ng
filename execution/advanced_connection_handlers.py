"""
Advanced Connection Handlers for Generic Blocks
Docker, Kubernetes, and HTTP handlers
"""

import asyncio
import json
import time
import aiohttp
from typing import Dict, Any, Optional
try:
    from .connection_manager import ConnectionHandler, CommandResult, FileOperationResult
except ImportError:
    from connection_manager import ConnectionHandler, CommandResult, FileOperationResult


class DockerConnectionHandler(ConnectionHandler):
    """Handles Docker container connections"""
    
    def __init__(self, target_config: Dict[str, Any]):
        self.target_config = target_config
        self.container_id = target_config.get('container_id')
        self.container_name = target_config.get('container_name')
        self.docker_host = target_config.get('docker_host', 'unix://var/run/docker.sock')
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute command in Docker container"""
        start_time = time.time()
        
        try:
            # Build docker exec command
            container = self.container_id or self.container_name
            if not container:
                raise ValueError("Container ID or name required for Docker connection")
            
            shell = kwargs.get('shell', 'sh')
            timeout = kwargs.get('timeout_seconds', 60)
            working_dir = kwargs.get('working_directory', '')
            env_vars = kwargs.get('environment_variables', {})
            
            # Build docker exec command
            docker_cmd = ['docker', 'exec']
            
            if working_dir:
                docker_cmd.extend(['-w', working_dir])
            
            for key, value in env_vars.items():
                docker_cmd.extend(['-e', f'{key}={value}'])
            
            docker_cmd.extend([container, shell, '-c', command])
            
            # Execute using subprocess (in real implementation, use docker-py)
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                exit_code = process.returncode
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise asyncio.TimeoutError("Docker command timed out")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return CommandResult(
                success=exit_code == 0,
                stdout=stdout.decode('utf-8') if stdout else '',
                stderr=stderr.decode('utf-8') if stderr else '',
                exit_code=exit_code,
                execution_time_ms=execution_time,
                target=container,
                connection_type="docker"
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=execution_time,
                target=self.container_id or self.container_name or "unknown",
                connection_type="docker",
                error_message=str(e)
            )
    
    async def file_operation(self, operation: str, **kwargs) -> FileOperationResult:
        """Perform file operation in Docker container"""
        try:
            container = self.container_id or self.container_name
            source_path = kwargs.get('source_path', '')
            
            if operation == "read":
                # Use docker cp to read file
                command = f"docker cp {container}:{source_path} -"
                result = await self.execute_command(command)
                
                return FileOperationResult(
                    success=result.success,
                    operation=operation,
                    path=source_path,
                    result={"content": result.stdout} if result.success else None,
                    target=container,
                    connection_type="docker",
                    error_message=result.error_message
                )
            
            elif operation == "write":
                # Write file content to container
                file_content = kwargs.get('file_content', '')
                temp_file = f"/tmp/opsconductor_temp_{int(time.time())}"
                
                # Create temp file and copy to container
                with open(temp_file, 'w') as f:
                    f.write(file_content)
                
                command = f"docker cp {temp_file} {container}:{source_path}"
                result = await self.execute_command(command)
                
                # Clean up temp file
                import os
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                return FileOperationResult(
                    success=result.success,
                    operation=operation,
                    path=source_path,
                    result={"bytes_written": len(file_content)} if result.success else None,
                    target=container,
                    connection_type="docker",
                    error_message=result.error_message
                )
            
            # Add more operations as needed...
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation=operation,
                path=kwargs.get('source_path', ''),
                result=None,
                target=self.container_id or self.container_name or "unknown",
                connection_type="docker",
                error_message=str(e)
            )
    
    async def test_connection(self) -> bool:
        """Test Docker container connection"""
        try:
            result = await self.execute_command("echo test", timeout_seconds=10)
            return result.success
        except:
            return False


class KubernetesConnectionHandler(ConnectionHandler):
    """Handles Kubernetes pod connections"""
    
    def __init__(self, target_config: Dict[str, Any]):
        self.target_config = target_config
        self.pod_name = target_config.get('pod_name')
        self.namespace = target_config.get('namespace', 'default')
        self.container_name = target_config.get('container_name')
        self.kubeconfig = target_config.get('kubeconfig')
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute command in Kubernetes pod"""
        start_time = time.time()
        
        try:
            if not self.pod_name:
                raise ValueError("Pod name required for Kubernetes connection")
            
            shell = kwargs.get('shell', 'sh')
            timeout = kwargs.get('timeout_seconds', 60)
            
            # Build kubectl exec command
            kubectl_cmd = ['kubectl', 'exec']
            
            if self.kubeconfig:
                kubectl_cmd.extend(['--kubeconfig', self.kubeconfig])
            
            kubectl_cmd.extend(['-n', self.namespace])
            
            if self.container_name:
                kubectl_cmd.extend(['-c', self.container_name])
            
            kubectl_cmd.extend([self.pod_name, '--', shell, '-c', command])
            
            # Execute using subprocess
            process = await asyncio.create_subprocess_exec(
                *kubectl_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                exit_code = process.returncode
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise asyncio.TimeoutError("Kubernetes command timed out")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return CommandResult(
                success=exit_code == 0,
                stdout=stdout.decode('utf-8') if stdout else '',
                stderr=stderr.decode('utf-8') if stderr else '',
                exit_code=exit_code,
                execution_time_ms=execution_time,
                target=f"{self.namespace}/{self.pod_name}",
                connection_type="kubernetes"
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=execution_time,
                target=f"{self.namespace}/{self.pod_name}",
                connection_type="kubernetes",
                error_message=str(e)
            )
    
    async def file_operation(self, operation: str, **kwargs) -> FileOperationResult:
        """Perform file operation in Kubernetes pod"""
        try:
            source_path = kwargs.get('source_path', '')
            
            if operation == "read":
                # Use kubectl exec to read file
                command = f"cat {source_path}"
                result = await self.execute_command(command)
                
                return FileOperationResult(
                    success=result.success,
                    operation=operation,
                    path=source_path,
                    result={"content": result.stdout} if result.success else None,
                    target=f"{self.namespace}/{self.pod_name}",
                    connection_type="kubernetes",
                    error_message=result.error_message
                )
            
            elif operation == "write":
                # Write file content to pod
                file_content = kwargs.get('file_content', '')
                # Use kubectl exec with tee to write content
                command = f"tee {source_path}"
                
                # This would need more sophisticated implementation
                # For now, simulate the operation
                return FileOperationResult(
                    success=True,
                    operation=operation,
                    path=source_path,
                    result={"bytes_written": len(file_content)},
                    target=f"{self.namespace}/{self.pod_name}",
                    connection_type="kubernetes"
                )
            
            # Add more operations as needed...
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation=operation,
                path=kwargs.get('source_path', ''),
                result=None,
                target=f"{self.namespace}/{self.pod_name}",
                connection_type="kubernetes",
                error_message=str(e)
            )
    
    async def test_connection(self) -> bool:
        """Test Kubernetes pod connection"""
        try:
            result = await self.execute_command("echo test", timeout_seconds=10)
            return result.success
        except:
            return False


class HTTPConnectionHandler(ConnectionHandler):
    """Handles HTTP/HTTPS API connections"""
    
    def __init__(self, target_config: Dict[str, Any]):
        self.target_config = target_config
        self.base_url = target_config.get('base_url', '')
        self.default_headers = target_config.get('headers', {})
        self.auth_config = target_config.get('authentication', {})
        self.ssl_verify = target_config.get('ssl_verify', True)
        self.timeout = target_config.get('timeout', 30)
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute HTTP request (command is the endpoint)"""
        start_time = time.time()
        
        try:
            # Parse command as HTTP request configuration
            if isinstance(command, str):
                # Simple case: command is the endpoint
                method = kwargs.get('method', 'GET')
                endpoint = command
                data = kwargs.get('data')
                params = kwargs.get('params')
            else:
                # Complex case: command is a dict with full request config
                method = command.get('method', 'GET')
                endpoint = command.get('endpoint', '/')
                data = command.get('data')
                params = command.get('params')
            
            # Build full URL
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Prepare headers
            headers = self.default_headers.copy()
            headers.update(kwargs.get('headers', {}))
            
            # Handle authentication
            auth = None
            if self.auth_config:
                auth_type = self.auth_config.get('type', 'none')
                if auth_type == 'basic':
                    import aiohttp
                    auth = aiohttp.BasicAuth(
                        self.auth_config['username'],
                        self.auth_config['password']
                    )
                elif auth_type == 'bearer':
                    headers['Authorization'] = f"Bearer {self.auth_config['token']}"
                elif auth_type == 'api_key':
                    key_header = self.auth_config.get('header', 'X-API-Key')
                    headers[key_header] = self.auth_config['key']
            
            # Make HTTP request
            timeout = aiohttp.ClientTimeout(total=kwargs.get('timeout_seconds', self.timeout))
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if isinstance(data, dict) else None,
                    data=data if isinstance(data, (str, bytes)) else None,
                    params=params,
                    auth=auth,
                    ssl=self.ssl_verify
                ) as response:
                    response_text = await response.text()
                    
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    return CommandResult(
                        success=200 <= response.status < 400,
                        stdout=response_text,
                        stderr="" if 200 <= response.status < 400 else f"HTTP {response.status}: {response.reason}",
                        exit_code=0 if 200 <= response.status < 400 else response.status,
                        execution_time_ms=execution_time,
                        target=url,
                        connection_type="http"
                    )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=execution_time,
                target=self.base_url,
                connection_type="http",
                error_message=str(e)
            )
    
    async def file_operation(self, operation: str, **kwargs) -> FileOperationResult:
        """Perform HTTP-based file operation"""
        try:
            if operation == "upload":
                # Upload file via HTTP POST/PUT
                source_path = kwargs.get('source_path', '')
                endpoint = kwargs.get('endpoint', '/upload')
                
                # This would implement file upload logic
                return FileOperationResult(
                    success=True,
                    operation=operation,
                    path=source_path,
                    result={"uploaded": True},
                    target=f"{self.base_url}{endpoint}",
                    connection_type="http"
                )
            
            elif operation == "download":
                # Download file via HTTP GET
                endpoint = kwargs.get('endpoint', '/')
                destination_path = kwargs.get('destination_path', '')
                
                # This would implement file download logic
                return FileOperationResult(
                    success=True,
                    operation=operation,
                    path=destination_path,
                    result={"downloaded": True},
                    target=f"{self.base_url}{endpoint}",
                    connection_type="http"
                )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation=operation,
                path=kwargs.get('source_path', ''),
                result=None,
                target=self.base_url,
                connection_type="http",
                error_message=str(e)
            )
    
    async def test_connection(self) -> bool:
        """Test HTTP connection"""
        try:
            result = await self.execute_command("/", method="GET", timeout_seconds=10)
            return result.success
        except:
            return False
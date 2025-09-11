#!/usr/bin/env python3
"""
SSH Executor Module
Handles SSH connections and command execution using paramiko
"""

import os
import io
import stat
import time
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

import paramiko
from paramiko import SSHClient, AutoAddPolicy, RSAKey, Ed25519Key, ECDSAKey, DSSKey
from paramiko.ssh_exception import SSHException, AuthenticationException, NoValidConnectionsError

logger = logging.getLogger(__name__)

class SSHExecutionError(Exception):
    """Custom exception for SSH execution errors"""
    pass

class SSHExecutor:
    """SSH command executor using paramiko"""
    
    def __init__(self):
        self.connections = {}  # Cache SSH connections
        
    def _get_key_from_string(self, private_key_str: str, passphrase: Optional[str] = None, key_type: str = 'rsa') -> paramiko.PKey:
        """Convert private key string to paramiko key object"""
        try:
            key_file = io.StringIO(private_key_str)
            
            # Try different key types
            key_classes = {
                'rsa': RSAKey,
                'ed25519': Ed25519Key,
                'ecdsa': ECDSAKey,
                'dsa': DSSKey
            }
            
            # First try the specified key type
            if key_type in key_classes:
                try:
                    return key_classes[key_type].from_private_key(key_file, password=passphrase)
                except Exception as e:
                    logger.debug(f"Failed to load {key_type} key: {e}")
                    key_file.seek(0)
            
            # Try all key types if the specified one fails
            for ktype, key_class in key_classes.items():
                if ktype == key_type:
                    continue  # Already tried
                try:
                    key_file.seek(0)
                    return key_class.from_private_key(key_file, password=passphrase)
                except Exception as e:
                    logger.debug(f"Failed to load {ktype} key: {e}")
                    continue
                    
            raise SSHExecutionError("Unable to load private key - unsupported format or invalid passphrase")
            
        except Exception as e:
            raise SSHExecutionError(f"Error parsing private key: {str(e)}")
    
    def _create_connection(self, host: str, port: int, username: str, 
                          password: Optional[str] = None, 
                          private_key: Optional[str] = None,
                          passphrase: Optional[str] = None,
                          key_type: str = 'rsa',
                          timeout: int = 30) -> SSHClient:
        """Create SSH connection"""
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            
            # Prepare authentication
            auth_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': timeout,
                'allow_agent': False,
                'look_for_keys': False
            }
            
            if private_key:
                # Key-based authentication
                pkey = self._get_key_from_string(private_key, passphrase, key_type)
                auth_kwargs['pkey'] = pkey
            elif password:
                # Password authentication
                auth_kwargs['password'] = password
            else:
                raise SSHExecutionError("No authentication method provided")
            
            # Connect
            client.connect(**auth_kwargs)
            logger.info(f"SSH connection established to {host}:{port} as {username}")
            return client
            
        except AuthenticationException as e:
            raise SSHExecutionError(f"SSH authentication failed: {str(e)}")
        except NoValidConnectionsError as e:
            raise SSHExecutionError(f"SSH connection failed: {str(e)}")
        except SSHException as e:
            raise SSHExecutionError(f"SSH error: {str(e)}")
        except Exception as e:
            raise SSHExecutionError(f"Unexpected SSH error: {str(e)}")
    
    def _get_connection(self, connection_key: str, **kwargs) -> SSHClient:
        """Get cached connection or create new one"""
        if connection_key in self.connections:
            client = self.connections[connection_key]
            try:
                # Test connection
                transport = client.get_transport()
                if transport and transport.is_active():
                    return client
                else:
                    # Connection is dead, remove from cache
                    del self.connections[connection_key]
            except:
                # Connection is dead, remove from cache
                if connection_key in self.connections:
                    del self.connections[connection_key]
        
        # Create new connection
        client = self._create_connection(**kwargs)
        self.connections[connection_key] = client
        return client
    
    def execute_command(self, host: str, port: int, username: str, command: str,
                       password: Optional[str] = None,
                       private_key: Optional[str] = None,
                       passphrase: Optional[str] = None,
                       key_type: str = 'rsa',
                       shell: str = 'bash',
                       working_directory: Optional[str] = None,
                       environment: Optional[Dict[str, str]] = None,
                       timeout: int = 300) -> Dict[str, Any]:
        """Execute SSH command"""
        
        connection_key = f"{username}@{host}:{port}"
        start_time = time.time()
        
        try:
            # Get SSH connection
            client = self._get_connection(
                connection_key,
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
                key_type=key_type,
                timeout=min(timeout, 30)  # Connection timeout
            )
            
            # Prepare command
            full_command = command
            
            # Add working directory change if specified
            if working_directory:
                full_command = f"cd {working_directory} && {full_command}"
            
            # Add environment variables if specified
            if environment:
                env_vars = ' '.join([f"{k}='{v}'" for k, v in environment.items()])
                full_command = f"env {env_vars} {full_command}"
            
            # Use specified shell
            if shell != 'bash':
                full_command = f"{shell} -c '{full_command}'"
            
            logger.info(f"Executing SSH command on {host}: {command}")
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(full_command, timeout=timeout)
            
            # Get results
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8', errors='replace')
            stderr_data = stderr.read().decode('utf-8', errors='replace')
            
            execution_time = int((time.time() - start_time) * 1000)
            
            result = {
                'status': 'succeeded' if exit_code == 0 else 'failed',
                'exit_code': exit_code,
                'stdout': stdout_data,
                'stderr': stderr_data,
                'execution_time_ms': execution_time,
                'command': command,
                'host': host,
                'username': username
            }
            
            logger.info(f"SSH command completed with exit code {exit_code} in {execution_time}ms")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"SSH command execution failed: {error_msg}")
            
            return {
                'status': 'failed',
                'exit_code': -1,
                'stdout': '',
                'stderr': error_msg,
                'execution_time_ms': execution_time,
                'command': command,
                'host': host,
                'username': username
            }
    
    def test_connection(self, host: str, port: int, username: str,
                       password: Optional[str] = None,
                       private_key: Optional[str] = None,
                       passphrase: Optional[str] = None,
                       key_type: str = 'rsa',
                       timeout: int = 30) -> Dict[str, Any]:
        """Test SSH connection and gather system information"""
        
        start_time = time.time()
        
        try:
            # Create connection
            client = self._create_connection(
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
                key_type=key_type,
                timeout=timeout
            )
            
            # Get system information
            commands = {
                'hostname': 'hostname',
                'os_info': 'uname -a',
                'uptime': 'uptime',
                'disk_usage': 'df -h /',
                'memory_info': 'free -h',
                'current_user': 'whoami',
                'shell': 'echo $SHELL',
                'python_version': 'python3 --version 2>/dev/null || python --version 2>/dev/null || echo "Python not found"'
            }
            
            system_info = {}
            for key, cmd in commands.items():
                try:
                    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code == 0:
                        system_info[key] = stdout.read().decode('utf-8', errors='replace').strip()
                    else:
                        system_info[key] = f"Command failed: {stderr.read().decode('utf-8', errors='replace').strip()}"
                except Exception as e:
                    system_info[key] = f"Error: {str(e)}"
            
            # Close test connection
            client.close()
            
            connection_time = int((time.time() - start_time) * 1000)
            
            return {
                'status': 'success',
                'connection_time_ms': connection_time,
                'system_info': system_info,
                'message': f'SSH connection successful to {host}:{port}'
            }
            
        except Exception as e:
            connection_time = int((time.time() - start_time) * 1000)
            return {
                'status': 'failed',
                'connection_time_ms': connection_time,
                'error': str(e),
                'message': f'SSH connection failed to {host}:{port}'
            }
    
    def close_connection(self, host: str, port: int, username: str):
        """Close cached SSH connection"""
        connection_key = f"{username}@{host}:{port}"
        if connection_key in self.connections:
            try:
                self.connections[connection_key].close()
            except:
                pass
            del self.connections[connection_key]
            logger.info(f"Closed SSH connection to {connection_key}")
    
    def close_all_connections(self):
        """Close all cached SSH connections"""
        for connection_key, client in list(self.connections.items()):
            try:
                client.close()
            except:
                pass
        self.connections.clear()
        logger.info("Closed all SSH connections")


class SFTPExecutor:
    """SFTP file transfer executor using paramiko"""
    
    def __init__(self, ssh_executor: SSHExecutor):
        self.ssh_executor = ssh_executor
    
    def _get_sftp_client(self, connection_key: str, **kwargs):
        """Get SFTP client from SSH connection"""
        ssh_client = self.ssh_executor._get_connection(connection_key, **kwargs)
        return ssh_client.open_sftp()
    
    def upload_file(self, host: str, port: int, username: str, 
                   local_path: str, remote_path: str,
                   password: Optional[str] = None,
                   private_key: Optional[str] = None,
                   passphrase: Optional[str] = None,
                   key_type: str = 'rsa',
                   preserve_permissions: bool = True,
                   preserve_timestamps: bool = True,
                   timeout: int = 300) -> Dict[str, Any]:
        """Upload file via SFTP"""
        
        connection_key = f"{username}@{host}:{port}"
        start_time = time.time()
        
        try:
            # Get SFTP client
            sftp = self._get_sftp_client(
                connection_key,
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
                key_type=key_type,
                timeout=min(timeout, 30)
            )
            
            # Check if local file exists
            if not os.path.exists(local_path):
                raise SSHExecutionError(f"Local file not found: {local_path}")
            
            # Get file size
            file_size = os.path.getsize(local_path)
            
            # Upload file
            logger.info(f"Uploading {local_path} to {host}:{remote_path}")
            sftp.put(local_path, remote_path)
            
            # Preserve permissions if requested
            if preserve_permissions:
                local_stat = os.stat(local_path)
                sftp.chmod(remote_path, local_stat.st_mode)
            
            # Preserve timestamps if requested
            if preserve_timestamps:
                local_stat = os.stat(local_path)
                sftp.utime(remote_path, (local_stat.st_atime, local_stat.st_mtime))
            
            sftp.close()
            
            transfer_time = int((time.time() - start_time) * 1000)
            transfer_speed = int(file_size / (transfer_time / 1000)) if transfer_time > 0 else 0
            
            return {
                'status': 'succeeded',
                'operation': 'upload',
                'local_path': local_path,
                'remote_path': remote_path,
                'file_size': file_size,
                'transfer_time_ms': transfer_time,
                'transfer_speed_bps': transfer_speed,
                'message': f'Successfully uploaded {local_path} to {remote_path}'
            }
            
        except Exception as e:
            transfer_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"SFTP upload failed: {error_msg}")
            
            return {
                'status': 'failed',
                'operation': 'upload',
                'local_path': local_path,
                'remote_path': remote_path,
                'transfer_time_ms': transfer_time,
                'error': error_msg
            }
    
    def download_file(self, host: str, port: int, username: str,
                     remote_path: str, local_path: str,
                     password: Optional[str] = None,
                     private_key: Optional[str] = None,
                     passphrase: Optional[str] = None,
                     key_type: str = 'rsa',
                     preserve_permissions: bool = True,
                     preserve_timestamps: bool = True,
                     timeout: int = 300) -> Dict[str, Any]:
        """Download file via SFTP"""
        
        connection_key = f"{username}@{host}:{port}"
        start_time = time.time()
        
        try:
            # Get SFTP client
            sftp = self._get_sftp_client(
                connection_key,
                host=host,
                port=port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
                key_type=key_type,
                timeout=min(timeout, 30)
            )
            
            # Check if remote file exists
            try:
                remote_stat = sftp.stat(remote_path)
                file_size = remote_stat.st_size
            except FileNotFoundError:
                raise SSHExecutionError(f"Remote file not found: {remote_path}")
            
            # Create local directory if needed
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            # Download file
            logger.info(f"Downloading {remote_path} from {host} to {local_path}")
            sftp.get(remote_path, local_path)
            
            # Preserve permissions if requested
            if preserve_permissions:
                os.chmod(local_path, remote_stat.st_mode)
            
            # Preserve timestamps if requested
            if preserve_timestamps:
                os.utime(local_path, (remote_stat.st_atime, remote_stat.st_mtime))
            
            sftp.close()
            
            transfer_time = int((time.time() - start_time) * 1000)
            transfer_speed = int(file_size / (transfer_time / 1000)) if transfer_time > 0 else 0
            
            return {
                'status': 'succeeded',
                'operation': 'download',
                'remote_path': remote_path,
                'local_path': local_path,
                'file_size': file_size,
                'transfer_time_ms': transfer_time,
                'transfer_speed_bps': transfer_speed,
                'message': f'Successfully downloaded {remote_path} to {local_path}'
            }
            
        except Exception as e:
            transfer_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"SFTP download failed: {error_msg}")
            
            return {
                'status': 'failed',
                'operation': 'download',
                'remote_path': remote_path,
                'local_path': local_path,
                'transfer_time_ms': transfer_time,
                'error': error_msg
            }
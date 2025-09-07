"""
SFTP Execution Utility
Handles SFTP file synchronization operations with connection management and error handling
"""

import json
import os
import stat
from typing import Dict, Any, Optional, List, Tuple
from jinja2 import Template
from datetime import datetime
import paramiko
import sys

# Add shared module to path
sys.path.append('/home/opsconductor')
from shared.logging import get_logger

logger = get_logger("executor.sftp")

class SFTPExecutor:
    """Handles SFTP operations with connection management"""
    
    def __init__(self):
        self.ssh_client = None
        self.sftp_client = None
    
    def execute_sftp_sync(self, step: Dict[str, Any], target_info: Dict[str, Any], credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SFTP synchronization operation
        
        Args:
            step: Step execution context
            target_info: Target server information
            credential_data: Authentication credentials
            
        Returns:
            Dict containing execution results
        """
        try:
            # Parse step context
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            step_definition = job_definition['steps'][step['idx']]
            
            # Prepare sync configuration
            sync_config = self._prepare_sync_config(step_definition, run_parameters)
            connection_config = self._prepare_connection_config(target_info, credential_data)
            
            # Execute sync operation
            start_time = datetime.utcnow()
            result = self._perform_sync_operation(sync_config, connection_config)
            end_time = datetime.utcnow()
            
            # Add timing information
            result['execution_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info(f"SFTP sync completed: {sync_config['direction']} - {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"SFTP sync execution failed: {e}")
            return {
                'status': 'failed',
                'exit_code': 1,
                'stdout': '',
                'stderr': f'SFTP sync failed: {str(e)}',
                'execution_time_ms': 0,
                'files_transferred': 0,
                'bytes_transferred': 0
            }
        finally:
            self._cleanup_connections()
    
    def _prepare_sync_config(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare synchronization configuration"""
        # Render path templates
        local_template = Template(step_definition['local_path'])
        remote_template = Template(step_definition['remote_path'])
        
        local_path = local_template.render(**run_parameters)
        remote_path = remote_template.render(**run_parameters)
        
        return {
            'local_path': local_path,
            'remote_path': remote_path,
            'direction': step_definition.get('direction', 'upload'),
            'recursive': step_definition.get('recursive', True),
            'preserve_permissions': step_definition.get('preserve_permissions', True),
            'preserve_timestamps': step_definition.get('preserve_timestamps', True),
            'overwrite_existing': step_definition.get('overwrite_existing', True),
            'exclude_patterns': step_definition.get('exclude_patterns', []),
            'include_patterns': step_definition.get('include_patterns', []),
            'dry_run': step_definition.get('dry_run', False)
        }
    
    def _prepare_connection_config(self, target_info: Dict[str, Any], credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare SSH/SFTP connection configuration"""
        # Use SSH port from target or default to 22
        ssh_port = target_info.get('ssh_port', 22)
        if ssh_port == 5985:  # Default WinRM port, use SSH default
            ssh_port = 22
        
        return {
            'hostname': target_info['hostname'],
            'port': ssh_port,
            'username': credential_data.get('username'),
            'password': credential_data.get('password'),
            'private_key': credential_data.get('private_key'),
            'private_key_passphrase': credential_data.get('private_key_passphrase'),
            'timeout': 30,
            'banner_timeout': 30,
            'auth_timeout': 30
        }
    
    def _perform_sync_operation(self, sync_config: Dict[str, Any], connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual sync operation"""
        # Establish connection
        self._connect_ssh(connection_config)
        
        # Validate paths
        self._validate_sync_paths(sync_config)
        
        # Perform sync based on direction
        if sync_config['direction'] == 'upload':
            return self._sync_upload(sync_config)
        elif sync_config['direction'] == 'download':
            return self._sync_download(sync_config)
        else:
            raise ValueError(f"Unsupported sync direction: {sync_config['direction']}")
    
    def _connect_ssh(self, config: Dict[str, Any]) -> None:
        """Establish SSH connection"""
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Prepare authentication
        auth_kwargs = {
            'hostname': config['hostname'],
            'port': config['port'],
            'username': config['username'],
            'timeout': config['timeout'],
            'banner_timeout': config['banner_timeout'],
            'auth_timeout': config['auth_timeout']
        }
        
        # Add authentication method
        if config.get('private_key'):
            # Use private key authentication
            private_key = self._load_private_key(config['private_key'], config.get('private_key_passphrase'))
            auth_kwargs['pkey'] = private_key
        elif config.get('password'):
            # Use password authentication
            auth_kwargs['password'] = config['password']
        else:
            raise ValueError("No valid authentication method provided")
        
        # Connect
        self.ssh_client.connect(**auth_kwargs)
        
        # Open SFTP channel
        self.sftp_client = self.ssh_client.open_sftp()
        
        logger.info(f"SFTP connection established to {config['hostname']}:{config['port']}")
    
    def _load_private_key(self, private_key_data: str, passphrase: Optional[str] = None) -> paramiko.PKey:
        """Load private key from string data"""
        from io import StringIO
        
        key_file = StringIO(private_key_data)
        
        # Try different key types
        key_types = [
            paramiko.RSAKey,
            paramiko.DSSKey,
            paramiko.ECDSAKey,
            paramiko.Ed25519Key
        ]
        
        for key_type in key_types:
            try:
                key_file.seek(0)
                return key_type.from_private_key(key_file, password=passphrase)
            except Exception:
                continue
        
        raise ValueError("Unable to load private key - unsupported format")
    
    def _validate_sync_paths(self, config: Dict[str, Any]) -> None:
        """Validate local and remote paths"""
        local_path = config['local_path']
        remote_path = config['remote_path']
        
        if config['direction'] == 'upload':
            # Check local path exists
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local path does not exist: {local_path}")
            
            # Create remote directory if needed
            try:
                self.sftp_client.stat(remote_path)
            except FileNotFoundError:
                if config['recursive']:
                    self._create_remote_directory(remote_path)
                else:
                    raise FileNotFoundError(f"Remote path does not exist: {remote_path}")
        
        elif config['direction'] == 'download':
            # Check remote path exists
            try:
                self.sftp_client.stat(remote_path)
            except FileNotFoundError:
                raise FileNotFoundError(f"Remote path does not exist: {remote_path}")
            
            # Create local directory if needed
            if not os.path.exists(local_path):
                if config['recursive']:
                    os.makedirs(local_path, exist_ok=True)
                else:
                    raise FileNotFoundError(f"Local path does not exist: {local_path}")
    
    def _create_remote_directory(self, path: str) -> None:
        """Create remote directory recursively"""
        try:
            self.sftp_client.stat(path)
            return  # Directory already exists
        except FileNotFoundError:
            pass
        
        # Create parent directories first
        parent = os.path.dirname(path)
        if parent and parent != path:
            self._create_remote_directory(parent)
        
        # Create the directory
        self.sftp_client.mkdir(path)
        logger.debug(f"Created remote directory: {path}")
    
    def _sync_upload(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Upload files from local to remote"""
        local_path = config['local_path']
        remote_path = config['remote_path']
        
        files_transferred = 0
        bytes_transferred = 0
        errors = []
        
        if os.path.isfile(local_path):
            # Single file upload
            try:
                if not config['dry_run']:
                    self.sftp_client.put(local_path, remote_path)
                    if config['preserve_permissions']:
                        local_stat = os.stat(local_path)
                        self.sftp_client.chmod(remote_path, local_stat.st_mode)
                
                file_size = os.path.getsize(local_path)
                files_transferred = 1
                bytes_transferred = file_size
                
                logger.debug(f"Uploaded file: {local_path} -> {remote_path}")
                
            except Exception as e:
                errors.append(f"Failed to upload {local_path}: {str(e)}")
        
        elif os.path.isdir(local_path):
            # Directory upload
            for root, dirs, files in os.walk(local_path):
                # Calculate relative path
                rel_path = os.path.relpath(root, local_path)
                if rel_path == '.':
                    remote_root = remote_path
                else:
                    remote_root = os.path.join(remote_path, rel_path).replace('\\', '/')
                
                # Create remote directory
                try:
                    if not config['dry_run']:
                        self._create_remote_directory(remote_root)
                except Exception as e:
                    errors.append(f"Failed to create remote directory {remote_root}: {str(e)}")
                    continue
                
                # Upload files
                for file in files:
                    if self._should_sync_file(file, config):
                        local_file = os.path.join(root, file)
                        remote_file = os.path.join(remote_root, file).replace('\\', '/')
                        
                        try:
                            if not config['dry_run']:
                                self.sftp_client.put(local_file, remote_file)
                                if config['preserve_permissions']:
                                    local_stat = os.stat(local_file)
                                    self.sftp_client.chmod(remote_file, local_stat.st_mode)
                            
                            file_size = os.path.getsize(local_file)
                            files_transferred += 1
                            bytes_transferred += file_size
                            
                            logger.debug(f"Uploaded file: {local_file} -> {remote_file}")
                            
                        except Exception as e:
                            errors.append(f"Failed to upload {local_file}: {str(e)}")
        
        # Determine status
        if errors:
            status = 'partial' if files_transferred > 0 else 'failed'
            stderr = '; '.join(errors)
        else:
            status = 'completed'
            stderr = ''
        
        return {
            'status': status,
            'exit_code': 0 if status == 'completed' else 1,
            'stdout': f"Uploaded {files_transferred} files ({bytes_transferred} bytes)",
            'stderr': stderr,
            'files_transferred': files_transferred,
            'bytes_transferred': bytes_transferred
        }
    
    def _sync_download(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Download files from remote to local"""
        local_path = config['local_path']
        remote_path = config['remote_path']
        
        files_transferred = 0
        bytes_transferred = 0
        errors = []
        
        try:
            remote_stat = self.sftp_client.stat(remote_path)
            
            if stat.S_ISREG(remote_stat.st_mode):
                # Single file download
                try:
                    if not config['dry_run']:
                        self.sftp_client.get(remote_path, local_path)
                        if config['preserve_permissions']:
                            os.chmod(local_path, remote_stat.st_mode)
                    
                    files_transferred = 1
                    bytes_transferred = remote_stat.st_size
                    
                    logger.debug(f"Downloaded file: {remote_path} -> {local_path}")
                    
                except Exception as e:
                    errors.append(f"Failed to download {remote_path}: {str(e)}")
            
            elif stat.S_ISDIR(remote_stat.st_mode):
                # Directory download
                files_transferred, bytes_transferred, errors = self._download_directory(
                    remote_path, local_path, config
                )
        
        except Exception as e:
            errors.append(f"Failed to access remote path {remote_path}: {str(e)}")
        
        # Determine status
        if errors:
            status = 'partial' if files_transferred > 0 else 'failed'
            stderr = '; '.join(errors)
        else:
            status = 'completed'
            stderr = ''
        
        return {
            'status': status,
            'exit_code': 0 if status == 'completed' else 1,
            'stdout': f"Downloaded {files_transferred} files ({bytes_transferred} bytes)",
            'stderr': stderr,
            'files_transferred': files_transferred,
            'bytes_transferred': bytes_transferred
        }
    
    def _download_directory(self, remote_path: str, local_path: str, config: Dict[str, Any]) -> Tuple[int, int, List[str]]:
        """Download directory recursively"""
        files_transferred = 0
        bytes_transferred = 0
        errors = []
        
        def download_recursive(remote_dir: str, local_dir: str):
            nonlocal files_transferred, bytes_transferred, errors
            
            try:
                # List remote directory
                for item in self.sftp_client.listdir_attr(remote_dir):
                    remote_item = os.path.join(remote_dir, item.filename).replace('\\', '/')
                    local_item = os.path.join(local_dir, item.filename)
                    
                    if stat.S_ISDIR(item.st_mode):
                        # Directory - recurse if enabled
                        if config['recursive']:
                            if not config['dry_run']:
                                os.makedirs(local_item, exist_ok=True)
                            download_recursive(remote_item, local_item)
                    
                    elif stat.S_ISREG(item.st_mode):
                        # File - download if it matches patterns
                        if self._should_sync_file(item.filename, config):
                            try:
                                if not config['dry_run']:
                                    # Ensure local directory exists
                                    os.makedirs(local_dir, exist_ok=True)
                                    self.sftp_client.get(remote_item, local_item)
                                    if config['preserve_permissions']:
                                        os.chmod(local_item, item.st_mode)
                                
                                files_transferred += 1
                                bytes_transferred += item.st_size
                                
                                logger.debug(f"Downloaded file: {remote_item} -> {local_item}")
                                
                            except Exception as e:
                                errors.append(f"Failed to download {remote_item}: {str(e)}")
            
            except Exception as e:
                errors.append(f"Failed to list remote directory {remote_dir}: {str(e)}")
        
        download_recursive(remote_path, local_path)
        return files_transferred, bytes_transferred, errors
    
    def _should_sync_file(self, filename: str, config: Dict[str, Any]) -> bool:
        """Check if file should be synchronized based on include/exclude patterns"""
        import fnmatch
        
        # Check exclude patterns first
        for pattern in config.get('exclude_patterns', []):
            if fnmatch.fnmatch(filename, pattern):
                return False
        
        # Check include patterns
        include_patterns = config.get('include_patterns', [])
        if include_patterns:
            for pattern in include_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    return True
            return False  # No include pattern matched
        
        return True  # No patterns or not excluded
    
    def _cleanup_connections(self) -> None:
        """Clean up SSH and SFTP connections"""
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None
        except Exception as e:
            logger.warning(f"Error closing SFTP client: {e}")
        
        try:
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
        except Exception as e:
            logger.warning(f"Error closing SSH client: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup_connections()
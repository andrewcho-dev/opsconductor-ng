#!/usr/bin/env python3
"""
Linux SSH Library for OpsConductor Automation Service
Handles SSH connections and bash script execution on Linux targets
"""

try:
    import paramiko
except ImportError:
    paramiko = None

import time
import socket
import structlog
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os
import io

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

# Configure structured logging
logger = structlog.get_logger(__name__)

class LinuxConnectionError(Exception):
    """Raised when Linux SSH connection fails"""
    pass

class LinuxExecutionError(Exception):
    """Raised when bash execution fails"""
    pass

class LinuxSSHLibrary:
    """
    Linux SSH execution library using Paramiko
    Provides secure connection management and bash script execution
    """
    
    def __init__(self):
        self.connection_timeout = 30  # seconds
        self.execution_timeout = 300  # seconds (5 minutes default)
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Check dependencies
        self.dependencies_available = self._check_dependencies()
        
        logger.info("Linux SSH Library initialized", 
                   connection_timeout=self.connection_timeout,
                   execution_timeout=self.execution_timeout,
                   dependencies_available=self.dependencies_available)

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are available"""
        return {
            "paramiko": paramiko is not None,
            "cryptography": Fernet is not None
        }

    def test_connection(self, target_host: str, username: str, password: str = None,
                       private_key: str = None, port: int = 22) -> Dict[str, Any]:
        """Test SSH connection to Linux target"""
        # Check dependencies first
        if not self.dependencies_available["paramiko"]:
            return {
                "success": False,
                "error": "Paramiko library not available. Install with: pip install paramiko",
                "duration_seconds": 0,
                "details": {"dependency_error": True}
            }
        
        start_time = time.time()
        
        try:
            logger.info("Testing SSH connection", 
                       target_host=target_host, 
                       port=port, 
                       username=username,
                       auth_method="password" if password else "key")
            
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with timeout
            if private_key:
                # Use private key authentication
                key_file = io.StringIO(private_key)
                pkey = paramiko.RSAKey.from_private_key(key_file)
                ssh_client.connect(
                    hostname=target_host,
                    port=port,
                    username=username,
                    pkey=pkey,
                    timeout=self.connection_timeout
                )
            else:
                # Use password authentication
                ssh_client.connect(
                    hostname=target_host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=self.connection_timeout
                )
            
            # Test with a simple command
            stdin, stdout, stderr = ssh_client.exec_command('echo "SSH connection test"')
            exit_code = stdout.channel.recv_exit_status()
            test_output = stdout.read().decode('utf-8').strip()
            
            ssh_client.close()
            
            duration = time.time() - start_time
            
            if exit_code == 0:
                logger.info("SSH connection test successful", 
                           target_host=target_host,
                           duration_seconds=duration)
                return {
                    "success": True,
                    "message": f"Successfully connected to {target_host}:{port} via SSH",
                    "duration_seconds": duration,
                    "details": {
                        "port": port,
                        "test_output": test_output,
                        "auth_method": "password" if password else "key"
                    }
                }
            else:
                error_output = stderr.read().decode('utf-8').strip()
                logger.warning("SSH connection test failed", 
                              target_host=target_host,
                              exit_code=exit_code,
                              error=error_output)
                return {
                    "success": False,
                    "error": f"SSH test command failed: {error_output}",
                    "duration_seconds": duration,
                    "details": {
                        "port": port,
                        "exit_code": exit_code
                    }
                }
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error("SSH connection test failed", 
                        target_host=target_host,
                        error=error_msg,
                        duration_seconds=duration)
            return {
                "success": False,
                "error": f"SSH connection failed: {error_msg}",
                "duration_seconds": duration,
                "details": {"exception": error_msg}
            }

    def execute_bash(self, target_host: str, username: str, script: str,
                    password: str = None, private_key: str = None, 
                    timeout: int = None, port: int = 22) -> Dict[str, Any]:
        """Execute bash script on Linux target via SSH"""
        # Check dependencies first
        if not self.dependencies_available["paramiko"]:
            return {
                "success": False,
                "error": "Paramiko library not available. Install with: pip install paramiko",
                "stdout": "",
                "stderr": "Dependency error",
                "exit_code": -1,
                "duration_seconds": 0,
                "attempts": 0
            }
        
        if timeout is None:
            timeout = self.execution_timeout
            
        start_time = time.time()
        attempts = 0
        last_error = None
        
        # Retry logic
        for attempt in range(self.max_retries):
            attempts += 1
            
            try:
                logger.info("Executing bash script", 
                           target_host=target_host, 
                           port=port, 
                           username=username,
                           attempt=attempt + 1,
                           script_length=len(script),
                           auth_method="password" if password else "key")
                
                # Create SSH client
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect
                if private_key:
                    # Use private key authentication
                    key_file = io.StringIO(private_key)
                    pkey = paramiko.RSAKey.from_private_key(key_file)
                    ssh_client.connect(
                        hostname=target_host,
                        port=port,
                        username=username,
                        pkey=pkey,
                        timeout=self.connection_timeout
                    )
                else:
                    # Use password authentication
                    ssh_client.connect(
                        hostname=target_host,
                        port=port,
                        username=username,
                        password=password,
                        timeout=self.connection_timeout
                    )
                
                # Execute bash script
                stdin, stdout, stderr = ssh_client.exec_command(
                    f'bash -c "{script}"',
                    timeout=timeout
                )
                
                # Wait for completion and get results
                exit_code = stdout.channel.recv_exit_status()
                stdout_data = stdout.read().decode('utf-8')
                stderr_data = stderr.read().decode('utf-8')
                
                ssh_client.close()
                
                duration = time.time() - start_time
                
                logger.info("Bash script execution completed", 
                           target_host=target_host,
                           exit_code=exit_code,
                           duration_seconds=duration,
                           attempts=attempts,
                           stdout_length=len(stdout_data),
                           stderr_length=len(stderr_data))
                
                return {
                    "success": exit_code == 0,
                    "error": stderr_data if exit_code != 0 else None,
                    "stdout": stdout_data,
                    "stderr": stderr_data,
                    "exit_code": exit_code,
                    "duration_seconds": duration,
                    "attempts": attempts,
                    "details": {
                        "port": port,
                        "timeout": timeout,
                        "script_length": len(script),
                        "auth_method": "password" if password else "key"
                    }
                }
                
            except Exception as e:
                last_error = str(e)
                logger.warning("Bash execution attempt failed", 
                              target_host=target_host,
                              attempt=attempt + 1,
                              error=last_error)
                
                # If not the last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    logger.info("Retrying bash execution", 
                               target_host=target_host,
                               retry_delay=self.retry_delay)
                    time.sleep(self.retry_delay)
        
        # All attempts failed
        duration = time.time() - start_time
        logger.error("Bash execution failed after all attempts", 
                    target_host=target_host,
                    attempts=attempts,
                    final_error=last_error,
                    duration_seconds=duration)
        
        return {
            "success": False,
            "error": f"Bash execution failed after {attempts} attempts: {last_error}",
            "stdout": "",
            "stderr": last_error or "Unknown error",
            "exit_code": -1,
            "duration_seconds": duration,
            "attempts": attempts,
            "details": {"final_error": last_error}
        }

    def get_library_info(self) -> Dict[str, Any]:
        """Get library information and capabilities"""
        return {
            "name": "Linux SSH Library",
            "version": "1.0.0",
            "description": "SSH-based bash execution for Linux targets",
            "capabilities": [
                "SSH connection testing",
                "Bash script execution",
                "Password and key-based authentication",
                "Connection retry logic",
                "Comprehensive error handling"
            ],
            "supported_auth": ["password", "private_key"],
            "default_port": 22,
            "timeouts": {
                "connection": self.connection_timeout,
                "execution": self.execution_timeout
            },
            "retry_settings": {
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay
            },
            "dependencies": self.dependencies_available,
            "ready": all(self.dependencies_available.values())
        }


# Library registration function for the automation service
def get_library():
    """Factory function to create library instance"""
    return LinuxSSHLibrary()


# Function mappings for the automation service worker
FUNCTION_MAPPINGS = {
    "test_connection": "test_connection",
    "execute_bash": "execute_bash", 
    "execute_script": "execute_bash",  # Alias
    "get_info": "get_library_info"
}


# Example usage and testing
if __name__ == "__main__":
    # Demo/testing code
    library = LinuxSSHLibrary()
    
    print("Linux SSH Library Demo")
    print("=" * 50)
    
    # Show library info
    info = library.get_library_info()
    print(f"Library: {info['name']} v{info['version']}")
    print(f"Ready: {info['ready']}")
    print(f"Dependencies: {info['dependencies']}")
    print(f"Capabilities: {', '.join(info['capabilities'])}")
    
    print("\nLibrary ready for automation service integration!")

# Module-level functions for direct worker access
_library_instance = None

def _get_library_instance():
    """Get or create library instance"""
    global _library_instance
    if _library_instance is None:
        _library_instance = LinuxSSHLibrary()
    return _library_instance

def get_library_info():
    """Module-level function for get_library_info"""
    return _get_library_instance().get_library_info()

def test_connection(target_host, username, password=None, private_key=None, port=22):
    """Module-level function for test_connection"""
    return _get_library_instance().test_connection(target_host, username, password, private_key, port)

def execute_bash(target_host, username, script, password=None, private_key=None, timeout=None, port=22):
    """Module-level function for execute_bash"""
    return _get_library_instance().execute_bash(target_host, username, script, password, private_key, timeout, port)

# Alias for execute_script
execute_script = execute_bash
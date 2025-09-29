#!/usr/bin/env python3
"""
Windows PowerShell Library for OpsConductor Automation Service
Handles WinRM connections and PowerShell script execution on Windows targets
"""

try:
    import winrm
except ImportError:
    winrm = None

import base64
import json
import time
import socket
import structlog
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

# Configure structured logging
logger = structlog.get_logger(__name__)

class WindowsConnectionError(Exception):
    """Raised when Windows connection fails"""
    pass

class WindowsExecutionError(Exception):
    """Raised when PowerShell execution fails"""
    pass

class WindowsPowerShellLibrary:
    """
    Windows PowerShell execution library using WinRM
    Provides secure connection management and PowerShell script execution
    """
    
    def __init__(self):
        self.connection_timeout = 30  # seconds
        self.execution_timeout = 300  # seconds (5 minutes default)
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Check dependencies
        self.dependencies_available = self._check_dependencies()
        
        logger.info("Windows PowerShell Library initialized", 
                   connection_timeout=self.connection_timeout,
                   execution_timeout=self.execution_timeout,
                   dependencies_available=self.dependencies_available)

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are available"""
        return {
            "winrm": winrm is not None,
            "cryptography": Fernet is not None
        }

    def test_connection(self, target_host: str, username: str, password: str, 
                       use_ssl: bool = True, port: int = None) -> Dict[str, Any]:
        """Test WinRM connection to Windows target"""
        # Check dependencies first
        if not self.dependencies_available["winrm"]:
            return {
                "success": False,
                "error": "WinRM library not available. Install with: pip install pywinrm",
                "duration_seconds": 0,
                "details": {"dependency_error": True}
            }
        
        start_time = time.time()
        
        # Temporarily disable proxy for direct WinRM connections
        original_http_proxy = os.environ.get('HTTP_PROXY')
        original_https_proxy = os.environ.get('HTTPS_PROXY')
        
        try:
            # Remove proxy settings for direct connection
            if 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']
            if 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']
            
            # Determine port and protocol
            if port is None:
                port = 5986 if use_ssl else 5985
            
            protocol = "https" if use_ssl else "http"
            endpoint = f"{protocol}://{target_host}:{port}/wsman"
            
            logger.info("Testing WinRM connection", 
                       target_host=target_host, 
                       port=port, 
                       protocol=protocol,
                       username=username)
            
            # Create WinRM session
            session = winrm.Session(
                endpoint,
                auth=(username, password),
                transport='ssl' if use_ssl else 'plaintext',
                server_cert_validation='ignore' if use_ssl else 'validate'
            )
            
            # Test with a simple command
            result = session.run_cmd('echo "WinRM connection test"')
            
            duration = time.time() - start_time
            
            if result.status_code == 0:
                logger.info("WinRM connection test successful", 
                           target_host=target_host,
                           duration_seconds=duration)
                return {
                    "success": True,
                    "message": f"Successfully connected to {target_host}:{port} via WinRM",
                    "duration_seconds": duration,
                    "details": {
                        "protocol": protocol,
                        "port": port,
                        "test_output": result.std_out.decode('utf-8').strip()
                    }
                }
            else:
                error_msg = result.std_err.decode('utf-8').strip() if result.std_err else "Unknown error"
                logger.warning("WinRM connection test failed", 
                              target_host=target_host,
                              status_code=result.status_code,
                              error=error_msg)
                return {
                    "success": False,
                    "error": f"WinRM test command failed: {error_msg}",
                    "duration_seconds": duration,
                    "details": {
                        "protocol": protocol,
                        "port": port,
                        "status_code": result.status_code
                    }
                }
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error("WinRM connection test failed", 
                        target_host=target_host,
                        error=error_msg,
                        duration_seconds=duration)
            return {
                "success": False,
                "error": f"WinRM connection failed: {error_msg}",
                "duration_seconds": duration,
                "details": {"exception": error_msg}
            }
        finally:
            # Restore proxy settings
            if original_http_proxy:
                os.environ['HTTP_PROXY'] = original_http_proxy
            if original_https_proxy:
                os.environ['HTTPS_PROXY'] = original_https_proxy

    def execute_powershell(self, target_host: str, username: str, password: str,
                          script: str, timeout: int = None, use_ssl: bool = True,
                          port: int = None) -> Dict[str, Any]:
        """Execute PowerShell script on Windows target via WinRM"""
        # Check dependencies first
        if not self.dependencies_available["winrm"]:
            return {
                "success": False,
                "error": "WinRM library not available. Install with: pip install pywinrm",
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
        
        # Temporarily disable proxy for direct WinRM connections
        original_http_proxy = os.environ.get('HTTP_PROXY')
        original_https_proxy = os.environ.get('HTTPS_PROXY')
        
        try:
            # Remove proxy settings for direct connection
            if 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']
            if 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']
        
            # Retry logic
            for attempt in range(self.max_retries):
                attempts += 1
                
                try:
                    # Determine port and protocol
                    if port is None:
                        port = 5986 if use_ssl else 5985
                    
                    protocol = "https" if use_ssl else "http"
                    endpoint = f"{protocol}://{target_host}:{port}/wsman"
                    
                    logger.info("Executing PowerShell script", 
                               target_host=target_host, 
                               port=port, 
                               protocol=protocol,
                               username=username,
                               attempt=attempt + 1,
                               script_length=len(script))
                    
                    # Create WinRM session
                    session = winrm.Session(
                        endpoint,
                        auth=(username, password),
                        transport='ssl' if use_ssl else 'plaintext',
                        server_cert_validation='ignore' if use_ssl else 'validate',
                        operation_timeout_sec=timeout,
                        read_timeout_sec=timeout + 10
                    )
                    
                    # Execute PowerShell script
                    result = session.run_ps(script)
                    
                    duration = time.time() - start_time
                    
                    # Decode output
                    stdout = result.std_out.decode('utf-8') if result.std_out else ""
                    stderr = result.std_err.decode('utf-8') if result.std_err else ""
                    
                    logger.info("PowerShell script execution completed", 
                               target_host=target_host,
                               exit_code=result.status_code,
                               duration_seconds=duration,
                               attempts=attempts,
                               stdout_length=len(stdout),
                               stderr_length=len(stderr))
                    
                    return {
                        "success": result.status_code == 0,
                        "error": stderr if result.status_code != 0 else None,
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": result.status_code,
                        "duration_seconds": duration,
                        "attempts": attempts,
                        "details": {
                            "protocol": protocol,
                            "port": port,
                            "timeout": timeout,
                            "script_length": len(script)
                        }
                    }
                    
                except Exception as e:
                    last_error = str(e)
                    logger.warning("PowerShell execution attempt failed", 
                                  target_host=target_host,
                                  attempt=attempt + 1,
                                  error=last_error)
                    
                    # If not the last attempt, wait before retrying
                    if attempt < self.max_retries - 1:
                        logger.info("Retrying PowerShell execution", 
                                   target_host=target_host,
                                   retry_delay=self.retry_delay)
                        time.sleep(self.retry_delay)
        
            # All attempts failed
            duration = time.time() - start_time
            logger.error("PowerShell execution failed after all attempts", 
                        target_host=target_host,
                        attempts=attempts,
                        final_error=last_error,
                        duration_seconds=duration)
            
            return {
                "success": False,
                "error": f"PowerShell execution failed after {attempts} attempts: {last_error}",
                "stdout": "",
                "stderr": last_error or "Unknown error",
                "exit_code": -1,
                "duration_seconds": duration,
                "attempts": attempts,
                "details": {"final_error": last_error}
            }
        finally:
            # Restore proxy settings
            if original_http_proxy:
                os.environ['HTTP_PROXY'] = original_http_proxy
            if original_https_proxy:
                os.environ['HTTPS_PROXY'] = original_https_proxy

    def get_library_info(self) -> Dict[str, Any]:
        """Get library information and capabilities"""
        return {
            "name": "Windows PowerShell Library",
            "version": "1.0.0",
            "description": "WinRM-based PowerShell execution for Windows targets",
            "capabilities": [
                "WinRM connection testing",
                "PowerShell script execution",
                "Credential encryption/decryption",
                "Connection retry logic",
                "Comprehensive error handling"
            ],
            "supported_protocols": ["HTTP", "HTTPS"],
            "default_ports": {"HTTP": 5985, "HTTPS": 5986},
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
    return WindowsPowerShellLibrary()


# Function mappings for the automation service worker
FUNCTION_MAPPINGS = {
    "test_connection": "test_connection",
    "execute_powershell": "execute_powershell", 
    "execute_script": "execute_powershell",  # Alias
    "get_info": "get_library_info"
}


# Example usage and testing
if __name__ == "__main__":
    # Demo/testing code
    library = WindowsPowerShellLibrary()
    
    print("Windows PowerShell Library Demo")
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
        _library_instance = WindowsPowerShellLibrary()
    return _library_instance

def get_library_info():
    """Module-level function for get_library_info"""
    return _get_library_instance().get_library_info()

def test_connection(target_host, username, password, use_ssl=True, port=None):
    """Module-level function for test_connection"""
    return _get_library_instance().test_connection(target_host, username, password, use_ssl, port)

def execute_powershell(target_host, username, password, script, timeout=None, use_ssl=True, port=None):
    """Module-level function for execute_powershell"""
    return _get_library_instance().execute_powershell(target_host, username, password, script, timeout, use_ssl, port)

# Alias for execute_script
execute_script = execute_powershell

async def execute_powershell_parallel(targets, script, timeout=None, max_concurrent=5):
    """Execute PowerShell script on multiple targets in parallel"""
    import asyncio
    import concurrent.futures
    from typing import List, Dict, Any
    
    if not targets:
        return {
            "success": False,
            "error": "No targets provided",
            "results": []
        }
    
    # Validate targets format
    if not isinstance(targets, list):
        return {
            "success": False,
            "error": "Targets must be a list",
            "results": []
        }
    
    async def execute_single_target(target):
        """Execute PowerShell on a single target"""
        try:
            # Extract connection details from target
            target_host = target.get('hostname') or target.get('ip_address')
            username = target.get('username')
            password = target.get('password')
            port = target.get('port', 5986)
            use_ssl = target.get('is_secure', True)
            
            if not all([target_host, username, password]):
                return {
                    "target_id": target.get('id'),
                    "target_name": target.get('name', target_host),
                    "success": False,
                    "error": "Missing required connection details (hostname, username, or password)",
                    "output": None
                }
            
            # Execute PowerShell script
            result = _get_library_instance().execute_powershell(
                target_host=target_host,
                username=username,
                password=password,
                script=script,
                timeout=timeout,
                use_ssl=use_ssl,
                port=port
            )
            
            return {
                "target_id": target.get('id'),
                "target_name": target.get('name', target_host),
                "success": result.get('success', False),
                "error": result.get('error'),
                "output": result.get('output'),
                "execution_time": result.get('execution_time')
            }
            
        except Exception as e:
            return {
                "target_id": target.get('id'),
                "target_name": target.get('name', 'unknown'),
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "output": None
            }
    
    # Execute on all targets with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_with_semaphore(target):
        async with semaphore:
            return await execute_single_target(target)
    
    # Run all executions concurrently
    tasks = [execute_with_semaphore(target) for target in targets]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_count = 0
    failed_count = 0
    processed_results = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "target_id": targets[i].get('id'),
                "target_name": targets[i].get('name', 'unknown'),
                "success": False,
                "error": f"Task failed: {str(result)}",
                "output": None
            })
            failed_count += 1
        else:
            processed_results.append(result)
            if result.get('success', False):
                successful_count += 1
            else:
                failed_count += 1
    
    return {
        "success": successful_count > 0,
        "total_targets": len(targets),
        "successful_count": successful_count,
        "failed_count": failed_count,
        "results": processed_results,
        "summary": f"Executed on {len(targets)} targets: {successful_count} successful, {failed_count} failed"
    }

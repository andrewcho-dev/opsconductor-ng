#!/usr/bin/env python3
"""
Windows PSExec Library for OpsConductor Automation Service
Handles PSExec-based remote execution on Windows targets for GUI and interactive applications
"""

import subprocess
import time
import structlog
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import os
import shlex

# Configure structured logging
logger = structlog.get_logger(__name__)

class PSExecConnectionError(Exception):
    """Raised when PSExec connection fails"""
    pass

class PSExecExecutionError(Exception):
    """Raised when PSExec execution fails"""
    pass

class WindowsPSExecLibrary:
    """
    Windows PSExec execution library
    Provides remote execution with interactive desktop support for GUI applications
    
    PSExec must be installed on the system running this service.
    Download from: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec
    """
    
    def __init__(self):
        self.connection_timeout = 30  # seconds
        self.execution_timeout = 300  # seconds (5 minutes default)
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Check if PSExec is available
        self.psexec_available = self._check_psexec_available()
        
        logger.info("Windows PSExec Library initialized", 
                   connection_timeout=self.connection_timeout,
                   execution_timeout=self.execution_timeout,
                   psexec_available=self.psexec_available)

    def _check_psexec_available(self) -> bool:
        """Check if PSExec is available in the system"""
        try:
            # Try to run psexec with -? to check if it exists
            result = subprocess.run(
                ['psexec', '-?'],
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning("PSExec not found in system PATH", error=str(e))
            return False

    def test_connection(self, target_host: str, username: str, password: str) -> Dict[str, Any]:
        """Test PSExec connection to Windows target"""
        if not self.psexec_available:
            return {
                "success": False,
                "error": "PSExec not available. Download from https://docs.microsoft.com/en-us/sysinternals/downloads/psexec",
                "duration_seconds": 0,
                "details": {"dependency_error": True}
            }
        
        start_time = time.time()
        
        try:
            # Build PSExec command for connection test
            # Format: psexec \\target -u username -p password cmd /c echo "test"
            cmd = [
                'psexec',
                f'\\\\{target_host}',
                '-u', username,
                '-p', password,
                '-accepteula',  # Auto-accept EULA
                'cmd', '/c', 'echo PSExec connection test'
            ]
            
            logger.info("Testing PSExec connection", 
                       target_host=target_host, 
                       username=username)
            
            # Execute test command
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.connection_timeout,
                text=True
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info("PSExec connection test successful", 
                           target_host=target_host,
                           duration_seconds=duration)
                return {
                    "success": True,
                    "message": f"Successfully connected to {target_host} via PSExec",
                    "duration_seconds": duration,
                    "details": {
                        "test_output": result.stdout.strip()
                    }
                }
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.warning("PSExec connection test failed", 
                              target_host=target_host,
                              return_code=result.returncode,
                              error=error_msg)
                return {
                    "success": False,
                    "error": f"PSExec test command failed: {error_msg}",
                    "duration_seconds": duration,
                    "details": {
                        "return_code": result.returncode,
                        "stderr": error_msg
                    }
                }
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error("PSExec connection test timed out", 
                        target_host=target_host,
                        timeout=self.connection_timeout,
                        duration_seconds=duration)
            return {
                "success": False,
                "error": f"PSExec connection test timed out after {self.connection_timeout} seconds",
                "duration_seconds": duration,
                "details": {"timeout": True}
            }
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error("PSExec connection test failed", 
                        target_host=target_host,
                        error=error_msg,
                        duration_seconds=duration)
            return {
                "success": False,
                "error": f"PSExec connection failed: {error_msg}",
                "duration_seconds": duration,
                "details": {"exception": error_msg}
            }

    def execute_command(self, target_host: str, username: str, password: str,
                       command: str, interactive: bool = False, session_id: int = None,
                       timeout: int = None, wait: bool = True) -> Dict[str, Any]:
        """
        Execute command on Windows target via PSExec
        
        Args:
            target_host: Target Windows host (IP or hostname)
            username: Username for authentication
            password: Password for authentication
            command: Command to execute
            interactive: If True, run with desktop interaction (-i flag)
            session_id: Session ID for interactive mode (default: 1)
            timeout: Execution timeout in seconds
            wait: If False, don't wait for process to complete (for GUI apps)
            
        Returns:
            Dict with execution results
        """
        if not self.psexec_available:
            return {
                "success": False,
                "error": "PSExec not available. Download from https://docs.microsoft.com/en-us/sysinternals/downloads/psexec",
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
                # Build PSExec command
                cmd = [
                    'psexec',
                    f'\\\\{target_host}',
                    '-u', username,
                    '-p', password,
                    '-accepteula'  # Auto-accept EULA
                ]
                
                # Add interactive flag if requested
                if interactive:
                    if session_id is not None:
                        cmd.extend(['-i', str(session_id)])
                    else:
                        cmd.append('-i')
                
                # Add -d flag if we don't want to wait (for GUI apps)
                if not wait:
                    cmd.append('-d')
                
                # Add the command to execute
                # If command contains spaces or special chars, we need to handle it properly
                if ' ' in command or any(c in command for c in ['&', '|', '>', '<', '^']):
                    # Wrap in cmd /c for complex commands
                    cmd.extend(['cmd', '/c', command])
                else:
                    cmd.append(command)
                
                logger.info("Executing PSExec command", 
                           target_host=target_host, 
                           username=username,
                           attempt=attempt + 1,
                           interactive=interactive,
                           session_id=session_id,
                           wait=wait,
                           command=command)
                
                # Execute command
                if wait:
                    # Wait for completion
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=timeout,
                        text=True
                    )
                    
                    duration = time.time() - start_time
                    
                    stdout = result.stdout if result.stdout else ""
                    stderr = result.stderr if result.stderr else ""
                    
                    logger.info("PSExec command execution completed", 
                               target_host=target_host,
                               exit_code=result.returncode,
                               duration_seconds=duration,
                               attempts=attempts,
                               stdout_length=len(stdout),
                               stderr_length=len(stderr))
                    
                    return {
                        "success": result.returncode == 0,
                        "error": stderr if result.returncode != 0 else None,
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": result.returncode,
                        "duration_seconds": duration,
                        "attempts": attempts,
                        "details": {
                            "interactive": interactive,
                            "session_id": session_id,
                            "timeout": timeout,
                            "command": command
                        }
                    }
                else:
                    # Don't wait for completion (for GUI apps)
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Give it a moment to start
                    time.sleep(2)
                    
                    # Check if process is still running (which is good for GUI apps)
                    poll_result = process.poll()
                    
                    duration = time.time() - start_time
                    
                    if poll_result is None:
                        # Process is still running - this is expected for GUI apps
                        logger.info("PSExec command launched successfully (non-blocking)", 
                                   target_host=target_host,
                                   duration_seconds=duration,
                                   attempts=attempts)
                        
                        return {
                            "success": True,
                            "error": None,
                            "stdout": f"Process launched successfully on {target_host}",
                            "stderr": "",
                            "exit_code": 0,
                            "duration_seconds": duration,
                            "attempts": attempts,
                            "details": {
                                "interactive": interactive,
                                "session_id": session_id,
                                "non_blocking": True,
                                "command": command,
                                "message": "Process launched in background. GUI should appear on remote desktop."
                            }
                        }
                    else:
                        # Process exited quickly - might be an error
                        stdout, stderr = process.communicate()
                        
                        logger.warning("PSExec command exited quickly", 
                                      target_host=target_host,
                                      exit_code=poll_result,
                                      duration_seconds=duration)
                        
                        return {
                            "success": poll_result == 0,
                            "error": stderr if poll_result != 0 else None,
                            "stdout": stdout,
                            "stderr": stderr,
                            "exit_code": poll_result,
                            "duration_seconds": duration,
                            "attempts": attempts,
                            "details": {
                                "interactive": interactive,
                                "session_id": session_id,
                                "non_blocking": True,
                                "command": command,
                                "warning": "Process exited quickly - may not be a GUI application"
                            }
                        }
                
            except subprocess.TimeoutExpired:
                last_error = f"Command timed out after {timeout} seconds"
                logger.warning("PSExec execution attempt timed out", 
                              target_host=target_host,
                              attempt=attempt + 1,
                              timeout=timeout)
                
                # If not the last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    logger.info("Retrying PSExec execution", 
                               target_host=target_host,
                               retry_delay=self.retry_delay)
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                last_error = str(e)
                logger.warning("PSExec execution attempt failed", 
                              target_host=target_host,
                              attempt=attempt + 1,
                              error=last_error)
                
                # If not the last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    logger.info("Retrying PSExec execution", 
                               target_host=target_host,
                               retry_delay=self.retry_delay)
                    time.sleep(self.retry_delay)
        
        # All attempts failed
        duration = time.time() - start_time
        logger.error("PSExec execution failed after all attempts", 
                    target_host=target_host,
                    attempts=attempts,
                    final_error=last_error,
                    duration_seconds=duration)
        
        return {
            "success": False,
            "error": f"PSExec execution failed after {attempts} attempts: {last_error}",
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
            "name": "Windows PSExec Library",
            "version": "1.0.0",
            "description": "PSExec-based remote execution for Windows targets with GUI support",
            "capabilities": [
                "Remote command execution",
                "Interactive desktop support (-i flag)",
                "Session-specific execution",
                "Non-blocking execution for GUI applications",
                "Connection retry logic",
                "Comprehensive error handling"
            ],
            "supported_features": [
                "GUI application launching",
                "Interactive session targeting",
                "Background process execution",
                "Administrative privileges"
            ],
            "timeouts": {
                "connection": self.connection_timeout,
                "execution": self.execution_timeout
            },
            "retry_settings": {
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay
            },
            "dependencies": {
                "psexec": self.psexec_available
            },
            "ready": self.psexec_available,
            "installation_note": "PSExec must be downloaded from https://docs.microsoft.com/en-us/sysinternals/downloads/psexec"
        }


# Library registration function for the automation service
def get_library():
    """Factory function to create library instance"""
    return WindowsPSExecLibrary()


# Function mappings for the automation service worker
FUNCTION_MAPPINGS = {
    "test_connection": "test_connection",
    "execute_command": "execute_command",
    "execute": "execute_command",  # Alias
    "get_info": "get_library_info"
}
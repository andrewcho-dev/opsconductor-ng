#!/usr/bin/env python3
"""
Windows Remote Execution Library for OpsConductor Automation Service
Handles remote execution on Windows targets for GUI and interactive applications using Impacket

This library uses Impacket's WMI/SMB capabilities to execute commands on remote Windows systems.
Unlike PowerShell remoting (WinRM), this can launch GUI applications that appear on the remote desktop.
"""

import time
import structlog
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import threading

# Impacket imports
try:
    from impacket.smbconnection import SMBConnection
    from impacket.dcerpc.v5.dcomrt import DCOMConnection
    from impacket.dcerpc.v5.dcom import wmi
    from impacket.dcerpc.v5.dtypes import NULL
    IMPACKET_AVAILABLE = True
except ImportError:
    IMPACKET_AVAILABLE = False

# Configure structured logging
logger = structlog.get_logger(__name__)

class ImpacketConnectionError(Exception):
    """Raised when remote execution connection fails"""
    pass

class ImpacketExecutionError(Exception):
    """Raised when remote execution fails"""
    pass

class WindowsImpacketExecutor:
    """
    Windows Remote Execution library using Impacket
    Provides remote execution with support for GUI applications and non-blocking execution
    
    This library uses Impacket's WMI capabilities to execute commands remotely.
    It works from Linux to Windows and can launch GUI applications.
    
    Requirements:
    - pip install impacket
    - Administrative credentials on target Windows system
    - SMB access (port 445) to target
    - DCOM/WMI access (ports 135, dynamic RPC ports)
    """
    
    def __init__(self):
        self.connection_timeout = 30  # seconds
        self.execution_timeout = 300  # seconds (5 minutes default)
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Check if Impacket is available
        self.impacket_available = IMPACKET_AVAILABLE
        
        logger.info("Windows Remote Execution Library initialized", 
                   connection_timeout=self.connection_timeout,
                   execution_timeout=self.execution_timeout,
                   impacket_available=self.impacket_available)

    def test_connection(self, target_host: str, username: str, password: str, 
                       domain: str = "") -> Dict[str, Any]:
        """
        Test WMI connection to Windows target
        
        Args:
            target_host: Target Windows host (IP or hostname)
            username: Username for authentication
            password: Password for authentication
            domain: Windows domain (optional, use "" for local accounts)
            
        Returns:
            Dict with connection test results
        """
        if not self.impacket_available:
            return {
                "success": False,
                "error": "Impacket library not available. Install with: pip install impacket",
                "duration_seconds": 0,
                "details": {"dependency_error": True}
            }
        
        start_time = time.time()
        
        try:
            logger.info("Testing WMI connection via Impacket", 
                       target_host=target_host, 
                       username=username,
                       domain=domain)
            
            # Establish DCOM connection
            dcom = DCOMConnection(
                target_host,
                username,
                password,
                domain,
                lmhash="",
                nthash="",
                aesKey=None,
                oxidResolver=True,
                doKerberos=False
            )
            
            # Create WMI interface
            iInterface = dcom.CoCreateInstanceEx(wmi.CLSID_WbemLevel1Login, wmi.IID_IWbemLevel1Login)
            iWbemLevel1Login = wmi.IWbemLevel1Login(iInterface)
            iWbemServices = iWbemLevel1Login.NTLMLogin('//./root/cimv2', NULL, NULL)
            iWbemLevel1Login.RemRelease()
            
            # Test by querying Win32_Process class
            win32Process, _ = iWbemServices.GetObject('Win32_Process')
            
            # Clean up
            dcom.disconnect()
            
            duration = time.time() - start_time
            
            logger.info("WMI connection test successful", 
                       target_host=target_host,
                       duration_seconds=duration)
            
            return {
                "success": True,
                "message": f"Successfully connected to {target_host} via WMI",
                "duration_seconds": duration,
                "details": {
                    "method": "Impacket WMI",
                    "test_output": "WMI connection established"
                }
            }
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error("WMI connection test failed", 
                        target_host=target_host,
                        error=error_msg,
                        duration_seconds=duration)
            return {
                "success": False,
                "error": f"WMI connection failed: {error_msg}",
                "duration_seconds": duration,
                "details": {"exception": error_msg}
            }

    def execute_command(self, target_host: str, username: str, password: str,
                       command: str, domain: str = "", interactive: bool = False, 
                       session_id: int = None, timeout: int = None, 
                       wait: bool = True) -> Dict[str, Any]:
        """
        Execute command on Windows target via WMI
        
        Args:
            target_host: Target Windows host (IP or hostname)
            username: Username for authentication
            password: Password for authentication
            command: Command to execute
            domain: Windows domain (optional, use "" for local accounts)
            interactive: If True, attempt to run with desktop interaction (best effort)
            session_id: Session ID for interactive mode (currently not used with WMI)
            timeout: Execution timeout in seconds
            wait: If False, don't wait for process to complete (for GUI apps)
            
        Returns:
            Dict with execution results
        """
        if not self.impacket_available:
            return {
                "success": False,
                "error": "Impacket library not available. Install with: pip install impacket",
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
                logger.info("Executing WMI command via Impacket", 
                           target_host=target_host, 
                           username=username,
                           domain=domain,
                           attempt=attempt + 1,
                           interactive=interactive,
                           session_id=session_id,
                           wait=wait,
                           command=command)
                
                # Establish DCOM connection
                dcom = DCOMConnection(
                    target_host,
                    username,
                    password,
                    domain,
                    lmhash="",
                    nthash="",
                    aesKey=None,
                    oxidResolver=True,
                    doKerberos=False
                )
                
                try:
                    # Create WMI interface
                    iInterface = dcom.CoCreateInstanceEx(wmi.CLSID_WbemLevel1Login, wmi.IID_IWbemLevel1Login)
                    iWbemLevel1Login = wmi.IWbemLevel1Login(iInterface)
                    iWbemServices = iWbemLevel1Login.NTLMLogin('//./root/cimv2', NULL, NULL)
                    iWbemLevel1Login.RemRelease()
                    
                    # Get Win32_Process class
                    win32Process, _ = iWbemServices.GetObject('Win32_Process')
                    
                    if wait:
                        # Execute and wait for completion
                        # For blocking execution, we wrap the command to capture output
                        output_file = f"C:\\Windows\\Temp\\wmi_output_{int(time.time())}.txt"
                        wrapped_command = f'cmd.exe /Q /c {command} > {output_file} 2>&1'
                        
                        # Execute the command
                        result = win32Process.Create(wrapped_command, "C:\\", None)
                        process_id = result.ProcessId
                        
                        logger.info("WMI process created (blocking mode)", 
                                   target_host=target_host,
                                   process_id=process_id)
                        
                        # Wait for process to complete (poll for completion)
                        wait_start = time.time()
                        process_completed = False
                        
                        while (time.time() - wait_start) < timeout:
                            # Query for the process
                            try:
                                query = f"SELECT * FROM Win32_Process WHERE ProcessId = {process_id}"
                                iEnumWbemClassObject = iWbemServices.ExecQuery(query)
                                
                                # Try to get the process
                                try:
                                    iEnumWbemClassObject.Next(0xffffffff, 1)
                                    # Process still exists, wait a bit
                                    time.sleep(1)
                                except Exception:
                                    # Process no longer exists - it completed
                                    process_completed = True
                                    break
                            except Exception as e:
                                logger.warning("Error checking process status", error=str(e))
                                time.sleep(1)
                        
                        # Try to retrieve output
                        stdout = ""
                        stderr = ""
                        exit_code = 0
                        
                        if process_completed:
                            # Try to read the output file via SMB
                            try:
                                smb_conn = SMBConnection(target_host, target_host)
                                smb_conn.login(username, password, domain)
                                
                                # Read the output file using callback
                                file_data = b""
                                def file_callback(data):
                                    nonlocal file_data
                                    file_data += data
                                
                                smb_conn.getFile("C$", output_file.replace("C:\\", ""), file_callback)
                                stdout = file_data.decode('utf-8', errors='ignore')
                                
                                # Delete the output file
                                smb_conn.deleteFile("C$", output_file.replace("C:\\", ""))
                                smb_conn.logoff()
                            except Exception as e:
                                logger.warning("Could not retrieve command output", error=str(e))
                                stdout = f"Command executed but output could not be retrieved: {str(e)}"
                        else:
                            stderr = f"Command timed out after {timeout} seconds"
                            exit_code = -1
                        
                        duration = time.time() - start_time
                        
                        logger.info("WMI command execution completed", 
                                   target_host=target_host,
                                   exit_code=exit_code,
                                   duration_seconds=duration,
                                   attempts=attempts,
                                   stdout_length=len(stdout),
                                   stderr_length=len(stderr))
                        
                        dcom.disconnect()
                        
                        return {
                            "success": exit_code == 0 and process_completed,
                            "error": stderr if exit_code != 0 else None,
                            "stdout": stdout,
                            "stderr": stderr,
                            "exit_code": exit_code,
                            "duration_seconds": duration,
                            "attempts": attempts,
                            "details": {
                                "interactive": interactive,
                                "session_id": session_id,
                                "timeout": timeout,
                                "command": command,
                                "method": "Impacket WMI (blocking)"
                            }
                        }
                    else:
                        # Don't wait for completion (for GUI apps)
                        # Just launch the process and return immediately
                        result = win32Process.Create(command, "C:\\", None)
                        process_id = result.ProcessId
                        return_value = result.ReturnValue
                        
                        duration = time.time() - start_time
                        
                        if return_value == 0:
                            logger.info("WMI process launched successfully (non-blocking)", 
                                       target_host=target_host,
                                       process_id=process_id,
                                       duration_seconds=duration,
                                       attempts=attempts)
                            
                            dcom.disconnect()
                            
                            return {
                                "success": True,
                                "error": None,
                                "stdout": f"Process launched successfully on {target_host} (PID: {process_id})",
                                "stderr": "",
                                "exit_code": 0,
                                "duration_seconds": duration,
                                "attempts": attempts,
                                "details": {
                                    "interactive": interactive,
                                    "session_id": session_id,
                                    "non_blocking": True,
                                    "command": command,
                                    "process_id": process_id,
                                    "method": "Impacket WMI (non-blocking)",
                                    "message": "Process launched in background. GUI should appear on remote desktop if user is logged in."
                                }
                            }
                        else:
                            error_msg = f"WMI Create returned error code: {return_value}"
                            logger.warning("WMI process creation failed", 
                                          target_host=target_host,
                                          return_value=return_value,
                                          duration_seconds=duration)
                            
                            dcom.disconnect()
                            
                            return {
                                "success": False,
                                "error": error_msg,
                                "stdout": "",
                                "stderr": error_msg,
                                "exit_code": return_value,
                                "duration_seconds": duration,
                                "attempts": attempts,
                                "details": {
                                    "interactive": interactive,
                                    "session_id": session_id,
                                    "non_blocking": True,
                                    "command": command,
                                    "return_value": return_value
                                }
                            }
                
                finally:
                    # Always disconnect DCOM
                    try:
                        dcom.disconnect()
                    except:
                        pass
                        
            except Exception as e:
                last_error = str(e)
                duration = time.time() - start_time
                
                logger.warning("WMI command execution attempt failed", 
                              target_host=target_host,
                              attempt=attempt + 1,
                              error=last_error,
                              duration_seconds=duration)
                
                # If this isn't the last attempt, wait before retrying
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...", 
                               attempt=attempt + 1,
                               max_retries=self.max_retries)
                    time.sleep(self.retry_delay)
                else:
                    # Last attempt failed
                    logger.error("All WMI command execution attempts failed", 
                                target_host=target_host,
                                attempts=attempts,
                                last_error=last_error,
                                duration_seconds=duration)
                    
                    return {
                        "success": False,
                        "error": f"All {attempts} attempts failed. Last error: {last_error}",
                        "stdout": "",
                        "stderr": last_error,
                        "exit_code": -1,
                        "duration_seconds": duration,
                        "attempts": attempts,
                        "details": {
                            "all_attempts_failed": True,
                            "last_error": last_error
                        }
                    }
        
        # Should never reach here, but just in case
        return {
            "success": False,
            "error": "Unexpected execution path",
            "stdout": "",
            "stderr": "Unexpected execution path",
            "exit_code": -1,
            "duration_seconds": time.time() - start_time,
            "attempts": attempts
        }

    def close(self):
        """Clean up resources"""
        logger.info("Windows Remote Execution Library closed")
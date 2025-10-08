"""
Phase 7: Execution Engine
Core execution logic with step-by-step execution and progress tracking
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
import base64

from execution.dtos import ExecutionResult, StepExecutionResult
from execution.models import (
    ExecutionModel,
    ExecutionStatus,
    ExecutionStepModel,
)
from execution.repository import ExecutionRepository
# from execution.services.asset_service_client import AssetServiceClient
# from execution.services.automation_service_client import AutomationServiceClient

# Import WinRM and SSH libraries
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'automation-service'))
try:
    from libraries.windows_powershell import WindowsPowerShellLibrary
    WINRM_AVAILABLE = True
except ImportError:
    WindowsPowerShellLibrary = None
    WINRM_AVAILABLE = False

try:
    from libraries.linux_ssh import LinuxSSHLibrary
    SSH_AVAILABLE = True
except ImportError:
    LinuxSSHLibrary = None
    SSH_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Execution Engine - Core execution logic
    
    Responsibilities:
    1. Step-by-step execution
    2. Progress tracking
    3. Error handling and retry logic
    4. Result aggregation
    """
    
    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        redis_url: Optional[str] = None,
        asset_service_url: Optional[str] = None,
        automation_service_url: Optional[str] = None
    ):
        """Initialize Execution Engine"""
        self.db_connection_string = db_connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"
        )
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Initialize repository
        self.repository = ExecutionRepository(self.db_connection_string)
        
        # Initialize service clients
        # self.asset_client = AssetServiceClient(base_url=asset_service_url)
        # self.automation_client = AutomationServiceClient(base_url=automation_service_url)
        
        # Initialize WinRM library if available
        self.winrm_library = None
        if WINRM_AVAILABLE:
            try:
                self.winrm_library = WindowsPowerShellLibrary()
                logger.info("WinRM library initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize WinRM library: {e}")
        else:
            logger.warning("WinRM library not available - Windows PowerShell execution will not work")
        
        # Initialize SSH library if available
        self.ssh_library = None
        if SSH_AVAILABLE:
            try:
                self.ssh_library = LinuxSSHLibrary()
                logger.info("SSH library initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize SSH library: {e}")
        else:
            logger.warning("SSH library not available - Linux SSH execution will not work")
        
        logger.info("ExecutionEngine initialized with service integrations")
    
    async def execute(self, execution: ExecutionModel) -> ExecutionResult:
        """
        Execute a plan step-by-step
        
        Args:
            execution: Execution model
        
        Returns:
            ExecutionResult with execution details
        """
        started_at = datetime.utcnow()
        step_results: List[Dict[str, Any]] = []
        
        try:
            logger.info("")
            logger.info("🎬 " + "=" * 77)
            logger.info(f"🎬 STARTING EXECUTION")
            logger.info(f"🎬 Execution ID: {execution.execution_id}")
            logger.info(f"🎬 Tenant ID: {execution.tenant_id}")
            logger.info(f"🎬 Execution Mode: {execution.execution_mode.value}")
            logger.info(f"🎬 SLA Class: {execution.sla_class.value}")
            logger.info("🎬 " + "=" * 77)
            
            # Step 1: Create execution steps from plan
            logger.info("")
            logger.info("📋 STEP 1: Creating execution steps from plan...")
            steps = await self._create_execution_steps(execution)
            
            logger.info(f"✅ Created {len(steps)} execution steps")
            for i, step in enumerate(steps):
                logger.info(f"   {i+1}. {step.step_name} (type: {step.step_type})")
            
            # Step 2: Execute steps sequentially
            for step in steps:
                try:
                    step_result = await self._execute_step(step, execution)
                    step_results.append({
                        "step_id": str(step.step_id),
                        "step_name": step.step_name,
                        "status": step_result.status.value,
                        "duration_ms": step_result.duration_ms,
                        "output_data": step_result.output_data,
                    })
                    
                    # Check if step failed
                    if step_result.status == ExecutionStatus.FAILED:
                        logger.warning(
                            f"Step failed: {step.step_id}, "
                            f"error={step_result.error_message}"
                        )
                        # Continue to next step (partial execution)
                
                except Exception as e:
                    logger.error(
                        f"Step execution error: {step.step_id}, error={e}",
                        exc_info=True
                    )
                    step_results.append({
                        "step_id": str(step.step_id),
                        "step_name": step.step_name,
                        "status": ExecutionStatus.FAILED.value,
                        "error_message": str(e),
                    })
            
            # Step 3: Determine final status
            logger.info("")
            logger.info("📊 DETERMINING FINAL STATUS...")
            final_status = self._determine_final_status(step_results)
            
            # Step 4: Build result
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()
            
            completed_count = sum(
                1 for r in step_results
                if r.get("status") == ExecutionStatus.COMPLETED.value
            )
            failed_count = sum(
                1 for r in step_results
                if r.get("status") == ExecutionStatus.FAILED.value
            )
            
            result = ExecutionResult(
                execution_id=execution.execution_id,
                status=final_status,
                result={
                    "total_steps": len(steps),
                    "completed_steps": completed_count,
                    "failed_steps": failed_count,
                },
                step_results=step_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
            )
            
            logger.info("")
            logger.info("🏁 " + "=" * 77)
            logger.info(f"🏁 EXECUTION COMPLETED")
            logger.info(f"🏁 Execution ID: {execution.execution_id}")
            logger.info(f"🏁 Final Status: {final_status.value}")
            logger.info(f"🏁 Total Steps: {len(steps)}")
            logger.info(f"🏁 Completed: {completed_count}")
            logger.info(f"🏁 Failed: {failed_count}")
            logger.info(f"🏁 Duration: {duration_seconds:.3f}s")
            logger.info("🏁 " + "=" * 77)
            
            return result
        
        except Exception as e:
            logger.error(
                f"Execution failed: {execution.execution_id}, error={e}",
                exc_info=True
            )
            
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()
            
            return ExecutionResult(
                execution_id=execution.execution_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                error_details={"exception": type(e).__name__},
                step_results=step_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
            )
    
    async def _create_execution_steps(
        self,
        execution: ExecutionModel
    ) -> List[ExecutionStepModel]:
        """
        Create execution steps from plan
        
        Args:
            execution: Execution model
        
        Returns:
            List of ExecutionStepModel
        """
        steps: List[ExecutionStepModel] = []
        plan_steps = execution.plan_snapshot.get("steps", [])
        
        for index, plan_step in enumerate(plan_steps):
            step = ExecutionStepModel(
                execution_id=execution.execution_id,
                step_index=index,
                step_name=plan_step.get("description", plan_step.get("name", f"Step {index + 1}")),
                step_type=plan_step.get("tool", plan_step.get("type", "unknown")),
                target_asset_id=plan_step.get("target_asset_id"),
                target_hostname=plan_step.get("target_hostname"),
                input_data=plan_step.get("inputs", plan_step.get("input_data", {})),
                trace_id=execution.trace_id,
            )
            
            # Save step to database
            step = self.repository.create_execution_step(step)
            steps.append(step)
        
        return steps
    
    async def _execute_step(
        self,
        step: ExecutionStepModel,
        execution: ExecutionModel
    ) -> StepExecutionResult:
        """
        Execute a single step
        
        Args:
            step: Execution step model
            execution: Execution model
        
        Returns:
            StepExecutionResult
        """
        started_at = datetime.utcnow()
        
        try:
            logger.info("")
            logger.info("▶️  " + "=" * 78)
            logger.info(f"▶️  EXECUTING STEP: {step.step_name}")
            logger.info(f"▶️  Step ID: {step.step_id}")
            logger.info(f"▶️  Step Type: {step.step_type}")
            logger.info(f"▶️  Step Index: {step.step_index}")
            logger.info("▶️  " + "=" * 78)
            
            # Update step status to running
            logger.info("   📝 Updating step status to RUNNING...")
            self.repository.update_step_status(
                step.step_id,
                ExecutionStatus.RUNNING
            )
            
            # Execute step based on type
            logger.info(f"   🔧 Executing step by type: {step.step_type}")
            output_data = await self._execute_step_by_type(step, execution)
            
            # Check if execution failed (output_data contains error status)
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            # Determine if step succeeded or failed based on output_data
            step_failed = False
            error_message = None
            
            if isinstance(output_data, dict):
                # Check for error status in output
                if output_data.get("status") == "error":
                    step_failed = True
                    error_message = output_data.get("error", "Unknown error")
                    logger.info(f"   ⚠️  Step returned error status: {error_message}")
            
            if step_failed:
                # Update step status to failed
                logger.info(f"   📝 Updating step status to FAILED...")
                self.repository.update_step_status(
                    step.step_id,
                    ExecutionStatus.FAILED,
                    error_message=error_message,
                    output_data=output_data,
                    duration_ms=duration_ms
                )
                
                logger.info("")
                logger.info(f"❌ STEP FAILED")
                logger.info(f"   • Duration: {duration_ms}ms")
                logger.info(f"   • Error: {error_message}")
                logger.info("=" * 80)
                
                return StepExecutionResult(
                    step_id=step.step_id,
                    status=ExecutionStatus.FAILED,
                    error_message=error_message,
                    output_data=output_data,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )
            else:
                # Update step status to completed
                logger.info(f"   📝 Updating step status to COMPLETED...")
                self.repository.update_step_status(
                    step.step_id,
                    ExecutionStatus.COMPLETED,
                    output_data=output_data,
                    duration_ms=duration_ms
                )
                
                logger.info("")
                logger.info(f"✅ STEP COMPLETED SUCCESSFULLY")
                logger.info(f"   • Duration: {duration_ms}ms")
                logger.info(f"   • Output keys: {list(output_data.keys()) if output_data else 'None'}")
                logger.info("=" * 80)
                
                return StepExecutionResult(
                    step_id=step.step_id,
                    status=ExecutionStatus.COMPLETED,
                    output_data=output_data,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )
        
        except Exception as e:
            logger.error(
                f"Step failed: {step.step_id}, error={e}",
                exc_info=True
            )
            
            # Update step status to failed
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            self.repository.update_step_status(
                step.step_id,
                ExecutionStatus.FAILED,
                error_message=str(e),
                duration_ms=duration_ms
            )
            
            return StepExecutionResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                error_details={"exception": type(e).__name__},
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )
    
    def _convert_tool_to_command(
        self,
        tool_name: str,
        inputs: Dict[str, Any]
    ) -> str:
        """
        Convert tool name and inputs to executable command
        
        Args:
            tool_name: Name of the tool (e.g., 'ps', 'journalctl')
            inputs: Tool inputs
        
        Returns:
            Executable command string
        """
        tool_name = tool_name.lower()
        
        # PS command
        if tool_name == "ps":
            cmd = "ps"
            if inputs.get("format") == "detailed":
                cmd += " aux"
            if inputs.get("sort_by") == "cpu_usage":
                cmd += " --sort=-%cpu"
            return cmd
        
        # Journalctl command
        elif tool_name == "journalctl":
            cmd = "journalctl"
            if inputs.get("lines"):
                cmd += f" -n {inputs['lines']}"
            if inputs.get("priority"):
                cmd += f" -p {inputs['priority']}"
            if not inputs.get("follow", False):
                cmd += " --no-pager"
            return cmd
        
        # Network tools (ping, traceroute, etc.)
        elif tool_name == "network_tools":
            subtool = inputs.get("tool", "ping")
            if subtool == "ping":
                target = inputs.get("target", "localhost")
                count = inputs.get("count", 4)
                return f"ping -c {count} {target}"
            elif subtool == "traceroute":
                target = inputs.get("target", "localhost")
                return f"traceroute {target}"
            elif subtool == "netstat":
                return "netstat -tuln"
            return "ping -c 4 localhost"
        
        # Systemctl command
        elif tool_name == "systemctl":
            action = inputs.get("action", "status")
            service = inputs.get("service", "")
            return f"systemctl {action} {service}".strip()
        
        # Df (disk free) command
        elif tool_name == "df":
            cmd = "df"
            if inputs.get("human_readable", True):
                cmd += " -h"
            if inputs.get("filesystem_type"):
                cmd += f" -t {inputs['filesystem_type']}"
            return cmd
        
        # Default: return the tool name as command
        else:
            logger.warning(f"Unknown tool: {tool_name}, using as-is")
            return tool_name
    
    async def _execute_step_by_type(
        self,
        step: ExecutionStepModel,
        execution: ExecutionModel
    ) -> Dict[str, Any]:
        """
        Execute step based on step type
        
        Args:
            step: Execution step model
            execution: Execution model
        
        Returns:
            Output data
        """
        logger.info("")
        logger.info("🔍 DETERMINING STEP TYPE")
        logger.info(f"   • Step type: {step.step_type}")
        logger.info(f"   • Target hostname: {step.target_hostname}")
        logger.info(f"   • Target asset ID: {step.target_asset_id}")
        logger.info(f"   • Input data keys: {list(step.input_data.keys()) if step.input_data else 'None'}")
        
        # Step 1: Fetch asset details if target_asset_id is provided
        asset = None
        if step.target_asset_id:
            try:
                logger.info(f"   🔍 Fetching asset by ID: {step.target_asset_id}")
                asset = await self.asset_client.get_asset_by_id(step.target_asset_id)
                if not asset:
                    raise ValueError(f"Asset not found: {step.target_asset_id}")
                logger.info(f"   ✅ Asset found: {asset.hostname if hasattr(asset, 'hostname') else 'N/A'}")
            except Exception as e:
                logger.error(f"   ❌ Failed to fetch asset {step.target_asset_id}: {e}")
                raise
        elif step.target_hostname:
            try:
                logger.info(f"   🔍 Fetching asset by hostname: {step.target_hostname}")
                asset = await self.asset_client.get_asset_by_hostname(step.target_hostname)
                if not asset:
                    raise ValueError(f"Asset not found: {step.target_hostname}")
                logger.info(f"   ✅ Asset found")
            except Exception as e:
                logger.error(f"   ❌ Failed to fetch asset {step.target_hostname}: {e}")
                raise
        else:
            logger.info("   ℹ️  No target asset specified")
        
        # Step 2: Check if this is a Windows/PowerShell tool
        logger.info("   🔍 Checking if Windows PowerShell tool...")
        if self._is_windows_powershell_tool(step):
            logger.info(f"   ✅ DETECTED: Windows PowerShell tool")
            return await self._execute_winrm_step(step, asset)
        logger.info("   ❌ Not a Windows PowerShell tool")
        
        # Step 2.5: Check if this is a Linux/SSH tool
        logger.info("   🔍 Checking if Linux SSH tool...")
        if self._is_linux_ssh_tool(step):
            logger.info(f"   ✅ DETECTED: Linux SSH tool")
            return await self._execute_ssh_step(step, asset)
        logger.info("   ❌ Not a Linux SSH tool")
        
        # Step 2.6: Check if this is an API/HTTP tool
        logger.info("   🔍 Checking if API/HTTP tool...")
        if self._is_api_http_tool(step):
            logger.info(f"   ✅ DETECTED: API/HTTP tool")
            return await self._execute_api_step(step, asset)
        logger.info("   ❌ Not an API/HTTP tool")
        
        # Step 3: Execute based on step type
        step_type = step.step_type.lower()
        
        if step_type in ["command", "shell", "bash", "powershell", "script"]:
            return await self._execute_command_step(step, asset)
        
        elif step_type in ["api", "http", "rest"]:
            return await self._execute_api_step(step, asset)
        
        elif step_type in ["asset-service-query", "asset-query", "asset-service", "asset-list", "list-assets"]:
            # Handle asset service queries
            return await self._execute_asset_service_query(step)
        
        elif step_type in ["database", "sql", "query"]:
            return await self._execute_database_step(step, asset)
        
        elif step_type in ["file", "copy", "transfer"]:
            return await self._execute_file_step(step, asset)
        
        elif step_type in ["validation", "check", "verify"]:
            return await self._execute_validation_step(step, asset)
        
        else:
            # Default: treat as command execution
            logger.warning(f"Unknown step type: {step_type}, treating as command")
            return await self._execute_command_step(step, asset)
    
    async def _execute_command_step(
        self,
        step: ExecutionStepModel,
        asset: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Execute a command step
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        try:
            # Extract command from input_data
            command = step.input_data.get("command")
            if not command:
                # Try to convert tool name + inputs to command
                command = self._convert_tool_to_command(step.step_type, step.input_data)
                if not command or command == step.step_type:
                    raise ValueError(f"No command specified and unable to convert tool '{step.step_type}' to command")
            
            # Determine connection type
            connection_type = "local"
            credentials = None
            target_host = None
            
            if asset:
                target_host = asset.hostname or asset.ip_address
                connection_type = self.automation_client.determine_connection_type(
                    asset.os_type,
                    asset.service_type
                )
                
                # Build credentials
                credentials = self.automation_client.build_credentials_dict(
                    username=asset.username,
                    password=asset.password,
                    private_key=asset.private_key,
                    api_key=asset.api_key,
                    bearer_token=asset.bearer_token,
                )
            
            # Execute command
            result = await self.automation_client.execute_command(
                command=command,
                target_host=target_host,
                connection_type=connection_type,
                credentials=credentials,
                timeout=step.input_data.get("timeout", 300),
                working_directory=step.input_data.get("working_directory"),
                environment_vars=step.input_data.get("environment_vars"),
            )
            
            # Return output
            return {
                "status": result.status,
                "execution_id": result.execution_id,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": result.duration_seconds,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            raise
    
    async def _execute_api_step(
        self,
        step: ExecutionStepModel,
        asset: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Execute an API/HTTP call step
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        try:
            logger.info("=" * 80)
            logger.info(f"🚀 EXECUTING API STEP: {step.step_name}")
            logger.info("=" * 80)
            
            # Extract connection parameters
            logger.info("📋 Extracting connection parameters...")
            url = step.input_data.get("url") or step.input_data.get("endpoint")
            method = step.input_data.get("method", "GET").upper()
            headers = step.input_data.get("headers", {})
            body = step.input_data.get("body") or step.input_data.get("data")
            params = step.input_data.get("params", {})
            timeout = step.input_data.get("timeout", 30)
            
            logger.info(f"   • URL from input: {url}")
            logger.info(f"   • Method: {method}")
            logger.info(f"   • Headers: {headers}")
            logger.info(f"   • Body: {body}")
            logger.info(f"   • Params: {params}")
            logger.info(f"   • Timeout: {timeout}s")
            
            # Extract authentication
            logger.info("🔐 Extracting authentication parameters...")
            username = step.input_data.get("username") or step.input_data.get("user")
            password = step.input_data.get("password")
            auth_type = step.input_data.get("auth_type", "basic").lower()
            
            logger.info(f"   • Username from input: {username}")
            logger.info(f"   • Password from input: {'***' if password else None}")
            logger.info(f"   • Auth type: {auth_type}")
            
            # Try to get from asset if not in input_data
            if asset and not username:
                logger.info("   • No username in input, checking asset...")
                username = asset.username
                password = asset.password
                logger.info(f"   • Username from asset: {username}")
                logger.info(f"   • Password from asset: {'***' if password else None}")
            
            # Build URL if host is provided separately
            host = step.input_data.get("host") or step.input_data.get("target_host")
            if host and not url:
                logger.info(f"🔧 Building URL from host: {host}")
                protocol = step.input_data.get("protocol", "http")
                port = step.input_data.get("port", "")
                path = step.input_data.get("path", "")
                
                logger.info(f"   • Protocol: {protocol}")
                logger.info(f"   • Port: {port}")
                logger.info(f"   • Path: {path}")
                
                if port:
                    url = f"{protocol}://{host}:{port}{path}"
                else:
                    url = f"{protocol}://{host}{path}"
                
                logger.info(f"   • Constructed URL: {url}")
            
            if not url:
                raise ValueError("No URL or endpoint specified for API call")
            
            logger.info("")
            logger.info("📤 PREPARING HTTP REQUEST")
            logger.info(f"   • Method: {method}")
            logger.info(f"   • URL: {url}")
            logger.info(f"   • Auth Type: {auth_type}")
            logger.info(f"   • Username: {username}")
            logger.info(f"   • Password: {'***' if password else None}")
            
            # Prepare authentication
            auth = None
            if username and password:
                if auth_type == "digest":
                    # Use httpx DigestAuth for digest authentication
                    auth = httpx.DigestAuth(username, password)
                    logger.info("   ✅ Using HTTP Digest Authentication")
                else:  # default to basic
                    # Use httpx BasicAuth
                    auth = httpx.BasicAuth(username, password)
                    logger.info("   ✅ Using HTTP Basic Authentication")
            else:
                logger.info("   ⚠️  No authentication configured")
            
            # Make the HTTP request using httpx
            logger.info("")
            logger.info("🌐 SENDING HTTP REQUEST...")
            start_time = datetime.utcnow()
            
            async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification for internal devices
                logger.info(f"   • Sending {method} request to {url}")
                logger.info(f"   • Timeout: {timeout}s")
                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    content=body if isinstance(body, str) else None,
                    params=params,
                    auth=auth,
                    timeout=timeout
                )
                response_text = response.text
                response_status = response.status_code
                response_headers = dict(response.headers)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("")
            logger.info("📥 RECEIVED HTTP RESPONSE")
            logger.info(f"   • Status Code: {response_status}")
            logger.info(f"   • Duration: {duration:.3f}s")
            logger.info(f"   • Response Length: {len(response_text)} bytes")
            logger.info(f"   • Response Headers: {response_headers}")
            if response_text:
                logger.info(f"   • Response Body: {response_text[:500]}")  # First 500 chars
            else:
                logger.info(f"   • Response Body: (empty)")
            
            success = 200 <= response_status < 300
            logger.info("")
            if success:
                logger.info("✅ API REQUEST SUCCESSFUL")
            else:
                logger.info(f"❌ API REQUEST FAILED (Status: {response_status})")
            logger.info("=" * 80)
            
            return {
                "status": "success" if success else "error",
                "http_status": response_status,
                "response": response_text,
                "response_headers": response_headers,
                "duration": duration,
                "url": url,
                "method": method,
                "connection_type": "api",
                "timestamp": end_time.isoformat(),
            }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP client error: {e}", exc_info=True)
            return {
                "status": "error",
                "error": f"HTTP client error: {str(e)}",
                "error_type": "HTTPError",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"API execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_asset_service_query(
        self,
        step: ExecutionStepModel
    ) -> Dict[str, Any]:
        """
        Execute an asset service query
        
        Args:
            step: Execution step model
        
        Returns:
            Output data with asset query results
        """
        try:
            logger.info(f"Executing asset service query: {step.step_name}")
            
            # Extract query parameters from input_data
            query_type = step.input_data.get("query_type", "list_all")
            filters = step.input_data.get("filters", {})
            fields = step.input_data.get("fields", [])
            limit = step.input_data.get("limit", 100)
            
            logger.info(f"Query params: type={query_type}, filters={filters}, limit={limit}")
            
            # Execute the query based on type
            if query_type == "list_all":
                # Fetch all assets
                assets = await self.asset_client.get_all_assets(limit=limit)
                
                # Filter fields if specified
                if fields and len(fields) > 0:
                    filtered_data = []
                    for asset in assets:
                        asset_dict = asset.dict() if hasattr(asset, 'dict') else asset
                        # Only include requested fields
                        filtered_asset = {field: asset_dict.get(field) for field in fields if field in asset_dict}
                        filtered_data.append(filtered_asset)
                    data = filtered_data
                else:
                    # Return all fields if no field filter specified
                    data = [asset.dict() if hasattr(asset, 'dict') else asset for asset in assets]
                
                return {
                    "status": "success",
                    "count": len(assets),
                    "data": data,
                    "query_type": query_type,
                    "fields_requested": fields if fields else "all",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            elif query_type == "count":
                # Just count assets
                assets = await self.asset_client.get_all_assets(limit=10000)
                
                return {
                    "status": "success",
                    "count": len(assets),
                    "query_type": query_type,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            elif query_type == "by_type":
                # Filter by asset type
                asset_type = filters.get("type")
                if not asset_type:
                    raise ValueError("Asset type filter required for 'by_type' query")
                
                assets = await self.asset_client.get_assets_by_type(asset_type, limit=limit)
                
                # Filter fields if specified
                if fields and len(fields) > 0:
                    filtered_data = []
                    for asset in assets:
                        asset_dict = asset.dict() if hasattr(asset, 'dict') else asset
                        filtered_asset = {field: asset_dict.get(field) for field in fields if field in asset_dict}
                        filtered_data.append(filtered_asset)
                    data = filtered_data
                else:
                    data = [asset.dict() if hasattr(asset, 'dict') else asset for asset in assets]
                
                return {
                    "status": "success",
                    "count": len(assets),
                    "data": data,
                    "query_type": query_type,
                    "filter": {"type": asset_type},
                    "fields_requested": fields if fields else "all",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            else:
                # Default: list all
                logger.warning(f"Unknown query_type: {query_type}, defaulting to list_all")
                assets = await self.asset_client.get_all_assets(limit=limit)
                
                # Filter fields if specified
                if fields and len(fields) > 0:
                    filtered_data = []
                    for asset in assets:
                        asset_dict = asset.dict() if hasattr(asset, 'dict') else asset
                        filtered_asset = {field: asset_dict.get(field) for field in fields if field in asset_dict}
                        filtered_data.append(filtered_asset)
                    data = filtered_data
                else:
                    data = [asset.dict() if hasattr(asset, 'dict') else asset for asset in assets]
                
                return {
                    "status": "success",
                    "count": len(assets),
                    "data": data,
                    "query_type": "list_all",
                    "fields_requested": fields if fields else "all",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        
        except Exception as e:
            logger.error(f"Asset service query failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "query_type": step.input_data.get("query_type", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_database_step(
        self,
        step: ExecutionStepModel,
        asset: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Execute a database query step
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        # TODO: Implement database execution
        # For now, return placeholder
        logger.warning("Database step execution not yet implemented")
        
        return {
            "status": "success",
            "message": "Database execution placeholder",
            "query": step.input_data.get("query"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _execute_file_step(
        self,
        step: ExecutionStepModel,
        asset: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Execute a file operation step
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        # TODO: Implement file operations
        # For now, use scp/rsync commands as fallback
        logger.info("File step execution - using scp/rsync fallback")
        
        source = step.input_data.get("source")
        destination = step.input_data.get("destination")
        operation = step.input_data.get("operation", "copy")
        
        if operation == "copy" and asset:
            # Build scp command
            target_host = asset.hostname or asset.ip_address
            command = f"scp {source} {asset.username}@{target_host}:{destination}"
            
            result = await self.automation_client.execute_command(
                command=command,
                connection_type="local",
                timeout=step.input_data.get("timeout", 300),
            )
            
            return {
                "status": result.status,
                "output": result.stdout,
                "error": result.stderr,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        return {
            "status": "success",
            "message": "File operation placeholder",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _execute_validation_step(
        self,
        step: ExecutionStepModel,
        asset: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Execute a validation step
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        # TODO: Implement validation logic
        logger.info("Validation step execution")
        
        validation_type = step.input_data.get("validation_type", "command")
        
        if validation_type == "command":
            # Execute validation command
            command = step.input_data.get("command")
            if command and asset:
                result = await self._execute_command_step(step, asset)
                
                # Check if validation passed
                expected_output = step.input_data.get("expected_output")
                expected_exit_code = step.input_data.get("expected_exit_code", 0)
                
                validation_passed = (
                    result.get("exit_code") == expected_exit_code
                )
                
                if expected_output and validation_passed:
                    validation_passed = expected_output in result.get("stdout", "")
                
                return {
                    "status": "success" if validation_passed else "failed",
                    "validation_passed": validation_passed,
                    "output": result.get("stdout"),
                    "timestamp": datetime.utcnow().isoformat(),
                }
        
        return {
            "status": "success",
            "validation_passed": True,
            "message": "Validation placeholder",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _determine_final_status(
        self,
        step_results: List[Dict[str, Any]]
    ) -> ExecutionStatus:
        """
        Determine final execution status based on step results
        
        Args:
            step_results: List of step results
        
        Returns:
            Final execution status
        """
        if not step_results:
            return ExecutionStatus.COMPLETED
        
        failed_count = sum(
            1 for r in step_results
            if r.get("status") == ExecutionStatus.FAILED.value
        )
        completed_count = sum(
            1 for r in step_results
            if r.get("status") == ExecutionStatus.COMPLETED.value
        )
        
        if failed_count == 0:
            return ExecutionStatus.COMPLETED
        elif completed_count == 0:
            return ExecutionStatus.FAILED
        else:
            return ExecutionStatus.PARTIAL
    
    def _is_windows_powershell_tool(self, step: ExecutionStepModel) -> bool:
        """
        Determine if a step is a Windows PowerShell tool
        
        Args:
            step: Execution step model
        
        Returns:
            True if this is a Windows PowerShell tool
        """
        # FIRST: Check if input_data explicitly indicates connection type
        # This takes precedence over tool name detection
        if step.input_data:
            connection_type = step.input_data.get('connection_type', '').lower()
            # If explicitly marked as SSH/Linux, this is NOT a PowerShell tool
            if connection_type in ['ssh', 'linux', 'unix']:
                return False
            # If explicitly marked as WinRM/PowerShell, this IS a PowerShell tool
            if connection_type in ['winrm', 'powershell', 'windows']:
                return True
        
        step_type = step.step_type.lower()
        
        # Check for PowerShell cmdlets (they typically use Verb-Noun format)
        powershell_cmdlets = [
            'invoke-command', 'get-childitem', 'get-process', 'get-service',
            'set-service', 'start-service', 'stop-service', 'restart-service',
            'get-eventlog', 'get-winevent', 'test-connection', 'get-content',
            'set-content', 'new-item', 'remove-item', 'copy-item', 'move-item',
            'get-computerinfo', 'get-hotfix', 'get-windowsfeature'
        ]
        
        if step_type in powershell_cmdlets:
            return True
        
        # Check if command contains PowerShell cmdlets
        if step.input_data:
            command = step.input_data.get('command', '').lower()
            if any(cmdlet in command for cmdlet in powershell_cmdlets):
                return True
        
        return False
    
    def _is_linux_ssh_tool(self, step: ExecutionStepModel) -> bool:
        """
        Determine if a step is a Linux SSH tool
        
        Args:
            step: Execution step model
        
        Returns:
            True if this is a Linux SSH tool
        """
        step_type = step.step_type.lower()
        
        # Check for common Linux commands
        linux_commands = [
            'ls', 'cd', 'pwd', 'cat', 'grep', 'find', 'ps', 'top', 'df', 'du',
            'chmod', 'chown', 'mkdir', 'rm', 'cp', 'mv', 'touch', 'echo',
            'systemctl', 'service', 'apt', 'yum', 'dnf', 'zypper',
            'ssh', 'scp', 'rsync', 'curl', 'wget', 'tar', 'gzip', 'unzip'
        ]
        
        if step_type in linux_commands:
            return True
        
        # Check if input_data indicates Linux/SSH
        if step.input_data:
            connection_type = step.input_data.get('connection_type', '').lower()
            if connection_type in ['ssh', 'linux', 'unix']:
                return True
            
            # Check if command contains Linux commands
            command = step.input_data.get('command', '').lower()
            if any(cmd in command for cmd in linux_commands):
                return True
        
        return False
    
    def _is_api_http_tool(self, step: ExecutionStepModel) -> bool:
        """
        Check if this step is an API/HTTP tool
        
        Args:
            step: Execution step model
        
        Returns:
            True if this is an API/HTTP tool
        """
        step_type = step.step_type.lower()
        
        # Check for explicit API/HTTP markers
        api_keywords = [
            'api', 'http', 'https', 'rest', 'restful', 'web', 'curl', 'wget',
            'get', 'post', 'put', 'patch', 'delete', 'request'
        ]
        
        if any(keyword in step_type for keyword in api_keywords):
            return True
        
        # Check if input_data indicates API/HTTP
        if step.input_data:
            connection_type = step.input_data.get('connection_type', '').lower()
            if connection_type in ['api', 'http', 'https', 'rest']:
                return True
            
            # Check for URL in input_data
            if 'url' in step.input_data or 'endpoint' in step.input_data:
                return True
            
            # Check for HTTP method
            method = step.input_data.get('method', '').upper()
            if method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']:
                return True
        
        return False
    
    async def _execute_winrm_step(
        self,
        step: ExecutionStepModel,
        asset: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Execute a Windows PowerShell step via WinRM
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        if not self.winrm_library:
            raise RuntimeError(
                "WinRM library not available. Install with: pip install pywinrm"
            )
        
        try:
            # Extract connection parameters
            target_host = None
            username = None
            password = None
            
            # Try to get from asset first
            if asset:
                target_host = asset.hostname or asset.ip_address
                username = asset.username
                password = asset.password
            
            # Override with step input_data if provided
            if step.input_data:
                # Support multiple naming conventions
                target_host = step.input_data.get('target_host') or \
                             step.input_data.get('computerName') or \
                             step.input_data.get('computer_name') or \
                             target_host
                
                # Check for credential object (PowerShell style)
                if 'credential' in step.input_data and isinstance(step.input_data['credential'], dict):
                    username = step.input_data['credential'].get('username', username)
                    password = step.input_data['credential'].get('password', password)
                else:
                    username = step.input_data.get('username', username)
                    password = step.input_data.get('password', password)
            
            # Validate required parameters
            if not target_host:
                raise ValueError("target_host is required for WinRM execution")
            if not username:
                raise ValueError("username is required for WinRM execution")
            if not password:
                raise ValueError("password is required for WinRM execution")
            
            # Build PowerShell script
            script = self._build_powershell_script(step)
            
            logger.info(
                f"Executing PowerShell via WinRM: host={target_host}, "
                f"user={username}, script_length={len(script)}"
            )
            
            # Execute via WinRM
            result = self.winrm_library.execute_powershell(
                target_host=target_host,
                username=username,
                password=password,
                script=script,
                timeout=step.input_data.get('timeout', 300) if step.input_data else 300,
                use_ssl=step.input_data.get('use_ssl', False) if step.input_data else False,
                port=step.input_data.get('port') if step.input_data else None
            )
            
            # Return output
            return {
                "status": "completed" if result.get("success") else "failed",
                "exit_code": result.get("exit_code", 0),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "duration_seconds": result.get("duration_seconds", 0),
                "attempts": result.get("attempts", 1),
                "timestamp": datetime.utcnow().isoformat(),
                "connection_type": "winrm",
            }
        
        except Exception as e:
            logger.error(f"WinRM execution failed: {e}", exc_info=True)
            raise
    
    def _build_powershell_script(self, step: ExecutionStepModel) -> str:
        """
        Build PowerShell script from step
        
        Args:
            step: Execution step model
        
        Returns:
            PowerShell script string
        """
        # If there's a direct script/command in input_data, use it
        if step.input_data:
            if 'script' in step.input_data:
                return step.input_data['script']
            if 'command' in step.input_data:
                return step.input_data['command']
        
        # Otherwise, build from step_type and inputs
        step_type = step.step_type
        inputs = step.input_data or {}
        
        # Handle common PowerShell cmdlets
        if step_type.lower() == 'invoke-command':
            # Invoke-Command with ScriptBlock
            script_block = inputs.get('ScriptBlock', inputs.get('script_block', ''))
            if script_block:
                return script_block
            else:
                # Default: Get directory listing
                return "Get-ChildItem"
        
        elif step_type.lower() == 'get-childitem':
            path = inputs.get('Path', inputs.get('path', 'C:\\'))
            return f"Get-ChildItem -Path '{path}'"
        
        elif step_type.lower() == 'get-process':
            name = inputs.get('Name', inputs.get('name', ''))
            if name:
                return f"Get-Process -Name '{name}'"
            return "Get-Process"
        
        elif step_type.lower() == 'get-service':
            name = inputs.get('Name', inputs.get('name', ''))
            if name:
                return f"Get-Service -Name '{name}'"
            return "Get-Service"
        
        else:
            # Default: use step_type as cmdlet name
            logger.warning(f"Unknown PowerShell cmdlet: {step_type}, using as-is")
            return step_type
    
    async def _execute_ssh_step(
        self,
        step: ExecutionStepModel,
        asset: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Execute a Linux bash step via SSH
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        if not self.ssh_library:
            raise RuntimeError(
                "SSH library not available. Install with: pip install paramiko"
            )
        
        try:
            # Extract connection parameters
            target_host = None
            username = None
            password = None
            private_key = None
            port = 22
            
            # Try to get from asset first
            if asset:
                target_host = asset.hostname or asset.ip_address
                username = asset.username
                password = asset.password
                if hasattr(asset, 'private_key'):
                    private_key = asset.private_key
            
            # Override with step input_data if provided
            if step.input_data:
                # Support multiple naming conventions
                target_host = step.input_data.get('target_host') or \
                             step.input_data.get('hostname') or \
                             step.input_data.get('host') or \
                             target_host
                
                username = step.input_data.get('username') or \
                          step.input_data.get('user') or \
                          username
                
                password = step.input_data.get('password', password)
                private_key = step.input_data.get('private_key', private_key)
                port = step.input_data.get('port', port)
            
            # Validate required parameters
            if not target_host:
                raise ValueError("target_host is required for SSH execution")
            if not username:
                raise ValueError("username is required for SSH execution")
            if not password and not private_key:
                raise ValueError("password or private_key is required for SSH execution")
            
            # Build bash script
            script = self._build_bash_script(step)
            
            logger.info(
                f"Executing bash via SSH: host={target_host}, "
                f"user={username}, script_length={len(script)}"
            )
            
            # Execute via SSH
            result = self.ssh_library.execute_bash(
                target_host=target_host,
                username=username,
                password=password,
                private_key=private_key,
                script=script,
                timeout=step.input_data.get('timeout', 300) if step.input_data else 300,
                port=port
            )
            
            # Return output
            return {
                "status": "completed" if result.get("success") else "failed",
                "exit_code": result.get("exit_code", 0),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "duration_seconds": result.get("duration_seconds", 0),
                "attempts": result.get("attempts", 1),
                "timestamp": datetime.utcnow().isoformat(),
                "connection_type": "ssh",
            }
        
        except Exception as e:
            logger.error(f"SSH execution failed: {e}", exc_info=True)
            raise
    
    def _build_bash_script(self, step: ExecutionStepModel) -> str:
        """
        Build bash script from step
        
        Args:
            step: Execution step model
        
        Returns:
            Bash script string
        """
        # If there's a direct script/command in input_data, use it
        if step.input_data:
            if 'script' in step.input_data:
                return step.input_data['script']
            if 'command' in step.input_data:
                return step.input_data['command']
        
        # Otherwise, build from step_type and inputs
        step_type = step.step_type.lower()
        inputs = step.input_data or {}
        
        # Handle common Linux commands
        if step_type == 'ls':
            path = inputs.get('path', inputs.get('directory', '/root'))
            options = inputs.get('options', '-la')
            return f"ls {options} {path}"
        
        elif step_type == 'cat':
            file_path = inputs.get('file', inputs.get('path', ''))
            if file_path:
                return f"cat {file_path}"
            return "cat"
        
        elif step_type == 'ps':
            options = inputs.get('options', 'aux')
            return f"ps {options}"
        
        elif step_type == 'df':
            options = inputs.get('options', '-h')
            return f"df {options}"
        
        elif step_type == 'systemctl':
            action = inputs.get('action', 'status')
            service = inputs.get('service', '')
            if service:
                return f"systemctl {action} {service}"
            return f"systemctl {action}"
        
        else:
            # Default: use step_type as command
            logger.warning(f"Unknown Linux command: {step_type}, using as-is")
            return step_type
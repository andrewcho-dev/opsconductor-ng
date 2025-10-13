#!/usr/bin/env python3
"""
OpsConductor Automation Service - CLEAN ARCHITECTURE
Simple execution API - No Celery, No Background Processing
Handles direct command execution and task management

UNIFIED EXECUTION FRAMEWORK:
All tool executions follow the same procedural steps.
The "flavor" is determined by tool metadata, not hardcoded logic.
"""

import sys
import os
import json
import asyncio
import subprocess
from typing import List, Optional, Dict, Any
from fastapi import Query, HTTPException, status, WebSocket
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging
import httpx

sys.path.append('/app/shared')
from base_service import BaseService
from execution_context import create_execution_context

# Import unified executor
from unified_executor import UnifiedExecutor

# ============================================================================
# CLEAN EXECUTION STATUS
# ============================================================================

class ExecutionStatus:
    """Simple execution status constants - matches execution.models.ExecutionStatus"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"  # Changed from SUCCESS to match execution.models
    FAILED = "failed"
    
    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if status indicates execution has finished"""
        return status in [cls.COMPLETED, cls.FAILED]

# ============================================================================
# CLEAN DATA MODELS
# ============================================================================

class CommandRequest(BaseModel):
    """Direct command execution request"""
    command: str
    target_host: Optional[str] = None
    connection_type: str = "ssh"  # ssh, powershell, local
    credentials: Optional[Dict[str, Any]] = None
    timeout: int = 300  # 5 minutes default
    working_directory: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None

class ExecutionResult(BaseModel):
    """Command execution result"""
    execution_id: str
    status: str
    command: str
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None

class WorkflowRequest(BaseModel):
    """Multi-step workflow execution request"""
    workflow_id: str
    name: str
    steps: List[CommandRequest]
    continue_on_error: bool = False

class WorkflowResult(BaseModel):
    """Workflow execution result"""
    workflow_id: str
    execution_id: str
    name: str
    status: str
    steps_completed: int
    total_steps: int
    step_results: List[ExecutionResult]
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

# ============================================================================
# CLEAN AUTOMATION SERVICE
# ============================================================================

class CleanAutomationService(BaseService):
    """
    Clean Automation Service - Simple Execution API
    
    Responsibilities:
    - Execute commands directly (synchronous)
    - Handle multi-step workflows
    - Manage connections to target systems
    - Return immediate results
    
    NOT Responsible For:
    - Background job queuing (Prefect handles this)
    - Complex orchestration (AI Brain handles this)
    - Scheduling (Prefect handles this)
    """
    
    def __init__(self):
        super().__init__(
            name="automation-service",
            version="1.0.0",
            port=3003
        )
        
        # Simple in-memory execution tracking
        self.active_executions: Dict[str, ExecutionResult] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # Connection managers
        self.connection_managers = {}
        self._initialize_connection_managers()
        
        # Initialize unified executor
        self.unified_executor = UnifiedExecutor(self.logger)
        
        logger = logging.getLogger(__name__)
        logger.info("🧹 Clean Automation Service initialized - No Celery, Direct Execution Only")
        logger.info("🎯 Unified Execution Framework enabled")
        logger.info("📋 Tool metadata will be provided by planner (no local registry needed)")
    
    def _initialize_connection_managers(self):
        """Initialize connection managers for different target types"""
        try:
            # Import connection libraries
            sys.path.append('/app/libraries')
            from libraries.linux_ssh import LinuxSSHLibrary
            from libraries.windows_powershell import WindowsPowerShellLibrary
            from libraries.windows_impacket_executor import WindowsImpacketExecutor
            
            self.connection_managers = {
                'ssh': LinuxSSHLibrary(),
                'powershell': WindowsPowerShellLibrary() if WindowsPowerShellLibrary else None,
                'impacket': WindowsImpacketExecutor() if WindowsImpacketExecutor else None,
                'local': None  # Direct subprocess execution
            }
            
            available_managers = [k for k, v in self.connection_managers.items() if v is not None]
            self.logger.info(f"Connection managers initialized: {available_managers}")
            
        except ImportError as e:
            self.logger.warning(f"Some connection managers unavailable: {e}")
    
    async def execute_command(self, request: CommandRequest) -> ExecutionResult:
        """
        Execute a single command directly (synchronous execution)
        
        Args:
            request: Command execution request
            
        Returns:
            ExecutionResult: Immediate execution result
        """
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        # Create initial result
        result = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING,
            command=request.command,
            started_at=started_at
        )
        
        # Track active execution
        self.active_executions[execution_id] = result
        
        try:
            self.logger.info(f"Executing command: {request.command[:100]}...")
            
            # Execute based on connection type
            if request.connection_type == "local":
                exit_code, stdout, stderr = await self._execute_local_command(request)
            elif request.connection_type == "ssh":
                exit_code, stdout, stderr = await self._execute_ssh_command(request)
            elif request.connection_type == "powershell":
                exit_code, stdout, stderr = await self._execute_powershell_command(request)
            elif request.connection_type == "impacket":
                exit_code, stdout, stderr = await self._execute_impacket_command(request)
            else:
                raise ValueError(f"Unsupported connection type: {request.connection_type}")
            
            # Update result
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            result.status = ExecutionStatus.COMPLETED if exit_code == 0 else ExecutionStatus.FAILED
            result.exit_code = exit_code
            result.stdout = stdout
            result.stderr = stderr
            result.completed_at = completed_at
            result.duration_seconds = duration
            
            if exit_code != 0:
                result.error_message = f"Command failed with exit code {exit_code}"
            
            self.logger.info(f"Command completed: {execution_id} - Status: {result.status}")
            
        except Exception as e:
            # Handle execution error
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            result.status = ExecutionStatus.FAILED
            result.completed_at = completed_at
            result.duration_seconds = duration
            result.error_message = str(e)
            
            self.logger.error(f"Command execution failed: {execution_id} - Error: {e}")
        
        finally:
            # Move to history and remove from active
            self.execution_history.append(result)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        return result
    
    async def execute_workflow(self, request: WorkflowRequest) -> WorkflowResult:
        """
        Execute a multi-step workflow
        
        Args:
            request: Workflow execution request
            
        Returns:
            WorkflowResult: Complete workflow execution result
        """
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        step_results = []
        
        self.logger.info(f"Starting workflow: {request.name} ({len(request.steps)} steps)")
        
        try:
            for i, step in enumerate(request.steps):
                self.logger.info(f"Executing step {i+1}/{len(request.steps)}: {step.command[:50]}...")
                
                # Execute step
                step_result = await self.execute_command(step)
                step_results.append(step_result)
                
                # Check if step failed and we shouldn't continue
                if step_result.status == ExecutionStatus.FAILED and not request.continue_on_error:
                    self.logger.warning(f"Workflow stopped at step {i+1} due to failure")
                    break
            
            # Determine overall status
            failed_steps = [r for r in step_results if r.status == ExecutionStatus.FAILED]
            overall_status = ExecutionStatus.FAILED if failed_steps else ExecutionStatus.SUCCESS
            
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            result = WorkflowResult(
                workflow_id=request.workflow_id,
                execution_id=execution_id,
                name=request.name,
                status=overall_status,
                steps_completed=len(step_results),
                total_steps=len(request.steps),
                step_results=step_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
            self.logger.info(f"Workflow completed: {request.name} - Status: {overall_status}")
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {request.name} - Error: {e}")
            
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            return WorkflowResult(
                workflow_id=request.workflow_id,
                execution_id=execution_id,
                name=request.name,
                status=ExecutionStatus.FAILED,
                steps_completed=len(step_results),
                total_steps=len(request.steps),
                step_results=step_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
    
    async def _execute_local_command(self, request: CommandRequest) -> tuple[int, str, str]:
        """Execute command locally using subprocess"""
        try:
            # Prepare environment
            env = os.environ.copy()
            if request.environment_vars:
                env.update(request.environment_vars)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                request.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=request.working_directory,
                env=env
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=request.timeout
            )
            
            return process.returncode, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            raise Exception(f"Command timed out after {request.timeout} seconds")
        except Exception as e:
            raise Exception(f"Local execution failed: {e}")
    
    async def _execute_ssh_command(self, request: CommandRequest) -> tuple[int, str, str]:
        """Execute command via SSH"""
        if 'ssh' not in self.connection_managers or not self.connection_managers['ssh']:
            raise Exception("SSH connection manager not available")
        
        # Use SSH library to execute command
        ssh_manager = self.connection_managers['ssh']
        
        # This would need to be implemented based on your SSH library
        # For now, return a placeholder
        return 0, "SSH execution not yet implemented", ""
    
    async def _execute_powershell_command(self, request: CommandRequest) -> tuple[int, str, str]:
        """Execute command via PowerShell/WinRM"""
        if 'powershell' not in self.connection_managers or not self.connection_managers['powershell']:
            raise Exception("PowerShell connection manager not available")
        
        if not request.target_host:
            raise Exception("target_host is required for PowerShell execution")
        
        if not request.credentials:
            raise Exception("credentials (username/password) are required for PowerShell execution")
        
        # Extract credentials
        username = request.credentials.get("username")
        password = request.credentials.get("password")
        
        if not username or not password:
            raise Exception("Both username and password are required in credentials")
        
        # Use PowerShell library to execute command
        ps_manager = self.connection_managers['powershell']
        
        # Debug: Log what we're about to pass to execute_powershell
        self.logger.info(
            f"DEBUG: About to call execute_powershell with: "
            f"target_host={request.target_host}, "
            f"username={username}, "
            f"password={'*' * len(password) if password else 'None'}"
        )
        
        # Execute PowerShell script via WinRM
        # Note: execute_powershell is synchronous, so we run it in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            ps_manager.execute_powershell,
            request.target_host,
            username,
            password,
            request.command,
            request.timeout,
            False,  # use_ssl - default to False for HTTP WinRM
            None    # port - will use default 5985
        )
        
        # Extract results
        exit_code = result.get("exit_code", -1)
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        
        if not result.get("success"):
            error_msg = result.get("error", "Unknown PowerShell execution error")
            self.logger.error(f"PowerShell execution failed: {error_msg}")
            # Return error in stderr
            stderr = error_msg if not stderr else f"{stderr}\n{error_msg}"
        
        return exit_code, stdout, stderr
    
    async def _execute_impacket_command(self, request: CommandRequest) -> tuple[int, str, str]:
        """Execute command via Impacket WMI"""
        if 'impacket' not in self.connection_managers or not self.connection_managers['impacket']:
            raise Exception("Impacket connection manager not available")
        
        if not request.target_host:
            raise Exception("target_host is required for Impacket execution")
        
        if not request.credentials:
            raise Exception("credentials (username/password) are required for Impacket execution")
        
        # Extract credentials
        username = request.credentials.get("username")
        password = request.credentials.get("password")
        domain = request.credentials.get("domain", "")  # Empty string for local accounts
        
        if not username or not password:
            raise Exception("Both username and password are required in credentials")
        
        # Extract Impacket-specific options from environment_vars if provided
        interactive = False
        session_id = None
        wait = True
        
        if request.environment_vars:
            interactive = request.environment_vars.get("interactive", "false").lower() == "true"
            session_id_str = request.environment_vars.get("session_id")
            if session_id_str:
                try:
                    session_id = int(session_id_str)
                except ValueError:
                    self.logger.warning(f"Invalid session_id: {session_id_str}, ignoring")
            wait = request.environment_vars.get("wait", "true").lower() == "true"
            # Also check for domain in environment_vars
            if "domain" in request.environment_vars:
                domain = request.environment_vars.get("domain", "")
        
        # Use Impacket library to execute command
        impacket_manager = self.connection_managers['impacket']
        
        # Execute command via Impacket WMI
        # Note: execute_command is synchronous, so we run it in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            impacket_manager.execute_command,
            request.target_host,
            username,
            password,
            request.command,
            domain,
            interactive,
            session_id,
            request.timeout,
            wait
        )
        
        # Extract results
        exit_code = result.get("exit_code", -1)
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        
        if not result.get("success"):
            error_msg = result.get("error", "Unknown Impacket execution error")
            self.logger.error(f"Impacket execution failed: {error_msg}")
            # Return error in stderr
            stderr = error_msg if not stderr else f"{stderr}\n{error_msg}"
        
        return exit_code, stdout, stderr

# ============================================================================
# API ENDPOINTS
# ============================================================================

# Create service instance
service = CleanAutomationService()

@service.app.post("/execute", response_model=ExecutionResult)
async def execute_command(request: CommandRequest):
    """Execute a single command directly"""
    try:
        result = await service.execute_command(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@service.app.post("/workflow", response_model=WorkflowResult)
async def execute_workflow(request: WorkflowRequest):
    """Execute a multi-step workflow"""
    try:
        result = await service.execute_workflow(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@service.app.get("/executions/active")
async def get_active_executions():
    """Get currently running executions"""
    return {"active_executions": list(service.active_executions.values())}

@service.app.get("/executions/history")
async def get_execution_history(limit: int = Query(50, ge=1, le=1000)):
    """Get execution history"""
    recent_history = service.execution_history[-limit:] if service.execution_history else []
    return {"executions": recent_history, "total": len(service.execution_history)}

# ============================================================================
# MOUNT ROUTERS
# ============================================================================

# Import and mount selector router with safe retry logic
try:
    from shared.selector_router import router as selector_router
except Exception as _e:
    print("[selector] import error:", _e)
    selector_router = None

def _include_router_on(obj):
    if not obj or not selector_router:
        return False
    app_obj = getattr(obj, "app", None) if hasattr(obj, "app") else obj
    if hasattr(app_obj, "include_router"):
        try:
            # Store service instance for router access to db pool
            if hasattr(app_obj, "state") and "service" in globals():
                app_obj.state.service = globals()["service"]
            app_obj.include_router(selector_router)
            print("[selector] route mounted on", getattr(app_obj, "title", "app"))
            return True
        except Exception as ee:
            print("[selector] include_router failed:", ee)
    return False

# Try immediate mount on all likely names
_mounted = False
for _name in ("service", "app", "application", "api"):
    _mounted |= _include_router_on(globals().get(_name))

# If not yet mounted, schedule a short retry after startup
if not _mounted:
    try:
        import asyncio
        async def _retry_mount():
            await asyncio.sleep(0.1)
            ok = False
            for _name in ("service", "app", "application", "api"):
                ok |= _include_router_on(globals().get(_name))
            if not ok:
                print("[selector] WARNING: router not mounted; check app variable names")
        # Attach to whichever app exists to ensure loop context; fall back to bare create_task
        _app = globals().get("service").app if ("service" in globals() and hasattr(globals().get("service"), "app")) else globals().get("app")
        try:
            @_app.on_event("startup")
            async def _mount_selector_on_startup():
                await _retry_mount()
        except Exception:
            asyncio.get_event_loop().create_task(_retry_mount())
    except Exception as e:
        print("[selector] scheduling retry failed:", e)

# Optional: list route once if mounted
try:
    _app2 = globals().get("service").app if ("service" in globals() and hasattr(globals().get("service"), "app")) else globals().get("app")
    if _app2:
        for r in _app2.routes:
            p = getattr(r, "path", None) or getattr(r, "path_format", None)
            if p == "/api/selector/search":
                print("[selector] confirmed:", p, getattr(r, "methods", []))
                break
except Exception:
    pass

# ============================================================================
# PLAN EXECUTION MODELS
# ============================================================================

class PlanExecutionRequest(BaseModel):
    """Plan execution request from AI pipeline"""
    execution_id: str
    plan: Dict[str, Any]
    tenant_id: str
    actor_id: int


async def _execute_single_step(
    service_instance, 
    step: Dict[str, Any], 
    step_index: int,
    loop_iteration: int = 1,
    loop_total: int = 1
) -> Dict[str, Any]:
    """
    Execute a single step using UNIFIED EXECUTION FRAMEWORK
    
    All tool types follow the same procedural steps:
    1. Parse tool metadata (or infer from tool name/platform)
    2. Resolve parameters
    3. Build command/request
    4. Resolve credentials
    5. Execute
    
    Args:
        service_instance: The automation service instance
        step: Step definition with resolved parameters
        step_index: Index of the step in the plan
        loop_iteration: Current loop iteration (1-based)
        loop_total: Total number of loop iterations
        
    Returns:
        Step result dictionary
    """
    try:
        tool_name = step.get("tool", step.get("tool_name", "unknown"))
        parameters = step.get("inputs", step.get("parameters", {}))
        
        service_instance.logger.info(f"🔧 Executing {tool_name} (iteration {loop_iteration}/{loop_total})")
        service_instance.logger.info(f"📦 Parameters: {json.dumps(parameters, indent=2)}")
        
        # ====================================================================
        # UNIFIED EXECUTION FRAMEWORK
        # ====================================================================
        
        # Create tool definition from step metadata
        # The planner enriches steps with tool metadata from the registry,
        # so we should use that information instead of inferring
        tool_definition = {
            "tool_name": tool_name,
            "platform": step.get("platform", ""),
            "category": step.get("category", ""),
            # Use metadata from the plan if available (enriched by planner)
            "requires_credentials": step.get("requires_credentials", False),
            "execution_location": step.get("execution_location", "automation-service"),
            "tool_metadata": step.get("tool_metadata", {})
        }
        
        service_instance.logger.info(f"🔍 Tool definition: requires_credentials={tool_definition['requires_credentials']}")
        
        # Use unified executor to build command and resolve credentials
        command, target_host, connection_type, credentials = await service_instance.unified_executor.execute_tool(
            tool_definition=tool_definition,
            parameters=parameters,
            service_instance=service_instance
        )
        
        # ====================================================================
        # SPECIAL HANDLERS (for tools that don't execute commands)
        # ====================================================================
        
        # Handle special case: asset-query (calls asset-service API)
        if tool_name in ["asset-query", "asset_query"]:
            service_instance.logger.info(f"🔍 Special handler: asset-query")
            try:
                async with httpx.AsyncClient() as client:
                    asset_service_url = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
                    response = await client.post(
                        f"{asset_service_url}/execute-plan",
                        json={
                            "execution_id": "asset-query",
                            "plan": {"steps": [{"tool": "asset-query", "inputs": parameters}]},
                            "tenant_id": "default",
                            "actor_id": 1
                        },
                        timeout=30.0
                    )
                    response.raise_for_status()
                    asset_result = response.json()
                
                asset_step_results = asset_result.get("step_results", [])
                if asset_step_results:
                    asset_step_result = asset_step_results[0]
                    return {
                        "step": step_index + 1,
                        "loop_iteration": loop_iteration,
                        "loop_total": loop_total,
                        "tool": tool_name,
                        "status": asset_step_result.get("status", "completed"),
                        "output": asset_step_result.get("output", {}),
                        "message": asset_step_result.get("message", "")
                    }
            except Exception as e:
                service_instance.logger.error(f"❌ Asset query failed: {e}")
                return {
                    "step": step_index + 1,
                    "loop_iteration": loop_iteration,
                    "loop_total": loop_total,
                    "tool": tool_name,
                    "status": "failed",
                    "error": str(e)
                }
        
        # ====================================================================
        # COMMAND EXECUTION (unified path for all command-based tools)
        # ====================================================================
        
        # Check if command was built
        if not command:
            skip_result = {
                "step": step_index + 1,
                "loop_iteration": loop_iteration,
                "loop_total": loop_total,
                "tool": tool_name,
                "status": "skipped",
                "message": "No command to execute"
            }
            
            # Add asset information if available
            loop_item = step.get("_loop_item")
            if loop_item and isinstance(loop_item, dict):
                asset_info = {}
                if "name" in loop_item:
                    asset_info["asset_name"] = loop_item["name"]
                if "hostname" in loop_item:
                    asset_info["hostname"] = loop_item["hostname"]
                if "id" in loop_item:
                    asset_info["asset_id"] = loop_item["id"]
                if "ip_address" in loop_item:
                    asset_info["ip_address"] = loop_item["ip_address"]
                
                if asset_info:
                    skip_result["asset"] = asset_info
            
            return skip_result
        
        # Handle special environment variables for impacket
        if connection_type == "impacket":
            env_vars = {}
            if parameters.get("interactive", False):
                env_vars["interactive"] = "true"
            if parameters.get("session_id"):
                env_vars["session_id"] = str(parameters.get("session_id"))
            if "wait" in parameters:
                env_vars["wait"] = "true" if parameters.get("wait") else "false"
            if parameters.get("domain"):
                env_vars["domain"] = parameters.get("domain")
            if env_vars:
                parameters["environment_vars"] = env_vars
        
        # Log execution details
        service_instance.logger.info(f"🎯 Unified execution:")
        service_instance.logger.info(f"   Command: {command}")
        service_instance.logger.info(f"   Target: {target_host}")
        service_instance.logger.info(f"   Connection: {connection_type}")
        if credentials:
            service_instance.logger.info(f"   Credentials: {credentials.get('username')}")
        
        # Execute command
        cmd_request = CommandRequest(
            command=command,
            target_host=target_host,
            connection_type=connection_type,
            credentials=credentials,
            timeout=parameters.get("timeout", 300),
            environment_vars=parameters.get("environment_vars")
        )
        
        result = await service_instance.execute_command(cmd_request)
        
        # Build result dictionary
        result_dict = {
            "step": step_index + 1,
            "loop_iteration": loop_iteration,
            "loop_total": loop_total,
            "tool": tool_name,
            "command": command,
            "target_host": target_host,
            "status": result.status,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_seconds": result.duration_seconds
        }
        
        # Add asset information if available from loop item
        loop_item = step.get("_loop_item")
        if loop_item and isinstance(loop_item, dict):
            # Add identifying information about the asset
            asset_info = {}
            if "name" in loop_item:
                asset_info["asset_name"] = loop_item["name"]
            if "hostname" in loop_item:
                asset_info["hostname"] = loop_item["hostname"]
            if "id" in loop_item:
                asset_info["asset_id"] = loop_item["id"]
            if "ip_address" in loop_item:
                asset_info["ip_address"] = loop_item["ip_address"]
            
            if asset_info:
                result_dict["asset"] = asset_info
        
        return result_dict
        
    except Exception as e:
        service_instance.logger.error(f"Error executing step: {e}", exc_info=True)
        error_result = {
            "step": step_index + 1,
            "loop_iteration": loop_iteration,
            "loop_total": loop_total,
            "tool": step.get("tool", "unknown"),
            "status": "failed",
            "error": str(e)
        }
        
        # Add asset information if available from loop item
        loop_item = step.get("_loop_item")
        if loop_item and isinstance(loop_item, dict):
            asset_info = {}
            if "name" in loop_item:
                asset_info["asset_name"] = loop_item["name"]
            if "hostname" in loop_item:
                asset_info["hostname"] = loop_item["hostname"]
            if "id" in loop_item:
                asset_info["asset_id"] = loop_item["id"]
            if "ip_address" in loop_item:
                asset_info["ip_address"] = loop_item["ip_address"]
            
            if asset_info:
                error_result["asset"] = asset_info
        
        return error_result


@service.app.post("/execute-plan")
async def execute_plan_from_pipeline(request: PlanExecutionRequest):
    """
    Execute a plan from AI-pipeline
    
    THIS IS THE ONLY CONTAINER THAT EXECUTES COMMANDS
    AI-pipeline orchestrates, automation-service executes
    
    Features:
    - Template variable resolution ({{variable}})
    - Step dependency resolution
    - Loop execution for multiple targets
    
    Args:
        request: Plan execution request with execution_id, plan, tenant_id, actor_id
    
    Returns:
        Execution result with status, output, and timing
    """
    started_at = datetime.utcnow()
    step_results = []
    
    try:
        service.logger.info(f"🚀 Received execution request from ai-pipeline: {request.execution_id}")
        service.logger.info(f"📋 Plan: {json.dumps(request.plan, indent=2)}")
        
        # Create execution context for template variables and dependencies
        context = create_execution_context(request.execution_id)
        
        # Load previous results into context (for multi-step orchestration)
        previous_results = request.plan.get("previous_results", [])
        if previous_results:
            service.logger.info(f"📥 Loading {len(previous_results)} previous step results into context")
            for prev_result in previous_results:
                step_index = prev_result.get("step_index", 0)
                context.store_step_result(step_index, prev_result)
                context.extract_variables_from_step_result(step_index, prev_result)
        
        # Extract steps from plan
        steps = request.plan.get("steps", [])
        if not steps:
            service.logger.warning("No steps found in plan")
            return {
                "execution_id": request.execution_id,
                "status": "failed",
                "result": {},
                "step_results": [],
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": "No steps found in execution plan"
            }
        
        print(f"📝 DEBUG: Executing {len(steps)} steps", flush=True)
        service.logger.info(f"📝 Executing {len(steps)} steps")
        
        # Execute each step
        for i, step in enumerate(steps):
            # Extract step details - handle both "tool" and "tool_name" keys
            tool_name = step.get("tool", step.get("tool_name", "unknown"))
            print(f"⚙️  DEBUG: Step {i+1}/{len(steps)}: {tool_name}", flush=True)
            service.logger.info(f"⚙️  Step {i+1}/{len(steps)}: {tool_name}")
            
            # Extract parameters - handle both "inputs" and "parameters" keys
            parameters = step.get("inputs", step.get("parameters", {}))
            service.logger.info(f"📦 Original Parameters: {json.dumps(parameters, indent=2)}")
            
            # Check if this step should be executed in a loop
            is_loop, loop_var, loop_items = context.detect_loop_execution(step)
            print(f"🔍 DEBUG: Loop detection: is_loop={is_loop}, loop_var={loop_var}, items_count={len(loop_items) if loop_items else 0}", flush=True)
            service.logger.info(f"🔍 Loop detection: is_loop={is_loop}, loop_var={loop_var}, items_count={len(loop_items) if loop_items else 0}")
            
            if is_loop and loop_items:
                print(f"🔁 DEBUG: Loop detected! Executing step {i+1} for {len(loop_items)} items", flush=True)
                print(f"🔁 DEBUG: Loop items: {json.dumps(loop_items, indent=2)}", flush=True)
                service.logger.info(f"🔁 Loop detected: Executing step {i+1} for {len(loop_items)} items")
                service.logger.info(f"🔁 Loop items: {json.dumps(loop_items, indent=2)}")
                
                # Expand the step into multiple executions
                expanded_steps = context.expand_step_for_loop(step, loop_items)
                service.logger.info(f"🔁 Expanded into {len(expanded_steps)} steps")
                
                # Execute each expanded step
                for loop_index, expanded_step in enumerate(expanded_steps):
                    print(f"🔁 DEBUG: Loop iteration {loop_index + 1}/{len(expanded_steps)}", flush=True)
                    service.logger.info(f"🔁 Loop iteration {loop_index + 1}/{len(expanded_steps)}")
                    expanded_params = expanded_step.get("inputs", expanded_step.get("parameters", {}))
                    print(f"🔁 DEBUG: Expanded step parameters: {json.dumps(expanded_params, indent=2)}", flush=True)
                    service.logger.info(f"🔁 Expanded step parameters: {json.dumps(expanded_params, indent=2)}")
                    
                    # Execute the expanded step
                    loop_result = await _execute_single_step(
                        service, 
                        expanded_step, 
                        i, 
                        loop_index + 1, 
                        len(expanded_steps)
                    )
                    
                    # Store the result
                    step_results.append(loop_result)
                    
                    # Store in context for potential use by later steps
                    context.store_step_result(i, loop_result)
                
                # After loop completes, extract variables from the last result
                if step_results:
                    context.extract_variables_from_step_result(i, step_results[-1])
                
                continue  # Move to next step
            
            # Not a loop - resolve template variables in parameters
            resolved_parameters = context.resolve_template_in_dict(parameters)
            service.logger.info(f"📦 Resolved Parameters: {json.dumps(resolved_parameters, indent=2)}")
            
            # Update step with resolved parameters
            step_copy = step.copy()
            if "inputs" in step_copy:
                step_copy["inputs"] = resolved_parameters
            else:
                step_copy["parameters"] = resolved_parameters
            
            # Handle special case: asset-query (calls asset-service API, not a command)
            if tool_name in ["asset-query", "asset_query"]:
                # Asset query - call asset-service
                service.logger.info(f"🔍 Executing asset-query")
                
                try:
                    # Call asset-service
                    async with httpx.AsyncClient() as client:
                        asset_service_url = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
                        response = await client.post(
                            f"{asset_service_url}/execute-plan",
                            json={
                                "execution_id": request.execution_id,
                                "plan": {
                                    "steps": [{
                                        "tool": "asset-query",
                                        "inputs": resolved_parameters
                                    }]
                                },
                                "tenant_id": request.tenant_id,
                                "actor_id": request.actor_id
                            },
                            timeout=30.0
                        )
                        response.raise_for_status()
                        asset_result = response.json()
                    
                    # Extract the step result from asset-service response
                    asset_step_results = asset_result.get("step_results", [])
                    if asset_step_results:
                        asset_step_result = asset_step_results[0]
                        step_result = {
                            "step": i+1,
                            "tool": tool_name,
                            "status": asset_step_result.get("status", "success"),
                            "output": asset_step_result.get("output", {}),
                            "message": asset_step_result.get("message", "")
                        }
                    else:
                        step_result = {
                            "step": i+1,
                            "tool": tool_name,
                            "status": "failed",
                            "output": {},
                            "message": "No results from asset-service"
                        }
                    
                    step_results.append(step_result)
                    context.store_step_result(i, step_result)
                    context.extract_variables_from_step_result(i, step_result)
                    
                    service.logger.info(f"✅ Asset query completed: {step_result.get('status')}")
                    continue  # Skip to next step
                    
                except Exception as e:
                    service.logger.error(f"❌ Asset query failed: {e}", exc_info=True)
                    step_result = {
                        "step": i+1,
                        "tool": tool_name,
                        "status": "failed",
                        "output": {},
                        "message": f"Asset query error: {str(e)}"
                    }
                    step_results.append(step_result)
                    context.store_step_result(i, step_result)
                    continue  # Skip to next step
            
            # Use unified executor for ALL command-based tools
            try:
                # Look up tool definition from registry, or create minimal one
                tool_definition = step.get("tool_definition")
                if not tool_definition and service.tool_registry:
                    # Try to get from registry
                    tool_obj = service.tool_registry.get_tool(tool_name)
                    if tool_obj:
                        print(f"🔧 DEBUG: Found tool in registry: {tool_name}", flush=True)
                        tool_definition = {
                            "tool_name": tool_obj.name,
                            "description": tool_obj.description,
                            "execution": tool_obj.execution
                        }
                    else:
                        print(f"⚠️  DEBUG: Tool not found in registry: {tool_name}", flush=True)
                
                # Fallback to minimal definition
                if not tool_definition:
                    tool_definition = {
                        "tool_name": tool_name,
                        "platform": step.get("platform", ""),
                        "category": step.get("category", "")
                    }
                
                # Execute tool using unified executor
                service.logger.info(f"🔧 Using unified executor for tool: {tool_name}")
                command, target_host, connection_type, credentials = await service.unified_executor.execute_tool(
                    tool_definition=tool_definition,
                    parameters=resolved_parameters,
                    service_instance=service
                )
                
                # Handle special environment variables for Impacket tools
                if tool_name in ["windows-impacket-executor", "windows-psexec", "PSExec"]:
                    env_vars = {}
                    if resolved_parameters.get("interactive", False):
                        env_vars["interactive"] = "true"
                    if resolved_parameters.get("session_id"):
                        env_vars["session_id"] = str(resolved_parameters.get("session_id"))
                    if "wait" in resolved_parameters:
                        env_vars["wait"] = "true" if resolved_parameters.get("wait") else "false"
                    if resolved_parameters.get("domain"):
                        env_vars["domain"] = resolved_parameters.get("domain")
                    
                    if env_vars:
                        resolved_parameters["environment_vars"] = env_vars
                        service.logger.info(f"🖥️  Impacket environment vars: {env_vars}")
                
                if not command:
                    service.logger.warning(f"No command found for step {i+1}")
                    step_result = {
                        "step": i+1,
                        "tool": tool_name,
                        "status": "skipped",
                        "message": "No command to execute"
                    }
                    step_results.append(step_result)
                    context.store_step_result(i, step_result)
                    continue
                
            except Exception as e:
                service.logger.error(f"❌ Unified executor failed for tool {tool_name}: {e}", exc_info=True)
                step_result = {
                    "step": i+1,
                    "tool": tool_name,
                    "status": "failed",
                    "output": {},
                    "message": f"Tool execution error: {str(e)}"
                }
                step_results.append(step_result)
                context.store_step_result(i, step_result)
                continue
            
            # Execute command
            cmd_request = CommandRequest(
                command=command,
                target_host=target_host,
                connection_type=connection_type,
                credentials=credentials,
                timeout=resolved_parameters.get("timeout", 300),
                environment_vars=resolved_parameters.get("environment_vars")
            )
            
            result = await service.execute_command(cmd_request)
            
            step_result = {
                "step": i+1,
                "tool": tool_name,
                "command": command,
                "status": result.status,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": result.duration_seconds
            }
            step_results.append(step_result)
            
            # Store result in context for dependency resolution
            context.store_step_result(i, step_result)
            context.extract_variables_from_step_result(i, step_result)
            
            service.logger.info(f"✅ Step {i+1} completed: {result.status}")
        
        # Determine overall status
        failed_steps = [s for s in step_results if s.get("status") == "failed"]
        overall_status = "failed" if failed_steps else "completed"
        
        completed_at = datetime.utcnow()
        
        service.logger.info(f"🎉 Plan execution completed: {overall_status}")
        
        return {
            "execution_id": request.execution_id,
            "status": overall_status,
            "result": {
                "steps_completed": len(step_results),
                "steps_failed": len(failed_steps),
                "steps_succeeded": len([s for s in step_results if s.get("status") == "success"])
            },
            "step_results": step_results,
            "completed_at": completed_at.isoformat(),
            "duration_seconds": (completed_at - started_at).total_seconds()
        }
        
    except Exception as e:
        service.logger.error(f"❌ Plan execution failed: {e}", exc_info=True)
        return {
            "execution_id": request.execution_id,
            "status": "failed",
            "result": {},
            "step_results": step_results,
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": str(e),
            "error_details": {"exception_type": type(e).__name__}
        }

@service.app.get("/status")
async def get_service_status():
    """Get service status and capabilities"""
    available_connections = [k for k, v in service.connection_managers.items() if v is not None]
    
    return {
        "service": "automation-service",
        "architecture": "clean",
        "capabilities": {
            "direct_execution": True,
            "workflow_execution": True,
            "plan_execution": True,  # NEW: Execute plans from ai-pipeline
            "background_processing": False,  # Handled by Prefect
            "job_queuing": False,  # Handled by Prefect
            "scheduling": False  # Handled by Prefect
        },
        "connection_types": available_connections,
        "active_executions": len(service.active_executions),
        "total_executions": len(service.execution_history)
    }

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🧹 Starting Clean Automation Service")
    print("📋 Responsibilities: Direct command execution only")
    print("🚫 NOT handling: Background jobs, queuing, scheduling (Prefect's job)")
    
    uvicorn.run(
        "main_clean:service.app",
        host="0.0.0.0",
        port=3003,
        reload=False,
        log_level="info"
    )
# --- SELECTOR ENDPOINT HOTFIX ---
from typing import Optional, List
from fastapi import APIRouter, Request, Query

try:
    from selector.dao import select_topk
except Exception as e:
    select_topk = None
    print("[selector] import error:", e)

_selector_router = APIRouter()

@_selector_router.get("/api/selector/search")
async def _selector_search(
    request: Request,
    query: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=20),
    platform: Optional[str] = None,
):
    if select_topk is None:
        return {"error": "selector.dao not available"}
    plats: List[str] = [p.strip() for p in platform.split(",")] if platform else []
    app = request.app
    pool = getattr(getattr(app, "state", app), "db", None) or \
           getattr(getattr(app, "state", app), "db_pool", None) or \
           getattr(app, "db_pool", None)
    if pool is None:
        return {"error": "DB pool not found on app.state"}
    async with pool.acquire() as conn:
        rows = await select_topk(conn, query, plats, k)
    return {"query": query, "k": k, "platform": plats, "results": rows}

def _mount_selector(candidate):
    if candidate is None:
        return False
    app_obj = getattr(candidate, "app", None) if hasattr(candidate, "app") else candidate
    if hasattr(app_obj, "include_router"):
        app_obj.include_router(_selector_router)
        print("[selector] route mounted on", getattr(app_obj, "title", "app"))
        return True
    return False

_mounted = False
for _name in ("service", "app", "application", "api"):
    _mounted |= _mount_selector(globals().get(_name))
if not _mounted:
    print("[selector] WARNING: failed to mount; ensure this block is at file end after app creation")
# --- END SELECTOR ENDPOINT HOTFIX ---


# --- DB POOL STARTUP (idempotent, robust) ---
import os
import asyncio
from typing import Optional

async def _ensure_db_pool(_app) -> None:
    try:
        import asyncpg
    except Exception as e:
        print("[db] asyncpg not available:", e)
        return
    state = getattr(_app, "state", _app)
    if getattr(state, "db_pool", None) or getattr(state, "db", None):
        return  # already present

    # Build DSN
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        pwd  = os.getenv("POSTGRES_PASSWORD", "postgres")
        db   = os.getenv("POSTGRES_DB", "postgres")
        dsn = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

    # Create pool
    try:
        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=int(os.getenv("DB_POOL_MAX", "10")))
        setattr(state, "db_pool", pool)
        print("[db] asyncpg pool established")
    except Exception as e:
        print("[db] failed to create pool:", e)

def _get_app_obj():
    # Prefer service.app; fall back to bare app
    try:
        if "service" in globals() and hasattr(service, "app"):
            return service.app
    except Exception:
        pass
    return globals().get("app")

_app_obj = _get_app_obj()
if _app_obj and hasattr(_app_obj, "add_event_handler"):
    async def _startup():
        await _ensure_db_pool(_app_obj)
    _app_obj.add_event_handler("startup", _startup)
    print("[db] startup hook installed for pool creation")
else:
    print("[db] app not available at import time; no startup hook installed")
# --- END DB POOL STARTUP ---


# --- DB POOL RELIABILITY v3 ---
import os, asyncio, time, random
from typing import Optional

def _get_app_obj():
    try:
        if "service" in globals() and hasattr(service, "app"):
            return service.app
    except Exception:
        pass
    return globals().get("app")

def _build_dsn():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return dsn
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    pwd  = os.getenv("POSTGRES_PASSWORD", "postgres")
    db   = os.getenv("POSTGRES_DB", "postgres")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

async def _create_pool_once(_app):
    try:
        import asyncpg
    except Exception as e:
        print("[db] asyncpg not available:", e)
        return None
    state = getattr(_app, "state", _app)
    dsn = _build_dsn()
    max_size = int(os.getenv("DB_POOL_MAX", "10"))
    try:
        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=max_size)
        setattr(state, "db_pool", pool)
        print("[db] asyncpg pool established")
        return pool
    except Exception as e:
        print("[db] failed to create pool:", e)
        return None

async def _create_pool_with_retry(_app):
    total = int(os.getenv("DB_WAIT_MAX_SECONDS", "60"))
    start = time.time()
    attempt = 0
    while True:
        attempt += 1
        pool = await _create_pool_once(_app)
        if pool:
            return
        elapsed = time.time() - start
        if elapsed >= total:
            print(f"[db] giving up after {attempt} attempts / {int(elapsed)}s")
            return
        # capped backoff (0.5s..2.0s) with jitter
        delay = min(2.0, 0.5 + attempt*0.2) + random.random()*0.2
        await asyncio.sleep(delay)

_app_obj = _get_app_obj()
if _app_obj and hasattr(_app_obj, "add_event_handler"):
    async def _startup():
        await _create_pool_with_retry(_app_obj)
    _app_obj.add_event_handler("startup", _startup)
    print("[db] startup hook installed for pool creation (v3 with retry)")
else:
    print("[db] app not available at import time; no startup hook installed (v3)")

# Middleware safety net: try once on-demand if pool is missing
try:
    state = getattr(_app_obj, "state", _app_obj) if _app_obj else None
    if _app_obj and hasattr(_app_obj, "middleware") and _app_obj not in (None,):
        @_app_obj.middleware("http")
        async def _ensure_pool_mw(request, call_next):
            st = getattr(_app_obj, "state", _app_obj)
            if not getattr(st, "db_pool", None):
                # don’t block requests long; single fast attempt
                await _create_pool_once(_app_obj)
            return await call_next(request)
        print("[db] ensure-pool middleware installed (v3)")
except Exception as e:
    print("[db] failed to install ensure-pool middleware:", e)
# --- END DB POOL RELIABILITY v3 ---

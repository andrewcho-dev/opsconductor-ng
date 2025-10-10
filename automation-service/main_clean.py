#!/usr/bin/env python3
"""
OpsConductor Automation Service - CLEAN ARCHITECTURE
Simple execution API - No Celery, No Background Processing
Handles direct command execution and task management
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

sys.path.append('/app/shared')
from base_service import BaseService

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
        
        logger = logging.getLogger(__name__)
        logger.info("🧹 Clean Automation Service initialized - No Celery, Direct Execution Only")
    
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

class PlanExecutionRequest(BaseModel):
    """Plan execution request from AI pipeline"""
    execution_id: str
    plan: Dict[str, Any]
    tenant_id: str
    actor_id: int

@service.app.post("/execute-plan")
async def execute_plan_from_pipeline(request: PlanExecutionRequest):
    """
    Execute a plan from AI-pipeline
    
    THIS IS THE ONLY CONTAINER THAT EXECUTES COMMANDS
    AI-pipeline orchestrates, automation-service executes
    
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
        
        service.logger.info(f"📝 Executing {len(steps)} steps")
        
        # Execute each step
        for i, step in enumerate(steps):
            # Extract step details - handle both "tool" and "tool_name" keys
            tool_name = step.get("tool", step.get("tool_name", "unknown"))
            service.logger.info(f"⚙️  Step {i+1}/{len(steps)}: {tool_name}")
            
            # Extract parameters - handle both "inputs" and "parameters" keys
            parameters = step.get("inputs", step.get("parameters", {}))
            service.logger.info(f"📦 Parameters: {json.dumps(parameters, indent=2)}")
            
            # Build command based on tool
            command = None
            target_host = None
            connection_type = "local"
            
            if tool_name == "ping":
                # Ping command - check multiple possible parameter names
                host = parameters.get("target_host", parameters.get("host", parameters.get("target", "")))
                count = parameters.get("count", 4)
                if host:
                    command = f"ping -c {count} {host}"
                    service.logger.info(f"🏓 Ping command: {command}")
            
            elif tool_name == "check_connectivity":
                # Check connectivity (ping)
                host = parameters.get("target_host", parameters.get("host", parameters.get("target", "")))
                if host:
                    command = f"ping -c 4 {host}"
                    service.logger.info(f"🔌 Connectivity check: {command}")
            
            elif tool_name == "windows-impacket-executor" or tool_name == "windows-psexec" or tool_name == "PSExec":
                # Impacket WMI execution for GUI applications
                command = parameters.get("command", parameters.get("application", ""))
                target_host = parameters.get("target_host")
                connection_type = "impacket"
                
                # Build environment vars for Impacket options
                env_vars = {}
                if parameters.get("interactive", False):
                    env_vars["interactive"] = "true"
                if parameters.get("session_id"):
                    env_vars["session_id"] = str(parameters.get("session_id"))
                if "wait" in parameters:
                    env_vars["wait"] = "true" if parameters.get("wait") else "false"
                if parameters.get("domain"):
                    env_vars["domain"] = parameters.get("domain")
                
                # Store env vars in request
                if env_vars:
                    parameters["environment_vars"] = env_vars
                
                service.logger.info(f"🖥️  Impacket WMI command: {command} (interactive={env_vars.get('interactive', 'false')}, domain={env_vars.get('domain', '')})")
            
            else:
                # Generic command execution
                command = parameters.get("command", "")
                target_host = parameters.get("target_host")
                connection_type = parameters.get("connection_type", "local")
                
                # Normalize connection type: "winrm" -> "powershell" for backward compatibility
                if connection_type == "winrm":
                    connection_type = "powershell"
                    service.logger.info(f"🔄 Normalized connection_type from 'winrm' to 'powershell'")
            
            if not command:
                service.logger.warning(f"No command found for step {i+1}")
                step_results.append({
                    "step": i+1,
                    "tool": tool_name,
                    "status": "skipped",
                    "message": "No command to execute"
                })
                continue
            
            # Build credentials if username/password provided
            credentials = None
            if parameters.get("username") or parameters.get("password"):
                credentials = {
                    "username": parameters.get("username"),
                    "password": parameters.get("password")
                }
                service.logger.info(f"🔐 Using credentials for user: {parameters.get('username')}")
            
            # Execute command
            cmd_request = CommandRequest(
                command=command,
                target_host=target_host,
                connection_type=connection_type,
                credentials=credentials,
                timeout=parameters.get("timeout", 300),
                environment_vars=parameters.get("environment_vars")
            )
            
            result = await service.execute_command(cmd_request)
            
            step_results.append({
                "step": i+1,
                "tool": tool_name,
                "command": command,
                "status": result.status,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": result.duration_seconds
            })
            
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
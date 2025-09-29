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
    """Simple execution status constants"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    
    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if status indicates execution has finished"""
        return status in [cls.SUCCESS, cls.FAILED]

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
            service_name="automation-service",
            service_port=3003,
            service_description="Clean Automation Service - Direct Command Execution"
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
            
            self.connection_managers = {
                'ssh': LinuxSSHLibrary(),
                'powershell': WindowsPowerShellLibrary() if WindowsPowerShellLibrary else None,
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
            else:
                raise ValueError(f"Unsupported connection type: {request.connection_type}")
            
            # Update result
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            result.status = ExecutionStatus.SUCCESS if exit_code == 0 else ExecutionStatus.FAILED
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
        """Execute command via PowerShell"""
        if 'powershell' not in self.connection_managers or not self.connection_managers['powershell']:
            raise Exception("PowerShell connection manager not available")
        
        # Use PowerShell library to execute command
        ps_manager = self.connection_managers['powershell']
        
        # This would need to be implemented based on your PowerShell library
        # For now, return a placeholder
        return 0, "PowerShell execution not yet implemented", ""

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
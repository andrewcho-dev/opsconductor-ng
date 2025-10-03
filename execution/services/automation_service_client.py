"""
Phase 7: Automation Service Client
HTTP client for interacting with the Automation Service
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================================
# MODELS (matching Automation Service)
# ============================================================================

class CommandRequest(BaseModel):
    """Command execution request"""
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
# AUTOMATION SERVICE CLIENT
# ============================================================================

class AutomationServiceClient:
    """
    HTTP client for Automation Service
    
    Responsibilities:
    - Execute commands on target systems
    - Execute multi-step workflows
    - Handle connection errors with retry logic
    - Map execution steps to automation commands
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 600.0,  # 10 minutes for long-running commands
        max_retries: int = 3
    ):
        """
        Initialize Automation Service Client
        
        Args:
            base_url: Base URL for Automation Service (default: from env)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url or os.getenv(
            "AUTOMATION_SERVICE_URL",
            "http://automation-service:3003"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create HTTP client with retry logic
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True
        )
        
        logger.info(f"AutomationServiceClient initialized: {self.base_url}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def execute_command(
        self,
        command: str,
        target_host: Optional[str] = None,
        connection_type: str = "ssh",
        credentials: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
        working_directory: Optional[str] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute a single command
        
        Args:
            command: Command to execute
            target_host: Target hostname or IP
            connection_type: Connection type (ssh, powershell, local)
            credentials: Authentication credentials
            timeout: Command timeout in seconds
            working_directory: Working directory for command
            environment_vars: Environment variables
        
        Returns:
            ExecutionResult
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        # For Phase 7: Execute locally if connection_type is "local"
        if connection_type == "local" and not target_host:
            return await self._execute_local_command(
                command=command,
                timeout=timeout,
                working_directory=working_directory,
                environment_vars=environment_vars
            )
        
        try:
            logger.info(
                f"Executing command: {command[:50]}... "
                f"on {target_host or 'local'} "
                f"via {connection_type}"
            )
            
            request = CommandRequest(
                command=command,
                target_host=target_host,
                connection_type=connection_type,
                credentials=credentials,
                timeout=timeout,
                working_directory=working_directory,
                environment_vars=environment_vars,
            )
            
            response = await self.client.post(
                "/execute",
                json=request.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            
            result_data = response.json()
            result = ExecutionResult(**result_data)
            
            logger.info(
                f"Command executed: {result.execution_id}, "
                f"status={result.status}, "
                f"exit_code={result.exit_code}, "
                f"duration={result.duration_seconds}s"
            )
            
            return result
        
        except httpx.HTTPError as e:
            logger.error(f"Connection error executing command: {e}")
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error executing command: {e}",
                exc_info=True
            )
            raise
    
    async def _execute_local_command(
        self,
        command: str,
        timeout: int = 300,
        working_directory: Optional[str] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute a command locally using subprocess
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            working_directory: Working directory for command
            environment_vars: Environment variables
        
        Returns:
            ExecutionResult
        """
        import asyncio
        import uuid
        
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        try:
            logger.info(f"Executing local command: {command[:100]}...")
            
            # Prepare environment
            env = os.environ.copy()
            if environment_vars:
                env.update(environment_vars)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")
            
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()
            
            result = ExecutionResult(
                execution_id=execution_id,
                status="completed" if process.returncode == 0 else "failed",
                command=command,
                exit_code=process.returncode,
                stdout=stdout.decode('utf-8', errors='replace') if stdout else "",
                stderr=stderr.decode('utf-8', errors='replace') if stderr else "",
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
                error_message=None if process.returncode == 0 else f"Command failed with exit code {process.returncode}"
            )
            
            logger.info(
                f"Local command completed: exit_code={process.returncode}, "
                f"duration={duration_seconds:.2f}s"
            )
            
            return result
        
        except Exception as e:
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()
            
            logger.error(f"Error executing local command: {e}")
            
            return ExecutionResult(
                execution_id=execution_id,
                status="failed",
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
                error_message=str(e)
            )
    
    async def execute_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: List[CommandRequest],
        continue_on_error: bool = False
    ) -> WorkflowResult:
        """
        Execute a multi-step workflow
        
        Args:
            workflow_id: Workflow identifier
            name: Workflow name
            steps: List of command requests
            continue_on_error: Continue execution if a step fails
        
        Returns:
            WorkflowResult
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        try:
            logger.info(
                f"Executing workflow: {workflow_id}, "
                f"name={name}, "
                f"steps={len(steps)}"
            )
            
            request = WorkflowRequest(
                workflow_id=workflow_id,
                name=name,
                steps=steps,
                continue_on_error=continue_on_error,
            )
            
            response = await self.client.post(
                "/workflow",
                json=request.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            
            result_data = response.json()
            result = WorkflowResult(**result_data)
            
            logger.info(
                f"Workflow executed: {workflow_id}, "
                f"status={result.status}, "
                f"completed={result.steps_completed}/{result.total_steps}, "
                f"duration={result.duration_seconds}s"
            )
            
            return result
        
        except httpx.HTTPError as e:
            logger.error(f"Connection error executing workflow: {e}")
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error executing workflow: {e}",
                exc_info=True
            )
            raise
    
    async def get_active_executions(self) -> List[ExecutionResult]:
        """
        Get currently running executions
        
        Returns:
            List of ExecutionResult
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        try:
            logger.info("Fetching active executions")
            
            response = await self.client.get("/executions/active")
            response.raise_for_status()
            
            data = response.json()
            executions_data = data.get("active_executions", [])
            executions = [
                ExecutionResult(**exec_data)
                for exec_data in executions_data
            ]
            
            logger.info(f"Active executions: {len(executions)}")
            
            return executions
        
        except httpx.HTTPError as e:
            logger.error(f"Connection error fetching active executions: {e}")
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error fetching active executions: {e}",
                exc_info=True
            )
            raise
    
    async def get_execution_history(
        self,
        limit: int = 50
    ) -> List[ExecutionResult]:
        """
        Get execution history
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List of ExecutionResult
        
        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        try:
            logger.info(f"Fetching execution history: limit={limit}")
            
            response = await self.client.get(
                "/executions/history",
                params={"limit": limit}
            )
            response.raise_for_status()
            
            data = response.json()
            executions_data = data.get("executions", [])
            executions = [
                ExecutionResult(**exec_data)
                for exec_data in executions_data
            ]
            
            logger.info(f"Execution history: {len(executions)} results")
            
            return executions
        
        except httpx.HTTPError as e:
            logger.error(f"Connection error fetching execution history: {e}")
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error fetching execution history: {e}",
                exc_info=True
            )
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Automation Service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get("/status")
            return response.status_code == 200
        
        except Exception as e:
            logger.warning(f"Automation Service health check failed: {e}")
            return False
    
    # ========================================================================
    # HELPER METHODS FOR STEP EXECUTION
    # ========================================================================
    
    def build_credentials_dict(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build credentials dictionary for automation service
        
        Args:
            username: Username
            password: Password
            private_key: SSH private key
            api_key: API key
            bearer_token: Bearer token
            **kwargs: Additional credential fields
        
        Returns:
            Credentials dictionary
        """
        credentials = {}
        
        if username:
            credentials["username"] = username
        if password:
            credentials["password"] = password
        if private_key:
            credentials["private_key"] = private_key
        if api_key:
            credentials["api_key"] = api_key
        if bearer_token:
            credentials["bearer_token"] = bearer_token
        
        # Add any additional fields
        credentials.update(kwargs)
        
        return credentials
    
    def determine_connection_type(
        self,
        os_type: str,
        service_type: str
    ) -> str:
        """
        Determine connection type based on OS and service type
        
        Args:
            os_type: Operating system type
            service_type: Service type
        
        Returns:
            Connection type (ssh, powershell, local)
        """
        os_type_lower = os_type.lower()
        service_type_lower = service_type.lower()
        
        # Windows systems
        if "windows" in os_type_lower:
            if "ssh" in service_type_lower:
                return "ssh"
            return "powershell"
        
        # Linux/Unix systems
        if any(os in os_type_lower for os in ["linux", "unix", "ubuntu", "centos", "rhel", "debian"]):
            return "ssh"
        
        # Default to SSH
        return "ssh"
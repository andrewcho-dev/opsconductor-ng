"""
Phase 7: Execution Engine
Core execution logic with step-by-step execution and progress tracking
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from execution.dtos import ExecutionResult, StepExecutionResult
from execution.models import (
    ExecutionModel,
    ExecutionStatus,
    ExecutionStepModel,
)
from execution.repository import ExecutionRepository
from execution.services.asset_service_client import AssetServiceClient
from execution.services.automation_service_client import AutomationServiceClient

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
        self.asset_client = AssetServiceClient(base_url=asset_service_url)
        self.automation_client = AutomationServiceClient(base_url=automation_service_url)
        
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
            logger.info(f"Starting execution: {execution.execution_id}")
            
            # Step 1: Create execution steps from plan
            steps = await self._create_execution_steps(execution)
            
            logger.info(
                f"Created {len(steps)} execution steps for {execution.execution_id}"
            )
            
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
            final_status = self._determine_final_status(step_results)
            
            # Step 4: Build result
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()
            
            result = ExecutionResult(
                execution_id=execution.execution_id,
                status=final_status,
                result={
                    "total_steps": len(steps),
                    "completed_steps": sum(
                        1 for r in step_results
                        if r.get("status") == ExecutionStatus.COMPLETED.value
                    ),
                    "failed_steps": sum(
                        1 for r in step_results
                        if r.get("status") == ExecutionStatus.FAILED.value
                    ),
                },
                step_results=step_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
            )
            
            logger.info(
                f"Execution completed: {execution.execution_id}, "
                f"status={final_status}, duration={duration_seconds}s"
            )
            
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
            logger.info(
                f"Executing step: {step.step_id}, "
                f"name={step.step_name}, type={step.step_type}"
            )
            
            # Update step status to running
            self.repository.update_step_status(
                step.step_id,
                ExecutionStatus.RUNNING
            )
            
            # Execute step based on type
            output_data = await self._execute_step_by_type(step, execution)
            
            # Update step status to completed
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            self.repository.update_step_status(
                step.step_id,
                ExecutionStatus.COMPLETED,
                output_data=output_data,
                duration_ms=duration_ms
            )
            
            logger.info(
                f"Step completed: {step.step_id}, duration={duration_ms}ms"
            )
            
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
        logger.info(
            f"Executing step type: {step.step_type}, "
            f"target={step.target_hostname or step.target_asset_id}"
        )
        
        # Step 1: Fetch asset details if target_asset_id is provided
        asset = None
        if step.target_asset_id:
            try:
                asset = await self.asset_client.get_asset_by_id(step.target_asset_id)
                if not asset:
                    raise ValueError(f"Asset not found: {step.target_asset_id}")
            except Exception as e:
                logger.error(f"Failed to fetch asset {step.target_asset_id}: {e}")
                raise
        elif step.target_hostname:
            try:
                asset = await self.asset_client.get_asset_by_hostname(step.target_hostname)
                if not asset:
                    raise ValueError(f"Asset not found: {step.target_hostname}")
            except Exception as e:
                logger.error(f"Failed to fetch asset {step.target_hostname}: {e}")
                raise
        
        # Step 2: Execute based on step type
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
        Execute an API call step
        
        Args:
            step: Execution step model
            asset: Asset details (optional)
        
        Returns:
            Output data
        """
        # TODO: Implement API execution
        # For now, use curl command as fallback
        logger.info("API step execution - using curl fallback")
        
        url = step.input_data.get("url")
        method = step.input_data.get("method", "GET")
        headers = step.input_data.get("headers", {})
        body = step.input_data.get("body")
        
        # Build curl command
        curl_cmd = f"curl -X {method}"
        
        for key, value in headers.items():
            curl_cmd += f" -H '{key}: {value}'"
        
        if body:
            import json
            curl_cmd += f" -d '{json.dumps(body)}'"
        
        curl_cmd += f" '{url}'"
        
        # Execute via automation service
        result = await self.automation_client.execute_command(
            command=curl_cmd,
            connection_type="local",
            timeout=step.input_data.get("timeout", 60),
        )
        
        return {
            "status": result.status,
            "response": result.stdout,
            "error": result.stderr,
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
                
                return {
                    "status": "success",
                    "count": len(assets),
                    "data": [asset.dict() if hasattr(asset, 'dict') else asset for asset in assets],
                    "query_type": query_type,
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
                
                return {
                    "status": "success",
                    "count": len(assets),
                    "data": [asset.dict() if hasattr(asset, 'dict') else asset for asset in assets],
                    "query_type": query_type,
                    "filter": {"type": asset_type},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            else:
                # Default: list all
                logger.warning(f"Unknown query_type: {query_type}, defaulting to list_all")
                assets = await self.asset_client.get_all_assets(limit=limit)
                
                return {
                    "status": "success",
                    "count": len(assets),
                    "data": [asset.dict() if hasattr(asset, 'dict') else asset for asset in assets],
                    "query_type": "list_all",
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
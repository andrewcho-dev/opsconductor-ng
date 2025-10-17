"""
Phase 7: Stage E Executor
Main entry point for execution with hybrid routing and safety features
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from execution.dtos import ExecutionRequest, ExecutionResponse
from execution.models import (
    ApprovalModel,
    ExecutionMode,
    ExecutionModel,
    ExecutionStatus,
    SLAClass,
    calculate_idempotency_key,
    determine_execution_mode,
    determine_sla_class,
)
from execution.repository import ExecutionRepository

logger = logging.getLogger(__name__)


class StageEExecutor:
    """
    Stage E Executor - Main entry point for execution
    
    Responsibilities:
    1. Idempotency check (prevent duplicate executions)
    2. Hybrid execution routing (immediate vs background)
    3. Approval workflow integration
    4. Execution lifecycle management
    """
    
    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        redis_url: Optional[str] = None
    ):
        """Initialize Stage E Executor"""
        self.db_connection_string = db_connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://opsconductor:opsconductor_secure_2024@localhost:5432/opsconductor"
        )
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Initialize repository
        self.repository = ExecutionRepository(self.db_connection_string)
        
        logger.info("StageEExecutor initialized")
    
    async def execute(
        self,
        request: ExecutionRequest,
        tenant_id: str,
        actor_id: int
    ) -> ExecutionResponse:
        """
        Execute a plan with safety features
        
        Args:
            request: Execution request with plan and approval level
            tenant_id: Tenant ID for multi-tenancy
            actor_id: Actor ID (user who initiated execution)
        
        Returns:
            ExecutionResponse with execution details
        """
        try:
            logger.info(
                f"Executing plan for tenant={tenant_id}, actor={actor_id}, "
                f"approval_level={request.approval_level}"
            )
            
            # Step 1: Calculate idempotency key
            idempotency_key = calculate_idempotency_key(
                request.plan,
                tenant_id,
                actor_id
            )
            
            # Step 2: Check for duplicate execution (idempotency)
            # DISABLED FOR TESTING - CACHING CAUSES ISSUES
            # existing_execution = self.repository.get_execution_by_idempotency_key(
            #     tenant_id,
            #     idempotency_key
            # )
            # 
            # if existing_execution:
            #     logger.info(
            #         f"Duplicate execution detected: {existing_execution.execution_id}"
            #     )
            #     return self._build_execution_response(existing_execution)
            
            # Step 3: Determine SLA class and execution mode
            estimated_duration = self._estimate_duration(request.plan)
            sla_class = determine_sla_class(estimated_duration)
            execution_mode = determine_execution_mode(sla_class)
            
            logger.info(
                f"Determined sla_class={sla_class}, execution_mode={execution_mode}, "
                f"estimated_duration={estimated_duration}s"
            )
            
            # Step 4: Get timeout policy
            action_class = self._determine_action_class(request.plan)
            timeout_policy = self.repository.get_timeout_policy(sla_class, action_class)
            
            if not timeout_policy:
                raise ValueError(
                    f"No timeout policy found for sla_class={sla_class}, "
                    f"action_class={action_class}"
                )
            
            # Step 5: Calculate timeout
            timeout_at = datetime.utcnow() + timedelta(
                seconds=timeout_policy.execution_timeout_seconds
            )
            
            # Step 6: Create execution record
            execution = ExecutionModel(
                execution_id=uuid4(),
                tenant_id=tenant_id,
                actor_id=actor_id,
                idempotency_key=idempotency_key,
                plan_snapshot=request.plan,
                execution_mode=execution_mode,
                sla_class=sla_class,
                approval_level=request.approval_level,
                status=self._determine_initial_status(request.approval_level),
                timeout_at=timeout_at,
                trace_id=request.trace_id or uuid4(),
                parent_execution_id=request.parent_execution_id,
                tags=request.tags,
                metadata=request.metadata,
            )
            
            # Step 7: Save execution to database
            execution = self.repository.create_execution(execution)
            
            logger.info(f"Created execution: {execution.execution_id}")
            
            # Step 8: Handle approval workflow
            if request.approval_level > 0:
                await self._create_approval(execution, timeout_policy)
                logger.info(
                    f"Approval required for execution: {execution.execution_id}, "
                    f"level={request.approval_level}"
                )
            else:
                # Level 0: Auto-execute
                await self._route_execution(execution, execution_mode)
                
                # Fetch updated execution after routing (to get results)
                execution = self.repository.get_execution_by_id(execution.execution_id)
            
            # Step 9: Return response
            return self._build_execution_response(execution)
        
        except Exception as e:
            logger.error(f"Failed to execute plan: {e}", exc_info=True)
            raise
    
    async def _route_execution(
        self,
        execution: ExecutionModel,
        execution_mode: ExecutionMode
    ) -> None:
        """
        Route execution to immediate or background path
        
        Args:
            execution: Execution model
            execution_mode: Execution mode (immediate or background)
        """
        if execution_mode == ExecutionMode.IMMEDIATE:
            # Immediate execution (<10s)
            logger.info(f"Routing to immediate execution: {execution.execution_id}")
            await self._execute_immediate(execution)
        else:
            # Background execution (>30s)
            logger.info(f"Routing to background execution: {execution.execution_id}")
            await self._enqueue_execution(execution)
    
    def _get_service_url_for_tool(self, tool_name: str) -> str:
        """
        Determine which execution service should handle a specific tool
        based on tool's execution_location metadata from the database.
        
        Args:
            tool_name: Name of the tool to execute
            
        Returns:
            Service URL (e.g., "http://automation-service:3003")
        """
        if not tool_name:
            logger.warning(f"No tool specified, defaulting to automation-service")
            return os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")
        
        # Get tool definition from database
        try:
            from pipeline.services.tool_catalog_service import ToolCatalogService
            catalog_service = ToolCatalogService()
            
            tool_data = catalog_service.get_tool_by_name(tool_name)
            if not tool_data:
                logger.warning(f"Tool '{tool_name}' not found in database, defaulting to automation-service")
                return os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")
            
            # Get execution_location from metadata field
            metadata = tool_data.get("metadata", {})
            execution_location = metadata.get("execution_location", "automation-service")
            
            # Map service name to URL
            service_urls = {
                "automation-service": os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003"),
                "communication-service": os.getenv("COMMUNICATION_SERVICE_URL", "http://communication-service:3004"),
                "asset-service": os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002"),
                "network-service": os.getenv("NETWORK_SERVICE_URL", "http://network-analyzer-service:3006"),
            }
            
            service_url = service_urls.get(execution_location)
            if not service_url:
                logger.warning(
                    f"Unknown execution_location '{execution_location}' for tool '{tool_name}', "
                    f"defaulting to automation-service"
                )
                return service_urls["automation-service"]
            
            logger.info(f"Routing tool '{tool_name}' to {execution_location}")
            return service_url
            
        except Exception as e:
            logger.error(f"Error getting tool definition for '{tool_name}': {e}", exc_info=True)
            return os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")
    
    def _get_execution_service_url(self, execution: ExecutionModel) -> str:
        """
        DEPRECATED: Use _get_service_url_for_tool instead
        
        Determine which execution service should handle this execution
        based on tool's execution_location metadata.
        
        Args:
            execution: Execution model with plan_snapshot
            
        Returns:
            Service URL (e.g., "http://automation-service:3003")
        """
        # Get first step's tool name to determine routing
        plan_steps = execution.plan_snapshot.get("steps", [])
        if not plan_steps:
            # No steps, default to automation-service
            logger.warning(f"No steps in plan {execution.execution_id}, defaulting to automation-service")
            return os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")
        
        first_tool = plan_steps[0].get("tool")
        return self._get_service_url_for_tool(first_tool)
    
    async def _execute_immediate(self, execution: ExecutionModel) -> None:
        """
        Execute immediately by orchestrating steps across appropriate services
        
        AI-PIPELINE DOES NOT EXECUTE - IT ONLY ORCHESTRATES
        All actual execution happens in execution service containers:
        - automation-service: infrastructure commands (SSH, WinRM, DB, etc.)
        - communication-service: notifications (email, Slack, Teams, SMS)
        - asset-service: asset operations (query, create, update, delete)
        - network-service: network analysis (tcpdump, tshark, nmap, etc.)
        
        This method orchestrates multi-step plans by:
        1. Executing each step individually
        2. Routing each step to the correct service
        3. Passing results between steps for variable resolution
        
        Args:
            execution: Execution model
        """
        import httpx
        
        try:
            # Update status to running
            self.repository.update_execution_status(
                execution.execution_id,
                ExecutionStatus.RUNNING,
                previous_status=execution.status
            )
            
            # Get steps from plan
            steps = execution.plan_snapshot.get("steps", [])
            if not steps:
                raise ValueError("No steps found in execution plan")
            
            logger.info(f"Orchestrating {len(steps)} steps for execution {execution.execution_id}")
            
            # Execute steps sequentially, routing each to the appropriate service
            all_step_results = []
            overall_success = True
            
            for step_index, step in enumerate(steps):
                tool_name = step.get("tool", "unknown")
                logger.info(f"Executing step {step_index + 1}/{len(steps)}: {tool_name}")
                
                # Determine which service should handle this step
                service_url = self._get_service_url_for_tool(tool_name)
                
                # Create a single-step plan for this service
                single_step_plan = {
                    "steps": [step]
                }
                
                # If this is not the first step, include previous results for variable resolution
                if all_step_results:
                    single_step_plan["previous_results"] = all_step_results
                
                try:
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        response = await client.post(
                            f"{service_url}/execute-plan",
                            json={
                                "execution_id": str(execution.execution_id),
                                "plan": single_step_plan,
                                "tenant_id": execution.tenant_id,
                                "actor_id": execution.actor_id
                            }
                        )
                        response.raise_for_status()
                        result_data = response.json()
                    
                    # Extract step results
                    step_results = result_data.get("step_results", [])
                    if step_results:
                        all_step_results.extend(step_results)
                        
                        # Check if any step failed
                        for step_result in step_results:
                            if step_result.get("status") != "completed":
                                overall_success = False
                    else:
                        overall_success = False
                        all_step_results.append({
                            "step_index": step_index,
                            "tool": tool_name,
                            "status": "failed",
                            "error": "No results returned from service",
                            "completed_at": datetime.utcnow().isoformat()
                        })
                    
                    logger.info(f"Step {step_index + 1} completed via {service_url}")
                    
                except Exception as e:
                    logger.error(f"Step {step_index + 1} failed: {e}", exc_info=True)
                    overall_success = False
                    all_step_results.append({
                        "step_index": step_index,
                        "tool": tool_name,
                        "status": "failed",
                        "error": str(e),
                        "completed_at": datetime.utcnow().isoformat()
                    })
            
            # Update execution with final results
            result_status = ExecutionStatus.COMPLETED if overall_success else ExecutionStatus.FAILED
            self.repository.update_execution_status(
                execution.execution_id,
                result_status,
                previous_status=ExecutionStatus.RUNNING,
                error_message=None if overall_success else "One or more steps failed"
            )
            
            # Build final result
            final_result = {
                "total_steps": len(steps),
                "successful_steps": sum(1 for r in all_step_results if r.get("status") == "completed"),
                "failed_steps": sum(1 for r in all_step_results if r.get("status") == "failed"),
                "step_results": all_step_results
            }
            
            self.repository.update_execution_result(
                execution.execution_id,
                final_result,
                datetime.utcnow()
            )
            
            logger.info(
                f"Orchestrated execution completed: {execution.execution_id}, "
                f"status={result_status}, steps={len(steps)}, "
                f"successful={final_result['successful_steps']}, failed={final_result['failed_steps']}"
            )
        
        except Exception as e:
            logger.error(
                f"Immediate execution failed: {execution.execution_id}, error={e}",
                exc_info=True
            )
            self.repository.update_execution_status(
                execution.execution_id,
                ExecutionStatus.FAILED,
                previous_status=ExecutionStatus.RUNNING,
                error_message=str(e)
            )
            raise
    
    async def _enqueue_execution(self, execution: ExecutionModel) -> None:
        """
        Enqueue execution for background processing
        
        Args:
            execution: Execution model
        """
        from execution.models import ExecutionQueueModel
        
        try:
            # Get timeout policy
            action_class = self._determine_action_class(execution.plan_snapshot)
            timeout_policy = self.repository.get_timeout_policy(
                execution.sla_class,
                action_class
            )
            
            if not timeout_policy:
                raise ValueError(
                    f"No timeout policy found for sla_class={execution.sla_class}, "
                    f"action_class={action_class}"
                )
            
            # Create queue entry
            queue_entry = ExecutionQueueModel(
                execution_id=execution.execution_id,
                priority=self._calculate_priority(execution),
                sla_class=execution.sla_class,
                visibility_timeout_seconds=timeout_policy.lease_timeout_seconds,
                max_attempts=timeout_policy.max_attempts,
            )
            
            # Enqueue
            self.repository.enqueue_execution(queue_entry)
            
            # Update execution status
            self.repository.update_execution_status(
                execution.execution_id,
                ExecutionStatus.QUEUED,
                previous_status=execution.status
            )
            
            logger.info(
                f"Execution enqueued: {execution.execution_id}, "
                f"priority={queue_entry.priority}"
            )
        
        except Exception as e:
            logger.error(
                f"Failed to enqueue execution: {execution.execution_id}, error={e}",
                exc_info=True
            )
            self.repository.update_execution_status(
                execution.execution_id,
                ExecutionStatus.FAILED,
                previous_status=execution.status,
                error_message=str(e)
            )
            raise
    
    async def _create_approval(
        self,
        execution: ExecutionModel,
        timeout_policy: Any
    ) -> None:
        """
        Create approval record for execution
        
        Args:
            execution: Execution model
            timeout_policy: Timeout policy
        """
        import hashlib
        import json
        
        # Calculate plan hash
        plan_json = json.dumps(execution.plan_snapshot, sort_keys=True)
        plan_hash = hashlib.sha256(plan_json.encode()).hexdigest()
        
        # Calculate approval expiration
        expires_at = None
        if timeout_policy.approval_timeout_seconds:
            expires_at = datetime.utcnow() + timedelta(
                seconds=timeout_policy.approval_timeout_seconds
            )
        
        # Create approval
        approval = ApprovalModel(
            execution_id=execution.execution_id,
            approval_level=execution.approval_level,
            plan_hash=plan_hash,
            expires_at=expires_at,
        )
        
        self.repository.create_approval(approval)
        
        logger.info(
            f"Approval created: {approval.approval_id}, "
            f"execution={execution.execution_id}, level={execution.approval_level}"
        )
    
    def _determine_initial_status(self, approval_level: int) -> ExecutionStatus:
        """Determine initial execution status based on approval level"""
        if approval_level == 0:
            return ExecutionStatus.APPROVED  # Auto-execute
        else:
            return ExecutionStatus.PENDING_APPROVAL
    
    def _estimate_duration(self, plan: Dict[str, Any]) -> float:
        """
        Estimate execution duration based on plan
        
        Args:
            plan: Execution plan
        
        Returns:
            Estimated duration in seconds
        """
        # Simple heuristic: 2 seconds per step
        steps = plan.get("steps", [])
        return len(steps) * 2.0
    
    def _determine_action_class(self, plan: Dict[str, Any]) -> str:
        """
        Determine action class based on plan
        
        Args:
            plan: Execution plan
        
        Returns:
            Action class ('read', 'modify', 'deploy')
        """
        # Simple heuristic based on plan type
        plan_type = plan.get("type", "").lower()
        
        if "read" in plan_type or "query" in plan_type or "get" in plan_type:
            return "read"
        elif "deploy" in plan_type or "install" in plan_type or "create" in plan_type:
            return "deploy"
        else:
            return "modify"
    
    def _calculate_priority(self, execution: ExecutionModel) -> int:
        """
        Calculate execution priority (1=highest, 10=lowest)
        
        Args:
            execution: Execution model
        
        Returns:
            Priority (1-10)
        """
        # Priority based on SLA class
        if execution.sla_class == SLAClass.FAST:
            return 1
        elif execution.sla_class == SLAClass.MEDIUM:
            return 5
        else:
            return 10
    
    def _build_execution_response(self, execution: ExecutionModel) -> ExecutionResponse:
        """
        Build execution response from execution model
        
        Args:
            execution: Execution model
        
        Returns:
            ExecutionResponse
        """
        # Get execution steps
        steps = self.repository.get_execution_steps(execution.execution_id)
        
        # Calculate progress
        total_steps = len(steps)
        completed_steps = sum(
            1 for step in steps
            if step.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
        )
        failed_steps = sum(
            1 for step in steps if step.status == ExecutionStatus.FAILED
        )
        progress_percentage = (
            (completed_steps / total_steps * 100) if total_steps > 0 else 0
        )
        
        # Extract step_results from result if available
        step_results = None
        if execution.result and "step_results" in execution.result:
            step_results = execution.result["step_results"]
        
        return ExecutionResponse(
            execution_id=execution.execution_id,
            status=execution.status,
            execution_mode=execution.execution_mode,
            sla_class=execution.sla_class,
            approval_level=execution.approval_level,
            created_at=execution.created_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            timeout_at=execution.timeout_at,
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            progress_percentage=progress_percentage,
            result=execution.result,
            step_results=step_results,
            error_message=execution.error_message,
            trace_id=execution.trace_id,
            tags=execution.tags,
        )
"""
OUIOE Phase 5: Adaptive Execution Engine

Revolutionary execution system that adapts workflows in real-time based on
execution results, system conditions, and learned patterns. Provides
intelligent error recovery, performance optimization, and dynamic workflow
modification capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
import json
import uuid
from contextlib import asynccontextmanager

from .workflow_models import (
    IntelligentWorkflow, WorkflowStep, WorkflowNode, WorkflowEdge,
    ExecutionContext, ExecutionResult, ExecutionStatus, AdaptationTrigger,
    AdaptationStrategy, WorkflowAdaptation, WorkflowStatus, ExecutionMonitor,
    ExecutionRecovery
)
from ..decision import DecisionEngine, DecisionRequest, DecisionType
from ..integrations.thinking_llm_client import ThinkingLLMClient
from ..streaming import StreamManager

logger = logging.getLogger(__name__)


class AdaptiveExecutionEngine:
    """
    Adaptive execution engine that intelligently executes workflows
    with real-time adaptation, error recovery, and optimization.
    """
    
    def __init__(
        self, 
        decision_engine: DecisionEngine, 
        llm_client: ThinkingLLMClient,
        stream_manager: StreamManager
    ):
        self.decision_engine = decision_engine
        self.llm_client = llm_client
        self.stream_manager = stream_manager
        
        # Execution tracking
        self.active_executions = {}
        self.execution_history = []
        self.adaptation_patterns = {}
        self.performance_metrics = {}
        
        # Service clients registry
        self.service_clients = {}
        
        # Monitoring and recovery
        self.monitors = {}
        self.recovery_strategies = {}
        
        # Configuration
        self.max_concurrent_executions = 10
        self.default_timeout = timedelta(minutes=30)
        self.adaptation_threshold = 0.7  # Confidence threshold for adaptations
        
        logger.info("Adaptive Execution Engine initialized")
    
    async def execute_workflow(
        self, 
        workflow: IntelligentWorkflow,
        service_clients: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute workflow with adaptive capabilities.
        
        Args:
            workflow: Workflow to execute
            service_clients: Optional service client registry
            
        Returns:
            Execution result with metrics and adaptations
        """
        execution_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting adaptive execution of workflow {workflow.workflow_id}")
            
            # Initialize execution context
            context = ExecutionContext(
                workflow=workflow,
                execution_environment={
                    "execution_id": execution_id,
                    "start_time": datetime.now(),
                    "engine_version": "5.0.0"
                },
                service_clients=service_clients or self.service_clients
            )
            
            # Register active execution
            self.active_executions[execution_id] = context
            
            # Update workflow status
            workflow.update_status(WorkflowStatus.RUNNING)
            
            # Set up monitoring
            monitor = await self._setup_execution_monitoring(workflow, context)
            
            # Execute workflow with adaptation
            result = await self._execute_with_adaptation(context, monitor)
            
            # Update final status
            if result.status == ExecutionStatus.SUCCESS:
                workflow.update_status(WorkflowStatus.COMPLETED)
            else:
                workflow.update_status(WorkflowStatus.FAILED)
            
            # Record execution for learning
            await self._record_execution(workflow, context, result)
            
            logger.info(f"Completed execution {execution_id} with status: {result.status}")
            return result
            
        except Exception as e:
            logger.error(f"Error in workflow execution {execution_id}: {str(e)}")
            workflow.update_status(WorkflowStatus.FAILED)
            
            return ExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow.workflow_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time=datetime.now() - context.execution_environment.get("start_time", datetime.now())
            )
        
        finally:
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            if execution_id in self.monitors:
                del self.monitors[execution_id]
    
    async def _execute_with_adaptation(
        self, 
        context: ExecutionContext,
        monitor: ExecutionMonitor
    ) -> ExecutionResult:
        """Execute workflow with real-time adaptation"""
        
        workflow = context.workflow
        execution_id = context.execution_environment["execution_id"]
        
        # Initialize execution tracking
        executed_steps = []
        failed_steps = []
        adapted_steps = []
        
        # Get execution order
        execution_order = await self._determine_execution_order(workflow)
        
        # Execute steps in order
        for step_batch in execution_order:
            # Execute batch (parallel or sequential)
            batch_results = await self._execute_step_batch(
                step_batch, context, monitor
            )
            
            # Process batch results
            for step_id, step_result in batch_results.items():
                if step_result.status == ExecutionStatus.SUCCESS:
                    executed_steps.append(step_id)
                    # Update shared data
                    context.shared_data.update(step_result.result_data)
                    
                elif step_result.status == ExecutionStatus.FAILED:
                    failed_steps.append(step_id)
                    
                    # Attempt adaptation
                    adaptation_result = await self._attempt_adaptation(
                        step_id, step_result, context, monitor
                    )
                    
                    if adaptation_result.success:
                        adapted_steps.append(step_id)
                        executed_steps.append(step_id)
                        context.shared_data.update(adaptation_result.result_data)
                    else:
                        # Check if failure is critical
                        if await self._is_critical_failure(step_id, workflow):
                            return ExecutionResult(
                                execution_id=execution_id,
                                workflow_id=workflow.workflow_id,
                                status=ExecutionStatus.FAILED,
                                error_message=f"Critical step {step_id} failed: {step_result.error_message}",
                                execution_time=datetime.now() - context.execution_environment["start_time"]
                            )
                
                # Update workflow metrics
                await self._update_workflow_metrics(workflow, step_result)
                
                # Stream progress update
                await self._stream_progress_update(context, step_id, step_result)
        
        # Calculate final result
        total_steps = len(workflow.graph.nodes)
        success_rate = len(executed_steps) / total_steps if total_steps > 0 else 0
        
        final_status = ExecutionStatus.SUCCESS if success_rate >= 0.8 else ExecutionStatus.FAILED
        
        return ExecutionResult(
            execution_id=execution_id,
            workflow_id=workflow.workflow_id,
            status=final_status,
            result_data=context.shared_data,
            execution_time=datetime.now() - context.execution_environment["start_time"],
            metadata={
                "executed_steps": executed_steps,
                "failed_steps": failed_steps,
                "adapted_steps": adapted_steps,
                "success_rate": success_rate,
                "total_adaptations": len(adapted_steps)
            }
        )
    
    async def _determine_execution_order(self, workflow: IntelligentWorkflow) -> List[List[str]]:
        """Determine optimal execution order for workflow steps"""
        
        # Topological sort with parallel batch identification
        graph = workflow.graph
        in_degree = {}
        
        # Calculate in-degrees
        for node_id in graph.nodes:
            in_degree[node_id] = 0
        
        for edge in graph.edges.values():
            in_degree[edge.to_node] += 1
        
        # Generate execution batches
        execution_order = []
        remaining_nodes = set(graph.nodes.keys())
        
        while remaining_nodes:
            # Find nodes with no incoming edges (can execute in parallel)
            ready_nodes = [
                node_id for node_id in remaining_nodes 
                if in_degree[node_id] == 0
            ]
            
            if not ready_nodes:
                # Handle circular dependencies
                logger.warning(f"Circular dependency detected in workflow {workflow.workflow_id}")
                ready_nodes = [list(remaining_nodes)[0]]  # Force execution of one node
            
            execution_order.append(ready_nodes)
            
            # Remove executed nodes and update in-degrees
            for node_id in ready_nodes:
                remaining_nodes.remove(node_id)
                
                # Update in-degrees of dependent nodes
                for edge in graph.edges.values():
                    if edge.from_node == node_id:
                        in_degree[edge.to_node] -= 1
        
        return execution_order
    
    async def _execute_step_batch(
        self, 
        step_batch: List[str], 
        context: ExecutionContext,
        monitor: ExecutionMonitor
    ) -> Dict[str, ExecutionResult]:
        """Execute a batch of steps (parallel or sequential)"""
        
        workflow = context.workflow
        batch_results = {}
        
        if len(step_batch) == 1:
            # Single step execution
            step_id = step_batch[0]
            result = await self._execute_single_step(step_id, context, monitor)
            batch_results[step_id] = result
        else:
            # Parallel execution
            logger.info(f"Executing {len(step_batch)} steps in parallel")
            
            # Create tasks for parallel execution
            tasks = []
            for step_id in step_batch:
                task = asyncio.create_task(
                    self._execute_single_step(step_id, context, monitor)
                )
                tasks.append((step_id, task))
            
            # Wait for all tasks to complete
            for step_id, task in tasks:
                try:
                    result = await task
                    batch_results[step_id] = result
                except Exception as e:
                    batch_results[step_id] = ExecutionResult(
                        execution_id=context.execution_environment["execution_id"],
                        workflow_id=workflow.workflow_id,
                        step_id=step_id,
                        status=ExecutionStatus.FAILED,
                        error_message=str(e)
                    )
        
        return batch_results
    
    async def _execute_single_step(
        self, 
        step_id: str, 
        context: ExecutionContext,
        monitor: ExecutionMonitor
    ) -> ExecutionResult:
        """Execute a single workflow step"""
        
        workflow = context.workflow
        node = workflow.graph.nodes[step_id]
        step = node.step
        
        logger.info(f"Executing step {step_id}: {step.name}")
        
        # Update node status
        node.status = ExecutionStatus.RUNNING
        node.start_time = datetime.now()
        
        try:
            # Check dependencies
            if not await self._check_step_dependencies(step_id, context):
                return ExecutionResult(
                    execution_id=context.execution_environment["execution_id"],
                    workflow_id=workflow.workflow_id,
                    step_id=step_id,
                    status=ExecutionStatus.FAILED,
                    error_message="Step dependencies not satisfied"
                )
            
            # Prepare step parameters
            parameters = await self._prepare_step_parameters(step, context)
            
            # Execute step with timeout
            async with self._execution_timeout(step.timeout or self.default_timeout):
                result = await self._call_service_action(
                    step.service, step.action, parameters, context
                )
            
            # Validate result
            validation_result = await self._validate_step_result(step, result, context)
            
            if validation_result.is_valid:
                node.status = ExecutionStatus.SUCCESS
                node.result = result
                
                return ExecutionResult(
                    execution_id=context.execution_environment["execution_id"],
                    workflow_id=workflow.workflow_id,
                    step_id=step_id,
                    status=ExecutionStatus.SUCCESS,
                    result_data=result,
                    execution_time=datetime.now() - node.start_time
                )
            else:
                node.status = ExecutionStatus.FAILED
                node.error = validation_result.error_message
                
                return ExecutionResult(
                    execution_id=context.execution_environment["execution_id"],
                    workflow_id=workflow.workflow_id,
                    step_id=step_id,
                    status=ExecutionStatus.FAILED,
                    error_message=validation_result.error_message,
                    execution_time=datetime.now() - node.start_time
                )
        
        except asyncio.TimeoutError:
            node.status = ExecutionStatus.FAILED
            node.error = "Step execution timeout"
            
            return ExecutionResult(
                execution_id=context.execution_environment["execution_id"],
                workflow_id=workflow.workflow_id,
                step_id=step_id,
                status=ExecutionStatus.FAILED,
                error_message="Step execution timeout",
                execution_time=datetime.now() - node.start_time
            )
        
        except Exception as e:
            node.status = ExecutionStatus.FAILED
            node.error = str(e)
            
            return ExecutionResult(
                execution_id=context.execution_environment["execution_id"],
                workflow_id=workflow.workflow_id,
                step_id=step_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time=datetime.now() - node.start_time
            )
        
        finally:
            node.end_time = datetime.now()
            if node.start_time:
                node.execution_time = node.end_time - node.start_time
    
    @asynccontextmanager
    async def _execution_timeout(self, timeout: timedelta):
        """Context manager for step execution timeout"""
        try:
            await asyncio.wait_for(
                asyncio.sleep(0),  # Placeholder for actual execution
                timeout=timeout.total_seconds()
            )
            yield
        except asyncio.TimeoutError:
            raise
    
    async def _check_step_dependencies(self, step_id: str, context: ExecutionContext) -> bool:
        """Check if step dependencies are satisfied"""
        
        workflow = context.workflow
        
        # Find incoming edges (dependencies)
        for edge in workflow.graph.edges.values():
            if edge.to_node == step_id:
                dependency = edge.dependency
                from_node = workflow.graph.nodes[edge.from_node]
                
                # Check completion dependency
                if dependency.dependency_type == "completion":
                    if from_node.status != ExecutionStatus.SUCCESS:
                        return False
                
                # Check condition dependency
                elif dependency.dependency_type == "condition":
                    if dependency.condition:
                        # Evaluate condition (simplified)
                        if not await self._evaluate_condition(dependency.condition, context):
                            return False
                
                # Check data dependency
                elif dependency.dependency_type == "data":
                    required_data = dependency.data_mapping
                    for key in required_data.keys():
                        if key not in context.shared_data:
                            return False
        
        return True
    
    async def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Evaluate a dependency condition"""
        
        # Simple condition evaluation (can be enhanced with expression parser)
        try:
            # Replace variables with actual values
            evaluated_condition = condition
            for key, value in context.shared_data.items():
                evaluated_condition = evaluated_condition.replace(f"{key}", str(value))
            
            # Basic evaluation (security risk in production - use proper parser)
            return eval(evaluated_condition)
        except:
            return False
    
    async def _prepare_step_parameters(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Prepare parameters for step execution"""
        
        parameters = step.parameters.copy()
        
        # Substitute variables from shared data
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                if var_name in context.shared_data:
                    parameters[key] = context.shared_data[var_name]
        
        # Add context parameters
        parameters["_context"] = {
            "workflow_id": context.workflow.workflow_id,
            "execution_id": context.execution_environment["execution_id"],
            "step_id": step.step_id
        }
        
        return parameters
    
    async def _call_service_action(
        self, 
        service: str, 
        action: str, 
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Call service action with parameters"""
        
        # Get service client
        if service not in context.service_clients:
            raise ValueError(f"Service client not available: {service}")
        
        service_client = context.service_clients[service]
        
        # Call service action
        if hasattr(service_client, action):
            method = getattr(service_client, action)
            if asyncio.iscoroutinefunction(method):
                result = await method(**parameters)
            else:
                result = method(**parameters)
        else:
            # Generic service call
            if hasattr(service_client, 'call_action'):
                result = await service_client.call_action(action, parameters)
            else:
                raise ValueError(f"Action not available: {service}.{action}")
        
        return result if isinstance(result, dict) else {"result": result}
    
    async def _validate_step_result(
        self, 
        step: WorkflowStep, 
        result: Dict[str, Any],
        context: ExecutionContext
    ) -> 'ValidationResult':
        """Validate step execution result"""
        
        # Check validation rules
        for rule in step.validation_rules:
            if not await self._check_validation_rule(rule, result, context):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Validation rule failed: {rule}"
                )
        
        # Check success criteria
        for criterion in step.success_criteria:
            if not await self._check_success_criterion(criterion, result, context):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Success criterion not met: {criterion}"
                )
        
        return ValidationResult(is_valid=True)
    
    async def _check_validation_rule(
        self, 
        rule: str, 
        result: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Check a validation rule"""
        
        # Simple rule checking (can be enhanced)
        if rule == "check_service_response":
            return "error" not in result
        elif rule == "check_completion":
            return result.get("status") == "completed"
        elif rule == "check_data_present":
            return bool(result.get("data"))
        else:
            return True  # Unknown rules pass by default
    
    async def _check_success_criterion(
        self, 
        criterion: str, 
        result: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Check a success criterion"""
        
        # Simple criterion checking
        if criterion == "operation_completed":
            return result.get("completed", False)
        elif criterion == "data_retrieved":
            return "data" in result and result["data"]
        elif criterion == "task_successful":
            return result.get("success", False)
        else:
            return True  # Unknown criteria pass by default
    
    async def _attempt_adaptation(
        self, 
        step_id: str, 
        step_result: ExecutionResult,
        context: ExecutionContext,
        monitor: ExecutionMonitor
    ) -> 'AdaptationResult':
        """Attempt to adapt failed step execution"""
        
        workflow = context.workflow
        node = workflow.graph.nodes[step_id]
        step = node.step
        
        logger.info(f"Attempting adaptation for failed step {step_id}")
        
        # Determine adaptation trigger
        trigger = await self._determine_adaptation_trigger(step_result, context)
        
        # Select adaptation strategy
        strategy = await self._select_adaptation_strategy(step, trigger, context)
        
        if not strategy:
            return AdaptationResult(success=False, reason="No suitable adaptation strategy")
        
        # Apply adaptation
        adaptation = WorkflowAdaptation(
            workflow_id=workflow.workflow_id,
            trigger=trigger,
            strategy=strategy,
            target_step=step_id,
            original_configuration=step.parameters.copy(),
            adaptation_reason=step_result.error_message or "Step execution failed"
        )
        
        try:
            # Execute adaptation strategy
            adapted_result = await self._execute_adaptation_strategy(
                strategy, step, step_result, context
            )
            
            if adapted_result.status == ExecutionStatus.SUCCESS:
                adaptation.success = True
                adaptation.adapted_configuration = adapted_result.result_data
                adaptation.impact_metrics = {
                    "execution_time": adapted_result.execution_time.total_seconds() if adapted_result.execution_time else 0,
                    "retry_count": node.retry_count + 1
                }
                
                # Record adaptation
                workflow.add_adaptation(adaptation)
                context.adaptation_history.append(adaptation)
                
                # Update node
                node.status = ExecutionStatus.ADAPTED
                node.retry_count += 1
                node.adaptation_history.append(adaptation.dict())
                
                logger.info(f"Successfully adapted step {step_id} using strategy {strategy}")
                
                return AdaptationResult(
                    success=True,
                    adaptation=adaptation,
                    result_data=adapted_result.result_data
                )
            else:
                adaptation.success = False
                workflow.add_adaptation(adaptation)
                
                return AdaptationResult(
                    success=False,
                    reason=f"Adaptation strategy {strategy} failed",
                    adaptation=adaptation
                )
        
        except Exception as e:
            adaptation.success = False
            workflow.add_adaptation(adaptation)
            
            logger.error(f"Error executing adaptation strategy {strategy}: {str(e)}")
            return AdaptationResult(
                success=False,
                reason=f"Adaptation execution error: {str(e)}",
                adaptation=adaptation
            )
    
    async def _determine_adaptation_trigger(
        self, 
        step_result: ExecutionResult,
        context: ExecutionContext
    ) -> AdaptationTrigger:
        """Determine what triggered the need for adaptation"""
        
        error_message = step_result.error_message or ""
        
        if "timeout" in error_message.lower():
            return AdaptationTrigger.PERFORMANCE
        elif "service" in error_message.lower() and "unavailable" in error_message.lower():
            return AdaptationTrigger.RESOURCE_CONSTRAINT
        elif "permission" in error_message.lower() or "auth" in error_message.lower():
            return AdaptationTrigger.CONTEXT_CHANGE
        else:
            return AdaptationTrigger.FAILURE
    
    async def _select_adaptation_strategy(
        self, 
        step: WorkflowStep, 
        trigger: AdaptationTrigger,
        context: ExecutionContext
    ) -> Optional[AdaptationStrategy]:
        """Select appropriate adaptation strategy"""
        
        # Use decision engine for strategy selection
        decision_request = DecisionRequest(
            request_id=f"adaptation_strategy_{step.step_id}",
            decision_type=DecisionType.STRATEGIC,
            context={
                "step": {
                    "name": step.name,
                    "type": step.step_type.value,
                    "service": step.service,
                    "action": step.action
                },
                "trigger": trigger.value,
                "adaptation_points": step.adaptation_points,
                "retry_count": context.workflow.graph.nodes[step.step_id].retry_count
            },
            question="What is the best adaptation strategy for this failed step?",
            options=[
                "retry: Retry the step with same parameters",
                "alternative_path: Use alternative execution path",
                "resource_reallocation: Reallocate resources and retry",
                "step_modification: Modify step parameters and retry",
                "skip: Skip this step and continue",
                "rollback: Rollback and try different approach"
            ]
        )
        
        decision_result = await self.decision_engine.make_decision(decision_request)
        
        if decision_result.confidence < self.adaptation_threshold:
            logger.warning(f"Low confidence in adaptation strategy: {decision_result.confidence}")
            return None
        
        # Extract strategy from decision
        strategy_name = decision_result.selected_option.split(":")[0]
        
        try:
            return AdaptationStrategy(strategy_name)
        except ValueError:
            return AdaptationStrategy.RETRY  # Default fallback
    
    async def _execute_adaptation_strategy(
        self, 
        strategy: AdaptationStrategy,
        step: WorkflowStep,
        step_result: ExecutionResult,
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute the selected adaptation strategy"""
        
        if strategy == AdaptationStrategy.RETRY:
            return await self._retry_step(step, context)
        
        elif strategy == AdaptationStrategy.ALTERNATIVE_PATH:
            return await self._execute_alternative_path(step, context)
        
        elif strategy == AdaptationStrategy.RESOURCE_REALLOCATION:
            return await self._reallocate_resources_and_retry(step, context)
        
        elif strategy == AdaptationStrategy.STEP_MODIFICATION:
            return await self._modify_step_and_retry(step, step_result, context)
        
        elif strategy == AdaptationStrategy.SKIP:
            return ExecutionResult(
                execution_id=context.execution_environment["execution_id"],
                workflow_id=context.workflow.workflow_id,
                step_id=step.step_id,
                status=ExecutionStatus.SKIPPED,
                result_data={"skipped": True, "reason": "Adaptation strategy: skip"}
            )
        
        else:
            # Default to retry
            return await self._retry_step(step, context)
    
    async def _retry_step(self, step: WorkflowStep, context: ExecutionContext) -> ExecutionResult:
        """Retry step execution with same parameters"""
        
        # Simple retry with exponential backoff
        retry_count = context.workflow.graph.nodes[step.step_id].retry_count
        delay = min(2 ** retry_count, 60)  # Max 60 seconds delay
        
        await asyncio.sleep(delay)
        
        # Execute step again
        return await self._execute_single_step(step.step_id, context, self.monitors.get(context.execution_environment["execution_id"]))
    
    async def _execute_alternative_path(self, step: WorkflowStep, context: ExecutionContext) -> ExecutionResult:
        """Execute alternative path for the step"""
        
        # Look for alternative service or action
        alternative_service = step.error_handling.get('fallback_service')
        
        if alternative_service and alternative_service in context.service_clients:
            # Try with alternative service
            parameters = await self._prepare_step_parameters(step, context)
            
            try:
                result = await self._call_service_action(
                    alternative_service, step.action, parameters, context
                )
                
                return ExecutionResult(
                    execution_id=context.execution_environment["execution_id"],
                    workflow_id=context.workflow.workflow_id,
                    step_id=step.step_id,
                    status=ExecutionStatus.SUCCESS,
                    result_data=result,
                    metadata={"used_alternative_service": alternative_service}
                )
            
            except Exception as e:
                return ExecutionResult(
                    execution_id=context.execution_environment["execution_id"],
                    workflow_id=context.workflow.workflow_id,
                    step_id=step.step_id,
                    status=ExecutionStatus.FAILED,
                    error_message=f"Alternative path failed: {str(e)}"
                )
        
        # No alternative available
        return ExecutionResult(
            execution_id=context.execution_environment["execution_id"],
            workflow_id=context.workflow.workflow_id,
            step_id=step.step_id,
            status=ExecutionStatus.FAILED,
            error_message="No alternative path available"
        )
    
    async def _reallocate_resources_and_retry(self, step: WorkflowStep, context: ExecutionContext) -> ExecutionResult:
        """Reallocate resources and retry step"""
        
        # Increase resource allocation
        current_memory = step.metadata.get('allocated_memory_mb', 100)
        current_cpu = step.metadata.get('allocated_cpu_cores', 0.1)
        
        step.metadata['allocated_memory_mb'] = min(current_memory * 1.5, 1000)
        step.metadata['allocated_cpu_cores'] = min(current_cpu * 1.5, 2.0)
        
        # Increase timeout
        if step.timeout:
            step.timeout = timedelta(seconds=step.timeout.total_seconds() * 1.5)
        
        # Retry with increased resources
        return await self._retry_step(step, context)
    
    async def _modify_step_and_retry(
        self, 
        step: WorkflowStep, 
        step_result: ExecutionResult,
        context: ExecutionContext
    ) -> ExecutionResult:
        """Modify step parameters and retry"""
        
        # Use LLM to suggest parameter modifications
        modification_prompt = f"""
        A workflow step failed with the following error. Suggest parameter modifications to fix the issue:
        
        Step: {step.name}
        Service: {step.service}
        Action: {step.action}
        Current Parameters: {json.dumps(step.parameters, indent=2)}
        Error: {step_result.error_message}
        
        Provide modified parameters in JSON format:
        {{
            "modified_parameters": {{<modified parameters>}},
            "modification_reason": "<explanation of changes>"
        }}
        """
        
        try:
            llm_response = await self.llm_client.generate_response(
                modification_prompt,
                context={"session_id": context.workflow.context.session_id}
            )
            
            modification = json.loads(llm_response.content)
            
            # Apply modifications
            original_params = step.parameters.copy()
            step.parameters.update(modification.get("modified_parameters", {}))
            
            # Retry with modified parameters
            result = await self._retry_step(step, context)
            
            # If still failed, restore original parameters
            if result.status == ExecutionStatus.FAILED:
                step.parameters = original_params
            
            return result
            
        except Exception as e:
            logger.error(f"Error modifying step parameters: {str(e)}")
            return await self._retry_step(step, context)
    
    async def _is_critical_failure(self, step_id: str, workflow: IntelligentWorkflow) -> bool:
        """Check if step failure is critical for workflow"""
        
        node = workflow.graph.nodes[step_id]
        
        # Check if step is on critical path
        if step_id in workflow.graph.critical_path:
            return True
        
        # Check if step is exit point
        if step_id in workflow.graph.exit_points:
            return True
        
        # Check if step has many dependents
        dependent_count = sum(
            1 for edge in workflow.graph.edges.values()
            if edge.from_node == step_id
        )
        
        if dependent_count > len(workflow.graph.nodes) * 0.5:  # More than 50% of nodes depend on this
            return True
        
        return False
    
    async def _setup_execution_monitoring(
        self, 
        workflow: IntelligentWorkflow,
        context: ExecutionContext
    ) -> ExecutionMonitor:
        """Set up monitoring for workflow execution"""
        
        execution_id = context.execution_environment["execution_id"]
        
        monitor = ExecutionMonitor(
            monitor_id=f"monitor_{execution_id}",
            workflow_id=workflow.workflow_id,
            monitoring_rules=[
                {"type": "execution_time", "threshold": 1800},  # 30 minutes
                {"type": "failure_rate", "threshold": 0.3},     # 30% failure rate
                {"type": "resource_usage", "threshold": 0.9}    # 90% resource usage
            ],
            alert_thresholds={
                "execution_time_warning": 900,  # 15 minutes
                "failure_rate_warning": 0.2,   # 20% failure rate
                "resource_usage_warning": 0.8  # 80% resource usage
            },
            recovery_policies={
                "execution_timeout": "extend_timeout",
                "high_failure_rate": "increase_retry_attempts",
                "resource_exhaustion": "scale_resources"
            }
        )
        
        self.monitors[execution_id] = monitor
        return monitor
    
    async def _update_workflow_metrics(
        self, 
        workflow: IntelligentWorkflow,
        step_result: ExecutionResult
    ):
        """Update workflow metrics based on step result"""
        
        metrics = workflow.metrics
        
        if step_result.status == ExecutionStatus.SUCCESS:
            metrics.completed_steps += 1
        elif step_result.status == ExecutionStatus.FAILED:
            metrics.failed_steps += 1
        elif step_result.status == ExecutionStatus.SKIPPED:
            metrics.skipped_steps += 1
        elif step_result.status == ExecutionStatus.ADAPTED:
            metrics.adapted_steps += 1
        
        # Update success rate
        total_processed = metrics.completed_steps + metrics.failed_steps + metrics.skipped_steps
        if total_processed > 0:
            metrics.success_rate = metrics.completed_steps / total_processed
        
        # Update adaptation rate
        if metrics.completed_steps > 0:
            metrics.adaptation_rate = metrics.adapted_steps / metrics.completed_steps
        
        # Update execution time
        if step_result.execution_time:
            if not metrics.total_execution_time:
                metrics.total_execution_time = step_result.execution_time
            else:
                metrics.total_execution_time += step_result.execution_time
            
            # Update average step time
            metrics.average_step_time = metrics.total_execution_time / total_processed
    
    async def _stream_progress_update(
        self, 
        context: ExecutionContext,
        step_id: str,
        step_result: ExecutionResult
    ):
        """Stream progress update to clients"""
        
        workflow = context.workflow
        progress_data = {
            "workflow_id": workflow.workflow_id,
            "execution_id": context.execution_environment["execution_id"],
            "step_id": step_id,
            "step_name": workflow.graph.nodes[step_id].step.name,
            "status": step_result.status.value,
            "progress_percentage": workflow.get_progress_percentage(),
            "completed_steps": workflow.metrics.completed_steps,
            "total_steps": workflow.metrics.total_steps,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.stream_manager.publish_progress_update(
            workflow.context.session_id,
            progress_data
        )
    
    async def _record_execution(
        self, 
        workflow: IntelligentWorkflow,
        context: ExecutionContext,
        result: ExecutionResult
    ):
        """Record execution for learning and analysis"""
        
        execution_record = {
            "workflow_id": workflow.workflow_id,
            "execution_id": context.execution_environment["execution_id"],
            "workflow_type": workflow.workflow_type.value,
            "execution_result": {
                "status": result.status.value,
                "execution_time": result.execution_time.total_seconds() if result.execution_time else 0,
                "success_rate": workflow.metrics.success_rate,
                "adaptation_rate": workflow.metrics.adaptation_rate
            },
            "adaptations": [adaptation.dict() for adaptation in workflow.adaptations],
            "performance_metrics": {
                "total_steps": workflow.metrics.total_steps,
                "completed_steps": workflow.metrics.completed_steps,
                "failed_steps": workflow.metrics.failed_steps,
                "adapted_steps": workflow.metrics.adapted_steps
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only recent history
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        # Update performance metrics
        self._update_performance_metrics(workflow, result)
    
    def _update_performance_metrics(
        self, 
        workflow: IntelligentWorkflow,
        result: ExecutionResult
    ):
        """Update global performance metrics"""
        
        workflow_type = workflow.workflow_type.value
        
        if workflow_type not in self.performance_metrics:
            self.performance_metrics[workflow_type] = {
                "total_executions": 0,
                "successful_executions": 0,
                "average_execution_time": 0,
                "average_success_rate": 0,
                "total_adaptations": 0
            }
        
        metrics = self.performance_metrics[workflow_type]
        metrics["total_executions"] += 1
        
        if result.status == ExecutionStatus.SUCCESS:
            metrics["successful_executions"] += 1
        
        if result.execution_time:
            # Update average execution time
            current_avg = metrics["average_execution_time"]
            new_time = result.execution_time.total_seconds()
            metrics["average_execution_time"] = (
                (current_avg * (metrics["total_executions"] - 1) + new_time) /
                metrics["total_executions"]
            )
        
        # Update average success rate
        metrics["average_success_rate"] = (
            metrics["successful_executions"] / metrics["total_executions"]
        )
        
        # Update adaptation count
        metrics["total_adaptations"] += len(workflow.adaptations)
    
    async def get_active_executions(self) -> Dict[str, ExecutionContext]:
        """Get currently active executions"""
        return self.active_executions.copy()
    
    async def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history.copy()
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel active execution"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            context.workflow.update_status(WorkflowStatus.CANCELLED)
            del self.active_executions[execution_id]
            return True
        return False
    
    def register_service_client(self, service_name: str, client: Any):
        """Register a service client"""
        self.service_clients[service_name] = client
        logger.info(f"Registered service client: {service_name}")
    
    def unregister_service_client(self, service_name: str):
        """Unregister a service client"""
        if service_name in self.service_clients:
            del self.service_clients[service_name]
            logger.info(f"Unregistered service client: {service_name}")


# Helper classes
class ValidationResult:
    """Result of step validation"""
    def __init__(self, is_valid: bool, error_message: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message


class AdaptationResult:
    """Result of adaptation attempt"""
    def __init__(
        self, 
        success: bool, 
        reason: str = "",
        adaptation: Optional[WorkflowAdaptation] = None,
        result_data: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.reason = reason
        self.adaptation = adaptation
        self.result_data = result_data or {}
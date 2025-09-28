"""
OUIOE Phase 5: Workflow Orchestrator

Advanced orchestration system that coordinates multiple workflows across
different services, manages cross-service dependencies, and provides
intelligent synchronization and resource management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import json
import uuid
from collections import defaultdict

from .workflow_models import (
    IntelligentWorkflow, WorkflowContext, WorkflowStatus, ExecutionResult,
    ExecutionStatus, OrchestrationContext, OrchestrationResult, OrchestrationStatus,
    ServiceCoordination, CrossServiceWorkflow, WorkflowExecution, ServiceIntegration
)
from .intelligent_workflow_generator import IntelligentWorkflowGenerator
from .adaptive_execution_engine import AdaptiveExecutionEngine
from ..decision import DecisionEngine, DecisionRequest, DecisionType
from ..integrations.thinking_llm_client import ThinkingLLMClient
from ..streaming import StreamManager

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Advanced workflow orchestrator that manages complex multi-service
    workflows with intelligent coordination and synchronization.
    """
    
    def __init__(
        self,
        workflow_generator: IntelligentWorkflowGenerator,
        execution_engine: AdaptiveExecutionEngine,
        decision_engine: DecisionEngine,
        llm_client: ThinkingLLMClient,
        stream_manager: StreamManager
    ):
        self.workflow_generator = workflow_generator
        self.execution_engine = execution_engine
        self.decision_engine = decision_engine
        self.llm_client = llm_client
        self.stream_manager = stream_manager
        
        # Orchestration tracking
        self.active_orchestrations = {}
        self.orchestration_history = []
        self.service_integrations = {}
        self.coordination_patterns = {}
        
        # Service registry and health
        self.service_registry = {}
        self.service_health = {}
        
        # Configuration
        self.max_concurrent_orchestrations = 5
        self.coordination_timeout = timedelta(minutes=60)
        self.synchronization_interval = timedelta(seconds=30)
        
        logger.info("Workflow Orchestrator initialized")
    
    async def orchestrate_complex_workflow(
        self,
        context: WorkflowContext,
        coordination_requirements: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """
        Orchestrate a complex workflow that may span multiple services.
        
        Args:
            context: Workflow context with requirements
            coordination_requirements: Optional coordination specifications
            
        Returns:
            Orchestration result with all workflow outcomes
        """
        orchestration_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting orchestration {orchestration_id} for: {context.primary_intent}")
            
            # Analyze orchestration requirements
            orchestration_analysis = await self._analyze_orchestration_requirements(
                context, coordination_requirements
            )
            
            # Create orchestration context
            orchestration_context = OrchestrationContext(
                orchestration_id=orchestration_id,
                workflows=[],
                coordination_rules=[],
                global_context={
                    "primary_intent": context.primary_intent,
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "start_time": datetime.now().isoformat()
                },
                service_registry=self.service_registry.copy(),
                monitoring_config={
                    "enable_real_time_monitoring": True,
                    "progress_update_interval": 10,
                    "health_check_interval": 30
                }
            )
            
            # Register active orchestration
            self.active_orchestrations[orchestration_id] = orchestration_context
            
            # Generate workflows for orchestration
            workflows = await self._generate_orchestration_workflows(
                context, orchestration_analysis
            )
            orchestration_context.workflows = workflows
            
            # Create coordination rules
            coordination_rules = await self._create_coordination_rules(
                workflows, orchestration_analysis
            )
            orchestration_context.coordination_rules = coordination_rules
            
            # Execute orchestrated workflows
            result = await self._execute_orchestrated_workflows(orchestration_context)
            
            # Record orchestration for learning
            await self._record_orchestration(orchestration_context, result)
            
            logger.info(f"Completed orchestration {orchestration_id} with status: {result.status}")
            return result
            
        except Exception as e:
            logger.error(f"Error in orchestration {orchestration_id}: {str(e)}")
            
            return OrchestrationResult(
                orchestration_id=orchestration_id,
                status=OrchestrationStatus.FAILED,
                workflow_results={},
                error_summary=str(e)
            )
        
        finally:
            # Clean up
            if orchestration_id in self.active_orchestrations:
                del self.active_orchestrations[orchestration_id]
    
    async def _analyze_orchestration_requirements(
        self,
        context: WorkflowContext,
        coordination_requirements: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze requirements for orchestration"""
        
        # Use decision engine for orchestration analysis
        decision_request = DecisionRequest(
            request_id=f"orchestration_analysis_{context.request_id}",
            decision_type=DecisionType.STRATEGIC,
            context={
                "intent": context.primary_intent,
                "available_services": context.available_services,
                "system_context": context.system_context,
                "coordination_requirements": coordination_requirements or {}
            },
            question="How should this complex request be orchestrated across services?",
            options=[
                "Single service workflow",
                "Sequential multi-service workflow",
                "Parallel multi-service workflow", 
                "Hierarchical service coordination",
                "Event-driven service orchestration",
                "Adaptive service mesh coordination"
            ]
        )
        
        decision_result = await self.decision_engine.make_decision(decision_request)
        
        # Use LLM for detailed orchestration analysis
        analysis_prompt = f"""
        Analyze this complex operational request for multi-service orchestration:
        
        Intent: {context.primary_intent}
        Available Services: {context.available_services}
        System Context: {json.dumps(context.system_context, indent=2)}
        Coordination Requirements: {json.dumps(coordination_requirements or {}, indent=2)}
        
        Provide orchestration analysis in JSON format:
        {{
            "orchestration_type": "single|sequential|parallel|hierarchical|event_driven|adaptive",
            "required_services": [<list of services needed>],
            "service_dependencies": {{<service>: [<dependent services>]}},
            "coordination_complexity": "low|medium|high|very_high",
            "estimated_workflows": <number>,
            "synchronization_points": [<list of sync points>],
            "data_flow_requirements": {{<from_service>: {{<to_service>: [<data_types>]}}}},
            "resource_coordination": {{<service>: {{<resource_type>: <allocation>}}}},
            "timing_constraints": {{<constraint_type>: <value>}},
            "failure_handling": {{<service>: <failure_strategy>}},
            "optimization_opportunities": [<list of optimizations>]
        }}
        """
        
        llm_response = await self.llm_client.generate_response(
            analysis_prompt,
            context={"session_id": context.session_id}
        )
        
        try:
            analysis = json.loads(llm_response.content)
        except json.JSONDecodeError:
            # Fallback analysis
            analysis = {
                "orchestration_type": "sequential",
                "required_services": context.available_services[:3],
                "service_dependencies": {},
                "coordination_complexity": "medium",
                "estimated_workflows": 2,
                "synchronization_points": ["start", "end"],
                "data_flow_requirements": {},
                "resource_coordination": {},
                "timing_constraints": {},
                "failure_handling": {},
                "optimization_opportunities": []
            }
        
        # Combine decision engine and LLM analysis
        analysis["decision_confidence"] = decision_result.confidence
        analysis["decision_reasoning"] = decision_result.reasoning
        analysis["orchestration_strategy"] = decision_result.selected_option
        
        return analysis
    
    async def _generate_orchestration_workflows(
        self,
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[IntelligentWorkflow]:
        """Generate workflows for orchestration"""
        
        workflows = []
        required_services = analysis.get("required_services", [])
        orchestration_type = analysis.get("orchestration_type", "sequential")
        
        if orchestration_type == "single":
            # Single comprehensive workflow
            workflow = await self.workflow_generator.generate_workflow(context)
            workflows.append(workflow)
        
        elif orchestration_type in ["sequential", "parallel"]:
            # Create service-specific workflows
            for i, service in enumerate(required_services):
                service_context = WorkflowContext(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    request_id=f"{context.request_id}_service_{i}",
                    primary_intent=f"{context.primary_intent} (via {service})",
                    system_context=context.system_context,
                    user_preferences=context.user_preferences,
                    safety_constraints=context.safety_constraints,
                    available_services=[service],  # Limit to specific service
                    resource_constraints=context.resource_constraints,
                    time_constraints=context.time_constraints,
                    quality_requirements=context.quality_requirements,
                    metadata={**context.metadata, "orchestration_service": service}
                )
                
                workflow = await self.workflow_generator.generate_workflow(service_context)
                workflow.name = f"{workflow.name} ({service})"
                workflow.metadata["orchestration_role"] = service
                workflow.metadata["orchestration_type"] = orchestration_type
                workflows.append(workflow)
        
        elif orchestration_type == "hierarchical":
            # Create master workflow and sub-workflows
            master_workflow = await self._create_master_workflow(context, analysis)
            workflows.append(master_workflow)
            
            # Create sub-workflows for each service
            for service in required_services:
                sub_context = self._create_sub_workflow_context(context, service, analysis)
                sub_workflow = await self.workflow_generator.generate_workflow(sub_context)
                sub_workflow.metadata["orchestration_role"] = "sub_workflow"
                sub_workflow.metadata["parent_workflow"] = master_workflow.workflow_id
                workflows.append(sub_workflow)
        
        elif orchestration_type == "event_driven":
            # Create event-driven workflows
            workflows = await self._create_event_driven_workflows(context, analysis)
        
        elif orchestration_type == "adaptive":
            # Create adaptive orchestration workflows
            workflows = await self._create_adaptive_workflows(context, analysis)
        
        else:
            # Default to sequential
            for service in required_services:
                service_context = WorkflowContext(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    request_id=f"{context.request_id}_default_{service}",
                    primary_intent=f"{context.primary_intent} (default {service})",
                    system_context=context.system_context,
                    available_services=[service]
                )
                
                workflow = await self.workflow_generator.generate_workflow(service_context)
                workflows.append(workflow)
        
        logger.info(f"Generated {len(workflows)} workflows for orchestration")
        return workflows
    
    async def _create_coordination_rules(
        self,
        workflows: List[IntelligentWorkflow],
        analysis: Dict[str, Any]
    ) -> List[ServiceCoordination]:
        """Create coordination rules between workflows"""
        
        coordination_rules = []
        orchestration_type = analysis.get("orchestration_type", "sequential")
        service_dependencies = analysis.get("service_dependencies", {})
        data_flow_requirements = analysis.get("data_flow_requirements", {})
        
        if orchestration_type == "sequential":
            # Sequential coordination
            for i in range(len(workflows) - 1):
                coordination = ServiceCoordination(
                    coordination_id=f"seq_coord_{i}",
                    involved_services=[
                        workflows[i].metadata.get("orchestration_role", f"workflow_{i}"),
                        workflows[i+1].metadata.get("orchestration_role", f"workflow_{i+1}")
                    ],
                    coordination_type="sequential",
                    data_flow={
                        workflows[i].workflow_id: [workflows[i+1].workflow_id]
                    },
                    synchronization_points=["completion"],
                    timeout_policy={"max_wait_time": 1800},  # 30 minutes
                    error_handling={"on_failure": "stop_orchestration"}
                )
                coordination_rules.append(coordination)
        
        elif orchestration_type == "parallel":
            # Parallel coordination with final synchronization
            if len(workflows) > 1:
                parallel_services = [
                    wf.metadata.get("orchestration_role", wf.workflow_id) 
                    for wf in workflows
                ]
                
                coordination = ServiceCoordination(
                    coordination_id="parallel_coord",
                    involved_services=parallel_services,
                    coordination_type="parallel",
                    data_flow={},  # No data flow in pure parallel
                    synchronization_points=["start", "completion"],
                    timeout_policy={"max_wait_time": 3600},  # 60 minutes
                    error_handling={"on_failure": "continue_others"}
                )
                coordination_rules.append(coordination)
        
        elif orchestration_type == "hierarchical":
            # Master-sub workflow coordination
            master_workflow = workflows[0]  # Assume first is master
            sub_workflows = workflows[1:]
            
            for sub_workflow in sub_workflows:
                coordination = ServiceCoordination(
                    coordination_id=f"hierarchical_{sub_workflow.workflow_id}",
                    involved_services=[
                        master_workflow.metadata.get("orchestration_role", "master"),
                        sub_workflow.metadata.get("orchestration_role", "sub")
                    ],
                    coordination_type="hierarchical",
                    data_flow={
                        master_workflow.workflow_id: [sub_workflow.workflow_id],
                        sub_workflow.workflow_id: [master_workflow.workflow_id]
                    },
                    synchronization_points=["delegation", "completion", "aggregation"],
                    timeout_policy={"max_wait_time": 2400},  # 40 minutes
                    error_handling={"on_failure": "escalate_to_master"}
                )
                coordination_rules.append(coordination)
        
        # Add data flow coordination based on analysis
        for from_service, to_services in data_flow_requirements.items():
            for to_service, data_types in to_services.items():
                # Find workflows for these services
                from_workflow = self._find_workflow_by_service(workflows, from_service)
                to_workflow = self._find_workflow_by_service(workflows, to_service)
                
                if from_workflow and to_workflow:
                    coordination = ServiceCoordination(
                        coordination_id=f"data_flow_{from_service}_{to_service}",
                        involved_services=[from_service, to_service],
                        coordination_type="data_flow",
                        data_flow={from_workflow.workflow_id: [to_workflow.workflow_id]},
                        synchronization_points=["data_ready", "data_consumed"],
                        timeout_policy={"max_wait_time": 600},  # 10 minutes
                        error_handling={"on_failure": "retry_data_transfer"}
                    )
                    coordination_rules.append(coordination)
        
        return coordination_rules
    
    async def _execute_orchestrated_workflows(
        self,
        orchestration_context: OrchestrationContext
    ) -> OrchestrationResult:
        """Execute orchestrated workflows with coordination"""
        
        orchestration_id = orchestration_context.orchestration_id
        workflows = orchestration_context.workflows
        coordination_rules = orchestration_context.coordination_rules
        
        logger.info(f"Executing {len(workflows)} orchestrated workflows")
        
        # Initialize result tracking
        workflow_results = {}
        coordination_metrics = defaultdict(dict)
        global_metrics = {
            "start_time": datetime.now(),
            "total_workflows": len(workflows),
            "completed_workflows": 0,
            "failed_workflows": 0,
            "total_coordination_events": 0
        }
        
        try:
            # Determine execution strategy based on coordination rules
            execution_strategy = self._determine_execution_strategy(coordination_rules)
            
            if execution_strategy == "sequential":
                # Execute workflows sequentially
                for workflow in workflows:
                    result = await self._execute_workflow_with_coordination(
                        workflow, orchestration_context, workflow_results
                    )
                    workflow_results[workflow.workflow_id] = result
                    
                    if result.status == ExecutionStatus.SUCCESS:
                        global_metrics["completed_workflows"] += 1
                    else:
                        global_metrics["failed_workflows"] += 1
                        
                        # Check if failure should stop orchestration
                        if self._should_stop_on_failure(workflow, coordination_rules):
                            break
            
            elif execution_strategy == "parallel":
                # Execute workflows in parallel
                tasks = []
                for workflow in workflows:
                    task = asyncio.create_task(
                        self._execute_workflow_with_coordination(
                            workflow, orchestration_context, workflow_results
                        )
                    )
                    tasks.append((workflow.workflow_id, task))
                
                # Wait for all tasks
                for workflow_id, task in tasks:
                    try:
                        result = await task
                        workflow_results[workflow_id] = result
                        
                        if result.status == ExecutionStatus.SUCCESS:
                            global_metrics["completed_workflows"] += 1
                        else:
                            global_metrics["failed_workflows"] += 1
                    
                    except Exception as e:
                        workflow_results[workflow_id] = ExecutionResult(
                            execution_id=f"orch_{orchestration_id}",
                            workflow_id=workflow_id,
                            status=ExecutionStatus.FAILED,
                            error_message=str(e)
                        )
                        global_metrics["failed_workflows"] += 1
            
            elif execution_strategy == "hierarchical":
                # Execute hierarchical orchestration
                result = await self._execute_hierarchical_orchestration(
                    orchestration_context, workflow_results, global_metrics
                )
                return result
            
            elif execution_strategy == "event_driven":
                # Execute event-driven orchestration
                result = await self._execute_event_driven_orchestration(
                    orchestration_context, workflow_results, global_metrics
                )
                return result
            
            # Determine overall status
            total_workflows = len(workflows)
            successful_workflows = global_metrics["completed_workflows"]
            
            if successful_workflows == total_workflows:
                status = OrchestrationStatus.COMPLETING
            elif successful_workflows > total_workflows * 0.5:
                status = OrchestrationStatus.COMPLETING  # Partial success
            else:
                status = OrchestrationStatus.FAILED
            
            # Final coordination and cleanup
            await self._perform_final_coordination(orchestration_context, workflow_results)
            
            global_metrics["end_time"] = datetime.now()
            global_metrics["total_execution_time"] = (
                global_metrics["end_time"] - global_metrics["start_time"]
            ).total_seconds()
            
            return OrchestrationResult(
                orchestration_id=orchestration_id,
                status=status,
                workflow_results=workflow_results,
                coordination_metrics=dict(coordination_metrics),
                global_metrics=global_metrics
            )
        
        except Exception as e:
            logger.error(f"Error in orchestrated execution: {str(e)}")
            
            return OrchestrationResult(
                orchestration_id=orchestration_id,
                status=OrchestrationStatus.FAILED,
                workflow_results=workflow_results,
                error_summary=str(e),
                global_metrics=global_metrics
            )
    
    async def _execute_workflow_with_coordination(
        self,
        workflow: IntelligentWorkflow,
        orchestration_context: OrchestrationContext,
        existing_results: Dict[str, ExecutionResult]
    ) -> ExecutionResult:
        """Execute workflow with coordination awareness"""
        
        logger.info(f"Executing workflow {workflow.workflow_id} with coordination")
        
        # Check coordination prerequisites
        await self._check_coordination_prerequisites(
            workflow, orchestration_context, existing_results
        )
        
        # Prepare coordination data
        coordination_data = await self._prepare_coordination_data(
            workflow, orchestration_context, existing_results
        )
        
        # Update workflow context with coordination data
        workflow.context.metadata.update(coordination_data)
        
        # Execute workflow
        result = await self.execution_engine.execute_workflow(workflow)
        
        # Handle coordination post-execution
        await self._handle_post_execution_coordination(
            workflow, result, orchestration_context
        )
        
        # Stream orchestration progress
        await self._stream_orchestration_progress(
            orchestration_context, workflow, result
        )
        
        return result
    
    async def _check_coordination_prerequisites(
        self,
        workflow: IntelligentWorkflow,
        orchestration_context: OrchestrationContext,
        existing_results: Dict[str, ExecutionResult]
    ):
        """Check if workflow prerequisites are met for coordination"""
        
        workflow_service = workflow.metadata.get("orchestration_role")
        
        # Check coordination rules
        for rule in orchestration_context.coordination_rules:
            if workflow_service in rule.involved_services:
                if rule.coordination_type == "sequential":
                    # Check if prerequisite workflows are completed
                    service_index = rule.involved_services.index(workflow_service)
                    if service_index > 0:
                        # Wait for previous service to complete
                        prev_service = rule.involved_services[service_index - 1]
                        prev_workflow = self._find_workflow_by_service(
                            orchestration_context.workflows, prev_service
                        )
                        
                        if prev_workflow and prev_workflow.workflow_id not in existing_results:
                            raise ValueError(f"Prerequisite workflow not completed: {prev_workflow.workflow_id}")
                
                elif rule.coordination_type == "data_flow":
                    # Check if required data is available
                    for from_workflow_id, to_workflow_ids in rule.data_flow.items():
                        if workflow.workflow_id in to_workflow_ids:
                            if from_workflow_id not in existing_results:
                                raise ValueError(f"Required data source not available: {from_workflow_id}")
    
    async def _prepare_coordination_data(
        self,
        workflow: IntelligentWorkflow,
        orchestration_context: OrchestrationContext,
        existing_results: Dict[str, ExecutionResult]
    ) -> Dict[str, Any]:
        """Prepare coordination data for workflow execution"""
        
        coordination_data = {
            "orchestration_id": orchestration_context.orchestration_id,
            "orchestration_context": orchestration_context.global_context,
            "available_results": {}
        }
        
        # Add results from completed workflows
        for workflow_id, result in existing_results.items():
            if result.status == ExecutionStatus.SUCCESS:
                coordination_data["available_results"][workflow_id] = result.result_data
        
        # Add service-specific coordination data
        workflow_service = workflow.metadata.get("orchestration_role")
        for rule in orchestration_context.coordination_rules:
            if workflow_service in rule.involved_services and rule.coordination_type == "data_flow":
                # Add data flow mappings
                coordination_data["data_flow_mappings"] = rule.data_flow
        
        return coordination_data
    
    async def _handle_post_execution_coordination(
        self,
        workflow: IntelligentWorkflow,
        result: ExecutionResult,
        orchestration_context: OrchestrationContext
    ):
        """Handle coordination tasks after workflow execution"""
        
        # Update global context with results
        if result.status == ExecutionStatus.SUCCESS:
            orchestration_context.global_context[f"result_{workflow.workflow_id}"] = result.result_data
        
        # Trigger coordination events
        workflow_service = workflow.metadata.get("orchestration_role")
        for rule in orchestration_context.coordination_rules:
            if workflow_service in rule.involved_services:
                await self._trigger_coordination_event(
                    rule, workflow, result, orchestration_context
                )
    
    async def _trigger_coordination_event(
        self,
        rule: ServiceCoordination,
        workflow: IntelligentWorkflow,
        result: ExecutionResult,
        orchestration_context: OrchestrationContext
    ):
        """Trigger coordination event based on rule"""
        
        event_data = {
            "rule_id": rule.coordination_id,
            "workflow_id": workflow.workflow_id,
            "service": workflow.metadata.get("orchestration_role"),
            "result_status": result.status.value,
            "timestamp": datetime.now().isoformat()
        }
        
        # Stream coordination event
        await self.stream_manager.publish_coordination_event(
            orchestration_context.orchestration_id,
            event_data
        )
    
    async def _stream_orchestration_progress(
        self,
        orchestration_context: OrchestrationContext,
        workflow: IntelligentWorkflow,
        result: ExecutionResult
    ):
        """Stream orchestration progress update"""
        
        completed_workflows = sum(
            1 for wf in orchestration_context.workflows
            if wf.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        )
        
        progress_data = {
            "orchestration_id": orchestration_context.orchestration_id,
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "workflow_status": workflow.status.value,
            "result_status": result.status.value,
            "completed_workflows": completed_workflows,
            "total_workflows": len(orchestration_context.workflows),
            "progress_percentage": (completed_workflows / len(orchestration_context.workflows)) * 100,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.stream_manager.publish_orchestration_progress(
            orchestration_context.global_context.get("session_id", "unknown"),
            progress_data
        )
    
    def _determine_execution_strategy(self, coordination_rules: List[ServiceCoordination]) -> str:
        """Determine execution strategy based on coordination rules"""
        
        if not coordination_rules:
            return "parallel"  # Default to parallel if no rules
        
        # Analyze coordination types
        coordination_types = [rule.coordination_type for rule in coordination_rules]
        
        if "hierarchical" in coordination_types:
            return "hierarchical"
        elif "event_driven" in coordination_types:
            return "event_driven"
        elif "sequential" in coordination_types:
            return "sequential"
        else:
            return "parallel"
    
    def _should_stop_on_failure(
        self,
        workflow: IntelligentWorkflow,
        coordination_rules: List[ServiceCoordination]
    ) -> bool:
        """Check if orchestration should stop on workflow failure"""
        
        workflow_service = workflow.metadata.get("orchestration_role")
        
        for rule in coordination_rules:
            if workflow_service in rule.involved_services:
                error_handling = rule.error_handling.get("on_failure", "continue")
                if error_handling == "stop_orchestration":
                    return True
        
        return False
    
    def _find_workflow_by_service(
        self,
        workflows: List[IntelligentWorkflow],
        service: str
    ) -> Optional[IntelligentWorkflow]:
        """Find workflow by service name"""
        
        for workflow in workflows:
            if workflow.metadata.get("orchestration_role") == service:
                return workflow
        return None
    
    async def _create_master_workflow(
        self,
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> IntelligentWorkflow:
        """Create master workflow for hierarchical orchestration"""
        
        master_context = WorkflowContext(
            user_id=context.user_id,
            session_id=context.session_id,
            request_id=f"{context.request_id}_master",
            primary_intent=f"Master orchestration: {context.primary_intent}",
            system_context=context.system_context,
            user_preferences=context.user_preferences,
            safety_constraints=context.safety_constraints,
            available_services=["ai-brain"],  # Master uses AI brain for coordination
            resource_constraints=context.resource_constraints,
            time_constraints=context.time_constraints,
            metadata={**context.metadata, "orchestration_role": "master"}
        )
        
        workflow = await self.workflow_generator.generate_workflow(master_context)
        workflow.name = f"Master Orchestration: {workflow.name}"
        workflow.metadata["orchestration_role"] = "master"
        workflow.metadata["orchestration_type"] = "hierarchical"
        
        return workflow
    
    def _create_sub_workflow_context(
        self,
        context: WorkflowContext,
        service: str,
        analysis: Dict[str, Any]
    ) -> WorkflowContext:
        """Create context for sub-workflow"""
        
        return WorkflowContext(
            user_id=context.user_id,
            session_id=context.session_id,
            request_id=f"{context.request_id}_sub_{service}",
            primary_intent=f"Sub-task for {service}: {context.primary_intent}",
            system_context=context.system_context,
            user_preferences=context.user_preferences,
            safety_constraints=context.safety_constraints,
            available_services=[service],
            resource_constraints=context.resource_constraints,
            time_constraints=context.time_constraints,
            metadata={**context.metadata, "orchestration_role": service, "parent_service": "master"}
        )
    
    async def _create_event_driven_workflows(
        self,
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[IntelligentWorkflow]:
        """Create event-driven workflows"""
        
        workflows = []
        required_services = analysis.get("required_services", [])
        
        # Create event producer workflow
        producer_context = WorkflowContext(
            user_id=context.user_id,
            session_id=context.session_id,
            request_id=f"{context.request_id}_producer",
            primary_intent=f"Event producer: {context.primary_intent}",
            system_context=context.system_context,
            available_services=[required_services[0]] if required_services else ["ai-brain"],
            metadata={**context.metadata, "orchestration_role": "event_producer"}
        )
        
        producer_workflow = await self.workflow_generator.generate_workflow(producer_context)
        producer_workflow.metadata["orchestration_role"] = "event_producer"
        workflows.append(producer_workflow)
        
        # Create event consumer workflows
        for i, service in enumerate(required_services[1:], 1):
            consumer_context = WorkflowContext(
                user_id=context.user_id,
                session_id=context.session_id,
                request_id=f"{context.request_id}_consumer_{i}",
                primary_intent=f"Event consumer {service}: {context.primary_intent}",
                system_context=context.system_context,
                available_services=[service],
                metadata={**context.metadata, "orchestration_role": f"event_consumer_{service}"}
            )
            
            consumer_workflow = await self.workflow_generator.generate_workflow(consumer_context)
            consumer_workflow.metadata["orchestration_role"] = f"event_consumer_{service}"
            workflows.append(consumer_workflow)
        
        return workflows
    
    async def _create_adaptive_workflows(
        self,
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[IntelligentWorkflow]:
        """Create adaptive orchestration workflows"""
        
        workflows = []
        required_services = analysis.get("required_services", [])
        
        # Create adaptive coordinator workflow
        coordinator_context = WorkflowContext(
            user_id=context.user_id,
            session_id=context.session_id,
            request_id=f"{context.request_id}_coordinator",
            primary_intent=f"Adaptive coordinator: {context.primary_intent}",
            system_context=context.system_context,
            available_services=["ai-brain"],
            metadata={**context.metadata, "orchestration_role": "adaptive_coordinator"}
        )
        
        coordinator_workflow = await self.workflow_generator.generate_workflow(coordinator_context)
        coordinator_workflow.metadata["orchestration_role"] = "adaptive_coordinator"
        workflows.append(coordinator_workflow)
        
        # Create adaptive service workflows
        for service in required_services:
            service_context = WorkflowContext(
                user_id=context.user_id,
                session_id=context.session_id,
                request_id=f"{context.request_id}_adaptive_{service}",
                primary_intent=f"Adaptive {service}: {context.primary_intent}",
                system_context=context.system_context,
                available_services=[service],
                metadata={**context.metadata, "orchestration_role": f"adaptive_{service}"}
            )
            
            service_workflow = await self.workflow_generator.generate_workflow(service_context)
            service_workflow.metadata["orchestration_role"] = f"adaptive_{service}"
            workflows.append(service_workflow)
        
        return workflows
    
    async def _execute_hierarchical_orchestration(
        self,
        orchestration_context: OrchestrationContext,
        workflow_results: Dict[str, ExecutionResult],
        global_metrics: Dict[str, Any]
    ) -> OrchestrationResult:
        """Execute hierarchical orchestration"""
        
        workflows = orchestration_context.workflows
        master_workflow = workflows[0]  # Assume first is master
        sub_workflows = workflows[1:]
        
        # Execute master workflow first
        master_result = await self._execute_workflow_with_coordination(
            master_workflow, orchestration_context, workflow_results
        )
        workflow_results[master_workflow.workflow_id] = master_result
        
        if master_result.status == ExecutionStatus.SUCCESS:
            global_metrics["completed_workflows"] += 1
            
            # Execute sub-workflows based on master result
            sub_tasks = []
            for sub_workflow in sub_workflows:
                task = asyncio.create_task(
                    self._execute_workflow_with_coordination(
                        sub_workflow, orchestration_context, workflow_results
                    )
                )
                sub_tasks.append((sub_workflow.workflow_id, task))
            
            # Wait for sub-workflows
            for workflow_id, task in sub_tasks:
                try:
                    result = await task
                    workflow_results[workflow_id] = result
                    
                    if result.status == ExecutionStatus.SUCCESS:
                        global_metrics["completed_workflows"] += 1
                    else:
                        global_metrics["failed_workflows"] += 1
                
                except Exception as e:
                    workflow_results[workflow_id] = ExecutionResult(
                        execution_id=f"hier_{orchestration_context.orchestration_id}",
                        workflow_id=workflow_id,
                        status=ExecutionStatus.FAILED,
                        error_message=str(e)
                    )
                    global_metrics["failed_workflows"] += 1
        else:
            global_metrics["failed_workflows"] += 1
            # Master failed, skip sub-workflows
            for sub_workflow in sub_workflows:
                workflow_results[sub_workflow.workflow_id] = ExecutionResult(
                    execution_id=f"hier_{orchestration_context.orchestration_id}",
                    workflow_id=sub_workflow.workflow_id,
                    status=ExecutionStatus.SKIPPED,
                    error_message="Master workflow failed"
                )
        
        # Determine status
        successful_count = global_metrics["completed_workflows"]
        total_count = len(workflows)
        
        if successful_count == total_count:
            status = OrchestrationStatus.COMPLETING
        elif successful_count > 0:
            status = OrchestrationStatus.COMPLETING  # Partial success
        else:
            status = OrchestrationStatus.FAILED
        
        return OrchestrationResult(
            orchestration_id=orchestration_context.orchestration_id,
            status=status,
            workflow_results=workflow_results,
            global_metrics=global_metrics
        )
    
    async def _execute_event_driven_orchestration(
        self,
        orchestration_context: OrchestrationContext,
        workflow_results: Dict[str, ExecutionResult],
        global_metrics: Dict[str, Any]
    ) -> OrchestrationResult:
        """Execute event-driven orchestration"""
        
        workflows = orchestration_context.workflows
        producer_workflow = workflows[0]  # Assume first is producer
        consumer_workflows = workflows[1:]
        
        # Execute producer workflow
        producer_result = await self._execute_workflow_with_coordination(
            producer_workflow, orchestration_context, workflow_results
        )
        workflow_results[producer_workflow.workflow_id] = producer_result
        
        if producer_result.status == ExecutionStatus.SUCCESS:
            global_metrics["completed_workflows"] += 1
            
            # Trigger consumer workflows based on events
            consumer_tasks = []
            for consumer_workflow in consumer_workflows:
                # Simulate event-driven trigger (in real implementation, this would be event-based)
                await asyncio.sleep(1)  # Simulate event processing delay
                
                task = asyncio.create_task(
                    self._execute_workflow_with_coordination(
                        consumer_workflow, orchestration_context, workflow_results
                    )
                )
                consumer_tasks.append((consumer_workflow.workflow_id, task))
            
            # Wait for consumers
            for workflow_id, task in consumer_tasks:
                try:
                    result = await task
                    workflow_results[workflow_id] = result
                    
                    if result.status == ExecutionStatus.SUCCESS:
                        global_metrics["completed_workflows"] += 1
                    else:
                        global_metrics["failed_workflows"] += 1
                
                except Exception as e:
                    workflow_results[workflow_id] = ExecutionResult(
                        execution_id=f"event_{orchestration_context.orchestration_id}",
                        workflow_id=workflow_id,
                        status=ExecutionStatus.FAILED,
                        error_message=str(e)
                    )
                    global_metrics["failed_workflows"] += 1
        else:
            global_metrics["failed_workflows"] += 1
            # Producer failed, consumers won't be triggered
            for consumer_workflow in consumer_workflows:
                workflow_results[consumer_workflow.workflow_id] = ExecutionResult(
                    execution_id=f"event_{orchestration_context.orchestration_id}",
                    workflow_id=consumer_workflow.workflow_id,
                    status=ExecutionStatus.SKIPPED,
                    error_message="Event producer failed"
                )
        
        # Determine status
        successful_count = global_metrics["completed_workflows"]
        total_count = len(workflows)
        
        if successful_count == total_count:
            status = OrchestrationStatus.COMPLETING
        elif successful_count > 0:
            status = OrchestrationStatus.COMPLETING
        else:
            status = OrchestrationStatus.FAILED
        
        return OrchestrationResult(
            orchestration_id=orchestration_context.orchestration_id,
            status=status,
            workflow_results=workflow_results,
            global_metrics=global_metrics
        )
    
    async def _perform_final_coordination(
        self,
        orchestration_context: OrchestrationContext,
        workflow_results: Dict[str, ExecutionResult]
    ):
        """Perform final coordination and cleanup"""
        
        # Aggregate results
        successful_results = {
            wf_id: result for wf_id, result in workflow_results.items()
            if result.status == ExecutionStatus.SUCCESS
        }
        
        # Update global context with aggregated results
        orchestration_context.global_context["final_results"] = {
            "successful_workflows": len(successful_results),
            "total_workflows": len(workflow_results),
            "aggregated_data": {}
        }
        
        # Aggregate data from successful workflows
        for workflow_id, result in successful_results.items():
            orchestration_context.global_context["final_results"]["aggregated_data"][workflow_id] = result.result_data
        
        # Stream final coordination event
        await self.stream_manager.publish_coordination_event(
            orchestration_context.orchestration_id,
            {
                "event_type": "final_coordination",
                "successful_workflows": len(successful_results),
                "total_workflows": len(workflow_results),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _record_orchestration(
        self,
        orchestration_context: OrchestrationContext,
        result: OrchestrationResult
    ):
        """Record orchestration for learning and analysis"""
        
        orchestration_record = {
            "orchestration_id": orchestration_context.orchestration_id,
            "orchestration_type": self._determine_execution_strategy(orchestration_context.coordination_rules),
            "total_workflows": len(orchestration_context.workflows),
            "coordination_rules": len(orchestration_context.coordination_rules),
            "result": {
                "status": result.status.value,
                "successful_workflows": result.global_metrics.get("completed_workflows", 0),
                "failed_workflows": result.global_metrics.get("failed_workflows", 0),
                "execution_time": result.global_metrics.get("total_execution_time", 0)
            },
            "services_involved": list(set(
                wf.metadata.get("orchestration_role", "unknown")
                for wf in orchestration_context.workflows
            )),
            "timestamp": datetime.now().isoformat()
        }
        
        self.orchestration_history.append(orchestration_record)
        
        # Keep only recent history
        if len(self.orchestration_history) > 500:
            self.orchestration_history = self.orchestration_history[-500:]
    
    async def get_active_orchestrations(self) -> Dict[str, OrchestrationContext]:
        """Get currently active orchestrations"""
        return self.active_orchestrations.copy()
    
    async def get_orchestration_history(self) -> List[Dict[str, Any]]:
        """Get orchestration history"""
        return self.orchestration_history.copy()
    
    async def cancel_orchestration(self, orchestration_id: str) -> bool:
        """Cancel active orchestration"""
        if orchestration_id in self.active_orchestrations:
            context = self.active_orchestrations[orchestration_id]
            
            # Cancel all workflows in orchestration
            for workflow in context.workflows:
                workflow.update_status(WorkflowStatus.CANCELLED)
            
            del self.active_orchestrations[orchestration_id]
            return True
        return False
    
    def register_service_integration(self, integration: ServiceIntegration):
        """Register service integration configuration"""
        self.service_integrations[integration.service_name] = integration
        logger.info(f"Registered service integration: {integration.service_name}")
    
    def update_service_health(self, service_name: str, health_status: Dict[str, Any]):
        """Update service health status"""
        self.service_health[service_name] = {
            **health_status,
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get current service health status"""
        return self.service_health.copy()
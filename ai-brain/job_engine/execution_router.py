"""
OpsConductor AI Brain - Execution Router

This module routes workflow execution between Celery (traditional) and Prefect (advanced)
based on workflow complexity, requirements, and system capabilities.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .workflow_generator import GeneratedWorkflow, WorkflowStep, StepType, ExecutionMode
from .prefect_flow_generator import PrefectFlowGenerator
from integrations.prefect_client import PrefectClient, PrefectFlowExecution
from fulfillment_engine.execution_coordinator import ExecutionCoordinator, WorkflowExecutionResult

logger = logging.getLogger(__name__)


class ExecutionEngine(Enum):
    """Available execution engines"""
    CELERY = "celery"
    PREFECT = "prefect"
    AUTO = "auto"


class ComplexityLevel(Enum):
    """Workflow complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


@dataclass
class ExecutionDecision:
    """Decision about which execution engine to use"""
    engine: ExecutionEngine
    reason: str
    complexity_level: ComplexityLevel
    confidence_score: float
    factors: Dict[str, Any]


@dataclass
class ExecutionResult:
    """Unified execution result from either engine"""
    workflow_id: str
    engine_used: ExecutionEngine
    success: bool
    execution_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    steps_completed: int = 0
    total_steps: int = 0
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class ExecutionRouter:
    """
    Routes workflow execution between Celery and Prefect engines
    
    Analyzes workflow complexity and requirements to determine the most
    appropriate execution engine, then handles the execution accordingly.
    """
    
    def __init__(self):
        """Initialize the execution router"""
        self.prefect_client = PrefectClient()
        self.prefect_flow_generator = PrefectFlowGenerator()
        self.celery_coordinator = ExecutionCoordinator()
        
        # Complexity scoring weights
        self.complexity_weights = {
            "step_count": 0.2,
            "dependency_complexity": 0.25,
            "parallel_execution": 0.15,
            "conditional_logic": 0.15,
            "error_handling": 0.1,
            "advanced_features": 0.15
        }
        
        logger.info("Execution router initialized")
    
    async def route_execution(
        self,
        workflow: GeneratedWorkflow,
        engine_preference: ExecutionEngine = ExecutionEngine.AUTO,
        force_engine: bool = False
    ) -> ExecutionResult:
        """
        Route workflow execution to the appropriate engine
        
        Args:
            workflow: The workflow to execute
            engine_preference: Preferred execution engine
            force_engine: Whether to force the preferred engine
            
        Returns:
            ExecutionResult with execution details
        """
        try:
            logger.info(f"Routing execution for workflow: {workflow.workflow_id}")
            
            # Make execution decision
            if force_engine and engine_preference != ExecutionEngine.AUTO:
                decision = ExecutionDecision(
                    engine=engine_preference,
                    reason="Forced by user preference",
                    complexity_level=ComplexityLevel.SIMPLE,
                    confidence_score=1.0,
                    factors={"forced": True}
                )
            else:
                decision = await self._make_execution_decision(workflow, engine_preference)
            
            logger.info(f"Execution decision: {decision.engine.value} (reason: {decision.reason})")
            
            # Execute using selected engine
            if decision.engine == ExecutionEngine.PREFECT:
                return await self._execute_with_prefect(workflow, decision)
            else:
                return await self._execute_with_celery(workflow, decision)
                
        except Exception as e:
            logger.error(f"Error routing workflow execution: {str(e)}")
            return ExecutionResult(
                workflow_id=workflow.workflow_id,
                engine_used=ExecutionEngine.CELERY,  # Fallback
                success=False,
                error_message=str(e),
                logs=[f"Execution routing failed: {str(e)}"]
            )
    
    async def _make_execution_decision(
        self,
        workflow: GeneratedWorkflow,
        preference: ExecutionEngine
    ) -> ExecutionDecision:
        """Make a decision about which execution engine to use"""
        
        # Check if Prefect is available
        prefect_available = await self.prefect_client.is_available()
        
        if not prefect_available:
            return ExecutionDecision(
                engine=ExecutionEngine.CELERY,
                reason="Prefect services not available",
                complexity_level=ComplexityLevel.SIMPLE,
                confidence_score=1.0,
                factors={"prefect_available": False}
            )
        
        # Analyze workflow complexity
        complexity_analysis = self._analyze_workflow_complexity(workflow)
        
        # Apply decision logic
        decision = self._apply_decision_logic(workflow, complexity_analysis, preference)
        
        return decision
    
    def _analyze_workflow_complexity(self, workflow: GeneratedWorkflow) -> Dict[str, Any]:
        """Analyze workflow complexity factors"""
        
        analysis = {
            "step_count": len(workflow.steps),
            "dependency_count": sum(len(step.dependencies) for step in workflow.steps),
            "parallel_steps": 0,
            "conditional_steps": 0,
            "error_handlers": 0,
            "advanced_step_types": 0,
            "estimated_duration": workflow.estimated_duration,
            "risk_level": workflow.risk_level,
            "requires_approval": workflow.requires_approval
        }
        
        # Analyze step types and patterns
        for step in workflow.steps:
            if step.step_type in [StepType.PARALLEL]:
                analysis["parallel_steps"] += 1
            
            if step.step_type in [StepType.CONDITION]:
                analysis["conditional_steps"] += 1
            
            if step.step_type in [StepType.ERROR_HANDLER]:
                analysis["error_handlers"] += 1
            
            if step.step_type in [
                StepType.NETWORK_CAPTURE,
                StepType.NETWORK_MONITOR,
                StepType.PROTOCOL_ANALYSIS,
                StepType.AI_NETWORK_DIAGNOSIS
            ]:
                analysis["advanced_step_types"] += 1
            
            # Check for retry logic
            if step.retry_count > 0:
                analysis["error_handlers"] += 1
        
        # Calculate complexity scores
        analysis["complexity_scores"] = self._calculate_complexity_scores(analysis)
        analysis["overall_complexity"] = self._determine_complexity_level(analysis["complexity_scores"])
        
        return analysis
    
    def _calculate_complexity_scores(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate complexity scores for different factors"""
        
        scores = {}
        
        # Step count complexity (0-1 scale)
        step_count = analysis["step_count"]
        if step_count <= 3:
            scores["step_count"] = 0.1
        elif step_count <= 10:
            scores["step_count"] = 0.5
        elif step_count <= 20:
            scores["step_count"] = 0.8
        else:
            scores["step_count"] = 1.0
        
        # Dependency complexity
        dependency_count = analysis["dependency_count"]
        if dependency_count == 0:
            scores["dependency_complexity"] = 0.1
        elif dependency_count <= 5:
            scores["dependency_complexity"] = 0.4
        elif dependency_count <= 15:
            scores["dependency_complexity"] = 0.7
        else:
            scores["dependency_complexity"] = 1.0
        
        # Parallel execution complexity
        parallel_steps = analysis["parallel_steps"]
        scores["parallel_execution"] = min(parallel_steps / 5.0, 1.0)
        
        # Conditional logic complexity
        conditional_steps = analysis["conditional_steps"]
        scores["conditional_logic"] = min(conditional_steps / 3.0, 1.0)
        
        # Error handling complexity
        error_handlers = analysis["error_handlers"]
        scores["error_handling"] = min(error_handlers / 5.0, 1.0)
        
        # Advanced features complexity
        advanced_steps = analysis["advanced_step_types"]
        scores["advanced_features"] = min(advanced_steps / 3.0, 1.0)
        
        return scores
    
    def _determine_complexity_level(self, scores: Dict[str, float]) -> ComplexityLevel:
        """Determine overall complexity level from scores"""
        
        # Calculate weighted average
        weighted_score = sum(
            scores.get(factor, 0) * weight
            for factor, weight in self.complexity_weights.items()
        )
        
        if weighted_score <= 0.3:
            return ComplexityLevel.SIMPLE
        elif weighted_score <= 0.6:
            return ComplexityLevel.MODERATE
        elif weighted_score <= 0.8:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.ADVANCED
    
    def _apply_decision_logic(
        self,
        workflow: GeneratedWorkflow,
        complexity_analysis: Dict[str, Any],
        preference: ExecutionEngine
    ) -> ExecutionDecision:
        """Apply decision logic to choose execution engine"""
        
        complexity_level = complexity_analysis["overall_complexity"]
        factors = complexity_analysis.copy()
        
        # Decision rules
        if preference == ExecutionEngine.PREFECT:
            # User prefers Prefect
            return ExecutionDecision(
                engine=ExecutionEngine.PREFECT,
                reason="User preference for Prefect",
                complexity_level=complexity_level,
                confidence_score=0.8,
                factors=factors
            )
        
        elif preference == ExecutionEngine.CELERY:
            # User prefers Celery
            return ExecutionDecision(
                engine=ExecutionEngine.CELERY,
                reason="User preference for Celery",
                complexity_level=complexity_level,
                confidence_score=0.8,
                factors=factors
            )
        
        else:
            # Auto decision based on complexity
            if complexity_level == ComplexityLevel.SIMPLE:
                # Simple workflows can use either, prefer Celery for compatibility
                return ExecutionDecision(
                    engine=ExecutionEngine.CELERY,
                    reason="Simple workflow, using Celery for efficiency",
                    complexity_level=complexity_level,
                    confidence_score=0.9,
                    factors=factors
                )
            
            elif complexity_level == ComplexityLevel.MODERATE:
                # Moderate complexity - check specific features
                if (complexity_analysis["parallel_steps"] > 0 or 
                    complexity_analysis["conditional_steps"] > 0 or
                    complexity_analysis["advanced_step_types"] > 0):
                    return ExecutionDecision(
                        engine=ExecutionEngine.PREFECT,
                        reason="Moderate complexity with advanced features",
                        complexity_level=complexity_level,
                        confidence_score=0.7,
                        factors=factors
                    )
                else:
                    return ExecutionDecision(
                        engine=ExecutionEngine.CELERY,
                        reason="Moderate complexity, standard features",
                        complexity_level=complexity_level,
                        confidence_score=0.6,
                        factors=factors
                    )
            
            else:
                # Complex or Advanced - use Prefect
                return ExecutionDecision(
                    engine=ExecutionEngine.PREFECT,
                    reason=f"High complexity ({complexity_level.value}) requires Prefect",
                    complexity_level=complexity_level,
                    confidence_score=0.9,
                    factors=factors
                )
    
    async def _execute_with_prefect(
        self,
        workflow: GeneratedWorkflow,
        decision: ExecutionDecision
    ) -> ExecutionResult:
        """Execute workflow using Prefect"""
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing workflow with Prefect: {workflow.workflow_id}")
            
            # Generate Prefect flow
            flow_definition = self.prefect_flow_generator.generate_prefect_flow(workflow)
            
            # Create and register flow
            async with self.prefect_client as client:
                # Create flow
                flow_result = await client.create_flow(flow_definition)
                flow_id = flow_result["flow_id"]
                
                # Register flow
                registration_result = await client.register_flow(flow_id)
                
                # Execute flow
                execution = await client.execute_flow(
                    flow_id,
                    parameters=workflow.parameters,
                    wait_for_completion=True,
                    timeout_seconds=workflow.estimated_duration * 60 + 300  # Add 5 min buffer
                )
                
                return ExecutionResult(
                    workflow_id=workflow.workflow_id,
                    engine_used=ExecutionEngine.PREFECT,
                    success=execution.success,
                    execution_id=execution.execution_id,
                    start_time=start_time,
                    end_time=execution.end_time or datetime.now(),
                    steps_completed=len(workflow.steps) if execution.success else 0,
                    total_steps=len(workflow.steps),
                    result_data=execution.result,
                    error_message=execution.error_message,
                    logs=execution.logs
                )
                
        except Exception as e:
            logger.error(f"Prefect execution failed: {str(e)}")
            return ExecutionResult(
                workflow_id=workflow.workflow_id,
                engine_used=ExecutionEngine.PREFECT,
                success=False,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
                logs=[f"Prefect execution failed: {str(e)}"]
            )
    
    async def _execute_with_celery(
        self,
        workflow: GeneratedWorkflow,
        decision: ExecutionDecision
    ) -> ExecutionResult:
        """Execute workflow using Celery (traditional execution coordinator)"""
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing workflow with Celery: {workflow.workflow_id}")
            
            # Convert to legacy workflow format for execution coordinator
            from fulfillment_engine.workflow_planner import Workflow, WorkflowStep as LegacyStep
            
            legacy_steps = []
            for step in workflow.steps:
                legacy_step = LegacyStep(
                    step_id=step.step_id,
                    name=step.name,
                    description=step.description,
                    command=step.command,
                    script_content=step.script,
                    target_systems=getattr(step, 'target_systems', []),
                    timeout_seconds=step.timeout,
                    dependencies=step.dependencies
                )
                legacy_steps.append(legacy_step)
            
            legacy_workflow = Workflow(
                workflow_id=workflow.workflow_id,
                name=workflow.name,
                description=workflow.description,
                steps=legacy_steps
            )
            
            # Execute using existing coordinator
            celery_result = await self.celery_coordinator.execute_workflow(legacy_workflow)
            
            return ExecutionResult(
                workflow_id=workflow.workflow_id,
                engine_used=ExecutionEngine.CELERY,
                success=celery_result.success,
                execution_id=str(celery_result.workflow_id),
                start_time=celery_result.start_time or start_time,
                end_time=celery_result.end_time or datetime.now(),
                steps_completed=celery_result.steps_completed,
                total_steps=celery_result.total_steps,
                result_data={"summary": celery_result.summary, "job_details": celery_result.job_details},
                error_message=celery_result.error_message,
                logs=celery_result.logs
            )
            
        except Exception as e:
            logger.error(f"Celery execution failed: {str(e)}")
            return ExecutionResult(
                workflow_id=workflow.workflow_id,
                engine_used=ExecutionEngine.CELERY,
                success=False,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
                logs=[f"Celery execution failed: {str(e)}"]
            )
    
    async def get_execution_status(
        self,
        execution_id: str,
        engine: ExecutionEngine
    ) -> Optional[ExecutionResult]:
        """Get status of a running execution"""
        
        try:
            if engine == ExecutionEngine.PREFECT:
                async with self.prefect_client as client:
                    execution = await client.get_flow_status(execution_id)
                    
                    return ExecutionResult(
                        workflow_id="unknown",  # Would need to track this
                        engine_used=ExecutionEngine.PREFECT,
                        success=execution.success,
                        execution_id=execution.execution_id,
                        start_time=execution.start_time,
                        end_time=execution.end_time,
                        result_data=execution.result,
                        error_message=execution.error_message,
                        logs=execution.logs
                    )
            else:
                # Celery status checking would be implemented here
                logger.warning("Celery status checking not implemented")
                return None
                
        except Exception as e:
            logger.error(f"Error getting execution status: {str(e)}")
            return None
    
    async def cancel_execution(
        self,
        execution_id: str,
        engine: ExecutionEngine
    ) -> bool:
        """Cancel a running execution"""
        
        try:
            if engine == ExecutionEngine.PREFECT:
                async with self.prefect_client as client:
                    return await client.cancel_execution(execution_id)
            else:
                # Celery cancellation would be implemented here
                logger.warning("Celery execution cancellation not implemented")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling execution: {str(e)}")
            return False
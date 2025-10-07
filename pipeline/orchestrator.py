"""
Pipeline Orchestrator - Phase 5 Integration

Main controller that coordinates the 4-stage OpsConductor pipeline:
User Request → Stage A (Classifier) → Stage B (Selector) → Stage C (Planner) → Stage D (Answerer) → User Response

This orchestrator ensures seamless data flow, error handling, and performance monitoring
across all pipeline stages.
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_c.planner import StageCPlanner
from pipeline.stages.stage_d.answerer import StageDAnswerer
from pipeline.stages.stage_e.executor import StageEExecutor
from pipeline.schemas.decision_v1 import DecisionV1, ConfidenceLevel
from pipeline.schemas.response_v1 import ResponseV1, ResponseType, ClarificationResponse, ClarificationRequest
from execution.dtos import ExecutionRequest
from pipeline.conversation_history import get_conversation_manager

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stage enumeration for tracking and monitoring."""
    STAGE_A = "stage_a"
    STAGE_B = "stage_b"
    STAGE_C = "stage_c"
    STAGE_D = "stage_d"
    STAGE_E = "stage_e"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_CLARIFICATION = "needs_clarification"


@dataclass
class PipelineMetrics:
    """Performance metrics for pipeline execution."""
    total_duration_ms: float
    stage_durations: Dict[str, float]
    memory_usage_mb: float
    request_id: str
    timestamp: float
    status: PipelineStatus
    error_details: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    response: ResponseV1
    metrics: PipelineMetrics
    intermediate_results: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    needs_clarification: bool = False


class PipelineOrchestrator:
    """
    Main pipeline orchestrator that coordinates all 4 stages.
    
    Responsibilities:
    - Stage coordination and data flow
    - Error handling and recovery
    - Performance monitoring
    - Resource management
    - Health status reporting
    """
    
    def __init__(self, llm_client=None):
        """Initialize the pipeline orchestrator with all stage components."""
        # Initialize LLM client if not provided
        if llm_client is None:
            from llm.factory import get_default_llm_client
            llm_client = get_default_llm_client()
        
        self.llm_client = llm_client
        
        # Initialize stages with required parameters
        # NOTE: tool_registry has been removed - database is the single source of truth
        self.stage_a = StageAClassifier(llm_client)
        self.stage_b = StageBSelector(llm_client)
        self.stage_c = StageCPlanner(llm_client)
        self.stage_d = StageDAnswerer(llm_client)
        self.stage_e = StageEExecutor()
        
        # Performance tracking
        self._active_requests: Dict[str, float] = {}
        self._completed_requests: List[PipelineMetrics] = []
        self._max_history = 1000  # Keep last 1000 requests for metrics
        
        # Clarification configuration
        self._confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
        self._max_clarification_attempts = int(os.getenv("MAX_CLARIFICATION_ATTEMPTS", "3"))
        
        # Health status
        self._last_health_check = time.time()
        self._health_status = "healthy"
        self._error_count = 0
        self._success_count = 0
    
    async def initialize(self):
        """Initialize the orchestrator and connect to LLM."""
        try:
            # Connect to LLM
            await self.llm_client.connect()
            if not self.llm_client.is_connected:
                raise Exception("Failed to connect to LLM")
        except Exception as e:
            raise Exception(f"Orchestrator initialization failed: {str(e)}")
    
    async def process_request(
        self, 
        user_request: str, 
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> PipelineResult:
        """
        Process a user request through the complete 4-stage pipeline with confidence-driven clarification.
        
        Args:
            user_request: The user's natural language request
            request_id: Optional request identifier for tracking
            context: Optional context including clarification history
            session_id: Optional session identifier for conversation history
            progress_callback: Optional callback function for real-time progress updates
                              Called with (stage: str, status: str, data: dict)
            
        Returns:
            PipelineResult containing the response and execution metrics
        """
        if request_id is None:
            request_id = str(uuid4())
        
        start_time = time.time()
        self._active_requests[request_id] = start_time
        
        stage_durations = {}
        intermediate_results = {}
        
        # Initialize clarification context
        if context is None:
            context = {}
        context.setdefault("clarification_attempts", 0)
        context.setdefault("original_request", user_request)
        context.setdefault("clarification_history", [])
        
        # Add conversation history to context if session_id is provided
        if session_id:
            conversation_manager = get_conversation_manager()
            # Add user message to history
            conversation_manager.add_message(session_id, "user", user_request)
            # Get formatted history for context injection
            conversation_history = conversation_manager.get_formatted_history(session_id, max_messages=10)
            context["conversation_history"] = conversation_history
            context["session_id"] = session_id
            logger.info(f"Session {session_id}: {conversation_manager.get_message_count(session_id)} messages in history")
        
        try:
            logger.info(f"🚀 [REQUEST {request_id}] Starting pipeline processing")
            logger.info(f"📝 User request: {user_request[:100]}...")
            
            # Stage A: Classification
            logger.info(f"⏱️  [STAGE A] Starting classification...")
            if progress_callback:
                await progress_callback("stage_a", "start", {"stage": "A", "name": "Classification", "message": "🔍 Analyzing your request..."})
            
            stage_start = time.time()
            classification_result = await self._execute_stage_a(user_request, context)
            stage_durations["stage_a"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_a"] = classification_result
            logger.info(f"✅ [STAGE A] Complete in {stage_durations['stage_a']:.2f}ms")
            logger.info(f"   Intent: {classification_result.intent.category}/{classification_result.intent.action}, Confidence: {classification_result.overall_confidence:.2f} ({classification_result.confidence_level.value})")
            
            # Compress Stage A result for context management
            context["compressed_stage_a"] = await self._compress_stage_result("Stage A", classification_result, user_request)
            
            if progress_callback:
                await progress_callback("stage_a", "complete", {"stage": "A", "name": "Classification", "duration_ms": stage_durations["stage_a"], "message": f"✅ Classification complete ({stage_durations['stage_a']:.0f}ms)"})
            
            # ✅ PURE LLM PIPELINE: All requests go through Stage B → C → D → E
            # No fast paths, no shortcuts - full intelligent routing
            logger.info(f"🧠 Stage A complete, routing to Stage B for tool selection")
            
            # Check if clarification is needed due to low confidence
            if await self._needs_clarification(classification_result, context):
                clarification_response = await self._handle_low_confidence_clarification(
                    classification_result, context, user_request
                )
                
                # Calculate metrics for clarification
                total_duration = (time.time() - start_time) * 1000
                metrics = PipelineMetrics(
                    total_duration_ms=total_duration,
                    stage_durations=stage_durations,
                    memory_usage_mb=self._get_memory_usage(),
                    request_id=request_id,
                    timestamp=start_time,
                    status=PipelineStatus.NEEDS_CLARIFICATION
                )
                
                return PipelineResult(
                    response=clarification_response,
                    metrics=metrics,
                    intermediate_results=intermediate_results,
                    success=True,
                    needs_clarification=True
                )
            
            # Stage B: Selection
            logger.info(f"⏱️  [STAGE B] Starting tool selection...")
            if progress_callback:
                await progress_callback("stage_b", "start", {"stage": "B", "name": "Tool Selection", "message": "🔧 Selecting tools..."})
            
            stage_start = time.time()
            selection_result = await self._execute_stage_b(classification_result, context)
            stage_durations["stage_b"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_b"] = selection_result
            logger.info(f"✅ [STAGE B] Complete in {stage_durations['stage_b']:.2f}ms")
            if selection_result and hasattr(selection_result, 'selected_tools'):
                logger.info(f"   Selected {len(selection_result.selected_tools)} tools")
            
            # Compress Stage B result for context management
            context["compressed_stage_b"] = await self._compress_stage_result("Stage B", selection_result, user_request)
            
            if progress_callback:
                await progress_callback("stage_b", "complete", {"stage": "B", "name": "Tool Selection", "duration_ms": stage_durations["stage_b"], "message": f"✅ Tool selection complete ({stage_durations['stage_b']:.0f}ms)"})
            
            # Stage C: Planning (skip if no tool selection)
            planning_result = None
            has_tools = (selection_result is not None and 
                        hasattr(selection_result, 'selected_tools') and 
                        len(selection_result.selected_tools) > 0)
            
            if has_tools:
                logger.info(f"⏱️  [STAGE C] Starting plan creation...")
                if progress_callback:
                    await progress_callback("stage_c", "start", {"stage": "C", "name": "Planning", "message": "📋 Creating execution plan..."})
                
                stage_start = time.time()
                planning_result = await self._execute_stage_c(classification_result, selection_result)
                stage_durations["stage_c"] = (time.time() - stage_start) * 1000
                intermediate_results["stage_c"] = planning_result
                logger.info(f"✅ [STAGE C] Complete in {stage_durations['stage_c']:.2f}ms")
                if planning_result and hasattr(planning_result, 'plan'):
                    plan_dict = planning_result.plan if isinstance(planning_result.plan, dict) else {}
                    steps = plan_dict.get('steps', [])
                    logger.info(f"   Created plan with {len(steps)} steps")
                
                # Compress Stage C result for context management
                context["compressed_stage_c"] = await self._compress_stage_result("Stage C", planning_result, user_request)
                
                if progress_callback:
                    await progress_callback("stage_c", "complete", {"stage": "C", "name": "Planning", "duration_ms": stage_durations["stage_c"], "message": f"✅ Planning complete ({stage_durations['stage_c']:.0f}ms)"})
            else:
                logger.info("⏭️  Skipping Stage C: No tool selection (information-only request)")
                stage_durations["stage_c"] = 0
            
            # Stage D: Response Generation
            logger.info(f"⏱️  [STAGE D] Starting response generation...")
            if progress_callback:
                await progress_callback("stage_d", "start", {"stage": "D", "name": "Response Generation", "message": "💬 Generating response..."})
            
            stage_start = time.time()
            response_result = await self._execute_stage_d(classification_result, selection_result, planning_result, context)
            stage_durations["stage_d"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_d"] = response_result
            logger.info(f"✅ [STAGE D] Complete in {stage_durations['stage_d']:.2f}ms")
            logger.info(f"   Response type: {response_result.response_type}, Approval required: {response_result.approval_required}")
            
            if progress_callback:
                await progress_callback("stage_d", "complete", {"stage": "D", "name": "Response Generation", "duration_ms": stage_durations["stage_d"], "message": f"✅ Response complete ({stage_durations['stage_d']:.0f}ms)"})
            
            # 🚀 PHASE 7: Stage E - Execution (if plan exists and should be executed)
            should_execute = False
            
            # Skip execution for information-only requests (no plan)
            if planning_result is None:
                logger.info("⏭️  Skipping Stage E: No execution plan (information-only request)")
            # Check if we have a plan with steps
            elif planning_result and hasattr(planning_result, 'plan') and planning_result.plan:
                plan_steps = planning_result.plan.get('steps', []) if isinstance(planning_result.plan, dict) else getattr(planning_result.plan, 'steps', [])
                if plan_steps and len(plan_steps) > 0:
                    # Execute if: EXECUTION_READY, or if approval_required is False
                    if response_result.response_type == ResponseType.EXECUTION_READY:
                        should_execute = True
                        logger.info("🚀 PHASE 7: Executing plan (EXECUTION_READY)")
                    elif not response_result.approval_required:
                        should_execute = True
                        logger.info("🚀 PHASE 7: Auto-executing plan (no approval required)")
            
            if should_execute:
                stage_start = time.time()
                
                try:
                    execution_result = await self._execute_stage_e(
                        planning_result, 
                        context,
                        request_id
                    )
                    stage_durations["stage_e"] = (time.time() - stage_start) * 1000
                    intermediate_results["stage_e"] = execution_result
                    
                    # For IMMEDIATE executions, fetch and display the actual results
                    if execution_result.execution_mode == "immediate":
                        logger.info(f"🔍 ORCHESTRATOR: Execution mode is IMMEDIATE, fetching results for {execution_result.execution_id}")
                        # Wait a moment for execution to complete
                        await asyncio.sleep(2.0)
                        
                        # Fetch the execution and step results from database
                        from execution.repository import ExecutionRepository
                        repo = ExecutionRepository(self.stage_e.db_connection_string)
                        completed_execution = repo.get_execution_by_id(execution_result.execution_id)
                        
                        logger.info(f"🔍 ORCHESTRATOR: Fetched execution: {completed_execution is not None}, Status: {completed_execution.status.value if completed_execution else 'N/A'}")
                        
                        if completed_execution and completed_execution.status.value == "completed":
                            # Fetch step results to get actual data
                            steps = repo.get_execution_steps(execution_result.execution_id)
                            logger.info(f"🔍 ORCHESTRATOR: Fetched {len(steps)} steps")
                            
                            # Check if any steps failed
                            has_errors = False
                            for step in steps:
                                if step.output_data and isinstance(step.output_data, dict):
                                    logger.info(f"🔍 ORCHESTRATOR: Step output_data status: {step.output_data.get('status')}")
                                    if step.output_data.get("status") == "failed":
                                        has_errors = True
                                        break
                            
                            logger.info(f"🔍 ORCHESTRATOR: has_errors = {has_errors}")
                            
                            # Display the appropriate header
                            if has_errors:
                                logger.info("🔍 ORCHESTRATOR: Adding 'Execution Completed with Errors' message")
                                response_result.message += f"\n\n⚠️ **Execution Completed with Errors**\n"
                                
                                # Extract error messages from failed steps
                                for step in steps:
                                    if step.output_data and isinstance(step.output_data, dict):
                                        if step.output_data.get("status") == "failed":
                                            logger.info(f"🔍 ORCHESTRATOR: Processing failed step, output_data keys: {step.output_data.keys()}")
                                            error_msg = None
                                            # Try different error field names
                                            if "error" in step.output_data:
                                                error_msg = step.output_data["error"]
                                                logger.info(f"🔍 ORCHESTRATOR: Found 'error' field: {error_msg}")
                                            elif "stderr" in step.output_data and step.output_data["stderr"]:
                                                error_msg = step.output_data["stderr"].strip()
                                                logger.info(f"🔍 ORCHESTRATOR: Found 'stderr' field: {error_msg}")
                                            elif "error_message" in step.output_data:
                                                error_msg = step.output_data["error_message"]
                                                logger.info(f"🔍 ORCHESTRATOR: Found 'error_message' field: {error_msg}")
                                            
                                            if error_msg:
                                                # Include step name for context
                                                step_name = step.step_name if hasattr(step, 'step_name') else "Unknown step"
                                                logger.info(f"🔍 ORCHESTRATOR: Adding error message for step '{step_name}'")
                                                response_result.message += f"\n⚠️ **Error in '{step_name}':** {error_msg}\n"
                                            else:
                                                logger.info(f"🔍 ORCHESTRATOR: No error message found in output_data")
                            else:
                                logger.info("🔍 ORCHESTRATOR: Adding 'Execution Completed Successfully' message")
                                response_result.message += f"\n\n✅ **Execution Completed Successfully**\n\n"
                                
                                # Use LLM to analyze execution results and answer the user's question
                                logger.info("🔍 ORCHESTRATOR: Analyzing execution results with LLM")
                                analysis = await self._analyze_execution_results(
                                    user_request=user_request,
                                    execution_steps=steps,
                                    decision=intermediate_results.get("stage_a")
                                )
                                response_result.message += f"{analysis}\n"
                            
                            response_result.message += f"\n---\n"
                            response_result.message += f"- Execution ID: `{execution_result.execution_id}`\n"
                            response_result.message += f"- Status: `{completed_execution.status.value}`\n"
                            logger.info(f"🔍 ORCHESTRATOR: Final message length: {len(response_result.message)} chars")
                            logger.info(f"🔍 ORCHESTRATOR: Message preview: {response_result.message[:500]}...")
                        else:
                            # Execution not yet complete or failed
                            logger.info("🔍 ORCHESTRATOR: Execution not completed yet or failed")
                            response_result.message += f"\n\n✅ **Execution Started**\n"
                            response_result.message += f"- Execution ID: `{execution_result.execution_id}`\n"
                            response_result.message += f"- Status: `{execution_result.status}`\n"
                            response_result.message += f"- Mode: `{execution_result.execution_mode}`\n"
                    else:
                        # For QUEUED or PENDING_APPROVAL executions
                        response_result.message += f"\n\n✅ **Execution Started**\n"
                        response_result.message += f"- Execution ID: `{execution_result.execution_id}`\n"
                        response_result.message += f"- Status: `{execution_result.status}`\n"
                        response_result.message += f"- Mode: `{execution_result.execution_mode}`\n"
                        
                        if execution_result.status == "queued":
                            response_result.message += f"\n📋 Your request has been queued for background execution. You can track progress using the execution ID."
                        elif execution_result.status == "pending_approval":
                            response_result.message += f"\n⏳ Your request requires approval before execution. An approval request has been created."
                    
                    logger.info(f"✅ Stage E execution completed: {execution_result.execution_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Stage E execution failed: {e}")
                    # Don't fail the entire pipeline, just log the error
                    response_result.message += f"\n\n⚠️ **Execution Failed**\n"
                    response_result.message += f"Error: {str(e)}\n"
                    response_result.message += f"The plan was created successfully, but execution could not be started."
            
            # Calculate total metrics
            total_duration = (time.time() - start_time) * 1000
            
            metrics = PipelineMetrics(
                total_duration_ms=total_duration,
                stage_durations=stage_durations,
                memory_usage_mb=self._get_memory_usage(),
                request_id=request_id,
                timestamp=start_time,
                status=PipelineStatus.COMPLETED
            )
            
            # Log comprehensive performance summary
            logger.info(f"🎉 [REQUEST {request_id}] Pipeline complete in {total_duration:.2f}ms")
            logger.info(f"📊 Performance breakdown:")
            logger.info(f"   Stage A (Classification): {stage_durations.get('stage_a', 0):.2f}ms")
            logger.info(f"   Stage B (Tool Selection): {stage_durations.get('stage_b', 0):.2f}ms")
            logger.info(f"   Stage C (Planning):       {stage_durations.get('stage_c', 0):.2f}ms")
            logger.info(f"   Stage D (Response):       {stage_durations.get('stage_d', 0):.2f}ms")
            logger.info(f"   Stage E (Execution):      {stage_durations.get('stage_e', 0):.2f}ms")
            logger.info(f"   Memory usage: {metrics.memory_usage_mb:.2f}MB")
            
            # Update success metrics
            self._success_count += 1
            self._update_metrics_history(metrics)
            
            # Store assistant response in conversation history
            if session_id and response_result:
                conversation_manager = get_conversation_manager()
                conversation_manager.add_message(session_id, "assistant", response_result.message)
            
            return PipelineResult(
                response=response_result,
                metrics=metrics,
                intermediate_results=intermediate_results,
                success=True
            )
            
        except Exception as e:
            # Handle pipeline errors
            total_duration = (time.time() - start_time) * 1000
            error_message = f"Pipeline failed: {str(e)}"
            
            metrics = PipelineMetrics(
                total_duration_ms=total_duration,
                stage_durations=stage_durations,
                memory_usage_mb=self._get_memory_usage(),
                request_id=request_id,
                timestamp=start_time,
                status=PipelineStatus.FAILED,
                error_details=error_message
            )
            
            # Update error metrics
            self._error_count += 1
            self._update_metrics_history(metrics)
            
            # Generate error response
            error_response = await self._generate_error_response(error_message)
            
            return PipelineResult(
                response=error_response,
                metrics=metrics,
                intermediate_results=intermediate_results,
                success=False,
                error_message=error_message
            )
            
        finally:
            # Clean up active request tracking
            if request_id in self._active_requests:
                del self._active_requests[request_id]
    
    async def _execute_stage_a(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> DecisionV1:
        """Execute Stage A: Classification."""
        try:
            result = await self.stage_a.classify(user_request, context)
            if not isinstance(result, DecisionV1):
                raise ValueError(f"Stage A returned invalid result type: {type(result)}")
            return result
        except Exception as e:
            raise Exception(f"Stage A failed: {str(e)}")
    
    async def _execute_stage_b(self, classification: DecisionV1, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute Stage B: Selection."""
        try:
            result = await self.stage_b.select_tools(classification, context)
            return result
        except Exception as e:
            raise Exception(f"Stage B failed: {str(e)}")
    
    async def _execute_stage_c(self, decision: DecisionV1, selection: Any) -> Any:
        """Execute Stage C: Planning."""
        try:
            result = await self.stage_c.create_plan(decision, selection)
            return result
        except Exception as e:
            raise Exception(f"Stage C failed: {str(e)}")
    
    async def _execute_stage_d(self, decision: DecisionV1, selection: Any, plan: Any, context: Optional[Dict[str, Any]] = None) -> ResponseV1:
        """Execute Stage D: Response Generation."""
        try:
            result = await self.stage_d.generate_response(decision, selection, plan, context)
            if not isinstance(result, ResponseV1):
                raise ValueError(f"Stage D returned invalid result type: {type(result)}")
            return result
        except Exception as e:
            raise Exception(f"Stage D failed: {str(e)}")
    
    async def _execute_stage_e(self, plan: Any, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> Any:
        """Execute Stage E: Execution."""
        try:
            # Extract tenant_id and actor_id from context (with defaults for now)
            tenant_id = context.get("tenant_id", "default") if context else "default"
            actor_id = context.get("actor_id", 1) if context else 1
            
            # Extract plan dict
            plan_dict = plan.model_dump() if hasattr(plan, 'model_dump') else plan
            if isinstance(plan_dict, dict) and 'plan' in plan_dict:
                plan_dict = plan_dict['plan']
            
            # Convert plan to execution request
            execution_request = ExecutionRequest(
                plan=plan_dict,
                approval_level=plan_dict.get('execution_metadata', {}).get('approval_level', 0),
                trace_id=request_id,
                tags=["source:pipeline", f"request_id:{request_id}"],
                metadata={"context": context} if context else {}
            )
            
            # Execute the plan
            result = await self.stage_e.execute(execution_request, tenant_id, actor_id)
            return result
        except Exception as e:
            raise Exception(f"Stage E failed: {str(e)}")
    
    async def _generate_error_response(self, error_message: str) -> ResponseV1:
        """Generate an error response when pipeline fails - FAIL HARD if Stage D fails."""
        # NO FALLBACKS - if Stage D fails, we fail
        return await self.stage_d.generate_error_response(error_message)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB - FAIL HARD if psutil not available."""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _update_metrics_history(self, metrics: PipelineMetrics):
        """Update metrics history with size limit."""
        self._completed_requests.append(metrics)
        if len(self._completed_requests) > self._max_history:
            self._completed_requests = self._completed_requests[-self._max_history:]
    
    async def _compress_stage_result(self, stage_name: str, result: Any, user_request: str) -> str:
        """
        Compress stage result into a compact summary (200-400 tokens).
        This prevents context window explosion in multi-stage pipelines.
        
        Args:
            stage_name: Name of the stage (e.g., "Stage A", "Stage B")
            result: Stage result object
            user_request: Original user request for context
            
        Returns:
            Compressed summary string (200-400 tokens)
        """
        from llm.client import LLMRequest
        
        # Convert result to string representation
        if hasattr(result, '__dict__'):
            result_str = str(result.__dict__)
        else:
            result_str = str(result)
        
        # Truncate if too long (rough estimate: 4 chars = 1 token)
        if len(result_str) > 4000:  # ~1000 tokens
            result_str = result_str[:4000] + "... [truncated]"
        
        compression_prompt = f"""Compress the following {stage_name} result into a compact summary (≤ 250 tokens).

**User Request:** {user_request}

**{stage_name} Result:**
{result_str}

**Instructions:**
- Preserve: numeric settings, file paths, API params, tool names, entity IDs, and key decisions
- Omit: narrative text, boilerplate, and redundant details
- Format: Bullet points, each ≤ 25 tokens
- Output under "Summary:" heading

Summary:"""

        try:
            request = LLMRequest(
                prompt=compression_prompt,
                system_prompt="You are a compression agent. Summarize technical data into compact, loss-aware summaries.",
                temperature=0.1,
                max_tokens=400  # Cap at 400 tokens for summary
            )
            
            response = await self.llm_client.generate(request)
            compressed = response.content.strip()
            
            logger.info(f"📦 Compressed {stage_name}: {len(result_str)} chars → {len(compressed)} chars")
            return compressed
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to compress {stage_name} result: {e}. Using truncated version.")
            # Fallback: simple truncation
            return result_str[:1000] + "... [compression failed, truncated]"
    
    async def _create_rolling_summary(self, context: Dict[str, Any]) -> str:
        """
        Create a rolling summary of all stage results so far.
        This is used to pass compressed context between stages.
        
        Args:
            context: Pipeline context with intermediate results
            
        Returns:
            Rolling summary string (≤ 500 tokens)
        """
        summaries = []
        
        # Collect compressed summaries from context
        if "compressed_stage_a" in context:
            summaries.append(f"**Stage A (Classification):**\n{context['compressed_stage_a']}")
        
        if "compressed_stage_b" in context:
            summaries.append(f"**Stage B (Tool Selection):**\n{context['compressed_stage_b']}")
        
        if "compressed_stage_c" in context:
            summaries.append(f"**Stage C (Planning):**\n{context['compressed_stage_c']}")
        
        if not summaries:
            return ""
        
        return "\n\n".join(summaries)
    
    async def _needs_clarification(self, classification_result: DecisionV1, context: Dict[str, Any]) -> bool:
        """
        Determine if clarification is needed based on confidence and attempt history.
        
        Args:
            classification_result: Stage A classification result
            context: Request context including clarification history
            
        Returns:
            True if clarification is needed, False otherwise
        """
        # Check if we've exceeded maximum clarification attempts
        if context.get("clarification_attempts", 0) >= self._max_clarification_attempts:
            return False
        
        # Check if confidence is below threshold
        if classification_result.overall_confidence < self._confidence_threshold:
            return True
        
        # Check if confidence level is explicitly LOW
        if classification_result.confidence_level == ConfidenceLevel.LOW:
            return True
        
        return False
    
    async def _handle_low_confidence_clarification(
        self, 
        classification_result: DecisionV1, 
        context: Dict[str, Any],
        user_request: str
    ) -> ResponseV1:
        """
        Handle low confidence by generating clarification request or refusing to proceed.
        
        Args:
            classification_result: Stage A classification result
            context: Request context
            user_request: Original user request
            
        Returns:
            ResponseV1 with clarification request or refusal
        """
        attempts = context.get("clarification_attempts", 0)
        
        # If we've reached max attempts, refuse to proceed
        if attempts >= self._max_clarification_attempts:
            return await self._generate_confidence_refusal_response(
                classification_result, context, user_request
            )
        
        # Generate clarification request
        missing_info = await self._identify_missing_information(classification_result, user_request)
        
        # Use Stage D to generate clarification response
        clarification_response = await self.stage_d.request_clarification(
            classification_result, missing_info, context
        )
        
        # Update context for next attempt
        context["clarification_attempts"] = attempts + 1
        context["clarification_history"].append({
            "attempt": attempts + 1,
            "confidence": classification_result.overall_confidence,
            "missing_info": missing_info,
            "timestamp": time.time()
        })
        
        # Convert ClarificationResponse to ResponseV1
        return ResponseV1(
            response_type=ResponseType.CLARIFICATION,
            message=clarification_response.message,
            confidence=ConfidenceLevel.LOW,
            clarification_needed=clarification_response.clarifications_needed,
            partial_analysis=clarification_response.partial_analysis,
            response_id=clarification_response.response_id,
            processing_time_ms=clarification_response.processing_time_ms,
            metadata={
                "clarification_attempt": attempts + 1,
                "max_attempts": self._max_clarification_attempts,
                "confidence_threshold": self._confidence_threshold
            }
        )
    
    async def _generate_confidence_refusal_response(
        self, 
        classification_result: DecisionV1, 
        context: Dict[str, Any],
        user_request: str
    ) -> ResponseV1:
        """
        Generate response refusing to proceed due to persistent low confidence.
        
        Args:
            classification_result: Stage A classification result
            context: Request context
            user_request: Original user request
            
        Returns:
            ResponseV1 explaining why the system cannot proceed
        """
        attempts = context.get("clarification_attempts", 0)
        
        message = f"""I apologize, but after {attempts} attempts to clarify your request, I still don't have enough confidence to proceed safely.

**Original request:** {user_request}

**Current understanding:**
- Intent: {classification_result.intent.category}/{classification_result.intent.action}
- Confidence: {classification_result.overall_confidence:.1%} (below {self._confidence_threshold:.1%} threshold)
- Entities found: {len(classification_result.entities)}

**Why I cannot proceed:**
As an AI system responsible for infrastructure operations, I must maintain a minimum confidence level of {self._confidence_threshold:.1%} before executing any actions. This ensures safety and prevents unintended consequences.

**What you can do:**
1. **Rephrase your request** with more specific details
2. **Include specific system names, services, or components**
3. **Clarify the exact action** you want me to perform
4. **Provide additional context** about your environment

**Example of a clearer request:**
Instead of: "fix the server"
Try: "restart the nginx service on web-server-01"

I'm designed to be helpful while maintaining safety standards. Please try again with a more detailed request."""

        return ResponseV1(
            response_type=ResponseType.ERROR,
            message=message,
            confidence=ConfidenceLevel.LOW,
            response_id=f"refuse_{int(time.time())}",
            processing_time_ms=1,
            metadata={
                "reason": "insufficient_confidence_after_clarification",
                "attempts_made": attempts,
                "final_confidence": classification_result.overall_confidence,
                "confidence_threshold": self._confidence_threshold
            }
        )
    
    async def _identify_missing_information(self, classification_result: DecisionV1, user_request: str) -> List[str]:
        """
        Identify what information is missing to improve confidence.
        
        Args:
            classification_result: Stage A classification result
            user_request: Original user request
            
        Returns:
            List of missing information items
        """
        missing_info = []
        
        # Check for missing entities based on intent type
        if classification_result.intent.category == "action":
            if not any(e.type == "target" for e in classification_result.entities):
                missing_info.append("specific target system or service name")
            
            if not any(e.type == "action" for e in classification_result.entities):
                missing_info.append("specific action to perform")
        
        elif classification_result.intent.category == "information":
            if not any(e.type in ["system", "service", "metric"] for e in classification_result.entities):
                missing_info.append("what system or service to check")
        
        # Check for vague language
        vague_indicators = ["something", "anything", "stuff", "thing", "it", "that"]
        if any(word in user_request.lower() for word in vague_indicators):
            missing_info.append("more specific description instead of vague terms")
        
        # Check for missing context
        if len(user_request.split()) < 4:
            missing_info.append("more detailed description of what you need")
        
        # If no specific missing info identified, add general guidance
        if not missing_info:
            missing_info.append("more specific details about your request")
        
        return missing_info
    
    def _format_asset_list_directly(self, assets: List[Dict]) -> str:
        """Format asset list directly without LLM - for simple listing queries."""
        if not assets:
            return "No assets found."
        
        result = f"### Asset List ({len(assets)} total)\n\n"
        
        for i, asset in enumerate(assets, 1):
            result += f"**{i}. {asset.get('name', 'Unknown')}**\n"
            result += f"   - Hostname: {asset.get('hostname', 'N/A')}\n"
            result += f"   - IP Address: {asset.get('ip_address', 'N/A')}\n"
            result += f"   - OS: {asset.get('os_version', asset.get('os_type', 'N/A'))}\n"
            result += f"   - Device Type: {asset.get('device_type', 'N/A')}\n"
            result += f"   - Environment: {asset.get('environment', 'N/A')}\n"
            result += f"   - Service: {asset.get('service_type', 'N/A')}"
            if asset.get('database_type'):
                result += f" ({asset.get('database_type')})"
            result += f"\n"
            result += f"   - Data Center: {asset.get('data_center', 'N/A')}\n"
            result += f"   - Criticality: {asset.get('criticality', 'N/A')}\n"
            if asset.get('description'):
                result += f"   - Description: {asset.get('description')}\n"
            result += "\n"
        
        return result
    
    async def _analyze_execution_results(
        self,
        user_request: str,
        execution_steps: List[Any],
        decision: Optional[DecisionV1] = None
    ) -> str:
        """
        Use LLM to analyze execution results and generate a natural language answer.
        
        Args:
            user_request: The original user question
            execution_steps: List of execution steps with output_data
            decision: Optional Stage A decision for context
            
        Returns:
            Natural language answer extracted from execution results
        """
        try:
            # Extract relevant data from execution steps
            execution_data = []
            raw_assets = []
            for step in execution_steps:
                if step.output_data and isinstance(step.output_data, dict):
                    if step.output_data.get("status") != "failed":
                        execution_data.append({
                            "step_name": step.step_name,
                            "data": step.output_data.get("data"),
                            "count": step.output_data.get("count"),
                            "query_type": step.output_data.get("query_type")
                        })
                        # Extract raw asset data for direct formatting
                        if step.output_data.get("data") and isinstance(step.output_data.get("data"), list):
                            raw_assets.extend(step.output_data.get("data"))
            
            if not execution_data:
                return "No data was retrieved from the execution."
            
            # Check if this is a simple asset listing query - format directly without LLM!
            is_simple_asset_list = (
                decision and 
                decision.intent.category == "asset_management" and
                any(keyword in user_request.lower() for keyword in ["list all", "show all", "list assets", "show assets"])
            )
            
            if is_simple_asset_list and raw_assets:
                logger.info(f"🔍 ORCHESTRATOR: Simple asset list detected, formatting {len(raw_assets)} assets directly")
                return self._format_asset_list_directly(raw_assets)
            
            
            # OPTIMIZATION: Detect query type and intelligently truncate data
            import json
            
            # Detect if this is a "count" or "how many" query
            is_count_query = any(
                keyword in user_request.lower() 
                for keyword in ["how many", "count", "number of", "total"]
            )
            
            # Detect if this is asking for specific attributes (OS types, environments, etc.)
            is_attribute_query = any(
                keyword in user_request.lower()
                for keyword in ["what os", "which os", "what environment", "which environment", 
                               "what type", "which type", "what database", "which database"]
            )
            
            # Detect if query asks for breakdowns (by OS, environment, etc.)
            is_breakdown_query = any(
                keyword in user_request.lower()
                for keyword in ["windows", "linux", "ubuntu", "centos", "macos", "os", "operating system",
                               "environment", "production", "staging", "development",
                               "database", "mysql", "postgres", "mongodb",
                               "device type", "server", "workstation", "laptop"]
            )
            
            # Optimize execution data based on query type
            if is_count_query:
                # Check if this is a count query with breakdown requirements
                if is_breakdown_query and raw_assets:
                    # Count query with breakdown - include aggregated counts by attributes
                    logger.info("🚀 OPTIMIZATION: Count query with breakdown detected - sending counts + breakdowns")
                    
                    # Calculate breakdowns
                    os_counts = {}
                    env_counts = {}
                    device_counts = {}
                    
                    for asset in raw_assets:
                        # OS breakdown
                        os_type = asset.get("os_type", "Unknown")
                        os_counts[os_type] = os_counts.get(os_type, 0) + 1
                        
                        # Environment breakdown
                        environment = asset.get("environment", "Unknown")
                        env_counts[environment] = env_counts.get(environment, 0) + 1
                        
                        # Device type breakdown
                        device_type = asset.get("device_type", "Unknown")
                        device_counts[device_type] = device_counts.get(device_type, 0) + 1
                    
                    optimized_data = [{
                        "total_count": len(raw_assets),
                        "breakdown_by_os": os_counts,
                        "breakdown_by_environment": env_counts,
                        "breakdown_by_device_type": device_counts,
                        "query_type": "count_with_breakdown"
                    }]
                    execution_data_json = json.dumps(optimized_data, indent=2, default=str)
                    asset_schema_context = "\n**Note:** Data includes total count and breakdowns by OS, environment, and device type."
                else:
                    # Simple count query - only send counts
                    logger.info("🚀 OPTIMIZATION: Count query detected - sending only counts")
                    optimized_data = []
                    for item in execution_data:
                        optimized_data.append({
                            "step_name": item["step_name"],
                            "count": item.get("count", len(item.get("data", [])) if item.get("data") else 0),
                            "query_type": item.get("query_type")
                        })
                    execution_data_json = json.dumps(optimized_data, indent=2, default=str)
                    asset_schema_context = ""  # No schema needed for counts
                
            elif is_attribute_query and raw_assets and len(raw_assets) > 10:
                # For attribute queries with many results, send summary + sample
                logger.info(f"🚀 OPTIMIZATION: Attribute query with {len(raw_assets)} assets - sending summary")
                
                # Extract unique values for common attributes
                summary = {
                    "total_count": len(raw_assets),
                    "sample_assets": raw_assets[:5],  # First 5 as examples
                    "unique_os_types": list(set(a.get("os_type") for a in raw_assets if a.get("os_type"))),
                    "unique_environments": list(set(a.get("environment") for a in raw_assets if a.get("environment"))),
                    "unique_device_types": list(set(a.get("device_type") for a in raw_assets if a.get("device_type"))),
                    "unique_database_types": list(set(a.get("database_type") for a in raw_assets if a.get("database_type"))),
                    "unique_data_centers": list(set(a.get("data_center") for a in raw_assets if a.get("data_center")))
                }
                execution_data_json = json.dumps(summary, indent=2, default=str)
                asset_schema_context = "\n**Note:** Data includes summary statistics and sample assets."
                
            elif raw_assets and len(raw_assets) > 15:
                # For large result sets, truncate to first 10 + summary
                logger.info(f"🚀 OPTIMIZATION: Large result set ({len(raw_assets)} assets) - truncating to 10 + summary")
                truncated_data = []
                for item in execution_data:
                    if item.get("data") and isinstance(item["data"], list) and len(item["data"]) > 15:
                        truncated_data.append({
                            "step_name": item["step_name"],
                            "count": len(item["data"]),
                            "data": item["data"][:10],  # First 10 items
                            "truncated": True,
                            "query_type": item.get("query_type")
                        })
                    else:
                        truncated_data.append(item)
                execution_data_json = json.dumps(truncated_data, indent=2, default=str)
                asset_schema_context = "\n**Note:** Large result set truncated to first 10 items for analysis."
                
            else:
                # Normal query - send full data but with condensed schema
                execution_data_json = json.dumps(execution_data, indent=2, default=str)
                asset_schema_context = "\n**Asset Fields:** name, hostname, ip_address, os_type, os_version, device_type, environment, service_type, database_type, data_center, criticality"
            
            logger.info(f"🔍 ORCHESTRATOR: Execution data length: {len(execution_data_json)} chars")
            logger.info(f"🔍 ORCHESTRATOR: Execution data preview: {execution_data_json[:500]}...")
            
            # Simplified prompt - reduced verbosity
            prompt = f"""Answer the user's question based on the execution results.

**Question:** {user_request}
{asset_schema_context}

**Data:**
```json
{execution_data_json}
```

**Instructions:**
- Extract the specific information requested
- Provide a clear, direct answer
- For counts: state the number
- For lists: summarize key details
- For attributes: list unique values

**Answer:**"""

            # Call LLM to analyze results
            from llm.client import LLMRequest
            
            # Calculate max_tokens dynamically based on prompt size
            # Rough estimate: 1 token ≈ 4 characters for English text
            estimated_prompt_tokens = len(prompt) // 4
            max_context_length = 131072  # Qwen2.5-14B-Instruct-AWQ context window (131K tokens)
            safety_buffer = 100  # Reserve tokens for formatting overhead
            
            # Calculate available tokens for output
            available_tokens = max_context_length - estimated_prompt_tokens - safety_buffer
            max_output_tokens = max(500, min(available_tokens, 8000))  # Between 500-8000 tokens
            
            logger.info(f"🔍 ORCHESTRATOR: Prompt length: {len(prompt)} chars (~{estimated_prompt_tokens} tokens)")
            logger.info(f"🔍 ORCHESTRATOR: Available output tokens: {available_tokens}, using: {max_output_tokens}")
            
            llm_request = LLMRequest(
                prompt=prompt,
                temperature=0.1,  # Very low temperature for factual extraction
                max_tokens=max_output_tokens  # Dynamically calculated to fit within context window
            )
            
            logger.info(f"🔍 ORCHESTRATOR: Sending prompt to LLM (length: {len(prompt)} chars)")
            
            # DEBUG: Save the full prompt to a file to see what's being sent
            with open("/tmp/llm_prompt_debug.txt", "w") as f:
                f.write(prompt)
            logger.info("🔍 ORCHESTRATOR: Full prompt saved to /tmp/llm_prompt_debug.txt")
            
            response = await self.llm_client.generate(llm_request)
            
            if response and response.content:
                logger.info(f"🔍 ORCHESTRATOR: LLM response length: {len(response.content)} chars")
                logger.info(f"🔍 ORCHESTRATOR: LLM response preview: {response.content[:500]}...")
                return response.content.strip()
            else:
                logger.warning("🔍 ORCHESTRATOR: LLM returned no content")
                return "Unable to analyze execution results."
                
        except Exception as e:
            logger.error(f"Failed to analyze execution results: {e}")
            return f"Error analyzing results: {str(e)}"
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current pipeline health status."""
        current_time = time.time()
        
        # Calculate success rate
        total_requests = self._success_count + self._error_count
        success_rate = (self._success_count / total_requests * 100) if total_requests > 0 else 100.0
        
        # Calculate average response time
        recent_requests = [
            m for m in self._completed_requests 
            if current_time - m.timestamp < 300  # Last 5 minutes
        ]
        avg_response_time = (
            sum(m.total_duration_ms for m in recent_requests) / len(recent_requests)
            if recent_requests else 0.0
        )
        
        # Determine health status
        health_status = "healthy"
        if success_rate < 95.0:
            health_status = "degraded"
        if success_rate < 80.0 or avg_response_time > 10000:  # 10 seconds
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "timestamp": current_time,
            "metrics": {
                "total_requests": total_requests,
                "success_count": self._success_count,
                "error_count": self._error_count,
                "success_rate_percent": round(success_rate, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "active_requests": len(self._active_requests),
                "memory_usage_mb": self._get_memory_usage()
            },
            "stages": {
                "stage_a": "healthy" if hasattr(self.stage_a, 'classify') else "unknown",
                "stage_b": "healthy" if hasattr(self.stage_b, 'select_tools') else "unknown",
                "stage_c": "healthy" if hasattr(self.stage_c, 'create_plan') else "unknown",
                "stage_d": "healthy" if hasattr(self.stage_d, 'generate_response') else "unknown"
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        if not self._completed_requests:
            return {
                "total_requests": 0,
                "avg_duration_ms": 0.0,
                "stage_averages": {},
                "percentiles": {}
            }
        
        # Calculate overall metrics
        durations = [m.total_duration_ms for m in self._completed_requests]
        durations.sort()
        
        # Calculate stage averages
        stage_averages = {}
        for stage in ["stage_a", "stage_b", "stage_c", "stage_d"]:
            stage_durations = [
                m.stage_durations.get(stage, 0.0) 
                for m in self._completed_requests 
                if stage in m.stage_durations
            ]
            stage_averages[stage] = (
                sum(stage_durations) / len(stage_durations) 
                if stage_durations else 0.0
            )
        
        # Calculate percentiles
        def percentile(data: List[float], p: float) -> float:
            if not data:
                return 0.0
            index = int(len(data) * p / 100)
            return data[min(index, len(data) - 1)]
        
        return {
            "total_requests": len(self._completed_requests),
            "avg_duration_ms": sum(durations) / len(durations),
            "stage_averages": stage_averages,
            "percentiles": {
                "p50": percentile(durations, 50),
                "p90": percentile(durations, 90),
                "p95": percentile(durations, 95),
                "p99": percentile(durations, 99)
            },
            "success_rate": (
                self._success_count / (self._success_count + self._error_count) * 100
                if (self._success_count + self._error_count) > 0 else 100.0
            )
        }
    
    async def process_batch_requests(
        self, 
        requests: List[str], 
        max_concurrent: int = 5
    ) -> List[PipelineResult]:
        """
        Process multiple requests concurrently with concurrency control.
        
        Args:
            requests: List of user requests to process
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List of pipeline results in the same order as input requests
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(request: str, index: int) -> tuple[int, PipelineResult]:
            async with semaphore:
                result = await self.process_request(request, f"batch_{index}")
                return index, result
        
        # Execute all requests concurrently with semaphore control
        tasks = [
            process_with_semaphore(request, i) 
            for i, request in enumerate(requests)
        ]
        
        # Wait for all tasks to complete
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Sort results by original index and extract results
        results = [None] * len(requests)
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                # Handle task exceptions
                continue
            index, result = task_result
            results[index] = result
        
        # Fill any None results with error responses
        for i, result in enumerate(results):
            if result is None:
                error_response = await self._generate_error_response("Batch processing failed")
                results[i] = PipelineResult(
                    response=error_response,
                    metrics=PipelineMetrics(
                        total_duration_ms=0.0,
                        stage_durations={},
                        memory_usage_mb=0.0,
                        request_id=f"batch_{i}_error",
                        timestamp=time.time(),
                        status=PipelineStatus.FAILED,
                        error_details="Batch processing failed"
                    ),
                    intermediate_results={},
                    success=False,
                    error_message="Batch processing failed"
                )
        
        return results


# Global pipeline orchestrator instance
_pipeline_orchestrator: Optional[PipelineOrchestrator] = None


async def get_pipeline_orchestrator(llm_client=None) -> PipelineOrchestrator:
    """Get the global pipeline orchestrator instance."""
    global _pipeline_orchestrator
    if _pipeline_orchestrator is None:
        _pipeline_orchestrator = PipelineOrchestrator(llm_client)
        await _pipeline_orchestrator.initialize()
    return _pipeline_orchestrator


async def process_user_request(user_request: str, request_id: Optional[str] = None) -> PipelineResult:
    """
    Convenience function to process a user request through the pipeline.
    
    Args:
        user_request: The user's natural language request
        request_id: Optional request identifier for tracking
        
    Returns:
        PipelineResult containing the response and execution metrics
    """
    orchestrator = await get_pipeline_orchestrator()
    return await orchestrator.process_request(user_request, request_id)
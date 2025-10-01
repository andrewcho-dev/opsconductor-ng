"""
Pipeline Orchestrator - Phase 5 Integration

Main controller that coordinates the 4-stage OpsConductor pipeline:
User Request → Stage A (Classifier) → Stage B (Selector) → Stage C (Planner) → Stage D (Answerer) → User Response

This orchestrator ensures seamless data flow, error handling, and performance monitoring
across all pipeline stages.
"""

import asyncio
import time
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_c.planner import StageCPlanner
from pipeline.stages.stage_d.answerer import StageDAnswerer
from pipeline.schemas.decision_v1 import DecisionV1, ConfidenceLevel
from pipeline.schemas.response_v1 import ResponseV1, ResponseType, ClarificationResponse, ClarificationRequest


class PipelineStage(Enum):
    """Pipeline stage enumeration for tracking and monitoring."""
    STAGE_A = "stage_a"
    STAGE_B = "stage_b"
    STAGE_C = "stage_c"
    STAGE_D = "stage_d"


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
            from llm.ollama_client import OllamaClient
            default_config = {
                "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                "default_model": os.getenv("DEFAULT_MODEL", "qwen2.5:14b-instruct-q4_k_m"),
                "timeout": int(os.getenv("OLLAMA_TIMEOUT", "30"))
            }
            llm_client = OllamaClient(default_config)
        
        self.llm_client = llm_client
        
        # Initialize tool registry
        from pipeline.stages.stage_b.tool_registry import ToolRegistry
        self.tool_registry = ToolRegistry()
        
        # Initialize stages with required parameters
        self.stage_a = StageAClassifier(llm_client)
        self.stage_b = StageBSelector(llm_client, self.tool_registry)
        self.stage_c = StageCPlanner(llm_client)
        self.stage_d = StageDAnswerer(llm_client)
        
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
        context: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Process a user request through the complete 4-stage pipeline with confidence-driven clarification.
        
        Args:
            user_request: The user's natural language request
            request_id: Optional request identifier for tracking
            context: Optional context including clarification history
            
        Returns:
            PipelineResult containing the response and execution metrics
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"
        
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
        
        try:
            # Stage A: Classification
            stage_start = time.time()
            classification_result = await self._execute_stage_a(user_request, context)
            stage_durations["stage_a"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_a"] = classification_result
            
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
            stage_start = time.time()
            selection_result = await self._execute_stage_b(classification_result, context)
            stage_durations["stage_b"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_b"] = selection_result
            
            # Stage C: Planning
            stage_start = time.time()
            planning_result = await self._execute_stage_c(classification_result, selection_result)
            stage_durations["stage_c"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_c"] = planning_result
            
            # Stage D: Response Generation
            stage_start = time.time()
            response_result = await self._execute_stage_d(classification_result, selection_result, planning_result, context)
            stage_durations["stage_d"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_d"] = response_result
            
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
            
            # Update success metrics
            self._success_count += 1
            self._update_metrics_history(metrics)
            
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
            result = self.stage_c.create_plan(decision, selection)
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
    
    async def _generate_error_response(self, error_message: str) -> ResponseV1:
        """Generate an error response when pipeline fails."""
        try:
            # Try to use Stage D to generate a proper error response
            return await self.stage_d.generate_error_response(error_message)
        except Exception:
            # Fallback to basic error response if Stage D fails
            from pipeline.schemas.response_v1 import ResponseType, ConfidenceLevel
            from datetime import datetime
            return ResponseV1(
                response_type=ResponseType.ERROR,
                message=f"Pipeline error: {error_message}",
                confidence=ConfidenceLevel.LOW,
                response_id="error",
                processing_time_ms=1
            )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    def _update_metrics_history(self, metrics: PipelineMetrics):
        """Update metrics history with size limit."""
        self._completed_requests.append(metrics)
        if len(self._completed_requests) > self._max_history:
            self._completed_requests = self._completed_requests[-self._max_history:]
    
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
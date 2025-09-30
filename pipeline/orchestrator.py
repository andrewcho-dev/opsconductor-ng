"""
Pipeline Orchestrator - Phase 5 Integration

Main controller that coordinates the 4-stage OpsConductor pipeline:
User Request → Stage A (Classifier) → Stage B (Selector) → Stage C (Planner) → Stage D (Answerer) → User Response

This orchestrator ensures seamless data flow, error handling, and performance monitoring
across all pipeline stages.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_c.planner import StageCPlanner
from pipeline.stages.stage_d.answerer import StageDAnswerer
from pipeline.schemas.decision_v1 import DecisionV1
from pipeline.schemas.response_v1 import ResponseV1


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
                "base_url": "http://localhost:11434",
                "default_model": "llama2",
                "timeout": 30
            }
            llm_client = OllamaClient(default_config)
        
        self.llm_client = llm_client
        
        # Initialize stages with required parameters
        self.stage_a = StageAClassifier(llm_client)
        self.stage_b = StageBSelector(llm_client)
        self.stage_c = StageCPlanner(llm_client)
        self.stage_d = StageDAnswerer(llm_client)
        
        # Performance tracking
        self._active_requests: Dict[str, float] = {}
        self._completed_requests: List[PipelineMetrics] = []
        self._max_history = 1000  # Keep last 1000 requests for metrics
        
        # Health status
        self._last_health_check = time.time()
        self._health_status = "healthy"
        self._error_count = 0
        self._success_count = 0
    
    async def process_request(
        self, 
        user_request: str, 
        request_id: Optional[str] = None
    ) -> PipelineResult:
        """
        Process a user request through the complete 4-stage pipeline.
        
        Args:
            user_request: The user's natural language request
            request_id: Optional request identifier for tracking
            
        Returns:
            PipelineResult containing the response and execution metrics
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"
        
        start_time = time.time()
        self._active_requests[request_id] = start_time
        
        stage_durations = {}
        intermediate_results = {}
        
        try:
            # Stage A: Classification
            stage_start = time.time()
            classification_result = await self._execute_stage_a(user_request)
            stage_durations["stage_a"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_a"] = classification_result
            
            # Stage B: Selection
            stage_start = time.time()
            selection_result = await self._execute_stage_b(classification_result)
            stage_durations["stage_b"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_b"] = selection_result
            
            # Stage C: Planning
            stage_start = time.time()
            planning_result = await self._execute_stage_c(classification_result, selection_result)
            stage_durations["stage_c"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_c"] = planning_result
            
            # Stage D: Response Generation
            stage_start = time.time()
            response_result = await self._execute_stage_d(classification_result, selection_result, planning_result)
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
    
    async def _execute_stage_a(self, user_request: str) -> DecisionV1:
        """Execute Stage A: Classification."""
        try:
            result = await self.stage_a.classify(user_request)
            if not isinstance(result, DecisionV1):
                raise ValueError(f"Stage A returned invalid result type: {type(result)}")
            return result
        except Exception as e:
            raise Exception(f"Stage A failed: {str(e)}")
    
    async def _execute_stage_b(self, classification: DecisionV1) -> Any:
        """Execute Stage B: Selection."""
        try:
            result = await self.stage_b.select_tools(classification)
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
    
    async def _execute_stage_d(self, decision: DecisionV1, selection: Any, plan: Any) -> ResponseV1:
        """Execute Stage D: Response Generation."""
        try:
            result = await self.stage_d.generate_response(decision, selection, plan)
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
            from pipeline.schemas.response_v1 import ResponseType
            return ResponseV1(
                type=ResponseType.ERROR,
                message=f"Pipeline error: {error_message}",
                timestamp=time.time(),
                request_id="error",
                success=False
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


def get_pipeline_orchestrator(llm_client=None) -> PipelineOrchestrator:
    """Get the global pipeline orchestrator instance."""
    global _pipeline_orchestrator
    if _pipeline_orchestrator is None:
        _pipeline_orchestrator = PipelineOrchestrator(llm_client)
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
    orchestrator = get_pipeline_orchestrator()
    return await orchestrator.process_request(user_request, request_id)
"""
Metrics Collector - Execution metrics collection and aggregation
Collects performance metrics, success rates, and execution statistics
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

from execution.models import ExecutionStatus, SLAClass
from execution.repository import ExecutionRepository


logger = logging.getLogger(__name__)


# ============================================================================
# MODELS
# ============================================================================

class ExecutionMetrics(BaseModel):
    """Execution metrics for a time period"""
    period_start: datetime
    period_end: datetime
    
    # Execution counts
    total_executions: int = 0
    completed_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    timeout_executions: int = 0
    
    # Success rate
    success_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Performance metrics
    avg_duration_ms: Optional[float] = None
    min_duration_ms: Optional[int] = None
    max_duration_ms: Optional[int] = None
    p50_duration_ms: Optional[float] = None
    p95_duration_ms: Optional[float] = None
    p99_duration_ms: Optional[float] = None
    
    # Step metrics
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    avg_steps_per_execution: float = 0.0
    
    # Queue metrics
    avg_queue_time_ms: Optional[float] = None
    max_queue_time_ms: Optional[int] = None
    
    # SLA metrics
    sla_violations: int = 0
    sla_compliance_rate: float = Field(default=100.0, ge=0.0, le=100.0)


class StepMetrics(BaseModel):
    """Metrics for a specific step type"""
    step_type: str
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    avg_duration_ms: Optional[float] = None


class SystemMetrics(BaseModel):
    """System-wide metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Active executions
    active_executions: int = 0
    queued_executions: int = 0
    
    # Worker metrics
    active_workers: int = 0
    idle_workers: int = 0
    
    # Queue metrics
    queue_depth: int = 0
    dlq_depth: int = 0
    
    # Resource metrics
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """
    Collects and aggregates execution metrics
    
    Features:
    - Execution success/failure rates
    - Performance metrics (duration, percentiles)
    - Step-level metrics
    - Queue metrics
    - SLA compliance tracking
    - Real-time system metrics
    """
    
    def __init__(self, repository: ExecutionRepository):
        self.repository = repository
        self._metrics_cache: Dict[str, ExecutionMetrics] = {}
        self._lock = asyncio.Lock()
        logger.info("MetricsCollector initialized")
    
    async def collect_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> ExecutionMetrics:
        """
        Collect execution metrics for a time period
        
        Args:
            start_time: Start of period (default: 24 hours ago)
            end_time: End of period (default: now)
            
        Returns:
            ExecutionMetrics
        """
        try:
            # Default to last 24 hours
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Check cache
            cache_key = f"{start_time.isoformat()}_{end_time.isoformat()}"
            if cache_key in self._metrics_cache:
                return self._metrics_cache[cache_key]
            
            # Fetch executions for the period
            executions = await self.repository.list_executions(
                created_after=start_time,
                created_before=end_time,
                limit=10000,  # Large limit for metrics
            )
            
            if not executions:
                return ExecutionMetrics(
                    period_start=start_time,
                    period_end=end_time,
                )
            
            # Initialize metrics
            metrics = ExecutionMetrics(
                period_start=start_time,
                period_end=end_time,
                total_executions=len(executions),
            )
            
            # Collect execution-level metrics
            durations = []
            queue_times = []
            total_steps = 0
            completed_steps = 0
            failed_steps = 0
            sla_violations = 0
            
            for execution in executions:
                # Count by status
                if execution.status == ExecutionStatus.COMPLETED:
                    metrics.completed_executions += 1
                elif execution.status == ExecutionStatus.FAILED:
                    metrics.failed_executions += 1
                elif execution.status == ExecutionStatus.CANCELLED:
                    metrics.cancelled_executions += 1
                elif execution.status == ExecutionStatus.TIMEOUT:
                    metrics.timeout_executions += 1
                    sla_violations += 1
                
                # Duration metrics
                if execution.started_at and execution.completed_at:
                    duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
                    durations.append(duration_ms)
                
                # Queue time metrics
                if execution.queued_at and execution.started_at:
                    queue_time_ms = int((execution.started_at - execution.queued_at).total_seconds() * 1000)
                    queue_times.append(queue_time_ms)
                
                # Step metrics
                steps = await self.repository.get_execution_steps(execution.execution_id)
                total_steps += len(steps)
                for step in steps:
                    if step.status == ExecutionStatus.COMPLETED:
                        completed_steps += 1
                    elif step.status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]:
                        failed_steps += 1
            
            # Calculate success rate
            if metrics.total_executions > 0:
                metrics.success_rate = (metrics.completed_executions / metrics.total_executions) * 100
            
            # Calculate duration metrics
            if durations:
                durations.sort()
                metrics.avg_duration_ms = sum(durations) / len(durations)
                metrics.min_duration_ms = durations[0]
                metrics.max_duration_ms = durations[-1]
                metrics.p50_duration_ms = self._percentile(durations, 50)
                metrics.p95_duration_ms = self._percentile(durations, 95)
                metrics.p99_duration_ms = self._percentile(durations, 99)
            
            # Calculate queue metrics
            if queue_times:
                metrics.avg_queue_time_ms = sum(queue_times) / len(queue_times)
                metrics.max_queue_time_ms = max(queue_times)
            
            # Calculate step metrics
            metrics.total_steps = total_steps
            metrics.completed_steps = completed_steps
            metrics.failed_steps = failed_steps
            if metrics.total_executions > 0:
                metrics.avg_steps_per_execution = total_steps / metrics.total_executions
            
            # Calculate SLA compliance
            metrics.sla_violations = sla_violations
            if metrics.total_executions > 0:
                metrics.sla_compliance_rate = ((metrics.total_executions - sla_violations) / metrics.total_executions) * 100
            
            # Cache metrics
            async with self._lock:
                self._metrics_cache[cache_key] = metrics
            
            logger.info(f"Collected metrics: {metrics.total_executions} executions, {metrics.success_rate:.1f}% success rate")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}", exc_info=True)
            return ExecutionMetrics(
                period_start=start_time or datetime.utcnow() - timedelta(hours=24),
                period_end=end_time or datetime.utcnow(),
            )
    
    async def collect_step_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[StepMetrics]:
        """
        Collect metrics by step type
        
        Args:
            start_time: Start of period
            end_time: End of period
            
        Returns:
            List of StepMetrics
        """
        try:
            # Default to last 24 hours
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Fetch executions
            executions = await self.repository.list_executions(
                created_after=start_time,
                created_before=end_time,
                limit=10000,
            )
            
            # Aggregate by step type
            step_data: Dict[str, Dict[str, Any]] = {}
            
            for execution in executions:
                steps = await self.repository.get_execution_steps(execution.execution_id)
                for step in steps:
                    step_type = step.step_type
                    if step_type not in step_data:
                        step_data[step_type] = {
                            "total": 0,
                            "success": 0,
                            "failure": 0,
                            "durations": [],
                        }
                    
                    step_data[step_type]["total"] += 1
                    
                    if step.status == ExecutionStatus.COMPLETED:
                        step_data[step_type]["success"] += 1
                    elif step.status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]:
                        step_data[step_type]["failure"] += 1
                    
                    if step.duration_ms:
                        step_data[step_type]["durations"].append(step.duration_ms)
            
            # Build metrics
            metrics_list = []
            for step_type, data in step_data.items():
                avg_duration = None
                if data["durations"]:
                    avg_duration = sum(data["durations"]) / len(data["durations"])
                
                success_rate = 0.0
                if data["total"] > 0:
                    success_rate = (data["success"] / data["total"]) * 100
                
                metrics_list.append(StepMetrics(
                    step_type=step_type,
                    total_executions=data["total"],
                    success_count=data["success"],
                    failure_count=data["failure"],
                    success_rate=success_rate,
                    avg_duration_ms=avg_duration,
                ))
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Error collecting step metrics: {e}", exc_info=True)
            return []
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """
        Collect real-time system metrics
        
        Returns:
            SystemMetrics
        """
        try:
            metrics = SystemMetrics()
            
            # Count active executions
            active = await self.repository.list_executions(
                status=[ExecutionStatus.RUNNING],
                limit=1000,
            )
            metrics.active_executions = len(active)
            
            # Count queued executions
            queued = await self.repository.list_executions(
                status=[ExecutionStatus.QUEUED],
                limit=1000,
            )
            metrics.queued_executions = len(queued)
            
            # Queue depth (from queue table)
            # Note: This would need queue manager integration
            metrics.queue_depth = metrics.queued_executions
            
            # DLQ depth (from DLQ table)
            # Note: This would need DLQ handler integration
            metrics.dlq_depth = 0
            
            logger.debug(f"System metrics: {metrics.active_executions} active, {metrics.queued_executions} queued")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}", exc_info=True)
            return SystemMetrics()
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive metrics summary
        
        Returns:
            Dictionary with all metrics
        """
        try:
            # Collect different time periods
            last_hour = await self.collect_metrics(
                start_time=datetime.utcnow() - timedelta(hours=1),
            )
            last_24h = await self.collect_metrics(
                start_time=datetime.utcnow() - timedelta(hours=24),
            )
            last_7d = await self.collect_metrics(
                start_time=datetime.utcnow() - timedelta(days=7),
            )
            
            # Collect step metrics
            step_metrics = await self.collect_step_metrics()
            
            # Collect system metrics
            system_metrics = await self.collect_system_metrics()
            
            return {
                "last_hour": last_hour.model_dump(),
                "last_24h": last_24h.model_dump(),
                "last_7d": last_7d.model_dump(),
                "step_metrics": [m.model_dump() for m in step_metrics],
                "system_metrics": system_metrics.model_dump(),
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}", exc_info=True)
            return {}
    
    async def clear_cache(self):
        """Clear metrics cache"""
        async with self._lock:
            self._metrics_cache.clear()
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data"""
        if not data:
            return 0.0
        index = int((percentile / 100) * len(data))
        if index >= len(data):
            index = len(data) - 1
        return data[index]
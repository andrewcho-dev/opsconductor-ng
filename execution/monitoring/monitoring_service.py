"""
Monitoring Service - Health checks and performance monitoring
Provides health checks, alerting, and system monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from execution.monitoring.metrics_collector import MetricsCollector, SystemMetrics
from execution.monitoring.progress_tracker import ProgressTracker
from execution.monitoring.event_emitter import EventEmitter, EventType
from execution.repository import ExecutionRepository


logger = logging.getLogger(__name__)


# ============================================================================
# MODELS
# ============================================================================

class HealthStatus(str, Enum):
    """Health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status for a component"""
    component: str
    status: HealthStatus
    message: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)


class SystemHealth(BaseModel):
    """Overall system health"""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: List[ComponentHealth] = Field(default_factory=list)
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        return self.status == HealthStatus.HEALTHY


class Alert(BaseModel):
    """System alert"""
    alert_id: str
    severity: str  # "info", "warning", "error", "critical"
    title: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    component: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MONITORING SERVICE
# ============================================================================

class MonitoringService:
    """
    Monitoring service for health checks and alerting
    
    Features:
    - Health checks for all components
    - Performance monitoring
    - Alert generation
    - SLA violation detection
    - Resource usage monitoring
    - Automatic health checks
    """
    
    def __init__(
        self,
        repository: ExecutionRepository,
        metrics_collector: MetricsCollector,
        progress_tracker: ProgressTracker,
        event_emitter: EventEmitter,
    ):
        self.repository = repository
        self.metrics_collector = metrics_collector
        self.progress_tracker = progress_tracker
        self.event_emitter = event_emitter
        
        self._alerts: List[Alert] = []
        self._health_cache: Optional[SystemHealth] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info("MonitoringService initialized")
    
    async def start(self):
        """Start monitoring service"""
        if not self._health_check_task:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("Monitoring service started")
    
    async def stop(self):
        """Stop monitoring service"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Monitoring service stopped")
    
    async def check_health(self) -> SystemHealth:
        """
        Perform comprehensive health check
        
        Returns:
            SystemHealth
        """
        try:
            components = []
            
            # Check database
            db_health = await self._check_database_health()
            components.append(db_health)
            
            # Check execution engine
            engine_health = await self._check_execution_engine_health()
            components.append(engine_health)
            
            # Check queue
            queue_health = await self._check_queue_health()
            components.append(queue_health)
            
            # Check metrics collector
            metrics_health = await self._check_metrics_health()
            components.append(metrics_health)
            
            # Determine overall status
            overall_status = HealthStatus.HEALTHY
            unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
            degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)
            
            if unhealthy_count > 0:
                overall_status = HealthStatus.UNHEALTHY
            elif degraded_count > 0:
                overall_status = HealthStatus.DEGRADED
            
            health = SystemHealth(
                status=overall_status,
                components=components,
            )
            
            # Cache health
            async with self._lock:
                self._health_cache = health
            
            # Emit health event
            from execution.monitoring.event_emitter import ExecutionEvent
            await self.event_emitter.emit(ExecutionEvent(
                event_type=EventType.SYSTEM_HEALTH,
                execution_id=UUID("00000000-0000-0000-0000-000000000000"),  # System event
                data={
                    "status": overall_status.value,
                    "components": [c.model_dump() for c in components],
                },
            ))
            
            logger.debug(f"Health check: {overall_status}")
            return health
            
        except Exception as e:
            logger.error(f"Error checking health: {e}", exc_info=True)
            return SystemHealth(
                status=HealthStatus.UNHEALTHY,
                components=[ComponentHealth(
                    component="monitoring",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                )],
            )
    
    async def get_health(self) -> SystemHealth:
        """Get cached health status"""
        if self._health_cache:
            return self._health_cache
        return await self.check_health()
    
    async def check_sla_violations(self) -> List[Alert]:
        """
        Check for SLA violations
        
        Returns:
            List of alerts
        """
        try:
            alerts = []
            
            # Get metrics for last hour
            metrics = await self.metrics_collector.collect_metrics(
                start_time=datetime.utcnow() - timedelta(hours=1),
            )
            
            # Check timeout rate
            if metrics.total_executions > 0:
                timeout_rate = (metrics.timeout_executions / metrics.total_executions) * 100
                if timeout_rate > 10:  # More than 10% timeouts
                    alert = Alert(
                        alert_id=f"sla_timeout_{datetime.utcnow().isoformat()}",
                        severity="error",
                        title="High Timeout Rate",
                        message=f"Timeout rate is {timeout_rate:.1f}% (threshold: 10%)",
                        component="execution_engine",
                        details={"timeout_rate": timeout_rate, "timeouts": metrics.timeout_executions},
                    )
                    alerts.append(alert)
                    await self._add_alert(alert)
            
            # Check failure rate
            if metrics.total_executions > 0:
                failure_rate = 100 - metrics.success_rate
                if failure_rate > 20:  # More than 20% failures
                    alert = Alert(
                        alert_id=f"sla_failure_{datetime.utcnow().isoformat()}",
                        severity="warning",
                        title="High Failure Rate",
                        message=f"Failure rate is {failure_rate:.1f}% (threshold: 20%)",
                        component="execution_engine",
                        details={"failure_rate": failure_rate, "failures": metrics.failed_executions},
                    )
                    alerts.append(alert)
                    await self._add_alert(alert)
            
            # Check queue depth
            system_metrics = await self.metrics_collector.collect_system_metrics()
            if system_metrics.queue_depth > 100:
                alert = Alert(
                    alert_id=f"queue_depth_{datetime.utcnow().isoformat()}",
                    severity="warning",
                    title="High Queue Depth",
                    message=f"Queue depth is {system_metrics.queue_depth} (threshold: 100)",
                    component="queue",
                    details={"queue_depth": system_metrics.queue_depth},
                )
                alerts.append(alert)
                await self._add_alert(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking SLA violations: {e}", exc_info=True)
            return []
    
    async def get_alerts(self, severity: Optional[str] = None, limit: int = 100) -> List[Alert]:
        """
        Get recent alerts
        
        Args:
            severity: Optional severity filter
            limit: Maximum number of alerts
            
        Returns:
            List of alerts
        """
        async with self._lock:
            alerts = self._alerts.copy()
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return alerts[:limit]
    
    async def clear_alerts(self):
        """Clear all alerts"""
        async with self._lock:
            self._alerts.clear()
    
    async def _check_database_health(self) -> ComponentHealth:
        """Check database health"""
        try:
            # Try to query database
            executions = await self.repository.list_executions(limit=1)
            
            return ComponentHealth(
                component="database",
                status=HealthStatus.HEALTHY,
                message="Database is responsive",
                details={"query_successful": True},
            )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}",
            )
    
    async def _check_execution_engine_health(self) -> ComponentHealth:
        """Check execution engine health"""
        try:
            # Get active executions
            active = await self.progress_tracker.get_active_executions()
            
            # Check if any are stuck (running > 1 hour)
            stuck_count = 0
            for progress in active:
                if progress.elapsed_ms and progress.elapsed_ms > 3600000:  # 1 hour
                    stuck_count += 1
            
            if stuck_count > 0:
                return ComponentHealth(
                    component="execution_engine",
                    status=HealthStatus.DEGRADED,
                    message=f"{stuck_count} executions running > 1 hour",
                    details={"active_executions": len(active), "stuck_executions": stuck_count},
                )
            
            return ComponentHealth(
                component="execution_engine",
                status=HealthStatus.HEALTHY,
                message=f"{len(active)} active executions",
                details={"active_executions": len(active)},
            )
        except Exception as e:
            logger.error(f"Execution engine health check failed: {e}")
            return ComponentHealth(
                component="execution_engine",
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
            )
    
    async def _check_queue_health(self) -> ComponentHealth:
        """Check queue health"""
        try:
            # Get system metrics
            metrics = await self.metrics_collector.collect_system_metrics()
            
            # Check queue depth
            if metrics.queue_depth > 1000:
                return ComponentHealth(
                    component="queue",
                    status=HealthStatus.DEGRADED,
                    message=f"High queue depth: {metrics.queue_depth}",
                    details={"queue_depth": metrics.queue_depth, "dlq_depth": metrics.dlq_depth},
                )
            
            return ComponentHealth(
                component="queue",
                status=HealthStatus.HEALTHY,
                message=f"Queue depth: {metrics.queue_depth}",
                details={"queue_depth": metrics.queue_depth, "dlq_depth": metrics.dlq_depth},
            )
        except Exception as e:
            logger.error(f"Queue health check failed: {e}")
            return ComponentHealth(
                component="queue",
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
            )
    
    async def _check_metrics_health(self) -> ComponentHealth:
        """Check metrics collector health"""
        try:
            # Try to collect metrics
            metrics = await self.metrics_collector.collect_metrics(
                start_time=datetime.utcnow() - timedelta(minutes=5),
            )
            
            return ComponentHealth(
                component="metrics",
                status=HealthStatus.HEALTHY,
                message="Metrics collection working",
                details={"executions_last_5min": metrics.total_executions},
            )
        except Exception as e:
            logger.error(f"Metrics health check failed: {e}")
            return ComponentHealth(
                component="metrics",
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
            )
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.check_health()
                await self.check_sla_violations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)
    
    async def _add_alert(self, alert: Alert):
        """Add alert to list"""
        async with self._lock:
            self._alerts.append(alert)
            # Keep only last 1000 alerts
            if len(self._alerts) > 1000:
                self._alerts = self._alerts[-1000:]
        
        # Emit alert event
        from execution.monitoring.event_emitter import ExecutionEvent
        await self.event_emitter.emit(ExecutionEvent(
            event_type=EventType.SYSTEM_ALERT,
            execution_id=UUID("00000000-0000-0000-0000-000000000000"),
            data=alert.model_dump(),
        ))
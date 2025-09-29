"""
📊 COMPREHENSIVE METRICS COLLECTION SYSTEM
Ollama Universal Intelligent Operations Engine (OUIOE)

Advanced metrics collection for production monitoring and observability.
Collects system, application, and business metrics for complete visibility.

Key Features:
- System resource metrics (CPU, memory, disk, network)
- Application performance metrics (response times, throughput, errors)
- Business metrics (requests processed, decisions made, workflows executed)
- Custom metrics with labels and dimensions
- Time-series data storage with Redis
- Prometheus-compatible metrics export
- Real-time metric streaming
- Metric aggregation and rollups
"""

import asyncio
import structlog
import psutil
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
from collections import defaultdict, deque
import threading
import weakref

logger = structlog.get_logger()

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class MetricUnit(Enum):
    """Metric units"""
    BYTES = "bytes"
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    PERCENT = "percent"
    COUNT = "count"
    REQUESTS_PER_SECOND = "rps"
    OPERATIONS_PER_SECOND = "ops"

@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: MetricUnit = MetricUnit.COUNT
    metric_type: MetricType = MetricType.GAUGE

@dataclass
class MetricSeries:
    """Time series of metric points"""
    name: str
    metric_type: MetricType
    unit: MetricUnit
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)
    
    def add_point(self, value: float, timestamp: Optional[datetime] = None, labels: Optional[Dict[str, str]] = None):
        """Add a metric point to the series"""
        if timestamp is None:
            timestamp = datetime.now()
        
        point_labels = {**self.labels}
        if labels:
            point_labels.update(labels)
            
        point = MetricPoint(
            name=self.name,
            value=value,
            timestamp=timestamp,
            labels=point_labels,
            unit=self.unit,
            metric_type=self.metric_type
        )
        self.points.append(point)

class MetricsCollector:
    """
    📊 COMPREHENSIVE METRICS COLLECTION SYSTEM
    
    Collects, stores, and exports metrics for complete system observability.
    """
    
    def __init__(self, redis_host: str = "redis", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        
        # Metric storage
        self.metrics: Dict[str, MetricSeries] = {}
        self.metric_lock = threading.RLock()
        
        # Collection settings
        self.collection_interval = 5.0  # seconds
        self.retention_period = timedelta(hours=24)
        self.is_collecting = False
        self.collection_task: Optional[asyncio.Task] = None
        
        # System metrics tracking
        self.last_cpu_times = None
        self.last_network_io = None
        self.last_disk_io = None
        
        # Application metrics
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)
        self.active_requests = 0
        
        logger.info("📊 Metrics Collector initialized")
    
    async def initialize(self):
        """Initialize metrics collection system"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Initialize core metrics
            await self._initialize_core_metrics()
            
            # Start collection
            await self.start_collection()
            
            logger.info("📊 Metrics collection system initialized")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to initialize metrics collector", error=str(e))
            return False
    
    async def _initialize_core_metrics(self):
        """Initialize core system and application metrics"""
        
        # System resource metrics
        self._register_metric("system_cpu_usage_percent", MetricType.GAUGE, MetricUnit.PERCENT)
        self._register_metric("system_memory_usage_bytes", MetricType.GAUGE, MetricUnit.BYTES)
        self._register_metric("system_memory_usage_percent", MetricType.GAUGE, MetricUnit.PERCENT)
        self._register_metric("system_disk_usage_bytes", MetricType.GAUGE, MetricUnit.BYTES)
        self._register_metric("system_disk_usage_percent", MetricType.GAUGE, MetricUnit.PERCENT)
        self._register_metric("system_network_bytes_sent", MetricType.COUNTER, MetricUnit.BYTES)
        self._register_metric("system_network_bytes_received", MetricType.COUNTER, MetricUnit.BYTES)
        self._register_metric("system_load_average", MetricType.GAUGE, MetricUnit.COUNT)
        
        # Application performance metrics
        self._register_metric("app_requests_total", MetricType.COUNTER, MetricUnit.COUNT)
        self._register_metric("app_requests_per_second", MetricType.GAUGE, MetricUnit.REQUESTS_PER_SECOND)
        self._register_metric("app_errors_total", MetricType.COUNTER, MetricUnit.COUNT)
        self._register_metric("app_error_rate_percent", MetricType.GAUGE, MetricUnit.PERCENT)
        self._register_metric("app_response_time_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS)
        self._register_metric("app_active_requests", MetricType.GAUGE, MetricUnit.COUNT)
        
        # AI/LLM specific metrics
        self._register_metric("ai_decisions_total", MetricType.COUNTER, MetricUnit.COUNT)
        self._register_metric("ai_decision_time_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS)
        self._register_metric("ai_workflows_executed", MetricType.COUNTER, MetricUnit.COUNT)
        self._register_metric("ai_workflow_execution_time_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS)
        self._register_metric("ai_conversations_active", MetricType.GAUGE, MetricUnit.COUNT)
        self._register_metric("ai_thinking_stream_events", MetricType.COUNTER, MetricUnit.COUNT)
        
        # Service integration metrics
        self._register_metric("service_calls_total", MetricType.COUNTER, MetricUnit.COUNT)
        self._register_metric("service_call_duration_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS)
        self._register_metric("service_errors_total", MetricType.COUNTER, MetricUnit.COUNT)
        
        # Database metrics
        self._register_metric("db_connections_active", MetricType.GAUGE, MetricUnit.COUNT)
        self._register_metric("db_query_duration_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS)
        self._register_metric("db_queries_total", MetricType.COUNTER, MetricUnit.COUNT)
        
        logger.info("📊 Core metrics initialized", count=len(self.metrics))
    
    def _register_metric(self, name: str, metric_type: MetricType, unit: MetricUnit, labels: Optional[Dict[str, str]] = None):
        """Register a new metric"""
        with self.metric_lock:
            if name not in self.metrics:
                self.metrics[name] = MetricSeries(
                    name=name,
                    metric_type=metric_type,
                    unit=unit,
                    labels=labels or {}
                )
    
    async def start_collection(self):
        """Start metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("📊 Metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("📊 Metrics collection stopped")
    
    async def _collection_loop(self):
        """Main metrics collection loop"""
        while self.is_collecting:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._store_metrics_to_redis()
                await self._cleanup_old_metrics()
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ Error in metrics collection loop", error=str(e))
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.record_metric("system_cpu_usage_percent", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric("system_memory_usage_bytes", memory.used)
            self.record_metric("system_memory_usage_percent", memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric("system_disk_usage_bytes", disk.used)
            self.record_metric("system_disk_usage_percent", (disk.used / disk.total) * 100)
            
            # Network I/O
            network = psutil.net_io_counters()
            self.record_metric("system_network_bytes_sent", network.bytes_sent)
            self.record_metric("system_network_bytes_received", network.bytes_recv)
            
            # Load average
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            self.record_metric("system_load_average", load_avg)
            
        except Exception as e:
            logger.error("❌ Error collecting system metrics", error=str(e))
    
    async def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        try:
            # Calculate requests per second
            current_time = time.time()
            recent_requests = sum(1 for t in self.response_times if current_time - t < 60)
            rps = recent_requests / 60.0
            self.record_metric("app_requests_per_second", rps)
            
            # Error rate
            total_requests = max(self.request_count, 1)
            error_rate = (self.error_count / total_requests) * 100
            self.record_metric("app_error_rate_percent", error_rate)
            
            # Active requests
            self.record_metric("app_active_requests", self.active_requests)
            
            # Response time statistics
            if self.response_times:
                recent_times = [t for t in self.response_times if current_time - t < 300]  # Last 5 minutes
                if recent_times:
                    avg_response_time = sum(recent_times) / len(recent_times) * 1000  # Convert to ms
                    self.record_metric("app_response_time_ms", avg_response_time)
            
        except Exception as e:
            logger.error("❌ Error collecting application metrics", error=str(e))
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric value"""
        with self.metric_lock:
            if name in self.metrics:
                self.metrics[name].add_point(value, labels=labels)
            else:
                logger.warning("📊 Attempted to record unknown metric", metric=name)
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self.metric_lock:
            if name in self.metrics and self.metrics[name].metric_type == MetricType.COUNTER:
                current_value = 0.0
                if self.metrics[name].points:
                    current_value = self.metrics[name].points[-1].value
                self.metrics[name].add_point(current_value + value, labels=labels)
            else:
                logger.warning("📊 Attempted to increment non-counter metric", metric=name)
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        self.record_metric(name, value, labels)
    
    async def _store_metrics_to_redis(self):
        """Store metrics to Redis for persistence"""
        if not self.redis_client:
            return
        
        try:
            pipeline = self.redis_client.pipeline()
            current_time = datetime.now()
            
            with self.metric_lock:
                for metric_name, metric_series in self.metrics.items():
                    if metric_series.points:
                        # Store latest point
                        latest_point = metric_series.points[-1]
                        key = f"metrics:{metric_name}:latest"
                        value = {
                            "value": latest_point.value,
                            "timestamp": latest_point.timestamp.isoformat(),
                            "labels": latest_point.labels,
                            "unit": latest_point.unit.value,
                            "type": latest_point.metric_type.value
                        }
                        pipeline.set(key, json.dumps(value))
                        pipeline.expire(key, int(self.retention_period.total_seconds()))
                        
                        # Store time series data
                        ts_key = f"metrics:{metric_name}:timeseries"
                        for point in list(metric_series.points)[-10:]:  # Store last 10 points
                            ts_value = {
                                "value": point.value,
                                "timestamp": point.timestamp.isoformat(),
                                "labels": point.labels
                            }
                            pipeline.zadd(ts_key, {json.dumps(ts_value): point.timestamp.timestamp()})
                        
                        # Clean old time series data
                        cutoff_time = (current_time - self.retention_period).timestamp()
                        pipeline.zremrangebyscore(ts_key, 0, cutoff_time)
                        pipeline.expire(ts_key, int(self.retention_period.total_seconds()))
            
            await pipeline.execute()
            
        except Exception as e:
            logger.error("❌ Error storing metrics to Redis", error=str(e))
    
    async def _cleanup_old_metrics(self):
        """Clean up old metric data"""
        cutoff_time = datetime.now() - self.retention_period
        
        with self.metric_lock:
            for metric_series in self.metrics.values():
                # Remove old points
                while metric_series.points and metric_series.points[0].timestamp < cutoff_time:
                    metric_series.points.popleft()
    
    async def get_metric_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get the latest value for a metric"""
        with self.metric_lock:
            if name in self.metrics and self.metrics[name].points:
                latest_point = self.metrics[name].points[-1]
                if labels is None or latest_point.labels == labels:
                    return latest_point.value
        return None
    
    async def get_metric_history(self, name: str, duration: timedelta = timedelta(hours=1)) -> List[MetricPoint]:
        """Get metric history for a specified duration"""
        cutoff_time = datetime.now() - duration
        
        with self.metric_lock:
            if name in self.metrics:
                return [point for point in self.metrics[name].points if point.timestamp >= cutoff_time]
        return []
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        summary = {
            "total_metrics": len(self.metrics),
            "collection_interval": self.collection_interval,
            "retention_period": str(self.retention_period),
            "is_collecting": self.is_collecting,
            "metrics": {}
        }
        
        with self.metric_lock:
            for name, metric_series in self.metrics.items():
                if metric_series.points:
                    latest_point = metric_series.points[-1]
                    summary["metrics"][name] = {
                        "latest_value": latest_point.value,
                        "latest_timestamp": latest_point.timestamp.isoformat(),
                        "unit": latest_point.unit.value,
                        "type": metric_series.metric_type.value,
                        "points_count": len(metric_series.points)
                    }
        
        return summary
    
    async def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        with self.metric_lock:
            for name, metric_series in self.metrics.items():
                if metric_series.points:
                    latest_point = metric_series.points[-1]
                    
                    # Add metric help and type
                    lines.append(f"# HELP {name} {metric_series.unit.value}")
                    lines.append(f"# TYPE {name} {metric_series.metric_type.value}")
                    
                    # Add metric value with labels
                    labels_str = ""
                    if latest_point.labels:
                        label_pairs = [f'{k}="{v}"' for k, v in latest_point.labels.items()]
                        labels_str = "{" + ",".join(label_pairs) + "}"
                    
                    lines.append(f"{name}{labels_str} {latest_point.value}")
        
        return "\n".join(lines)
    
    # Context managers for request tracking
    def track_request(self):
        """Context manager for tracking request metrics"""
        return RequestTracker(self)
    
    def track_ai_operation(self, operation_type: str):
        """Context manager for tracking AI operation metrics"""
        return AIOperationTracker(self, operation_type)

class RequestTracker:
    """Context manager for tracking HTTP request metrics"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.collector.active_requests += 1
        self.collector.increment_counter("app_requests_total")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.response_times.append(self.start_time)
            self.collector.record_histogram("app_response_time_ms", duration * 1000)
        
        self.collector.active_requests -= 1
        
        if exc_type is not None:
            self.collector.error_count += 1
            self.collector.increment_counter("app_errors_total")

class AIOperationTracker:
    """Context manager for tracking AI operation metrics"""
    
    def __init__(self, collector: MetricsCollector, operation_type: str):
        self.collector = collector
        self.operation_type = operation_type
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            if self.operation_type == "decision":
                self.collector.increment_counter("ai_decisions_total")
                self.collector.record_histogram("ai_decision_time_ms", duration * 1000)
            elif self.operation_type == "workflow":
                self.collector.increment_counter("ai_workflows_executed")
                self.collector.record_histogram("ai_workflow_execution_time_ms", duration * 1000)

# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None

async def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        await _metrics_collector.initialize()
    return _metrics_collector

async def initialize_metrics_system() -> bool:
    """Initialize the global metrics system"""
    try:
        collector = await get_metrics_collector()
        logger.info("📊 Global metrics system initialized")
        return True
    except Exception as e:
        logger.error("❌ Failed to initialize global metrics system", error=str(e))
        return False
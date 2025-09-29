"""
🔍 DISTRIBUTED TRACING SYSTEM
Ollama Universal Intelligent Operations Engine (OUIOE)

Comprehensive distributed tracing for request flow tracking and performance analysis.
Provides end-to-end visibility across all services and components.

Key Features:
- OpenTelemetry-compatible tracing
- Automatic span creation and correlation
- Cross-service trace propagation
- Performance bottleneck identification
- Error tracking and correlation
- Custom span attributes and events
- Trace sampling and filtering
- Integration with monitoring dashboards
"""

import asyncio
import structlog
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
from collections import defaultdict
import threading
import contextvars
import functools
import inspect

logger = structlog.get_logger()

class SpanKind(Enum):
    """Span kinds following OpenTelemetry specification"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"

class SpanStatus(Enum):
    """Span status"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class SpanEvent:
    """Span event for additional context"""
    name: str
    timestamp: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    kind: SpanKind = SpanKind.INTERNAL
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Trace:
    """Complete trace containing multiple spans"""
    trace_id: str
    spans: List[Span]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    service_count: int = 0
    span_count: int = 0
    error_count: int = 0
    root_span: Optional[Span] = None

class TraceContext:
    """Trace context for correlation"""
    
    def __init__(self, trace_id: str, span_id: str, parent_span_id: Optional[str] = None):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.baggage: Dict[str, str] = {}
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for propagation"""
        headers = {
            "X-Trace-Id": self.trace_id,
            "X-Span-Id": self.span_id
        }
        
        if self.parent_span_id:
            headers["X-Parent-Span-Id"] = self.parent_span_id
        
        if self.baggage:
            headers["X-Trace-Baggage"] = json.dumps(self.baggage)
        
        return headers
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> Optional['TraceContext']:
        """Create from HTTP headers"""
        trace_id = headers.get("X-Trace-Id")
        span_id = headers.get("X-Span-Id")
        
        if not trace_id or not span_id:
            return None
        
        context = cls(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=headers.get("X-Parent-Span-Id")
        )
        
        baggage_header = headers.get("X-Trace-Baggage")
        if baggage_header:
            try:
                context.baggage = json.loads(baggage_header)
            except:
                pass
        
        return context

# Context variable for current trace context
current_trace_context: contextvars.ContextVar[Optional[TraceContext]] = contextvars.ContextVar(
    'current_trace_context', default=None
)

class TracingSystem:
    """
    🔍 DISTRIBUTED TRACING SYSTEM
    
    Provides comprehensive distributed tracing capabilities for request flow tracking.
    """
    
    def __init__(self, service_name: str, redis_host: str = "redis", redis_port: int = 6379):
        self.service_name = service_name
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        
        # Span storage
        self.active_spans: Dict[str, Span] = {}
        self.completed_traces: Dict[str, Trace] = {}
        
        # Configuration
        self.sampling_rate = 1.0  # Sample 100% by default
        self.max_trace_duration = timedelta(hours=1)
        self.max_spans_per_trace = 1000
        
        # Metrics
        self.trace_count = 0
        self.span_count = 0
        self.error_count = 0
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.export_task: Optional[asyncio.Task] = None
        
        logger.info("🔍 Tracing System initialized", service=service_name)
    
    async def initialize(self):
        """Initialize tracing system"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Start background tasks
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.export_task = asyncio.create_task(self._export_loop())
            
            logger.info("🔍 Tracing system initialized")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to initialize tracing system", error=str(e))
            return False
    
    def start_trace(self, operation_name: str, kind: SpanKind = SpanKind.INTERNAL, 
                   parent_context: Optional[TraceContext] = None) -> 'SpanContext':
        """Start a new trace or continue existing one"""
        
        # Check if we should sample this trace
        if not self._should_sample():
            return NoOpSpanContext()
        
        # Generate IDs
        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None
        
        span_id = self._generate_span_id()
        
        # Create span
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=self.service_name,
            start_time=datetime.now(),
            kind=kind,
            attributes={
                "service.name": self.service_name,
                "span.kind": kind.value
            }
        )
        
        # Store active span
        self.active_spans[span_id] = span
        self.span_count += 1
        
        # Create trace context
        trace_context = TraceContext(trace_id, span_id, parent_span_id)
        
        # Set current context
        current_trace_context.set(trace_context)
        
        logger.debug("🔍 Span started", trace_id=trace_id, span_id=span_id, operation=operation_name)
        
        return SpanContext(self, span, trace_context)
    
    def get_current_span(self) -> Optional[Span]:
        """Get current active span"""
        context = current_trace_context.get()
        if context:
            return self.active_spans.get(context.span_id)
        return None
    
    def get_current_trace_context(self) -> Optional[TraceContext]:
        """Get current trace context"""
        return current_trace_context.get()
    
    async def finish_span(self, span: Span, status: SpanStatus = SpanStatus.OK, 
                         error: Optional[Exception] = None):
        """Finish a span"""
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        
        if error:
            span.status = SpanStatus.ERROR
            span.attributes["error"] = True
            span.attributes["error.message"] = str(error)
            span.attributes["error.type"] = type(error).__name__
            self.error_count += 1
        
        # Remove from active spans
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]
        
        # Store completed span
        await self._store_span(span)
        
        # Check if trace is complete
        await self._check_trace_completion(span.trace_id)
        
        logger.debug("🔍 Span finished", 
                    trace_id=span.trace_id, 
                    span_id=span.span_id, 
                    duration=span.duration_ms,
                    status=status.value)
    
    async def _store_span(self, span: Span):
        """Store span in Redis"""
        if not self.redis_client:
            return
        
        try:
            span_data = {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "operation_name": span.operation_name,
                "service_name": span.service_name,
                "start_time": span.start_time.isoformat(),
                "end_time": span.end_time.isoformat() if span.end_time else None,
                "duration_ms": span.duration_ms,
                "status": span.status.value,
                "kind": span.kind.value,
                "attributes": span.attributes,
                "events": [
                    {
                        "name": event.name,
                        "timestamp": event.timestamp.isoformat(),
                        "attributes": event.attributes
                    } for event in span.events
                ],
                "tags": span.tags,
                "logs": span.logs
            }
            
            # Store span
            await self.redis_client.set(
                f"span:{span.span_id}",
                json.dumps(span_data),
                ex=int(self.max_trace_duration.total_seconds())
            )
            
            # Add to trace index
            await self.redis_client.sadd(f"trace:{span.trace_id}:spans", span.span_id)
            await self.redis_client.expire(f"trace:{span.trace_id}:spans", 
                                         int(self.max_trace_duration.total_seconds()))
            
        except Exception as e:
            logger.error("❌ Error storing span", error=str(e))
    
    async def _check_trace_completion(self, trace_id: str):
        """Check if trace is complete and build trace object"""
        try:
            # Get all spans for trace
            span_ids = await self.redis_client.smembers(f"trace:{trace_id}:spans")
            
            if not span_ids:
                return
            
            # Check if any spans are still active
            active_spans_in_trace = [
                span for span in self.active_spans.values() 
                if span.trace_id == trace_id
            ]
            
            if active_spans_in_trace:
                return  # Trace still has active spans
            
            # Build complete trace
            spans = []
            for span_id in span_ids:
                span_data = await self.redis_client.get(f"span:{span_id}")
                if span_data:
                    data = json.loads(span_data)
                    span = self._reconstruct_span(data)
                    spans.append(span)
            
            if spans:
                trace = self._build_trace(trace_id, spans)
                self.completed_traces[trace_id] = trace
                self.trace_count += 1
                
                logger.info("🔍 Trace completed", 
                           trace_id=trace_id, 
                           spans=len(spans),
                           duration=trace.duration_ms,
                           services=trace.service_count)
        
        except Exception as e:
            logger.error("❌ Error checking trace completion", error=str(e))
    
    def _reconstruct_span(self, data: Dict[str, Any]) -> Span:
        """Reconstruct span from stored data"""
        span = Span(
            trace_id=data["trace_id"],
            span_id=data["span_id"],
            parent_span_id=data.get("parent_span_id"),
            operation_name=data["operation_name"],
            service_name=data["service_name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration_ms=data.get("duration_ms"),
            status=SpanStatus(data["status"]),
            kind=SpanKind(data["kind"]),
            attributes=data.get("attributes", {}),
            tags=data.get("tags", {}),
            logs=data.get("logs", [])
        )
        
        # Reconstruct events
        for event_data in data.get("events", []):
            event = SpanEvent(
                name=event_data["name"],
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                attributes=event_data.get("attributes", {})
            )
            span.events.append(event)
        
        return span
    
    def _build_trace(self, trace_id: str, spans: List[Span]) -> Trace:
        """Build trace from spans"""
        # Sort spans by start time
        spans.sort(key=lambda s: s.start_time)
        
        # Find root span (no parent)
        root_span = next((s for s in spans if not s.parent_span_id), None)
        
        # Calculate trace metrics
        start_time = min(s.start_time for s in spans)
        end_time = max(s.end_time for s in spans if s.end_time)
        duration_ms = (end_time - start_time).total_seconds() * 1000 if end_time else None
        
        service_count = len(set(s.service_name for s in spans))
        error_count = sum(1 for s in spans if s.status == SpanStatus.ERROR)
        
        return Trace(
            trace_id=trace_id,
            spans=spans,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            service_count=service_count,
            span_count=len(spans),
            error_count=error_count,
            root_span=root_span
        )
    
    async def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get complete trace by ID"""
        # Check completed traces first
        if trace_id in self.completed_traces:
            return self.completed_traces[trace_id]
        
        # Try to build from stored spans
        try:
            span_ids = await self.redis_client.smembers(f"trace:{trace_id}:spans")
            if not span_ids:
                return None
            
            spans = []
            for span_id in span_ids:
                span_data = await self.redis_client.get(f"span:{span_id}")
                if span_data:
                    data = json.loads(span_data)
                    span = self._reconstruct_span(data)
                    spans.append(span)
            
            if spans:
                return self._build_trace(trace_id, spans)
        
        except Exception as e:
            logger.error("❌ Error getting trace", trace_id=trace_id, error=str(e))
        
        return None
    
    async def search_traces(self, service_name: Optional[str] = None,
                           operation_name: Optional[str] = None,
                           min_duration_ms: Optional[float] = None,
                           max_duration_ms: Optional[float] = None,
                           has_errors: Optional[bool] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           limit: int = 100) -> List[Trace]:
        """Search traces with filters"""
        traces = []
        
        # Search in completed traces
        for trace in self.completed_traces.values():
            if self._trace_matches_filters(trace, service_name, operation_name, 
                                         min_duration_ms, max_duration_ms, 
                                         has_errors, start_time, end_time):
                traces.append(trace)
        
        # Sort by start time (newest first)
        traces.sort(key=lambda t: t.start_time, reverse=True)
        
        return traces[:limit]
    
    def _trace_matches_filters(self, trace: Trace, service_name: Optional[str],
                              operation_name: Optional[str], min_duration_ms: Optional[float],
                              max_duration_ms: Optional[float], has_errors: Optional[bool],
                              start_time: Optional[datetime], end_time: Optional[datetime]) -> bool:
        """Check if trace matches search filters"""
        
        if service_name and not any(s.service_name == service_name for s in trace.spans):
            return False
        
        if operation_name and not any(s.operation_name == operation_name for s in trace.spans):
            return False
        
        if min_duration_ms and (not trace.duration_ms or trace.duration_ms < min_duration_ms):
            return False
        
        if max_duration_ms and (not trace.duration_ms or trace.duration_ms > max_duration_ms):
            return False
        
        if has_errors is not None:
            if has_errors and trace.error_count == 0:
                return False
            if not has_errors and trace.error_count > 0:
                return False
        
        if start_time and trace.start_time < start_time:
            return False
        
        if end_time and trace.start_time > end_time:
            return False
        
        return True
    
    def _should_sample(self) -> bool:
        """Determine if trace should be sampled"""
        import random
        return random.random() < self.sampling_rate
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return str(uuid.uuid4()).replace('-', '')
    
    def _generate_span_id(self) -> str:
        """Generate unique span ID"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    async def _cleanup_loop(self):
        """Background task to clean up old traces"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_old_traces()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ Error in cleanup loop", error=str(e))
    
    async def _export_loop(self):
        """Background task to export traces"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._export_traces()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ Error in export loop", error=str(e))
    
    async def _cleanup_old_traces(self):
        """Clean up old traces and spans"""
        cutoff_time = datetime.now() - self.max_trace_duration
        
        # Clean up completed traces
        traces_to_remove = [
            trace_id for trace_id, trace in self.completed_traces.items()
            if trace.start_time < cutoff_time
        ]
        
        for trace_id in traces_to_remove:
            del self.completed_traces[trace_id]
        
        if traces_to_remove:
            logger.info("🧹 Cleaned up old traces", count=len(traces_to_remove))
    
    async def _export_traces(self):
        """Export traces to external systems"""
        # This would export to systems like Jaeger, Zipkin, etc.
        # For now, just log metrics
        if self.completed_traces:
            logger.debug("📊 Trace metrics", 
                        total_traces=self.trace_count,
                        total_spans=self.span_count,
                        error_count=self.error_count,
                        active_spans=len(self.active_spans))
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get tracing system metrics"""
        return {
            "service_name": self.service_name,
            "total_traces": self.trace_count,
            "total_spans": self.span_count,
            "error_count": self.error_count,
            "active_spans": len(self.active_spans),
            "completed_traces": len(self.completed_traces),
            "sampling_rate": self.sampling_rate,
            "error_rate": self.error_count / max(self.span_count, 1)
        }

class SpanContext:
    """Context manager for spans"""
    
    def __init__(self, tracer: TracingSystem, span: Span, trace_context: TraceContext):
        self.tracer = tracer
        self.span = span
        self.trace_context = trace_context
        self.previous_context = None
    
    def __enter__(self):
        self.previous_context = current_trace_context.get()
        current_trace_context.set(self.trace_context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        current_trace_context.set(self.previous_context)
        
        # Finish span
        status = SpanStatus.ERROR if exc_type else SpanStatus.OK
        asyncio.create_task(self.tracer.finish_span(self.span, status, exc_val))
    
    async def __aenter__(self):
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)
    
    def set_attribute(self, key: str, value: Any):
        """Set span attribute"""
        self.span.attributes[key] = value
    
    def set_tag(self, key: str, value: str):
        """Set span tag"""
        self.span.tags[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add span event"""
        event = SpanEvent(
            name=name,
            timestamp=datetime.now(),
            attributes=attributes or {}
        )
        self.span.events.append(event)
    
    def log(self, message: str, level: str = "info", **kwargs):
        """Add log entry to span"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.span.logs.append(log_entry)

class NoOpSpanContext:
    """No-op span context for when tracing is disabled"""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def set_attribute(self, key: str, value: Any):
        pass
    
    def set_tag(self, key: str, value: str):
        pass
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        pass
    
    def log(self, message: str, level: str = "info", **kwargs):
        pass

# Decorator for automatic tracing
def trace(operation_name: Optional[str] = None, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator to automatically trace function calls"""
    def decorator(func):
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = await get_tracing_system()
            with tracer.start_trace(op_name, kind) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result_type", type(result).__name__)
                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to handle differently
            # This is a simplified implementation
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error("Function error", function=func.__name__, error=str(e))
                raise
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Global tracing system
_tracing_system: Optional[TracingSystem] = None

async def get_tracing_system() -> TracingSystem:
    """Get the global tracing system instance"""
    global _tracing_system
    if _tracing_system is None:
        _tracing_system = TracingSystem("ai-brain")
        await _tracing_system.initialize()
    return _tracing_system

async def initialize_tracing_system(service_name: str = "ai-brain") -> bool:
    """Initialize the global tracing system"""
    try:
        global _tracing_system
        _tracing_system = TracingSystem(service_name)
        await _tracing_system.initialize()
        logger.info("🔍 Global tracing system initialized", service=service_name)
        return True
    except Exception as e:
        logger.error("❌ Failed to initialize global tracing system", error=str(e))
        return False

# Utility functions
def get_current_trace_id() -> Optional[str]:
    """Get current trace ID"""
    context = current_trace_context.get()
    return context.trace_id if context else None

def get_current_span_id() -> Optional[str]:
    """Get current span ID"""
    context = current_trace_context.get()
    return context.span_id if context else None

def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """Inject trace context into headers for propagation"""
    context = current_trace_context.get()
    if context:
        headers.update(context.to_headers())
    return headers

def extract_trace_context(headers: Dict[str, str]) -> Optional[TraceContext]:
    """Extract trace context from headers"""
    return TraceContext.from_headers(headers)
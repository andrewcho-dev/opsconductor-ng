"""
Prometheus Metrics for Automation Service
Includes both selector and exec path metrics
"""
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict
import time


# ============================================================================
# AI EXECUTION METRICS (PR #4)
# ============================================================================

# Counter for total AI requests
ai_requests_total = Counter(
    'ai_requests_total',
    'Total number of AI execution requests',
    ['status', 'tool']
)

# Counter for AI request errors
ai_request_errors_total = Counter(
    'ai_request_errors_total',
    'Total number of AI execution errors',
    ['reason', 'tool']
)

# Histogram for AI request duration
ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'Duration of AI execution requests in seconds',
    ['tool'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)


# ============================================================================
# SELECTOR METRICS (existing from PR #2)
# ============================================================================

# Import selector metrics if available
try:
    from selector.metrics import (
        selector_requests_total,
        selector_errors_total,
        selector_duration_seconds,
        selector_candidates_found,
        selector_db_query_duration_seconds
    )
    SELECTOR_METRICS_AVAILABLE = True
except ImportError:
    SELECTOR_METRICS_AVAILABLE = False


# ============================================================================
# METRIC HELPERS
# ============================================================================

class MetricsContext:
    """Context manager for tracking request metrics"""
    
    def __init__(self, tool: str):
        self.tool = tool
        self.start_time = None
        self.success = False
        self.error_reason = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        
        # Record duration
        ai_request_duration_seconds.labels(tool=self.tool).observe(duration)
        
        # Record success/failure
        if exc_type is None and self.success:
            ai_requests_total.labels(status='success', tool=self.tool).inc()
        else:
            ai_requests_total.labels(status='error', tool=self.tool).inc()
            
            # Record error reason if set
            if self.error_reason:
                ai_request_errors_total.labels(
                    reason=self.error_reason,
                    tool=self.tool
                ).inc()
        
        return False  # Don't suppress exceptions
    
    def mark_success(self):
        """Mark the request as successful"""
        self.success = True
    
    def mark_error(self, reason: str):
        """Mark the request as failed with a reason"""
        self.error_reason = reason


def record_ai_request_success(tool: str, duration_seconds: float):
    """Record a successful AI request"""
    ai_requests_total.labels(status='success', tool=tool).inc()
    ai_request_duration_seconds.labels(tool=tool).observe(duration_seconds)


def record_ai_request_error(tool: str, reason: str, duration_seconds: float):
    """Record a failed AI request"""
    ai_requests_total.labels(status='error', tool=tool).inc()
    ai_request_errors_total.labels(reason=reason, tool=tool).inc()
    ai_request_duration_seconds.labels(tool=tool).observe(duration_seconds)


def get_metrics_text() -> str:
    """
    Get Prometheus metrics in text format
    
    Returns:
        Metrics in Prometheus exposition format
    """
    return generate_latest().decode('utf-8')


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics"""
    return CONTENT_TYPE_LATEST
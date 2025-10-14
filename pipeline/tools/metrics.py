"""
Tool Execution Metrics

Prometheus metrics for tool registry and execution
"""

from prometheus_client import Counter, Histogram, Gauge
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL EXECUTION METRICS
# ============================================================================

# Counter for total tool requests
ai_tool_requests_total = Counter(
    'ai_tool_requests_total',
    'Total number of tool execution requests',
    ['tool', 'status']
)

# Counter for tool request errors
ai_tool_request_errors_total = Counter(
    'ai_tool_request_errors_total',
    'Total number of tool execution errors',
    ['tool', 'error_type']
)

# Histogram for tool request duration
ai_tool_request_duration_seconds = Histogram(
    'ai_tool_request_duration_seconds',
    'Duration of tool execution requests in seconds',
    ['tool'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

# Gauge for registered tools count
ai_tool_registry_size = Gauge(
    'ai_tool_registry_size',
    'Number of tools registered in the registry'
)

# Counter for tool registry operations
ai_tool_registry_operations_total = Counter(
    'ai_tool_registry_operations_total',
    'Total number of tool registry operations',
    ['operation', 'status']
)


# ============================================================================
# METRIC HELPERS
# ============================================================================

def record_tool_request(tool: str, duration_seconds: float, success: bool):
    """
    Record tool execution request metrics
    
    Args:
        tool: Tool name
        duration_seconds: Execution duration in seconds
        success: Whether execution was successful
    """
    try:
        # Record duration
        ai_tool_request_duration_seconds.labels(tool=tool).observe(duration_seconds)
        
        # Record success/failure
        status = 'success' if success else 'error'
        ai_tool_requests_total.labels(tool=tool, status=status).inc()
    
    except Exception as e:
        logger.warning(f"Failed to record tool request metrics: {e}")


def record_tool_error(tool: str, error_type: str):
    """
    Record tool execution error
    
    Args:
        tool: Tool name
        error_type: Error type (timeout, validation, execution, etc.)
    """
    try:
        ai_tool_request_errors_total.labels(tool=tool, error_type=error_type).inc()
    except Exception as e:
        logger.warning(f"Failed to record tool error metrics: {e}")


def update_registry_size(count: int):
    """
    Update tool registry size gauge
    
    Args:
        count: Number of registered tools
    """
    try:
        ai_tool_registry_size.set(count)
    except Exception as e:
        logger.warning(f"Failed to update registry size metrics: {e}")


def record_registry_operation(operation: str, success: bool):
    """
    Record tool registry operation
    
    Args:
        operation: Operation type (register, delete, load)
        success: Whether operation was successful
    """
    try:
        status = 'success' if success else 'error'
        ai_tool_registry_operations_total.labels(operation=operation, status=status).inc()
    except Exception as e:
        logger.warning(f"Failed to record registry operation metrics: {e}")
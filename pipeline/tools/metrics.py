"""
Tool Execution Metrics

Prometheus metrics for tool registry and execution
TEMPORARY: Prometheus disabled until prometheus-client is added to requirements.txt
"""

# TEMPORARY: Commented out prometheus imports
# from prometheus_client import Counter, Histogram, Gauge
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL EXECUTION METRICS (TEMPORARILY DISABLED)
# ============================================================================

# TEMPORARY: Metrics disabled - uncomment when prometheus-client is installed
# # Counter for total tool requests
# ai_tool_requests_total = Counter(
#     'ai_tool_requests_total',
#     'Total number of tool execution requests',
#     ['tool', 'status']
# )
# 
# # Counter for tool request errors
# ai_tool_request_errors_total = Counter(
#     'ai_tool_request_errors_total',
#     'Total number of tool execution errors',
#     ['tool', 'error_type']
# )
# 
# # Histogram for tool request duration
# ai_tool_request_duration_seconds = Histogram(
#     'ai_tool_request_duration_seconds',
#     'Duration of tool execution requests in seconds',
#     ['tool'],
#     buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
# )
# 
# # Gauge for registered tools count
# ai_tool_registry_size = Gauge(
#     'ai_tool_registry_size',
#     'Number of tools registered in the registry'
# )
# 
# # Counter for tool registry operations
# ai_tool_registry_operations_total = Counter(
#     'ai_tool_registry_operations_total',
#     'Total number of tool registry operations',
#     ['operation', 'status']
# )


# ============================================================================
# METRIC HELPERS
# ============================================================================

def record_tool_request(tool: str, duration_seconds: float, success: bool):
    """
    Record tool execution request metrics
    TEMPORARY: No-op until prometheus-client is installed
    
    Args:
        tool: Tool name
        duration_seconds: Execution duration in seconds
        success: Whether execution was successful
    """
    # TEMPORARY: Metrics disabled
    pass


def record_tool_error(tool: str, error_type: str):
    """
    Record tool execution error
    TEMPORARY: No-op until prometheus-client is installed
    
    Args:
        tool: Tool name
        error_type: Error type (timeout, validation, execution, etc.)
    """
    # TEMPORARY: Metrics disabled
    pass


def update_registry_size(count: int):
    """
    Update tool registry size gauge
    TEMPORARY: No-op until prometheus-client is installed
    
    Args:
        count: Number of registered tools
    """
    # TEMPORARY: Metrics disabled
    pass


def record_registry_operation(operation: str, success: bool):
    """
    Record tool registry operation
    TEMPORARY: No-op until prometheus-client is installed
    
    Args:
        operation: Operation type (register, delete, load)
        success: Whether operation was successful
    """
    # TEMPORARY: Metrics disabled
    pass
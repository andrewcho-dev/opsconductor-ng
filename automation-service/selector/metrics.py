"""
Prometheus metrics endpoint for Selector v3.

This module provides a standalone /metrics endpoint at the app root level
that exposes selector metrics in Prometheus text format.
"""

from fastapi.responses import Response

# Import the metrics instance from v3
from selector.v3 import _metrics


async def metrics() -> Response:
    """
    Prometheus metrics endpoint.
    
    Exposes selector metrics in Prometheus text format (version 0.0.4).
    Returns HTTP 200 with content-type: text/plain; version=0.0.4; charset=utf-8
    
    Includes:
    - selector_requests_total (counter with status/source labels)
    - selector_request_duration_seconds (histogram)
    - selector_cache_entries (gauge)
    - selector_cache_ttl_seconds (gauge)
    - selector_build_info (gauge)
    - selector_cache_evictions_total (counter)
    - selector_db_errors_total (counter)
    """
    text = _metrics.to_prometheus_text()
    return Response(
        content=text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
        headers={"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}
    )
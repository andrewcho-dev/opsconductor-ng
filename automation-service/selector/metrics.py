"""
Prometheus metrics for automation-service selector.

This module provides Prometheus-compatible metrics collection and export.
"""

import time
from typing import Dict, Tuple
from collections import defaultdict


class SelectorMetrics:
    """Prometheus-compatible metrics collector for selector."""
    
    def __init__(self):
        # Counters
        self.requests_total: Dict[Tuple[str, str], int] = defaultdict(int)  # (status, source) -> count
        self.cache_evictions_total = 0
        self.db_errors_total = 0
        
        # Histogram buckets for request duration (seconds)
        self.duration_buckets = [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10]
        self.duration_counts: Dict[float, int] = {b: 0 for b in self.duration_buckets}
        self.duration_sum = 0.0
        self.duration_count = 0
        
        # Gauges (current values)
        self.cache_entries = 0
        self.cache_ttl_seconds = 300  # Default 5 minutes
        
        # Build info
        self.version = "3.0.0"
        self.git_commit = "unknown"
        self.built_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    def inc_request(self, status: str, source: str = "fresh"):
        """Increment request counter.
        
        Args:
            status: Request status (ok, error, etc.)
            source: Request source (fresh, cache, degraded)
        """
        key = (status, source)
        self.requests_total[key] += 1
    
    def observe_duration(self, duration_sec: float):
        """Observe request duration.
        
        Args:
            duration_sec: Request duration in seconds
        """
        self.duration_sum += duration_sec
        self.duration_count += 1
        for bucket in self.duration_buckets:
            if duration_sec <= bucket:
                self.duration_counts[bucket] += 1
    
    def to_prometheus_text(self) -> str:
        """Export metrics in Prometheus text format (version 0.0.4).
        
        Returns:
            Prometheus-formatted metrics text
        """
        lines = []
        
        # Build info
        lines.append("# HELP selector_build_info Selector build information")
        lines.append("# TYPE selector_build_info gauge")
        lines.append(
            f'selector_build_info{{version="{self.version}",git_commit="{self.git_commit}",'
            f'built_at="{self.built_at}"}} 1'
        )
        
        # Requests total
        lines.append("# HELP selector_requests_total Total number of selector requests")
        lines.append("# TYPE selector_requests_total counter")
        if self.requests_total:
            for (status, source), count in sorted(self.requests_total.items()):
                lines.append(f'selector_requests_total{{status="{status}",source="{source}"}} {count}')
        else:
            # Emit at least one sample to ensure metric exists
            lines.append('selector_requests_total{status="ok",source="fresh"} 0')
        
        # Cache evictions
        lines.append("# HELP selector_cache_evictions_total Total number of cache evictions")
        lines.append("# TYPE selector_cache_evictions_total counter")
        lines.append(f"selector_cache_evictions_total {self.cache_evictions_total}")
        
        # DB errors
        lines.append("# HELP selector_db_errors_total Total number of database errors")
        lines.append("# TYPE selector_db_errors_total counter")
        lines.append(f"selector_db_errors_total {self.db_errors_total}")
        
        # Request duration histogram
        lines.append("# HELP selector_request_duration_seconds Request duration in seconds")
        lines.append("# TYPE selector_request_duration_seconds histogram")
        for bucket in self.duration_buckets:
            count = self.duration_counts[bucket]
            lines.append(f'selector_request_duration_seconds_bucket{{le="{bucket}"}} {count}')
        lines.append(f'selector_request_duration_seconds_bucket{{le="+Inf"}} {self.duration_count}')
        lines.append(f"selector_request_duration_seconds_sum {self.duration_sum:.6f}")
        lines.append(f"selector_request_duration_seconds_count {self.duration_count}")
        
        # Cache entries gauge
        lines.append("# HELP selector_cache_entries Current number of entries in cache")
        lines.append("# TYPE selector_cache_entries gauge")
        lines.append(f"selector_cache_entries {self.cache_entries}")
        
        # Cache TTL gauge
        lines.append("# HELP selector_cache_ttl_seconds Cache TTL in seconds")
        lines.append("# TYPE selector_cache_ttl_seconds gauge")
        lines.append(f"selector_cache_ttl_seconds {self.cache_ttl_seconds}")
        
        return "\n".join(lines) + "\n"


# Global metrics instance
_metrics = SelectorMetrics()


def get_metrics() -> SelectorMetrics:
    """Get the global metrics instance."""
    return _metrics
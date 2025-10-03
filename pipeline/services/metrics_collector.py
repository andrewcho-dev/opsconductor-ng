"""
Metrics Collector for Tool Catalog System

Collects and aggregates metrics for:
- Tool loading performance
- Cache effectiveness
- API performance
- Database query performance
- Error rates

Author: Tool Catalog Team
Date: October 3, 2025
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class Counter:
    """Thread-safe counter metric"""
    
    def __init__(self):
        self._value = 0
        self._by_label = defaultdict(int)
        self._lock = threading.Lock()
    
    def inc(self, amount: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment counter"""
        with self._lock:
            self._value += amount
            if labels:
                label_key = self._make_label_key(labels)
                self._by_label[label_key] += amount
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get counter value"""
        with self._lock:
            if labels:
                label_key = self._make_label_key(labels)
                return self._by_label.get(label_key, 0)
            return self._value
    
    def reset(self):
        """Reset counter"""
        with self._lock:
            self._value = 0
            self._by_label.clear()
    
    @staticmethod
    def _make_label_key(labels: Dict[str, str]) -> str:
        """Create a key from labels"""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Histogram:
    """Thread-safe histogram metric for tracking distributions"""
    
    def __init__(self, max_size: int = 10000):
        self._values = deque(maxlen=max_size)
        self._lock = threading.Lock()
    
    def observe(self, value: float):
        """Record a value"""
        with self._lock:
            self._values.append(value)
    
    def get_stats(self) -> Dict[str, float]:
        """Get statistical summary"""
        with self._lock:
            if not self._values:
                return {
                    'count': 0,
                    'sum': 0,
                    'min': 0,
                    'max': 0,
                    'avg': 0,
                    'p50': 0,
                    'p95': 0,
                    'p99': 0
                }
            
            values = list(self._values)
            return {
                'count': len(values),
                'sum': sum(values),
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'p50': self._percentile(values, 50),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99)
            }
    
    def reset(self):
        """Reset histogram"""
        with self._lock:
            self._values.clear()
    
    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]


class Gauge:
    """Thread-safe gauge metric for current values"""
    
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def set(self, value: float):
        """Set gauge value"""
        with self._lock:
            self._value = value
    
    def inc(self, amount: float = 1):
        """Increment gauge"""
        with self._lock:
            self._value += amount
    
    def dec(self, amount: float = 1):
        """Decrement gauge"""
        with self._lock:
            self._value -= amount
    
    def get(self) -> float:
        """Get gauge value"""
        with self._lock:
            return self._value


class MetricsCollector:
    """
    Central metrics collector for Tool Catalog System
    
    Collects metrics for:
    - Tool loading (ProfileLoader)
    - Cache performance
    - API requests
    - Database queries
    - Errors
    """
    
    def __init__(self):
        # Tool loading metrics
        self.tool_loads = Counter()
        self.tool_load_duration = Histogram()
        self.tool_load_errors = Counter()
        
        # Cache metrics
        self.cache_hits = Counter()
        self.cache_misses = Counter()
        self.cache_size = Gauge()
        self.cache_evictions = Counter()
        
        # API metrics
        self.api_requests = Counter()
        self.api_duration = Histogram()
        self.api_errors = Counter()
        
        # Database metrics
        self.db_queries = Counter()
        self.db_query_duration = Histogram()
        self.db_errors = Counter()
        self.db_connections_active = Gauge()
        
        # Hot reload metrics
        self.reload_count = Counter()
        self.reload_duration = Histogram()
        self.reload_errors = Counter()
        
        # General metrics
        self.start_time = datetime.now()
        self._lock = threading.Lock()
    
    # ========================================================================
    # TOOL LOADING METRICS
    # ========================================================================
    
    def record_tool_load(
        self,
        tool_name: str,
        duration_ms: float,
        from_cache: bool,
        success: bool = True
    ):
        """Record a tool load operation"""
        labels = {'tool_name': tool_name}
        
        self.tool_loads.inc(labels=labels)
        self.tool_load_duration.observe(duration_ms)
        
        if from_cache:
            self.cache_hits.inc(labels=labels)
        else:
            self.cache_misses.inc(labels=labels)
        
        if not success:
            self.tool_load_errors.inc(labels=labels)
    
    # ========================================================================
    # CACHE METRICS
    # ========================================================================
    
    def record_cache_hit(self, tool_name: str):
        """Record a cache hit"""
        self.cache_hits.inc(labels={'tool_name': tool_name})
    
    def record_cache_miss(self, tool_name: str):
        """Record a cache miss"""
        self.cache_misses.inc(labels={'tool_name': tool_name})
    
    def update_cache_size(self, size: int):
        """Update current cache size"""
        self.cache_size.set(size)
    
    def record_cache_eviction(self):
        """Record a cache eviction"""
        self.cache_evictions.inc()
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        hits = self.cache_hits.get()
        misses = self.cache_misses.get()
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0
    
    # ========================================================================
    # API METRICS
    # ========================================================================
    
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        duration_ms: float,
        status_code: int
    ):
        """Record an API request"""
        labels = {
            'method': method,
            'endpoint': endpoint,
            'status_code': str(status_code)
        }
        
        self.api_requests.inc(labels=labels)
        self.api_duration.observe(duration_ms)
        
        if status_code >= 400:
            self.api_errors.inc(labels=labels)
    
    # ========================================================================
    # DATABASE METRICS
    # ========================================================================
    
    def record_db_query(
        self,
        query_type: str,
        duration_ms: float,
        success: bool = True
    ):
        """Record a database query"""
        labels = {'query_type': query_type}
        
        self.db_queries.inc(labels=labels)
        self.db_query_duration.observe(duration_ms)
        
        if not success:
            self.db_errors.inc(labels=labels)
    
    def update_db_connections(self, active: int):
        """Update active database connections"""
        self.db_connections_active.set(active)
    
    # ========================================================================
    # HOT RELOAD METRICS
    # ========================================================================
    
    def record_reload(
        self,
        trigger_type: str,
        duration_ms: float,
        success: bool = True
    ):
        """Record a hot reload operation"""
        labels = {'trigger_type': trigger_type}
        
        self.reload_count.inc(labels=labels)
        self.reload_duration.observe(duration_ms)
        
        if not success:
            self.reload_errors.inc(labels=labels)
    
    # ========================================================================
    # METRICS EXPORT
    # ========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        tool_load_stats = self.tool_load_duration.get_stats()
        api_stats = self.api_duration.get_stats()
        db_stats = self.db_query_duration.get_stats()
        reload_stats = self.reload_duration.get_stats()
        
        return {
            'system': {
                'uptime_seconds': uptime,
                'start_time': self.start_time.isoformat()
            },
            'tool_loading': {
                'total_loads': self.tool_loads.get(),
                'load_errors': self.tool_load_errors.get(),
                'duration_ms': tool_load_stats
            },
            'cache': {
                'hits': self.cache_hits.get(),
                'misses': self.cache_misses.get(),
                'hit_rate_percent': self.get_cache_hit_rate(),
                'current_size': self.cache_size.get(),
                'evictions': self.cache_evictions.get()
            },
            'api': {
                'total_requests': self.api_requests.get(),
                'errors': self.api_errors.get(),
                'error_rate_percent': self._calculate_error_rate(
                    self.api_requests.get(),
                    self.api_errors.get()
                ),
                'duration_ms': api_stats
            },
            'database': {
                'total_queries': self.db_queries.get(),
                'errors': self.db_errors.get(),
                'error_rate_percent': self._calculate_error_rate(
                    self.db_queries.get(),
                    self.db_errors.get()
                ),
                'duration_ms': db_stats,
                'active_connections': self.db_connections_active.get()
            },
            'hot_reload': {
                'total_reloads': self.reload_count.get(),
                'errors': self.reload_errors.get(),
                'error_rate_percent': self._calculate_error_rate(
                    self.reload_count.get(),
                    self.reload_errors.get()
                ),
                'duration_ms': reload_stats
            }
        }
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        metrics = self.get_metrics()
        lines = []
        
        # System metrics
        lines.append(f"# HELP tool_catalog_uptime_seconds System uptime in seconds")
        lines.append(f"# TYPE tool_catalog_uptime_seconds gauge")
        lines.append(f"tool_catalog_uptime_seconds {metrics['system']['uptime_seconds']}")
        
        # Tool loading metrics
        lines.append(f"# HELP tool_catalog_loads_total Total number of tool loads")
        lines.append(f"# TYPE tool_catalog_loads_total counter")
        lines.append(f"tool_catalog_loads_total {metrics['tool_loading']['total_loads']}")
        
        lines.append(f"# HELP tool_catalog_load_duration_ms Tool load duration in milliseconds")
        lines.append(f"# TYPE tool_catalog_load_duration_ms summary")
        for key, value in metrics['tool_loading']['duration_ms'].items():
            lines.append(f"tool_catalog_load_duration_ms{{quantile=\"{key}\"}} {value}")
        
        # Cache metrics
        lines.append(f"# HELP tool_catalog_cache_hits_total Total cache hits")
        lines.append(f"# TYPE tool_catalog_cache_hits_total counter")
        lines.append(f"tool_catalog_cache_hits_total {metrics['cache']['hits']}")
        
        lines.append(f"# HELP tool_catalog_cache_misses_total Total cache misses")
        lines.append(f"# TYPE tool_catalog_cache_misses_total counter")
        lines.append(f"tool_catalog_cache_misses_total {metrics['cache']['misses']}")
        
        lines.append(f"# HELP tool_catalog_cache_hit_rate_percent Cache hit rate percentage")
        lines.append(f"# TYPE tool_catalog_cache_hit_rate_percent gauge")
        lines.append(f"tool_catalog_cache_hit_rate_percent {metrics['cache']['hit_rate_percent']}")
        
        # API metrics
        lines.append(f"# HELP tool_catalog_api_requests_total Total API requests")
        lines.append(f"# TYPE tool_catalog_api_requests_total counter")
        lines.append(f"tool_catalog_api_requests_total {metrics['api']['total_requests']}")
        
        lines.append(f"# HELP tool_catalog_api_duration_ms API request duration in milliseconds")
        lines.append(f"# TYPE tool_catalog_api_duration_ms summary")
        for key, value in metrics['api']['duration_ms'].items():
            lines.append(f"tool_catalog_api_duration_ms{{quantile=\"{key}\"}} {value}")
        
        # Database metrics
        lines.append(f"# HELP tool_catalog_db_queries_total Total database queries")
        lines.append(f"# TYPE tool_catalog_db_queries_total counter")
        lines.append(f"tool_catalog_db_queries_total {metrics['database']['total_queries']}")
        
        lines.append(f"# HELP tool_catalog_db_duration_ms Database query duration in milliseconds")
        lines.append(f"# TYPE tool_catalog_db_duration_ms summary")
        for key, value in metrics['database']['duration_ms'].items():
            lines.append(f"tool_catalog_db_duration_ms{{quantile=\"{key}\"}} {value}")
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all metrics"""
        self.tool_loads.reset()
        self.tool_load_duration.reset()
        self.tool_load_errors.reset()
        
        self.cache_hits.reset()
        self.cache_misses.reset()
        self.cache_evictions.reset()
        
        self.api_requests.reset()
        self.api_duration.reset()
        self.api_errors.reset()
        
        self.db_queries.reset()
        self.db_query_duration.reset()
        self.db_errors.reset()
        
        self.reload_count.reset()
        self.reload_duration.reset()
        self.reload_errors.reset()
        
        self.start_time = datetime.now()
    
    @staticmethod
    def _calculate_error_rate(total: int, errors: int) -> float:
        """Calculate error rate percentage"""
        return (errors / total * 100) if total > 0 else 0


# Global metrics collector instance
_metrics_collector = None
_metrics_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance"""
    global _metrics_collector
    
    if _metrics_collector is None:
        with _metrics_lock:
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
    
    return _metrics_collector
"""
Selector v3 - Production-grade tool selection with caching, metrics, and resilience.

Features:
- LRU+TTL cache with size cap and concurrency safety
- Prometheus metrics at /metrics
- Degraded mode: serves Last-Known-Good (LKG) during DB outages
- Input validation and parameter guardrails
- Structured JSON logging
- Environment-driven configuration
"""

import asyncio
import os
import sys
import time
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path so 'shared' module can be imported
# Try both /app (Docker) and relative path (local dev)
parent_paths = [
    '/app',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
]
for path in parent_paths:
    shared_dir = os.path.join(path, 'shared')
    if os.path.exists(shared_dir) and path not in sys.path:
        sys.path.insert(0, path)
        break

import asyncpg
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field, validator

# Use stdlib logging (avoid conflict with shared.logging)
import logging as stdlib_logging

# Use stdlib logging
logging = stdlib_logging

# OpenTelemetry tracing (optional)
try:
    from shared.otel import get_tracer, add_span_attributes
    _tracer = None  # Will be initialized on first use
except ImportError:
    get_tracer = None
    add_span_attributes = None
    _tracer = None

# ============================================================================
# CONFIGURATION
# ============================================================================

SELECTOR_CACHE_TTL_SEC = int(os.getenv("SELECTOR_CACHE_TTL_SEC", "600"))
SELECTOR_CACHE_MAX_ENTRIES = int(os.getenv("SELECTOR_CACHE_MAX_ENTRIES", "1000"))
SELECTOR_DEGRADED_ENABLE = os.getenv("SELECTOR_DEGRADED_ENABLE", "true").lower() in ("true", "1", "yes")

# Build info
SELECTOR_VERSION = "3.0.0"
SELECTOR_GIT_COMMIT = os.getenv("GIT_COMMIT", "unknown")
SELECTOR_BUILT_AT = os.getenv("BUILT_AT", "unknown")

# ============================================================================
# MODELS
# ============================================================================

class ToolResult(BaseModel):
    """Single tool result from selector."""
    name: str
    short_desc: str = ""


class SelectorResponse(BaseModel):
    """Selector search response."""
    query: str
    platforms: List[str] = Field(default_factory=list)
    k: int
    results: List[ToolResult]
    from_cache: bool
    duration_ms: float


class SelectorError(BaseModel):
    """Selector error response for 503."""
    error: str
    code: str
    degraded: bool
    hint: str
    retry_after_sec: int


# ============================================================================
# METRICS
# ============================================================================

class SelectorMetrics:
    """Prometheus-compatible metrics collector."""
    
    def __init__(self):
        # Counters
        self.requests_total: Dict[Tuple[str, str], int] = {}  # (status, source) -> count
        self.cache_evictions_total = 0
        self.db_errors_total = 0
        
        # Histogram buckets for request duration
        self.duration_buckets = [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10]
        self.duration_counts: Dict[float, int] = {b: 0 for b in self.duration_buckets}
        self.duration_sum = 0.0
        self.duration_count = 0
        
        # Gauges (current values)
        self.cache_entries = 0
        self.cache_ttl_seconds = SELECTOR_CACHE_TTL_SEC
    
    def inc_request(self, status: str, source: str):
        """Increment request counter."""
        key = (status, source)
        self.requests_total[key] = self.requests_total.get(key, 0) + 1
    
    def observe_duration(self, duration_sec: float):
        """Observe request duration."""
        self.duration_sum += duration_sec
        self.duration_count += 1
        for bucket in self.duration_buckets:
            if duration_sec <= bucket:
                self.duration_counts[bucket] += 1
    
    def to_prometheus_text(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Build info
        lines.append("# HELP selector_build_info Selector build information")
        lines.append("# TYPE selector_build_info gauge")
        lines.append(
            f'selector_build_info{{version="{SELECTOR_VERSION}",git_commit="{SELECTOR_GIT_COMMIT}",'
            f'built_at="{SELECTOR_BUILT_AT}",hotfix="v2"}} 1'
        )
        
        # Requests total
        lines.append("# HELP selector_requests_total Total number of selector requests")
        lines.append("# TYPE selector_requests_total counter")
        for (status, source), count in sorted(self.requests_total.items()):
            lines.append(f'selector_requests_total{{status="{status}",source="{source}"}} {count}')
        
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


# ============================================================================
# LRU+TTL CACHE
# ============================================================================

class LRUTTLCache:
    """
    In-memory LRU cache with per-entry TTL and size cap.
    
    Thread-safe for async operations using asyncio.Lock.
    """
    
    def __init__(self, max_entries: int, ttl_sec: int):
        self.max_entries = max_entries
        self.ttl_sec = ttl_sec
        self._cache: OrderedDict[Tuple, Tuple[float, Dict]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger("selector.cache")
    
    async def get(self, key: Tuple) -> Optional[Dict]:
        """Get value from cache if not expired."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            expires_at, value = self._cache[key]
            
            # Check if expired
            if time.time() > expires_at:
                self._logger.debug(f"Cache key expired: {key}")
                del self._cache[key]
                return None
            
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            return value
    
    async def put(self, key: Tuple, value: Dict):
        """Put value in cache with TTL."""
        async with self._lock:
            expires_at = time.time() + self.ttl_sec
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = (expires_at, value)
                self._cache.move_to_end(key)
                return
            
            # Check if we need to evict
            if len(self._cache) >= self.max_entries:
                # Evict oldest (first item)
                evicted_key, _ = self._cache.popitem(last=False)
                _metrics.cache_evictions_total += 1
                self._logger.debug(f"Evicted cache key: {evicted_key}")
            
            # Add new entry
            self._cache[key] = (expires_at, value)
    
    async def size(self) -> int:
        """Get current cache size."""
        async with self._lock:
            return len(self._cache)
    
    async def clear(self):
        """Clear all cache entries (for testing)."""
        async with self._lock:
            self._cache.clear()


# Global cache instance
_cache = LRUTTLCache(max_entries=SELECTOR_CACHE_MAX_ENTRIES, ttl_sec=SELECTOR_CACHE_TTL_SEC)


def get_cache() -> LRUTTLCache:
    """Get the global cache instance (for testing)."""
    return _cache


# ============================================================================
# UTILITIES
# ============================================================================

def normalize_cache_key(query: str, k: int, platforms: List[str]) -> Tuple:
    """
    Normalize cache key to match v2 behavior.
    
    Returns: (query.lower().strip(), int(k), tuple(sorted(p.strip().lower() for p in platforms)))
    """
    normalized_query = query.lower().strip()
    normalized_k = int(k)
    normalized_platforms = tuple(sorted(p.strip().lower() for p in platforms if p and p.strip()))
    return (normalized_query, normalized_k, normalized_platforms)


def generate_trace_id(request: Request) -> str:
    """Generate or extract trace ID from request."""
    trace_id = request.headers.get("X-Trace-Id")
    if not trace_id:
        trace_id = f"sel-{int(time.time() * 1000)}-{id(request)}"
    return trace_id


# ============================================================================
# VALIDATION
# ============================================================================

def validate_query(query: str) -> str:
    """Validate and normalize query parameter."""
    # Check for empty or whitespace-only query
    if not query or not query.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "code": "QUERY_EMPTY",
                "message": "Query parameter cannot be empty"
            }
        )
    
    query = query.strip()
    
    if len(query) > 200:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "code": "QUERY_TOO_LONG",
                "message": f"Query parameter exceeds maximum length of 200 characters (got {len(query)})"
            }
        )
    
    return query


def validate_platforms(platforms: List[str]) -> List[str]:
    """Validate platform parameters."""
    if len(platforms) > 5:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "code": "TOO_MANY_PLATFORMS",
                "message": f"Maximum 5 platform values allowed (got {len(platforms)})"
            }
        )
    
    validated = []
    for p in platforms:
        p_stripped = p.strip()
        if not p_stripped:
            continue
        if len(p_stripped) < 1 or len(p_stripped) > 32:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ValidationError",
                    "code": "INVALID_PLATFORM_LENGTH",
                    "message": f"Platform value must be 1-32 characters (got '{p_stripped}')"
                }
            )
        validated.append(p_stripped)
    
    return validated


def validate_k(k: int) -> int:
    """Validate k parameter."""
    if k < 1 or k > 10:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "code": "K_OUT_OF_RANGE",
                "message": f"Parameter k must be between 1 and 10 (got {k})"
            }
        )
    return k


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="", tags=["selector"])
logger = logging.getLogger("selector.v3")


@router.get("/api/selector/search", response_model=SelectorResponse)
async def selector_search(
    request: Request,
    query: str = Query(..., min_length=1, description="Search query (required, max 200 chars)"),
    platform: List[str] = Query(default=[], description="Platform filters (max 5, each 1-32 chars)"),
    k: int = Query(3, ge=1, le=10, description="Number of results (1-10)")
):
    """
    Search for tools matching the query.
    
    Returns top-k tools based on semantic similarity to the query.
    Results may be served from cache or database.
    
    During database outages, warm cache keys return 200 with from_cache=true,
    while cold keys return 503 with Retry-After header.
    """
    t0 = time.time()
    trace_id = generate_trace_id(request)
    
    # Add span attributes for tracing
    if add_span_attributes:
        add_span_attributes(
            query_len=len(query),
            k=k,
            platforms_count=len(platform)
        )
    
    # Validate inputs
    try:
        query = validate_query(query)
        platforms = validate_platforms(platform)
        k = validate_k(k)
    except HTTPException as e:
        # Log validation error
        logger.warning(
            "Validation error",
            extra={
                "event": "selector_request",
                "trace_id": trace_id,
                "status": 400,
                "code": e.detail.get("code") if isinstance(e.detail, dict) else "VALIDATION_ERROR"
            }
        )
        raise
    
    # Normalize cache key
    cache_key = normalize_cache_key(query, k, platforms)
    
    # Try cache first
    cached_value = await _cache.get(cache_key)
    if cached_value:
        duration_sec = time.time() - t0
        _metrics.inc_request("ok", "cache")
        _metrics.observe_duration(duration_sec)
        _metrics.cache_entries = await _cache.size()
        
        # Add span attributes
        if add_span_attributes:
            add_span_attributes(
                from_cache=True,
                status="ok"
            )
        
        # Log request
        logger.info(
            "Selector request (cached)",
            extra={
                "event": "selector_request",
                "trace_id": trace_id,
                "query": query[:120],
                "k": k,
                "platforms": platforms,
                "from_cache": True,
                "source": "cache",
                "duration_ms": round(duration_sec * 1000, 1),
                "status": 200
            }
        )
        
        # Update from_cache flag and duration for cached response
        cached_response = cached_value.copy()
        cached_response["from_cache"] = True
        cached_response["duration_ms"] = round(duration_sec * 1000, 1)
        
        return SelectorResponse(**cached_response)
    
    # Get DB pool
    pool = getattr(getattr(request.app, "state", None), "db_pool", None)
    if pool is None:
        pool = getattr(request.app, "db_pool", None)
    
    if pool is None:
        # DB not available - check degraded mode
        if SELECTOR_DEGRADED_ENABLE:
            # Try to serve from cache (LKG)
            cached_value = await _cache.get(cache_key)
            if cached_value:
                duration_sec = time.time() - t0
                _metrics.inc_request("ok", "degraded")
                _metrics.observe_duration(duration_sec)
                _metrics.db_errors_total += 1
                
                logger.warning(
                    "Selector request (degraded - DB unavailable, serving LKG)",
                    extra={
                        "event": "selector_request",
                        "trace_id": trace_id,
                        "query": query[:120],
                        "k": k,
                        "platforms": platforms,
                        "from_cache": True,
                        "source": "degraded",
                        "duration_ms": round(duration_sec * 1000, 1),
                        "status": 200
                    }
                )
                
                return SelectorResponse(**cached_value)
        
        # Cold key during outage - return 503
        duration_sec = time.time() - t0
        _metrics.inc_request("error", "fresh")
        _metrics.observe_duration(duration_sec)
        _metrics.db_errors_total += 1
        
        logger.error(
            "Selector request failed (DB unavailable, cold key)",
            extra={
                "event": "selector_request",
                "trace_id": trace_id,
                "query": query[:120],
                "k": k,
                "platforms": platforms,
                "from_cache": False,
                "source": "fresh",
                "duration_ms": round(duration_sec * 1000, 1),
                "status": 503,
                "code": "SELECTOR_DB_UNAVAILABLE",
                "cause": "db_pool_not_ready"
            }
        )
        
        error_response = SelectorError(
            error="DependencyUnavailable",
            code="SELECTOR_DB_UNAVAILABLE",
            degraded=False,
            hint="Try again shortly or reduce k; warm keys will be served from cache.",
            retry_after_sec=30
        )
        
        return Response(
            content=error_response.model_dump_json(),
            status_code=503,
            headers={"Retry-After": "30", "Content-Type": "application/json"}
        )
    
    # Query database
    try:
        # Import here to allow test mocking of selector.dao.select_topk
        from selector.dao import select_topk
        
        async with pool.acquire() as conn:
            rows = await select_topk(conn, query, platforms, k)
            
            # Build response
            results = [
                ToolResult(
                    name=row.get("name", ""),
                    short_desc=row.get("short_desc", "")
                )
                for row in rows
            ]
            
            duration_sec = time.time() - t0
            
            response_data = {
                "query": query,
                "platforms": platforms,
                "k": k,
                "results": [r.model_dump() for r in results],
                "from_cache": False,
                "duration_ms": round(duration_sec * 1000, 1)
            }
            
            # Store in cache
            await _cache.put(cache_key, response_data)
            
            # Update metrics
            _metrics.inc_request("ok", "fresh")
            _metrics.observe_duration(duration_sec)
            _metrics.cache_entries = await _cache.size()
            
            # Add span attributes
            if add_span_attributes:
                add_span_attributes(
                    from_cache=False,
                    status="ok"
                )
            
            # Log request
            logger.info(
                "Selector request (fresh)",
                extra={
                    "event": "selector_request",
                    "trace_id": trace_id,
                    "query": query[:120],
                    "k": k,
                    "platforms": platforms,
                    "from_cache": False,
                    "source": "fresh",
                    "duration_ms": round(duration_sec * 1000, 1),
                    "status": 200
                }
            )
            
            return SelectorResponse(**response_data)
    
    except Exception as e:
        # Database error - try degraded mode
        if SELECTOR_DEGRADED_ENABLE:
            cached_value = await _cache.get(cache_key)
            if cached_value:
                duration_sec = time.time() - t0
                _metrics.inc_request("ok", "degraded")
                _metrics.observe_duration(duration_sec)
                _metrics.db_errors_total += 1
                
                logger.warning(
                    "Selector request (degraded - DB error, serving LKG)",
                    extra={
                        "event": "selector_request",
                        "trace_id": trace_id,
                        "query": query[:120],
                        "k": k,
                        "platforms": platforms,
                        "from_cache": True,
                        "source": "degraded",
                        "duration_ms": round(duration_sec * 1000, 1),
                        "status": 200,
                        "cause": str(e)[:100]
                    }
                )
                
                return SelectorResponse(**cached_value)
        
        # Cold key during error - return 503
        duration_sec = time.time() - t0
        _metrics.inc_request("error", "fresh")
        _metrics.observe_duration(duration_sec)
        _metrics.db_errors_total += 1
        
        logger.error(
            "Selector request failed (DB error, cold key)",
            extra={
                "event": "selector_request",
                "trace_id": trace_id,
                "query": query[:120],
                "k": k,
                "platforms": platforms,
                "from_cache": False,
                "source": "fresh",
                "duration_ms": round(duration_sec * 1000, 1),
                "status": 503,
                "code": "SELECTOR_DB_ERROR",
                "cause": str(e)[:100]
            }
        )
        
        error_response = SelectorError(
            error="DependencyUnavailable",
            code="SELECTOR_DB_UNAVAILABLE",
            degraded=False,
            hint="Try again shortly or reduce k; warm keys will be served from cache.",
            retry_after_sec=30
        )
        
        return Response(
            content=error_response.model_dump_json(),
            status_code=503,
            headers={"Retry-After": "30", "Content-Type": "application/json"}
        )


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Exposes selector metrics in Prometheus text format (version 0.0.4).
    
    Note: This endpoint is also registered at app root level in main_clean.py
    to ensure it's accessible at /metrics for CI tests and production.
    """
    return _metrics.to_prometheus_text()
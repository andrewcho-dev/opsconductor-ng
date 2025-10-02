"""
Asset Service Integration Metrics
Tracks performance, usage, and quality metrics for asset-service integration.

Metrics tracked:
- Selection accuracy (precision/recall)
- Query performance (latency, cache hit rate)
- Error rates and types
- Tool usage patterns
- Disambiguation effectiveness
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SelectionMetrics:
    """Metrics for tool selection decisions"""
    total_queries: int = 0
    selected_count: int = 0
    skipped_count: int = 0
    clarify_count: int = 0
    
    # Score distribution
    score_sum: float = 0.0
    score_count: int = 0
    
    # Timing
    total_scoring_time_ms: float = 0.0
    
    def record_selection(self, score: float, selected: bool, duration_ms: float) -> None:
        """Record a selection decision"""
        self.total_queries += 1
        self.score_sum += score
        self.score_count += 1
        self.total_scoring_time_ms += duration_ms
        
        if selected:
            if score >= 0.6:
                self.selected_count += 1
            elif score >= 0.4:
                self.clarify_count += 1
            else:
                self.skipped_count += 1
        else:
            self.skipped_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get selection statistics"""
        avg_score = self.score_sum / self.score_count if self.score_count > 0 else 0.0
        avg_time = self.total_scoring_time_ms / self.score_count if self.score_count > 0 else 0.0
        
        return {
            "total_queries": self.total_queries,
            "selected_count": self.selected_count,
            "skipped_count": self.skipped_count,
            "clarify_count": self.clarify_count,
            "selection_rate": f"{(self.selected_count / self.total_queries * 100):.1f}%" if self.total_queries > 0 else "0%",
            "avg_score": f"{avg_score:.3f}",
            "avg_scoring_time_ms": f"{avg_time:.2f}"
        }


@dataclass
class QueryMetrics:
    """Metrics for asset-service queries"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    
    # By query type
    query_type_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Timing
    total_query_time_ms: float = 0.0
    query_times: deque = field(default_factory=lambda: deque(maxlen=100))  # Last 100 queries
    
    # Cache
    cache_hits: int = 0
    cache_misses: int = 0
    
    # Errors
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_query(
        self,
        query_type: str,
        success: bool,
        duration_ms: float,
        cache_hit: bool = False,
        error_type: Optional[str] = None
    ) -> None:
        """Record a query execution"""
        self.total_queries += 1
        self.query_type_counts[query_type] += 1
        self.total_query_time_ms += duration_ms
        self.query_times.append(duration_ms)
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
            if error_type:
                self.error_counts[error_type] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        avg_time = self.total_query_time_ms / self.total_queries if self.total_queries > 0 else 0.0
        
        # Calculate percentiles
        p50 = p95 = p99 = 0.0
        if self.query_times:
            sorted_times = sorted(self.query_times)
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0.0
        
        success_rate = (self.successful_queries / self.total_queries * 100) if self.total_queries > 0 else 0.0
        
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": f"{success_rate:.1f}%",
            "avg_query_time_ms": f"{avg_time:.1f}",
            "p50_ms": f"{p50:.1f}",
            "p95_ms": f"{p95:.1f}",
            "p99_ms": f"{p99:.1f}",
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "query_types": dict(self.query_type_counts),
            "error_types": dict(self.error_counts)
        }


@dataclass
class DisambiguationMetrics:
    """Metrics for disambiguation scenarios"""
    total_disambiguations: int = 0
    zero_results: int = 0
    single_result: int = 0
    few_results: int = 0  # 2-5
    many_results: int = 0  # 5+
    
    # User actions after disambiguation
    user_refined_query: int = 0
    user_selected_option: int = 0
    user_abandoned: int = 0
    
    def record_disambiguation(self, result_count: int) -> None:
        """Record a disambiguation scenario"""
        self.total_disambiguations += 1
        
        if result_count == 0:
            self.zero_results += 1
        elif result_count == 1:
            self.single_result += 1
        elif result_count <= 5:
            self.few_results += 1
        else:
            self.many_results += 1
    
    def record_user_action(self, action: str) -> None:
        """Record user action after disambiguation"""
        if action == "refined":
            self.user_refined_query += 1
        elif action == "selected":
            self.user_selected_option += 1
        elif action == "abandoned":
            self.user_abandoned += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get disambiguation statistics"""
        return {
            "total_disambiguations": self.total_disambiguations,
            "zero_results": self.zero_results,
            "single_result": self.single_result,
            "few_results": self.few_results,
            "many_results": self.many_results,
            "user_refined_query": self.user_refined_query,
            "user_selected_option": self.user_selected_option,
            "user_abandoned": self.user_abandoned
        }


@dataclass
class ContextInjectionMetrics:
    """Metrics for dynamic context injection"""
    total_requests: int = 0
    injected_count: int = 0
    skipped_count: int = 0
    
    # Token savings
    tokens_saved: int = 0
    tokens_used: int = 0
    
    def record_injection(self, injected: bool, tokens: int) -> None:
        """Record a context injection decision"""
        self.total_requests += 1
        
        if injected:
            self.injected_count += 1
            self.tokens_used += tokens
        else:
            self.skipped_count += 1
            self.tokens_saved += tokens  # Tokens we would have used
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context injection statistics"""
        injection_rate = (self.injected_count / self.total_requests * 100) if self.total_requests > 0 else 0.0
        total_tokens = self.tokens_saved + self.tokens_used
        savings_rate = (self.tokens_saved / total_tokens * 100) if total_tokens > 0 else 0.0
        
        return {
            "total_requests": self.total_requests,
            "injected_count": self.injected_count,
            "skipped_count": self.skipped_count,
            "injection_rate": f"{injection_rate:.1f}%",
            "tokens_saved": self.tokens_saved,
            "tokens_used": self.tokens_used,
            "savings_rate": f"{savings_rate:.1f}%"
        }


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class AssetMetricsCollector:
    """Central metrics collector for asset-service integration"""
    
    def __init__(self):
        self.selection = SelectionMetrics()
        self.query = QueryMetrics()
        self.disambiguation = DisambiguationMetrics()
        self.context_injection = ContextInjectionMetrics()
        self.start_time = time.time()
    
    # ========================================================================
    # RECORDING METHODS
    # ========================================================================
    
    def record_selection(self, query: str, score: float, selected: bool, duration_ms: float) -> None:
        """Record a tool selection decision"""
        self.selection.record_selection(score, selected, duration_ms)
        
        logger.info(
            f"Tool selection recorded",
            extra={
                "query": query[:100],  # Truncate long queries
                "score": f"{score:.3f}",
                "selected": selected,
                "duration_ms": f"{duration_ms:.2f}"
            }
        )
    
    def record_query(
        self,
        query_type: str,
        success: bool,
        duration_ms: float,
        cache_hit: bool = False,
        error_type: Optional[str] = None
    ) -> None:
        """Record a query execution"""
        self.query.record_query(query_type, success, duration_ms, cache_hit, error_type)
        
        logger.info(
            f"Query execution recorded",
            extra={
                "query_type": query_type,
                "success": success,
                "duration_ms": f"{duration_ms:.1f}",
                "cache_hit": cache_hit,
                "error_type": error_type
            }
        )
    
    def record_disambiguation(self, result_count: int) -> None:
        """Record a disambiguation scenario"""
        self.disambiguation.record_disambiguation(result_count)
        
        logger.info(
            f"Disambiguation recorded",
            extra={"result_count": result_count}
        )
    
    def record_context_injection(self, injected: bool, tokens: int) -> None:
        """Record a context injection decision"""
        self.context_injection.record_injection(injected, tokens)
        
        logger.debug(
            f"Context injection recorded",
            extra={"injected": injected, "tokens": tokens}
        )
    
    # ========================================================================
    # REPORTING METHODS
    # ========================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        uptime_seconds = time.time() - self.start_time
        uptime_hours = uptime_seconds / 3600
        
        return {
            "uptime_hours": f"{uptime_hours:.2f}",
            "selection": self.selection.get_stats(),
            "query": self.query.get_stats(),
            "disambiguation": self.disambiguation.get_stats(),
            "context_injection": self.context_injection.get_stats()
        }
    
    def get_health_score(self) -> Dict[str, Any]:
        """Calculate overall health score (0-100)"""
        scores = []
        
        # Query success rate (0-40 points)
        if self.query.total_queries > 0:
            success_rate = self.query.successful_queries / self.query.total_queries
            scores.append(success_rate * 40)
        
        # Cache hit rate (0-20 points)
        total_cache = self.query.cache_hits + self.query.cache_misses
        if total_cache > 0:
            cache_rate = self.query.cache_hits / total_cache
            scores.append(cache_rate * 20)
        
        # Selection accuracy (0-20 points)
        # Assume good if selection rate is between 20-60%
        if self.selection.total_queries > 0:
            selection_rate = self.selection.selected_count / self.selection.total_queries
            if 0.2 <= selection_rate <= 0.6:
                scores.append(20)
            else:
                scores.append(10)
        
        # Performance (0-20 points)
        # Good if p95 < 2000ms
        if self.query.query_times:
            sorted_times = sorted(self.query.query_times)
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            if p95 < 2000:
                scores.append(20)
            elif p95 < 5000:
                scores.append(10)
            else:
                scores.append(0)
        
        health_score = sum(scores) if scores else 0
        
        return {
            "health_score": int(health_score),
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "unhealthy",
            "components": {
                "query_success": scores[0] if len(scores) > 0 else 0,
                "cache_performance": scores[1] if len(scores) > 1 else 0,
                "selection_accuracy": scores[2] if len(scores) > 2 else 0,
                "query_performance": scores[3] if len(scores) > 3 else 0
            }
        }
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.selection = SelectionMetrics()
        self.query = QueryMetrics()
        self.disambiguation = DisambiguationMetrics()
        self.context_injection = ContextInjectionMetrics()
        self.start_time = time.time()
        
        logger.info("Metrics reset")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Global metrics collector
_metrics: Optional[AssetMetricsCollector] = None


def get_metrics_collector() -> AssetMetricsCollector:
    """Get or create the global metrics collector"""
    global _metrics
    if _metrics is None:
        _metrics = AssetMetricsCollector()
    return _metrics


def reset_metrics() -> None:
    """Reset the global metrics collector"""
    global _metrics
    if _metrics:
        _metrics.reset()
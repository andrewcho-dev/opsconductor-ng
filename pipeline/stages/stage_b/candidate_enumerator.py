"""
Candidate Enumerator - Phase 3 Module 2/2

Enumerates candidate tools that match required capabilities and evaluates
their performance metrics using runtime context.

This module:
1. Loads tool profiles from YAML
2. Matches capabilities to query requirements
3. Evaluates expressions (time_ms, cost) with runtime context
4. Builds ToolCandidate objects for scoring

Design Principles:
1. Fail gracefully (skip invalid patterns, log errors)
2. Context-aware evaluation (N, pages, p95_latency)
3. Complete candidate information (for scoring and policy enforcement)
4. Performance-conscious (cache profiles, evaluate once)
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

from .profile_loader import ProfileLoader
from .safe_math_eval import SafeMathEvaluator
from .optimization_schemas import PatternProfile, PolicyConfig


logger = logging.getLogger(__name__)


@dataclass
class ToolCandidate:
    """
    A candidate tool with evaluated metrics.
    
    This is the input to the deterministic scorer and policy enforcer.
    All expressions have been evaluated with runtime context.
    """
    # Identification
    tool_name: str
    capability_name: str
    pattern_name: str
    
    # Evaluated performance metrics (expressions resolved)
    estimated_time_ms: float
    estimated_cost: float
    complexity: float  # [0,1] where 0=simple, 1=complex
    
    # Quality metrics (from profile)
    accuracy: float  # [0,1] from preference_match.accuracy
    completeness: float  # [0,1] from preference_match.completeness
    
    # Policy configuration
    policy: PolicyConfig
    
    # Metadata
    description: str
    typical_use_cases: List[str]
    limitations: List[str]
    
    # Additional context
    accuracy_level: Optional[str] = None
    freshness: Optional[str] = None
    scope: Optional[str] = None
    data_source: Optional[str] = None


class CandidateEnumerator:
    """
    Enumerates candidate tools for a query.
    
    Takes required capabilities and runtime context, returns list of
    evaluated ToolCandidate objects ready for scoring.
    
    Example:
        enumerator = CandidateEnumerator()
        candidates = enumerator.enumerate_candidates(
            required_capabilities=["asset_query"],
            context={"N": 100, "pages": 1, "p95_latency": 1000}
        )
        # Returns: [ToolCandidate(...), ToolCandidate(...), ...]
    """
    
    def __init__(self, profile_loader: Optional[ProfileLoader] = None):
        """
        Initialize candidate enumerator.
        
        Args:
            profile_loader: ProfileLoader instance. If None, creates default.
        """
        self.profile_loader = profile_loader or ProfileLoader()
        self._profiles = None
    
    def enumerate_candidates(
        self,
        required_capabilities: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[ToolCandidate]:
        """
        Enumerate all candidate tools matching required capabilities.
        
        Process:
        1. Normalize capability names (NEW: permanent fix for capability mismatches)
        2. Load tool profiles (cached)
        3. Filter by required capabilities
        4. Evaluate expressions with context
        5. Build ToolCandidate objects
        6. Skip invalid patterns (log errors)
        
        Args:
            required_capabilities: List of capability names (e.g., ["asset_query"])
            context: Runtime context for expression evaluation
                     Expected keys: N, pages, p95_latency, etc.
                     
        Returns:
            List of ToolCandidate objects with evaluated metrics
            
        Examples:
            >>> enumerator = CandidateEnumerator()
            >>> candidates = enumerator.enumerate_candidates(
            ...     required_capabilities=["asset_query"],
            ...     context={"N": 100}
            ... )
            >>> len(candidates) > 0
            True
            >>> candidates[0].estimated_time_ms > 0
            True
        """
        # PERMANENT FIX: Normalize capability names to canonical versions
        try:
            from capability_validation_hook import normalize_stage_a_capabilities
            required_capabilities = normalize_stage_a_capabilities(required_capabilities)
            logger.debug(f"Normalized capabilities: {required_capabilities}")
        except ImportError:
            logger.warning("Capability normalization hook not available - using raw capabilities")
        except Exception as e:
            logger.error(f"Capability normalization failed: {e} - using raw capabilities")
        
        # Default context if not provided
        if context is None:
            context = self._default_context()
        
        # Load profiles (cached after first load)
        if self._profiles is None:
            self._profiles = self.profile_loader.load()
        
        candidates = []
        
        # Iterate through all tools and their capabilities
        for tool_name, tool_profile in self._profiles.tools.items():
            for capability_name, capability_profile in tool_profile.capabilities.items():
                # Check if this capability matches requirements
                if capability_name not in required_capabilities:
                    continue
                
                # Enumerate all patterns for this capability
                for pattern_name, pattern in capability_profile.patterns.items():
                    try:
                        candidate = self._build_candidate(
                            tool_name=tool_name,
                            capability_name=capability_name,
                            pattern_name=pattern_name,
                            pattern=pattern,
                            context=context
                        )
                        candidates.append(candidate)
                        
                    except Exception as e:
                        # Log error but continue (fail gracefully)
                        logger.warning(
                            f"Failed to evaluate pattern {tool_name}.{capability_name}.{pattern_name}: {e}"
                        )
                        continue
        
        logger.info(
            f"Enumerated {len(candidates)} candidates for capabilities: {required_capabilities}"
        )
        
        return candidates
    
    def _build_candidate(
        self,
        tool_name: str,
        capability_name: str,
        pattern_name: str,
        pattern: PatternProfile,
        context: Dict[str, Any]
    ) -> ToolCandidate:
        """
        Build a ToolCandidate from a pattern profile.
        
        Evaluates all expressions with runtime context.
        
        Args:
            tool_name: Tool name
            capability_name: Capability name
            pattern_name: Pattern name
            pattern: PatternProfile from YAML
            context: Runtime context for evaluation
            
        Returns:
            ToolCandidate with evaluated metrics
            
        Raises:
            Exception: If expression evaluation fails
        """
        # Evaluate time estimate
        time_ms = self._evaluate_metric(
            pattern.time_estimate_ms,
            context,
            metric_name="time_estimate_ms"
        )
        
        # Evaluate cost estimate
        cost = self._evaluate_metric(
            pattern.cost_estimate,
            context,
            metric_name="cost_estimate"
        )
        
        # Build candidate
        candidate = ToolCandidate(
            tool_name=tool_name,
            capability_name=capability_name,
            pattern_name=pattern_name,
            estimated_time_ms=time_ms,
            estimated_cost=cost,
            complexity=pattern.complexity_score,
            accuracy=pattern.preference_match.accuracy,
            completeness=pattern.preference_match.completeness,
            policy=pattern.policy,
            description=pattern.description,
            typical_use_cases=pattern.typical_use_cases,
            limitations=pattern.limitations,
            accuracy_level=pattern.accuracy_level,
            freshness=pattern.freshness,
            scope=pattern.scope,
            data_source=pattern.data_source
        )
        
        return candidate
    
    def _evaluate_metric(
        self,
        value: Any,
        context: Dict[str, Any],
        metric_name: str
    ) -> float:
        """
        Evaluate a metric value (number or expression).
        
        Args:
            value: Metric value (int, float, or expression string)
            context: Runtime context for evaluation
            metric_name: Metric name (for error messages)
            
        Returns:
            Evaluated float value
            
        Raises:
            ValueError: If evaluation fails
        """
        # If already a number, return it
        if isinstance(value, (int, float)):
            return float(value)
        
        # If string, evaluate as expression
        if isinstance(value, str):
            try:
                evaluator = SafeMathEvaluator()
                result = evaluator.evaluate(value, context)
                return float(result)
            except Exception as e:
                raise ValueError(
                    f"Failed to evaluate {metric_name} expression '{value}': {e}"
                )
        
        raise ValueError(
            f"Invalid {metric_name} value type: {type(value)}. "
            f"Expected int, float, or expression string."
        )
    
    def _default_context(self) -> Dict[str, Any]:
        """
        Get default runtime context.
        
        Used when no context is provided. These are conservative estimates
        that should work for most queries.
        
        Returns:
            Default context dictionary
        """
        return {
            "N": 100,           # Assume 100 assets
            "pages": 1,         # Assume 1 page of results
            "p95_latency": 1000 # Assume 1s p95 latency
        }
    
    def estimate_context(
        self,
        query: str,
        intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate runtime context from query and metadata.
        
        This is a heuristic-based estimation. In the future, this could be
        enhanced with:
        - Historical query patterns
        - Asset count from database
        - Real-time latency metrics
        
        Args:
            query: User query text
            intent: Query intent (e.g., "QUERY_ASSETS")
            metadata: Additional metadata from Stage A
            
        Returns:
            Estimated context dictionary
            
        Examples:
            >>> enumerator = CandidateEnumerator()
            >>> ctx = enumerator.estimate_context("count all Linux assets")
            >>> ctx["N"] >= 1
            True
        """
        context = self._default_context()
        
        # Heuristic: detect "all" keyword → assume larger N
        if "all" in query.lower() or "every" in query.lower():
            context["N"] = 1000  # Larger dataset
        
        # Heuristic: detect "single" or specific ID → assume N=1
        if "single" in query.lower() or "one" in query.lower():
            context["N"] = 1
        
        # Heuristic: detect pagination keywords
        if "page" in query.lower() or "paginate" in query.lower():
            context["pages"] = 5  # Assume multiple pages
        
        # Override with metadata if provided
        if metadata:
            if "asset_count" in metadata:
                context["N"] = metadata["asset_count"]
            if "page_count" in metadata:
                context["pages"] = metadata["page_count"]
            if "p95_latency" in metadata:
                context["p95_latency"] = metadata["p95_latency"]
        
        return context
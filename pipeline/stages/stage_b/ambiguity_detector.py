"""
Ambiguity Detector - Phase 4 Module 1/2

Detects ambiguous tool selection cases where top-2 candidates have similar scores.
When ambiguity is detected, generates clarifying questions to help the user.

Ambiguity Threshold:
    |score_1 - score_2| < 0.08 (8% difference)
    
When scores are this close, the deterministic scorer cannot confidently choose.
We delegate to the LLM tie-breaker for nuanced decision-making.

Design Principles:
1. Conservative threshold (8%) - only delegate when truly ambiguous
2. Generate helpful clarifying questions based on feature differences
3. Fallback to deterministic winner if LLM unavailable
4. Log ambiguity events for telemetry
"""

import math
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class AmbiguityResult:
    """Result of ambiguity detection"""
    is_ambiguous: bool
    clarifying_question: Optional[str] = None
    score_difference: float = 0.0
    top_candidates: List[str] = None  # Tool names for logging
    
    def __post_init__(self):
        if self.top_candidates is None:
            self.top_candidates = []


class AmbiguityDetector:
    """
    Detects ambiguous tool selection cases.
    
    When top-2 candidates have scores within EPSILON (8%), we consider
    the decision ambiguous and delegate to LLM tie-breaker.
    """
    
    # Ambiguity threshold: 8% score difference
    # Rationale: Below this threshold, small variations in context or
    # user intent could flip the decision. Better to ask LLM.
    EPSILON = 0.08
    
    # Normalization bounds (must match FeatureNormalizer)
    MIN_TIME = 50.0      # 50ms = instant
    MAX_TIME = 60000.0   # 60s = very slow
    MIN_COST = 0.0       # Free
    MAX_COST = 10.0      # $10 per query
    
    def detect_ambiguity(
        self,
        ranked_candidates: List,
        epsilon: Optional[float] = None
    ) -> AmbiguityResult:
        """
        Detect if top-2 candidates are too close to call.
        
        Args:
            ranked_candidates: List of scored candidates sorted by score (descending)
                Can be either dicts or ScoredCandidate dataclass objects
            epsilon: Optional custom threshold (default: 0.08)
        
        Returns:
            AmbiguityResult with detection status and clarifying question
        """
        threshold = epsilon if epsilon is not None else self.EPSILON
        
        # Need at least 2 candidates to have ambiguity
        if len(ranked_candidates) < 2:
            tool_name = self._get_field(ranked_candidates[0], 'tool_name') if ranked_candidates else None
            return AmbiguityResult(
                is_ambiguous=False,
                score_difference=0.0,
                top_candidates=[tool_name] if tool_name else []
            )
        
        top1 = ranked_candidates[0]
        top2 = ranked_candidates[1]
        
        score1 = self._get_field(top1, 'total_score')
        score2 = self._get_field(top2, 'total_score')
        score_diff = abs(score1 - score2)
        
        # Check if ambiguous
        if score_diff < threshold:
            # Generate clarifying question
            question = self._generate_clarifying_question(top1, top2)
            
            return AmbiguityResult(
                is_ambiguous=True,
                clarifying_question=question,
                score_difference=score_diff,
                top_candidates=[
                    self._get_field(top1, 'tool_name'),
                    self._get_field(top2, 'tool_name')
                ]
            )
        
        # Clear winner
        return AmbiguityResult(
            is_ambiguous=False,
            score_difference=score_diff,
            top_candidates=[
                self._get_field(top1, 'tool_name'),
                self._get_field(top2, 'tool_name')
            ]
        )
    
    def _get_field(self, candidate, field_name: str):
        """
        Get field from candidate (supports both dict and dataclass).
        
        Args:
            candidate: Candidate object (dict or dataclass)
            field_name: Field name to retrieve
        
        Returns:
            Field value
        """
        if isinstance(candidate, dict):
            return candidate.get(field_name)
        else:
            return getattr(candidate, field_name, None)
    
    def _generate_clarifying_question(
        self,
        candidate1,
        candidate2
    ) -> str:
        """
        Generate a clarifying question to help choose between candidates.
        
        Strategy: Find the dimension with the largest difference and ask about it.
        This helps the user understand the trade-off.
        
        Args:
            candidate1: First candidate (dict or dataclass)
            candidate2: Second candidate (dict or dataclass)
        
        Returns:
            Clarifying question string
        """
        # Extract raw features
        raw1 = self._get_field(candidate1, 'raw_features') or {}
        raw2 = self._get_field(candidate2, 'raw_features') or {}
        
        # Calculate normalized differences for each dimension
        diffs = {}
        
        # Time difference (normalized)
        time1 = raw1.get('time_ms', 0)
        time2 = raw2.get('time_ms', 0)
        diffs['speed'] = abs(self._normalize_time(time1) - self._normalize_time(time2))
        
        # Cost difference (normalized)
        cost1 = raw1.get('cost', 0)
        cost2 = raw2.get('cost', 0)
        diffs['cost'] = abs(self._normalize_cost(cost1) - self._normalize_cost(cost2))
        
        # Accuracy difference (already normalized)
        acc1 = raw1.get('accuracy', 0.5)
        acc2 = raw2.get('accuracy', 0.5)
        diffs['accuracy'] = abs(acc1 - acc2)
        
        # Completeness difference (already normalized)
        comp1 = raw1.get('completeness', 0.5)
        comp2 = raw2.get('completeness', 0.5)
        diffs['completeness'] = abs(comp1 - comp2)
        
        # Complexity difference (already normalized)
        complex1 = raw1.get('complexity', 0.5)
        complex2 = raw2.get('complexity', 0.5)
        diffs['complexity'] = abs(complex1 - complex2)
        
        # Find dimension with largest difference
        if not diffs:
            return "Do you prefer speed or accuracy?"
        
        max_dim = max(diffs, key=diffs.get)
        max_diff = diffs[max_dim]
        
        # If all differences are tiny, ask generic question
        if max_diff < 0.05:
            return "Do you prefer speed or accuracy?"
        
        # Generate question based on dimension
        questions = {
            "speed": "Do you need results immediately, or can you wait a bit longer for more accuracy?",
            "accuracy": "Do you need highly accurate real-time data, or is cached data acceptable?",
            "cost": "Are you willing to pay more for better results?",
            "completeness": "Do you need all details, or is a summary sufficient?",
            "complexity": "Do you prefer a simple approach or a more comprehensive one?"
        }
        
        return questions.get(max_dim, "Do you prefer speed or accuracy?")
    
    def _normalize_time(self, time_ms: float) -> float:
        """
        Normalize time to [0,1] where 1 is best (fastest).
        Must match FeatureNormalizer implementation.
        """
        if time_ms <= self.MIN_TIME:
            return 1.0
        if time_ms >= self.MAX_TIME:
            return 0.0
        
        log_time = math.log(time_ms)
        log_min = math.log(self.MIN_TIME)
        log_max = math.log(self.MAX_TIME)
        
        normalized = 1.0 - (log_time - log_min) / (log_max - log_min)
        return max(0.0, min(1.0, normalized))
    
    def _normalize_cost(self, cost: float) -> float:
        """
        Normalize cost to [0,1] where 1 is best (cheapest).
        Must match FeatureNormalizer implementation.
        """
        if cost <= self.MIN_COST:
            return 1.0
        if cost >= self.MAX_COST:
            return 0.0
        
        normalized = 1.0 - (cost - self.MIN_COST) / (self.MAX_COST - self.MIN_COST)
        return max(0.0, min(1.0, normalized))
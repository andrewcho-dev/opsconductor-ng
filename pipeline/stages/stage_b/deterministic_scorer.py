"""
Deterministic Scorer - Phase 2 Module 2/3

Computes weighted scores for tool candidates using normalized features.
This is the "source of truth" for tool selection - deterministic and explainable.

Scoring Formula:
    score = Σ(weight_i × normalized_feature_i)
    
Where weights come from user preferences (detected from query):
- fast mode: high weight on time
- accurate mode: high weight on accuracy
- balanced mode: equal weights
- cost-conscious: high weight on cost

Design Principles:
1. Deterministic (same inputs = same outputs)
2. Explainable (can show why tool was selected)
3. Preference-driven (respects user intent)
4. Bounded [0,1] (normalized features × normalized weights)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PreferenceMode(Enum):
    """User preference modes detected from query"""
    FAST = "fast"           # Prioritize speed
    ACCURATE = "accurate"   # Prioritize accuracy
    THOROUGH = "thorough"   # Prioritize completeness
    CHEAP = "cheap"         # Prioritize low cost
    SIMPLE = "simple"       # Prioritize low complexity
    BALANCED = "balanced"   # Equal weights (default)


@dataclass
class FeatureWeights:
    """Weights for each feature dimension [0,1], must sum to 1.0"""
    time: float = 0.2
    cost: float = 0.2
    complexity: float = 0.2
    accuracy: float = 0.2
    completeness: float = 0.2
    
    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = self.time + self.cost + self.complexity + self.accuracy + self.completeness
        if not (0.99 <= total <= 1.01):  # Allow small floating point error
            raise ValueError(f"Feature weights must sum to 1.0, got {total}")
    
    @classmethod
    def from_mode(cls, mode: PreferenceMode) -> 'FeatureWeights':
        """
        Create weights from preference mode.
        
        Weight Distribution Strategy:
        - Primary dimension: 0.4 (40%)
        - Secondary dimensions: 0.15 each (15% × 4 = 60%)
        - Total: 100%
        
        Args:
            mode: User preference mode
            
        Returns:
            FeatureWeights configured for the mode
        """
        if mode == PreferenceMode.FAST:
            return cls(time=0.4, cost=0.15, complexity=0.15, accuracy=0.15, completeness=0.15)
        elif mode == PreferenceMode.ACCURATE:
            return cls(time=0.15, cost=0.15, complexity=0.15, accuracy=0.4, completeness=0.15)
        elif mode == PreferenceMode.THOROUGH:
            return cls(time=0.15, cost=0.15, complexity=0.15, accuracy=0.15, completeness=0.4)
        elif mode == PreferenceMode.CHEAP:
            return cls(time=0.15, cost=0.4, complexity=0.15, accuracy=0.15, completeness=0.15)
        elif mode == PreferenceMode.SIMPLE:
            return cls(time=0.15, cost=0.15, complexity=0.4, accuracy=0.15, completeness=0.15)
        else:  # BALANCED (default)
            return cls(time=0.2, cost=0.2, complexity=0.2, accuracy=0.2, completeness=0.2)


@dataclass
class ScoredCandidate:
    """Tool candidate with computed score and breakdown"""
    tool_name: str
    pattern_name: str
    total_score: float
    feature_scores: Dict[str, float]  # Normalized features [0,1]
    weighted_contributions: Dict[str, float]  # weight × feature
    justification: str
    raw_features: Dict[str, Any]  # Original feature values


class DeterministicScorer:
    """
    Computes deterministic scores for tool candidates.
    
    This is the mathematical "source of truth" for tool selection.
    LLM is only used for tie-breaking when scores are too close.
    
    Usage:
        scorer = DeterministicScorer()
        candidates = [
            {'tool_name': 'asset-service-query', 'pattern': 'count', 
             'features': {'time_ms': 500, 'cost': 0.05, 'complexity': 0.3, 
                         'accuracy': 0.9, 'completeness': 0.95}},
            {'tool_name': 'asset-direct-poll', 'pattern': 'parallel',
             'features': {'time_ms': 2000, 'cost': 0.0, 'complexity': 0.6,
                         'accuracy': 1.0, 'completeness': 1.0}}
        ]
        scored = scorer.score_candidates(candidates, mode=PreferenceMode.FAST)
        best = scored[0]  # Highest score first
    """
    
    def __init__(self):
        """Initialize deterministic scorer"""
        pass
    
    def score_candidates(self, 
                        candidates: List[Dict[str, Any]], 
                        mode: PreferenceMode = PreferenceMode.BALANCED,
                        custom_weights: Optional[FeatureWeights] = None) -> List[ScoredCandidate]:
        """
        Score and rank tool candidates.
        
        Args:
            candidates: List of tool candidates with normalized features
            mode: User preference mode (ignored if custom_weights provided)
            custom_weights: Optional custom feature weights
            
        Returns:
            List of ScoredCandidate objects, sorted by score (descending)
            
        Example:
            >>> scorer = DeterministicScorer()
            >>> candidates = [
            ...     {'tool_name': 'tool1', 'pattern': 'fast', 
            ...      'features': {'time_ms': 0.9, 'cost': 0.8, 'complexity': 0.7,
            ...                  'accuracy': 0.85, 'completeness': 0.9}},
            ...     {'tool_name': 'tool2', 'pattern': 'accurate',
            ...      'features': {'time_ms': 0.6, 'cost': 0.9, 'complexity': 0.5,
            ...                  'accuracy': 0.95, 'completeness': 0.95}}
            ... ]
            >>> scored = scorer.score_candidates(candidates, PreferenceMode.FAST)
            >>> scored[0].tool_name  # 'tool1' (higher time weight)
        """
        # Get weights
        weights = custom_weights or FeatureWeights.from_mode(mode)
        
        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            scored = self._score_single_candidate(candidate, weights)
            scored_candidates.append(scored)
        
        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x.total_score, reverse=True)
        
        return scored_candidates
    
    def _score_single_candidate(self, 
                                candidate: Dict[str, Any], 
                                weights: FeatureWeights) -> ScoredCandidate:
        """
        Score a single candidate.
        
        Args:
            candidate: Tool candidate with features
            weights: Feature weights
            
        Returns:
            ScoredCandidate with computed score
        """
        features = candidate.get('features', {})
        tool_name = candidate.get('tool_name', 'unknown')
        pattern_name = candidate.get('pattern', 'default')
        
        # Extract normalized features (should already be [0,1])
        time_score = features.get('time_ms', 0.5)
        cost_score = features.get('cost', 0.5)
        complexity_score = features.get('complexity', 0.5)
        accuracy_score = features.get('accuracy', 0.5)
        completeness_score = features.get('completeness', 0.5)
        
        # Compute weighted contributions
        weighted_contributions = {
            'time': weights.time * time_score,
            'cost': weights.cost * cost_score,
            'complexity': weights.complexity * complexity_score,
            'accuracy': weights.accuracy * accuracy_score,
            'completeness': weights.completeness * completeness_score
        }
        
        # Total score (sum of weighted contributions)
        total_score = sum(weighted_contributions.values())
        
        # Generate justification
        justification = self._generate_justification(
            tool_name, pattern_name, total_score, 
            features, weighted_contributions, weights
        )
        
        return ScoredCandidate(
            tool_name=tool_name,
            pattern_name=pattern_name,
            total_score=total_score,
            feature_scores=features,
            weighted_contributions=weighted_contributions,
            justification=justification,
            raw_features=candidate.get('raw_features', {})
        )
    
    def _generate_justification(self, 
                               tool_name: str,
                               pattern_name: str,
                               total_score: float,
                               features: Dict[str, float],
                               contributions: Dict[str, float],
                               weights: FeatureWeights) -> str:
        """
        Generate human-readable justification for score.
        
        Args:
            tool_name: Tool name
            pattern_name: Pattern name
            total_score: Total computed score
            features: Normalized feature scores
            contributions: Weighted contributions
            weights: Feature weights
            
        Returns:
            Justification string
        """
        # Find top contributing factors (top 2)
        sorted_contributions = sorted(
            contributions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        top_factors = sorted_contributions[:2]
        
        # Build justification
        justification_parts = [
            f"Score: {total_score:.3f}",
            f"Tool: {tool_name} ({pattern_name})"
        ]
        
        # Add top factors
        for factor, contribution in top_factors:
            feature_score = features.get(factor, 0.0)
            weight = getattr(weights, factor)
            justification_parts.append(
                f"{factor.capitalize()}: {feature_score:.2f} (weight: {weight:.2f}, contribution: {contribution:.3f})"
            )
        
        return " | ".join(justification_parts)
    
    def compute_score_gap(self, scored_candidates: List[ScoredCandidate]) -> float:
        """
        Compute gap between top 2 candidates (for ambiguity detection).
        
        Args:
            scored_candidates: List of scored candidates (sorted by score)
            
        Returns:
            Score gap [0,1] between top 2 candidates (0 = tie, 1 = clear winner)
            Returns 1.0 if only one candidate
        """
        if len(scored_candidates) < 2:
            return 1.0  # Clear winner (only one option)
        
        top_score = scored_candidates[0].total_score
        second_score = scored_candidates[1].total_score
        
        gap = abs(top_score - second_score)
        return gap
    
    def is_ambiguous(self, 
                    scored_candidates: List[ScoredCandidate], 
                    threshold: float = 0.08) -> bool:
        """
        Check if top candidates are too close (ambiguous).
        
        Args:
            scored_candidates: List of scored candidates (sorted by score)
            threshold: Ambiguity threshold (default: 0.08 = 8% difference)
            
        Returns:
            True if gap < threshold (ambiguous), False otherwise
            
        Example:
            >>> scorer = DeterministicScorer()
            >>> # ... score candidates ...
            >>> if scorer.is_ambiguous(scored):
            ...     # Use LLM tie-breaker
            ...     pass
        """
        gap = self.compute_score_gap(scored_candidates)
        return gap < threshold


# Convenience function for quick scoring
def score_candidates(candidates: List[Dict[str, Any]], 
                    mode: PreferenceMode = PreferenceMode.BALANCED) -> List[ScoredCandidate]:
    """
    Convenience function for scoring candidates.
    
    Args:
        candidates: List of tool candidates with features
        mode: User preference mode
        
    Returns:
        List of scored candidates (sorted by score)
        
    Example:
        >>> from pipeline.stages.stage_b.deterministic_scorer import score_candidates, PreferenceMode
        >>> scored = score_candidates(candidates, PreferenceMode.FAST)
    """
    scorer = DeterministicScorer()
    return scorer.score_candidates(candidates, mode)
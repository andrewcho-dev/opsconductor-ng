"""
Feature Normalizer - Phase 2 Module 1/3

Normalizes raw performance features to [0,1] scale for fair comparison:
- time_ms: Bounded log transform (50ms-60s range)
- cost: Bounded linear transform ($0-$10 range)
- complexity: Invert to [0,1] (lower complexity = higher score)
- accuracy, completeness: Already [0,1] from profiles

Mathematical Approach:
- Log scale for time (captures human perception of speed)
- Linear scale for cost (direct proportional value)
- Bounded transforms prevent outliers from dominating
"""

import math
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class NormalizationConfig:
    """Configuration for feature normalization bounds"""
    # Time normalization (milliseconds)
    time_min_ms: float = 50.0      # 50ms = instant (normalized to 1.0)
    time_max_ms: float = 60000.0   # 60s = very slow (normalized to 0.0)
    
    # Cost normalization (dollars)
    cost_min: float = 0.0          # $0 = free (normalized to 1.0)
    cost_max: float = 10.0         # $10 = expensive (normalized to 0.0)
    
    # Complexity normalization (already [0,1] in profiles)
    complexity_min: float = 0.0    # 0 = simple (normalized to 1.0)
    complexity_max: float = 1.0    # 1 = complex (normalized to 0.0)


class FeatureNormalizer:
    """
    Normalizes raw performance features to [0,1] scale.
    
    Design Principles:
    1. Higher normalized values = better (more desirable)
    2. Bounded transforms prevent outliers
    3. Log scale for time (human perception)
    4. Linear scale for cost (direct value)
    5. Invert complexity (simpler is better)
    
    Usage:
        normalizer = FeatureNormalizer()
        normalized = normalizer.normalize_features({
            'time_ms': 500,
            'cost': 0.05,
            'complexity': 0.3,
            'accuracy': 0.9,
            'completeness': 0.95
        })
    """
    
    def __init__(self, config: Optional[NormalizationConfig] = None):
        """
        Initialize feature normalizer.
        
        Args:
            config: Optional normalization configuration (uses defaults if not provided)
        """
        self.config = config or NormalizationConfig()
    
    def normalize_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize all features to [0,1] scale.
        
        Args:
            features: Raw feature values (time_ms, cost, complexity, accuracy, completeness)
            
        Returns:
            Dictionary of normalized features (all in [0,1] range, higher = better)
            
        Example:
            >>> normalizer = FeatureNormalizer()
            >>> features = {'time_ms': 500, 'cost': 0.05, 'complexity': 0.3}
            >>> normalized = normalizer.normalize_features(features)
            >>> normalized['time_ms']  # ~0.85 (fast)
            >>> normalized['cost']     # ~0.995 (cheap)
            >>> normalized['complexity']  # ~0.7 (simple)
        """
        normalized = {}
        
        # Normalize time (log scale, inverted: faster = higher score)
        if 'time_ms' in features:
            normalized['time_ms'] = self._normalize_time(features['time_ms'])
        
        # Normalize cost (linear scale, inverted: cheaper = higher score)
        if 'cost' in features:
            normalized['cost'] = self._normalize_cost(features['cost'])
        
        # Normalize complexity (inverted: simpler = higher score)
        if 'complexity' in features:
            normalized['complexity'] = self._normalize_complexity(features['complexity'])
        
        # Accuracy and completeness are already [0,1] (higher = better)
        if 'accuracy' in features:
            normalized['accuracy'] = self._clamp(features['accuracy'], 0.0, 1.0)
        
        if 'completeness' in features:
            normalized['completeness'] = self._clamp(features['completeness'], 0.0, 1.0)
        
        return normalized
    
    def _normalize_time(self, time_ms: float) -> float:
        """
        Normalize time using bounded log transform.
        
        Formula: 1 - (log(t) - log(t_min)) / (log(t_max) - log(t_min))
        
        Rationale:
        - Log scale captures human perception (100ms→200ms feels like 1s→2s)
        - Bounded to [50ms, 60s] range
        - Inverted so faster = higher score
        
        Args:
            time_ms: Time in milliseconds
            
        Returns:
            Normalized time score [0,1] where 1.0 = fastest, 0.0 = slowest
        """
        # Clamp to bounds
        time_ms = self._clamp(time_ms, self.config.time_min_ms, self.config.time_max_ms)
        
        # Log transform
        log_time = math.log(time_ms)
        log_min = math.log(self.config.time_min_ms)
        log_max = math.log(self.config.time_max_ms)
        
        # Normalize to [0,1] and invert (faster = higher)
        normalized = 1.0 - (log_time - log_min) / (log_max - log_min)
        
        return self._clamp(normalized, 0.0, 1.0)
    
    def _normalize_cost(self, cost: float) -> float:
        """
        Normalize cost using bounded linear transform.
        
        Formula: 1 - (c - c_min) / (c_max - c_min)
        
        Rationale:
        - Linear scale (cost is directly proportional)
        - Bounded to [$0, $10] range
        - Inverted so cheaper = higher score
        
        Args:
            cost: Cost in dollars
            
        Returns:
            Normalized cost score [0,1] where 1.0 = cheapest, 0.0 = most expensive
        """
        # Clamp to bounds
        cost = self._clamp(cost, self.config.cost_min, self.config.cost_max)
        
        # Linear transform and invert (cheaper = higher)
        normalized = 1.0 - (cost - self.config.cost_min) / (self.config.cost_max - self.config.cost_min)
        
        return self._clamp(normalized, 0.0, 1.0)
    
    def _normalize_complexity(self, complexity: float) -> float:
        """
        Normalize complexity (invert so simpler = higher score).
        
        Formula: 1 - c
        
        Rationale:
        - Complexity already in [0,1] from profiles
        - Invert so simpler = higher score
        
        Args:
            complexity: Complexity score [0,1] where 0 = simple, 1 = complex
            
        Returns:
            Normalized complexity score [0,1] where 1.0 = simplest, 0.0 = most complex
        """
        # Clamp to [0,1]
        complexity = self._clamp(complexity, self.config.complexity_min, self.config.complexity_max)
        
        # Invert (simpler = higher)
        normalized = 1.0 - complexity
        
        return self._clamp(normalized, 0.0, 1.0)
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to [min_val, max_val] range"""
        return max(min_val, min(max_val, value))
    
    def denormalize_time(self, normalized_time: float) -> float:
        """
        Convert normalized time back to milliseconds (for debugging/display).
        
        Args:
            normalized_time: Normalized time score [0,1]
            
        Returns:
            Time in milliseconds
        """
        # Invert normalization
        log_ratio = 1.0 - normalized_time
        log_min = math.log(self.config.time_min_ms)
        log_max = math.log(self.config.time_max_ms)
        log_time = log_min + log_ratio * (log_max - log_min)
        
        return math.exp(log_time)
    
    def denormalize_cost(self, normalized_cost: float) -> float:
        """
        Convert normalized cost back to dollars (for debugging/display).
        
        Args:
            normalized_cost: Normalized cost score [0,1]
            
        Returns:
            Cost in dollars
        """
        # Invert normalization
        cost_ratio = 1.0 - normalized_cost
        cost = self.config.cost_min + cost_ratio * (self.config.cost_max - self.config.cost_min)
        
        return cost


# Convenience function for quick normalization
def normalize_features(features: Dict[str, Any], 
                       config: Optional[NormalizationConfig] = None) -> Dict[str, float]:
    """
    Convenience function for feature normalization.
    
    Args:
        features: Raw feature values
        config: Optional normalization configuration
        
    Returns:
        Normalized features [0,1]
        
    Example:
        >>> from pipeline.stages.stage_b.feature_normalizer import normalize_features
        >>> normalized = normalize_features({'time_ms': 500, 'cost': 0.05})
    """
    normalizer = FeatureNormalizer(config)
    return normalizer.normalize_features(features)
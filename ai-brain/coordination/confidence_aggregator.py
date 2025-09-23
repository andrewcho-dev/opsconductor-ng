"""
Confidence Aggregator for Multi-Brain AI Architecture

This module provides sophisticated confidence aggregation algorithms
for combining confidence scores from multiple AI brains.
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

class AggregationMethod(Enum):
    """Confidence aggregation methods."""
    WEIGHTED_AVERAGE = "weighted_average"
    HARMONIC_MEAN = "harmonic_mean"
    GEOMETRIC_MEAN = "geometric_mean"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    CONSENSUS = "consensus"

@dataclass
class ConfidenceScore:
    """Individual confidence score from a brain."""
    brain_id: str
    confidence: float
    weight: float = 1.0
    reasoning: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class AggregatedConfidence:
    """Aggregated confidence result."""
    final_confidence: float
    method_used: AggregationMethod
    individual_scores: List[ConfidenceScore]
    confidence_variance: float
    consensus_level: float
    reasoning: str

class ConfidenceAggregator:
    """
    Advanced confidence aggregation system for multi-brain coordination.
    
    Provides multiple aggregation methods and intelligent selection
    based on the context and brain characteristics.
    """
    
    def __init__(self):
        """Initialize the confidence aggregator."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Confidence Aggregator initialized")
    
    async def aggregate_confidence(
        self,
        confidence_scores: List[ConfidenceScore],
        method: Optional[AggregationMethod] = None,
        context: Optional[Dict] = None
    ) -> AggregatedConfidence:
        """
        Aggregate confidence scores from multiple brains.
        
        Args:
            confidence_scores: List of confidence scores from different brains
            method: Aggregation method to use (auto-selected if None)
            context: Additional context for aggregation decisions
            
        Returns:
            AggregatedConfidence with final score and metadata
        """
        if not confidence_scores:
            return AggregatedConfidence(
                final_confidence=0.0,
                method_used=AggregationMethod.WEIGHTED_AVERAGE,
                individual_scores=[],
                confidence_variance=0.0,
                consensus_level=0.0,
                reasoning="No confidence scores provided"
            )
        
        # Auto-select method if not specified
        if method is None:
            method = self._select_aggregation_method(confidence_scores, context)
        
        # Calculate aggregated confidence
        final_confidence = self._calculate_confidence(confidence_scores, method)
        
        # Calculate variance and consensus
        confidence_values = [score.confidence for score in confidence_scores]
        confidence_variance = statistics.variance(confidence_values) if len(confidence_values) > 1 else 0.0
        consensus_level = self._calculate_consensus(confidence_values)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(confidence_scores, method, final_confidence)
        
        self.logger.info(f"Aggregated confidence: {final_confidence:.2%} using {method.value}")
        
        return AggregatedConfidence(
            final_confidence=final_confidence,
            method_used=method,
            individual_scores=confidence_scores,
            confidence_variance=confidence_variance,
            consensus_level=consensus_level,
            reasoning=reasoning
        )
    
    def _select_aggregation_method(
        self,
        confidence_scores: List[ConfidenceScore],
        context: Optional[Dict] = None
    ) -> AggregationMethod:
        """
        Intelligently select the best aggregation method.
        
        Args:
            confidence_scores: Individual confidence scores
            context: Additional context for decision making
            
        Returns:
            Selected aggregation method
        """
        num_scores = len(confidence_scores)
        confidence_values = [score.confidence for score in confidence_scores]
        
        # Calculate variance to determine consensus level
        variance = statistics.variance(confidence_values) if num_scores > 1 else 0.0
        
        # High consensus (low variance) - use weighted average
        if variance < 0.01:  # Very low variance
            return AggregationMethod.WEIGHTED_AVERAGE
        
        # Medium consensus - use harmonic mean (conservative)
        elif variance < 0.05:
            return AggregationMethod.HARMONIC_MEAN
        
        # Low consensus (high variance) - use consensus method
        else:
            return AggregationMethod.CONSENSUS
    
    def _calculate_confidence(
        self,
        confidence_scores: List[ConfidenceScore],
        method: AggregationMethod
    ) -> float:
        """
        Calculate confidence using the specified method.
        
        Args:
            confidence_scores: Individual confidence scores
            method: Aggregation method to use
            
        Returns:
            Aggregated confidence score (0.0 to 1.0)
        """
        if not confidence_scores:
            return 0.0
        
        confidence_values = [score.confidence for score in confidence_scores]
        weights = [score.weight for score in confidence_scores]
        
        if method == AggregationMethod.WEIGHTED_AVERAGE:
            total_weight = sum(weights)
            if total_weight == 0:
                return 0.0
            weighted_sum = sum(conf * weight for conf, weight in zip(confidence_values, weights))
            return weighted_sum / total_weight
        
        elif method == AggregationMethod.HARMONIC_MEAN:
            # Harmonic mean is conservative - dominated by lower values
            reciprocal_sum = sum(1.0 / max(conf, 0.001) for conf in confidence_values)
            return len(confidence_values) / reciprocal_sum
        
        elif method == AggregationMethod.GEOMETRIC_MEAN:
            # Geometric mean
            product = 1.0
            for conf in confidence_values:
                product *= max(conf, 0.001)  # Avoid zero
            return product ** (1.0 / len(confidence_values))
        
        elif method == AggregationMethod.MINIMUM:
            return min(confidence_values)
        
        elif method == AggregationMethod.MAXIMUM:
            return max(confidence_values)
        
        elif method == AggregationMethod.CONSENSUS:
            # Consensus method: weighted by agreement level
            mean_conf = statistics.mean(confidence_values)
            variance = statistics.variance(confidence_values) if len(confidence_values) > 1 else 0.0
            
            # Reduce confidence based on disagreement
            disagreement_penalty = min(variance * 2, 0.3)  # Max 30% penalty
            return max(mean_conf - disagreement_penalty, 0.0)
        
        else:
            # Default to weighted average
            return self._calculate_confidence(confidence_scores, AggregationMethod.WEIGHTED_AVERAGE)
    
    def _calculate_consensus(self, confidence_values: List[float]) -> float:
        """
        Calculate consensus level among confidence scores.
        
        Args:
            confidence_values: List of confidence values
            
        Returns:
            Consensus level (0.0 to 1.0, higher = more consensus)
        """
        if len(confidence_values) <= 1:
            return 1.0
        
        variance = statistics.variance(confidence_values)
        # Convert variance to consensus (inverse relationship)
        # High variance = low consensus, low variance = high consensus
        consensus = max(0.0, 1.0 - (variance * 4))  # Scale factor of 4
        return min(consensus, 1.0)
    
    def _generate_reasoning(
        self,
        confidence_scores: List[ConfidenceScore],
        method: AggregationMethod,
        final_confidence: float
    ) -> str:
        """
        Generate human-readable reasoning for the aggregation.
        
        Args:
            confidence_scores: Individual confidence scores
            method: Method used for aggregation
            final_confidence: Final aggregated confidence
            
        Returns:
            Reasoning string
        """
        num_brains = len(confidence_scores)
        confidence_values = [score.confidence for score in confidence_scores]
        
        if num_brains == 0:
            return "No brain confidence scores available"
        
        if num_brains == 1:
            return f"Single brain confidence: {confidence_values[0]:.2%}"
        
        mean_conf = statistics.mean(confidence_values)
        variance = statistics.variance(confidence_values) if num_brains > 1 else 0.0
        
        # Describe consensus level
        if variance < 0.01:
            consensus_desc = "high consensus"
        elif variance < 0.05:
            consensus_desc = "moderate consensus"
        else:
            consensus_desc = "low consensus"
        
        # Describe method rationale
        method_desc = {
            AggregationMethod.WEIGHTED_AVERAGE: "weighted average for balanced assessment",
            AggregationMethod.HARMONIC_MEAN: "harmonic mean for conservative estimate",
            AggregationMethod.GEOMETRIC_MEAN: "geometric mean for multiplicative effects",
            AggregationMethod.MINIMUM: "minimum for risk-averse approach",
            AggregationMethod.MAXIMUM: "maximum for optimistic estimate",
            AggregationMethod.CONSENSUS: "consensus method accounting for disagreement"
        }.get(method, "weighted average")
        
        return (f"Aggregated {num_brains} brain confidences "
                f"(mean: {mean_conf:.2%}, {consensus_desc}) "
                f"using {method_desc} → {final_confidence:.2%}")

# Global instance for easy access
confidence_aggregator = ConfidenceAggregator()
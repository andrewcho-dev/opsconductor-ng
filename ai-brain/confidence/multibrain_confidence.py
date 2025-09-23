"""
Multi-Brain Confidence Engine - Phase 2 Week 6 Implementation

This module implements the multi-brain confidence aggregation system:
- Confidence aggregation from all brain components
- Risk-adjusted decision logic
- Execution strategy selection
- Confidence calibration and learning
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import asyncio
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Execution strategies based on confidence levels"""
    AUTOMATED_EXECUTION = "automated_execution"     # High confidence, low risk
    GUIDED_EXECUTION = "guided_execution"           # Medium-high confidence
    ASSISTED_EXECUTION = "assisted_execution"       # Medium confidence
    MANUAL_REVIEW = "manual_review"                 # Low confidence or high risk
    EXPERT_CONSULTATION = "expert_consultation"     # Very low confidence
    ABORT_EXECUTION = "abort_execution"             # Safety concerns


class ConfidenceSource(Enum):
    """Sources of confidence in the multi-brain system"""
    INTENT_BRAIN = "intent_brain"
    TECHNICAL_BRAIN = "technical_brain"
    SME_CONTAINER = "sme_container"
    SME_SECURITY = "sme_security"
    SME_NETWORK = "sme_network"
    SME_DATABASE = "sme_database"
    EXECUTION_HISTORY = "execution_history"
    EXTERNAL_VALIDATION = "external_validation"


class RiskLevel(Enum):
    """Risk levels for execution"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BrainConfidence:
    """Confidence from a specific brain component"""
    source: ConfidenceSource
    confidence_score: float
    reasoning: str
    weight: float = 1.0
    reliability: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedConfidence:
    """Aggregated confidence from all brain components"""
    overall_confidence: float
    weighted_confidence: float
    confidence_variance: float
    brain_confidences: Dict[str, BrainConfidence]
    confidence_factors: Dict[str, float]
    risk_adjusted_confidence: float
    execution_strategy: ExecutionStrategy
    strategy_reasoning: str
    aggregation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceCalibration:
    """Confidence calibration data for learning"""
    predicted_confidence: float
    actual_success: bool
    execution_outcome: Dict[str, Any]
    calibration_error: float
    brain_source: str
    timestamp: datetime = field(default_factory=datetime.now)


class MultibrainConfidenceEngine:
    """
    Multi-Brain Confidence Engine for aggregating confidence and determining execution strategies
    
    This engine takes confidence scores from all brain components and:
    1. Aggregates them using weighted algorithms
    2. Adjusts for risk factors
    3. Determines appropriate execution strategy
    4. Learns from execution outcomes to improve calibration
    """
    
    def __init__(self):
        # Brain weights for confidence aggregation
        self.brain_weights = {
            ConfidenceSource.INTENT_BRAIN: 0.25,
            ConfidenceSource.TECHNICAL_BRAIN: 0.30,
            ConfidenceSource.SME_CONTAINER: 0.15,
            ConfidenceSource.SME_SECURITY: 0.15,
            ConfidenceSource.SME_NETWORK: 0.10,
            ConfidenceSource.SME_DATABASE: 0.10,
            ConfidenceSource.EXECUTION_HISTORY: 0.20,
            ConfidenceSource.EXTERNAL_VALIDATION: 0.15
        }
        
        # Execution strategy thresholds
        self.strategy_thresholds = {
            ExecutionStrategy.AUTOMATED_EXECUTION: 0.85,
            ExecutionStrategy.GUIDED_EXECUTION: 0.70,
            ExecutionStrategy.ASSISTED_EXECUTION: 0.55,
            ExecutionStrategy.MANUAL_REVIEW: 0.40,
            ExecutionStrategy.EXPERT_CONSULTATION: 0.25,
            ExecutionStrategy.ABORT_EXECUTION: 0.0
        }
        
        # Risk adjustment factors
        self.risk_adjustments = {
            RiskLevel.VERY_LOW: 1.1,    # Boost confidence for very low risk
            RiskLevel.LOW: 1.05,        # Slight boost for low risk
            RiskLevel.MEDIUM: 1.0,      # No adjustment for medium risk
            RiskLevel.HIGH: 0.8,        # Reduce confidence for high risk
            RiskLevel.CRITICAL: 0.5     # Significantly reduce for critical risk
        }
        
        # Calibration history for learning
        self.calibration_history: List[ConfidenceCalibration] = []
        self.brain_reliability_scores: Dict[str, float] = {}
        
        # Confidence aggregation metrics
        self.aggregation_metrics = {
            "total_aggregations": 0,
            "average_confidence": 0.0,
            "strategy_distribution": {strategy.value: 0 for strategy in ExecutionStrategy},
            "calibration_accuracy": 0.0,
            "risk_adjustment_frequency": 0
        }
        
        # Initialize brain reliability scores
        self._initialize_brain_reliability()
    
    def _initialize_brain_reliability(self):
        """Initialize brain reliability scores"""
        # Start with default reliability scores
        for source in ConfidenceSource:
            self.brain_reliability_scores[source.value] = 1.0
        
        # Adjust based on brain characteristics
        self.brain_reliability_scores[ConfidenceSource.EXECUTION_HISTORY.value] = 1.2  # Historical data is reliable
        self.brain_reliability_scores[ConfidenceSource.EXTERNAL_VALIDATION.value] = 0.9  # External sources need validation
    
    async def aggregate_confidence(self, brain_confidences: Dict[str, float], 
                                 risk_assessment: Optional[Dict[str, Any]] = None,
                                 execution_context: Optional[Dict[str, Any]] = None,
                                 complexity_factor: Optional[float] = None,
                                 risk_factor: Optional[float] = None) -> float:
        """
        Aggregate confidence from all brain components
        
        Args:
            brain_confidences: Dictionary of brain confidence scores
            risk_assessment: Optional risk assessment data
            execution_context: Optional execution context for adjustments
            complexity_factor: Optional complexity factor (0.0-1.0) for confidence adjustment
            risk_factor: Optional risk factor (0.0-1.0) for risk-based adjustments
            
        Returns:
            float: Final aggregated confidence score (0.0-1.0)
        """
        try:
            # Convert to BrainConfidence objects
            brain_confidence_objects = await self._create_brain_confidence_objects(brain_confidences)
            
            # Calculate basic aggregated confidence
            basic_confidence = await self._calculate_basic_confidence(brain_confidence_objects)
            
            # Calculate weighted confidence
            weighted_confidence = await self._calculate_weighted_confidence(brain_confidence_objects)
            
            # Calculate confidence variance
            confidence_variance = await self._calculate_confidence_variance(brain_confidence_objects)
            
            # Prepare enhanced risk assessment with provided factors
            enhanced_risk_assessment = risk_assessment or {}
            if risk_factor is not None:
                enhanced_risk_assessment['risk_factor'] = risk_factor
            if complexity_factor is not None:
                enhanced_risk_assessment['complexity_factor'] = complexity_factor
            
            # Apply risk adjustments
            risk_level = await self._assess_risk_level(enhanced_risk_assessment)
            risk_adjusted_confidence = await self._apply_risk_adjustments(weighted_confidence, risk_level)
            
            # Prepare enhanced execution context
            enhanced_execution_context = execution_context or {}
            if complexity_factor is not None:
                enhanced_execution_context['complexity_factor'] = complexity_factor
            
            # Apply context adjustments
            context_adjusted_confidence = await self._apply_context_adjustments(
                risk_adjusted_confidence, enhanced_execution_context
            )
            
            # Determine execution strategy
            execution_strategy, strategy_reasoning = await self._determine_execution_strategy(
                context_adjusted_confidence, risk_level, confidence_variance
            )
            
            # Create confidence factors breakdown
            confidence_factors = await self._calculate_confidence_factors(
                brain_confidence_objects, risk_level, enhanced_execution_context
            )
            
            # Create aggregated confidence result
            aggregated_confidence = AggregatedConfidence(
                overall_confidence=basic_confidence,
                weighted_confidence=weighted_confidence,
                confidence_variance=confidence_variance,
                brain_confidences={source.value: conf for source, conf in brain_confidence_objects.items()},
                confidence_factors=confidence_factors,
                risk_adjusted_confidence=context_adjusted_confidence,
                execution_strategy=execution_strategy,
                strategy_reasoning=strategy_reasoning,
                aggregation_metadata={
                    "risk_level": risk_level.value,
                    "brain_count": len(brain_confidence_objects),
                    "aggregation_timestamp": datetime.now().isoformat(),
                    "confidence_spread": max(brain_confidences.values()) - min(brain_confidences.values()) if brain_confidences else 0,
                    "dominant_brain": max(brain_confidences.items(), key=lambda x: x[1])[0] if brain_confidences else None
                }
            )
            
            # Update metrics
            await self._update_aggregation_metrics(aggregated_confidence)
            
            logger.info(f"Confidence aggregation completed: {context_adjusted_confidence:.3f} -> {execution_strategy.value}")
            return context_adjusted_confidence
            
        except Exception as e:
            logger.error(f"Error aggregating confidence: {str(e)}")
            
            # Return safe default confidence value
            return 0.3
    
    def determine_execution_strategy(self, confidence_score: float, brain_confidences: Dict[str, float]) -> str:
        """
        Determine execution strategy based on confidence score and brain agreement
        
        Args:
            confidence_score: Overall confidence score (0.0-1.0)
            brain_confidences: Individual brain confidence scores
            
        Returns:
            str: Execution strategy name
        """
        try:
            # Calculate confidence variance
            if brain_confidences:
                confidence_values = list(brain_confidences.values())
                variance = sum((x - confidence_score) ** 2 for x in confidence_values) / len(confidence_values)
            else:
                variance = 0.0
            
            # Determine strategy based on confidence and variance
            if confidence_score >= 0.9 and variance <= 0.05:
                return "automated_execution"
            elif confidence_score >= 0.8 and variance <= 0.1:
                return "supervised_execution"
            elif confidence_score >= 0.6 and variance <= 0.2:
                return "guided_execution"
            elif confidence_score >= 0.4:
                return "manual_review"
            else:
                return "expert_consultation"
                
        except Exception as e:
            logger.error(f"Error determining execution strategy: {str(e)}")
            return "manual_review"
    
    async def _create_brain_confidence_objects(self, brain_confidences: Dict[str, float]) -> Dict[ConfidenceSource, BrainConfidence]:
        """Create BrainConfidence objects from confidence scores"""
        brain_objects = {}
        
        for brain_name, confidence_score in brain_confidences.items():
            try:
                # Map brain name to confidence source
                if brain_name == "intent":
                    source = ConfidenceSource.INTENT_BRAIN
                elif brain_name == "technical":
                    source = ConfidenceSource.TECHNICAL_BRAIN
                elif "container" in brain_name.lower():
                    source = ConfidenceSource.SME_CONTAINER
                elif "security" in brain_name.lower():
                    source = ConfidenceSource.SME_SECURITY
                elif "network" in brain_name.lower():
                    source = ConfidenceSource.SME_NETWORK
                elif "database" in brain_name.lower():
                    source = ConfidenceSource.SME_DATABASE
                elif "history" in brain_name.lower():
                    source = ConfidenceSource.EXECUTION_HISTORY
                elif "external" in brain_name.lower():
                    source = ConfidenceSource.EXTERNAL_VALIDATION
                else:
                    # Default to technical brain for unknown sources
                    source = ConfidenceSource.TECHNICAL_BRAIN
                
                brain_confidence = BrainConfidence(
                    source=source,
                    confidence_score=confidence_score,
                    reasoning=f"Confidence from {brain_name}",
                    weight=self.brain_weights.get(source, 1.0),
                    reliability=self.brain_reliability_scores.get(source.value, 1.0)
                )
                
                brain_objects[source] = brain_confidence
                
            except Exception as e:
                logger.error(f"Error creating brain confidence object for {brain_name}: {str(e)}")
        
        return brain_objects
    
    async def _calculate_basic_confidence(self, brain_confidences: Dict[ConfidenceSource, BrainConfidence]) -> float:
        """Calculate basic (unweighted) average confidence"""
        if not brain_confidences:
            return 0.0
        
        total_confidence = sum(conf.confidence_score for conf in brain_confidences.values())
        return total_confidence / len(brain_confidences)
    
    async def _calculate_weighted_confidence(self, brain_confidences: Dict[ConfidenceSource, BrainConfidence]) -> float:
        """Calculate weighted confidence based on brain weights and reliability"""
        if not brain_confidences:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for source, brain_conf in brain_confidences.items():
            # Combine brain weight with reliability
            effective_weight = brain_conf.weight * brain_conf.reliability
            weighted_sum += brain_conf.confidence_score * effective_weight
            total_weight += effective_weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    async def _calculate_confidence_variance(self, brain_confidences: Dict[ConfidenceSource, BrainConfidence]) -> float:
        """Calculate variance in confidence scores"""
        if len(brain_confidences) < 2:
            return 0.0
        
        scores = [conf.confidence_score for conf in brain_confidences.values()]
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        return math.sqrt(variance)  # Return standard deviation
    
    async def _assess_risk_level(self, risk_assessment: Optional[Dict[str, Any]]) -> RiskLevel:
        """Assess overall risk level from risk assessment data"""
        if not risk_assessment:
            return RiskLevel.MEDIUM
        
        try:
            # Check for explicit risk level
            if "overall_risk_level" in risk_assessment:
                risk_str = risk_assessment["overall_risk_level"].lower()
                for risk_level in RiskLevel:
                    if risk_level.value in risk_str:
                        return risk_level
            
            # Calculate risk based on risk factors
            high_risks = risk_assessment.get("high_risk", [])
            medium_risks = risk_assessment.get("medium_risk", [])
            low_risks = risk_assessment.get("low_risk", [])
            
            # Simple risk scoring
            risk_score = len(high_risks) * 3 + len(medium_risks) * 2 + len(low_risks) * 1
            
            if risk_score >= 10:
                return RiskLevel.CRITICAL
            elif risk_score >= 7:
                return RiskLevel.HIGH
            elif risk_score >= 4:
                return RiskLevel.MEDIUM
            elif risk_score >= 2:
                return RiskLevel.LOW
            else:
                return RiskLevel.VERY_LOW
                
        except Exception as e:
            logger.error(f"Error assessing risk level: {str(e)}")
            return RiskLevel.MEDIUM
    
    async def _apply_risk_adjustments(self, confidence: float, risk_level: RiskLevel) -> float:
        """Apply risk adjustments to confidence score"""
        adjustment_factor = self.risk_adjustments.get(risk_level, 1.0)
        adjusted_confidence = confidence * adjustment_factor
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, adjusted_confidence))
    
    async def _apply_context_adjustments(self, confidence: float, 
                                       execution_context: Optional[Dict[str, Any]]) -> float:
        """Apply context-specific adjustments to confidence"""
        if not execution_context:
            return confidence
        
        try:
            adjusted_confidence = confidence
            
            # Time-based adjustments
            if "urgency" in execution_context:
                urgency = execution_context["urgency"].lower()
                if urgency == "high":
                    adjusted_confidence *= 0.95  # Slight reduction for urgent tasks
                elif urgency == "low":
                    adjusted_confidence *= 1.05  # Slight boost for non-urgent tasks
            
            # Complexity adjustments
            if "complexity" in execution_context:
                complexity = execution_context["complexity"].lower()
                if complexity == "high":
                    adjusted_confidence *= 0.9
                elif complexity == "very_high":
                    adjusted_confidence *= 0.8
                elif complexity == "low":
                    adjusted_confidence *= 1.1
            
            # Environment adjustments
            if "environment" in execution_context:
                env = execution_context["environment"].lower()
                if env == "production":
                    adjusted_confidence *= 0.9  # More conservative in production
                elif env == "development":
                    adjusted_confidence *= 1.05  # Less conservative in development
            
            # User experience adjustments
            if "user_experience" in execution_context:
                experience = execution_context["user_experience"].lower()
                if experience == "beginner":
                    adjusted_confidence *= 0.85  # More guidance for beginners
                elif experience == "expert":
                    adjusted_confidence *= 1.1  # More automation for experts
            
            # Ensure confidence stays within bounds
            return max(0.0, min(1.0, adjusted_confidence))
            
        except Exception as e:
            logger.error(f"Error applying context adjustments: {str(e)}")
            return confidence
    
    async def _determine_execution_strategy(self, confidence: float, risk_level: RiskLevel, 
                                          confidence_variance: float) -> Tuple[ExecutionStrategy, str]:
        """Determine execution strategy based on confidence and risk"""
        try:
            # Base strategy determination
            base_strategy = ExecutionStrategy.MANUAL_REVIEW
            for strategy, threshold in sorted(self.strategy_thresholds.items(), 
                                            key=lambda x: x[1], reverse=True):
                if confidence >= threshold:
                    base_strategy = strategy
                    break
            
            # Risk-based strategy adjustments
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                if base_strategy == ExecutionStrategy.AUTOMATED_EXECUTION:
                    base_strategy = ExecutionStrategy.GUIDED_EXECUTION
                    reasoning = f"Downgraded from automated to guided due to {risk_level.value} risk"
                elif base_strategy == ExecutionStrategy.GUIDED_EXECUTION:
                    base_strategy = ExecutionStrategy.ASSISTED_EXECUTION
                    reasoning = f"Downgraded from guided to assisted due to {risk_level.value} risk"
                else:
                    reasoning = f"Strategy maintained despite {risk_level.value} risk due to low confidence"
            
            # Variance-based adjustments
            elif confidence_variance > 0.3:  # High disagreement between brains
                if base_strategy == ExecutionStrategy.AUTOMATED_EXECUTION:
                    base_strategy = ExecutionStrategy.GUIDED_EXECUTION
                    reasoning = f"Downgraded due to high confidence variance ({confidence_variance:.2f})"
                else:
                    reasoning = f"Strategy maintained with high variance ({confidence_variance:.2f})"
            
            # Safety checks
            elif confidence < 0.2:
                base_strategy = ExecutionStrategy.ABORT_EXECUTION
                reasoning = "Confidence too low for safe execution"
            
            else:
                reasoning = f"Strategy based on confidence {confidence:.2f} and {risk_level.value} risk"
            
            return base_strategy, reasoning
            
        except Exception as e:
            logger.error(f"Error determining execution strategy: {str(e)}")
            return ExecutionStrategy.MANUAL_REVIEW, f"Error in strategy determination: {str(e)}"
    
    async def _calculate_confidence_factors(self, brain_confidences: Dict[ConfidenceSource, BrainConfidence],
                                          risk_level: RiskLevel, 
                                          execution_context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate breakdown of confidence factors"""
        factors = {}
        
        try:
            # Brain contribution factors
            total_weighted_confidence = 0.0
            total_weight = 0.0
            
            for source, brain_conf in brain_confidences.items():
                weight = brain_conf.weight * brain_conf.reliability
                contribution = brain_conf.confidence_score * weight
                total_weighted_confidence += contribution
                total_weight += weight
                
                # Calculate percentage contribution
                factors[f"{source.value}_contribution"] = contribution
            
            # Normalize contributions to percentages
            if total_weighted_confidence > 0:
                for key in list(factors.keys()):
                    factors[key] = (factors[key] / total_weighted_confidence) * 100
            
            # Risk factor
            factors["risk_adjustment"] = self.risk_adjustments.get(risk_level, 1.0)
            
            # Context factors
            if execution_context:
                factors["context_complexity"] = self._get_complexity_factor(execution_context)
                factors["context_urgency"] = self._get_urgency_factor(execution_context)
                factors["context_environment"] = self._get_environment_factor(execution_context)
            
            return factors
            
        except Exception as e:
            logger.error(f"Error calculating confidence factors: {str(e)}")
            return {"error": str(e)}
    
    def _get_complexity_factor(self, context: Dict[str, Any]) -> float:
        """Get complexity factor from context"""
        complexity = context.get("complexity", "medium").lower()
        complexity_factors = {
            "very_low": 1.2,
            "low": 1.1,
            "medium": 1.0,
            "high": 0.9,
            "very_high": 0.8
        }
        return complexity_factors.get(complexity, 1.0)
    
    def _get_urgency_factor(self, context: Dict[str, Any]) -> float:
        """Get urgency factor from context"""
        urgency = context.get("urgency", "medium").lower()
        urgency_factors = {
            "low": 1.05,
            "medium": 1.0,
            "high": 0.95,
            "critical": 0.9
        }
        return urgency_factors.get(urgency, 1.0)
    
    def _get_environment_factor(self, context: Dict[str, Any]) -> float:
        """Get environment factor from context"""
        environment = context.get("environment", "unknown").lower()
        env_factors = {
            "development": 1.05,
            "testing": 1.02,
            "staging": 1.0,
            "production": 0.9,
            "critical_production": 0.8
        }
        return env_factors.get(environment, 1.0)
    
    async def _update_aggregation_metrics(self, aggregated_confidence: AggregatedConfidence):
        """Update aggregation metrics"""
        try:
            self.aggregation_metrics["total_aggregations"] += 1
            
            # Update average confidence
            total = self.aggregation_metrics["total_aggregations"]
            current_avg = self.aggregation_metrics["average_confidence"]
            new_confidence = aggregated_confidence.risk_adjusted_confidence
            
            self.aggregation_metrics["average_confidence"] = (
                (current_avg * (total - 1) + new_confidence) / total
            )
            
            # Update strategy distribution
            strategy = aggregated_confidence.execution_strategy.value
            self.aggregation_metrics["strategy_distribution"][strategy] += 1
            
            # Update risk adjustment frequency
            risk_level = aggregated_confidence.aggregation_metadata.get("risk_level", "medium")
            if risk_level in ["high", "critical"]:
                self.aggregation_metrics["risk_adjustment_frequency"] += 1
            
        except Exception as e:
            logger.error(f"Error updating aggregation metrics: {str(e)}")
    
    async def learn_from_execution(self, predicted_confidence: float, execution_result: Dict[str, Any],
                                 brain_source: str = "aggregated"):
        """
        Learn from execution results to improve confidence calibration
        
        Args:
            predicted_confidence: The confidence that was predicted
            execution_result: The actual execution result
            brain_source: Source brain for the confidence prediction
        """
        try:
            # Determine if execution was successful
            success = execution_result.get("success", False)
            if "status" in execution_result:
                success = execution_result["status"] in ["success", "completed", "passed"]
            
            # Calculate calibration error
            actual_success_score = 1.0 if success else 0.0
            calibration_error = abs(predicted_confidence - actual_success_score)
            
            # Create calibration record
            calibration = ConfidenceCalibration(
                predicted_confidence=predicted_confidence,
                actual_success=success,
                execution_outcome=execution_result,
                calibration_error=calibration_error,
                brain_source=brain_source
            )
            
            # Store calibration history
            self.calibration_history.append(calibration)
            
            # Update brain reliability if specific brain source
            if brain_source != "aggregated" and brain_source in self.brain_reliability_scores:
                await self._update_brain_reliability(brain_source, calibration_error)
            
            # Update calibration accuracy metric
            if len(self.calibration_history) > 0:
                recent_errors = [c.calibration_error for c in self.calibration_history[-50:]]
                self.aggregation_metrics["calibration_accuracy"] = 1.0 - (sum(recent_errors) / len(recent_errors))
            
            logger.info(f"Learned from execution: predicted={predicted_confidence:.3f}, "
                       f"actual={actual_success_score}, error={calibration_error:.3f}")
            
        except Exception as e:
            logger.error(f"Error learning from execution: {str(e)}")
    
    async def _update_brain_reliability(self, brain_source: str, calibration_error: float):
        """Update brain reliability based on calibration error"""
        try:
            current_reliability = self.brain_reliability_scores.get(brain_source, 1.0)
            
            # Adjust reliability based on calibration error
            if calibration_error < 0.1:  # Very accurate
                adjustment = 0.02
            elif calibration_error < 0.2:  # Accurate
                adjustment = 0.01
            elif calibration_error < 0.3:  # Moderate
                adjustment = 0.0
            elif calibration_error < 0.5:  # Poor
                adjustment = -0.01
            else:  # Very poor
                adjustment = -0.02
            
            # Apply adjustment with bounds
            new_reliability = max(0.5, min(1.5, current_reliability + adjustment))
            self.brain_reliability_scores[brain_source] = new_reliability
            
            logger.debug(f"Updated {brain_source} reliability: {current_reliability:.3f} -> {new_reliability:.3f}")
            
        except Exception as e:
            logger.error(f"Error updating brain reliability: {str(e)}")
    
    async def get_confidence_metrics(self) -> Dict[str, Any]:
        """Get confidence engine metrics"""
        try:
            # Calculate calibration statistics
            calibration_stats = {}
            if self.calibration_history:
                recent_calibrations = self.calibration_history[-100:]
                calibration_stats = {
                    "total_calibrations": len(self.calibration_history),
                    "recent_calibrations": len(recent_calibrations),
                    "average_error": sum(c.calibration_error for c in recent_calibrations) / len(recent_calibrations),
                    "accuracy_trend": self._calculate_accuracy_trend()
                }
            
            return {
                "aggregation_metrics": self.aggregation_metrics,
                "brain_reliability_scores": self.brain_reliability_scores,
                "calibration_statistics": calibration_stats,
                "strategy_thresholds": {s.value: t for s, t in self.strategy_thresholds.items()},
                "brain_weights": {s.value: w for s, w in self.brain_weights.items()},
                "risk_adjustments": {r.value: a for r, a in self.risk_adjustments.items()}
            }
            
        except Exception as e:
            logger.error(f"Error getting confidence metrics: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_accuracy_trend(self) -> str:
        """Calculate accuracy trend from recent calibrations"""
        try:
            if len(self.calibration_history) < 20:
                return "insufficient_data"
            
            # Compare recent vs older calibrations
            recent_errors = [c.calibration_error for c in self.calibration_history[-10:]]
            older_errors = [c.calibration_error for c in self.calibration_history[-20:-10]]
            
            recent_avg = sum(recent_errors) / len(recent_errors)
            older_avg = sum(older_errors) / len(older_errors)
            
            if recent_avg < older_avg - 0.05:
                return "improving"
            elif recent_avg > older_avg + 0.05:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error calculating accuracy trend: {str(e)}")
            return "unknown"
    
    async def update_strategy_thresholds(self, new_thresholds: Dict[str, float]):
        """Update execution strategy thresholds"""
        try:
            for strategy_name, threshold in new_thresholds.items():
                for strategy in ExecutionStrategy:
                    if strategy.value == strategy_name:
                        self.strategy_thresholds[strategy] = threshold
                        break
            
            logger.info("Updated strategy thresholds")
            
        except Exception as e:
            logger.error(f"Error updating strategy thresholds: {str(e)}")
    
    async def update_brain_weights(self, new_weights: Dict[str, float]):
        """Update brain weights for confidence aggregation"""
        try:
            for brain_name, weight in new_weights.items():
                for source in ConfidenceSource:
                    if source.value == brain_name:
                        self.brain_weights[source] = weight
                        break
            
            logger.info("Updated brain weights")
            
        except Exception as e:
            logger.error(f"Error updating brain weights: {str(e)}")
    
    async def get_recent_calibrations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent calibration history"""
        try:
            recent_calibrations = self.calibration_history[-limit:]
            return [
                {
                    "predicted_confidence": cal.predicted_confidence,
                    "actual_success": cal.actual_success,
                    "calibration_error": cal.calibration_error,
                    "brain_source": cal.brain_source,
                    "timestamp": cal.timestamp.isoformat(),
                    "execution_summary": str(cal.execution_outcome)[:100] + "..." if len(str(cal.execution_outcome)) > 100 else str(cal.execution_outcome)
                }
                for cal in recent_calibrations
            ]
        except Exception as e:
            logger.error(f"Error getting recent calibrations: {str(e)}")
            return []
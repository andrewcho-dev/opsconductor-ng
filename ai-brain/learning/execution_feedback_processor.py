"""
Execution Feedback Processor for Multi-Brain AI Architecture

This module processes execution feedback to improve AI brain performance
through continuous learning and adaptation.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import statistics

logger = logging.getLogger(__name__)

class ExecutionOutcome(Enum):
    """Execution outcome types."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"

class FeedbackType(Enum):
    """Types of feedback."""
    AUTOMATIC = "automatic"  # System-generated feedback
    USER_EXPLICIT = "user_explicit"  # Direct user feedback
    USER_IMPLICIT = "user_implicit"  # Inferred from user behavior
    SYSTEM_METRICS = "system_metrics"  # Performance metrics

@dataclass
class ExecutionFeedback:
    """Execution feedback data structure."""
    feedback_id: str
    coordination_id: str
    brain_id: str
    execution_outcome: ExecutionOutcome
    feedback_type: FeedbackType
    confidence_accuracy: Optional[float] = None  # How accurate was the confidence?
    execution_time: Optional[float] = None
    user_satisfaction: Optional[float] = None  # 0.0 to 1.0
    error_details: Optional[str] = None
    success_metrics: Optional[Dict[str, float]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LearningInsight:
    """Learning insight derived from feedback."""
    insight_id: str
    brain_id: str
    insight_type: str
    description: str
    confidence_impact: float  # Expected impact on future confidence
    pattern_strength: float  # How strong is this pattern
    applicable_contexts: List[str]
    created_at: datetime = field(default_factory=datetime.now)

class ExecutionFeedbackProcessor:
    """
    Processes execution feedback to generate learning insights
    and improve AI brain performance.
    """
    
    def __init__(self):
        """Initialize the execution feedback processor."""
        self.logger = logging.getLogger(__name__)
        self.feedback_history: List[ExecutionFeedback] = []
        self.learning_insights: List[LearningInsight] = []
        self.brain_performance_metrics: Dict[str, Dict] = {}
        self.logger.info("Execution Feedback Processor initialized")
    
    async def process_feedback(
        self,
        feedback: ExecutionFeedback
    ) -> List[LearningInsight]:
        """
        Process execution feedback and generate learning insights.
        
        Args:
            feedback: Execution feedback to process
            
        Returns:
            List of generated learning insights
        """
        self.logger.info(f"Processing feedback for brain {feedback.brain_id}: {feedback.execution_outcome.value}")
        
        # Store feedback
        self.feedback_history.append(feedback)
        
        # Update brain performance metrics
        await self._update_brain_metrics(feedback)
        
        # Generate learning insights
        insights = await self._generate_insights(feedback)
        
        # Store insights
        self.learning_insights.extend(insights)
        
        # Clean up old data
        await self._cleanup_old_data()
        
        self.logger.info(f"Generated {len(insights)} learning insights from feedback")
        return insights
    
    async def get_brain_performance_summary(
        self,
        brain_id: str,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get performance summary for a specific brain.
        
        Args:
            brain_id: ID of the brain to analyze
            time_window: Time window for analysis (default: last 7 days)
            
        Returns:
            Performance summary dictionary
        """
        if time_window is None:
            time_window = timedelta(days=7)
        
        cutoff_time = datetime.now() - time_window
        
        # Filter feedback for this brain and time window
        relevant_feedback = [
            fb for fb in self.feedback_history
            if fb.brain_id == brain_id and fb.timestamp >= cutoff_time
        ]
        
        if not relevant_feedback:
            return {
                "brain_id": brain_id,
                "total_executions": 0,
                "success_rate": 0.0,
                "average_confidence_accuracy": 0.0,
                "average_user_satisfaction": 0.0,
                "performance_trend": "insufficient_data"
            }
        
        # Calculate metrics
        total_executions = len(relevant_feedback)
        successful_executions = len([
            fb for fb in relevant_feedback
            if fb.execution_outcome in [ExecutionOutcome.SUCCESS, ExecutionOutcome.PARTIAL_SUCCESS]
        ])
        success_rate = successful_executions / total_executions
        
        # Confidence accuracy
        confidence_accuracies = [
            fb.confidence_accuracy for fb in relevant_feedback
            if fb.confidence_accuracy is not None
        ]
        avg_confidence_accuracy = statistics.mean(confidence_accuracies) if confidence_accuracies else 0.0
        
        # User satisfaction
        user_satisfactions = [
            fb.user_satisfaction for fb in relevant_feedback
            if fb.user_satisfaction is not None
        ]
        avg_user_satisfaction = statistics.mean(user_satisfactions) if user_satisfactions else 0.0
        
        # Performance trend (simplified)
        recent_feedback = relevant_feedback[-10:]  # Last 10 executions
        older_feedback = relevant_feedback[:-10] if len(relevant_feedback) > 10 else []
        
        if older_feedback:
            recent_success_rate = len([
                fb for fb in recent_feedback
                if fb.execution_outcome in [ExecutionOutcome.SUCCESS, ExecutionOutcome.PARTIAL_SUCCESS]
            ]) / len(recent_feedback)
            
            older_success_rate = len([
                fb for fb in older_feedback
                if fb.execution_outcome in [ExecutionOutcome.SUCCESS, ExecutionOutcome.PARTIAL_SUCCESS]
            ]) / len(older_feedback)
            
            if recent_success_rate > older_success_rate + 0.1:
                trend = "improving"
            elif recent_success_rate < older_success_rate - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "brain_id": brain_id,
            "total_executions": total_executions,
            "success_rate": success_rate,
            "average_confidence_accuracy": avg_confidence_accuracy,
            "average_user_satisfaction": avg_user_satisfaction,
            "performance_trend": trend,
            "recent_insights": len([
                insight for insight in self.learning_insights
                if insight.brain_id == brain_id and insight.created_at >= cutoff_time
            ])
        }
    
    async def get_learning_recommendations(
        self,
        brain_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get learning recommendations for a specific brain.
        
        Args:
            brain_id: ID of the brain to get recommendations for
            
        Returns:
            List of learning recommendations
        """
        # Get recent insights for this brain
        recent_insights = [
            insight for insight in self.learning_insights
            if insight.brain_id == brain_id
            and insight.created_at >= datetime.now() - timedelta(days=30)
        ]
        
        recommendations = []
        
        # Analyze patterns in insights
        insight_types = {}
        for insight in recent_insights:
            insight_types[insight.insight_type] = insight_types.get(insight.insight_type, 0) + 1
        
        # Generate recommendations based on patterns
        for insight_type, count in insight_types.items():
            if count >= 3:  # Pattern threshold
                recommendations.append({
                    "type": "pattern_reinforcement",
                    "description": f"Strong pattern detected in {insight_type}",
                    "recommendation": f"Consider adjusting {insight_type} algorithms based on {count} similar insights",
                    "priority": "high" if count >= 5 else "medium",
                    "evidence_count": count
                })
        
        # Performance-based recommendations
        performance = await self.get_brain_performance_summary(brain_id)
        
        if performance["success_rate"] < 0.7:
            recommendations.append({
                "type": "performance_improvement",
                "description": f"Success rate below threshold: {performance['success_rate']:.2%}",
                "recommendation": "Review and improve core algorithms",
                "priority": "high",
                "current_metric": performance["success_rate"]
            })
        
        if performance["average_confidence_accuracy"] < 0.6:
            recommendations.append({
                "type": "confidence_calibration",
                "description": f"Confidence accuracy needs improvement: {performance['average_confidence_accuracy']:.2%}",
                "recommendation": "Recalibrate confidence scoring mechanisms",
                "priority": "medium",
                "current_metric": performance["average_confidence_accuracy"]
            })
        
        return recommendations
    
    async def _update_brain_metrics(self, feedback: ExecutionFeedback):
        """Update brain performance metrics with new feedback."""
        brain_id = feedback.brain_id
        
        if brain_id not in self.brain_performance_metrics:
            self.brain_performance_metrics[brain_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_confidence_accuracy": 0.0,
                "confidence_accuracy_count": 0,
                "total_user_satisfaction": 0.0,
                "user_satisfaction_count": 0,
                "last_updated": datetime.now()
            }
        
        metrics = self.brain_performance_metrics[brain_id]
        metrics["total_executions"] += 1
        
        if feedback.execution_outcome in [ExecutionOutcome.SUCCESS, ExecutionOutcome.PARTIAL_SUCCESS]:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
        
        if feedback.confidence_accuracy is not None:
            metrics["total_confidence_accuracy"] += feedback.confidence_accuracy
            metrics["confidence_accuracy_count"] += 1
        
        if feedback.user_satisfaction is not None:
            metrics["total_user_satisfaction"] += feedback.user_satisfaction
            metrics["user_satisfaction_count"] += 1
        
        metrics["last_updated"] = datetime.now()
    
    async def _generate_insights(self, feedback: ExecutionFeedback) -> List[LearningInsight]:
        """Generate learning insights from feedback."""
        insights = []
        
        # Confidence accuracy insight
        if feedback.confidence_accuracy is not None:
            if feedback.confidence_accuracy < 0.5:
                insights.append(LearningInsight(
                    insight_id=f"conf_acc_{feedback.feedback_id}",
                    brain_id=feedback.brain_id,
                    insight_type="confidence_accuracy",
                    description=f"Low confidence accuracy detected: {feedback.confidence_accuracy:.2%}",
                    confidence_impact=-0.1,
                    pattern_strength=0.7,
                    applicable_contexts=["similar_requests"]
                ))
            elif feedback.confidence_accuracy > 0.9:
                insights.append(LearningInsight(
                    insight_id=f"conf_acc_{feedback.feedback_id}",
                    brain_id=feedback.brain_id,
                    insight_type="confidence_accuracy",
                    description=f"High confidence accuracy achieved: {feedback.confidence_accuracy:.2%}",
                    confidence_impact=0.05,
                    pattern_strength=0.8,
                    applicable_contexts=["similar_requests"]
                ))
        
        # Execution outcome insight
        if feedback.execution_outcome == ExecutionOutcome.FAILURE:
            insights.append(LearningInsight(
                insight_id=f"exec_fail_{feedback.feedback_id}",
                brain_id=feedback.brain_id,
                insight_type="execution_failure",
                description=f"Execution failure: {feedback.error_details or 'Unknown error'}",
                confidence_impact=-0.15,
                pattern_strength=0.9,
                applicable_contexts=["error_handling", "similar_requests"]
            ))
        
        # User satisfaction insight
        if feedback.user_satisfaction is not None:
            if feedback.user_satisfaction < 0.3:
                insights.append(LearningInsight(
                    insight_id=f"user_sat_{feedback.feedback_id}",
                    brain_id=feedback.brain_id,
                    insight_type="user_satisfaction",
                    description=f"Low user satisfaction: {feedback.user_satisfaction:.2%}",
                    confidence_impact=-0.2,
                    pattern_strength=0.8,
                    applicable_contexts=["user_experience", "similar_requests"]
                ))
            elif feedback.user_satisfaction > 0.8:
                insights.append(LearningInsight(
                    insight_id=f"user_sat_{feedback.feedback_id}",
                    brain_id=feedback.brain_id,
                    insight_type="user_satisfaction",
                    description=f"High user satisfaction: {feedback.user_satisfaction:.2%}",
                    confidence_impact=0.1,
                    pattern_strength=0.7,
                    applicable_contexts=["user_experience", "similar_requests"]
                ))
        
        return insights
    
    async def _cleanup_old_data(self):
        """Clean up old feedback and insights to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(days=90)  # Keep 90 days of data
        
        # Clean up old feedback
        self.feedback_history = [
            fb for fb in self.feedback_history
            if fb.timestamp >= cutoff_time
        ]
        
        # Clean up old insights
        self.learning_insights = [
            insight for insight in self.learning_insights
            if insight.created_at >= cutoff_time
        ]
        
        self.logger.debug(f"Cleaned up old data, keeping {len(self.feedback_history)} feedback entries and {len(self.learning_insights)} insights")

# Global instance for easy access
execution_feedback_processor = ExecutionFeedbackProcessor()
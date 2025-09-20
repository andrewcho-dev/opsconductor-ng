"""
OpsConductor Knowledge Engine - Learning System Module

This module implements continuous learning capabilities that improve the AI Brain's
performance over time by analyzing job outcomes, user feedback, and system patterns.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import statistics

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Types of learning activities"""
    JOB_OUTCOME = "job_outcome"
    USER_FEEDBACK = "user_feedback"
    PATTERN_RECOGNITION = "pattern_recognition"
    ERROR_ANALYSIS = "error_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"

class FeedbackType(Enum):
    """Types of user feedback"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    SUGGESTION = "suggestion"
    CORRECTION = "correction"

class LearningPriority(Enum):
    """Priority levels for learning items"""
    CRITICAL = "critical"    # Immediate learning required
    HIGH = "high"           # Learn within 24 hours
    MEDIUM = "medium"       # Learn within week
    LOW = "low"            # Learn when convenient

@dataclass
class JobOutcome:
    """Outcome data from job execution"""
    job_id: str
    job_description: str
    target_type: str
    protocol: str
    workflow_steps: List[Dict[str, Any]]
    success: bool
    execution_time: float
    error_messages: List[str]
    user_satisfaction: Optional[int] = None  # 1-5 scale
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class UserFeedback:
    """User feedback on AI recommendations or job outcomes"""
    feedback_id: str
    user_id: str
    job_id: Optional[str]
    feedback_type: FeedbackType
    rating: Optional[int]  # 1-5 scale
    comment: str
    suggested_improvement: Optional[str]
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class LearningInsight:
    """Insight gained from learning analysis"""
    insight_id: str
    learning_type: LearningType
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    impact_score: float  # Estimated impact on system performance
    supporting_data: List[str]  # References to source data
    recommended_actions: List[str]
    applicable_contexts: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    applied: bool = False

@dataclass
class PerformanceMetric:
    """Performance metric tracking"""
    metric_name: str
    value: float
    timestamp: datetime
    context: Dict[str, Any]

class LearningSystem:
    """Continuous learning system for the AI Brain"""
    
    def __init__(self):
        self.job_outcomes: List[JobOutcome] = []
        self.user_feedback: List[UserFeedback] = []
        self.learning_insights: List[LearningInsight] = []
        self.performance_metrics: Dict[str, List[PerformanceMetric]] = {}
        self._learning_rules = self._initialize_learning_rules()
        logger.info("Initialized learning system")
    
    def _initialize_learning_rules(self) -> Dict[str, Any]:
        """Initialize learning rules and thresholds"""
        return {
            "min_job_samples": 5,  # Minimum jobs needed to identify patterns
            "success_rate_threshold": 0.8,  # Threshold for considering a pattern successful
            "feedback_weight": {
                FeedbackType.POSITIVE: 1.0,
                FeedbackType.NEGATIVE: -1.5,  # Negative feedback weighted more heavily
                FeedbackType.SUGGESTION: 0.5,
                FeedbackType.CORRECTION: -2.0
            },
            "confidence_thresholds": {
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4
            },
            "learning_retention_days": 90,  # How long to keep detailed learning data
            "pattern_similarity_threshold": 0.7
        }
    
    def record_job_outcome(self, outcome: JobOutcome) -> None:
        """Record the outcome of a job execution for learning"""
        self.job_outcomes.append(outcome)
        
        # Trigger learning analysis if we have enough data
        if len(self.job_outcomes) % 10 == 0:  # Analyze every 10 jobs
            self._analyze_job_patterns()
        
        logger.info(f"Recorded job outcome: {outcome.job_id}, success: {outcome.success}")
    
    def record_user_feedback(self, feedback: UserFeedback) -> None:
        """Record user feedback for learning"""
        self.user_feedback.append(feedback)
        
        # Immediate learning from critical feedback
        if feedback.feedback_type in [FeedbackType.NEGATIVE, FeedbackType.CORRECTION]:
            self._analyze_negative_feedback(feedback)
        
        logger.info(f"Recorded user feedback: {feedback.feedback_id}, type: {feedback.feedback_type.value}")
    
    def record_performance_metric(self, metric_name: str, value: float, context: Dict[str, Any] = None) -> None:
        """Record a performance metric"""
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
        
        metric = PerformanceMetric(
            metric_name=metric_name,
            value=value,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        self.performance_metrics[metric_name].append(metric)
        
        # Keep only recent metrics (last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.performance_metrics[metric_name] = [
            m for m in self.performance_metrics[metric_name] 
            if m.timestamp > cutoff_date
        ]
    
    def _analyze_job_patterns(self) -> None:
        """Analyze job execution patterns to identify learning opportunities"""
        recent_jobs = [
            job for job in self.job_outcomes 
            if job.timestamp > datetime.now() - timedelta(days=7)
        ]
        
        if len(recent_jobs) < self._learning_rules["min_job_samples"]:
            return
        
        # Group jobs by similarity
        job_groups = self._group_similar_jobs(recent_jobs)
        
        for group_key, jobs in job_groups.items():
            if len(jobs) >= self._learning_rules["min_job_samples"]:
                insight = self._analyze_job_group(group_key, jobs)
                if insight:
                    self.learning_insights.append(insight)
    
    def _group_similar_jobs(self, jobs: List[JobOutcome]) -> Dict[str, List[JobOutcome]]:
        """Group similar jobs together for pattern analysis"""
        groups = {}
        
        for job in jobs:
            # Create a key based on job characteristics
            key = f"{job.target_type}_{job.protocol}_{len(job.workflow_steps)}"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(job)
        
        return groups
    
    def _analyze_job_group(self, group_key: str, jobs: List[JobOutcome]) -> Optional[LearningInsight]:
        """Analyze a group of similar jobs to extract insights"""
        success_rate = sum(1 for job in jobs if job.success) / len(jobs)
        avg_execution_time = statistics.mean(job.execution_time for job in jobs)
        
        # Identify common failure patterns
        failed_jobs = [job for job in jobs if not job.success]
        common_errors = self._find_common_errors(failed_jobs)
        
        # Generate insight based on analysis
        if success_rate < self._learning_rules["success_rate_threshold"]:
            # Low success rate - identify improvement opportunities
            insight = LearningInsight(
                insight_id=f"low_success_{group_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                learning_type=LearningType.JOB_OUTCOME,
                title=f"Low Success Rate for {group_key} Jobs",
                description=f"Jobs of type {group_key} have a {success_rate:.1%} success rate, below threshold",
                confidence=0.8 if len(jobs) >= 10 else 0.6,
                impact_score=0.7,
                supporting_data=[job.job_id for job in jobs],
                recommended_actions=[
                    "Review common failure patterns",
                    "Improve error handling in workflow templates",
                    "Add validation steps before execution"
                ],
                applicable_contexts=[group_key]
            )
            
            if common_errors:
                insight.description += f". Common errors: {', '.join(common_errors[:3])}"
                insight.recommended_actions.append("Create specific error resolution procedures")
            
            return insight
        
        elif avg_execution_time > 300:  # 5 minutes threshold
            # Long execution time - optimization opportunity
            return LearningInsight(
                insight_id=f"slow_execution_{group_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                learning_type=LearningType.PERFORMANCE_OPTIMIZATION,
                title=f"Slow Execution for {group_key} Jobs",
                description=f"Jobs of type {group_key} take an average of {avg_execution_time:.1f} seconds",
                confidence=0.7,
                impact_score=0.5,
                supporting_data=[job.job_id for job in jobs],
                recommended_actions=[
                    "Optimize workflow steps",
                    "Implement parallel execution where possible",
                    "Review timeout settings"
                ],
                applicable_contexts=[group_key]
            )
        
        return None
    
    def _find_common_errors(self, failed_jobs: List[JobOutcome]) -> List[str]:
        """Find common error patterns in failed jobs"""
        error_counts = {}
        
        for job in failed_jobs:
            for error in job.error_messages:
                # Extract key error phrases
                error_key = self._extract_error_key(error)
                error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        # Return errors that appear in at least 30% of failed jobs
        threshold = max(1, len(failed_jobs) * 0.3)
        common_errors = [
            error for error, count in error_counts.items() 
            if count >= threshold
        ]
        
        return sorted(common_errors, key=lambda x: error_counts[x], reverse=True)
    
    def _extract_error_key(self, error_message: str) -> str:
        """Extract key phrases from error message for pattern matching"""
        # Simple extraction - in practice, this would be more sophisticated
        error_lower = error_message.lower()
        
        key_phrases = [
            "connection refused", "permission denied", "no space left",
            "service failed", "timeout", "not found", "access denied",
            "authentication failed", "network unreachable"
        ]
        
        for phrase in key_phrases:
            if phrase in error_lower:
                return phrase
        
        # Return first few words if no key phrase found
        words = error_lower.split()[:3]
        return " ".join(words)
    
    def _analyze_negative_feedback(self, feedback: UserFeedback) -> None:
        """Analyze negative feedback for immediate learning"""
        insight = LearningInsight(
            insight_id=f"negative_feedback_{feedback.feedback_id}",
            learning_type=LearningType.USER_FEEDBACK,
            title=f"Negative Feedback: {feedback.comment[:50]}...",
            description=f"User provided negative feedback: {feedback.comment}",
            confidence=0.9,  # High confidence in direct user feedback
            impact_score=0.8,
            supporting_data=[feedback.feedback_id],
            recommended_actions=[
                "Review the specific job or recommendation",
                "Adjust AI model parameters if needed",
                "Improve user communication"
            ],
            applicable_contexts=[feedback.context.get("job_type", "general")]
        )
        
        if feedback.suggested_improvement:
            insight.recommended_actions.append(f"Consider suggestion: {feedback.suggested_improvement}")
        
        self.learning_insights.append(insight)
    
    def get_learning_insights(self, 
                            learning_type: Optional[LearningType] = None,
                            min_confidence: float = 0.5) -> List[LearningInsight]:
        """Get learning insights, optionally filtered by type and confidence"""
        insights = self.learning_insights
        
        if learning_type:
            insights = [i for i in insights if i.learning_type == learning_type]
        
        insights = [i for i in insights if i.confidence >= min_confidence]
        
        # Sort by impact score and confidence
        insights.sort(key=lambda x: (x.impact_score, x.confidence), reverse=True)
        
        return insights
    
    def get_performance_trends(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Get performance trends for a specific metric"""
        if metric_name not in self.performance_metrics:
            return {"error": f"Metric {metric_name} not found"}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_metrics = [
            m for m in self.performance_metrics[metric_name]
            if m.timestamp > cutoff_date
        ]
        
        if not recent_metrics:
            return {"error": "No recent data available"}
        
        values = [m.value for m in recent_metrics]
        
        return {
            "metric_name": metric_name,
            "period_days": days,
            "data_points": len(values),
            "current_value": values[-1] if values else None,
            "average": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "trend": self._calculate_trend(values),
            "improvement_percentage": self._calculate_improvement(values)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple trend calculation - compare first and last quartiles
        quarter_size = len(values) // 4
        if quarter_size == 0:
            quarter_size = 1
        
        first_quarter = statistics.mean(values[:quarter_size])
        last_quarter = statistics.mean(values[-quarter_size:])
        
        change_percentage = ((last_quarter - first_quarter) / first_quarter) * 100
        
        if change_percentage > 5:
            return "improving"
        elif change_percentage < -5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_improvement(self, values: List[float]) -> float:
        """Calculate improvement percentage from first to last value"""
        if len(values) < 2:
            return 0.0
        
        first_value = values[0]
        last_value = values[-1]
        
        if first_value == 0:
            return 0.0
        
        return ((last_value - first_value) / first_value) * 100
    
    def generate_learning_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning report"""
        recent_jobs = [
            job for job in self.job_outcomes 
            if job.timestamp > datetime.now() - timedelta(days=30)
        ]
        
        recent_feedback = [
            fb for fb in self.user_feedback 
            if fb.timestamp > datetime.now() - timedelta(days=30)
        ]
        
        report = {
            "report_generated": datetime.now().isoformat(),
            "learning_period": "30 days",
            "job_analysis": {
                "total_jobs": len(recent_jobs),
                "success_rate": sum(1 for job in recent_jobs if job.success) / len(recent_jobs) if recent_jobs else 0,
                "average_execution_time": statistics.mean(job.execution_time for job in recent_jobs) if recent_jobs else 0,
                "most_common_target_types": self._get_most_common(recent_jobs, "target_type"),
                "most_common_protocols": self._get_most_common(recent_jobs, "protocol")
            },
            "feedback_analysis": {
                "total_feedback": len(recent_feedback),
                "feedback_distribution": self._get_feedback_distribution(recent_feedback),
                "average_rating": self._get_average_rating(recent_feedback),
                "improvement_suggestions": self._get_improvement_suggestions(recent_feedback)
            },
            "learning_insights": {
                "total_insights": len(self.learning_insights),
                "high_confidence_insights": len([i for i in self.learning_insights if i.confidence >= 0.8]),
                "applied_insights": len([i for i in self.learning_insights if i.applied]),
                "top_insights": [
                    {
                        "title": insight.title,
                        "confidence": insight.confidence,
                        "impact_score": insight.impact_score,
                        "learning_type": insight.learning_type.value
                    }
                    for insight in sorted(self.learning_insights, key=lambda x: x.impact_score, reverse=True)[:5]
                ]
            },
            "performance_metrics": {
                metric_name: self.get_performance_trends(metric_name, 30)
                for metric_name in self.performance_metrics.keys()
            },
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _get_most_common(self, jobs: List[JobOutcome], attribute: str) -> List[Tuple[str, int]]:
        """Get most common values for a job attribute"""
        counts = {}
        for job in jobs:
            value = getattr(job, attribute)
            counts[value] = counts.get(value, 0) + 1
        
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _get_feedback_distribution(self, feedback: List[UserFeedback]) -> Dict[str, int]:
        """Get distribution of feedback types"""
        distribution = {}
        for fb in feedback:
            fb_type = fb.feedback_type.value
            distribution[fb_type] = distribution.get(fb_type, 0) + 1
        
        return distribution
    
    def _get_average_rating(self, feedback: List[UserFeedback]) -> Optional[float]:
        """Get average rating from feedback"""
        ratings = [fb.rating for fb in feedback if fb.rating is not None]
        return statistics.mean(ratings) if ratings else None
    
    def _get_improvement_suggestions(self, feedback: List[UserFeedback]) -> List[str]:
        """Extract improvement suggestions from feedback"""
        suggestions = []
        for fb in feedback:
            if fb.suggested_improvement:
                suggestions.append(fb.suggested_improvement)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on learning analysis"""
        recommendations = []
        
        # Analyze recent job success rates
        recent_jobs = [
            job for job in self.job_outcomes 
            if job.timestamp > datetime.now() - timedelta(days=7)
        ]
        
        if recent_jobs:
            success_rate = sum(1 for job in recent_jobs if job.success) / len(recent_jobs)
            
            if success_rate < 0.8:
                recommendations.append("Focus on improving job success rate through better error handling")
            
            avg_time = statistics.mean(job.execution_time for job in recent_jobs)
            if avg_time > 300:  # 5 minutes
                recommendations.append("Optimize job execution time through workflow improvements")
        
        # Analyze feedback trends
        recent_feedback = [
            fb for fb in self.user_feedback 
            if fb.timestamp > datetime.now() - timedelta(days=7)
        ]
        
        negative_feedback = [fb for fb in recent_feedback if fb.feedback_type == FeedbackType.NEGATIVE]
        if len(negative_feedback) > len(recent_feedback) * 0.3:
            recommendations.append("Address user concerns highlighted in recent negative feedback")
        
        # High-impact insights
        high_impact_insights = [i for i in self.learning_insights if i.impact_score >= 0.7 and not i.applied]
        if high_impact_insights:
            recommendations.append(f"Apply {len(high_impact_insights)} high-impact learning insights")
        
        return recommendations
    
    def apply_insight(self, insight_id: str) -> bool:
        """Mark an insight as applied"""
        for insight in self.learning_insights:
            if insight.insight_id == insight_id:
                insight.applied = True
                logger.info(f"Applied learning insight: {insight_id}")
                return True
        
        return False
    
    def cleanup_old_data(self, retention_days: int = None) -> Dict[str, int]:
        """Clean up old learning data to manage memory usage"""
        if retention_days is None:
            retention_days = self._learning_rules["learning_retention_days"]
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Count items before cleanup
        initial_counts = {
            "job_outcomes": len(self.job_outcomes),
            "user_feedback": len(self.user_feedback),
            "learning_insights": len(self.learning_insights)
        }
        
        # Clean up old data
        self.job_outcomes = [job for job in self.job_outcomes if job.timestamp > cutoff_date]
        self.user_feedback = [fb for fb in self.user_feedback if fb.timestamp > cutoff_date]
        self.learning_insights = [insight for insight in self.learning_insights if insight.created_at > cutoff_date]
        
        # Count items after cleanup
        final_counts = {
            "job_outcomes": len(self.job_outcomes),
            "user_feedback": len(self.user_feedback),
            "learning_insights": len(self.learning_insights)
        }
        
        # Calculate removed items
        removed_counts = {
            key: initial_counts[key] - final_counts[key]
            for key in initial_counts.keys()
        }
        
        logger.info(f"Cleaned up old learning data: {removed_counts}")
        return removed_counts

# Global instance
learning_system = LearningSystem()
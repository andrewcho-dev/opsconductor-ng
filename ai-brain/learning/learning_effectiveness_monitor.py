"""
Learning Effectiveness Monitor for AI-Intent-Based Strategy Phase 3
Monitors and evaluates the effectiveness of learning systems across SME brains
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from pathlib import Path

logger = logging.getLogger(__name__)

class LearningMetricType(Enum):
    """Types of learning metrics"""
    CONFIDENCE_IMPROVEMENT = "confidence_improvement"
    ACCURACY_IMPROVEMENT = "accuracy_improvement"
    RESPONSE_TIME_IMPROVEMENT = "response_time_improvement"
    USER_SATISFACTION = "user_satisfaction"
    KNOWLEDGE_RETENTION = "knowledge_retention"
    CROSS_DOMAIN_TRANSFER = "cross_domain_transfer"

@dataclass
class LearningMetric:
    """Individual learning metric data"""
    metric_type: LearningMetricType
    domain: str
    timestamp: datetime
    value: float
    baseline_value: Optional[float] = None
    improvement_percentage: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LearningSession:
    """Learning session tracking"""
    session_id: str
    domain: str
    start_time: datetime
    end_time: Optional[datetime] = None
    interactions_count: int = 0
    successful_interactions: int = 0
    average_confidence: float = 0.0
    knowledge_items_learned: int = 0
    errors_encountered: List[str] = field(default_factory=list)

@dataclass
class EffectivenessReport:
    """Learning effectiveness report"""
    report_id: str
    generated_at: datetime
    time_period: Tuple[datetime, datetime]
    overall_effectiveness_score: float
    domain_scores: Dict[str, float]
    key_improvements: List[str]
    areas_for_improvement: List[str]
    recommendations: List[str]
    metrics_summary: Dict[str, Any]

class LearningEffectivenessMonitor:
    """
    Monitors and evaluates the effectiveness of learning systems
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "/tmp/learning_effectiveness"
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        
        self.metrics_history: List[LearningMetric] = []
        self.learning_sessions: List[LearningSession] = []
        self.baseline_metrics: Dict[str, Dict[LearningMetricType, float]] = {}
        
        # Load existing data
        self._load_historical_data()
    
    def _load_historical_data(self):
        """Load historical learning data"""
        try:
            metrics_file = Path(self.storage_path) / "metrics_history.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    # Convert back to LearningMetric objects
                    for metric_data in data:
                        metric = LearningMetric(
                            metric_type=LearningMetricType(metric_data['metric_type']),
                            domain=metric_data['domain'],
                            timestamp=datetime.fromisoformat(metric_data['timestamp']),
                            value=metric_data['value'],
                            baseline_value=metric_data.get('baseline_value'),
                            improvement_percentage=metric_data.get('improvement_percentage'),
                            context=metric_data.get('context', {})
                        )
                        self.metrics_history.append(metric)
            
            baseline_file = Path(self.storage_path) / "baseline_metrics.json"
            if baseline_file.exists():
                with open(baseline_file, 'r') as f:
                    data = json.load(f)
                    for domain, metrics in data.items():
                        self.baseline_metrics[domain] = {
                            LearningMetricType(k): v for k, v in metrics.items()
                        }
                        
        except Exception as e:
            logger.warning(f"Failed to load historical learning data: {e}")
    
    def _save_data(self):
        """Save learning data to storage"""
        try:
            # Save metrics history
            metrics_file = Path(self.storage_path) / "metrics_history.json"
            metrics_data = []
            for metric in self.metrics_history:
                metrics_data.append({
                    'metric_type': metric.metric_type.value,
                    'domain': metric.domain,
                    'timestamp': metric.timestamp.isoformat(),
                    'value': metric.value,
                    'baseline_value': metric.baseline_value,
                    'improvement_percentage': metric.improvement_percentage,
                    'context': metric.context
                })
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Save baseline metrics
            baseline_file = Path(self.storage_path) / "baseline_metrics.json"
            baseline_data = {}
            for domain, metrics in self.baseline_metrics.items():
                baseline_data[domain] = {k.value: v for k, v in metrics.items()}
            
            with open(baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")
    
    def record_learning_metric(self, 
                             metric_type: LearningMetricType,
                             domain: str,
                             value: float,
                             context: Optional[Dict[str, Any]] = None) -> LearningMetric:
        """
        Record a learning effectiveness metric
        """
        # Get baseline value if available
        baseline_value = None
        improvement_percentage = None
        
        if domain in self.baseline_metrics and metric_type in self.baseline_metrics[domain]:
            baseline_value = self.baseline_metrics[domain][metric_type]
            if baseline_value > 0:
                improvement_percentage = ((value - baseline_value) / baseline_value) * 100
        
        metric = LearningMetric(
            metric_type=metric_type,
            domain=domain,
            timestamp=datetime.now(),
            value=value,
            baseline_value=baseline_value,
            improvement_percentage=improvement_percentage,
            context=context or {}
        )
        
        self.metrics_history.append(metric)
        self._save_data()
        
        logger.info(f"📊 Recorded learning metric: {metric_type.value} for {domain} = {value}")
        if improvement_percentage is not None:
            logger.info(f"   Improvement: {improvement_percentage:.1f}% from baseline")
        
        return metric
    
    def set_baseline_metric(self, 
                           domain: str, 
                           metric_type: LearningMetricType, 
                           value: float):
        """
        Set a baseline metric for comparison
        """
        if domain not in self.baseline_metrics:
            self.baseline_metrics[domain] = {}
        
        self.baseline_metrics[domain][metric_type] = value
        self._save_data()
        
        logger.info(f"📏 Set baseline for {domain}.{metric_type.value} = {value}")
    
    def start_learning_session(self, domain: str) -> str:
        """
        Start tracking a learning session
        """
        session_id = f"{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = LearningSession(
            session_id=session_id,
            domain=domain,
            start_time=datetime.now()
        )
        
        self.learning_sessions.append(session)
        
        logger.info(f"🎓 Started learning session: {session_id}")
        return session_id
    
    def end_learning_session(self, session_id: str, 
                           interactions_count: int,
                           successful_interactions: int,
                           average_confidence: float,
                           knowledge_items_learned: int,
                           errors: Optional[List[str]] = None):
        """
        End a learning session and record results
        """
        session = next((s for s in self.learning_sessions if s.session_id == session_id), None)
        if not session:
            logger.warning(f"Learning session {session_id} not found")
            return
        
        session.end_time = datetime.now()
        session.interactions_count = interactions_count
        session.successful_interactions = successful_interactions
        session.average_confidence = average_confidence
        session.knowledge_items_learned = knowledge_items_learned
        session.errors_encountered = errors or []
        
        # Calculate and record session metrics
        success_rate = successful_interactions / interactions_count if interactions_count > 0 else 0
        session_duration = (session.end_time - session.start_time).total_seconds() / 60  # minutes
        
        self.record_learning_metric(
            LearningMetricType.ACCURACY_IMPROVEMENT,
            session.domain,
            success_rate,
            {
                'session_id': session_id,
                'duration_minutes': session_duration,
                'interactions': interactions_count
            }
        )
        
        self.record_learning_metric(
            LearningMetricType.CONFIDENCE_IMPROVEMENT,
            session.domain,
            average_confidence,
            {
                'session_id': session_id,
                'knowledge_items_learned': knowledge_items_learned
            }
        )
        
        logger.info(f"✅ Ended learning session: {session_id}")
        logger.info(f"   Success rate: {success_rate:.2f}, Avg confidence: {average_confidence:.2f}")
    
    def calculate_domain_effectiveness(self, domain: str, 
                                     time_period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate learning effectiveness for a specific domain
        """
        cutoff_date = datetime.now() - timedelta(days=time_period_days)
        
        # Get recent metrics for the domain
        recent_metrics = [
            m for m in self.metrics_history 
            if m.domain == domain and m.timestamp >= cutoff_date
        ]
        
        if not recent_metrics:
            return {
                'domain': domain,
                'effectiveness_score': 0.0,
                'metrics_count': 0,
                'message': 'No recent learning data available'
            }
        
        # Calculate effectiveness by metric type
        metric_scores = {}
        for metric_type in LearningMetricType:
            type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
            if type_metrics:
                # Calculate average improvement percentage
                improvements = [m.improvement_percentage for m in type_metrics if m.improvement_percentage is not None]
                if improvements:
                    metric_scores[metric_type.value] = statistics.mean(improvements)
                else:
                    # If no baseline, use raw values
                    values = [m.value for m in type_metrics]
                    metric_scores[metric_type.value] = statistics.mean(values) * 100  # Convert to percentage
        
        # Calculate overall effectiveness score
        if metric_scores:
            effectiveness_score = statistics.mean(metric_scores.values())
        else:
            effectiveness_score = 0.0
        
        # Get recent learning sessions
        recent_sessions = [
            s for s in self.learning_sessions 
            if s.domain == domain and s.start_time >= cutoff_date and s.end_time is not None
        ]
        
        session_stats = {}
        if recent_sessions:
            session_stats = {
                'total_sessions': len(recent_sessions),
                'avg_success_rate': statistics.mean([
                    s.successful_interactions / s.interactions_count 
                    for s in recent_sessions if s.interactions_count > 0
                ]),
                'avg_confidence': statistics.mean([s.average_confidence for s in recent_sessions]),
                'total_knowledge_learned': sum([s.knowledge_items_learned for s in recent_sessions])
            }
        
        return {
            'domain': domain,
            'effectiveness_score': effectiveness_score,
            'metric_scores': metric_scores,
            'metrics_count': len(recent_metrics),
            'session_stats': session_stats,
            'time_period_days': time_period_days
        }
    
    def generate_effectiveness_report(self, time_period_days: int = 30) -> EffectivenessReport:
        """
        Generate a comprehensive learning effectiveness report
        """
        report_id = f"effectiveness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        end_time = datetime.now()
        start_time = end_time - timedelta(days=time_period_days)
        
        # Get all domains that have learning data
        domains = set(m.domain for m in self.metrics_history if m.timestamp >= start_time)
        
        # Calculate effectiveness for each domain
        domain_scores = {}
        for domain in domains:
            domain_effectiveness = self.calculate_domain_effectiveness(domain, time_period_days)
            domain_scores[domain] = domain_effectiveness['effectiveness_score']
        
        # Calculate overall effectiveness
        overall_effectiveness = statistics.mean(domain_scores.values()) if domain_scores else 0.0
        
        # Identify key improvements and areas for improvement
        key_improvements = []
        areas_for_improvement = []
        
        for domain, score in domain_scores.items():
            if score > 10:  # More than 10% improvement
                key_improvements.append(f"{domain}: {score:.1f}% improvement")
            elif score < -5:  # More than 5% degradation
                areas_for_improvement.append(f"{domain}: {abs(score):.1f}% degradation")
        
        # Generate recommendations
        recommendations = []
        if overall_effectiveness < 5:
            recommendations.append("Consider reviewing learning algorithms and training data quality")
        if len(areas_for_improvement) > len(key_improvements):
            recommendations.append("Focus on domains showing degradation in performance")
        if not key_improvements:
            recommendations.append("Investigate potential issues with learning system effectiveness")
        
        # Create metrics summary
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= start_time]
        metrics_summary = {
            'total_metrics_recorded': len(recent_metrics),
            'domains_monitored': len(domains),
            'average_improvement': overall_effectiveness,
            'metrics_by_type': {}
        }
        
        for metric_type in LearningMetricType:
            type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
            if type_metrics:
                improvements = [m.improvement_percentage for m in type_metrics if m.improvement_percentage is not None]
                if improvements:
                    metrics_summary['metrics_by_type'][metric_type.value] = {
                        'count': len(type_metrics),
                        'avg_improvement': statistics.mean(improvements)
                    }
        
        report = EffectivenessReport(
            report_id=report_id,
            generated_at=datetime.now(),
            time_period=(start_time, end_time),
            overall_effectiveness_score=overall_effectiveness,
            domain_scores=domain_scores,
            key_improvements=key_improvements,
            areas_for_improvement=areas_for_improvement,
            recommendations=recommendations,
            metrics_summary=metrics_summary
        )
        
        # Save report
        self._save_report(report)
        
        logger.info(f"📋 Generated effectiveness report: {report_id}")
        logger.info(f"   Overall effectiveness: {overall_effectiveness:.1f}%")
        
        return report
    
    def _save_report(self, report: EffectivenessReport):
        """Save effectiveness report to storage"""
        try:
            report_file = Path(self.storage_path) / f"{report.report_id}.json"
            
            report_data = {
                'report_id': report.report_id,
                'generated_at': report.generated_at.isoformat(),
                'time_period': [report.time_period[0].isoformat(), report.time_period[1].isoformat()],
                'overall_effectiveness_score': report.overall_effectiveness_score,
                'domain_scores': report.domain_scores,
                'key_improvements': report.key_improvements,
                'areas_for_improvement': report.areas_for_improvement,
                'recommendations': report.recommendations,
                'metrics_summary': report.metrics_summary
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save effectiveness report: {e}")
    
    def get_learning_trends(self, domain: str, 
                           metric_type: LearningMetricType,
                           time_period_days: int = 90) -> Dict[str, Any]:
        """
        Get learning trends for a specific domain and metric type
        """
        cutoff_date = datetime.now() - timedelta(days=time_period_days)
        
        metrics = [
            m for m in self.metrics_history 
            if (m.domain == domain and 
                m.metric_type == metric_type and 
                m.timestamp >= cutoff_date)
        ]
        
        if not metrics:
            return {
                'domain': domain,
                'metric_type': metric_type.value,
                'trend': 'no_data',
                'message': 'No data available for the specified period'
            }
        
        # Sort by timestamp
        metrics.sort(key=lambda x: x.timestamp)
        
        # Calculate trend
        values = [m.value for m in metrics]
        timestamps = [m.timestamp for m in metrics]
        
        if len(values) < 2:
            trend = 'insufficient_data'
        else:
            # Simple linear trend calculation
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            
            if second_avg > first_avg * 1.05:  # 5% improvement threshold
                trend = 'improving'
            elif second_avg < first_avg * 0.95:  # 5% degradation threshold
                trend = 'declining'
            else:
                trend = 'stable'
        
        return {
            'domain': domain,
            'metric_type': metric_type.value,
            'trend': trend,
            'data_points': len(metrics),
            'time_period_days': time_period_days,
            'latest_value': values[-1] if values else None,
            'average_value': statistics.mean(values) if values else None,
            'min_value': min(values) if values else None,
            'max_value': max(values) if values else None
        }
    
    def get_cross_domain_learning_analysis(self) -> Dict[str, Any]:
        """
        Analyze learning transfer between domains
        """
        domains = set(m.domain for m in self.metrics_history)
        
        if len(domains) < 2:
            return {
                'analysis': 'insufficient_domains',
                'message': 'Need at least 2 domains for cross-domain analysis'
            }
        
        # Analyze correlation between domain improvements
        domain_improvements = {}
        for domain in domains:
            recent_metrics = [
                m for m in self.metrics_history 
                if (m.domain == domain and 
                    m.improvement_percentage is not None and
                    m.timestamp >= datetime.now() - timedelta(days=30))
            ]
            
            if recent_metrics:
                domain_improvements[domain] = statistics.mean([
                    m.improvement_percentage for m in recent_metrics
                ])
        
        # Find potential learning transfer patterns
        transfer_patterns = []
        for domain1 in domain_improvements:
            for domain2 in domain_improvements:
                if domain1 != domain2:
                    improvement1 = domain_improvements[domain1]
                    improvement2 = domain_improvements[domain2]
                    
                    # If both domains show similar improvement patterns
                    if abs(improvement1 - improvement2) < 5 and improvement1 > 5:
                        transfer_patterns.append({
                            'source_domain': domain1,
                            'target_domain': domain2,
                            'correlation_strength': 'high',
                            'improvement_similarity': abs(improvement1 - improvement2)
                        })
        
        return {
            'analysis': 'completed',
            'domains_analyzed': len(domains),
            'domain_improvements': domain_improvements,
            'transfer_patterns': transfer_patterns,
            'cross_domain_learning_score': len(transfer_patterns) / max(len(domains) - 1, 1)
        }
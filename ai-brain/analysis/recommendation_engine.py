"""
OUIOE Phase 6: Deductive Analysis & Intelligent Insights - Recommendation Engine
================================================================================

This module provides intelligent recommendation generation based on analysis results,
patterns, root causes, and trends. It generates actionable, prioritized recommendations
with implementation guidance and risk assessment.

Key Features:
- AI-driven recommendation generation
- Multi-criteria recommendation scoring
- Implementation guidance and risk assessment
- Preventive and corrective recommendation types
- Best practice recommendations
- Context-aware recommendation filtering
- Learning from recommendation outcomes

Author: OUIOE Development Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import json
import statistics
import math
from collections import defaultdict, Counter

from .analysis_models import (
    AnalysisResult, Recommendation, RecommendationType, Pattern, RootCause,
    Trend, Correlation, AnalysisContext, AnalysisMetrics, PatternType,
    TrendDirection, LearningData
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Intelligent recommendation engine for generating actionable insights.
    
    This engine analyzes patterns, root causes, trends, and correlations to generate
    prioritized, actionable recommendations with implementation guidance and risk assessment.
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.recommendation_templates: Dict[str, Dict[str, Any]] = {}
        self.learning_data: Dict[str, List[LearningData]] = defaultdict(list)
        self.recommendation_cache: Dict[str, List[Recommendation]] = {}
        
        # Recommendation scoring weights
        self.scoring_weights = {
            'impact': 0.3,
            'confidence': 0.25,
            'urgency': 0.2,
            'feasibility': 0.15,
            'risk': 0.1
        }
        
        # Initialize recommendation templates
        self._initialize_recommendation_templates()
        
        logger.info("Recommendation Engine initialized")
    
    def _initialize_recommendation_templates(self):
        """Initialize built-in recommendation templates."""
        self.recommendation_templates = {
            # Error Pattern Recommendations
            'error_cascade': {
                'type': RecommendationType.CORRECTIVE,
                'title': 'Address Error Cascade',
                'description_template': 'Implement error handling and circuit breaker patterns to prevent error cascades',
                'priority_base': 4,
                'implementation_steps': [
                    'Implement circuit breaker pattern',
                    'Add comprehensive error logging',
                    'Set up error monitoring and alerting',
                    'Review and improve error handling logic',
                    'Implement graceful degradation'
                ],
                'expected_benefits': [
                    'Reduced error propagation',
                    'Improved system stability',
                    'Better error visibility',
                    'Faster error recovery'
                ],
                'risks': [
                    'Temporary service disruption during implementation',
                    'Potential performance overhead'
                ]
            },
            'recurring_error': {
                'type': RecommendationType.CORRECTIVE,
                'title': 'Fix Recurring Error',
                'description_template': 'Investigate and resolve recurring error: {error_type}',
                'priority_base': 4,
                'implementation_steps': [
                    'Analyze error logs and stack traces',
                    'Identify root cause of recurring error',
                    'Implement fix for identified issue',
                    'Add unit tests to prevent regression',
                    'Monitor error rates post-fix'
                ],
                'expected_benefits': [
                    'Elimination of recurring errors',
                    'Improved system reliability',
                    'Better user experience'
                ],
                'risks': [
                    'Potential introduction of new bugs',
                    'Service downtime during deployment'
                ]
            },
            
            # Performance Pattern Recommendations
            'performance_degradation': {
                'type': RecommendationType.CORRECTIVE,
                'title': 'Address Performance Degradation',
                'description_template': 'Investigate and resolve performance degradation of {degradation_percentage}%',
                'priority_base': 4,
                'implementation_steps': [
                    'Profile application performance',
                    'Identify performance bottlenecks',
                    'Optimize critical code paths',
                    'Review database queries and indexes',
                    'Consider caching strategies',
                    'Monitor performance metrics'
                ],
                'expected_benefits': [
                    'Restored performance levels',
                    'Improved user experience',
                    'Better resource utilization'
                ],
                'risks': [
                    'Optimization may introduce complexity',
                    'Potential for over-optimization'
                ]
            },
            'performance_spike': {
                'type': RecommendationType.PREVENTIVE,
                'title': 'Prevent Performance Spikes',
                'description_template': 'Implement monitoring and auto-scaling to handle performance spikes',
                'priority_base': 3,
                'implementation_steps': [
                    'Set up performance monitoring',
                    'Implement auto-scaling policies',
                    'Add load balancing',
                    'Optimize resource allocation',
                    'Create performance alerts'
                ],
                'expected_benefits': [
                    'Automatic spike handling',
                    'Improved system resilience',
                    'Better resource efficiency'
                ],
                'risks': [
                    'Increased infrastructure costs',
                    'Complexity in scaling logic'
                ]
            },
            
            # Trend-based Recommendations
            'increasing_error_trend': {
                'type': RecommendationType.PREVENTIVE,
                'title': 'Address Increasing Error Trend',
                'description_template': 'Take preventive action for increasing error trend',
                'priority_base': 4,
                'implementation_steps': [
                    'Analyze error trend patterns',
                    'Identify contributing factors',
                    'Implement preventive measures',
                    'Enhance monitoring and alerting',
                    'Review system capacity'
                ],
                'expected_benefits': [
                    'Prevention of error escalation',
                    'Improved system stability',
                    'Proactive issue resolution'
                ],
                'risks': [
                    'Resource investment in prevention',
                    'Potential false positives'
                ]
            },
            'decreasing_performance_trend': {
                'type': RecommendationType.OPTIMIZATION,
                'title': 'Optimize Declining Performance',
                'description_template': 'Address declining performance trend before it becomes critical',
                'priority_base': 3,
                'implementation_steps': [
                    'Conduct performance analysis',
                    'Identify degradation causes',
                    'Implement performance optimizations',
                    'Review resource allocation',
                    'Set up performance baselines'
                ],
                'expected_benefits': [
                    'Prevented performance crisis',
                    'Maintained service quality',
                    'Optimized resource usage'
                ],
                'risks': [
                    'Optimization complexity',
                    'Potential service disruption'
                ]
            },
            
            # Security Pattern Recommendations
            'suspicious_access': {
                'type': RecommendationType.SECURITY,
                'title': 'Investigate Suspicious Access',
                'description_template': 'Investigate and secure against suspicious access patterns',
                'priority_base': 5,
                'implementation_steps': [
                    'Review access logs and patterns',
                    'Implement additional authentication measures',
                    'Set up access monitoring and alerts',
                    'Review and update security policies',
                    'Consider implementing rate limiting'
                ],
                'expected_benefits': [
                    'Enhanced security posture',
                    'Prevention of unauthorized access',
                    'Better access visibility'
                ],
                'risks': [
                    'Potential impact on legitimate users',
                    'Increased authentication complexity'
                ]
            },
            
            # Resource Pattern Recommendations
            'high_resource_utilization': {
                'type': RecommendationType.SCALING,
                'title': 'Address High Resource Utilization',
                'description_template': 'Scale resources to handle high {resource_type} utilization',
                'priority_base': 3,
                'implementation_steps': [
                    'Analyze resource usage patterns',
                    'Implement resource monitoring',
                    'Scale resources horizontally or vertically',
                    'Optimize resource allocation',
                    'Set up auto-scaling policies'
                ],
                'expected_benefits': [
                    'Improved system performance',
                    'Better resource availability',
                    'Reduced bottlenecks'
                ],
                'risks': [
                    'Increased infrastructure costs',
                    'Potential over-provisioning'
                ]
            },
            
            # Correlation-based Recommendations
            'strong_correlation': {
                'type': RecommendationType.OPTIMIZATION,
                'title': 'Leverage Strong Correlation',
                'description_template': 'Optimize based on strong correlation between {variables}',
                'priority_base': 2,
                'implementation_steps': [
                    'Analyze correlation implications',
                    'Identify optimization opportunities',
                    'Implement correlation-based improvements',
                    'Monitor correlation stability',
                    'Document correlation insights'
                ],
                'expected_benefits': [
                    'Data-driven optimizations',
                    'Better system understanding',
                    'Improved predictability'
                ],
                'risks': [
                    'Correlation may not imply causation',
                    'Correlation may change over time'
                ]
            },
            
            # Best Practice Recommendations
            'monitoring_enhancement': {
                'type': RecommendationType.BEST_PRACTICE,
                'title': 'Enhance Monitoring Coverage',
                'description_template': 'Improve monitoring and observability based on analysis findings',
                'priority_base': 2,
                'implementation_steps': [
                    'Identify monitoring gaps',
                    'Implement comprehensive metrics collection',
                    'Set up intelligent alerting',
                    'Create monitoring dashboards',
                    'Establish monitoring best practices'
                ],
                'expected_benefits': [
                    'Better system visibility',
                    'Faster issue detection',
                    'Improved troubleshooting'
                ],
                'risks': [
                    'Monitoring overhead',
                    'Alert fatigue potential'
                ]
            },
            'documentation_update': {
                'type': RecommendationType.MAINTENANCE,
                'title': 'Update System Documentation',
                'description_template': 'Update documentation based on discovered patterns and insights',
                'priority_base': 1,
                'implementation_steps': [
                    'Review current documentation',
                    'Document discovered patterns',
                    'Update troubleshooting guides',
                    'Create operational runbooks',
                    'Establish documentation maintenance process'
                ],
                'expected_benefits': [
                    'Better knowledge sharing',
                    'Improved troubleshooting',
                    'Reduced learning curve'
                ],
                'risks': [
                    'Documentation maintenance overhead',
                    'Potential for outdated information'
                ]
            }
        }
    
    async def generate_recommendations(
        self,
        analysis_result: AnalysisResult,
        context: AnalysisContext
    ) -> Tuple[List[Recommendation], AnalysisMetrics]:
        """
        Generate intelligent recommendations based on analysis results.
        
        Args:
            analysis_result: Results from deductive analysis
            context: Analysis context and preferences
            
        Returns:
            Tuple of (recommendations list, generation metrics)
        """
        start_time = datetime.now()
        
        logger.info(f"Generating recommendations for analysis {analysis_result.id}")
        
        # Initialize metrics
        metrics = AnalysisMetrics(
            analysis_id=analysis_result.id
        )
        
        recommendations = []
        
        try:
            # Generate recommendations from different analysis components
            pattern_recommendations = await self._generate_pattern_recommendations(
                analysis_result.patterns, context
            )
            recommendations.extend(pattern_recommendations)
            
            root_cause_recommendations = await self._generate_root_cause_recommendations(
                analysis_result.root_causes, context
            )
            recommendations.extend(root_cause_recommendations)
            
            trend_recommendations = await self._generate_trend_recommendations(
                analysis_result.trends, context
            )
            recommendations.extend(trend_recommendations)
            
            correlation_recommendations = await self._generate_correlation_recommendations(
                analysis_result.correlations, context
            )
            recommendations.extend(correlation_recommendations)
            
            # Generate general best practice recommendations
            best_practice_recommendations = await self._generate_best_practice_recommendations(
                analysis_result, context
            )
            recommendations.extend(best_practice_recommendations)
            
            # Remove duplicates and merge similar recommendations
            recommendations = await self._deduplicate_recommendations(recommendations)
            
            # Score and prioritize recommendations
            recommendations = await self._score_and_prioritize_recommendations(
                recommendations, analysis_result, context
            )
            
            # Apply context-based filtering
            recommendations = await self._filter_recommendations(recommendations, context)
            
            # Limit to top recommendations
            max_recommendations = context.preferences.get('max_recommendations', 20)
            recommendations = recommendations[:max_recommendations]
            
            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            metrics.execution_time = execution_time
            metrics.recommendations_generated = len(recommendations)
            metrics.confidence_score = self._calculate_recommendation_confidence(recommendations)
            
            logger.info(f"Generated {len(recommendations)} recommendations in {execution_time:.2f}s")
            
            return recommendations, metrics
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return [], metrics
    
    async def _generate_pattern_recommendations(
        self,
        patterns: List[Pattern],
        context: AnalysisContext
    ) -> List[Recommendation]:
        """Generate recommendations based on identified patterns."""
        recommendations = []
        
        for pattern in patterns:
            # Error patterns
            if pattern.pattern_type == PatternType.ERROR:
                if 'cascade' in pattern.name.lower():
                    rec = await self._create_recommendation_from_template(
                        'error_cascade', pattern, context
                    )
                    recommendations.append(rec)
                elif 'recurring' in pattern.name.lower():
                    rec = await self._create_recommendation_from_template(
                        'recurring_error', pattern, context,
                        {'error_type': pattern.characteristics.get('error_type', 'Unknown')}
                    )
                    recommendations.append(rec)
            
            # Performance patterns
            elif pattern.pattern_type == PatternType.PERFORMANCE:
                if 'degradation' in pattern.name.lower():
                    rec = await self._create_recommendation_from_template(
                        'performance_degradation', pattern, context,
                        {'degradation_percentage': pattern.characteristics.get('degradation_percentage', 0)}
                    )
                    recommendations.append(rec)
                elif 'spike' in pattern.name.lower():
                    rec = await self._create_recommendation_from_template(
                        'performance_spike', pattern, context
                    )
                    recommendations.append(rec)
            
            # Security patterns
            elif pattern.pattern_type == PatternType.SECURITY:
                if 'suspicious' in pattern.name.lower():
                    rec = await self._create_recommendation_from_template(
                        'suspicious_access', pattern, context
                    )
                    recommendations.append(rec)
            
            # Resource patterns
            elif pattern.pattern_type == PatternType.RESOURCE:
                if 'high' in pattern.name.lower() and 'utilization' in pattern.name.lower():
                    rec = await self._create_recommendation_from_template(
                        'high_resource_utilization', pattern, context,
                        {'resource_type': pattern.characteristics.get('resource_type', 'system')}
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    async def _generate_root_cause_recommendations(
        self,
        root_causes: List[RootCause],
        context: AnalysisContext
    ) -> List[Recommendation]:
        """Generate recommendations based on identified root causes."""
        recommendations = []
        
        for root_cause in root_causes:
            # High severity root causes get immediate attention
            if root_cause.severity > 0.7:
                rec = Recommendation(
                    title=f"Critical: Address {root_cause.name}",
                    description=f"Immediate action required for high-severity root cause: {root_cause.description}",
                    recommendation_type=RecommendationType.CORRECTIVE,
                    priority=5,
                    confidence=root_cause.confidence,
                    impact_score=root_cause.severity,
                    effort_estimate="high",
                    implementation_steps=[
                        "Assemble incident response team",
                        "Investigate root cause evidence",
                        "Implement immediate mitigation",
                        "Develop long-term solution",
                        "Monitor for recurrence"
                    ],
                    expected_benefits=[
                        "Resolution of critical issue",
                        "Prevention of system failure",
                        "Improved system stability"
                    ],
                    risks=[
                        "Potential service disruption during fix",
                        "Resource intensive resolution"
                    ],
                    prerequisites=["Access to affected systems", "Technical expertise"],
                    related_analysis=[root_cause.id]
                )
                recommendations.append(rec)
            
            # Medium severity root causes get planned attention
            elif root_cause.severity > 0.4:
                rec = Recommendation(
                    title=f"Plan Resolution: {root_cause.name}",
                    description=f"Schedule resolution for moderate-severity root cause: {root_cause.description}",
                    recommendation_type=RecommendationType.CORRECTIVE,
                    priority=3,
                    confidence=root_cause.confidence,
                    impact_score=root_cause.severity,
                    effort_estimate="medium",
                    implementation_steps=[
                        "Schedule investigation time",
                        "Analyze contributing factors",
                        "Design solution approach",
                        "Implement and test solution",
                        "Deploy and monitor"
                    ],
                    expected_benefits=[
                        "Prevention of issue escalation",
                        "Improved system reliability",
                        "Reduced future incidents"
                    ],
                    risks=[
                        "Issue may worsen if delayed",
                        "Solution complexity"
                    ],
                    prerequisites=["Development resources", "Testing environment"],
                    related_analysis=[root_cause.id]
                )
                recommendations.append(rec)
        
        return recommendations
    
    async def _generate_trend_recommendations(
        self,
        trends: List[Trend],
        context: AnalysisContext
    ) -> List[Recommendation]:
        """Generate recommendations based on identified trends."""
        recommendations = []
        
        for trend in trends:
            # Increasing error trends
            if (trend.direction == TrendDirection.INCREASING and 
                'error' in trend.name.lower() and trend.confidence > 0.7):
                rec = await self._create_recommendation_from_template(
                    'increasing_error_trend', trend, context
                )
                recommendations.append(rec)
            
            # Decreasing performance trends
            elif (trend.direction == TrendDirection.DECREASING and 
                  'performance' in trend.name.lower() and trend.confidence > 0.7):
                rec = await self._create_recommendation_from_template(
                    'decreasing_performance_trend', trend, context
                )
                recommendations.append(rec)
            
            # Strong trends with forecasting capability
            elif trend.strength > 0.8 and trend.forecast:
                rec = Recommendation(
                    title=f"Monitor Trend: {trend.name}",
                    description=f"Monitor {trend.direction.value} trend with strong predictive value",
                    recommendation_type=RecommendationType.PREVENTIVE,
                    priority=2,
                    confidence=trend.confidence,
                    impact_score=trend.strength,
                    effort_estimate="low",
                    implementation_steps=[
                        "Set up trend monitoring",
                        "Create trend-based alerts",
                        "Review trend forecasts regularly",
                        "Plan proactive actions"
                    ],
                    expected_benefits=[
                        "Proactive issue prevention",
                        "Better capacity planning",
                        "Improved predictability"
                    ],
                    risks=[
                        "Trend may change unexpectedly",
                        "False positive alerts"
                    ],
                    related_analysis=[trend.id]
                )
                recommendations.append(rec)
        
        return recommendations
    
    async def _generate_correlation_recommendations(
        self,
        correlations: List[Correlation],
        context: AnalysisContext
    ) -> List[Recommendation]:
        """Generate recommendations based on identified correlations."""
        recommendations = []
        
        # Strong correlations
        strong_correlations = [c for c in correlations if abs(c.correlation_coefficient) > 0.8]
        
        for correlation in strong_correlations:
            rec = await self._create_recommendation_from_template(
                'strong_correlation', correlation, context,
                {'variables': ' and '.join(correlation.variables)}
            )
            recommendations.append(rec)
        
        return recommendations
    
    async def _generate_best_practice_recommendations(
        self,
        analysis_result: AnalysisResult,
        context: AnalysisContext
    ) -> List[Recommendation]:
        """Generate general best practice recommendations."""
        recommendations = []
        
        # Always recommend monitoring enhancement if patterns were found
        if analysis_result.patterns:
            rec = await self._create_recommendation_from_template(
                'monitoring_enhancement', None, context
            )
            recommendations.append(rec)
        
        # Recommend documentation update if significant findings
        if (len(analysis_result.patterns) > 5 or 
            len(analysis_result.root_causes) > 2 or 
            len(analysis_result.trends) > 3):
            rec = await self._create_recommendation_from_template(
                'documentation_update', None, context
            )
            recommendations.append(rec)
        
        return recommendations
    
    async def _create_recommendation_from_template(
        self,
        template_name: str,
        analysis_object: Any,
        context: AnalysisContext,
        template_vars: Optional[Dict[str, Any]] = None
    ) -> Recommendation:
        """Create a recommendation from a template."""
        template = self.recommendation_templates[template_name]
        template_vars = template_vars or {}
        
        # Format description with template variables
        description = template['description_template'].format(**template_vars)
        
        # Calculate confidence based on analysis object
        confidence = 0.8  # Default confidence
        if hasattr(analysis_object, 'confidence'):
            confidence = analysis_object.confidence * 0.9  # Slightly reduce for recommendation
        
        # Calculate impact score
        impact_score = 0.7  # Default impact
        if hasattr(analysis_object, 'severity'):
            impact_score = analysis_object.severity
        elif hasattr(analysis_object, 'strength'):
            impact_score = analysis_object.strength
        elif hasattr(analysis_object, 'confidence'):
            impact_score = analysis_object.confidence
        
        # Create recommendation
        rec = Recommendation(
            title=template['title'],
            description=description,
            recommendation_type=template['type'],
            priority=template['priority_base'],
            confidence=confidence,
            impact_score=impact_score,
            effort_estimate="medium",  # Default effort
            implementation_steps=template['implementation_steps'].copy(),
            expected_benefits=template['expected_benefits'].copy(),
            risks=template['risks'].copy(),
            related_analysis=[analysis_object.id] if hasattr(analysis_object, 'id') else []
        )
        
        return rec
    
    async def _deduplicate_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Remove duplicate and merge similar recommendations."""
        if not recommendations:
            return recommendations
        
        # Group similar recommendations by title similarity
        grouped_recommendations = defaultdict(list)
        
        for rec in recommendations:
            # Create a key based on title words
            title_words = set(rec.title.lower().split())
            
            # Find existing group with similar title
            found_group = None
            for existing_key in grouped_recommendations.keys():
                existing_words = set(existing_key.lower().split())
                # If more than 50% of words overlap, consider similar
                overlap = len(title_words.intersection(existing_words))
                if overlap > 0 and overlap / max(len(title_words), len(existing_words)) > 0.5:
                    found_group = existing_key
                    break
            
            if found_group:
                grouped_recommendations[found_group].append(rec)
            else:
                grouped_recommendations[rec.title].append(rec)
        
        # Merge similar recommendations
        merged_recommendations = []
        
        for group_title, group_recs in grouped_recommendations.items():
            if len(group_recs) == 1:
                merged_recommendations.append(group_recs[0])
            else:
                # Merge multiple similar recommendations
                merged_rec = await self._merge_recommendations(group_recs)
                merged_recommendations.append(merged_rec)
        
        return merged_recommendations
    
    async def _merge_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> Recommendation:
        """Merge multiple similar recommendations into one."""
        if len(recommendations) == 1:
            return recommendations[0]
        
        # Use the highest priority recommendation as base
        base_rec = max(recommendations, key=lambda x: x.priority)
        
        # Merge characteristics
        merged_rec = Recommendation(
            title=base_rec.title,
            description=base_rec.description,
            recommendation_type=base_rec.recommendation_type,
            priority=max(rec.priority for rec in recommendations),
            confidence=statistics.mean(rec.confidence for rec in recommendations),
            impact_score=max(rec.impact_score for rec in recommendations),
            effort_estimate=base_rec.effort_estimate
        )
        
        # Merge implementation steps (remove duplicates)
        all_steps = []
        for rec in recommendations:
            all_steps.extend(rec.implementation_steps)
        merged_rec.implementation_steps = list(dict.fromkeys(all_steps))  # Remove duplicates while preserving order
        
        # Merge benefits and risks
        all_benefits = []
        all_risks = []
        for rec in recommendations:
            all_benefits.extend(rec.expected_benefits)
            all_risks.extend(rec.risks)
        
        merged_rec.expected_benefits = list(dict.fromkeys(all_benefits))
        merged_rec.risks = list(dict.fromkeys(all_risks))
        
        # Merge related analysis
        all_related = []
        for rec in recommendations:
            all_related.extend(rec.related_analysis)
        merged_rec.related_analysis = list(set(all_related))
        
        return merged_rec
    
    async def _score_and_prioritize_recommendations(
        self,
        recommendations: List[Recommendation],
        analysis_result: AnalysisResult,
        context: AnalysisContext
    ) -> List[Recommendation]:
        """Score and prioritize recommendations based on multiple criteria."""
        for rec in recommendations:
            # Calculate composite score
            score = await self._calculate_recommendation_score(rec, analysis_result, context)
            
            # Store score in impact_score field for sorting
            rec.impact_score = score
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x.impact_score, reverse=True)
        
        return recommendations
    
    async def _calculate_recommendation_score(
        self,
        recommendation: Recommendation,
        analysis_result: AnalysisResult,
        context: AnalysisContext
    ) -> float:
        """Calculate a composite score for recommendation prioritization."""
        # Base scores
        impact_score = recommendation.impact_score
        confidence_score = recommendation.confidence
        urgency_score = recommendation.priority / 5.0  # Normalize to 0-1
        
        # Feasibility score based on effort estimate
        feasibility_scores = {
            'low': 1.0,
            'medium': 0.7,
            'high': 0.4
        }
        feasibility_score = feasibility_scores.get(recommendation.effort_estimate, 0.7)
        
        # Risk score (inverse - lower risk is better)
        risk_score = 1.0 - (len(recommendation.risks) * 0.1)  # Reduce score for each risk
        risk_score = max(0.1, risk_score)  # Minimum risk score
        
        # Apply learning from historical data
        learning_adjustment = await self._get_learning_adjustment(recommendation)
        
        # Calculate weighted composite score
        composite_score = (
            self.scoring_weights['impact'] * impact_score +
            self.scoring_weights['confidence'] * confidence_score +
            self.scoring_weights['urgency'] * urgency_score +
            self.scoring_weights['feasibility'] * feasibility_score +
            self.scoring_weights['risk'] * risk_score
        )
        
        # Apply learning adjustment
        composite_score *= (1.0 + learning_adjustment)
        
        return min(1.0, composite_score)  # Cap at 1.0
    
    async def _get_learning_adjustment(self, recommendation: Recommendation) -> float:
        """Get learning-based adjustment for recommendation scoring."""
        # Look for similar recommendations in learning data
        similar_recommendations = []
        
        for rec_type, learning_entries in self.learning_data.items():
            if rec_type == recommendation.recommendation_type.value:
                similar_recommendations.extend(learning_entries)
        
        if not similar_recommendations:
            return 0.0  # No learning data available
        
        # Calculate average success rate
        successful_implementations = [
            entry for entry in similar_recommendations 
            if entry.implementation_success is True
        ]
        
        if len(similar_recommendations) < 3:
            return 0.0  # Not enough data for reliable learning
        
        success_rate = len(successful_implementations) / len(similar_recommendations)
        
        # Adjust score based on success rate
        # +20% for high success rate (>80%), -20% for low success rate (<40%)
        if success_rate > 0.8:
            return 0.2
        elif success_rate < 0.4:
            return -0.2
        else:
            return 0.0
    
    async def _filter_recommendations(
        self,
        recommendations: List[Recommendation],
        context: AnalysisContext
    ) -> List[Recommendation]:
        """Apply context-based filtering to recommendations."""
        filtered_recommendations = []
        
        # Get filtering preferences from context
        min_confidence = context.preferences.get('min_recommendation_confidence', 0.5)
        excluded_types = context.preferences.get('excluded_recommendation_types', [])
        max_effort = context.preferences.get('max_effort_level', 'high')
        
        effort_levels = {'low': 1, 'medium': 2, 'high': 3}
        max_effort_level = effort_levels.get(max_effort, 3)
        
        for rec in recommendations:
            # Filter by confidence
            if rec.confidence < min_confidence:
                continue
            
            # Filter by type
            if rec.recommendation_type.value in excluded_types:
                continue
            
            # Filter by effort level
            rec_effort_level = effort_levels.get(rec.effort_estimate, 2)
            if rec_effort_level > max_effort_level:
                continue
            
            filtered_recommendations.append(rec)
        
        return filtered_recommendations
    
    def _calculate_recommendation_confidence(self, recommendations: List[Recommendation]) -> float:
        """Calculate overall confidence score for generated recommendations."""
        if not recommendations:
            return 0.0
        
        # Weight by recommendation priority
        weighted_sum = sum(rec.confidence * rec.priority for rec in recommendations)
        weight_total = sum(rec.priority for rec in recommendations)
        
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    async def learn_from_feedback(
        self,
        recommendation_id: str,
        learning_data: LearningData
    ) -> bool:
        """Learn from recommendation implementation feedback."""
        try:
            # Find the recommendation type for categorization
            recommendation = None
            for cached_recs in self.recommendation_cache.values():
                for rec in cached_recs:
                    if rec.id == recommendation_id:
                        recommendation = rec
                        break
                if recommendation:
                    break
            
            if not recommendation:
                logger.warning(f"Recommendation {recommendation_id} not found for learning")
                return False
            
            # Store learning data
            rec_type = recommendation.recommendation_type.value
            self.learning_data[rec_type].append(learning_data)
            
            # Limit learning data to prevent memory issues
            max_learning_entries = 100
            if len(self.learning_data[rec_type]) > max_learning_entries:
                # Keep most recent entries
                self.learning_data[rec_type] = self.learning_data[rec_type][-max_learning_entries:]
            
            logger.info(f"Learned from recommendation {recommendation_id}: success={learning_data.implementation_success}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn from feedback: {e}")
            return False
    
    async def get_recommendation_analytics(self) -> Dict[str, Any]:
        """Get analytics about recommendation generation and success rates."""
        analytics = {
            'total_recommendations_generated': sum(
                len(recs) for recs in self.recommendation_cache.values()
            ),
            'recommendation_types': defaultdict(int),
            'success_rates': {},
            'learning_data_points': sum(
                len(entries) for entries in self.learning_data.values()
            )
        }
        
        # Count recommendation types
        for cached_recs in self.recommendation_cache.values():
            for rec in cached_recs:
                analytics['recommendation_types'][rec.recommendation_type.value] += 1
        
        # Calculate success rates from learning data
        for rec_type, learning_entries in self.learning_data.items():
            if learning_entries:
                successful = sum(
                    1 for entry in learning_entries 
                    if entry.implementation_success is True
                )
                total = len([
                    entry for entry in learning_entries 
                    if entry.implementation_success is not None
                ])
                
                if total > 0:
                    analytics['success_rates'][rec_type] = successful / total
        
        return dict(analytics)
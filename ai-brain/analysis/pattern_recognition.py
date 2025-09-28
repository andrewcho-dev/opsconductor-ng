"""
OUIOE Phase 6: Deductive Analysis & Intelligent Insights - Pattern Recognition Engine
=====================================================================================

This module provides advanced pattern recognition capabilities for identifying
recurring patterns, anomalies, and behavioral trends in operational data.

Key Features:
- Multi-dimensional pattern detection
- Temporal pattern analysis
- Behavioral pattern recognition
- Anomaly detection and classification
- Pattern correlation and clustering
- Real-time pattern monitoring
- Machine learning-based pattern discovery

Author: OUIOE Development Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, Counter
import json
import math
import statistics

from .analysis_models import (
    DataPoint, Pattern, PatternType, AnalysisContext, 
    AnalysisMetrics, ConfidenceLevel
)

logger = logging.getLogger(__name__)


class PatternRecognitionEngine:
    """
    Advanced pattern recognition engine for identifying patterns in operational data.
    
    This engine uses multiple algorithms and techniques to identify various types
    of patterns including temporal, behavioral, structural, and performance patterns.
    """
    
    def __init__(self):
        """Initialize the pattern recognition engine."""
        self.patterns_cache: Dict[str, List[Pattern]] = {}
        self.pattern_templates: Dict[PatternType, Dict[str, Any]] = {}
        self.learning_data: Dict[str, Any] = defaultdict(list)
        self.confidence_thresholds = {
            PatternType.TEMPORAL: 0.7,
            PatternType.BEHAVIORAL: 0.6,
            PatternType.STRUCTURAL: 0.8,
            PatternType.PERFORMANCE: 0.75,
            PatternType.ERROR: 0.85,
            PatternType.USAGE: 0.65,
            PatternType.SECURITY: 0.9,
            PatternType.RESOURCE: 0.7
        }
        
        # Initialize pattern templates
        self._initialize_pattern_templates()
        
        logger.info("Pattern Recognition Engine initialized")
    
    def _initialize_pattern_templates(self):
        """Initialize built-in pattern templates."""
        self.pattern_templates = {
            PatternType.TEMPORAL: {
                "daily_cycle": {
                    "description": "Daily recurring pattern",
                    "period": 24 * 3600,  # 24 hours in seconds
                    "min_occurrences": 3,
                    "tolerance": 0.1
                },
                "weekly_cycle": {
                    "description": "Weekly recurring pattern",
                    "period": 7 * 24 * 3600,  # 7 days in seconds
                    "min_occurrences": 2,
                    "tolerance": 0.15
                },
                "burst_pattern": {
                    "description": "Sudden burst of activity",
                    "threshold_multiplier": 3.0,
                    "min_duration": 60,  # 1 minute
                    "max_duration": 3600  # 1 hour
                }
            },
            PatternType.BEHAVIORAL: {
                "user_session": {
                    "description": "User session behavior pattern",
                    "min_actions": 3,
                    "max_idle_time": 1800,  # 30 minutes
                    "common_sequences": []
                },
                "error_cascade": {
                    "description": "Cascading error pattern",
                    "time_window": 300,  # 5 minutes
                    "min_errors": 3,
                    "correlation_threshold": 0.8
                }
            },
            PatternType.PERFORMANCE: {
                "degradation": {
                    "description": "Performance degradation pattern",
                    "threshold_decrease": 0.2,  # 20% decrease
                    "min_duration": 300,  # 5 minutes
                    "trend_confidence": 0.8
                },
                "spike": {
                    "description": "Performance spike pattern",
                    "threshold_increase": 2.0,  # 200% increase
                    "max_duration": 600,  # 10 minutes
                    "recovery_time": 1800  # 30 minutes
                }
            }
        }
    
    async def recognize_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext,
        pattern_types: Optional[List[PatternType]] = None
    ) -> Tuple[List[Pattern], AnalysisMetrics]:
        """
        Recognize patterns in the provided data points.
        
        Args:
            data_points: List of data points to analyze
            context: Analysis context and parameters
            pattern_types: Specific pattern types to look for (optional)
            
        Returns:
            Tuple of (recognized patterns, analysis metrics)
        """
        start_time = datetime.now()
        
        if pattern_types is None:
            pattern_types = list(PatternType)
        
        logger.info(f"Starting pattern recognition for {len(data_points)} data points")
        
        # Initialize metrics
        metrics = AnalysisMetrics(
            analysis_id=context.request_id,
            data_points_processed=len(data_points)
        )
        
        # Recognize patterns by type
        all_patterns = []
        
        for pattern_type in pattern_types:
            try:
                patterns = await self._recognize_patterns_by_type(
                    data_points, pattern_type, context
                )
                all_patterns.extend(patterns)
                logger.info(f"Found {len(patterns)} {pattern_type.value} patterns")
            except Exception as e:
                logger.error(f"Error recognizing {pattern_type.value} patterns: {e}")
        
        # Post-process patterns
        all_patterns = await self._post_process_patterns(all_patterns, context)
        
        # Update metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        metrics.execution_time = execution_time
        metrics.patterns_found = len(all_patterns)
        metrics.confidence_score = self._calculate_overall_confidence(all_patterns)
        metrics.quality_score = self._calculate_quality_score(all_patterns, data_points)
        
        logger.info(f"Pattern recognition completed in {execution_time:.2f}s, found {len(all_patterns)} patterns")
        
        return all_patterns, metrics
    
    async def _recognize_patterns_by_type(
        self,
        data_points: List[DataPoint],
        pattern_type: PatternType,
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize patterns of a specific type."""
        if pattern_type == PatternType.TEMPORAL:
            return await self._recognize_temporal_patterns(data_points, context)
        elif pattern_type == PatternType.BEHAVIORAL:
            return await self._recognize_behavioral_patterns(data_points, context)
        elif pattern_type == PatternType.STRUCTURAL:
            return await self._recognize_structural_patterns(data_points, context)
        elif pattern_type == PatternType.PERFORMANCE:
            return await self._recognize_performance_patterns(data_points, context)
        elif pattern_type == PatternType.ERROR:
            return await self._recognize_error_patterns(data_points, context)
        elif pattern_type == PatternType.USAGE:
            return await self._recognize_usage_patterns(data_points, context)
        elif pattern_type == PatternType.SECURITY:
            return await self._recognize_security_patterns(data_points, context)
        elif pattern_type == PatternType.RESOURCE:
            return await self._recognize_resource_patterns(data_points, context)
        else:
            return []
    
    async def _recognize_temporal_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize temporal patterns in the data."""
        patterns = []
        
        # Sort data points by timestamp
        sorted_points = sorted(data_points, key=lambda x: x.timestamp)
        
        if len(sorted_points) < 3:
            return patterns
        
        # Detect daily cycles
        daily_patterns = await self._detect_cyclical_patterns(
            sorted_points, 24 * 3600, "daily_cycle"
        )
        patterns.extend(daily_patterns)
        
        # Detect weekly cycles
        weekly_patterns = await self._detect_cyclical_patterns(
            sorted_points, 7 * 24 * 3600, "weekly_cycle"
        )
        patterns.extend(weekly_patterns)
        
        # Detect burst patterns
        burst_patterns = await self._detect_burst_patterns(sorted_points)
        patterns.extend(burst_patterns)
        
        # Detect trend patterns
        trend_patterns = await self._detect_trend_patterns(sorted_points)
        patterns.extend(trend_patterns)
        
        return patterns
    
    async def _recognize_behavioral_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize behavioral patterns in the data."""
        patterns = []
        
        # Group data points by source/user
        grouped_data = defaultdict(list)
        for point in data_points:
            source = point.metadata.get('user_id', point.source)
            grouped_data[source].append(point)
        
        # Analyze each source's behavior
        for source, points in grouped_data.items():
            if len(points) < 3:
                continue
            
            # Detect session patterns
            session_patterns = await self._detect_session_patterns(points, source)
            patterns.extend(session_patterns)
            
            # Detect sequence patterns
            sequence_patterns = await self._detect_sequence_patterns(points, source)
            patterns.extend(sequence_patterns)
        
        return patterns
    
    async def _recognize_structural_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize structural patterns in the data."""
        patterns = []
        
        # Analyze data structure patterns
        structure_analysis = await self._analyze_data_structure(data_points)
        
        # Create structural patterns based on analysis
        if structure_analysis['hierarchical_depth'] > 3:
            pattern = Pattern(
                pattern_type=PatternType.STRUCTURAL,
                name="Deep Hierarchical Structure",
                description=f"Data shows deep hierarchical structure with {structure_analysis['hierarchical_depth']} levels",
                confidence=0.8,
                characteristics=structure_analysis
            )
            patterns.append(pattern)
        
        return patterns
    
    async def _recognize_performance_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize performance patterns in the data."""
        patterns = []
        
        # Filter numeric performance data
        numeric_points = [
            p for p in data_points 
            if isinstance(p.value, (int, float)) and 'performance' in p.tags
        ]
        
        if len(numeric_points) < 5:
            return patterns
        
        # Detect performance degradation
        degradation_patterns = await self._detect_performance_degradation(numeric_points)
        patterns.extend(degradation_patterns)
        
        # Detect performance spikes
        spike_patterns = await self._detect_performance_spikes(numeric_points)
        patterns.extend(spike_patterns)
        
        return patterns
    
    async def _recognize_error_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize error patterns in the data."""
        patterns = []
        
        # Filter error data
        error_points = [
            p for p in data_points 
            if 'error' in p.tags or 'exception' in str(p.value).lower()
        ]
        
        if len(error_points) < 2:
            return patterns
        
        # Detect error cascades
        cascade_patterns = await self._detect_error_cascades(error_points)
        patterns.extend(cascade_patterns)
        
        # Detect recurring errors
        recurring_patterns = await self._detect_recurring_errors(error_points)
        patterns.extend(recurring_patterns)
        
        return patterns
    
    async def _recognize_usage_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize usage patterns in the data."""
        patterns = []
        
        # Analyze usage frequency
        usage_analysis = await self._analyze_usage_frequency(data_points)
        
        # Create usage patterns
        for pattern_data in usage_analysis:
            pattern = Pattern(
                pattern_type=PatternType.USAGE,
                name=pattern_data['name'],
                description=pattern_data['description'],
                confidence=pattern_data['confidence'],
                frequency=pattern_data['frequency'],
                characteristics=pattern_data['characteristics']
            )
            patterns.append(pattern)
        
        return patterns
    
    async def _recognize_security_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize security patterns in the data."""
        patterns = []
        
        # Filter security-related data
        security_points = [
            p for p in data_points 
            if any(tag in ['security', 'auth', 'login', 'access'] for tag in p.tags)
        ]
        
        if len(security_points) < 3:
            return patterns
        
        # Detect suspicious access patterns
        suspicious_patterns = await self._detect_suspicious_access(security_points)
        patterns.extend(suspicious_patterns)
        
        return patterns
    
    async def _recognize_resource_patterns(
        self,
        data_points: List[DataPoint],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Recognize resource usage patterns in the data."""
        patterns = []
        
        # Filter resource data
        resource_points = [
            p for p in data_points 
            if any(tag in ['cpu', 'memory', 'disk', 'network'] for tag in p.tags)
        ]
        
        if len(resource_points) < 5:
            return patterns
        
        # Detect resource utilization patterns
        utilization_patterns = await self._detect_resource_utilization(resource_points)
        patterns.extend(utilization_patterns)
        
        return patterns
    
    async def _detect_cyclical_patterns(
        self,
        data_points: List[DataPoint],
        period_seconds: int,
        pattern_name: str
    ) -> List[Pattern]:
        """Detect cyclical patterns with a specific period."""
        patterns = []
        
        if len(data_points) < 3:
            return patterns
        
        # Group data points by period
        period_groups = defaultdict(list)
        base_time = data_points[0].timestamp
        
        for point in data_points:
            time_diff = (point.timestamp - base_time).total_seconds()
            period_offset = int(time_diff % period_seconds)
            period_groups[period_offset].append(point)
        
        # Find periods with multiple occurrences
        recurring_periods = {
            offset: points for offset, points in period_groups.items()
            if len(points) >= 3
        }
        
        if recurring_periods:
            # Calculate confidence based on consistency
            total_points = len(data_points)
            recurring_points = sum(len(points) for points in recurring_periods.values())
            confidence = min(0.95, recurring_points / total_points)
            
            if confidence >= self.confidence_thresholds[PatternType.TEMPORAL]:
                pattern = Pattern(
                    pattern_type=PatternType.TEMPORAL,
                    name=f"{pattern_name.replace('_', ' ').title()}",
                    description=f"Recurring pattern every {period_seconds // 3600} hours",
                    confidence=confidence,
                    frequency=len(recurring_periods),
                    first_occurrence=min(data_points, key=lambda x: x.timestamp).timestamp,
                    last_occurrence=max(data_points, key=lambda x: x.timestamp).timestamp,
                    data_points=data_points,
                    characteristics={
                        'period_seconds': period_seconds,
                        'recurring_periods': len(recurring_periods),
                        'average_occurrences_per_period': statistics.mean(
                            len(points) for points in recurring_periods.values()
                        )
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_burst_patterns(self, data_points: List[DataPoint]) -> List[Pattern]:
        """Detect burst patterns in the data."""
        patterns = []
        
        if len(data_points) < 5:
            return patterns
        
        # Calculate time intervals between consecutive points
        intervals = []
        for i in range(1, len(data_points)):
            interval = (data_points[i].timestamp - data_points[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return patterns
        
        # Find bursts (periods of high activity)
        mean_interval = statistics.mean(intervals)
        std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
        
        burst_threshold = max(1, mean_interval - 2 * std_interval)
        
        # Identify burst periods
        burst_starts = []
        burst_ends = []
        in_burst = False
        
        for i, interval in enumerate(intervals):
            if interval <= burst_threshold and not in_burst:
                burst_starts.append(i)
                in_burst = True
            elif interval > burst_threshold and in_burst:
                burst_ends.append(i)
                in_burst = False
        
        # Close any open burst
        if in_burst:
            burst_ends.append(len(intervals) - 1)
        
        # Create burst patterns
        for start, end in zip(burst_starts, burst_ends):
            if end - start >= 2:  # At least 3 points in burst
                burst_points = data_points[start:end+2]
                duration = (burst_points[-1].timestamp - burst_points[0].timestamp).total_seconds()
                
                pattern = Pattern(
                    pattern_type=PatternType.TEMPORAL,
                    name="Activity Burst",
                    description=f"Burst of activity lasting {duration:.1f} seconds",
                    confidence=0.8,
                    frequency=1,
                    first_occurrence=burst_points[0].timestamp,
                    last_occurrence=burst_points[-1].timestamp,
                    data_points=burst_points,
                    characteristics={
                        'duration_seconds': duration,
                        'points_in_burst': len(burst_points),
                        'average_interval': statistics.mean(
                            (burst_points[i+1].timestamp - burst_points[i].timestamp).total_seconds()
                            for i in range(len(burst_points) - 1)
                        )
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_trend_patterns(self, data_points: List[DataPoint]) -> List[Pattern]:
        """Detect trend patterns in numeric data."""
        patterns = []
        
        # Filter numeric data points
        numeric_points = [
            p for p in data_points 
            if isinstance(p.value, (int, float))
        ]
        
        if len(numeric_points) < 5:
            return patterns
        
        # Sort by timestamp
        numeric_points.sort(key=lambda x: x.timestamp)
        
        # Calculate trend using linear regression
        x_values = [(p.timestamp - numeric_points[0].timestamp).total_seconds() for p in numeric_points]
        y_values = [float(p.value) for p in numeric_points]
        
        # Simple linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        # Calculate slope and correlation
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Calculate correlation coefficient
        mean_x = sum_x / n
        mean_y = sum_y / n
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
        denominator_x = sum((x - mean_x) ** 2 for x in x_values)
        denominator_y = sum((y - mean_y) ** 2 for y in y_values)
        
        if denominator_x > 0 and denominator_y > 0:
            correlation = numerator / math.sqrt(denominator_x * denominator_y)
            
            # Create trend pattern if correlation is strong enough
            if abs(correlation) >= 0.7:
                trend_direction = "increasing" if slope > 0 else "decreasing"
                
                pattern = Pattern(
                    pattern_type=PatternType.TEMPORAL,
                    name=f"{trend_direction.title()} Trend",
                    description=f"Strong {trend_direction} trend with correlation {correlation:.3f}",
                    confidence=min(0.95, abs(correlation)),
                    frequency=1,
                    first_occurrence=numeric_points[0].timestamp,
                    last_occurrence=numeric_points[-1].timestamp,
                    data_points=numeric_points,
                    characteristics={
                        'slope': slope,
                        'correlation': correlation,
                        'trend_direction': trend_direction,
                        'start_value': y_values[0],
                        'end_value': y_values[-1],
                        'total_change': y_values[-1] - y_values[0]
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_session_patterns(
        self,
        data_points: List[DataPoint],
        source: str
    ) -> List[Pattern]:
        """Detect user session patterns."""
        patterns = []
        
        if len(data_points) < 3:
            return patterns
        
        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda x: x.timestamp)
        
        # Group into sessions based on idle time
        sessions = []
        current_session = [sorted_points[0]]
        max_idle_time = 1800  # 30 minutes
        
        for i in range(1, len(sorted_points)):
            time_gap = (sorted_points[i].timestamp - sorted_points[i-1].timestamp).total_seconds()
            
            if time_gap <= max_idle_time:
                current_session.append(sorted_points[i])
            else:
                if len(current_session) >= 3:
                    sessions.append(current_session)
                current_session = [sorted_points[i]]
        
        # Add final session
        if len(current_session) >= 3:
            sessions.append(current_session)
        
        # Analyze sessions for patterns
        if len(sessions) >= 2:
            avg_session_length = statistics.mean(len(session) for session in sessions)
            avg_session_duration = statistics.mean(
                (session[-1].timestamp - session[0].timestamp).total_seconds()
                for session in sessions
            )
            
            pattern = Pattern(
                pattern_type=PatternType.BEHAVIORAL,
                name=f"User Session Pattern - {source}",
                description=f"Consistent session behavior with average {avg_session_length:.1f} actions per session",
                confidence=0.75,
                frequency=len(sessions),
                first_occurrence=sessions[0][0].timestamp,
                last_occurrence=sessions[-1][-1].timestamp,
                data_points=data_points,
                characteristics={
                    'total_sessions': len(sessions),
                    'average_session_length': avg_session_length,
                    'average_session_duration': avg_session_duration,
                    'source': source
                }
            )
            patterns.append(pattern)
        
        return patterns
    
    async def _detect_sequence_patterns(
        self,
        data_points: List[DataPoint],
        source: str
    ) -> List[Pattern]:
        """Detect sequence patterns in user actions."""
        patterns = []
        
        if len(data_points) < 4:
            return patterns
        
        # Extract action sequences
        actions = [str(p.value) for p in data_points]
        
        # Find common subsequences of length 3
        subsequences = []
        for i in range(len(actions) - 2):
            subseq = tuple(actions[i:i+3])
            subsequences.append(subseq)
        
        # Count subsequence frequencies
        subseq_counts = Counter(subsequences)
        
        # Find patterns that occur multiple times
        for subseq, count in subseq_counts.items():
            if count >= 2:  # Occurs at least twice
                pattern = Pattern(
                    pattern_type=PatternType.BEHAVIORAL,
                    name=f"Action Sequence Pattern - {source}",
                    description=f"Recurring sequence: {' → '.join(subseq)}",
                    confidence=min(0.9, count / len(subsequences)),
                    frequency=count,
                    characteristics={
                        'sequence': list(subseq),
                        'occurrences': count,
                        'source': source
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _analyze_data_structure(self, data_points: List[DataPoint]) -> Dict[str, Any]:
        """Analyze the structure of the data."""
        structure_info = {
            'total_points': len(data_points),
            'unique_sources': len(set(p.source for p in data_points)),
            'unique_tags': len(set(tag for p in data_points for tag in p.tags)),
            'hierarchical_depth': 0,
            'metadata_complexity': 0
        }
        
        # Analyze metadata complexity
        if data_points:
            max_metadata_depth = max(
                self._calculate_dict_depth(p.metadata) for p in data_points
            )
            structure_info['hierarchical_depth'] = max_metadata_depth
            structure_info['metadata_complexity'] = statistics.mean(
                len(p.metadata) for p in data_points
            )
        
        return structure_info
    
    def _calculate_dict_depth(self, d: Dict[str, Any], depth: int = 0) -> int:
        """Calculate the depth of a nested dictionary."""
        if not isinstance(d, dict) or not d:
            return depth
        
        return max(
            self._calculate_dict_depth(v, depth + 1) if isinstance(v, dict) else depth + 1
            for v in d.values()
        )
    
    async def _detect_performance_degradation(
        self,
        data_points: List[DataPoint]
    ) -> List[Pattern]:
        """Detect performance degradation patterns."""
        patterns = []
        
        if len(data_points) < 5:
            return patterns
        
        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda x: x.timestamp)
        values = [float(p.value) for p in sorted_points]
        
        # Calculate moving average to smooth data
        window_size = min(5, len(values) // 2)
        moving_avg = []
        
        for i in range(len(values) - window_size + 1):
            avg = statistics.mean(values[i:i + window_size])
            moving_avg.append(avg)
        
        # Detect degradation (sustained decrease)
        if len(moving_avg) >= 3:
            degradation_threshold = 0.2  # 20% decrease
            
            for i in range(len(moving_avg) - 2):
                start_value = moving_avg[i]
                end_value = moving_avg[i + 2]
                
                if start_value > 0 and (start_value - end_value) / start_value >= degradation_threshold:
                    pattern = Pattern(
                        pattern_type=PatternType.PERFORMANCE,
                        name="Performance Degradation",
                        description=f"Performance decreased by {((start_value - end_value) / start_value * 100):.1f}%",
                        confidence=0.8,
                        frequency=1,
                        first_occurrence=sorted_points[i].timestamp,
                        last_occurrence=sorted_points[i + 2 + window_size - 1].timestamp,
                        characteristics={
                            'start_value': start_value,
                            'end_value': end_value,
                            'degradation_percentage': (start_value - end_value) / start_value * 100,
                            'duration_seconds': (
                                sorted_points[i + 2 + window_size - 1].timestamp - 
                                sorted_points[i].timestamp
                            ).total_seconds()
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_performance_spikes(
        self,
        data_points: List[DataPoint]
    ) -> List[Pattern]:
        """Detect performance spike patterns."""
        patterns = []
        
        if len(data_points) < 3:
            return patterns
        
        values = [float(p.value) for p in data_points]
        mean_value = statistics.mean(values)
        std_value = statistics.stdev(values) if len(values) > 1 else 0
        
        spike_threshold = mean_value + 2 * std_value
        
        # Find spikes
        for i, point in enumerate(data_points):
            if float(point.value) > spike_threshold:
                pattern = Pattern(
                    pattern_type=PatternType.PERFORMANCE,
                    name="Performance Spike",
                    description=f"Performance spike: {point.value} (threshold: {spike_threshold:.2f})",
                    confidence=0.85,
                    frequency=1,
                    first_occurrence=point.timestamp,
                    last_occurrence=point.timestamp,
                    data_points=[point],
                    characteristics={
                        'spike_value': float(point.value),
                        'threshold': spike_threshold,
                        'deviation_factor': float(point.value) / mean_value if mean_value > 0 else 0
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_error_cascades(self, error_points: List[DataPoint]) -> List[Pattern]:
        """Detect error cascade patterns."""
        patterns = []
        
        if len(error_points) < 3:
            return patterns
        
        # Sort by timestamp
        sorted_errors = sorted(error_points, key=lambda x: x.timestamp)
        
        # Group errors within time windows
        cascade_window = 300  # 5 minutes
        cascades = []
        current_cascade = [sorted_errors[0]]
        
        for i in range(1, len(sorted_errors)):
            time_gap = (sorted_errors[i].timestamp - sorted_errors[i-1].timestamp).total_seconds()
            
            if time_gap <= cascade_window:
                current_cascade.append(sorted_errors[i])
            else:
                if len(current_cascade) >= 3:
                    cascades.append(current_cascade)
                current_cascade = [sorted_errors[i]]
        
        # Add final cascade
        if len(current_cascade) >= 3:
            cascades.append(current_cascade)
        
        # Create cascade patterns
        for cascade in cascades:
            duration = (cascade[-1].timestamp - cascade[0].timestamp).total_seconds()
            
            pattern = Pattern(
                pattern_type=PatternType.ERROR,
                name="Error Cascade",
                description=f"Cascade of {len(cascade)} errors in {duration:.1f} seconds",
                confidence=0.9,
                frequency=1,
                first_occurrence=cascade[0].timestamp,
                last_occurrence=cascade[-1].timestamp,
                data_points=cascade,
                characteristics={
                    'error_count': len(cascade),
                    'duration_seconds': duration,
                    'error_rate': len(cascade) / duration if duration > 0 else 0,
                    'error_types': list(set(str(p.value) for p in cascade))
                }
            )
            patterns.append(pattern)
        
        return patterns
    
    async def _detect_recurring_errors(self, error_points: List[DataPoint]) -> List[Pattern]:
        """Detect recurring error patterns."""
        patterns = []
        
        # Group errors by type
        error_groups = defaultdict(list)
        for point in error_points:
            error_type = str(point.value)
            error_groups[error_type].append(point)
        
        # Find recurring errors
        for error_type, points in error_groups.items():
            if len(points) >= 3:  # At least 3 occurrences
                pattern = Pattern(
                    pattern_type=PatternType.ERROR,
                    name=f"Recurring Error: {error_type}",
                    description=f"Error '{error_type}' occurred {len(points)} times",
                    confidence=0.85,
                    frequency=len(points),
                    first_occurrence=min(points, key=lambda x: x.timestamp).timestamp,
                    last_occurrence=max(points, key=lambda x: x.timestamp).timestamp,
                    data_points=points,
                    characteristics={
                        'error_type': error_type,
                        'occurrences': len(points),
                        'sources': list(set(p.source for p in points))
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _analyze_usage_frequency(self, data_points: List[DataPoint]) -> List[Dict[str, Any]]:
        """Analyze usage frequency patterns."""
        usage_patterns = []
        
        # Group by source
        source_usage = defaultdict(list)
        for point in data_points:
            source_usage[point.source].append(point)
        
        # Analyze each source's usage
        for source, points in source_usage.items():
            if len(points) >= 3:
                # Calculate usage frequency
                time_span = (
                    max(points, key=lambda x: x.timestamp).timestamp -
                    min(points, key=lambda x: x.timestamp).timestamp
                ).total_seconds()
                
                frequency = len(points) / (time_span / 3600) if time_span > 0 else 0  # per hour
                
                usage_patterns.append({
                    'name': f"Usage Pattern - {source}",
                    'description': f"Source '{source}' usage frequency: {frequency:.2f} events/hour",
                    'confidence': min(0.8, len(points) / 10),
                    'frequency': len(points),
                    'characteristics': {
                        'source': source,
                        'events_per_hour': frequency,
                        'total_events': len(points),
                        'time_span_hours': time_span / 3600
                    }
                })
        
        return usage_patterns
    
    async def _detect_suspicious_access(self, security_points: List[DataPoint]) -> List[Pattern]:
        """Detect suspicious access patterns."""
        patterns = []
        
        # Group by source/user
        user_access = defaultdict(list)
        for point in security_points:
            user_id = point.metadata.get('user_id', point.source)
            user_access[user_id].append(point)
        
        # Detect unusual access patterns
        for user_id, points in user_access.items():
            if len(points) >= 5:  # Minimum threshold for analysis
                # Sort by timestamp
                sorted_points = sorted(points, key=lambda x: x.timestamp)
                
                # Calculate access intervals
                intervals = []
                for i in range(1, len(sorted_points)):
                    interval = (sorted_points[i].timestamp - sorted_points[i-1].timestamp).total_seconds()
                    intervals.append(interval)
                
                if intervals:
                    # Detect rapid successive access (potential brute force)
                    rapid_access_threshold = 10  # 10 seconds
                    rapid_accesses = sum(1 for interval in intervals if interval <= rapid_access_threshold)
                    
                    if rapid_accesses >= 3:
                        pattern = Pattern(
                            pattern_type=PatternType.SECURITY,
                            name=f"Suspicious Access Pattern - {user_id}",
                            description=f"Rapid successive access attempts: {rapid_accesses} within {rapid_access_threshold}s",
                            confidence=0.9,
                            frequency=rapid_accesses,
                            first_occurrence=sorted_points[0].timestamp,
                            last_occurrence=sorted_points[-1].timestamp,
                            data_points=points,
                            characteristics={
                                'user_id': user_id,
                                'rapid_accesses': rapid_accesses,
                                'total_accesses': len(points),
                                'min_interval': min(intervals),
                                'avg_interval': statistics.mean(intervals)
                            }
                        )
                        patterns.append(pattern)
        
        return patterns
    
    async def _detect_resource_utilization(self, resource_points: List[DataPoint]) -> List[Pattern]:
        """Detect resource utilization patterns."""
        patterns = []
        
        # Group by resource type
        resource_groups = defaultdict(list)
        for point in resource_points:
            for tag in point.tags:
                if tag in ['cpu', 'memory', 'disk', 'network']:
                    resource_groups[tag].append(point)
                    break
        
        # Analyze each resource type
        for resource_type, points in resource_groups.items():
            if len(points) >= 5:
                numeric_points = [p for p in points if isinstance(p.value, (int, float))]
                
                if len(numeric_points) >= 5:
                    values = [float(p.value) for p in numeric_points]
                    mean_value = statistics.mean(values)
                    max_value = max(values)
                    
                    # Detect high utilization pattern
                    high_threshold = 80.0  # 80% utilization
                    high_util_count = sum(1 for v in values if v >= high_threshold)
                    
                    if high_util_count >= len(values) * 0.3:  # 30% of readings are high
                        pattern = Pattern(
                            pattern_type=PatternType.RESOURCE,
                            name=f"High {resource_type.upper()} Utilization",
                            description=f"High {resource_type} utilization: {high_util_count}/{len(values)} readings above {high_threshold}%",
                            confidence=0.8,
                            frequency=high_util_count,
                            first_occurrence=min(numeric_points, key=lambda x: x.timestamp).timestamp,
                            last_occurrence=max(numeric_points, key=lambda x: x.timestamp).timestamp,
                            data_points=numeric_points,
                            characteristics={
                                'resource_type': resource_type,
                                'high_utilization_count': high_util_count,
                                'total_readings': len(values),
                                'average_utilization': mean_value,
                                'peak_utilization': max_value,
                                'threshold': high_threshold
                            }
                        )
                        patterns.append(pattern)
        
        return patterns
    
    async def _post_process_patterns(
        self,
        patterns: List[Pattern],
        context: AnalysisContext
    ) -> List[Pattern]:
        """Post-process patterns to remove duplicates and enhance quality."""
        if not patterns:
            return patterns
        
        # Remove duplicate patterns
        unique_patterns = []
        seen_signatures = set()
        
        for pattern in patterns:
            # Create a signature for the pattern
            signature = (
                pattern.pattern_type,
                pattern.name,
                len(pattern.data_points),
                pattern.first_occurrence,
                pattern.last_occurrence
            )
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_patterns.append(pattern)
        
        # Sort by confidence (highest first)
        unique_patterns.sort(key=lambda x: x.confidence, reverse=True)
        
        # Limit to top patterns if too many
        max_patterns = context.preferences.get('max_patterns', 50)
        if len(unique_patterns) > max_patterns:
            unique_patterns = unique_patterns[:max_patterns]
        
        logger.info(f"Post-processing: {len(patterns)} -> {len(unique_patterns)} patterns")
        
        return unique_patterns
    
    def _calculate_overall_confidence(self, patterns: List[Pattern]) -> float:
        """Calculate overall confidence score for all patterns."""
        if not patterns:
            return 0.0
        
        # Weight by pattern confidence and frequency
        weighted_sum = sum(p.confidence * (1 + math.log(max(1, p.frequency))) for p in patterns)
        weight_total = sum(1 + math.log(max(1, p.frequency)) for p in patterns)
        
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    def _calculate_quality_score(
        self,
        patterns: List[Pattern],
        data_points: List[DataPoint]
    ) -> float:
        """Calculate quality score based on pattern coverage and diversity."""
        if not patterns or not data_points:
            return 0.0
        
        # Coverage: how much of the data is explained by patterns
        covered_points = set()
        for pattern in patterns:
            for point in pattern.data_points:
                covered_points.add(id(point))
        
        coverage = len(covered_points) / len(data_points)
        
        # Diversity: variety of pattern types
        pattern_types = set(p.pattern_type for p in patterns)
        diversity = len(pattern_types) / len(PatternType)
        
        # Combine coverage and diversity
        quality_score = (coverage * 0.7) + (diversity * 0.3)
        
        return min(1.0, quality_score)
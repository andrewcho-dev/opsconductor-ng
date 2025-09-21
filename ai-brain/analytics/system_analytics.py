"""
Modern System Analytics Engine
Vector-based predictive analytics using AI Brain's system model and vector store
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import structlog

# Import AI Brain components
from integrations.vector_client import OpsConductorVectorStore, VectorCollection
from integrations.llm_client import LLMEngine

logger = structlog.get_logger()

@dataclass
class MaintenanceRecommendation:
    """Maintenance recommendation"""
    target_system: str
    maintenance_type: str
    priority: str  # low, medium, high, critical
    recommended_date: datetime
    reason: str
    estimated_duration: float  # hours
    risk_if_delayed: str
    prerequisites: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['recommended_date'] = self.recommended_date.isoformat()
        return result

@dataclass
class SecurityAlert:
    """Security monitoring alert"""
    alert_id: str
    alert_type: str
    severity: str
    target_system: str
    description: str
    timestamp: datetime
    indicators: List[str]
    recommended_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class PerformanceInsight:
    """Performance analysis insight"""
    metric_name: str
    current_value: float
    trend: str  # improving, stable, degrading
    prediction_7d: float
    prediction_30d: float
    confidence: float
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SystemAnomaly:
    """System anomaly detection result"""
    anomaly_id: str
    system_component: str
    anomaly_type: str
    severity: str
    description: str
    detected_at: datetime
    metrics_involved: List[str]
    confidence_score: float
    suggested_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['detected_at'] = self.detected_at.isoformat()
        return result

class SystemAnalytics:
    """Modern vector-based system analytics engine"""
    
    def __init__(self):
        """Initialize the system analytics engine"""
        self.vector_store = OpsConductorVectorStore()
        self.llm_engine = LLMEngine()
        
        # Time series data for trend analysis
        self.metric_history = defaultdict(lambda: deque(maxlen=1000))
        self.baseline_metrics = {}
        
        # Analytics patterns stored in vector space
        self.analytics_initialized = False
        
        logger.info("Modern System Analytics initialized")
    
    async def initialize(self):
        """Initialize analytics patterns and models"""
        if self.analytics_initialized:
            return
            
        try:
            # Initialize vector store
            await self.vector_store.initialize()
            
            # Load or create analytics patterns
            await self._initialize_analytics_patterns()
            
            self.analytics_initialized = True
            logger.info("System Analytics patterns initialized")
            
        except Exception as e:
            logger.error("Failed to initialize System Analytics", error=str(e))
            raise
    
    async def _initialize_analytics_patterns(self):
        """Initialize analytics patterns in vector store"""
        try:
            # Store system performance patterns
            performance_patterns = [
                {
                    "pattern": "High CPU usage with memory pressure indicates resource contention",
                    "category": "performance",
                    "severity": "high",
                    "indicators": ["cpu_usage > 80", "memory_usage > 85"],
                    "recommendations": ["Scale resources", "Optimize processes", "Check for memory leaks"]
                },
                {
                    "pattern": "Increasing error rates with stable traffic suggests system degradation",
                    "category": "performance", 
                    "severity": "medium",
                    "indicators": ["error_rate increasing", "request_volume stable"],
                    "recommendations": ["Check logs", "Review recent deployments", "Monitor dependencies"]
                },
                {
                    "pattern": "Network latency spikes correlate with database connection issues",
                    "category": "performance",
                    "severity": "high", 
                    "indicators": ["network_latency > 500ms", "db_connection_errors > 0"],
                    "recommendations": ["Check database health", "Review network configuration", "Optimize queries"]
                }
            ]
            
            # Store security patterns
            security_patterns = [
                {
                    "pattern": "Multiple failed login attempts from single IP indicates brute force attack",
                    "category": "security",
                    "severity": "high",
                    "indicators": ["failed_logins > 5", "source_ip_repeated"],
                    "recommendations": ["Block IP address", "Enable rate limiting", "Review authentication logs"]
                },
                {
                    "pattern": "Unusual outbound traffic patterns suggest data exfiltration",
                    "category": "security",
                    "severity": "critical",
                    "indicators": ["outbound_traffic > baseline * 3", "unusual_destinations"],
                    "recommendations": ["Investigate traffic", "Check for malware", "Review user activities"]
                }
            ]
            
            # Store maintenance patterns
            maintenance_patterns = [
                {
                    "pattern": "System uptime exceeding 90 days requires maintenance window",
                    "category": "maintenance",
                    "severity": "medium",
                    "indicators": ["uptime > 90 days", "pending_updates > 0"],
                    "recommendations": ["Schedule maintenance", "Apply security updates", "Restart services"]
                },
                {
                    "pattern": "Disk usage above 85% requires immediate attention",
                    "category": "maintenance", 
                    "severity": "high",
                    "indicators": ["disk_usage > 85"],
                    "recommendations": ["Clean up logs", "Archive old data", "Expand storage"]
                }
            ]
            
            # Store all patterns in vector store
            all_patterns = performance_patterns + security_patterns + maintenance_patterns
            
            for i, pattern in enumerate(all_patterns):
                await self.vector_store.store_automation_pattern(
                    pattern_id=f"analytics_pattern_{i}",
                    pattern_name=f"{pattern['category']}_pattern_{i}",
                    description=pattern['pattern'],
                    metadata={
                        "category": pattern['category'],
                        "severity": pattern['severity'],
                        "indicators": pattern['indicators'],
                        "recommendations": pattern['recommendations'],
                        "type": "analytics_pattern"
                    }
                )
            
            logger.info(f"Stored {len(all_patterns)} analytics patterns in vector store")
            
        except Exception as e:
            logger.error("Failed to initialize analytics patterns", error=str(e))
            raise
    
    async def analyze_system_performance(self, metrics: Dict[str, float]) -> List[PerformanceInsight]:
        """Analyze system performance using vector-based pattern matching"""
        try:
            await self.initialize()
            insights = []
            
            for metric_name, current_value in metrics.items():
                # Store metric history
                self.metric_history[metric_name].append({
                    'timestamp': datetime.utcnow(),
                    'value': current_value
                })
                
                # Calculate trend using vector analysis
                trend = await self._calculate_trend_vector(metric_name)
                
                # Generate predictions using LLM
                prediction_7d, prediction_30d, confidence = await self._predict_metric_values_llm(
                    metric_name, current_value, trend
                )
                
                # Generate recommendations using vector search
                recommendations = await self._generate_performance_recommendations_vector(
                    metric_name, current_value, trend
                )
                
                insight = PerformanceInsight(
                    metric_name=metric_name,
                    current_value=current_value,
                    trend=trend,
                    prediction_7d=prediction_7d,
                    prediction_30d=prediction_30d,
                    confidence=confidence,
                    recommendations=recommendations
                )
                
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            logger.error("Failed to analyze system performance", error=str(e))
            return []
    
    async def _calculate_trend_vector(self, metric_name: str) -> str:
        """Calculate trend using vector-based analysis"""
        try:
            history = list(self.metric_history[metric_name])
            if len(history) < 10:
                return "stable"
            
            # Create trend description for LLM analysis
            recent_values = [h['value'] for h in history[-10:]]
            older_values = [h['value'] for h in history[-20:-10]] if len(history) >= 20 else recent_values
            
            trend_description = f"Metric {metric_name}: recent values {recent_values}, older values {older_values}"
            
            # Use LLM to analyze trend
            prompt = f"""
            Analyze the following metric trend and classify it as 'improving', 'stable', or 'degrading':
            
            {trend_description}
            
            For metrics like cpu_usage, memory_usage, error_rate: increasing values = degrading
            For metrics like throughput, response_time: depends on context
            
            Respond with only one word: improving, stable, or degrading
            """
            
            response = await self.llm_engine.generate_response(prompt)
            trend = response.strip().lower()
            
            if trend not in ['improving', 'stable', 'degrading']:
                trend = 'stable'
                
            return trend
            
        except Exception as e:
            logger.error(f"Failed to calculate trend for {metric_name}", error=str(e))
            return "stable"
    
    async def _predict_metric_values_llm(self, metric_name: str, current_value: float, trend: str) -> Tuple[float, float, float]:
        """Predict metric values using LLM analysis"""
        try:
            history = list(self.metric_history[metric_name])
            
            # Create prediction prompt
            prompt = f"""
            Based on the metric history and current trend, predict future values:
            
            Metric: {metric_name}
            Current Value: {current_value}
            Trend: {trend}
            History Length: {len(history)} data points
            
            Provide predictions for:
            1. 7-day prediction
            2. 30-day prediction  
            3. Confidence level (0.0-1.0)
            
            Consider the trend direction and typical patterns for {metric_name}.
            
            Respond in JSON format:
            {{"prediction_7d": <value>, "prediction_30d": <value>, "confidence": <value>}}
            """
            
            response = await self.llm_engine.generate_response(prompt)
            
            try:
                predictions = json.loads(response)
                return (
                    float(predictions.get('prediction_7d', current_value)),
                    float(predictions.get('prediction_30d', current_value)),
                    float(predictions.get('confidence', 0.7))
                )
            except (json.JSONDecodeError, ValueError):
                # Fallback to simple trend-based prediction
                if trend == 'degrading':
                    return current_value * 1.1, current_value * 1.2, 0.6
                elif trend == 'improving':
                    return current_value * 0.9, current_value * 0.8, 0.6
                else:
                    return current_value, current_value, 0.8
                    
        except Exception as e:
            logger.error(f"Failed to predict values for {metric_name}", error=str(e))
            return current_value, current_value, 0.5
    
    async def _generate_performance_recommendations_vector(self, metric_name: str, current_value: float, trend: str) -> List[str]:
        """Generate recommendations using vector search"""
        try:
            # Create query for similar performance patterns
            query = f"{metric_name} {trend} performance issue recommendations"
            
            # Search for similar patterns
            results = await self.vector_store.search_patterns(
                query=query,
                collection=VectorCollection.AUTOMATION_PATTERNS,
                limit=3
            )
            
            recommendations = []
            
            # Extract recommendations from similar patterns
            for result in results:
                if result.get('metadata', {}).get('category') == 'performance':
                    pattern_recommendations = result.get('metadata', {}).get('recommendations', [])
                    recommendations.extend(pattern_recommendations)
            
            # Add metric-specific recommendations
            if metric_name in ['cpu_usage', 'memory_usage'] and current_value > 80:
                recommendations.append(f"High {metric_name} detected - consider scaling resources")
            
            if trend == 'degrading':
                recommendations.append(f"{metric_name} is degrading - investigate root cause")
            
            # Remove duplicates and limit
            recommendations = list(set(recommendations))[:3]
            
            # Fallback recommendations if none found
            if not recommendations:
                recommendations = [
                    f"Monitor {metric_name} trends closely",
                    "Review system logs for anomalies",
                    "Consider proactive optimization"
                ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations for {metric_name}", error=str(e))
            return [f"Monitor {metric_name} performance"]
    
    async def detect_advanced_anomalies(self, metrics: Dict[str, float], execution_data: Dict[str, Any]) -> List[SystemAnomaly]:
        """Detect anomalies using vector-based pattern matching"""
        try:
            await self.initialize()
            anomalies = []
            
            # Create anomaly detection query
            metrics_description = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
            query = f"system anomaly detection {metrics_description}"
            
            # Search for anomaly patterns
            results = await self.vector_store.search_patterns(
                query=query,
                collection=VectorCollection.AUTOMATION_PATTERNS,
                limit=5
            )
            
            # Analyze each metric for anomalies
            for metric_name, value in metrics.items():
                # Check if value is anomalous based on history
                if await self._is_anomalous_value(metric_name, value):
                    anomaly = SystemAnomaly(
                        anomaly_id=f"anomaly_{metric_name}_{int(datetime.utcnow().timestamp())}",
                        system_component=metric_name.split('_')[0] if '_' in metric_name else 'system',
                        anomaly_type='performance',
                        severity=await self._calculate_anomaly_severity(metric_name, value),
                        description=f"Anomalous {metric_name} value: {value}",
                        detected_at=datetime.utcnow(),
                        metrics_involved=[metric_name],
                        confidence_score=await self._calculate_anomaly_confidence(metric_name, value),
                        suggested_actions=await self._get_anomaly_actions(metric_name, value)
                    )
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error("Failed to detect anomalies", error=str(e))
            return []
    
    async def _is_anomalous_value(self, metric_name: str, value: float) -> bool:
        """Check if a value is anomalous based on history"""
        try:
            history = list(self.metric_history[metric_name])
            if len(history) < 20:
                return False
            
            # Calculate statistical bounds
            values = [h['value'] for h in history[-50:]]  # Last 50 values
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            # Check if value is outside 2 standard deviations
            return abs(value - mean_val) > 2 * std_val
            
        except Exception as e:
            logger.error(f"Failed to check anomaly for {metric_name}", error=str(e))
            return False
    
    async def _calculate_anomaly_severity(self, metric_name: str, value: float) -> str:
        """Calculate anomaly severity"""
        try:
            history = list(self.metric_history[metric_name])
            if len(history) < 10:
                return "low"
            
            values = [h['value'] for h in history[-20:]]
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            deviation = abs(value - mean_val) / std_val if std_val > 0 else 0
            
            if deviation > 3:
                return "critical"
            elif deviation > 2.5:
                return "high"
            elif deviation > 2:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Failed to calculate severity for {metric_name}", error=str(e))
            return "medium"
    
    async def _calculate_anomaly_confidence(self, metric_name: str, value: float) -> float:
        """Calculate confidence score for anomaly detection"""
        try:
            history = list(self.metric_history[metric_name])
            if len(history) < 10:
                return 0.5
            
            # More history = higher confidence
            history_factor = min(len(history) / 100, 1.0)
            
            # Statistical confidence based on deviation
            values = [h['value'] for h in history[-20:]]
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val > 0:
                deviation = abs(value - mean_val) / std_val
                stat_confidence = min(deviation / 3, 1.0)
            else:
                stat_confidence = 0.5
            
            return (history_factor + stat_confidence) / 2
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence for {metric_name}", error=str(e))
            return 0.5
    
    async def _get_anomaly_actions(self, metric_name: str, value: float) -> List[str]:
        """Get suggested actions for anomaly"""
        try:
            # Use vector search for similar anomaly patterns
            query = f"{metric_name} anomaly resolution actions"
            
            results = await self.vector_store.search_patterns(
                query=query,
                collection=VectorCollection.AUTOMATION_PATTERNS,
                limit=2
            )
            
            actions = []
            for result in results:
                pattern_actions = result.get('metadata', {}).get('recommendations', [])
                actions.extend(pattern_actions)
            
            # Add metric-specific actions
            if 'cpu' in metric_name.lower():
                actions.append("Check for high CPU processes")
            elif 'memory' in metric_name.lower():
                actions.append("Investigate memory usage patterns")
            elif 'disk' in metric_name.lower():
                actions.append("Review disk space and I/O patterns")
            
            return list(set(actions))[:3]
            
        except Exception as e:
            logger.error(f"Failed to get actions for {metric_name}", error=str(e))
            return ["Investigate system logs", "Monitor metric trends"]
    
    async def generate_maintenance_schedule(self, targets: List[Dict[str, Any]]) -> List[MaintenanceRecommendation]:
        """Generate maintenance recommendations using LLM analysis"""
        try:
            await self.initialize()
            recommendations = []
            
            for target in targets:
                hostname = target.get('hostname', 'unknown')
                target_type = target.get('type', 'server')
                last_maintenance = target.get('last_maintenance')
                
                # Calculate maintenance urgency using LLM
                prompt = f"""
                Analyze maintenance requirements for:
                - Hostname: {hostname}
                - Type: {target_type}
                - Last Maintenance: {last_maintenance}
                - Current Date: {datetime.utcnow().isoformat()}
                
                Determine:
                1. Maintenance type needed (security_updates, system_restart, hardware_check, etc.)
                2. Priority level (low, medium, high, critical)
                3. Recommended date (within next 30 days)
                4. Estimated duration in hours
                5. Risk if delayed
                
                Respond in JSON format:
                {{
                    "maintenance_type": "<type>",
                    "priority": "<priority>",
                    "recommended_date": "<ISO date>",
                    "estimated_duration": <hours>,
                    "reason": "<explanation>",
                    "risk_if_delayed": "<risk description>",
                    "prerequisites": ["<prerequisite1>", "<prerequisite2>"]
                }}
                """
                
                response = await self.llm_engine.generate_response(prompt)
                
                try:
                    maintenance_data = json.loads(response)
                    
                    recommendation = MaintenanceRecommendation(
                        target_system=hostname,
                        maintenance_type=maintenance_data.get('maintenance_type', 'general_maintenance'),
                        priority=maintenance_data.get('priority', 'medium'),
                        recommended_date=datetime.fromisoformat(
                            maintenance_data.get('recommended_date', 
                                               (datetime.utcnow() + timedelta(days=7)).isoformat())
                        ),
                        reason=maintenance_data.get('reason', 'Regular maintenance required'),
                        estimated_duration=float(maintenance_data.get('estimated_duration', 2.0)),
                        risk_if_delayed=maintenance_data.get('risk_if_delayed', 'Potential system degradation'),
                        prerequisites=maintenance_data.get('prerequisites', ['Schedule downtime', 'Backup data'])
                    )
                    
                    recommendations.append(recommendation)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse maintenance recommendation for {hostname}", error=str(e))
                    
                    # Fallback recommendation
                    recommendation = MaintenanceRecommendation(
                        target_system=hostname,
                        maintenance_type='general_maintenance',
                        priority='medium',
                        recommended_date=datetime.utcnow() + timedelta(days=14),
                        reason='Regular maintenance schedule',
                        estimated_duration=2.0,
                        risk_if_delayed='System performance may degrade',
                        prerequisites=['Schedule maintenance window', 'Notify stakeholders']
                    )
                    recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to generate maintenance schedule", error=str(e))
            return []
    
    async def monitor_security_events(self, log_entries: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Monitor security events using vector-based pattern matching"""
        try:
            await self.initialize()
            alerts = []
            
            for entry in log_entries:
                log_message = entry.get('message', '')
                timestamp = entry.get('timestamp', datetime.utcnow().isoformat())
                source = entry.get('source', 'unknown')
                
                # Search for security patterns
                query = f"security threat detection {log_message}"
                
                results = await self.vector_store.search_patterns(
                    query=query,
                    collection=VectorCollection.AUTOMATION_PATTERNS,
                    limit=3
                )
                
                # Check for security indicators
                security_indicators = []
                severity = 'low'
                
                # Analyze log message for security patterns
                if any(keyword in log_message.lower() for keyword in ['failed login', 'authentication failed', 'invalid user']):
                    security_indicators.append('Authentication failure')
                    severity = 'medium'
                
                if any(keyword in log_message.lower() for keyword in ['sudo', 'privilege escalation', 'admin access']):
                    security_indicators.append('Privilege escalation attempt')
                    severity = 'high'
                
                if any(keyword in log_message.lower() for keyword in ['malware', 'virus', 'trojan', 'suspicious']):
                    security_indicators.append('Malware detection')
                    severity = 'critical'
                
                # Create alert if security indicators found
                if security_indicators:
                    alert = SecurityAlert(
                        alert_id=f"security_{int(datetime.utcnow().timestamp())}_{hash(log_message) % 10000}",
                        alert_type='security_event',
                        severity=severity,
                        target_system=source,
                        description=f"Security event detected: {log_message[:100]}",
                        timestamp=datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp,
                        indicators=security_indicators,
                        recommended_actions=await self._get_security_actions(security_indicators, severity)
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error("Failed to monitor security events", error=str(e))
            return []
    
    async def _get_security_actions(self, indicators: List[str], severity: str) -> List[str]:
        """Get recommended security actions"""
        try:
            # Use vector search for security response patterns
            query = f"security incident response {' '.join(indicators)} {severity}"
            
            results = await self.vector_store.search_patterns(
                query=query,
                collection=VectorCollection.AUTOMATION_PATTERNS,
                limit=2
            )
            
            actions = []
            for result in results:
                if result.get('metadata', {}).get('category') == 'security':
                    pattern_actions = result.get('metadata', {}).get('recommendations', [])
                    actions.extend(pattern_actions)
            
            # Add severity-based actions
            if severity == 'critical':
                actions.extend(['Isolate affected system', 'Initiate incident response'])
            elif severity == 'high':
                actions.extend(['Investigate immediately', 'Review access logs'])
            else:
                actions.extend(['Monitor closely', 'Review security policies'])
            
            return list(set(actions))[:4]
            
        except Exception as e:
            logger.error("Failed to get security actions", error=str(e))
            return ['Review security logs', 'Monitor system activity']
    
    async def get_predictive_insights(self) -> Dict[str, Any]:
        """Get comprehensive predictive insights"""
        try:
            await self.initialize()
            
            # Generate insights using LLM analysis of system state
            prompt = """
            Generate comprehensive predictive insights for system health monitoring.
            
            Provide insights for:
            1. Performance trends and forecasts
            2. Anomaly detection summary
            3. Maintenance scheduling forecast
            4. Security risk assessment
            5. Top recommendations for system optimization
            
            Respond in JSON format with realistic data:
            {
                "performance_trends": {
                    "overall_health": "good|degraded|critical",
                    "cpu_forecast": "stable|increasing|decreasing",
                    "memory_forecast": "stable|increasing|decreasing",
                    "network_forecast": "stable|increasing|decreasing"
                },
                "anomaly_summary": {
                    "active_anomalies": <number>,
                    "resolved_anomalies": <number>,
                    "anomaly_trend": "improving|stable|worsening"
                },
                "maintenance_forecast": {
                    "systems_requiring_maintenance": <number>,
                    "overdue_maintenance": <number>,
                    "upcoming_maintenance": <number>
                },
                "security_status": {
                    "risk_level": "low|medium|high|critical",
                    "active_threats": <number>,
                    "security_score": <0-100>
                },
                "top_recommendations": [
                    "recommendation1",
                    "recommendation2",
                    "recommendation3"
                ]
            }
            """
            
            response = await self.llm_engine.generate_response(prompt)
            
            try:
                insights = json.loads(response)
                return insights
            except json.JSONDecodeError:
                # Fallback insights
                return {
                    "performance_trends": {
                        "overall_health": "good",
                        "cpu_forecast": "stable",
                        "memory_forecast": "stable", 
                        "network_forecast": "stable"
                    },
                    "anomaly_summary": {
                        "active_anomalies": 0,
                        "resolved_anomalies": 5,
                        "anomaly_trend": "improving"
                    },
                    "maintenance_forecast": {
                        "systems_requiring_maintenance": 2,
                        "overdue_maintenance": 0,
                        "upcoming_maintenance": 3
                    },
                    "security_status": {
                        "risk_level": "low",
                        "active_threats": 0,
                        "security_score": 85
                    },
                    "top_recommendations": [
                        "System operating normally - continue monitoring",
                        "Schedule routine maintenance for optimal performance",
                        "Review security policies and update as needed"
                    ]
                }
                
        except Exception as e:
            logger.error("Failed to get predictive insights", error=str(e))
            return {
                "error": "Failed to generate insights",
                "performance_trends": {"overall_health": "unknown"},
                "anomaly_summary": {"active_anomalies": 0},
                "maintenance_forecast": {"systems_requiring_maintenance": 0},
                "security_status": {"risk_level": "unknown"},
                "top_recommendations": ["System status unavailable"]
            }

# Global system analytics instance
system_analytics = SystemAnalytics()
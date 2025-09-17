"""
Predictive Analytics Module
Advanced anomaly detection, maintenance scheduling, and security monitoring
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import sqlite3
import pickle
import os
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import structlog

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
    indicators: List[str]
    detection_time: datetime
    confidence: float
    recommended_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['detection_time'] = self.detection_time.isoformat()
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

class PredictiveAnalytics:
    """Advanced predictive analytics for system optimization"""
    
    def __init__(self, db_path: str = "/app/data/learning.db"):
        self.db_path = db_path
        self.anomaly_models = {}
        self.performance_models = {}
        self.security_models = {}
        self.scalers = {}
        
        # Time series data for trend analysis
        self.metric_history = defaultdict(lambda: deque(maxlen=1000))
        self.baseline_metrics = {}
        
        # Security monitoring patterns
        self.security_patterns = {
            'failed_logins': {'threshold': 5, 'window': 300},  # 5 failures in 5 minutes
            'unusual_traffic': {'threshold': 2.0, 'baseline_multiplier': True},
            'privilege_escalation': {'keywords': ['sudo', 'admin', 'root', 'administrator']},
            'suspicious_processes': {'keywords': ['nc', 'netcat', 'wget', 'curl', 'powershell -enc']}
        }
        
        logger.info("Predictive analytics initialized")
    
    async def analyze_system_performance(self, metrics: Dict[str, float]) -> List[PerformanceInsight]:
        """Analyze system performance and generate insights"""
        try:
            insights = []
            
            for metric_name, current_value in metrics.items():
                # Store metric history
                self.metric_history[metric_name].append({
                    'timestamp': datetime.utcnow(),
                    'value': current_value
                })
                
                # Calculate trend
                trend = await self._calculate_trend(metric_name)
                
                # Generate predictions
                prediction_7d, prediction_30d, confidence = await self._predict_metric_values(
                    metric_name, current_value
                )
                
                # Generate recommendations
                recommendations = await self._generate_performance_recommendations(
                    metric_name, current_value, trend, prediction_7d
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
    
    async def _calculate_trend(self, metric_name: str) -> str:
        """Calculate trend for a metric"""
        try:
            history = list(self.metric_history[metric_name])
            if len(history) < 10:
                return "stable"
            
            # Get recent values
            recent_values = [h['value'] for h in history[-10:]]
            older_values = [h['value'] for h in history[-20:-10]] if len(history) >= 20 else recent_values
            
            recent_avg = np.mean(recent_values)
            older_avg = np.mean(older_values)
            
            change_percent = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
            
            if change_percent > 5:
                return "degrading" if metric_name in ['cpu_usage', 'memory_usage', 'error_rate'] else "improving"
            elif change_percent < -5:
                return "improving" if metric_name in ['cpu_usage', 'memory_usage', 'error_rate'] else "degrading"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Failed to calculate trend for {metric_name}", error=str(e))
            return "stable"
    
    async def _predict_metric_values(self, metric_name: str, current_value: float) -> Tuple[float, float, float]:
        """Predict future metric values"""
        try:
            history = list(self.metric_history[metric_name])
            if len(history) < 20:
                # Not enough data for prediction
                return current_value, current_value, 0.5
            
            # Prepare time series data
            values = [h['value'] for h in history]
            timestamps = [(h['timestamp'] - history[0]['timestamp']).total_seconds() for h in history]
            
            # Simple linear regression for trend
            X = np.array(timestamps).reshape(-1, 1)
            y = np.array(values)
            
            # Use last 50 points for prediction
            if len(X) > 50:
                X = X[-50:]
                y = y[-50:]
            
            # Fit model
            if metric_name not in self.performance_models:
                from sklearn.linear_model import LinearRegression
                self.performance_models[metric_name] = LinearRegression()
            
            model = self.performance_models[metric_name]
            model.fit(X, y)
            
            # Predict future values
            current_time = timestamps[-1]
            future_7d = current_time + (7 * 24 * 3600)  # 7 days in seconds
            future_30d = current_time + (30 * 24 * 3600)  # 30 days in seconds
            
            pred_7d = model.predict([[future_7d]])[0]
            pred_30d = model.predict([[future_30d]])[0]
            
            # Calculate confidence based on R²
            confidence = max(0.1, min(0.9, model.score(X, y)))
            
            return pred_7d, pred_30d, confidence
            
        except Exception as e:
            logger.error(f"Failed to predict values for {metric_name}", error=str(e))
            return current_value, current_value, 0.5
    
    async def _generate_performance_recommendations(self, metric_name: str, current_value: float, 
                                                  trend: str, prediction_7d: float) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        try:
            # CPU usage recommendations
            if metric_name == 'cpu_usage':
                if current_value > 80:
                    recommendations.append("High CPU usage detected - consider scaling resources")
                if trend == "degrading":
                    recommendations.append("CPU usage trending upward - investigate resource-intensive processes")
                if prediction_7d > 90:
                    recommendations.append("CPU usage predicted to reach critical levels - plan capacity upgrade")
            
            # Memory usage recommendations
            elif metric_name == 'memory_usage':
                if current_value > 85:
                    recommendations.append("High memory usage - check for memory leaks")
                if trend == "degrading":
                    recommendations.append("Memory usage increasing - monitor application memory consumption")
                if prediction_7d > 95:
                    recommendations.append("Memory exhaustion predicted - urgent capacity planning needed")
            
            # Response time recommendations
            elif metric_name == 'response_time':
                if current_value > 1000:  # > 1 second
                    recommendations.append("Slow response times detected - optimize database queries and caching")
                if trend == "degrading":
                    recommendations.append("Response times degrading - review recent code changes")
                if prediction_7d > current_value * 1.5:
                    recommendations.append("Response times predicted to worsen significantly")
            
            # Error rate recommendations
            elif metric_name == 'error_rate':
                if current_value > 0.05:  # > 5%
                    recommendations.append("High error rate - investigate application logs")
                if trend == "degrading":
                    recommendations.append("Error rate increasing - check system health and dependencies")
                if prediction_7d > 0.1:
                    recommendations.append("Error rate predicted to exceed 10% - immediate attention required")
            
            # Disk usage recommendations
            elif metric_name == 'disk_usage':
                if current_value > 80:
                    recommendations.append("High disk usage - clean up old files and logs")
                if trend == "degrading":
                    recommendations.append("Disk usage growing - implement log rotation and archival")
                if prediction_7d > 95:
                    recommendations.append("Disk space critical - urgent cleanup or expansion needed")
            
            # Generic recommendations if no specific ones
            if not recommendations:
                if trend == "degrading":
                    recommendations.append(f"Monitor {metric_name} closely as it's showing a degrading trend")
                elif current_value > 80:  # Assuming percentage metrics
                    recommendations.append(f"{metric_name} is at {current_value:.1f}% - consider optimization")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations for {metric_name}", error=str(e))
        
        return recommendations
    
    async def detect_advanced_anomalies(self, metrics: Dict[str, float], 
                                      execution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect advanced anomalies using ML models"""
        try:
            anomalies = []
            
            # Prepare feature vector
            features = self._prepare_anomaly_features(metrics, execution_data)
            
            # Use Isolation Forest for anomaly detection
            if 'system_anomaly' not in self.anomaly_models:
                self.anomaly_models['system_anomaly'] = IsolationForest(
                    contamination=0.1, 
                    random_state=42
                )
                
                # Train with historical data if available
                historical_features = await self._get_historical_features()
                if len(historical_features) > 50:
                    self.anomaly_models['system_anomaly'].fit(historical_features)
            
            model = self.anomaly_models['system_anomaly']
            
            # Detect anomaly
            if hasattr(model, 'decision_function'):
                anomaly_score = model.decision_function([features])[0]
                is_anomaly = model.predict([features])[0] == -1
                
                if is_anomaly:
                    anomalies.append({
                        'type': 'system_anomaly',
                        'severity': 'high' if anomaly_score < -0.5 else 'medium',
                        'description': f'Unusual system behavior detected (score: {anomaly_score:.3f})',
                        'confidence': min(0.9, abs(anomaly_score)),
                        'affected_metrics': list(metrics.keys()),
                        'recommendations': [
                            'Investigate system logs for unusual activity',
                            'Check for recent configuration changes',
                            'Monitor system resources closely'
                        ]
                    })
            
            # Pattern-based anomaly detection
            pattern_anomalies = await self._detect_pattern_anomalies(metrics, execution_data)
            anomalies.extend(pattern_anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error("Failed to detect advanced anomalies", error=str(e))
            return []
    
    def _prepare_anomaly_features(self, metrics: Dict[str, float], 
                                execution_data: Dict[str, Any]) -> List[float]:
        """Prepare feature vector for anomaly detection"""
        features = []
        
        # System metrics
        features.extend([
            metrics.get('cpu_usage', 0) / 100.0,
            metrics.get('memory_usage', 0) / 100.0,
            metrics.get('disk_usage', 0) / 100.0,
            metrics.get('network_io', 0) / 1000.0,  # Normalize
            metrics.get('response_time', 0) / 1000.0,  # Normalize to seconds
            metrics.get('error_rate', 0),
            metrics.get('active_connections', 0) / 100.0  # Normalize
        ])
        
        # Execution metrics
        features.extend([
            execution_data.get('duration', 0) / 3600.0,  # Normalize to hours
            1.0 if execution_data.get('success', True) else 0.0,
            datetime.utcnow().hour / 24.0,  # Time of day
            datetime.utcnow().weekday() / 6.0  # Day of week
        ])
        
        # Ensure fixed feature count
        while len(features) < 15:
            features.append(0.0)
        
        return features[:15]
    
    async def _get_historical_features(self) -> List[List[float]]:
        """Get historical features for model training"""
        try:
            features = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT system_load, memory_usage, network_latency, duration_seconds,
                           success, execution_time
                    FROM execution_logs 
                    WHERE execution_time > datetime('now', '-30 days')
                    AND system_load IS NOT NULL
                    ORDER BY execution_time DESC
                    LIMIT 1000
                """)
                
                for row in cursor.fetchall():
                    feature_vector = [
                        row[0] / 100.0,  # system_load
                        row[1] / 100.0,  # memory_usage
                        row[2] / 1000.0,  # network_latency
                        row[3] / 3600.0,  # duration in hours
                        1.0 if row[4] else 0.0,  # success
                        0.5, 0.5, 0.5, 0.5, 0.5,  # Placeholder features
                        0.5, 0.5, 0.5, 0.5, 0.5   # More placeholders
                    ]
                    features.append(feature_vector)
            
            return features
            
        except Exception as e:
            logger.error("Failed to get historical features", error=str(e))
            return []
    
    async def _detect_pattern_anomalies(self, metrics: Dict[str, float], 
                                      execution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect pattern-based anomalies"""
        anomalies = []
        
        try:
            # Check for unusual metric combinations
            cpu = metrics.get('cpu_usage', 0)
            memory = metrics.get('memory_usage', 0)
            response_time = metrics.get('response_time', 0)
            
            # High CPU but low memory usage (unusual)
            if cpu > 80 and memory < 30:
                anomalies.append({
                    'type': 'resource_imbalance',
                    'severity': 'medium',
                    'description': f'High CPU usage ({cpu:.1f}%) with low memory usage ({memory:.1f}%)',
                    'confidence': 0.7,
                    'recommendations': [
                        'Check for CPU-intensive processes',
                        'Investigate potential CPU-bound operations'
                    ]
                })
            
            # High response time but low resource usage
            if response_time > 1000 and cpu < 50 and memory < 50:
                anomalies.append({
                    'type': 'performance_anomaly',
                    'severity': 'medium',
                    'description': f'High response time ({response_time:.0f}ms) with low resource usage',
                    'confidence': 0.8,
                    'recommendations': [
                        'Check database performance',
                        'Investigate network latency',
                        'Review external service dependencies'
                    ]
                })
            
            # Execution time anomalies
            duration = execution_data.get('duration', 0)
            operation_type = execution_data.get('operation_type', 'unknown')
            
            # Get typical duration for this operation
            typical_duration = await self._get_typical_duration(operation_type)
            if typical_duration > 0 and duration > typical_duration * 3:
                anomalies.append({
                    'type': 'execution_duration_anomaly',
                    'severity': 'medium',
                    'description': f'{operation_type} took {duration:.1f}s (typical: {typical_duration:.1f}s)',
                    'confidence': 0.8,
                    'recommendations': [
                        'Check target system performance',
                        'Review operation parameters',
                        'Investigate network connectivity'
                    ]
                })
            
        except Exception as e:
            logger.error("Failed to detect pattern anomalies", error=str(e))
        
        return anomalies
    
    async def _get_typical_duration(self, operation_type: str) -> float:
        """Get typical duration for an operation type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT AVG(duration_seconds) as avg_duration
                    FROM execution_logs 
                    WHERE operation_type = ? 
                    AND success = 1
                    AND execution_time > datetime('now', '-30 days')
                """, (operation_type,))
                
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0.0
                
        except Exception as e:
            logger.error(f"Failed to get typical duration for {operation_type}", error=str(e))
            return 0.0
    
    async def generate_maintenance_schedule(self, targets: List[Dict[str, Any]]) -> List[MaintenanceRecommendation]:
        """Generate predictive maintenance recommendations"""
        try:
            recommendations = []
            
            for target in targets:
                target_recommendations = await self._analyze_target_maintenance_needs(target)
                recommendations.extend(target_recommendations)
            
            # Sort by priority and date
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(key=lambda x: (priority_order.get(x.priority, 3), x.recommended_date))
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to generate maintenance schedule", error=str(e))
            return []
    
    async def _analyze_target_maintenance_needs(self, target: Dict[str, Any]) -> List[MaintenanceRecommendation]:
        """Analyze maintenance needs for a specific target"""
        recommendations = []
        
        try:
            hostname = target.get('hostname', 'unknown')
            target_type = target.get('type', 'server')
            last_maintenance = target.get('last_maintenance')
            
            # Calculate time since last maintenance
            if last_maintenance:
                last_maintenance_date = datetime.fromisoformat(last_maintenance)
                days_since_maintenance = (datetime.utcnow() - last_maintenance_date).days
            else:
                days_since_maintenance = 365  # Assume no maintenance for a year
            
            # Regular maintenance recommendations
            if days_since_maintenance > 90:  # 3 months
                recommendations.append(MaintenanceRecommendation(
                    target_system=hostname,
                    maintenance_type="routine_maintenance",
                    priority="medium" if days_since_maintenance > 180 else "low",
                    recommended_date=datetime.utcnow() + timedelta(days=7),
                    reason=f"Last maintenance was {days_since_maintenance} days ago",
                    estimated_duration=2.0,
                    risk_if_delayed="Increased risk of system failures and performance degradation",
                    prerequisites=["Schedule maintenance window", "Backup system state", "Notify users"]
                ))
            
            # Security updates
            if target_type in ['server', 'workstation']:
                recommendations.append(MaintenanceRecommendation(
                    target_system=hostname,
                    maintenance_type="security_updates",
                    priority="high",
                    recommended_date=datetime.utcnow() + timedelta(days=3),
                    reason="Regular security update cycle",
                    estimated_duration=1.0,
                    risk_if_delayed="Security vulnerabilities may remain unpatched",
                    prerequisites=["Test updates in staging", "Schedule maintenance window"]
                ))
            
            # Performance optimization
            performance_score = await self._calculate_performance_score(target)
            if performance_score < 0.7:
                recommendations.append(MaintenanceRecommendation(
                    target_system=hostname,
                    maintenance_type="performance_optimization",
                    priority="medium",
                    recommended_date=datetime.utcnow() + timedelta(days=14),
                    reason=f"Performance score is {performance_score:.2f} (below optimal)",
                    estimated_duration=3.0,
                    risk_if_delayed="Continued performance degradation affecting user experience",
                    prerequisites=["Performance analysis", "Resource planning", "Testing environment"]
                ))
            
        except Exception as e:
            logger.error(f"Failed to analyze maintenance needs for {target}", error=str(e))
        
        return recommendations
    
    async def _calculate_performance_score(self, target: Dict[str, Any]) -> float:
        """Calculate performance score for a target"""
        try:
            # This would integrate with monitoring systems
            # For now, return a simulated score based on target age and type
            
            hostname = target.get('hostname', '')
            target_type = target.get('type', 'server')
            
            # Base score
            base_score = 0.8
            
            # Adjust based on target type
            type_adjustments = {
                'server': 0.0,
                'workstation': -0.1,
                'network_device': 0.1,
                'storage': -0.05
            }
            
            score = base_score + type_adjustments.get(target_type, 0.0)
            
            # Add some randomness to simulate real performance variations
            import random
            score += random.uniform(-0.2, 0.1)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Failed to calculate performance score for {target}", error=str(e))
            return 0.5
    
    async def monitor_security_events(self, log_entries: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Monitor for security events and generate alerts"""
        try:
            alerts = []
            
            for entry in log_entries:
                security_alerts = await self._analyze_log_entry_security(entry)
                alerts.extend(security_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error("Failed to monitor security events", error=str(e))
            return []
    
    async def _analyze_log_entry_security(self, log_entry: Dict[str, Any]) -> List[SecurityAlert]:
        """Analyze a log entry for security indicators"""
        alerts = []
        
        try:
            message = log_entry.get('message', '').lower()
            source_ip = log_entry.get('source_ip', '')
            timestamp = log_entry.get('timestamp', datetime.utcnow())
            
            # Failed login detection
            if any(keyword in message for keyword in ['failed login', 'authentication failed', 'login failed']):
                alerts.append(SecurityAlert(
                    alert_id=f"security_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="failed_authentication",
                    severity="medium",
                    target_system=log_entry.get('hostname', 'unknown'),
                    description=f"Failed authentication attempt from {source_ip}",
                    indicators=[message, source_ip],
                    detection_time=timestamp,
                    confidence=0.8,
                    recommended_actions=[
                        "Monitor for repeated attempts from same IP",
                        "Consider IP blocking if pattern continues",
                        "Review user account security"
                    ]
                ))
            
            # Privilege escalation detection
            if any(keyword in message for keyword in self.security_patterns['privilege_escalation']['keywords']):
                alerts.append(SecurityAlert(
                    alert_id=f"security_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="privilege_escalation",
                    severity="high",
                    target_system=log_entry.get('hostname', 'unknown'),
                    description="Potential privilege escalation attempt detected",
                    indicators=[message],
                    detection_time=timestamp,
                    confidence=0.7,
                    recommended_actions=[
                        "Investigate user activity immediately",
                        "Review system access logs",
                        "Check for unauthorized system changes"
                    ]
                ))
            
            # Suspicious process detection
            if any(keyword in message for keyword in self.security_patterns['suspicious_processes']['keywords']):
                alerts.append(SecurityAlert(
                    alert_id=f"security_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="suspicious_process",
                    severity="high",
                    target_system=log_entry.get('hostname', 'unknown'),
                    description="Suspicious process activity detected",
                    indicators=[message],
                    detection_time=timestamp,
                    confidence=0.8,
                    recommended_actions=[
                        "Investigate process immediately",
                        "Check for malware indicators",
                        "Review system integrity"
                    ]
                ))
            
        except Exception as e:
            logger.error(f"Failed to analyze log entry for security: {e}")
        
        return alerts
    
    async def get_predictive_insights(self) -> Dict[str, Any]:
        """Get comprehensive predictive insights"""
        try:
            insights = {
                'performance_trends': {},
                'anomaly_summary': {},
                'maintenance_forecast': {},
                'security_status': {},
                'recommendations': []
            }
            
            # Get recent metrics for analysis
            recent_metrics = await self._get_recent_metrics()
            if recent_metrics:
                performance_insights = await self.analyze_system_performance(recent_metrics)
                insights['performance_trends'] = {
                    'insights': [insight.to_dict() for insight in performance_insights],
                    'overall_health': self._calculate_overall_health(performance_insights)
                }
            
            # Anomaly summary
            insights['anomaly_summary'] = {
                'active_anomalies': len(await self._get_active_anomalies()),
                'anomaly_types': await self._get_anomaly_types_summary(),
                'trend': 'stable'  # This would be calculated from historical data
            }
            
            # Maintenance forecast
            insights['maintenance_forecast'] = {
                'upcoming_maintenance': len(await self._get_upcoming_maintenance()),
                'overdue_maintenance': len(await self._get_overdue_maintenance()),
                'next_critical_date': await self._get_next_critical_maintenance_date()
            }
            
            # Security status
            insights['security_status'] = {
                'active_alerts': len(await self._get_active_security_alerts()),
                'risk_level': await self._calculate_security_risk_level(),
                'recent_incidents': len(await self._get_recent_security_incidents())
            }
            
            # Generate top recommendations
            insights['recommendations'] = await self._generate_top_recommendations(insights)
            
            return insights
            
        except Exception as e:
            logger.error("Failed to get predictive insights", error=str(e))
            return {
                'performance_trends': {},
                'anomaly_summary': {},
                'maintenance_forecast': {},
                'security_status': {},
                'recommendations': []
            }
    
    async def _get_recent_metrics(self) -> Dict[str, float]:
        """Get recent system metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT AVG(cpu_usage), AVG(memory_usage), AVG(response_time), AVG(error_rate)
                    FROM system_metrics 
                    WHERE timestamp > datetime('now', '-1 hour')
                """)
                
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return {
                        'cpu_usage': row[0],
                        'memory_usage': row[1],
                        'response_time': row[2],
                        'error_rate': row[3]
                    }
            
            return {}
            
        except Exception as e:
            logger.error("Failed to get recent metrics", error=str(e))
            return {}
    
    def _calculate_overall_health(self, performance_insights: List[PerformanceInsight]) -> str:
        """Calculate overall system health"""
        if not performance_insights:
            return "unknown"
        
        degrading_count = sum(1 for insight in performance_insights if insight.trend == "degrading")
        total_count = len(performance_insights)
        
        if degrading_count / total_count > 0.5:
            return "degraded"
        elif degrading_count / total_count > 0.3:
            return "fair"
        else:
            return "good"
    
    async def _get_active_anomalies(self) -> List[Dict[str, Any]]:
        """Get active anomalies"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM anomalies 
                    WHERE resolved = FALSE 
                    AND detection_time > datetime('now', '-24 hours')
                """)
                return cursor.fetchone()[0] or 0
        except:
            return 0
    
    async def _get_anomaly_types_summary(self) -> Dict[str, int]:
        """Get summary of anomaly types"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT anomaly_type, COUNT(*) 
                    FROM anomalies 
                    WHERE resolved = FALSE 
                    GROUP BY anomaly_type
                """)
                return dict(cursor.fetchall())
        except:
            return {}
    
    async def _get_upcoming_maintenance(self) -> int:
        """Get count of upcoming maintenance tasks"""
        # This would integrate with maintenance scheduling system
        return 3  # Placeholder
    
    async def _get_overdue_maintenance(self) -> int:
        """Get count of overdue maintenance tasks"""
        # This would integrate with maintenance scheduling system
        return 1  # Placeholder
    
    async def _get_next_critical_maintenance_date(self) -> Optional[str]:
        """Get next critical maintenance date"""
        # This would integrate with maintenance scheduling system
        next_date = datetime.utcnow() + timedelta(days=5)
        return next_date.isoformat()
    
    async def _get_active_security_alerts(self) -> int:
        """Get count of active security alerts"""
        # This would integrate with security monitoring system
        return 2  # Placeholder
    
    async def _calculate_security_risk_level(self) -> str:
        """Calculate current security risk level"""
        # This would analyze security metrics
        return "medium"  # Placeholder
    
    async def _get_recent_security_incidents(self) -> int:
        """Get count of recent security incidents"""
        # This would integrate with security incident tracking
        return 0  # Placeholder
    
    async def _generate_top_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate top recommendations based on insights"""
        recommendations = []
        
        # Performance recommendations
        if insights['performance_trends'].get('overall_health') == 'degraded':
            recommendations.append("System performance is degraded - investigate resource usage and optimize")
        
        # Anomaly recommendations
        active_anomalies = insights['anomaly_summary'].get('active_anomalies', 0)
        if active_anomalies > 5:
            recommendations.append(f"{active_anomalies} active anomalies detected - review and address high-priority issues")
        
        # Maintenance recommendations
        overdue_maintenance = insights['maintenance_forecast'].get('overdue_maintenance', 0)
        if overdue_maintenance > 0:
            recommendations.append(f"{overdue_maintenance} overdue maintenance tasks - schedule immediate attention")
        
        # Security recommendations
        security_risk = insights['security_status'].get('risk_level', 'low')
        if security_risk in ['high', 'critical']:
            recommendations.append(f"Security risk level is {security_risk} - review security alerts and implement mitigations")
        
        # Default recommendations if none specific
        if not recommendations:
            recommendations.extend([
                "System operating normally - continue regular monitoring",
                "Consider proactive maintenance scheduling",
                "Review performance trends for optimization opportunities"
            ])
        
        return recommendations[:5]  # Return top 5 recommendations

# Global predictive analytics instance
predictive_analytics = PredictiveAnalytics()
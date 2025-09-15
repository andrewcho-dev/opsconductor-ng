"""
OpsConductor AI Learning Engine
Advanced pattern recognition, predictive analytics, and self-improvement capabilities
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
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import structlog

logger = structlog.get_logger()

@dataclass
class ExecutionPattern:
    """Represents a pattern in job execution"""
    user_id: str
    operation_type: str
    target_pattern: str
    time_pattern: str  # hour of day, day of week
    success_rate: float
    avg_duration: float
    frequency: int
    last_seen: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['last_seen'] = self.last_seen.isoformat()
        return result

@dataclass
class PredictionResult:
    """Result of a prediction analysis"""
    prediction_type: str
    confidence: float
    predicted_outcome: str
    risk_factors: List[str]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class AnomalyAlert:
    """Anomaly detection alert"""
    alert_id: str
    anomaly_type: str
    severity: str  # low, medium, high, critical
    description: str
    affected_systems: List[str]
    detection_time: datetime
    confidence: float
    suggested_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['detection_time'] = self.detection_time.isoformat()
        return result

class LearningEngine:
    """Advanced learning engine for pattern recognition and predictive analytics"""
    
    def __init__(self, db_path: str = "/app/data/learning.db"):
        self.db_path = db_path
        self.models = {}
        self.scalers = {}
        self.pattern_cache = {}
        self.anomaly_detectors = {}
        self.execution_history = deque(maxlen=10000)  # Keep last 10k executions
        self.user_patterns = defaultdict(list)
        self.system_metrics = deque(maxlen=1000)  # Keep last 1k metric snapshots
        
        # Initialize database
        self._init_database()
        
        # Load existing models
        self._load_models()
        
        logger.info("Learning engine initialized", db_path=db_path)
    
    def _init_database(self):
        """Initialize SQLite database for learning data"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    target_info TEXT NOT NULL,
                    execution_time TIMESTAMP NOT NULL,
                    duration_seconds REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    system_load REAL,
                    memory_usage REAL,
                    network_latency REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS user_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_type TEXT NOT NULL,
                    target_system TEXT NOT NULL,
                    predicted_outcome TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    actual_outcome TEXT,
                    prediction_time TIMESTAMP NOT NULL,
                    validation_time TIMESTAMP,
                    accuracy REAL
                );
                
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_systems TEXT NOT NULL,
                    detection_time TIMESTAMP NOT NULL,
                    confidence REAL NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_time TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_io REAL,
                    active_connections INTEGER,
                    error_rate REAL,
                    response_time REAL
                );
                
                CREATE INDEX IF NOT EXISTS idx_execution_user_time ON execution_logs(user_id, execution_time);
                CREATE INDEX IF NOT EXISTS idx_predictions_time ON predictions(prediction_time);
                CREATE INDEX IF NOT EXISTS idx_anomalies_time ON anomalies(detection_time);
                CREATE INDEX IF NOT EXISTS idx_metrics_time ON system_metrics(timestamp);
            """)
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        models_dir = "/app/data/models"
        os.makedirs(models_dir, exist_ok=True)
        
        model_files = {
            'failure_predictor': 'failure_predictor.pkl',
            'anomaly_detector': 'anomaly_detector.pkl',
            'performance_optimizer': 'performance_optimizer.pkl',
            'user_behavior': 'user_behavior.pkl'
        }
        
        for model_name, filename in model_files.items():
            filepath = os.path.join(models_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                    logger.info(f"Loaded model: {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to load model {model_name}: {e}")
    
    def _save_model(self, model_name: str, model: Any):
        """Save a trained model to disk"""
        models_dir = "/app/data/models"
        os.makedirs(models_dir, exist_ok=True)
        
        filepath = os.path.join(models_dir, f"{model_name}.pkl")
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Saved model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to save model {model_name}: {e}")
    
    async def record_execution(self, user_id: str, operation_type: str, 
                             target_info: Dict[str, Any], duration: float, 
                             success: bool, error_message: Optional[str] = None,
                             system_metrics: Optional[Dict[str, float]] = None):
        """Record a job execution for learning"""
        try:
            execution_data = {
                'user_id': user_id,
                'operation_type': operation_type,
                'target_info': json.dumps(target_info),
                'execution_time': datetime.utcnow(),
                'duration_seconds': duration,
                'success': success,
                'error_message': error_message,
                'system_load': system_metrics.get('cpu_usage', 0) if system_metrics else 0,
                'memory_usage': system_metrics.get('memory_usage', 0) if system_metrics else 0,
                'network_latency': system_metrics.get('network_latency', 0) if system_metrics else 0
            }
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO execution_logs 
                    (user_id, operation_type, target_info, execution_time, duration_seconds, 
                     success, error_message, system_load, memory_usage, network_latency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution_data['user_id'],
                    execution_data['operation_type'],
                    execution_data['target_info'],
                    execution_data['execution_time'],
                    execution_data['duration_seconds'],
                    execution_data['success'],
                    execution_data['error_message'],
                    execution_data['system_load'],
                    execution_data['memory_usage'],
                    execution_data['network_latency']
                ))
            
            # Add to in-memory cache
            self.execution_history.append(execution_data)
            
            # Update user patterns
            await self._update_user_patterns(user_id, execution_data)
            
            # Check for anomalies
            await self._detect_execution_anomalies(execution_data)
            
            logger.info("Recorded execution for learning", 
                       user_id=user_id, 
                       operation=operation_type, 
                       success=success)
            
        except Exception as e:
            logger.error("Failed to record execution", error=str(e))
    
    async def _update_user_patterns(self, user_id: str, execution_data: Dict[str, Any]):
        """Update user behavior patterns"""
        try:
            # Extract pattern features
            hour = execution_data['execution_time'].hour
            day_of_week = execution_data['execution_time'].weekday()
            operation = execution_data['operation_type']
            
            pattern_key = f"{user_id}_{operation}"
            
            if pattern_key not in self.user_patterns:
                self.user_patterns[pattern_key] = {
                    'user_id': user_id,
                    'operation_type': operation,
                    'time_patterns': defaultdict(int),
                    'success_count': 0,
                    'total_count': 0,
                    'avg_duration': 0,
                    'durations': deque(maxlen=100)
                }
            
            pattern = self.user_patterns[pattern_key]
            pattern['time_patterns'][f"{day_of_week}_{hour}"] += 1
            pattern['total_count'] += 1
            pattern['durations'].append(execution_data['duration_seconds'])
            
            if execution_data['success']:
                pattern['success_count'] += 1
            
            # Update average duration
            pattern['avg_duration'] = np.mean(pattern['durations'])
            
            # Store in database if significant pattern
            if pattern['total_count'] >= 5:
                await self._store_user_pattern(pattern)
                
        except Exception as e:
            logger.error("Failed to update user patterns", error=str(e))
    
    async def _store_user_pattern(self, pattern: Dict[str, Any]):
        """Store user pattern in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_patterns 
                    (user_id, pattern_type, pattern_data, confidence)
                    VALUES (?, ?, ?, ?)
                """, (
                    pattern['user_id'],
                    pattern['operation_type'],
                    json.dumps(pattern),
                    pattern['success_count'] / pattern['total_count']
                ))
        except Exception as e:
            logger.error("Failed to store user pattern", error=str(e))
    
    async def _detect_execution_anomalies(self, execution_data: Dict[str, Any]):
        """Detect anomalies in execution patterns"""
        try:
            # Check for unusual duration
            operation = execution_data['operation_type']
            duration = execution_data['duration_seconds']
            
            # Get historical durations for this operation
            recent_durations = []
            for exec_data in list(self.execution_history)[-100:]:
                if exec_data['operation_type'] == operation and exec_data['success']:
                    recent_durations.append(exec_data['duration_seconds'])
            
            if len(recent_durations) >= 10:
                mean_duration = np.mean(recent_durations)
                std_duration = np.std(recent_durations)
                
                # Check if current duration is anomalous (> 3 standard deviations)
                if abs(duration - mean_duration) > 3 * std_duration:
                    await self._create_anomaly_alert(
                        anomaly_type="execution_duration",
                        severity="medium" if duration > mean_duration else "low",
                        description=f"Unusual execution duration for {operation}: {duration:.2f}s (avg: {mean_duration:.2f}s)",
                        affected_systems=[execution_data.get('target_info', {}).get('hostname', 'unknown')],
                        confidence=0.8
                    )
            
            # Check for repeated failures
            if not execution_data['success']:
                recent_failures = sum(1 for exec_data in list(self.execution_history)[-10:] 
                                    if exec_data['operation_type'] == operation and not exec_data['success'])
                
                if recent_failures >= 3:
                    await self._create_anomaly_alert(
                        anomaly_type="repeated_failures",
                        severity="high",
                        description=f"Multiple recent failures for {operation}: {recent_failures} in last 10 executions",
                        affected_systems=[execution_data.get('target_info', {}).get('hostname', 'unknown')],
                        confidence=0.9
                    )
                    
        except Exception as e:
            logger.error("Failed to detect execution anomalies", error=str(e))
    
    async def _create_anomaly_alert(self, anomaly_type: str, severity: str, 
                                  description: str, affected_systems: List[str], 
                                  confidence: float):
        """Create an anomaly alert"""
        try:
            alert = AnomalyAlert(
                alert_id=f"anomaly_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                anomaly_type=anomaly_type,
                severity=severity,
                description=description,
                affected_systems=affected_systems,
                detection_time=datetime.utcnow(),
                confidence=confidence,
                suggested_actions=self._get_suggested_actions(anomaly_type, severity)
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO anomalies 
                    (anomaly_type, severity, description, affected_systems, 
                     detection_time, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    alert.anomaly_type,
                    alert.severity,
                    alert.description,
                    json.dumps(alert.affected_systems),
                    alert.detection_time,
                    alert.confidence
                ))
            
            logger.warning("Anomaly detected", 
                          type=anomaly_type, 
                          severity=severity, 
                          confidence=confidence)
            
            return alert
            
        except Exception as e:
            logger.error("Failed to create anomaly alert", error=str(e))
            return None
    
    def _get_suggested_actions(self, anomaly_type: str, severity: str) -> List[str]:
        """Get suggested actions for an anomaly"""
        actions = {
            "execution_duration": [
                "Check system resource usage",
                "Review target system performance",
                "Consider optimizing the operation",
                "Monitor for network latency issues"
            ],
            "repeated_failures": [
                "Check target system connectivity",
                "Review operation parameters",
                "Verify credentials and permissions",
                "Check system logs for errors",
                "Consider temporary system maintenance"
            ],
            "resource_usage": [
                "Monitor CPU and memory usage",
                "Check for resource-intensive processes",
                "Consider scaling resources",
                "Review system capacity planning"
            ]
        }
        
        return actions.get(anomaly_type, ["Investigate the issue", "Monitor system behavior"])
    
    async def predict_failure_risk(self, operation_type: str, target_info: Dict[str, Any], 
                                 user_id: str) -> PredictionResult:
        """Predict the risk of failure for a planned operation"""
        try:
            # Gather features for prediction
            features = await self._extract_prediction_features(operation_type, target_info, user_id)
            
            # Use trained model if available
            if 'failure_predictor' in self.models:
                model = self.models['failure_predictor']
                scaler = self.scalers.get('failure_predictor')
                
                if scaler:
                    features_scaled = scaler.transform([features])
                    prediction = model.predict_proba(features_scaled)[0]
                    failure_risk = prediction[1] if len(prediction) > 1 else prediction[0]
                else:
                    failure_risk = 0.5  # Default uncertainty
            else:
                # Use heuristic-based prediction
                failure_risk = await self._heuristic_failure_prediction(operation_type, target_info, user_id)
            
            # Determine risk level and recommendations
            if failure_risk > 0.8:
                risk_level = "high"
                recommendations = [
                    "Consider postponing this operation",
                    "Check target system health first",
                    "Ensure backup procedures are in place",
                    "Have rollback plan ready"
                ]
            elif failure_risk > 0.6:
                risk_level = "medium"
                recommendations = [
                    "Monitor the operation closely",
                    "Verify system prerequisites",
                    "Have support team on standby"
                ]
            elif failure_risk > 0.3:
                risk_level = "low"
                recommendations = [
                    "Operation should proceed normally",
                    "Standard monitoring recommended"
                ]
            else:
                risk_level = "very_low"
                recommendations = [
                    "Operation has high success probability",
                    "Proceed with confidence"
                ]
            
            # Identify risk factors
            risk_factors = await self._identify_risk_factors(operation_type, target_info, user_id, features)
            
            result = PredictionResult(
                prediction_type="failure_risk",
                confidence=min(0.9, max(0.6, 1.0 - abs(failure_risk - 0.5) * 2)),
                predicted_outcome=risk_level,
                risk_factors=risk_factors,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
            # Store prediction for later validation
            await self._store_prediction(result, operation_type, target_info)
            
            return result
            
        except Exception as e:
            logger.error("Failed to predict failure risk", error=str(e))
            return PredictionResult(
                prediction_type="failure_risk",
                confidence=0.5,
                predicted_outcome="unknown",
                risk_factors=["Prediction system error"],
                recommendations=["Proceed with caution", "Monitor operation closely"],
                timestamp=datetime.utcnow()
            )
    
    async def _extract_prediction_features(self, operation_type: str, target_info: Dict[str, Any], 
                                         user_id: str) -> List[float]:
        """Extract features for failure prediction"""
        features = []
        
        try:
            # Time-based features
            now = datetime.utcnow()
            features.extend([
                now.hour / 24.0,  # Hour of day (normalized)
                now.weekday() / 6.0,  # Day of week (normalized)
                (now.day - 1) / 30.0  # Day of month (normalized)
            ])
            
            # Historical success rate for this operation type
            success_rate = await self._get_operation_success_rate(operation_type)
            features.append(success_rate)
            
            # User experience with this operation
            user_success_rate = await self._get_user_success_rate(user_id, operation_type)
            features.append(user_success_rate)
            
            # Target system health indicators (if available)
            target_health = await self._get_target_health_score(target_info)
            features.append(target_health)
            
            # Recent system load
            recent_load = await self._get_recent_system_load()
            features.append(recent_load)
            
            # Operation complexity score
            complexity = self._calculate_operation_complexity(operation_type, target_info)
            features.append(complexity)
            
            # Recent failure rate
            recent_failure_rate = await self._get_recent_failure_rate(operation_type)
            features.append(recent_failure_rate)
            
            # Ensure we have exactly the expected number of features
            while len(features) < 10:
                features.append(0.5)  # Default neutral value
            
            return features[:10]  # Limit to 10 features
            
        except Exception as e:
            logger.error("Failed to extract prediction features", error=str(e))
            return [0.5] * 10  # Return neutral features on error
    
    async def _get_operation_success_rate(self, operation_type: str) -> float:
        """Get historical success rate for an operation type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT AVG(CAST(success AS FLOAT)) as success_rate
                    FROM execution_logs 
                    WHERE operation_type = ? 
                    AND execution_time > datetime('now', '-30 days')
                """, (operation_type,))
                
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0.5
                
        except Exception as e:
            logger.error("Failed to get operation success rate", error=str(e))
            return 0.5
    
    async def _get_user_success_rate(self, user_id: str, operation_type: str) -> float:
        """Get user's success rate with specific operation type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT AVG(CAST(success AS FLOAT)) as success_rate
                    FROM execution_logs 
                    WHERE user_id = ? AND operation_type = ?
                    AND execution_time > datetime('now', '-30 days')
                """, (user_id, operation_type))
                
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0.5
                
        except Exception as e:
            logger.error("Failed to get user success rate", error=str(e))
            return 0.5
    
    async def _get_target_health_score(self, target_info: Dict[str, Any]) -> float:
        """Get target system health score"""
        # This would integrate with monitoring systems
        # For now, return a default score
        return 0.8
    
    async def _get_recent_system_load(self) -> float:
        """Get recent system load average"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT AVG(cpu_usage) as avg_load
                    FROM system_metrics 
                    WHERE timestamp > datetime('now', '-1 hour')
                """)
                
                result = cursor.fetchone()
                return (result[0] / 100.0) if result[0] is not None else 0.5
                
        except Exception as e:
            logger.error("Failed to get recent system load", error=str(e))
            return 0.5
    
    def _calculate_operation_complexity(self, operation_type: str, target_info: Dict[str, Any]) -> float:
        """Calculate operation complexity score"""
        complexity_scores = {
            'restart': 0.3,
            'update': 0.7,
            'install': 0.8,
            'configure': 0.6,
            'backup': 0.4,
            'monitor': 0.2,
            'script_execution': 0.5
        }
        
        base_complexity = complexity_scores.get(operation_type, 0.5)
        
        # Adjust based on target count
        target_count = len(target_info.get('targets', []))
        if target_count > 10:
            base_complexity += 0.2
        elif target_count > 5:
            base_complexity += 0.1
        
        return min(1.0, base_complexity)
    
    async def _get_recent_failure_rate(self, operation_type: str) -> float:
        """Get recent failure rate for operation type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 1.0 - AVG(CAST(success AS FLOAT)) as failure_rate
                    FROM execution_logs 
                    WHERE operation_type = ? 
                    AND execution_time > datetime('now', '-7 days')
                """, (operation_type,))
                
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0.1
                
        except Exception as e:
            logger.error("Failed to get recent failure rate", error=str(e))
            return 0.1
    
    async def _heuristic_failure_prediction(self, operation_type: str, 
                                          target_info: Dict[str, Any], user_id: str) -> float:
        """Heuristic-based failure prediction when ML model is not available"""
        risk_score = 0.0
        
        # Base risk by operation type
        operation_risks = {
            'restart': 0.1,
            'update': 0.3,
            'install': 0.4,
            'configure': 0.2,
            'backup': 0.1,
            'monitor': 0.05,
            'script_execution': 0.25
        }
        
        risk_score += operation_risks.get(operation_type, 0.2)
        
        # Adjust for target count
        target_count = len(target_info.get('targets', []))
        if target_count > 20:
            risk_score += 0.2
        elif target_count > 10:
            risk_score += 0.1
        
        # Adjust for time of day (higher risk during business hours)
        hour = datetime.utcnow().hour
        if 9 <= hour <= 17:
            risk_score += 0.1
        
        # Recent failure history
        recent_failure_rate = await self._get_recent_failure_rate(operation_type)
        risk_score += recent_failure_rate * 0.5
        
        return min(1.0, risk_score)
    
    async def _identify_risk_factors(self, operation_type: str, target_info: Dict[str, Any], 
                                   user_id: str, features: List[float]) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        # Check recent failure rate
        recent_failure_rate = await self._get_recent_failure_rate(operation_type)
        if recent_failure_rate > 0.2:
            risk_factors.append(f"High recent failure rate for {operation_type}: {recent_failure_rate:.1%}")
        
        # Check target count
        target_count = len(target_info.get('targets', []))
        if target_count > 20:
            risk_factors.append(f"Large number of targets: {target_count}")
        
        # Check time of day
        hour = datetime.utcnow().hour
        if 9 <= hour <= 17:
            risk_factors.append("Operation during business hours")
        
        # Check user experience
        user_success_rate = await self._get_user_success_rate(user_id, operation_type)
        if user_success_rate < 0.8:
            risk_factors.append(f"User has lower success rate with {operation_type}: {user_success_rate:.1%}")
        
        # Check system load
        if features[6] > 0.8:  # Recent system load feature
            risk_factors.append("High system load detected")
        
        return risk_factors
    
    async def _store_prediction(self, prediction: PredictionResult, operation_type: str, 
                              target_info: Dict[str, Any]):
        """Store prediction for later validation"""
        try:
            target_system = target_info.get('hostname', 'unknown')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO predictions 
                    (prediction_type, target_system, predicted_outcome, confidence, prediction_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    prediction.prediction_type,
                    target_system,
                    prediction.predicted_outcome,
                    prediction.confidence,
                    prediction.timestamp
                ))
                
        except Exception as e:
            logger.error("Failed to store prediction", error=str(e))
    
    async def get_user_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized recommendations for a user"""
        try:
            recommendations = []
            
            # Analyze user patterns
            user_patterns = await self._get_user_patterns(user_id)
            
            for pattern in user_patterns:
                if pattern['success_rate'] < 0.8:
                    recommendations.append({
                        'type': 'improvement',
                        'priority': 'medium',
                        'title': f"Improve success rate for {pattern['operation_type']}",
                        'description': f"Your success rate is {pattern['success_rate']:.1%}. Consider reviewing the process.",
                        'suggested_actions': [
                            "Review operation parameters",
                            "Check target system requirements",
                            "Consider additional training"
                        ]
                    })
                
                # Check for timing patterns
                if pattern.get('preferred_times'):
                    recommendations.append({
                        'type': 'optimization',
                        'priority': 'low',
                        'title': f"Optimal timing for {pattern['operation_type']}",
                        'description': f"You typically have better success rates at {pattern['preferred_times']}",
                        'suggested_actions': [
                            f"Schedule {pattern['operation_type']} operations during {pattern['preferred_times']}"
                        ]
                    })
            
            # Check for unused capabilities
            available_operations = ['restart', 'update', 'install', 'configure', 'backup', 'monitor']
            used_operations = [p['operation_type'] for p in user_patterns]
            unused_operations = set(available_operations) - set(used_operations)
            
            if unused_operations:
                recommendations.append({
                    'type': 'discovery',
                    'priority': 'low',
                    'title': "Explore new automation capabilities",
                    'description': f"You haven't used: {', '.join(unused_operations)}",
                    'suggested_actions': [
                        "Explore automation documentation",
                        "Try creating simple automations with new operation types"
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to get user recommendations", error=str(e))
            return []
    
    async def _get_user_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user behavior patterns from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT pattern_type, pattern_data, confidence
                    FROM user_patterns 
                    WHERE user_id = ?
                    ORDER BY last_updated DESC
                """, (user_id,))
                
                patterns = []
                for row in cursor.fetchall():
                    pattern_data = json.loads(row[1])
                    pattern_data['success_rate'] = row[2]
                    patterns.append(pattern_data)
                
                return patterns
                
        except Exception as e:
            logger.error("Failed to get user patterns", error=str(e))
            return []
    
    async def get_system_health_insights(self) -> Dict[str, Any]:
        """Get system health insights and predictions"""
        try:
            insights = {
                'overall_health': 'good',
                'risk_level': 'low',
                'active_anomalies': [],
                'predictions': [],
                'recommendations': [],
                'metrics_summary': {}
            }
            
            # Get recent anomalies
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT anomaly_type, severity, description, confidence, detection_time
                    FROM anomalies 
                    WHERE resolved = FALSE 
                    AND detection_time > datetime('now', '-24 hours')
                    ORDER BY detection_time DESC
                """)
                
                for row in cursor.fetchall():
                    insights['active_anomalies'].append({
                        'type': row[0],
                        'severity': row[1],
                        'description': row[2],
                        'confidence': row[3],
                        'detection_time': row[4]
                    })
            
            # Calculate overall risk level
            if insights['active_anomalies']:
                high_severity_count = sum(1 for a in insights['active_anomalies'] if a['severity'] in ['high', 'critical'])
                if high_severity_count > 0:
                    insights['risk_level'] = 'high'
                    insights['overall_health'] = 'degraded'
                elif len(insights['active_anomalies']) > 3:
                    insights['risk_level'] = 'medium'
                    insights['overall_health'] = 'fair'
            
            # Get system metrics summary
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        AVG(cpu_usage) as avg_cpu,
                        AVG(memory_usage) as avg_memory,
                        AVG(response_time) as avg_response_time,
                        AVG(error_rate) as avg_error_rate
                    FROM system_metrics 
                    WHERE timestamp > datetime('now', '-1 hour')
                """)
                
                row = cursor.fetchone()
                if row and row[0] is not None:
                    insights['metrics_summary'] = {
                        'cpu_usage': round(row[0], 2),
                        'memory_usage': round(row[1], 2),
                        'response_time': round(row[2], 2),
                        'error_rate': round(row[3], 4)
                    }
            
            # Generate recommendations
            if insights['risk_level'] == 'high':
                insights['recommendations'].extend([
                    "Investigate high-severity anomalies immediately",
                    "Consider scaling resources if needed",
                    "Review recent system changes"
                ])
            elif insights['risk_level'] == 'medium':
                insights['recommendations'].extend([
                    "Monitor system closely",
                    "Address anomalies when possible",
                    "Review system performance trends"
                ])
            else:
                insights['recommendations'].extend([
                    "System operating normally",
                    "Continue regular monitoring",
                    "Consider proactive maintenance"
                ])
            
            return insights
            
        except Exception as e:
            logger.error("Failed to get system health insights", error=str(e))
            return {
                'overall_health': 'unknown',
                'risk_level': 'unknown',
                'active_anomalies': [],
                'predictions': [],
                'recommendations': ["System health analysis unavailable"],
                'metrics_summary': {}
            }
    
    async def train_models(self):
        """Train or retrain ML models with accumulated data"""
        try:
            logger.info("Starting model training...")
            
            # Train failure prediction model
            await self._train_failure_predictor()
            
            # Train anomaly detection model
            await self._train_anomaly_detector()
            
            # Train performance optimization model
            await self._train_performance_optimizer()
            
            logger.info("Model training completed")
            
        except Exception as e:
            logger.error("Failed to train models", error=str(e))
    
    async def _train_failure_predictor(self):
        """Train the failure prediction model"""
        try:
            # Get training data
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        operation_type,
                        duration_seconds,
                        system_load,
                        memory_usage,
                        network_latency,
                        success,
                        strftime('%H', execution_time) as hour,
                        strftime('%w', execution_time) as day_of_week
                    FROM execution_logs 
                    WHERE execution_time > datetime('now', '-90 days')
                """, conn)
            
            if len(df) < 100:
                logger.warning("Insufficient data for failure predictor training")
                return
            
            # Prepare features
            features = []
            labels = []
            
            for _, row in df.iterrows():
                feature_vector = [
                    int(row['hour']) / 24.0,
                    int(row['day_of_week']) / 6.0,
                    row['duration_seconds'] / 3600.0,  # Normalize to hours
                    row['system_load'] / 100.0,
                    row['memory_usage'] / 100.0,
                    row['network_latency'] / 1000.0,  # Normalize to seconds
                    hash(row['operation_type']) % 100 / 100.0,  # Simple operation encoding
                    0.5, 0.5, 0.5  # Placeholder features
                ]
                
                features.append(feature_vector)
                labels.append(1 if row['success'] else 0)
            
            X = np.array(features)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Failure predictor trained with accuracy: {accuracy:.3f}")
            
            # Save model and scaler
            self.models['failure_predictor'] = model
            self.scalers['failure_predictor'] = scaler
            self._save_model('failure_predictor', model)
            self._save_model('failure_predictor_scaler', scaler)
            
        except Exception as e:
            logger.error("Failed to train failure predictor", error=str(e))
    
    async def _train_anomaly_detector(self):
        """Train the anomaly detection model"""
        try:
            # Get system metrics data
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        cpu_usage,
                        memory_usage,
                        disk_usage,
                        network_io,
                        active_connections,
                        error_rate,
                        response_time
                    FROM system_metrics 
                    WHERE timestamp > datetime('now', '-30 days')
                    AND cpu_usage IS NOT NULL
                """, conn)
            
            if len(df) < 50:
                logger.warning("Insufficient data for anomaly detector training")
                return
            
            # Prepare features
            features = df.fillna(0).values
            
            # Train Isolation Forest
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(features)
            
            # Save model
            self.models['anomaly_detector'] = model
            self._save_model('anomaly_detector', model)
            
            logger.info("Anomaly detector trained successfully")
            
        except Exception as e:
            logger.error("Failed to train anomaly detector", error=str(e))
    
    async def _train_performance_optimizer(self):
        """Train the performance optimization model"""
        try:
            # This would analyze execution patterns and suggest optimizations
            # For now, we'll create a simple heuristic-based optimizer
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        operation_type,
                        AVG(duration_seconds) as avg_duration,
                        AVG(CAST(success AS FLOAT)) as success_rate,
                        COUNT(*) as execution_count
                    FROM execution_logs 
                    WHERE execution_time > datetime('now', '-30 days')
                    GROUP BY operation_type
                    HAVING COUNT(*) >= 10
                """, conn)
            
            if len(df) == 0:
                logger.warning("Insufficient data for performance optimizer training")
                return
            
            # Create performance insights
            performance_insights = {}
            for _, row in df.iterrows():
                operation = row['operation_type']
                performance_insights[operation] = {
                    'avg_duration': row['avg_duration'],
                    'success_rate': row['success_rate'],
                    'execution_count': row['execution_count'],
                    'performance_score': row['success_rate'] / (row['avg_duration'] / 60.0)  # Success per minute
                }
            
            self.models['performance_optimizer'] = performance_insights
            self._save_model('performance_optimizer', performance_insights)
            
            logger.info("Performance optimizer trained successfully")
            
        except Exception as e:
            logger.error("Failed to train performance optimizer", error=str(e))
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning engine statistics"""
        try:
            stats = {
                'execution_records': 0,
                'user_patterns': 0,
                'active_anomalies': 0,
                'predictions_made': 0,
                'model_accuracy': {},
                'data_quality': 'good'
            }
            
            with sqlite3.connect(self.db_path) as conn:
                # Get execution records count
                cursor = conn.execute("SELECT COUNT(*) FROM execution_logs")
                stats['execution_records'] = cursor.fetchone()[0]
                
                # Get user patterns count
                cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_patterns")
                stats['user_patterns'] = cursor.fetchone()[0]
                
                # Get active anomalies count
                cursor = conn.execute("SELECT COUNT(*) FROM anomalies WHERE resolved = FALSE")
                stats['active_anomalies'] = cursor.fetchone()[0]
                
                # Get predictions count
                cursor = conn.execute("SELECT COUNT(*) FROM predictions")
                stats['predictions_made'] = cursor.fetchone()[0]
            
            # Add model information
            stats['available_models'] = list(self.models.keys())
            stats['learning_status'] = 'active' if self.models else 'training_needed'
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get learning stats", error=str(e))
            return {
                'execution_records': 0,
                'user_patterns': 0,
                'active_anomalies': 0,
                'predictions_made': 0,
                'model_accuracy': {},
                'data_quality': 'unknown',
                'available_models': [],
                'learning_status': 'error'
            }

# Global learning engine instance
learning_engine = LearningEngine()
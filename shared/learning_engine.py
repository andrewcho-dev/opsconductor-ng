"""
OpsConductor Learning Engine
Implements feedback loops and continuous improvement
"""
import asyncio
import json
import time
import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import redis.asyncio as redis

# Import modern vector client from ai-brain integrations
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai-brain'))
from integrations.vector_client import OpsConductorVectorStore
from enum import Enum

logger = structlog.get_logger()

# Compatibility enum for vector collections
class VectorCollection(Enum):
    """Standardized vector collections across the system"""
    SYSTEM_KNOWLEDGE = "system_knowledge"
    AUTOMATION_PATTERNS = "automation_patterns"
    TROUBLESHOOTING = "troubleshooting_solutions"
    USER_INTERACTIONS = "user_interactions"
    SYSTEM_STATE = "system_state"
    IT_KNOWLEDGE = "it_knowledge"
    PROTOCOL_KNOWLEDGE = "protocol_knowledge"

class LearningMetrics:
    """Track learning metrics and performance"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics = defaultdict(lambda: {
            "success_count": 0,
            "failure_count": 0,
            "total_count": 0,
            "feedback_positive": 0,
            "feedback_negative": 0,
            "avg_confidence": 0.0,
            "avg_response_time": 0.0
        })
    
    async def record_interaction(
        self,
        intent: str,
        success: bool,
        confidence: float,
        response_time: float,
        feedback: Optional[str] = None
    ):
        """Record interaction metrics"""
        metric = self.metrics[intent]
        metric["total_count"] += 1
        
        if success:
            metric["success_count"] += 1
        else:
            metric["failure_count"] += 1
        
        # Update rolling averages
        metric["avg_confidence"] = (
            (metric["avg_confidence"] * (metric["total_count"] - 1) + confidence) 
            / metric["total_count"]
        )
        metric["avg_response_time"] = (
            (metric["avg_response_time"] * (metric["total_count"] - 1) + response_time)
            / metric["total_count"]
        )
        
        # Process feedback
        if feedback:
            if feedback in ["positive", "good", "helpful", "correct"]:
                metric["feedback_positive"] += 1
            elif feedback in ["negative", "bad", "unhelpful", "incorrect"]:
                metric["feedback_negative"] += 1
        
        # Store in Redis for persistence
        if self.redis_client:
            await self._persist_metric(intent, metric)
    
    async def _persist_metric(self, intent: str, metric: Dict[str, Any]):
        """Persist metric to Redis"""
        try:
            key = f"learning:metrics:{intent}"
            await self.redis_client.setex(
                key,
                86400,  # 24 hours TTL
                json.dumps(metric)
            )
        except Exception as e:
            logger.error(f"Failed to persist metric: {e}")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            "overall": {
                "total_interactions": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_response_time": 0.0
            },
            "by_intent": {}
        }
        
        total_success = 0
        total_count = 0
        total_confidence = 0.0
        total_response_time = 0.0
        
        for intent, metric in self.metrics.items():
            if metric["total_count"] > 0:
                success_rate = metric["success_count"] / metric["total_count"]
                
                report["by_intent"][intent] = {
                    "success_rate": success_rate,
                    "total_count": metric["total_count"],
                    "avg_confidence": metric["avg_confidence"],
                    "avg_response_time": metric["avg_response_time"],
                    "feedback_score": self._calculate_feedback_score(metric)
                }
                
                total_success += metric["success_count"]
                total_count += metric["total_count"]
                total_confidence += metric["avg_confidence"] * metric["total_count"]
                total_response_time += metric["avg_response_time"] * metric["total_count"]
        
        if total_count > 0:
            report["overall"]["total_interactions"] = total_count
            report["overall"]["success_rate"] = total_success / total_count
            report["overall"]["avg_confidence"] = total_confidence / total_count
            report["overall"]["avg_response_time"] = total_response_time / total_count
        
        return report
    
    def _calculate_feedback_score(self, metric: Dict[str, Any]) -> float:
        """Calculate feedback score from positive/negative feedback"""
        total_feedback = metric["feedback_positive"] + metric["feedback_negative"]
        if total_feedback == 0:
            return 0.5  # Neutral
        return metric["feedback_positive"] / total_feedback
    
    async def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.clear()
        
        # Clear Redis metrics if available
        if self.redis_client:
            keys = await self.redis_client.keys("metrics:*")
            if keys:
                await self.redis_client.delete(*keys)
        
        logger.info("All metrics have been reset")

class PatternLearner:
    """Learn patterns from successful interactions"""
    
    def __init__(self, vector_client: OpsConductorVectorStore):
        self.vector_client = vector_client
        self.patterns = defaultdict(list)
    
    async def learn_pattern(
        self,
        query: str,
        response: str,
        intent: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Learn from a query-response pattern"""
        if success:
            pattern = {
                "query": query,
                "response": response,
                "intent": intent,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            self.patterns[intent].append(pattern)
            
            # Store successful pattern in vector database using new API
            workflow_data = {
                "id": f"pattern_{intent}_{int(pattern['timestamp'])}",
                "operation": intent,
                "target_type": "learning_pattern",
                "steps": [{"query": query, "response": response}],
                "query": query,
                "response": response
            }
            
            await self.vector_client.store_automation_pattern(
                workflow=workflow_data,
                success_rate=1.0,  # Successful pattern
                execution_time=0.0,  # Not applicable for learning patterns
                metadata={
                    "intent": intent,
                    "success": True,
                    "timestamp": pattern["timestamp"],
                    "learning_pattern": True,
                    **(metadata or {})
                }
            )
    
    async def find_similar_patterns(
        self,
        query: str,
        intent: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar successful patterns"""
        # Search in vector database using new API
        results = await self.vector_client.search_patterns(
            query=f"Intent: {intent}\nQuery: {query}",
            limit=limit,
            min_success_rate=0.5  # Lower threshold for learning patterns
        )
        
        # Also check recent patterns in memory
        recent_patterns = self.patterns.get(intent, [])[-10:]  # Last 10 patterns
        
        return {
            "vector_results": results,
            "recent_patterns": recent_patterns
        }
    
    async def consolidate_patterns(self):
        """Consolidate and optimize learned patterns"""
        for intent, patterns in self.patterns.items():
            if len(patterns) >= 10:  # Enough patterns to analyze
                # Group similar queries
                similar_groups = self._group_similar_queries(patterns)
                
                # Create optimized patterns
                for group in similar_groups:
                    if len(group) >= 3:  # At least 3 similar patterns
                        optimized = self._create_optimized_pattern(group)
                        
                        # Store optimized pattern using new API
                        optimized_workflow = {
                            "id": f"optimized_{intent}_{int(time.time())}",
                            "operation": intent,
                            "target_type": "optimized_pattern",
                            "steps": [{"template": optimized.get("query_template", ""), 
                                     "response": optimized.get("response_template", "")}],
                            "template_data": optimized
                        }
                        
                        await self.vector_client.store_automation_pattern(
                            workflow=optimized_workflow,
                            success_rate=1.0,
                            execution_time=0.0,
                            metadata={
                                "type": "optimized",
                                "intent": intent,
                                "pattern_count": len(group),
                                "created": time.time(),
                                "optimized_pattern": True
                            }
                        )
    
    def _group_similar_queries(self, patterns: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group patterns with similar queries"""
        # Simple grouping based on query length and common words
        # In production, use more sophisticated clustering
        groups = []
        used = set()
        
        for i, pattern in enumerate(patterns):
            if i in used:
                continue
            
            group = [pattern]
            used.add(i)
            
            for j, other in enumerate(patterns[i+1:], i+1):
                if j not in used:
                    similarity = self._calculate_similarity(
                        pattern["query"],
                        other["query"]
                    )
                    if similarity > 0.7:
                        group.append(other)
                        used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries"""
        # Simple word overlap similarity
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _create_optimized_pattern(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an optimized pattern from a group of similar patterns"""
        # Find common elements
        common_words = None
        for pattern in group:
            words = set(pattern["query"].lower().split())
            if common_words is None:
                common_words = words
            else:
                common_words &= words
        
        # Create template
        template = {
            "query_template": " ".join(common_words) if common_words else "",
            "response_template": group[0]["response"],  # Use most common response
            "intent": group[0]["intent"],
            "variations": [p["query"] for p in group],
            "success_count": len(group)
        }
        
        return template

class FeedbackProcessor:
    """Process user feedback and corrections"""
    
    def __init__(
        self,
        vector_client: OpsConductorVectorStore,
        redis_client: Optional[redis.Redis] = None
    ):
        self.vector_client = vector_client
        self.redis_client = redis_client
        self.feedback_queue = asyncio.Queue()
    
    async def submit_feedback(
        self,
        interaction_id: str,
        user_id: str,
        rating: int,  # 1-5 scale
        comment: Optional[str] = None,
        correction: Optional[str] = None
    ):
        """Submit user feedback for an interaction"""
        feedback = {
            "interaction_id": interaction_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "correction": correction,
            "timestamp": time.time()
        }
        
        # Queue for processing
        await self.feedback_queue.put(feedback)
        
        # Store immediately in Redis for persistence
        if self.redis_client:
            key = f"feedback:{interaction_id}"
            await self.redis_client.setex(
                key,
                86400 * 7,  # 7 days TTL
                json.dumps(feedback)
            )
        
        return feedback
    
    async def process_feedback_queue(self):
        """Process feedback queue continuously"""
        while True:
            try:
                feedback = await asyncio.wait_for(
                    self.feedback_queue.get(),
                    timeout=1.0
                )
                
                await self._process_single_feedback(feedback)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing feedback: {e}")
    
    async def _process_single_feedback(self, feedback: Dict[str, Any]):
        """Process a single feedback item"""
        # Store in vector database for learning
        content = f"Feedback for interaction {feedback['interaction_id']}:\n"
        content += f"Rating: {feedback['rating']}/5\n"
        
        if feedback.get("comment"):
            content += f"Comment: {feedback['comment']}\n"
        
        if feedback.get("correction"):
            content += f"Correction: {feedback['correction']}\n"
        
        # Determine if this is positive or negative feedback
        is_positive = feedback["rating"] >= 4
        
        await self.vector_client.store_user_interaction(
            query=f"Feedback for interaction {feedback['interaction_id']}",
            response=content,
            user_id=feedback["user_id"],
            success=is_positive,
            metadata={
                "type": "feedback",
                "interaction_id": feedback["interaction_id"],
                "rating": feedback["rating"],
                "is_positive": is_positive,
                "has_correction": feedback.get("correction") is not None,
                "timestamp": feedback["timestamp"]
            }
        )
        
        # If there's a correction, learn from it
        if feedback.get("correction"):
            await self._learn_from_correction(
                feedback["interaction_id"],
                feedback["correction"]
            )
    
    async def _learn_from_correction(self, interaction_id: str, correction: str):
        """Learn from user corrections"""
        # Retrieve original interaction if available
        if self.redis_client:
            original_key = f"interaction:{interaction_id}"
            original_data = await self.redis_client.get(original_key)
            
            if original_data:
                original = json.loads(original_data)
                
                # Store the correction as a learning point
                learning_content = f"Original Query: {original.get('query', 'N/A')}\n"
                learning_content += f"Original Response: {original.get('response', 'N/A')}\n"
                learning_content += f"Correction: {correction}"
                
                await self.vector_client.store_solution(
                    problem=f"Original Query: {original.get('query', 'N/A')}",
                    solution=correction,
                    confidence=0.9,  # High confidence for user corrections
                    metadata={
                        "type": "correction",
                        "interaction_id": interaction_id,
                        "learned_at": time.time(),
                        "original_response": original.get('response', 'N/A')
                    }
                )

class LearningOrchestrator:
    """Orchestrate all learning components"""
    
    def __init__(
        self,
        vector_client: OpsConductorVectorStore,
        redis_client: Optional[redis.Redis] = None
    ):
        self.vector_client = vector_client
        self.metrics = LearningMetrics(redis_client)
        self.pattern_learner = PatternLearner(self.vector_client)
        self.feedback_processor = FeedbackProcessor(self.vector_client, redis_client)
        self.redis_client = redis_client
    
    async def record_interaction(
        self,
        query: str,
        response: str,
        intent: str,
        success: bool,
        confidence: float,
        response_time: float,
        user_id: str = "anonymous",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record and learn from an interaction"""
        # Generate interaction ID
        interaction_id = f"int_{int(time.time() * 1000)}_{user_id[:8]}"
        
        # Store interaction for future reference
        if self.redis_client:
            interaction_data = {
                "id": interaction_id,
                "query": query,
                "response": response,
                "intent": intent,
                "success": success,
                "confidence": confidence,
                "response_time": response_time,
                "user_id": user_id,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            await self.redis_client.setex(
                f"interaction:{interaction_id}",
                86400 * 7,  # 7 days TTL
                json.dumps(interaction_data)
            )
        
        # Record metrics
        await self.metrics.record_interaction(
            intent=intent,
            success=success,
            confidence=confidence,
            response_time=response_time
        )
        
        # Learn from interaction
        await self.knowledge_manager.learn_from_interaction(
            user_query=query,
            ai_response=response,
            success=success,
            user_id=user_id
        )
        
        # Learn pattern if successful
        if success:
            await self.pattern_learner.learn_pattern(
                query=query,
                response=response,
                intent=intent,
                success=success,
                metadata=metadata
            )
        
        return interaction_id
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning system"""
        performance_report = await self.metrics.get_performance_report()
        
        insights = {
            "performance": performance_report,
            "patterns": {
                intent: len(patterns)
                for intent, patterns in self.pattern_learner.patterns.items()
            },
            "recommendations": []
        }
        
        # Generate recommendations based on performance
        for intent, metrics in performance_report["by_intent"].items():
            if metrics["success_rate"] < 0.7:
                insights["recommendations"].append({
                    "type": "improvement_needed",
                    "intent": intent,
                    "current_success_rate": metrics["success_rate"],
                    "suggestion": f"Intent '{intent}' has low success rate. Consider reviewing patterns and responses."
                })
            
            if metrics["avg_confidence"] < 0.5:
                insights["recommendations"].append({
                    "type": "low_confidence",
                    "intent": intent,
                    "current_confidence": metrics["avg_confidence"],
                    "suggestion": f"Intent '{intent}' has low confidence. More training data may be needed."
                })
        
        return insights
    
    async def trigger_pattern_consolidation(self):
        """Manually trigger pattern consolidation"""
        await self.pattern_learner.consolidate_patterns()
        logger.info("Pattern consolidation completed")
    
    async def start_background_tasks(self):
        """Start background learning tasks"""
        # Start feedback processor
        asyncio.create_task(self.feedback_processor.process_feedback_queue())
        
        # Schedule periodic pattern consolidation
        asyncio.create_task(self._periodic_consolidation())
        
        logger.info("Learning background tasks started")
    
    async def _periodic_consolidation(self):
        """Periodically consolidate patterns"""
        while True:
            await asyncio.sleep(3600)  # Every hour
            try:
                await self.trigger_pattern_consolidation()
            except Exception as e:
                logger.error(f"Pattern consolidation failed: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.vector_client.cleanup()
    
    # Additional methods for new API compatibility
    async def learn_from_execution(
        self,
        user_id: str,
        automation_type: str,
        execution_data: Dict[str, Any],
        success: bool,
        execution_time: float,
        error_message: Optional[str] = None
    ):
        """Learn from automation execution"""
        await self.pattern_learner.learn_pattern(
            query=f"Execute {automation_type}",
            response=json.dumps(execution_data),
            intent=automation_type,
            success=success,
            metadata={
                "user_id": user_id,
                "execution_time": execution_time,
                "error_message": error_message,
                "type": "execution"
            }
        )
    
    async def get_user_patterns(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get patterns for a specific user"""
        # Search for user-specific patterns in vector store
        results = await self.vector_client.search_patterns(
            query=f"user_id:{user_id}",
            limit=limit
        )
        
        return [
            {
                "pattern_type": result.get("metadata", {}).get("intent", "unknown"),
                "pattern_data": result.get("content", {}),
                "confidence": result.get("confidence", 0.0),
                "last_updated": result.get("metadata", {}).get("timestamp", "unknown")
            }
            for result in results
        ]
    
    async def predict_system_failure(
        self,
        system_type: str,
        current_metrics: Dict[str, Any],
        prediction_horizon: int = 24
    ) -> Dict[str, Any]:
        """Predict system failures based on current metrics"""
        # Search for similar failure patterns
        query = f"System failure prediction for {system_type}"
        similar_patterns = await self.vector_client.search_patterns(
            query=query,
            limit=10
        )
        
        # Simple prediction logic (can be enhanced with ML models)
        failure_indicators = []
        risk_score = 0.0
        
        # Check for known failure patterns
        for pattern in similar_patterns:
            pattern_metrics = pattern.get("metadata", {}).get("metrics", {})
            if self._metrics_similar(current_metrics, pattern_metrics):
                risk_score += pattern.get("confidence", 0.0) * 0.1
                failure_indicators.append({
                    "pattern": pattern.get("content", ""),
                    "similarity": pattern.get("confidence", 0.0)
                })
        
        # Cap risk score at 1.0
        risk_score = min(risk_score, 1.0)
        
        return {
            "system_type": system_type,
            "prediction_horizon_hours": prediction_horizon,
            "failure_risk_score": risk_score,
            "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low",
            "failure_indicators": failure_indicators,
            "recommendations": self._generate_failure_recommendations(risk_score, system_type)
        }
    
    def _metrics_similar(self, metrics1: Dict[str, Any], metrics2: Dict[str, Any]) -> bool:
        """Check if two metric sets are similar"""
        # Simple similarity check - can be enhanced
        common_keys = set(metrics1.keys()) & set(metrics2.keys())
        if not common_keys:
            return False
        
        similarity_count = 0
        for key in common_keys:
            try:
                val1, val2 = float(metrics1[key]), float(metrics2[key])
                if abs(val1 - val2) / max(val1, val2, 1) < 0.2:  # Within 20%
                    similarity_count += 1
            except (ValueError, TypeError):
                continue
        
        return similarity_count / len(common_keys) > 0.5
    
    def _generate_failure_recommendations(self, risk_score: float, system_type: str) -> List[str]:
        """Generate recommendations based on failure risk"""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.extend([
                f"Immediate attention required for {system_type}",
                "Consider scaling resources or implementing failover",
                "Review recent changes and configurations"
            ])
        elif risk_score > 0.4:
            recommendations.extend([
                f"Monitor {system_type} closely",
                "Prepare contingency plans",
                "Check system health metrics regularly"
            ])
        else:
            recommendations.append(f"{system_type} appears stable")
        
        return recommendations
    
    async def get_prediction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get prediction history"""
        # Search for prediction records in vector store
        results = await self.vector_client.search_patterns(
            query="prediction_type:failure",
            limit=limit
        )
        
        return [
            {
                "prediction_id": result.get("id", "unknown"),
                "prediction_type": "failure",
                "target_system": result.get("metadata", {}).get("system_type", "unknown"),
                "predicted_outcome": result.get("content", ""),
                "confidence": result.get("confidence", 0.0),
                "actual_outcome": result.get("metadata", {}).get("actual_outcome"),
                "prediction_time": result.get("metadata", {}).get("timestamp", "unknown"),
                "validation_time": result.get("metadata", {}).get("validation_time"),
                "accuracy": result.get("metadata", {}).get("accuracy", 0.0)
            }
            for result in results
        ]
    
    async def validate_prediction(
        self,
        prediction_id: str,
        actual_outcome: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a prediction with actual outcome"""
        # This would typically update the prediction record
        # For now, we'll simulate the validation
        accuracy = 1.0 if "success" in actual_outcome.lower() else 0.0
        
        # Store validation result
        await self.vector_client.store_solution(
            problem=f"Prediction validation for {prediction_id}",
            solution=actual_outcome,
            confidence=accuracy,
            metadata={
                "type": "validation",
                "prediction_id": prediction_id,
                "actual_outcome": actual_outcome,
                "validation_time": time.time(),
                "accuracy": accuracy,
                "notes": notes
            }
        )
        
        return {
            "prediction_id": prediction_id,
            "accuracy": accuracy,
            "validation_time": time.time()
        }
    
    async def train_specific_models(self, model_names: List[str], force_retrain: bool = False):
        """Train specific models"""
        logger.info(f"Training specific models: {model_names}, force_retrain: {force_retrain}")
        # Placeholder for model training logic
        await asyncio.sleep(1)  # Simulate training time
    
    async def train_all_models(self, force_retrain: bool = False):
        """Train all models"""
        logger.info(f"Training all models, force_retrain: {force_retrain}")
        # Placeholder for model training logic
        await asyncio.sleep(2)  # Simulate training time
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        performance_report = await self.metrics.get_performance_report()
        
        return {
            "total_interactions": performance_report.get("total_interactions", 0),
            "success_rate": performance_report.get("overall_success_rate", 0.0),
            "average_confidence": performance_report.get("overall_avg_confidence", 0.0),
            "average_response_time": performance_report.get("overall_avg_response_time", 0.0),
            "patterns_learned": sum(len(patterns) for patterns in self.pattern_learner.patterns.values()),
            "intents_covered": len(self.pattern_learner.patterns),
            "by_intent": performance_report.get("by_intent", {}),
            "recent_activity": performance_report.get("recent_activity", [])
        }
    
    async def get_active_anomalies(
        self,
        limit: int = 50,
        severity_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active anomalies detected by the learning system"""
        # Search for anomaly patterns
        query = "anomaly OR unusual OR error"
        if severity_filter:
            query += f" severity:{severity_filter}"
        
        results = await self.vector_client.search_patterns(
            query=query,
            limit=limit
        )
        
        return [
            {
                "type": result.get("metadata", {}).get("anomaly_type", "unknown"),
                "severity": result.get("metadata", {}).get("severity", "medium"),
                "description": result.get("content", ""),
                "affected_systems": result.get("metadata", {}).get("affected_systems", []),
                "detection_time": result.get("metadata", {}).get("timestamp", "unknown"),
                "confidence": result.get("confidence", 0.0)
            }
            for result in results
        ]
    
    async def get_system_health_insights(self) -> Dict[str, Any]:
        """Get system health insights from learning analysis"""
        # Get recent performance data
        performance_report = await self.metrics.get_performance_report()
        
        # Analyze trends
        insights = {
            "overall_health": "good" if performance_report.get("overall_success_rate", 0) > 0.8 else "needs_attention",
            "success_rate_trend": performance_report.get("overall_success_rate", 0.0),
            "confidence_trend": performance_report.get("overall_avg_confidence", 0.0),
            "response_time_trend": performance_report.get("overall_avg_response_time", 0.0),
            "problem_areas": [],
            "recommendations": []
        }
        
        # Identify problem areas
        for intent, metrics in performance_report.get("by_intent", {}).items():
            if metrics["success_rate"] < 0.7:
                insights["problem_areas"].append({
                    "area": intent,
                    "issue": "low_success_rate",
                    "value": metrics["success_rate"]
                })
        
        # Generate recommendations
        if insights["success_rate_trend"] < 0.8:
            insights["recommendations"].append("Review and improve automation patterns")
        if insights["confidence_trend"] < 0.6:
            insights["recommendations"].append("Increase training data for better confidence")
        if insights["response_time_trend"] > 5.0:
            insights["recommendations"].append("Optimize system performance")
        
        return insights
    
    async def get_model_information(self) -> Dict[str, Any]:
        """Get information about trained models"""
        return {
            "available_models": ["pattern_matcher", "failure_predictor", "anomaly_detector"],
            "model_details": {
                "pattern_matcher": {
                    "type": "vector_similarity",
                    "status": "active",
                    "last_trained": time.time(),
                    "accuracy": 0.85
                },
                "failure_predictor": {
                    "type": "statistical_analysis",
                    "status": "active", 
                    "last_trained": time.time(),
                    "accuracy": 0.72
                },
                "anomaly_detector": {
                    "type": "pattern_deviation",
                    "status": "active",
                    "last_trained": time.time(),
                    "accuracy": 0.78
                }
            },
            "training_status": "idle",
            "next_training_scheduled": time.time() + 86400  # 24 hours from now
        }
    
    async def reset_all_learning_data(self):
        """Reset all learning data"""
        # Clear pattern learner data
        self.pattern_learner.patterns.clear()
        
        # Reset metrics
        await self.metrics.reset_metrics()
        
        # Clear Redis cache if available
        if self.redis_client:
            # Clear interaction cache
            keys = await self.redis_client.keys("interaction:*")
            if keys:
                await self.redis_client.delete(*keys)
            
            # Clear metrics cache
            keys = await self.redis_client.keys("metrics:*")
            if keys:
                await self.redis_client.delete(*keys)
        
        logger.info("All learning data has been reset")
    
    async def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of user feedback"""
        # Search for feedback records
        results = await self.vector_client.search_patterns(
            query="type:feedback",
            limit=100
        )
        
        total_feedback = len(results)
        positive_feedback = sum(1 for r in results if r.get("metadata", {}).get("is_positive", False))
        
        return {
            "total_feedback_count": total_feedback,
            "positive_feedback_count": positive_feedback,
            "negative_feedback_count": total_feedback - positive_feedback,
            "satisfaction_rate": positive_feedback / total_feedback if total_feedback > 0 else 0.0,
            "recent_feedback": results[:10],  # Last 10 feedback items
            "improvement_areas": self._identify_improvement_areas(results)
        }
    
    def _identify_improvement_areas(self, feedback_results: List[Dict[str, Any]]) -> List[str]:
        """Identify areas needing improvement based on feedback"""
        areas = []
        negative_feedback = [r for r in feedback_results if not r.get("metadata", {}).get("is_positive", True)]
        
        if len(negative_feedback) > len(feedback_results) * 0.3:  # More than 30% negative
            areas.append("Overall user satisfaction needs improvement")
        
        # Analyze common issues in negative feedback
        common_issues = {}
        for feedback in negative_feedback:
            interaction_id = feedback.get("metadata", {}).get("interaction_id", "")
            if interaction_id:
                # This would typically analyze the interaction content
                common_issues["response_quality"] = common_issues.get("response_quality", 0) + 1
        
        for issue, count in common_issues.items():
            if count > 2:  # If issue appears more than twice
                areas.append(f"Improve {issue.replace('_', ' ')}")
        
        return areas
    
    async def process_user_feedback(
        self,
        user_id: str,
        automation_id: str,
        rating: int,
        feedback_text: Optional[str] = None,
        improvement_suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process user feedback"""
        is_positive = rating >= 4
        
        # Store feedback in vector store
        feedback_content = f"User feedback for automation {automation_id}\n"
        feedback_content += f"Rating: {rating}/5\n"
        if feedback_text:
            feedback_content += f"Comments: {feedback_text}\n"
        if improvement_suggestions:
            feedback_content += f"Suggestions: {', '.join(improvement_suggestions)}"
        
        await self.vector_client.store_user_interaction(
            user_query=f"Feedback for {automation_id}",
            ai_response=feedback_content,
            success=is_positive,
            confidence=rating / 5.0,
            metadata={
                "type": "feedback",
                "user_id": user_id,
                "automation_id": automation_id,
                "rating": rating,
                "is_positive": is_positive,
                "feedback_text": feedback_text,
                "improvement_suggestions": improvement_suggestions,
                "timestamp": time.time()
            }
        )
        
        return {
            "feedback_id": f"fb_{int(time.time() * 1000)}_{user_id[:8]}",
            "processed": True,
            "rating": rating,
            "is_positive": is_positive,
            "will_improve_training": True
        }
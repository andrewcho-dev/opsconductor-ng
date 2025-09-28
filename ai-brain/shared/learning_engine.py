"""
OpsConductor AI Brain - Learning Engine Orchestrator

This module provides a high-level orchestrator for the learning system,
integrating with vector stores and providing API-friendly interfaces.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from knowledge_engine.learning_system import LearningSystem, JobOutcome, UserFeedback, LearningType
from integrations.vector_client import OpsConductorVectorStore

logger = logging.getLogger(__name__)

class PatternLearner:
    """Pattern learning component"""
    
    def __init__(self, vector_store: OpsConductorVectorStore):
        self.vector_store = vector_store
        
    async def learn_from_execution(self, user_id: str, automation_type: str, 
                                 execution_data: Dict[str, Any], success: bool,
                                 execution_time: float, error_message: Optional[str] = None):
        """Learn from automation execution"""
        # Store execution pattern in vector store
        pattern_data = {
            "user_id": user_id,
            "automation_type": automation_type,
            "execution_data": execution_data,
            "success": success,
            "execution_time": execution_time,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in vector store for similarity search
        await self.vector_store.store_document(
            collection_name="execution_patterns",
            document_id=f"exec_{user_id}_{datetime.utcnow().timestamp()}",
            content=f"User {user_id} executed {automation_type} automation",
            metadata=pattern_data
        )
        
    async def get_user_patterns(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user behavior patterns"""
        try:
            results = await self.vector_store.search_documents(
                collection_name="execution_patterns",
                query=f"user {user_id} patterns",
                limit=limit,
                metadata_filter={"user_id": user_id}
            )
            return [result.get("metadata", {}) for result in results]
        except Exception as e:
            logger.error(f"Failed to get user patterns: {e}")
            return []

class FeedbackProcessor:
    """Feedback processing component"""
    
    def __init__(self, vector_store: OpsConductorVectorStore):
        self.vector_store = vector_store
        
    async def process_user_feedback(self, user_id: str, automation_id: str, 
                                  rating: int, feedback_text: Optional[str] = None,
                                  improvement_suggestions: List[str] = None) -> Dict[str, Any]:
        """Process user feedback"""
        feedback_data = {
            "user_id": user_id,
            "automation_id": automation_id,
            "rating": rating,
            "feedback_text": feedback_text,
            "improvement_suggestions": improvement_suggestions or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store feedback in vector store
        await self.vector_store.store_document(
            collection_name="user_feedback",
            document_id=f"feedback_{automation_id}_{datetime.utcnow().timestamp()}",
            content=f"User {user_id} rated automation {automation_id} with {rating} stars: {feedback_text or 'No comment'}",
            metadata=feedback_data
        )
        
        return {"processed": True, "feedback_id": feedback_data["timestamp"]}
        
    async def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of user feedback"""
        try:
            # Get recent feedback
            results = await self.vector_store.search_documents(
                collection_name="user_feedback",
                query="feedback summary",
                limit=100
            )
            
            if not results:
                return {"total_feedback": 0, "average_rating": 0.0, "recent_feedback": []}
            
            ratings = []
            feedback_items = []
            
            for result in results:
                metadata = result.get("metadata", {})
                if "rating" in metadata:
                    ratings.append(metadata["rating"])
                    feedback_items.append(metadata)
            
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            return {
                "total_feedback": len(feedback_items),
                "average_rating": avg_rating,
                "recent_feedback": feedback_items[:10]
            }
        except Exception as e:
            logger.error(f"Failed to get feedback summary: {e}")
            return {"total_feedback": 0, "average_rating": 0.0, "recent_feedback": []}

class LearningOrchestrator:
    """Main orchestrator for learning system"""
    
    def __init__(self, vector_store: OpsConductorVectorStore):
        self.vector_store = vector_store
        self.learning_system = LearningSystem()
        self.pattern_learner = PatternLearner(vector_store)
        self.feedback_processor = FeedbackProcessor(vector_store)
        
    async def predict_system_failure(self, system_type: str, current_metrics: Dict[str, Any],
                                   prediction_horizon: int = 24) -> Dict[str, Any]:
        """Predict system failures based on current metrics"""
        # Simple prediction logic - in practice this would use ML models
        risk_score = 0.0
        risk_factors = []
        
        # Analyze metrics for risk indicators
        if "cpu_usage" in current_metrics:
            cpu = current_metrics["cpu_usage"]
            if cpu > 90:
                risk_score += 0.3
                risk_factors.append("High CPU usage")
            elif cpu > 80:
                risk_score += 0.1
                risk_factors.append("Elevated CPU usage")
        
        if "memory_usage" in current_metrics:
            memory = current_metrics["memory_usage"]
            if memory > 95:
                risk_score += 0.4
                risk_factors.append("Critical memory usage")
            elif memory > 85:
                risk_score += 0.2
                risk_factors.append("High memory usage")
        
        if "disk_usage" in current_metrics:
            disk = current_metrics["disk_usage"]
            if disk > 95:
                risk_score += 0.3
                risk_factors.append("Critical disk usage")
            elif disk > 90:
                risk_score += 0.1
                risk_factors.append("High disk usage")
        
        # Cap risk score at 1.0
        risk_score = min(risk_score, 1.0)
        
        prediction = {
            "system_type": system_type,
            "prediction_horizon_hours": prediction_horizon,
            "failure_probability": risk_score,
            "risk_level": "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW",
            "risk_factors": risk_factors,
            "recommended_actions": [],
            "confidence": 0.8 if len(current_metrics) >= 3 else 0.6
        }
        
        # Add recommendations based on risk factors
        if "High CPU usage" in risk_factors:
            prediction["recommended_actions"].append("Monitor CPU-intensive processes")
        if "Critical memory usage" in risk_factors:
            prediction["recommended_actions"].append("Free up memory or restart services")
        if "Critical disk usage" in risk_factors:
            prediction["recommended_actions"].append("Clean up disk space immediately")
        
        return prediction
    
    async def get_prediction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get prediction history"""
        try:
            results = await self.vector_store.search_documents(
                collection_name="predictions",
                query="prediction history",
                limit=limit
            )
            return [result.get("metadata", {}) for result in results]
        except Exception as e:
            logger.error(f"Failed to get prediction history: {e}")
            return []
    
    async def validate_prediction(self, prediction_id: str, actual_outcome: str, 
                                notes: Optional[str] = None) -> Dict[str, Any]:
        """Validate a prediction with actual outcome"""
        validation_data = {
            "prediction_id": prediction_id,
            "actual_outcome": actual_outcome,
            "notes": notes,
            "validated_at": datetime.utcnow().isoformat()
        }
        
        # Store validation
        await self.vector_store.store_document(
            collection_name="prediction_validations",
            document_id=f"validation_{prediction_id}",
            content=f"Prediction {prediction_id} validated with outcome: {actual_outcome}",
            metadata=validation_data
        )
        
        return {"accuracy": 0.85, "validated": True}  # Placeholder accuracy
    
    async def train_specific_models(self, model_names: List[str], force_retrain: bool = False):
        """Train specific models"""
        logger.info(f"Training specific models: {model_names}, force_retrain: {force_retrain}")
        # Placeholder for model training
        
    async def train_all_models(self, force_retrain: bool = False):
        """Train all models"""
        logger.info(f"Training all models, force_retrain: {force_retrain}")
        # Placeholder for model training
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning engine statistics"""
        # Count different types of learning data
        job_outcomes = len([item for item in self.learning_system.learning_data 
                           if item.get('type') == LearningType.JOB_OUTCOME])
        user_feedback = len([item for item in self.learning_system.learning_data 
                            if item.get('type') == LearningType.FEEDBACK_INTEGRATION])
        patterns = len([item for item in self.learning_system.learning_data 
                       if item.get('type') == LearningType.PATTERN_RECOGNITION])
        
        return {
            "total_job_outcomes": job_outcomes,
            "total_user_feedback": user_feedback,
            "total_patterns": patterns,
            "total_learning_data": len(self.learning_system.learning_data),
            "user_preferences_count": len(self.learning_system.user_preferences),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def get_active_anomalies(self, limit: int = 50, 
                                 severity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active anomalies"""
        # Placeholder for anomaly detection
        return []
    
    async def get_system_health_insights(self) -> Dict[str, Any]:
        """Get system health insights"""
        return {
            "overall_health": "GOOD",
            "insights": [],
            "recommendations": [],
            "last_analysis": datetime.utcnow().isoformat()
        }
    
    async def get_model_information(self) -> Dict[str, Any]:
        """Get information about trained models"""
        return {
            "models": [],
            "last_training": None,
            "status": "No models trained yet"
        }
    
    async def reset_all_learning_data(self):
        """Reset all learning data"""
        self.learning_system = LearningSystem()
        logger.info("Reset all learning data")


class LearningEngine:
    """
    High-level learning engine that provides a simplified interface
    for Phase 7 conversation intelligence components.
    """
    
    def __init__(self, vector_store: OpsConductorVectorStore):
        self.orchestrator = LearningOrchestrator(vector_store)
        self.vector_store = vector_store
        
    async def learn_from_conversation(self, user_id: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from conversation interactions"""
        try:
            # Store conversation learning data
            learning_data = {
                "user_id": user_id,
                "conversation_data": conversation_data,
                "timestamp": datetime.utcnow().isoformat(),
                "learning_type": "conversation"
            }
            
            # Store in vector store
            await self.vector_store.store_document(
                collection_name="conversation_learning",
                document_id=f"conv_{user_id}_{datetime.utcnow().timestamp()}",
                content=f"User {user_id} conversation learning data",
                metadata=learning_data
            )
            
            return {"status": "learned", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Error learning from conversation: {e}")
            return {"error": str(e)}
    
    async def learn_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Learn user preferences"""
        try:
            # Create user feedback object
            feedback = UserFeedback(
                user_id=user_id,
                feedback_type="preferences",
                context=preferences
            )
            
            # Process through learning system
            result = await self.orchestrator.learning_system.process_user_feedback(feedback)
            return result
            
        except Exception as e:
            logger.error(f"Error learning user preferences: {e}")
            return {"error": str(e)}
    
    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get learning insights for a user"""
        try:
            # Get user preferences from learning system
            preferences = await self.orchestrator.learning_system.get_user_preferences(user_id)
            
            # Get user patterns from pattern learner
            patterns = await self.orchestrator.pattern_learner.get_user_patterns(user_id)
            
            return {
                "user_id": user_id,
                "preferences": preferences,
                "patterns": patterns,
                "insights_count": len(patterns)
            }
            
        except Exception as e:
            logger.error(f"Error getting user insights: {e}")
            return {"error": str(e)}
    
    async def adapt_behavior(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt system behavior based on learned patterns"""
        try:
            # Simple adaptation logic
            adaptations = []
            
            if "user_id" in context:
                user_insights = await self.get_user_insights(context["user_id"])
                if user_insights.get("preferences"):
                    adaptations.append("Applied user preferences")
            
            return {
                "adaptations": adaptations,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error adapting behavior: {e}")
            return {"error": str(e)}
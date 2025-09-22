"""
AI Training and Improvement System

This module provides comprehensive training capabilities for the OpsConductor AI,
including feedback collection, pattern optimization, and continuous learning.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class TrainingMode(Enum):
    """Training modes for the AI system"""
    PASSIVE = "passive"      # Learn from normal interactions
    ACTIVE = "active"        # Actively request feedback
    SUPERVISED = "supervised" # Human-guided training
    REINFORCEMENT = "reinforcement" # Reward-based learning

@dataclass
class TrainingSession:
    """Represents a training session"""
    session_id: str
    mode: TrainingMode
    start_time: datetime
    end_time: Optional[datetime] = None
    interactions_processed: int = 0
    feedback_collected: int = 0
    patterns_learned: int = 0
    accuracy_improvement: float = 0.0
    notes: str = ""

@dataclass
class UserInteractionPattern:
    """Represents a user interaction pattern for learning"""
    user_id: str
    common_intents: List[str]
    preferred_response_style: str
    typical_context: Dict[str, Any]
    success_rate: float
    last_interaction: datetime

class AITrainingSystem:
    """Comprehensive AI training and improvement system"""
    
    def __init__(self, conversation_handler, vector_store=None):
        self.conversation_handler = conversation_handler
        self.vector_store = vector_store
        self.training_sessions: List[TrainingSession] = []
        self.user_patterns: Dict[str, UserInteractionPattern] = {}
        self.training_config = self._initialize_training_config()
        
    def _initialize_training_config(self) -> Dict[str, Any]:
        """Initialize training configuration"""
        return {
            "feedback_request_frequency": 0.1,  # Request feedback on 10% of interactions
            "min_confidence_for_feedback": 0.3,  # Request feedback when confidence is low
            "pattern_update_threshold": 5,  # Update patterns after 5 similar interactions
            "training_batch_size": 20,  # Process training in batches
            "accuracy_target": 0.85,  # Target accuracy for intent recognition
            "learning_rate": 0.1,  # How quickly to adapt patterns
            "feedback_weight": 2.0,  # Weight of explicit feedback vs implicit signals
        }
    
    async def start_training_session(self, mode: TrainingMode, notes: str = "") -> str:
        """Start a new training session"""
        session_id = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = TrainingSession(
            session_id=session_id,
            mode=mode,
            start_time=datetime.now(),
            notes=notes
        )
        
        self.training_sessions.append(session)
        logger.info(f"Started training session {session_id} in {mode.value} mode")
        
        return session_id
    
    async def end_training_session(self, session_id: str) -> Dict[str, Any]:
        """End a training session and return results"""
        session = self._find_session(session_id)
        if not session:
            return {"error": "Training session not found"}
        
        session.end_time = datetime.now()
        
        # Calculate session statistics
        duration = (session.end_time - session.start_time).total_seconds()
        
        results = {
            "session_id": session_id,
            "duration_seconds": duration,
            "interactions_processed": session.interactions_processed,
            "feedback_collected": session.feedback_collected,
            "patterns_learned": session.patterns_learned,
            "accuracy_improvement": session.accuracy_improvement,
            "learning_rate": session.patterns_learned / max(session.interactions_processed, 1)
        }
        
        logger.info(f"Training session {session_id} completed: {results}")
        return results
    
    def _find_session(self, session_id: str) -> Optional[TrainingSession]:
        """Find a training session by ID"""
        for session in self.training_sessions:
            if session.session_id == session_id:
                return session
        return None
    
    async def process_interaction_for_learning(self, user_message: str, ai_response: str, 
                                             user_id: str, intent_analysis: Dict[str, Any],
                                             session_id: str = None) -> Dict[str, Any]:
        """Process an interaction for learning opportunities"""
        
        # Update session if active
        if session_id:
            session = self._find_session(session_id)
            if session and not session.end_time:
                session.interactions_processed += 1
        
        # Analyze interaction for learning opportunities
        learning_opportunities = await self._identify_learning_opportunities(
            user_message, ai_response, intent_analysis
        )
        
        # Update user patterns
        await self._update_user_patterns(user_id, user_message, intent_analysis)
        
        # Determine if feedback should be requested
        should_request_feedback = self._should_request_feedback(intent_analysis, learning_opportunities)
        
        result = {
            "learning_opportunities": learning_opportunities,
            "should_request_feedback": should_request_feedback,
            "confidence_level": intent_analysis.get("confidence_level", "unknown"),
            "suggested_improvements": []
        }
        
        # Add specific suggestions based on analysis
        if intent_analysis.get("confidence", 0) < 0.5:
            result["suggested_improvements"].append("Low confidence - consider requesting clarification")
        
        if len(intent_analysis.get("alternative_intents", [])) > 1:
            result["suggested_improvements"].append("Multiple possible intents - consider disambiguation")
        
        return result
    
    async def _identify_learning_opportunities(self, user_message: str, ai_response: str, 
                                             intent_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific learning opportunities from an interaction"""
        opportunities = []
        
        # Low confidence intent detection
        confidence = intent_analysis.get("confidence", 0)
        if confidence < 0.5:
            opportunities.append({
                "type": "low_confidence_intent",
                "description": f"Intent detection confidence is low ({confidence:.2f})",
                "priority": "high",
                "suggested_action": "Request user clarification or feedback"
            })
        
        # Ambiguous intent (multiple high-scoring alternatives)
        alternatives = intent_analysis.get("alternative_intents", [])
        if len(alternatives) > 1 and alternatives[0].get("confidence", 0) > 0.4:
            opportunities.append({
                "type": "ambiguous_intent",
                "description": "Multiple plausible intents detected",
                "priority": "medium",
                "suggested_action": "Improve disambiguation patterns",
                "alternatives": alternatives
            })
        
        # Unknown intent
        if intent_analysis.get("intent") == "unknown":
            opportunities.append({
                "type": "unknown_intent",
                "description": "No matching intent patterns found",
                "priority": "high",
                "suggested_action": "Create new intent pattern or improve existing ones",
                "suggestions": intent_analysis.get("suggestions", [])
            })
        
        # Complex or long user message
        if len(user_message.split()) > 20:
            opportunities.append({
                "type": "complex_message",
                "description": "User message is complex or lengthy",
                "priority": "low",
                "suggested_action": "Consider breaking down complex intents"
            })
        
        return opportunities
    
    async def _update_user_patterns(self, user_id: str, user_message: str, 
                                  intent_analysis: Dict[str, Any]) -> None:
        """Update patterns for a specific user"""
        
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = UserInteractionPattern(
                user_id=user_id,
                common_intents=[],
                preferred_response_style="standard",
                typical_context={},
                success_rate=0.0,
                last_interaction=datetime.now()
            )
        
        pattern = self.user_patterns[user_id]
        
        # Update common intents
        detected_intent = intent_analysis.get("intent", "unknown")
        if detected_intent != "unknown":
            if detected_intent not in pattern.common_intents:
                pattern.common_intents.append(detected_intent)
            elif len(pattern.common_intents) > 10:
                # Keep only the most recent 10 intents
                pattern.common_intents = pattern.common_intents[-10:]
        
        pattern.last_interaction = datetime.now()
    
    def _should_request_feedback(self, intent_analysis: Dict[str, Any], 
                               learning_opportunities: List[Dict[str, Any]]) -> bool:
        """Determine if feedback should be requested for this interaction"""
        
        # Always request feedback for unknown intents
        if intent_analysis.get("intent") == "unknown":
            return True
        
        # Request feedback for low confidence
        if intent_analysis.get("confidence", 0) < self.training_config["min_confidence_for_feedback"]:
            return True
        
        # Request feedback based on frequency setting
        import random
        if random.random() < self.training_config["feedback_request_frequency"]:
            return True
        
        # Request feedback if there are high-priority learning opportunities
        high_priority_opportunities = [
            opp for opp in learning_opportunities 
            if opp.get("priority") == "high"
        ]
        
        return len(high_priority_opportunities) > 0
    
    async def collect_user_feedback(self, interaction_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and process user feedback"""
        
        feedback_type = feedback_data.get("type", "general")  # general, intent_correction, satisfaction
        
        result = {"feedback_processed": True, "improvements_made": []}
        
        if feedback_type == "intent_correction":
            # User corrected the intent interpretation
            interpretation_id = feedback_data.get("interpretation_id")
            correct_intent = feedback_data.get("correct_intent")
            
            if interpretation_id and correct_intent:
                feedback_result = await self.conversation_handler.record_intent_feedback(
                    interpretation_id, False, correct_intent, feedback_data.get("comment", "")
                )
                result["improvements_made"].append("Updated intent patterns based on correction")
        
        elif feedback_type == "satisfaction":
            # User provided satisfaction rating
            rating = feedback_data.get("rating", 0)  # 1-5 scale
            
            if rating <= 2:  # Poor rating
                result["improvements_made"].append("Flagged interaction for review due to low satisfaction")
            elif rating >= 4:  # Good rating
                result["improvements_made"].append("Reinforced successful patterns")
        
        elif feedback_type == "suggestion":
            # User provided improvement suggestion
            suggestion = feedback_data.get("suggestion", "")
            if suggestion:
                result["improvements_made"].append(f"Recorded suggestion: {suggestion}")
        
        # Update training session if active
        active_sessions = [s for s in self.training_sessions if not s.end_time]
        for session in active_sessions:
            session.feedback_collected += 1
        
        logger.info(f"Processed user feedback: {feedback_type}")
        return result
    
    async def generate_training_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate a comprehensive training report"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get recent training sessions
        recent_sessions = [
            s for s in self.training_sessions 
            if s.start_time > cutoff_date
        ]
        
        # Get intent learning statistics
        intent_stats = await self.conversation_handler.get_intent_learning_stats()
        
        # Calculate overall metrics
        total_interactions = sum(s.interactions_processed for s in recent_sessions)
        total_feedback = sum(s.feedback_collected for s in recent_sessions)
        total_patterns_learned = sum(s.patterns_learned for s in recent_sessions)
        
        # User pattern analysis
        active_users = len([
            p for p in self.user_patterns.values() 
            if p.last_interaction > cutoff_date
        ])
        
        report = {
            "report_period_days": days,
            "generated_at": datetime.now().isoformat(),
            "training_sessions": {
                "total_sessions": len(recent_sessions),
                "total_interactions": total_interactions,
                "total_feedback_collected": total_feedback,
                "total_patterns_learned": total_patterns_learned,
                "feedback_rate": total_feedback / max(total_interactions, 1)
            },
            "intent_recognition": intent_stats,
            "user_engagement": {
                "active_users": active_users,
                "total_registered_patterns": len(self.user_patterns)
            },
            "recommendations": []
        }
        
        # Add recommendations based on analysis
        if intent_stats.get("overall_accuracy", 0) < self.training_config["accuracy_target"]:
            report["recommendations"].append(
                "Intent recognition accuracy is below target - consider more training"
            )
        
        if total_feedback / max(total_interactions, 1) < 0.05:
            report["recommendations"].append(
                "Low feedback rate - consider more active feedback collection"
            )
        
        if total_patterns_learned == 0:
            report["recommendations"].append(
                "No new patterns learned recently - review learning thresholds"
            )
        
        return report
    
    async def auto_optimize_system(self) -> Dict[str, Any]:
        """Automatically optimize the AI system based on performance data"""
        
        optimization_results = {
            "optimizations_applied": [],
            "performance_improvements": {},
            "recommendations": []
        }
        
        # Optimize intent patterns
        pattern_optimization = await self.conversation_handler.optimize_intent_patterns()
        optimization_results["optimizations_applied"].append("Intent pattern optimization")
        optimization_results["performance_improvements"]["patterns"] = pattern_optimization
        
        # Adjust training configuration based on performance
        intent_stats = await self.conversation_handler.get_intent_learning_stats()
        current_accuracy = intent_stats.get("overall_accuracy", 0)
        
        if current_accuracy < 0.7:
            # Increase feedback request frequency for low accuracy
            self.training_config["feedback_request_frequency"] = min(0.3, 
                self.training_config["feedback_request_frequency"] * 1.5)
            optimization_results["optimizations_applied"].append("Increased feedback request frequency")
        
        elif current_accuracy > 0.9:
            # Decrease feedback requests for high accuracy
            self.training_config["feedback_request_frequency"] = max(0.05,
                self.training_config["feedback_request_frequency"] * 0.8)
            optimization_results["optimizations_applied"].append("Decreased feedback request frequency")
        
        logger.info(f"Auto-optimization completed: {len(optimization_results['optimizations_applied'])} changes")
        return optimization_results
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """Get comprehensive training statistics"""
        
        total_sessions = len(self.training_sessions)
        completed_sessions = len([s for s in self.training_sessions if s.end_time])
        
        if completed_sessions > 0:
            avg_interactions = sum(s.interactions_processed for s in self.training_sessions) / completed_sessions
            avg_feedback = sum(s.feedback_collected for s in self.training_sessions) / completed_sessions
            avg_patterns = sum(s.patterns_learned for s in self.training_sessions) / completed_sessions
        else:
            avg_interactions = avg_feedback = avg_patterns = 0
        
        return {
            "total_training_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "active_sessions": total_sessions - completed_sessions,
            "average_interactions_per_session": avg_interactions,
            "average_feedback_per_session": avg_feedback,
            "average_patterns_learned_per_session": avg_patterns,
            "total_user_patterns": len(self.user_patterns),
            "current_training_config": self.training_config,
            "last_optimization": "Not implemented yet"  # Placeholder
        }
"""
OUIOE Knowledge Engine - Learning System
========================================

This module provides the core learning system for capturing and processing
user feedback, job outcomes, and learning patterns.

Author: OUIOE Development Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """Types of learning supported by the system"""
    USER_PREFERENCE = "user_preference"
    JOB_OUTCOME = "job_outcome"
    PATTERN_RECOGNITION = "pattern_recognition"
    BEHAVIORAL_ADAPTATION = "behavioral_adaptation"
    CONTEXT_AWARENESS = "context_awareness"
    FEEDBACK_INTEGRATION = "feedback_integration"


@dataclass
class JobOutcome:
    """Represents the outcome of a job execution"""
    job_id: str
    user_id: str
    job_type: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class UserFeedback:
    """Represents user feedback on system behavior"""
    user_id: str
    feedback_type: str
    rating: Optional[int] = None  # 1-5 scale
    comment: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class LearningSystem:
    """
    Core learning system that processes various types of learning data
    and adapts system behavior based on patterns and feedback.
    """
    
    def __init__(self):
        self.learning_data = []
        self.patterns = {}
        self.user_preferences = {}
        
    async def process_job_outcome(self, outcome: JobOutcome) -> Dict[str, Any]:
        """
        Process a job outcome and extract learning insights
        
        Args:
            outcome: JobOutcome instance containing job execution data
            
        Returns:
            Dict containing learning insights and recommendations
        """
        try:
            # Store the outcome
            self.learning_data.append({
                'type': LearningType.JOB_OUTCOME,
                'data': outcome,
                'timestamp': outcome.timestamp
            })
            
            # Analyze patterns
            insights = await self._analyze_job_patterns(outcome)
            
            logger.info(f"Processed job outcome for job {outcome.job_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Error processing job outcome: {e}")
            return {"error": str(e)}
    
    async def process_user_feedback(self, feedback: UserFeedback) -> Dict[str, Any]:
        """
        Process user feedback and update learning models
        
        Args:
            feedback: UserFeedback instance containing user input
            
        Returns:
            Dict containing processing results
        """
        try:
            # Store the feedback
            self.learning_data.append({
                'type': LearningType.FEEDBACK_INTEGRATION,
                'data': feedback,
                'timestamp': feedback.timestamp
            })
            
            # Update user preferences
            await self._update_user_preferences(feedback)
            
            logger.info(f"Processed feedback from user {feedback.user_id}")
            return {"status": "processed", "user_id": feedback.user_id}
            
        except Exception as e:
            logger.error(f"Error processing user feedback: {e}")
            return {"error": str(e)}
    
    async def learn_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from a specific pattern in the data
        
        Args:
            pattern_type: Type of pattern being learned
            pattern_data: Data representing the pattern
            
        Returns:
            Dict containing learning results
        """
        try:
            # Store pattern learning
            self.learning_data.append({
                'type': LearningType.PATTERN_RECOGNITION,
                'pattern_type': pattern_type,
                'data': pattern_data,
                'timestamp': datetime.utcnow()
            })
            
            # Update pattern knowledge
            if pattern_type not in self.patterns:
                self.patterns[pattern_type] = []
            
            self.patterns[pattern_type].append(pattern_data)
            
            logger.info(f"Learned pattern of type {pattern_type}")
            return {"status": "learned", "pattern_type": pattern_type}
            
        except Exception as e:
            logger.error(f"Error learning pattern: {e}")
            return {"error": str(e)}
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get learned preferences for a specific user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict containing user preferences
        """
        return self.user_preferences.get(user_id, {})
    
    async def get_patterns(self, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get learned patterns, optionally filtered by type
        
        Args:
            pattern_type: Optional pattern type filter
            
        Returns:
            Dict containing patterns
        """
        if pattern_type:
            return {pattern_type: self.patterns.get(pattern_type, [])}
        return self.patterns
    
    async def _analyze_job_patterns(self, outcome: JobOutcome) -> Dict[str, Any]:
        """Analyze job outcome patterns"""
        # Simple pattern analysis - can be enhanced
        user_jobs = [
            item for item in self.learning_data 
            if (item.get('type') == LearningType.JOB_OUTCOME and 
                item.get('data', {}).user_id == outcome.user_id)
        ]
        
        success_rate = sum(1 for job in user_jobs if job.get('data', {}).success) / max(len(user_jobs), 1)
        
        return {
            "user_id": outcome.user_id,
            "job_type": outcome.job_type,
            "success_rate": success_rate,
            "total_jobs": len(user_jobs),
            "insights": [
                f"User has {success_rate:.1%} success rate for {outcome.job_type} jobs"
            ]
        }
    
    async def _update_user_preferences(self, feedback: UserFeedback):
        """Update user preferences based on feedback"""
        if feedback.user_id not in self.user_preferences:
            self.user_preferences[feedback.user_id] = {}
        
        user_prefs = self.user_preferences[feedback.user_id]
        
        # Update preferences based on feedback
        if feedback.rating:
            if 'average_rating' not in user_prefs:
                user_prefs['average_rating'] = feedback.rating
                user_prefs['rating_count'] = 1
            else:
                total = user_prefs['average_rating'] * user_prefs['rating_count']
                user_prefs['rating_count'] += 1
                user_prefs['average_rating'] = (total + feedback.rating) / user_prefs['rating_count']
        
        if feedback.feedback_type not in user_prefs:
            user_prefs[feedback.feedback_type] = []
        user_prefs[feedback.feedback_type].append({
            'comment': feedback.comment,
            'context': feedback.context,
            'timestamp': feedback.timestamp
        })
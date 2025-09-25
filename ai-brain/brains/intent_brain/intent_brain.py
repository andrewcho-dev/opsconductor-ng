"""
Simple Intent Brain - Understanding what the user wants

This brain has one job: Use LLM intelligence to understand what the user wants.
No complex frameworks, no JSON parsing, no unnecessary complexity.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .intent_analyzer import IntentAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class IntentAnalysisResult:
    """Simple intent analysis result"""
    intent_id: str
    user_message: str
    timestamp: datetime
    user_intent: str  # What the user wants in plain language
    needs_clarification: bool
    clarifying_questions: list[str]
    processing_time: float
    brain_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "intent_id": self.intent_id,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "user_intent": self.user_intent,
            "needs_clarification": self.needs_clarification,
            "clarifying_questions": self.clarifying_questions,
            "processing_time": self.processing_time,
            "brain_version": self.brain_version
        }


class IntentBrain:
    """
    Simple Intent Brain - Understanding what the user wants
    
    This brain uses LLM intelligence to understand user intent in plain language.
    No complex frameworks, just: What does the user want?
    """
    
    def __init__(self, llm_engine=None):
        """Initialize the Intent Brain."""
        self.brain_id = "intent_brain"
        self.version = "3.0.0"  # Simplified version
        self.llm_engine = llm_engine
        
        # Initialize the simple intent analyzer
        self.intent_analyzer = IntentAnalyzer(llm_engine)
        
        logger.info(f"Simple Intent Brain v{self.version} initialized")
    
    async def analyze_intent(self, user_message: str, 
                           context: Optional[Dict] = None) -> IntentAnalysisResult:
        """
        Analyze user intent - understand what they want.
        
        Args:
            user_message: The user's natural language request
            context: Optional context information
            
        Returns:
            IntentAnalysisResult with what the user wants
        """
        start_time = datetime.now()
        intent_id = f"intent_{int(start_time.timestamp())}"
        
        try:
            logger.info(f"Intent Brain analyzing: {user_message[:100]}...")
            
            # Understand what the user wants
            user_intent = await self.intent_analyzer.understand_user_intent(user_message, context)
            
            # Check if we need clarification
            needs_clarification, clarifying_questions = await self.intent_analyzer.needs_clarification(user_message, context)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = IntentAnalysisResult(
                intent_id=intent_id,
                user_message=user_message,
                timestamp=start_time,
                user_intent=user_intent,
                needs_clarification=needs_clarification,
                clarifying_questions=clarifying_questions,
                processing_time=processing_time,
                brain_version=self.version
            )
            
            logger.info(f"Intent analysis completed in {processing_time:.2f}s")
            logger.info(f"User wants: {user_intent}")
            
            if needs_clarification:
                logger.info(f"Clarification needed: {clarifying_questions}")
            
            return result
            
        except Exception as e:
            logger.error(f"Intent Brain analysis failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # NO FALLBACK - FAIL HARD
            raise Exception(f"Intent Brain analysis FAILED: {e}")
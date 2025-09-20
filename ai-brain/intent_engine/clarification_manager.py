"""
AI Clarification Manager - Interactive requirement gathering

This module manages the clarification process when AI requests are incomplete
or ambiguous, ensuring complete requirements before job generation.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .conversation_manager import ConversationManager, Conversation, ConversationMessage, MessageType
from .natural_language_understanding import Intent, IntentType

logger = logging.getLogger(__name__)

class ClarificationState(Enum):
    """States of clarification process"""
    GATHERING_REQUIREMENTS = "gathering_requirements"
    CONFIRMING_DETAILS = "confirming_details"
    READY_FOR_GENERATION = "ready_for_generation"
    CANCELLED = "cancelled"

@dataclass
class ClarificationContext:
    """Context for clarification process"""
    original_request: str
    intent_type: IntentType
    collected_requirements: Dict[str, Any]
    missing_requirements: List[str]
    clarification_questions: List[Dict[str, Any]]
    current_question_index: int = 0
    state: ClarificationState = ClarificationState.GATHERING_REQUIREMENTS
    confidence_threshold: float = 0.8

class ClarificationManager:
    """Manages interactive clarification for incomplete AI requests"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.conversation_manager = conversation_manager
        self.active_clarifications: Dict[str, ClarificationContext] = {}
        
    def needs_clarification(
        self,
        intent: Intent,
        requirements: Dict[str, Any],
        confidence_score: float,
        missing_requirements: List[str]
    ) -> bool:
        """
        Determine if request needs clarification
        
        Args:
            intent: Parsed intent
            requirements: Extracted requirements
            confidence_score: Confidence in understanding
            missing_requirements: List of missing required fields
            
        Returns:
            True if clarification is needed
        """
        # Need clarification if:
        # 1. Confidence is too low
        # 2. Missing critical requirements
        # 3. Ambiguous intent
        
        return (
            confidence_score < 0.7 or
            len(missing_requirements) > 0 or
            intent.type == IntentType.UNKNOWN or
            self._has_ambiguous_requirements(requirements)
        )
    
    def start_clarification(
        self,
        conversation_id: str,
        original_request: str,
        intent: Intent,
        requirements: Dict[str, Any],
        missing_requirements: List[str],
        clarification_questions: List[Dict[str, Any]]
    ) -> str:
        """
        Start clarification process for a conversation
        
        Args:
            conversation_id: ID of the conversation
            original_request: Original user request
            intent: Parsed intent
            requirements: Current requirements
            missing_requirements: Missing required fields
            clarification_questions: Generated questions
            
        Returns:
            Clarification response message
        """
        try:
            # Create clarification context
            context = ClarificationContext(
                original_request=original_request,
                intent_type=intent.type,
                collected_requirements=requirements.copy(),
                missing_requirements=missing_requirements.copy(),
                clarification_questions=clarification_questions.copy()
            )
            
            self.active_clarifications[conversation_id] = context
            
            # Generate first clarification message
            return self._generate_clarification_message(context)
            
        except Exception as e:
            logger.error(f"Failed to start clarification: {e}")
            return "I need more information to help you, but I'm having trouble processing your request. Could you please rephrase it?"
    
    def process_clarification_response(
        self,
        conversation_id: str,
        user_response: str,
        parsed_intent: Intent
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process user's response to clarification question
        
        Args:
            conversation_id: ID of the conversation
            user_response: User's response
            parsed_intent: Parsed intent from response
            
        Returns:
            Tuple of (is_complete, response_message, final_requirements)
        """
        try:
            context = self.active_clarifications.get(conversation_id)
            if not context:
                return False, "I couldn't find our clarification context. Let's start over.", None
            
            # Process the response
            self._process_user_answer(context, user_response, parsed_intent)
            
            # Check if we have more questions
            if context.current_question_index < len(context.clarification_questions):
                # Ask next question
                response = self._generate_clarification_message(context)
                return False, response, None
            
            # Check if we have all requirements now
            if len(context.missing_requirements) == 0:
                # Clarification complete
                context.state = ClarificationState.READY_FOR_GENERATION
                
                # Generate confirmation message
                confirmation = self._generate_confirmation_message(context)
                
                return True, confirmation, context.collected_requirements
            else:
                # Still missing requirements, generate additional questions
                additional_questions = self._generate_additional_questions(context)
                if additional_questions:
                    context.clarification_questions.extend(additional_questions)
                    response = self._generate_clarification_message(context)
                    return False, response, None
                else:
                    # Can't generate more questions, proceed with what we have
                    context.state = ClarificationState.READY_FOR_GENERATION
                    warning_msg = self._generate_incomplete_confirmation(context)
                    return True, warning_msg, context.collected_requirements
            
        except Exception as e:
            logger.error(f"Failed to process clarification response: {e}")
            return False, "I had trouble understanding your response. Could you please try again?", None
    
    def _generate_clarification_message(self, context: ClarificationContext) -> str:
        """Generate clarification question message"""
        if context.current_question_index >= len(context.clarification_questions):
            return "I think I have all the information I need now."
        
        question_data = context.clarification_questions[context.current_question_index]
        question = question_data.get('question', 'Could you provide more details?')
        options = question_data.get('options', [])
        
        message = f"To help you with '{context.original_request}', I need to clarify:\n\n"
        message += f"**{question}**\n"
        
        if options:
            message += "\nPlease choose from:\n"
            for i, option in enumerate(options, 1):
                message += f"{i}. {option}\n"
            message += "\nOr describe your specific needs."
        
        return message
    
    def _process_user_answer(
        self,
        context: ClarificationContext,
        user_response: str,
        parsed_intent: Intent
    ):
        """Process user's answer to current question"""
        if context.current_question_index >= len(context.clarification_questions):
            return
        
        question_data = context.clarification_questions[context.current_question_index]
        field = question_data.get('field', 'unknown')
        
        # Extract answer from user response
        answer = self._extract_answer(user_response, question_data, parsed_intent)
        
        if answer:
            # Store the answer
            context.collected_requirements[field] = answer
            
            # Remove from missing requirements if present
            if field in context.missing_requirements:
                context.missing_requirements.remove(field)
        
        # Move to next question
        context.current_question_index += 1
    
    def _extract_answer(
        self,
        user_response: str,
        question_data: Dict[str, Any],
        parsed_intent: Intent
    ) -> Optional[str]:
        """Extract answer from user response"""
        options = question_data.get('options', [])
        question_type = question_data.get('type', 'open')
        
        # Check if user selected a numbered option
        for i, option in enumerate(options, 1):
            if str(i) in user_response or option.lower() in user_response.lower():
                return option
        
        # Extract from entities if available
        for entity in parsed_intent.entities:
            if entity.value and len(entity.value.strip()) > 0:
                return entity.value
        
        # Use the full response as answer for open questions
        if question_type == 'open' and len(user_response.strip()) > 0:
            return user_response.strip()
        
        return None
    
    def _generate_confirmation_message(self, context: ClarificationContext) -> str:
        """Generate confirmation message with collected requirements"""
        message = "Perfect! I now have all the information I need:\n\n"
        
        for field, value in context.collected_requirements.items():
            if value:
                field_name = field.replace('_', ' ').title()
                message += f"• **{field_name}**: {value}\n"
        
        message += "\nShould I proceed to create and execute this automation job?"
        
        return message
    
    def _generate_incomplete_confirmation(self, context: ClarificationContext) -> str:
        """Generate confirmation when some requirements are still missing"""
        message = "I'll proceed with the information I have:\n\n"
        
        for field, value in context.collected_requirements.items():
            if value:
                field_name = field.replace('_', ' ').title()
                message += f"• **{field_name}**: {value}\n"
        
        if context.missing_requirements:
            message += f"\n⚠️ **Note**: Some details are still unclear: {', '.join(context.missing_requirements)}\n"
            message += "I'll use reasonable defaults where possible.\n"
        
        message += "\nShould I proceed to create this automation job?"
        
        return message
    
    def _generate_additional_questions(self, context: ClarificationContext) -> List[Dict[str, Any]]:
        """Generate additional questions for remaining missing requirements"""
        questions = []
        
        for missing_field in context.missing_requirements:
            question = self._create_question_for_field(missing_field, context.intent_type)
            if question:
                questions.append(question)
        
        return questions
    
    def _create_question_for_field(self, field: str, intent_type: IntentType) -> Optional[Dict[str, Any]]:
        """Create a clarification question for a specific field"""
        field_questions = {
            'target_systems': {
                'question': 'Which systems should I target for this operation?',
                'options': ['All servers', 'Web servers', 'Database servers', 'Development servers'],
                'type': 'single_choice',
                'field': 'target_systems'
            },
            'service_name': {
                'question': 'Which service do you want to manage?',
                'options': ['IIS', 'Apache', 'SQL Server', 'MySQL', 'Windows Service'],
                'type': 'single_choice',
                'field': 'service_name'
            },
            'operation': {
                'question': 'What specific operation should I perform?',
                'options': ['Start', 'Stop', 'Restart', 'Status Check', 'Install', 'Update'],
                'type': 'single_choice',
                'field': 'operation'
            },
            'file_path': {
                'question': 'What file or directory path should I work with?',
                'options': [],
                'type': 'open',
                'field': 'file_path'
            },
            'username': {
                'question': 'Which user account should I manage?',
                'options': [],
                'type': 'open',
                'field': 'username'
            }
        }
        
        return field_questions.get(field)
    
    def _has_ambiguous_requirements(self, requirements: Dict[str, Any]) -> bool:
        """Check if requirements are ambiguous"""
        # Check for vague terms
        vague_terms = ['something', 'anything', 'stuff', 'things', 'some', 'maybe']
        
        for value in requirements.values():
            if isinstance(value, str):
                if any(term in value.lower() for term in vague_terms):
                    return True
        
        return False
    
    def cancel_clarification(self, conversation_id: str) -> str:
        """Cancel ongoing clarification"""
        if conversation_id in self.active_clarifications:
            del self.active_clarifications[conversation_id]
        
        return "Clarification cancelled. Feel free to ask me anything else!"
    
    def get_clarification_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of ongoing clarification"""
        context = self.active_clarifications.get(conversation_id)
        if not context:
            return None
        
        return {
            'state': context.state.value,
            'progress': f"{context.current_question_index}/{len(context.clarification_questions)}",
            'collected_requirements': context.collected_requirements,
            'missing_requirements': context.missing_requirements
        }
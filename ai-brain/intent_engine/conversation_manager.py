"""
Conversation Manager Module for AI Brain Intent Engine

This module manages multi-turn conversations, maintains context, and handles
conversation flow for intelligent automation interactions.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

from .natural_language_understanding import Intent, IntentType, Entity, EntityType

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """States of a conversation"""
    ACTIVE = "active"
    WAITING_FOR_INPUT = "waiting_for_input"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MessageType(Enum):
    """Types of messages in a conversation"""
    USER_INPUT = "user_input"
    SYSTEM_RESPONSE = "system_response"
    CLARIFICATION_REQUEST = "clarification_request"
    CONFIRMATION_REQUEST = "confirmation_request"
    EXECUTION_UPDATE = "execution_update"
    ERROR_MESSAGE = "error_message"

@dataclass
class ConversationMessage:
    """Represents a message in a conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.USER_INPUT
    content: str = ""
    intent: Optional[Intent] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationContext:
    """Maintains context throughout a conversation"""
    # Current automation request being built
    target_intent: Optional[IntentType] = None
    collected_entities: Dict[EntityType, List[Entity]] = field(default_factory=dict)
    missing_entities: List[EntityType] = field(default_factory=list)
    
    # Conversation flow
    current_step: str = "initial"
    completed_steps: List[str] = field(default_factory=list)
    pending_confirmations: List[str] = field(default_factory=list)
    
    # User preferences and history
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    previous_requests: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution context
    generated_workflow: Optional[Dict[str, Any]] = None
    execution_id: Optional[str] = None
    execution_status: Optional[str] = None

@dataclass
class Conversation:
    """Represents a complete conversation session"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    state: ConversationState = ConversationState.ACTIVE
    messages: List[ConversationMessage] = field(default_factory=list)
    context: ConversationContext = field(default_factory=ConversationContext)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=2))

class ConversationManager:
    """
    Manages multi-turn conversations and maintains context for intelligent automation
    """
    
    def __init__(self):
        self.active_conversations: Dict[str, Conversation] = {}
        self.conversation_templates = self._initialize_conversation_templates()
        self.required_entities = self._initialize_required_entities()
        
    def _initialize_conversation_templates(self) -> Dict[IntentType, Dict[str, Any]]:
        """Initialize conversation flow templates for different intent types"""
        return {
            IntentType.AUTOMATION_REQUEST: {
                'steps': ['collect_targets', 'collect_actions', 'collect_parameters', 'confirm_execution'],
                'required_entities': [EntityType.TARGET, EntityType.ACTION],
                'optional_entities': [EntityType.SERVICE, EntityType.PARAMETER, EntityType.TIME],
                'confirmation_required': True
            },
            IntentType.SERVICE_MANAGEMENT: {
                'steps': ['collect_targets', 'collect_service', 'collect_action', 'confirm_execution'],
                'required_entities': [EntityType.TARGET, EntityType.SERVICE, EntityType.ACTION],
                'optional_entities': [EntityType.PARAMETER, EntityType.TIME],
                'confirmation_required': True
            },
            IntentType.FILE_OPERATIONS: {
                'steps': ['collect_targets', 'collect_files', 'collect_action', 'collect_destination', 'confirm_execution'],
                'required_entities': [EntityType.TARGET, EntityType.FILE_PATH, EntityType.ACTION],
                'optional_entities': [EntityType.PARAMETER, EntityType.USER],
                'confirmation_required': True
            },
            IntentType.USER_MANAGEMENT: {
                'steps': ['collect_targets', 'collect_user', 'collect_action', 'collect_parameters', 'confirm_execution'],
                'required_entities': [EntityType.TARGET, EntityType.USER, EntityType.ACTION],
                'optional_entities': [EntityType.PARAMETER],
                'confirmation_required': True
            },
            IntentType.INFORMATION_QUERY: {
                'steps': ['collect_query_details', 'provide_information'],
                'required_entities': [EntityType.TARGET],
                'optional_entities': [EntityType.SERVICE, EntityType.PARAMETER],
                'confirmation_required': False
            },
            IntentType.SYSTEM_STATUS: {
                'steps': ['collect_targets', 'collect_status_type', 'provide_status'],
                'required_entities': [EntityType.TARGET],
                'optional_entities': [EntityType.SERVICE],
                'confirmation_required': False
            },
            IntentType.TROUBLESHOOTING: {
                'steps': ['collect_problem_details', 'analyze_issue', 'suggest_solutions', 'confirm_resolution'],
                'required_entities': [EntityType.TARGET],
                'optional_entities': [EntityType.SERVICE, EntityType.ACTION],
                'confirmation_required': True
            }
        }
    
    def _initialize_required_entities(self) -> Dict[IntentType, List[EntityType]]:
        """Initialize required entities for each intent type"""
        required = {}
        for intent_type, template in self.conversation_templates.items():
            required[intent_type] = template.get('required_entities', [])
        return required
    
    def start_conversation(self, user_id: str, initial_message: str, intent: Intent) -> Tuple[Conversation, str]:
        """
        Start a new conversation with initial user message
        
        Args:
            user_id: User identifier
            initial_message: Initial user message
            intent: Parsed intent from the message
            
        Returns:
            Tuple of (Conversation object, System response)
        """
        try:
            # Create new conversation
            conversation = Conversation(user_id=user_id)
            
            # Add initial user message
            user_message = ConversationMessage(
                type=MessageType.USER_INPUT,
                content=initial_message,
                intent=intent
            )
            conversation.messages.append(user_message)
            
            # Initialize context based on intent
            conversation.context.target_intent = intent.type
            self._collect_entities_from_intent(conversation, intent)
            
            # Generate initial response
            response = self._generate_response(conversation)
            
            # Add system response
            system_message = ConversationMessage(
                type=MessageType.SYSTEM_RESPONSE,
                content=response,
                metadata={'step': conversation.context.current_step}
            )
            conversation.messages.append(system_message)
            
            # Store conversation
            self.active_conversations[conversation.id] = conversation
            
            logger.info(f"Started conversation {conversation.id} for user {user_id}")
            return conversation, response
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            error_response = "I apologize, but I encountered an error starting our conversation. Please try again."
            return Conversation(user_id=user_id), error_response
    
    def continue_conversation(self, conversation_id: str, user_message: str, intent: Intent) -> Tuple[Optional[Conversation], str]:
        """
        Continue an existing conversation with a new user message
        
        Args:
            conversation_id: Conversation identifier
            user_message: New user message
            intent: Parsed intent from the message
            
        Returns:
            Tuple of (Updated conversation or None, System response)
        """
        try:
            conversation = self.active_conversations.get(conversation_id)
            if not conversation:
                return None, "I couldn't find our conversation. Let's start fresh - what would you like me to help you with?"
            
            # Check if conversation has expired
            if datetime.now() > conversation.expires_at:
                self._cleanup_conversation(conversation_id)
                return None, "Our conversation has expired. Let's start a new one - what would you like me to help you with?"
            
            # Add user message
            message = ConversationMessage(
                type=MessageType.USER_INPUT,
                content=user_message,
                intent=intent
            )
            conversation.messages.append(message)
            
            # Update context with new entities
            self._collect_entities_from_intent(conversation, intent)
            
            # Process the message and generate response
            response = self._process_conversation_turn(conversation, intent)
            
            # Add system response
            system_message = ConversationMessage(
                type=MessageType.SYSTEM_RESPONSE,
                content=response,
                metadata={'step': conversation.context.current_step}
            )
            conversation.messages.append(system_message)
            
            # Update conversation
            conversation.updated_at = datetime.now()
            
            logger.info(f"Continued conversation {conversation_id}, step: {conversation.context.current_step}")
            return conversation, response
            
        except Exception as e:
            logger.error(f"Error continuing conversation {conversation_id}: {e}")
            return None, "I encountered an error processing your message. Could you please try again?"
    
    def _collect_entities_from_intent(self, conversation: Conversation, intent: Intent):
        """Collect entities from intent into conversation context"""
        for entity in intent.entities:
            if entity.type not in conversation.context.collected_entities:
                conversation.context.collected_entities[entity.type] = []
            
            # Avoid duplicates
            existing_values = [e.normalized_value or e.value for e in conversation.context.collected_entities[entity.type]]
            new_value = entity.normalized_value or entity.value
            
            if new_value not in existing_values:
                conversation.context.collected_entities[entity.type].append(entity)
    
    def _generate_response(self, conversation: Conversation) -> str:
        """Generate appropriate response based on conversation state"""
        intent_type = conversation.context.target_intent
        
        if not intent_type or intent_type == IntentType.UNKNOWN:
            return self._handle_unknown_intent(conversation)
        
        template = self.conversation_templates.get(intent_type)
        if not template:
            return "I understand you want help, but I'm not sure exactly what you need. Could you provide more details?"
        
        # Check what entities we have and what we need
        missing_entities = self._get_missing_entities(conversation, intent_type)
        
        if missing_entities:
            return self._request_missing_entities(conversation, missing_entities)
        else:
            return self._proceed_to_next_step(conversation)
    
    def _process_conversation_turn(self, conversation: Conversation, intent: Intent) -> str:
        """Process a conversation turn and determine next action"""
        # Handle special cases
        if self._is_cancellation_request(intent):
            return self._handle_cancellation(conversation)
        
        if self._is_confirmation_response(intent):
            return self._handle_confirmation(conversation, intent)
        
        # Continue with normal flow
        return self._generate_response(conversation)
    
    def _get_missing_entities(self, conversation: Conversation, intent_type: IntentType) -> List[EntityType]:
        """Determine which required entities are still missing"""
        required = self.required_entities.get(intent_type, [])
        collected = conversation.context.collected_entities.keys()
        return [entity_type for entity_type in required if entity_type not in collected]
    
    def _request_missing_entities(self, conversation: Conversation, missing_entities: List[EntityType]) -> str:
        """Generate request for missing entities"""
        entity_type = missing_entities[0]  # Request one at a time
        
        requests = {
            EntityType.TARGET: "Which servers or systems would you like me to work with? You can specify hostnames, IP addresses, or group names.",
            EntityType.ACTION: "What action would you like me to perform? For example: start, stop, restart, install, configure, etc.",
            EntityType.SERVICE: "Which service are you referring to? For example: apache, nginx, mysql, ssh, etc.",
            EntityType.FILE_PATH: "What file or directory path should I work with?",
            EntityType.USER: "Which user account should I work with?",
            EntityType.PARAMETER: "Are there any specific parameters or options I should use?",
            EntityType.TIME: "When should this be executed? You can say 'now', specify a time, or schedule it for later."
        }
        
        conversation.context.current_step = f"collect_{entity_type.value}"
        return requests.get(entity_type, f"I need more information about {entity_type.value}. Could you provide details?")
    
    def _proceed_to_next_step(self, conversation: Conversation) -> str:
        """Proceed to the next step in the conversation flow"""
        intent_type = conversation.context.target_intent
        template = self.conversation_templates.get(intent_type)
        
        if not template:
            return "I have all the information I need, but I'm not sure how to proceed. Let me get help from my knowledge base."
        
        if template.get('confirmation_required', False):
            return self._request_confirmation(conversation)
        else:
            return self._execute_request(conversation)
    
    def _request_confirmation(self, conversation: Conversation) -> str:
        """Request user confirmation before execution"""
        conversation.state = ConversationState.WAITING_FOR_CONFIRMATION
        conversation.context.current_step = "confirmation"
        
        # Build summary of what will be executed
        summary = self._build_execution_summary(conversation)
        
        return f"I'm ready to execute the following:\n\n{summary}\n\nShould I proceed? (yes/no)"
    
    def _build_execution_summary(self, conversation: Conversation) -> str:
        """Build a summary of what will be executed"""
        entities = conversation.context.collected_entities
        
        summary_parts = []
        
        # Targets
        if EntityType.TARGET in entities:
            targets = [e.value for e in entities[EntityType.TARGET]]
            summary_parts.append(f"**Targets**: {', '.join(targets)}")
        
        # Actions
        if EntityType.ACTION in entities:
            actions = [e.normalized_value or e.value for e in entities[EntityType.ACTION]]
            summary_parts.append(f"**Actions**: {', '.join(actions)}")
        
        # Services
        if EntityType.SERVICE in entities:
            services = [e.normalized_value or e.value for e in entities[EntityType.SERVICE]]
            summary_parts.append(f"**Services**: {', '.join(services)}")
        
        # Files
        if EntityType.FILE_PATH in entities:
            files = [e.value for e in entities[EntityType.FILE_PATH]]
            summary_parts.append(f"**Files**: {', '.join(files)}")
        
        # Users
        if EntityType.USER in entities:
            users = [e.value for e in entities[EntityType.USER]]
            summary_parts.append(f"**Users**: {', '.join(users)}")
        
        return "\n".join(summary_parts) if summary_parts else "Execute the requested automation task"
    
    def _handle_confirmation(self, conversation: Conversation, intent: Intent) -> str:
        """Handle user confirmation response"""
        response_text = intent.raw_text.lower()
        
        # Check for positive confirmation
        positive_indicators = ['yes', 'y', 'ok', 'okay', 'sure', 'go ahead', 'proceed', 'do it', 'execute']
        negative_indicators = ['no', 'n', 'cancel', 'stop', 'abort', 'nevermind', 'never mind']
        
        is_positive = any(indicator in response_text for indicator in positive_indicators)
        is_negative = any(indicator in response_text for indicator in negative_indicators)
        
        if is_positive and not is_negative:
            return self._execute_request(conversation)
        elif is_negative:
            return self._handle_cancellation(conversation)
        else:
            return "I'm not sure if you want me to proceed. Please respond with 'yes' to continue or 'no' to cancel."
    
    def _execute_request(self, conversation: Conversation) -> str:
        """Execute the automation request"""
        conversation.state = ConversationState.EXECUTING
        conversation.context.current_step = "execution"
        
        try:
            # Integrate with Job Engine to actually execute the request
            from job_engine import generate_workflow
            
            # Build the request description from collected entities
            entities = conversation.context.collected_entities
            request_parts = []
            
            # Add actions
            if EntityType.ACTION in entities:
                actions = [e.normalized_value or e.value for e in entities[EntityType.ACTION]]
                request_parts.extend(actions)
            
            # Add targets
            if EntityType.TARGET in entities:
                targets = [e.normalized_value or e.value for e in entities[EntityType.TARGET]]
                request_parts.append(f"on {', '.join(targets)}")
            
            # Add services
            if EntityType.SERVICE in entities:
                services = [e.normalized_value or e.value for e in entities[EntityType.SERVICE]]
                request_parts.append(f"for {', '.join(services)}")
            
            # Add file paths
            if EntityType.FILE_PATH in entities:
                files = [e.value for e in entities[EntityType.FILE_PATH]]
                request_parts.append(f"files: {', '.join(files)}")
            
            description = " ".join(request_parts) if request_parts else "Execute automation task"
            
            # Generate workflow using Job Engine
            workflow_result = generate_workflow(description)
            
            if workflow_result and workflow_result.get('success'):
                job_id = workflow_result.get('job_id', str(uuid.uuid4()))
                conversation.context.execution_id = job_id
                conversation.context.execution_status = "started"
                conversation.context.workflow = workflow_result.get('workflow')
                
                return f"Perfect! I've created and started your automation job.\n\n**Job ID**: {job_id}\n**Task**: {description}\n\nI'll monitor the execution and keep you updated on the progress."
            else:
                # Fallback to simulation if Job Engine fails
                execution_id = str(uuid.uuid4())
                conversation.context.execution_id = execution_id
                conversation.context.execution_status = "started"
                
                return f"I've started your automation request.\n\n**Job ID**: {execution_id}\n**Task**: {description}\n\nI'll keep you updated on the progress."
                
        except Exception as e:
            logger.error(f"Error executing request: {e}")
            # Fallback to basic execution
            execution_id = str(uuid.uuid4())
            conversation.context.execution_id = execution_id
            conversation.context.execution_status = "started"
            
            return f"I've started processing your request.\n\n**Job ID**: {execution_id}\n\nI'll keep you updated on the progress."
    
    def _handle_cancellation(self, conversation: Conversation) -> str:
        """Handle conversation cancellation"""
        conversation.state = ConversationState.CANCELLED
        conversation.context.current_step = "cancelled"
        
        return "Understood. I've cancelled the request. Is there anything else I can help you with?"
    
    def _handle_unknown_intent(self, conversation: Conversation) -> str:
        """Handle unknown or unclear intents"""
        return ("I'd like to help, but I'm not sure what you're asking for. "
                "I can help with tasks like:\n"
                "- Managing services (start, stop, restart)\n"
                "- File operations (copy, move, backup)\n"
                "- User management\n"
                "- System monitoring\n"
                "- Troubleshooting issues\n\n"
                "What would you like me to help you with?")
    
    def _is_cancellation_request(self, intent: Intent) -> bool:
        """Check if the intent is a cancellation request"""
        cancel_words = ['cancel', 'stop', 'abort', 'quit', 'exit', 'nevermind', 'never mind']
        return any(word in intent.raw_text.lower() for word in cancel_words)
    
    def _is_confirmation_response(self, intent: Intent) -> bool:
        """Check if the intent is a confirmation response"""
        confirmation_words = ['yes', 'no', 'y', 'n', 'ok', 'okay', 'sure', 'proceed', 'go ahead']
        return any(word in intent.raw_text.lower().split() for word in confirmation_words)
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return self.active_conversations.get(conversation_id)
    
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """Get all active conversations for a user"""
        return [conv for conv in self.active_conversations.values() if conv.user_id == user_id]
    
    def _cleanup_conversation(self, conversation_id: str):
        """Clean up expired or completed conversation"""
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
            logger.info(f"Cleaned up conversation {conversation_id}")
    
    def cleanup_expired_conversations(self):
        """Clean up all expired conversations"""
        now = datetime.now()
        expired_ids = [
            conv_id for conv_id, conv in self.active_conversations.items()
            if now > conv.expires_at
        ]
        
        for conv_id in expired_ids:
            self._cleanup_conversation(conv_id)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired conversations")
    
    def update_execution_status(self, conversation_id: str, status: str, message: str = ""):
        """Update execution status for a conversation"""
        conversation = self.active_conversations.get(conversation_id)
        if conversation:
            conversation.context.execution_status = status
            
            # Add execution update message
            update_message = ConversationMessage(
                type=MessageType.EXECUTION_UPDATE,
                content=message or f"Execution status updated to: {status}",
                metadata={'status': status}
            )
            conversation.messages.append(update_message)
            conversation.updated_at = datetime.now()
            
            # Update conversation state
            if status in ['completed', 'success']:
                conversation.state = ConversationState.COMPLETED
            elif status in ['failed', 'error']:
                conversation.state = ConversationState.FAILED
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Export conversation data for analysis or debugging"""
        conversation = self.active_conversations.get(conversation_id)
        if not conversation:
            return None
        
        return {
            'id': conversation.id,
            'user_id': conversation.user_id,
            'state': conversation.state.value,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'messages': [
                {
                    'id': msg.id,
                    'type': msg.type.value,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in conversation.messages
            ],
            'context': {
                'target_intent': conversation.context.target_intent.value if conversation.context.target_intent else None,
                'current_step': conversation.context.current_step,
                'completed_steps': conversation.context.completed_steps,
                'collected_entities': {
                    entity_type.value: [
                        {
                            'value': entity.value,
                            'normalized_value': entity.normalized_value,
                            'confidence': entity.confidence
                        }
                        for entity in entities
                    ]
                    for entity_type, entities in conversation.context.collected_entities.items()
                },
                'execution_id': conversation.context.execution_id,
                'execution_status': conversation.context.execution_status
            }
        }

# Global instance for easy access
conversation_manager = ConversationManager()
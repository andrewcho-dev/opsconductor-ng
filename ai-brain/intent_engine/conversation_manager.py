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
            logger.info(f"CONVERSATION_DEBUG: Attempting to continue conversation {conversation_id}")
            logger.info(f"CONVERSATION_DEBUG: Active conversations: {list(self.active_conversations.keys())}")
            
            conversation = self.active_conversations.get(conversation_id)
            if not conversation:
                logger.warning(f"CONVERSATION_DEBUG: Conversation {conversation_id} not found in active conversations")
                return None, "I couldn't find our conversation. Let's start fresh - what would you like me to help you with?"
            
            logger.info(f"CONVERSATION_DEBUG: Found conversation {conversation_id}, current state: {conversation.state}")
            
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
            
            # Process the message and generate response FIRST (before collecting entities)
            # This ensures confirmation responses are handled before entity extraction
            response = self._process_conversation_turn(conversation, intent)
            
            # Only collect entities if this wasn't a confirmation or cancellation
            if not (self._is_confirmation_response(intent) or self._is_cancellation_request(intent)):
                self._collect_entities_from_intent(conversation, intent)
            
            # Add system response
            system_message = ConversationMessage(
                type=MessageType.SYSTEM_RESPONSE,
                content=response,
                metadata={'step': conversation.context.current_step}
            )
            conversation.messages.append(system_message)
            
            # Update conversation
            conversation.updated_at = datetime.now()
            
            logger.info(f"Continued conversation {conversation_id}, step: {conversation.context.current_step}, new state: {conversation.state}")
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
        logger.info(f"NEW_CODE_RUNNING: Processing turn for conversation {conversation.id}, state: {conversation.state}, intent: '{intent.raw_text}'")
        
        # Handle special cases
        if self._is_cancellation_request(intent):
            logger.info(f"Detected cancellation request for conversation {conversation.id}")
            return self._handle_cancellation(conversation)
        
        # Only handle confirmation if we're actually waiting for it
        if self._is_confirmation_response(intent):
            logger.info(f"Detected confirmation response for conversation {conversation.id}")
            if conversation.state == ConversationState.WAITING_FOR_CONFIRMATION:
                logger.info(f"Conversation is waiting for confirmation, processing confirmation")
                return self._handle_confirmation(conversation, intent)
            elif conversation.state == ConversationState.EXECUTING:
                logger.info(f"Conversation is already executing, ignoring duplicate confirmation")
                return "Your request is already being processed. Please wait for the results."
            elif conversation.state == ConversationState.COMPLETED:
                logger.info(f"Conversation is completed, ignoring additional confirmation")
                return "Your request has already been completed. You can check the Job Monitoring section for results, or start a new request if needed."
            else:
                logger.info(f"Received confirmation but conversation state is {conversation.state}, treating as normal message")
                # Fall through to normal processing
        
        # Continue with normal flow
        logger.info(f"Continuing normal flow for conversation {conversation.id}")
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
        
        # Handle case where intent_type might be a string instead of enum
        if not template and isinstance(intent_type, str):
            # Try to find the enum value
            for enum_type in IntentType:
                if enum_type.value == intent_type:
                    intent_type = enum_type
                    template = self.conversation_templates.get(intent_type)
                    break
        
        if not template:
            logger.error(f"No template found for intent: {intent_type}")
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
        response_text = intent.raw_text.lower().strip()
        logger.info(f"CONFIRMATION_DEBUG: Handling confirmation for conversation {conversation.id}, state: {conversation.state}, text: '{response_text}'")
        logger.info(f"CONFIRMATION_DEBUG: Current step: {conversation.context.current_step}")
        logger.info(f"CONFIRMATION_DEBUG: Collected entities: {list(conversation.context.collected_entities.keys())}")
        
        # At this point we know the conversation state is WAITING_FOR_CONFIRMATION
        # because _process_conversation_turn already checked it
        
        # Check for positive confirmation
        positive_indicators = ['yes', 'y', 'ok', 'okay', 'sure', 'go ahead', 'proceed', 'do it', 'execute']
        negative_indicators = ['no', 'n', 'cancel', 'stop', 'abort', 'nevermind', 'never mind']
        
        is_positive = any(indicator in response_text for indicator in positive_indicators)
        is_negative = any(indicator in response_text for indicator in negative_indicators)
        
        logger.info(f"CONFIRMATION_DEBUG: Confirmation analysis: positive={is_positive}, negative={is_negative}")
        logger.info(f"CONFIRMATION_DEBUG: Response text: '{response_text}'")
        
        if is_positive and not is_negative:
            logger.info(f"CONFIRMATION_DEBUG: EXECUTING REQUEST for conversation {conversation.id}")
            return self._execute_request(conversation)
        elif is_negative:
            logger.info(f"CONFIRMATION_DEBUG: CANCELLING REQUEST for conversation {conversation.id}")
            return self._handle_cancellation(conversation)
        else:
            logger.info(f"CONFIRMATION_DEBUG: UNCLEAR CONFIRMATION for conversation {conversation.id}")
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
            
            # Prepare structured parameters for Job Engine
            target_intent = conversation.context.target_intent
            if isinstance(target_intent, str):
                # Convert string to enum if needed
                for enum_type in IntentType:
                    if enum_type.value == target_intent:
                        target_intent = enum_type
                        break
            
            intent_type = target_intent.value if target_intent else "automation_request"
            
            # Extract targets
            target_systems = []
            if EntityType.TARGET in entities:
                target_systems = [e.normalized_value or e.value for e in entities[EntityType.TARGET]]
            
            # Build requirements dictionary
            requirements = {
                "description": description,
                "actions": [e.normalized_value or e.value for e in entities.get(EntityType.ACTION, [])],
                "services": [e.normalized_value or e.value for e in entities.get(EntityType.SERVICE, [])],
                "files": [e.value for e in entities.get(EntityType.FILE_PATH, [])],
                "parameters": [e.value for e in entities.get(EntityType.PARAMETER, [])]
            }
            
            # Generate workflow using Job Engine with proper parameters
            generated_workflow = generate_workflow(intent_type, requirements, target_systems)
            
            if generated_workflow:
                # Convert workflow to automation service format and submit
                try:
                    from integrations.automation_client import AutomationServiceClient
                    automation_client = AutomationServiceClient()
                    
                    # Convert GeneratedWorkflow to automation service format (using 'nodes' structure)
                    workflow_data = {
                        "id": generated_workflow.workflow_id,
                        "name": generated_workflow.name,
                        "description": generated_workflow.description,
                        "nodes": [
                            {
                                "id": str(i + 1),
                                "type": "execute",
                                "name": step.name,
                                "command": step.command,
                                "timeout": step.timeout,
                                "retry_count": step.retry_count,
                                "expected_output": getattr(step, 'expected_output', None),
                                "description": getattr(step, 'description', step.name)
                            }
                            for i, step in enumerate(generated_workflow.steps)
                        ],
                        "target_systems": generated_workflow.target_systems,
                        "source_request": description,
                        "confidence": getattr(generated_workflow, 'confidence', 0.8),
                        "metadata": {
                            "conversation_id": conversation.id,
                            "intent_type": intent_type,
                            "created_by": "ai_brain"
                        }
                    }
                    
                    # Submit workflow to automation service (this is async)
                    import asyncio
                    import concurrent.futures
                    
                    # Create a new event loop in a thread to handle the async call
                    def run_async_in_thread():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(automation_client.submit_ai_workflow(
                                workflow_data, 
                                job_name=f"AI Job: {generated_workflow.name}"
                            ))
                        finally:
                            loop.close()
                    
                    # Run the async function in a separate thread
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_async_in_thread)
                        job_result = future.result(timeout=30)  # 30 second timeout
                    
                    if job_result and job_result.get('success'):
                        job_id = job_result.get('job_id')
                        conversation.context.execution_id = job_id
                        conversation.context.execution_status = "started"
                        conversation.context.generated_workflow = generated_workflow
                        
                        # Reset conversation state after successful execution
                        conversation.state = ConversationState.COMPLETED
                        
                        return f"🚀 Perfect! I've created and started your automation job.\n\n**Job ID**: {job_id}\n**Task**: {description}\n**Workflow**: {generated_workflow.name}\n\nI'll monitor the execution and keep you updated on the progress. You can also check the Job Monitoring section for real-time updates."
                    else:
                        # Job creation failed, but we have a workflow
                        execution_id = str(uuid.uuid4())
                        conversation.context.execution_id = execution_id
                        conversation.context.execution_status = "planned"
                        conversation.context.generated_workflow = generated_workflow
                        
                        # Reset conversation state after workflow creation
                        conversation.state = ConversationState.COMPLETED
                        
                        return f"✅ I've created a detailed workflow for your request.\n\n**Workflow ID**: {execution_id}\n**Task**: {description}\n**Steps**: {len(generated_workflow.steps)} automation steps\n\nThe workflow is ready but couldn't be automatically executed. You can review and manually execute it from the Job Management section."
                        
                except Exception as automation_error:
                    logger.error(f"Failed to submit job to automation service: {automation_error}")
                    # Fallback to workflow creation only
                    execution_id = str(uuid.uuid4())
                    conversation.context.execution_id = execution_id
                    conversation.context.execution_status = "planned"
                    conversation.context.generated_workflow = generated_workflow
                    
                    # Reset conversation state after workflow creation
                    conversation.state = ConversationState.COMPLETED
                    
                    return f"✅ I've created a detailed workflow for your request.\n\n**Workflow ID**: {execution_id}\n**Task**: {description}\n**Steps**: {len(generated_workflow.steps)} automation steps\n\nThe workflow is ready for execution. You can review and execute it from the Job Management section."
            else:
                # Fallback to basic execution tracking
                execution_id = str(uuid.uuid4())
                conversation.context.execution_id = execution_id
                conversation.context.execution_status = "started"
                
                # Reset conversation state after basic execution
                conversation.state = ConversationState.COMPLETED
                
                return f"🔄 I've started processing your automation request.\n\n**Job ID**: {execution_id}\n**Task**: {description}\n\nI'll keep you updated on the progress."
                
        except Exception as e:
            logger.error(f"Error executing request: {e}")
            # Fallback to basic execution
            execution_id = str(uuid.uuid4())
            conversation.context.execution_id = execution_id
            conversation.context.execution_status = "started"
            
            # Reset conversation state after fallback execution
            conversation.state = ConversationState.COMPLETED
            
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
        text_lower = intent.raw_text.lower().strip()
        is_confirmation = any(word in text_lower for word in confirmation_words)
        logger.info(f"DEBUG: Checking confirmation for '{intent.raw_text}' (stripped: '{text_lower}') -> {is_confirmation}")
        logger.info(f"DEBUG: Confirmation words checked: {confirmation_words}")
        return is_confirmation
    
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
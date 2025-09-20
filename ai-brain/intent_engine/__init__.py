"""
Intent Engine Module for AI Brain

This module provides comprehensive natural language understanding and intent processing
capabilities for intelligent automation conversations.

The Intent Engine consists of four main components:

1. Natural Language Understanding (NLU) - Parses user input and extracts intents and entities
2. Conversation Manager - Handles multi-turn conversations and maintains context
3. Context Analyzer - Analyzes conversation context and extracts requirements
4. Intent Classifier - Advanced intent classification with confidence scoring

Key Features:
- Advanced natural language understanding with 16 intent types
- Multi-turn conversation management with context preservation
- Intelligent context analysis and requirement extraction
- Risk assessment and mitigation suggestions
- Entity extraction and normalization
- Confidence scoring and alternative intent suggestions
- Conversation flow management and user confirmation handling
"""

from .natural_language_understanding import (
    NaturalLanguageUnderstanding,
    Intent,
    IntentType,
    Entity,
    EntityType,
    nlu_engine
)

from .conversation_manager import (
    ConversationManager,
    Conversation,
    ConversationState,
    ConversationMessage,
    ConversationContext,
    MessageType,
    conversation_manager
)

from .context_analyzer import (
    ContextAnalyzer,
    AnalyzedContext,
    ContextualRequirement,
    RiskAssessment,
    ContextualInsight,
    RequirementType,
    RiskLevel,
    ContextType,
    context_analyzer
)

from .intent_classifier import (
    IntentClassifier,
    ClassificationResult,
    ClassificationMethod,
    IntentSignature,
    intent_classifier
)

# Export all main classes and instances
__all__ = [
    # Natural Language Understanding
    'NaturalLanguageUnderstanding',
    'Intent',
    'IntentType', 
    'Entity',
    'EntityType',
    'nlu_engine',
    
    # Conversation Management
    'ConversationManager',
    'Conversation',
    'ConversationState',
    'ConversationMessage',
    'ConversationContext',
    'MessageType',
    'conversation_manager',
    
    # Context Analysis
    'ContextAnalyzer',
    'AnalyzedContext',
    'ContextualRequirement',
    'RiskAssessment',
    'ContextualInsight',
    'RequirementType',
    'RiskLevel',
    'ContextType',
    'context_analyzer',
    
    # Intent Classification
    'IntentClassifier',
    'ClassificationResult',
    'ClassificationMethod',
    'IntentSignature',
    'intent_classifier'
]

# Module metadata
__version__ = "1.0.0"
__author__ = "AI Brain Team"
__description__ = "Advanced Intent Engine for Natural Language Understanding and Conversation Management"

# Intent Engine capabilities summary
CAPABILITIES = {
    'intent_types': 16,
    'entity_types': 12,
    'conversation_states': 7,
    'message_types': 6,
    'risk_levels': 4,
    'requirement_types': 7,
    'classification_methods': 5
}

# Supported intent types
SUPPORTED_INTENTS = [
    IntentType.AUTOMATION_REQUEST,
    IntentType.INFORMATION_QUERY,
    IntentType.SYSTEM_STATUS,
    IntentType.TROUBLESHOOTING,
    IntentType.CONFIGURATION,
    IntentType.MONITORING,
    IntentType.DEPLOYMENT,
    IntentType.MAINTENANCE,
    IntentType.SECURITY,
    IntentType.BACKUP_RESTORE,
    IntentType.USER_MANAGEMENT,
    IntentType.NETWORK_OPERATIONS,
    IntentType.DATABASE_OPERATIONS,
    IntentType.FILE_OPERATIONS,
    IntentType.SERVICE_MANAGEMENT,
    IntentType.UNKNOWN
]

# Supported entity types
SUPPORTED_ENTITIES = [
    EntityType.TARGET,
    EntityType.SERVICE,
    EntityType.ACTION,
    EntityType.PARAMETER,
    EntityType.TIME,
    EntityType.FILE_PATH,
    EntityType.USER,
    EntityType.PROTOCOL,
    EntityType.PORT,
    EntityType.CREDENTIAL,
    EntityType.CONDITION,
    EntityType.QUANTITY
]

def get_engine_info():
    """Get information about the Intent Engine capabilities"""
    return {
        'version': __version__,
        'description': __description__,
        'capabilities': CAPABILITIES,
        'supported_intents': [intent.value for intent in SUPPORTED_INTENTS],
        'supported_entities': [entity.value for entity in SUPPORTED_ENTITIES],
        'components': {
            'nlu_engine': 'Natural Language Understanding with pattern matching and entity extraction',
            'conversation_manager': 'Multi-turn conversation management with context preservation',
            'context_analyzer': 'Advanced context analysis and requirement extraction',
            'intent_classifier': 'Hybrid intent classification with confidence scoring'
        }
    }

def process_user_input(user_input: str, user_id: str = "default", conversation_id: str = None):
    """
    High-level function to process user input through the complete Intent Engine pipeline
    
    Args:
        user_input: User's natural language input
        user_id: User identifier
        conversation_id: Optional existing conversation ID
        
    Returns:
        Dictionary with processed results including intent, entities, conversation, and analysis
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"DEBUG: process_user_input called with user_id='{user_id}', conversation_id='{conversation_id}', input='{user_input}'")
        
        # Step 1: Parse intent and entities using NLU
        intent = nlu_engine.parse_intent(user_input)
        logger.info(f"DEBUG: Parsed intent: {intent.type.value}, confidence: {intent.confidence}")
        
        # Step 2: Handle conversation flow
        if conversation_id:
            # Continue existing conversation
            logger.info(f"DEBUG: Continuing existing conversation {conversation_id}")
            conversation, response = conversation_manager.continue_conversation(
                conversation_id, user_input, intent
            )
        else:
            # Start new conversation
            logger.info(f"DEBUG: Starting new conversation for user {user_id}")
            conversation, response = conversation_manager.start_conversation(
                user_id, user_input, intent
            )
        
        # Step 3: Analyze context if conversation exists
        context_analysis = None
        if conversation:
            context_analysis = context_analyzer.analyze_context(conversation)
        
        # Step 4: Enhanced classification
        classification = intent_classifier.classify_intent(
            user_input, intent.entities, conversation.context.__dict__ if conversation else {}
        )
        
        result = {
            'success': True,
            'intent': {
                'type': intent.type.value,
                'confidence': intent.confidence,
                'entities': [
                    {
                        'type': entity.type.value,
                        'value': entity.value,
                        'normalized_value': entity.normalized_value,
                        'confidence': entity.confidence
                    }
                    for entity in intent.entities
                ]
            },
            'conversation': {
                'id': conversation.id if conversation else None,
                'state': conversation.state.value if conversation else None,
                'response': response
            },
            'context_analysis': {
                'confidence_score': context_analysis.confidence_score if context_analysis else 0.0,
                'risk_level': context_analysis.risk_assessment.level.value if context_analysis and context_analysis.risk_assessment else 'unknown',
                'requirements_count': len(context_analysis.requirements) if context_analysis else 0,
                'recommendations': context_analysis.recommendations if context_analysis else []
            },
            'classification': {
                'intent_type': classification.intent_type.value,
                'confidence': classification.confidence,
                'method': classification.method.value,
                'alternatives': [
                    {'intent': alt[0].value, 'confidence': alt[1]}
                    for alt in classification.alternative_intents
                ]
            }
        }
        
        logger.info(f"DEBUG: Returning result with conversation_id: {result['conversation']['id']}, state: {result['conversation']['state']}")
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'intent': {'type': 'unknown', 'confidence': 0.0, 'entities': []},
            'conversation': {'id': None, 'state': None, 'response': 'I encountered an error processing your request.'},
            'context_analysis': {'confidence_score': 0.0, 'risk_level': 'unknown', 'requirements_count': 0, 'recommendations': []},
            'classification': {'intent_type': 'unknown', 'confidence': 0.0, 'method': 'hybrid', 'alternatives': []}
        }
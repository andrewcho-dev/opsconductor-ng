"""
AI Brain Engine - Unified Intelligent AI System for OpsConductor

This module serves as the main orchestrator for the AI Brain system,
integrating all AI capabilities into a single, intelligent interface.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Legacy imports for backward compatibility
from legacy.ai_engine import OpsConductorAI as LegacyAIEngine
from legacy.system_capabilities import SystemCapabilitiesManager as SystemCapabilities

# Integration imports
from integrations.asset_client import AssetServiceClient as AssetClient
from integrations.automation_client import AutomationServiceClient as AutomationClient
from integrations.communication_client import CommunicationServiceClient as CommunicationClient
from integrations.vector_client import OpsConductorVectorStore as VectorStore
from integrations.llm_client import LLMEngine

logger = logging.getLogger(__name__)

class AIBrainEngine:
    """
    Unified AI Brain Engine that orchestrates all AI capabilities.
    
    This engine provides:
    - System model with complete OpsConductor knowledge
    - Knowledge engine with IT expertise
    - Intent engine with LLM-powered understanding
    - Job engine with intelligent workflow creation
    - Legacy support for existing functionality
    """
    
    def __init__(self):
        """Initialize the AI Brain Engine with all components."""
        self.legacy_mode = os.getenv("LEGACY_MODE_ENABLED", "true").lower() == "true"
        self.system_model_enabled = os.getenv("SYSTEM_MODEL_ENABLED", "true").lower() == "true"
        self.knowledge_graph_enabled = os.getenv("KNOWLEDGE_GRAPH_ENABLED", "true").lower() == "true"
        self.job_creation_enabled = os.getenv("JOB_CREATION_ENGINE_ENABLED", "true").lower() == "true"
        self.intent_engine_enabled = os.getenv("INTENT_ENGINE_ENABLED", "true").lower() == "true"
        
        # Initialize legacy components for backward compatibility
        if self.legacy_mode:
            logger.info("Initializing AI Brain in legacy compatibility mode")
            self.legacy_engine = LegacyAIEngine()
            self.system_capabilities = SystemCapabilities()
        
        # Initialize integration clients
        self._init_integration_clients()
        
        # Initialize new AI components (placeholder for now)
        self._init_ai_components()
        
        logger.info(f"AI Brain Engine initialized - Legacy: {self.legacy_mode}, "
                   f"System Model: {self.system_model_enabled}, "
                   f"Knowledge Graph: {self.knowledge_graph_enabled}, "
                   f"Job Creation: {self.job_creation_enabled}, "
                   f"Intent Engine: {self.intent_engine_enabled}")
    
    async def initialize(self) -> bool:
        """
        Initialize the AI Brain Engine asynchronously.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            logger.info("Starting AI Brain Engine async initialization...")
            
            # Perform any async initialization tasks here
            # For now, just return success since all initialization is done in __init__
            
            logger.info("AI Brain Engine async initialization completed successfully")
            return True
        except Exception as e:
            logger.error(f"AI Brain Engine async initialization failed: {e}")
            return False
    
    def _init_integration_clients(self):
        """Initialize all external service integration clients."""
        try:
            self.asset_client = AssetClient()
            self.automation_client = AutomationClient()
            self.communication_client = CommunicationClient()
            
            # Initialize vector store and LLM engine
            try:
                import chromadb
                
                # Configure ChromaDB with new client configuration
                chroma_client = chromadb.PersistentClient(path="/app/chromadb_data")
                
                self.vector_store = VectorStore(chroma_client)
                logger.info("Vector store initialized successfully")
            except Exception as ve:
                logger.warning(f"Vector store initialization failed: {ve}")
                self.vector_store = None
            
            # Initialize LLM engine with configuration
            ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
            default_model = os.getenv("DEFAULT_MODEL", "llama3.2")
            self.llm_engine = LLMEngine(ollama_host, default_model)
            
            logger.info("Integration clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize integration clients: {e}")
            raise
    
    def _init_ai_components(self):
        """Initialize new AI Brain components."""
        
        if self.system_model_enabled:
            try:
                from system_model import (
                    service_capabilities, protocol_knowledge, 
                    resource_mapper, workflow_templates
                )
                self.service_capabilities = service_capabilities
                self.protocol_knowledge = protocol_knowledge
                self.resource_mapper = resource_mapper
                self.workflow_templates = workflow_templates
                logger.info("System model components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize system model: {e}")
                self.system_model_enabled = False
        
        if self.knowledge_graph_enabled:
            try:
                from knowledge_engine import (
                    it_knowledge_base, solution_patterns,
                    error_resolution, learning_system
                )
                self.it_knowledge_base = it_knowledge_base
                self.solution_patterns = solution_patterns
                self.error_resolution = error_resolution
                self.learning_system = learning_system
                logger.info("Knowledge engine components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize knowledge engine: {e}")
                self.knowledge_graph_enabled = False
        
        if self.intent_engine_enabled:
            try:
                from intent_engine import (
                    nlu_engine, conversation_manager,
                    context_analyzer, intent_classifier,
                    process_user_input
                )
                from intent_engine.clarification_manager import ClarificationManager
                
                self.nlu_engine = nlu_engine
                self.conversation_manager = conversation_manager
                self.context_analyzer = context_analyzer
                self.intent_classifier = intent_classifier
                self.process_user_input = process_user_input
                
                # Debug conversation_manager before passing to ClarificationManager
                logger.info(f"DEBUG: conversation_manager type: {type(conversation_manager)}")
                logger.info(f"DEBUG: conversation_manager is None: {conversation_manager is None}")
                
                if conversation_manager is None:
                    logger.error("conversation_manager is None, cannot initialize ClarificationManager")
                    self.clarification_manager = None
                else:
                    self.clarification_manager = ClarificationManager(conversation_manager)
                logger.info("Intent engine components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize intent engine: {e}")
                self.intent_engine_enabled = False
        
        if self.job_creation_enabled:
            try:
                from job_engine import (
                    workflow_generator, target_resolver,
                    step_optimizer, execution_planner,
                    generate_workflow, resolve_targets,
                    optimize_workflow_steps, create_execution_plan
                )
                self.workflow_generator = workflow_generator
                self.target_resolver = target_resolver
                self.step_optimizer = step_optimizer
                self.execution_planner = execution_planner
                self.generate_workflow = generate_workflow
                self.resolve_targets = resolve_targets
                self.optimize_workflow_steps = optimize_workflow_steps
                self.create_execution_plan = create_execution_plan
                logger.info("Job engine components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize job engine: {e}")
                self.job_creation_enabled = False
    
    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user query using the appropriate AI engine.
        
        Args:
            query: The user's natural language query
            user_context: Optional user context information
            
        Returns:
            Dict containing the AI response and metadata
        """
        try:
            # Use new Intent Engine if available
            if self.intent_engine_enabled and hasattr(self, 'process_user_input'):
                logger.info(f"Processing query via Intent Engine: {query[:50]}...")
                
                user_id = user_context.get('user_id', 'default') if user_context else 'default'
                conversation_id = user_context.get('conversation_id') if user_context else None
                
                result = self.process_user_input(query, user_id, conversation_id)
                
                return {
                    'response': result['conversation']['response'],
                    'intent': result['intent'],
                    'confidence': result['intent'].get('confidence', 0.8) if isinstance(result['intent'], dict) else 0.8,
                    'conversation': result['conversation'],
                    'conversation_id': result['conversation']['id'],
                    'conversation_state': result['conversation']['state'],
                    'context_analysis': result['context_analysis'],
                    'classification': result['classification'],
                    'success': result['success'],
                    'metadata': {
                        'engine': 'intent_engine',
                        'timestamp': datetime.now().isoformat(),
                        'success': result['success']
                    }
                }
            
            # Fallback to legacy engine for backward compatibility
            elif self.legacy_mode and hasattr(self, 'legacy_engine'):
                logger.info(f"Processing query via legacy engine: {query[:50]}...")
                return await self.legacy_engine.process_query(query, user_context)
            
            else:
                # Basic fallback response
                return {
                    'response': "I'm currently initializing my AI capabilities. Please try again in a moment.",
                    'intent': {'type': 'unknown', 'confidence': 0.0},
                    'metadata': {
                        'engine': 'fallback',
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': 'No AI engine available'
                    }
                }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "intent": "error",
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "engine": "ai_brain_error"
            }
    
    async def get_system_capabilities(self) -> Dict[str, Any]:
        """
        Get comprehensive system capabilities information.
        
        Returns:
            Dict containing complete system capabilities
        """
        try:
            if self.legacy_mode and hasattr(self, 'system_capabilities'):
                return await self.system_capabilities.get_capabilities()
            
            # TODO: Implement new system model capabilities
            return {
                "ai_brain": {
                    "status": "initializing",
                    "components": {
                        "system_model": self.system_model_enabled,
                        "knowledge_engine": self.knowledge_graph_enabled,
                        "intent_engine": self.intent_engine_enabled,
                        "job_creation_engine": self.job_creation_enabled,
                        "legacy_mode": self.legacy_mode
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system capabilities: {e}")
            return {"error": str(e)}
    
    async def process_message(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message through the AI Brain Engine.
        
        Args:
            message: The user's message
            user_id: User identifier
            
        Returns:
            Dict containing the AI response and metadata
        """
        try:
            logger.info(f"Processing message from user {user_id}: {message[:50]}...")
            
            # Use the process_query method with user context
            user_context = {"user_id": user_id}
            result = await self.process_query(message, user_context)
            
            # Convert to expected format for chat interface
            return {
                "response": result.get("response", "I'm processing your request..."),
                "intent": result.get("intent", "unknown"),
                "success": result.get("metadata", {}).get("success", True),
                "data": {
                    "conversation_id": result.get("conversation_id"),
                    "context_analysis": result.get("context_analysis"),
                    "classification": result.get("classification")
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": f"I encountered an error processing your message: {str(e)}",
                "intent": "error",
                "success": False,
                "data": {}
            }

    async def create_job_from_natural_language(self, description: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create an executable job from natural language description using the Job Engine.
        
        Args:
            description: Natural language description of the desired job
            user_context: Optional user context information
            
        Returns:
            Dict containing the created job or error information
        """
        try:
            logger.info(f"Job creation requested: {description[:50]}...")
            
            if not self.job_creation_enabled:
                return {
                    "success": False,
                    "error": "Job creation engine is not available",
                    "fallback_message": "Please use the legacy automation interface"
                }
            
            # Step 1: Process user input through Intent Engine
            if self.intent_engine_enabled and hasattr(self, 'process_user_input'):
                user_id = user_context.get('user_id', 'default') if user_context else 'default'
                conversation_id = user_context.get('conversation_id') if user_context else None
                
                intent_result = self.process_user_input(description, user_id, conversation_id)
                
                if not intent_result['success']:
                    return {
                        "success": False,
                        "error": "Failed to understand the request",
                        "details": intent_result
                    }
                
                intent_type = intent_result['intent']['type']
                requirements = intent_result['context_analysis']['requirements']
                target_input = intent_result['context_analysis']['entities'].get('targets', [])
                
            else:
                # Fallback: basic parsing
                intent_type = "automation_request"
                requirements = {"description": description}
                target_input = user_context.get('targets', []) if user_context else []
            
            # Step 2: Resolve target systems
            target_resolution = self.resolve_targets(target_input, {"test_connections": True})
            
            if not target_resolution.resolved_targets:
                return {
                    "success": False,
                    "error": "No valid target systems found",
                    "details": {
                        "unresolved_targets": target_resolution.unresolved_targets,
                        "resolution_errors": target_resolution.resolution_errors
                    }
                }
            
            target_systems = [t.hostname for t in target_resolution.resolved_targets]
            
            # Step 3: Generate workflow
            workflow = self.generate_workflow(
                intent_type=intent_type,
                requirements=requirements,
                target_systems=target_systems,
                context=user_context
            )
            
            # Step 4: Optimize workflow
            optimized_workflow = self.optimize_workflow_steps(
                workflow.steps,
                optimization_goals=None,  # Use defaults
                constraints=user_context.get('constraints') if user_context else None
            )
            
            # Step 5: Create execution plan
            execution_plan = self.create_execution_plan(
                workflow=workflow,
                optimized_workflow=optimized_workflow,
                execution_preferences=user_context.get('execution_preferences') if user_context else None,
                constraints=user_context.get('constraints') if user_context else None
            )
            
            # Step 6: Validate execution plan
            is_valid, validation_errors = self.execution_planner.validate_execution_plan(execution_plan)
            
            if not is_valid:
                return {
                    "success": False,
                    "error": "Execution plan validation failed",
                    "validation_errors": validation_errors,
                    "workflow": self.workflow_generator.export_workflow(workflow),
                    "execution_plan": self.execution_planner.export_execution_plan(execution_plan)
                }
            
            # Return complete job creation result
            return {
                "success": True,
                "job_id": workflow.workflow_id,
                "workflow": self.workflow_generator.export_workflow(workflow),
                "optimized_workflow": self.step_optimizer.export_optimization(optimized_workflow),
                "execution_plan": self.execution_planner.export_execution_plan(execution_plan),
                "target_resolution": {
                    "resolved_targets": self.target_resolver.export_targets(target_resolution.resolved_targets),
                    "target_summary": self.target_resolver.get_target_summary(target_resolution.resolved_targets),
                    "resolution_time": target_resolution.resolution_time
                },
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "intent_type": intent_type,
                    "requires_approval": execution_plan.requires_approval,
                    "estimated_duration": execution_plan.execution_schedule.estimated_end_time - execution_plan.execution_schedule.planned_start_time,
                    "risk_level": workflow.risk_level
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating job from natural language: {e}")
            return {
                "success": False,
                "error": f"Failed to create job: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation details by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Dict containing conversation details or None if not found
        """
        try:
            if self.intent_engine_enabled and hasattr(self, 'conversation_manager'):
                conversation = self.conversation_manager.get_conversation(conversation_id)
                if conversation:
                    return self.conversation_manager.export_conversation(conversation_id)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active conversations for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of conversation dictionaries
        """
        try:
            if self.intent_engine_enabled and hasattr(self, 'conversation_manager'):
                conversations = self.conversation_manager.get_user_conversations(user_id)
                return [
                    self.conversation_manager.export_conversation(conv.id)
                    for conv in conversations
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            return []
    
    async def analyze_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Analyze context for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Dict containing context analysis or None if not found
        """
        try:
            if (self.intent_engine_enabled and 
                hasattr(self, 'conversation_manager') and 
                hasattr(self, 'context_analyzer')):
                
                conversation = self.conversation_manager.get_conversation(conversation_id)
                if conversation:
                    analysis = self.context_analyzer.analyze_context(conversation)
                    return self.context_analyzer.export_analysis(analysis)
            return None
        except Exception as e:
            logger.error(f"Error analyzing context for conversation {conversation_id}: {e}")
            return None
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the AI Brain Engine.
        
        Returns:
            Dict containing health status information
        """
        return {
            "status": "healthy",
            "service": "ai-brain",
            "components": {
                "legacy_engine": self.legacy_mode and hasattr(self, 'legacy_engine'),
                "integration_clients": True,  # Assume healthy if initialized
                "system_model": self.system_model_enabled,
                "knowledge_engine": self.knowledge_graph_enabled,
                "intent_engine": self.intent_engine_enabled,
                "job_creation_engine": self.job_creation_enabled
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def process_message(self, message: str, user_id: str = "system") -> Dict[str, Any]:
        """
        Process a chat message through the AI Brain Engine.
        
        Args:
            message: The user's message
            user_id: User identifier
            
        Returns:
            Dict containing the response and any generated data
        """
        try:
            logger.info(f"Processing message from user {user_id}: {message}")
            
            # Use the existing process_query method as the core processing engine
            result = await self.process_query(message, {"user_id": user_id})
            
            # Handle different result structures from different engines
            if isinstance(result, dict):
                # Extract response text
                response_text = ""
                if "response" in result:
                    response_text = result["response"]
                elif "conversation" in result and isinstance(result["conversation"], dict):
                    response_text = result["conversation"].get("response", "")
                else:
                    response_text = "I've processed your request."
                
                # Extract intent
                intent = "unknown"
                if "intent" in result:
                    if isinstance(result["intent"], dict):
                        intent = result["intent"].get("type", "unknown")
                    else:
                        intent = str(result["intent"])
                
                # Determine success
                success = result.get("success", True)
                if "metadata" in result:
                    success = result["metadata"].get("success", success)
                
                return {
                    "response": response_text,
                    "intent": intent,
                    "success": success,
                    "data": {
                        "conversation_id": result.get("conversation_id"),
                        "classification": result.get("classification"),
                        "context_analysis": result.get("context_analysis")
                    }
                }
            else:
                # Handle unexpected result format
                return {
                    "response": str(result) if result else "I processed your request.",
                    "intent": "unknown",
                    "success": True,
                    "data": {}
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "intent": "error",
                "success": False,
                "data": {}
            }
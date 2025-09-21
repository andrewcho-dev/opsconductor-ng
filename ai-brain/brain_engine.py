"""
AI Brain Engine - Unified Intelligent AI System for OpsConductor

This module serves as the main orchestrator for the AI Brain system,
integrating all AI capabilities into a single, intelligent interface.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Modern AI components
from analytics.system_analytics import SystemAnalytics
from processors.intent_processor import IntentProcessor
from capabilities.system_capabilities import SystemCapabilities
from engines.ai_engine import ModernAIEngine

# Integration imports
from integrations.asset_client import AssetServiceClient as AssetClient
from integrations.automation_client import AutomationServiceClient as AutomationClient
from integrations.communication_client import CommunicationServiceClient as CommunicationClient
from integrations.vector_client import OpsConductorVectorStore as VectorStore
from integrations.llm_client import LLMEngine
from llm_conversation_handler import LLMConversationHandler

# LLM-based job creation engine
from job_engine.llm_job_creator import LLMJobCreator

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
        self.system_model_enabled = os.getenv("SYSTEM_MODEL_ENABLED", "true").lower() == "true"
        self.knowledge_graph_enabled = os.getenv("KNOWLEDGE_GRAPH_ENABLED", "true").lower() == "true"
        self.job_creation_enabled = os.getenv("JOB_CREATION_ENGINE_ENABLED", "true").lower() == "true"
        self.intent_engine_enabled = False  # NLM DISABLED - USING PURE LLM
        self.llm_conversation_enabled = os.getenv("LLM_CONVERSATION_ENABLED", "true").lower() == "true"
        
        logger.info("Initializing AI Brain with modern components")
        # Initialize modern AI components
        self.system_analytics = SystemAnalytics()
        self.intent_processor = IntentProcessor()
        self.system_capabilities = SystemCapabilities()
        self.ai_engine = ModernAIEngine()
        
        # Initialize integration clients
        self._init_integration_clients()
        
        # Initialize new AI components (placeholder for now)
        self._init_ai_components()
        
        logger.info(f"AI Brain Engine initialized - "
                   f"System Model: {self.system_model_enabled}, "
                   f"Knowledge Graph: {self.knowledge_graph_enabled}, "
                   f"Job Creation: {self.job_creation_enabled}, "
                   f"Intent Engine: {self.intent_engine_enabled}, "
                   f"LLM Conversation: {self.llm_conversation_enabled}")
    
    async def initialize(self) -> bool:
        """
        Initialize the AI Brain Engine asynchronously.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            logger.info("Starting AI Brain Engine async initialization...")
            
            # Initialize LLM engine asynchronously
            if hasattr(self, 'llm_engine'):
                logger.info("Initializing LLM engine...")
                llm_success = await self.llm_engine.initialize()
                if not llm_success:
                    logger.error("Failed to initialize LLM engine")
                    return False
                logger.info("LLM engine initialized successfully")
            
            # Initialize modern AI components
            logger.info("Initializing modern AI components...")
            
            # Initialize system analytics
            if hasattr(self, 'system_analytics'):
                await self.system_analytics.initialize()
                logger.info("System analytics initialized")
            
            # Initialize intent processor
            if hasattr(self, 'intent_processor'):
                await self.intent_processor.initialize()
                logger.info("Intent processor initialized")
            
            # Initialize system capabilities
            if hasattr(self, 'system_capabilities'):
                await self.system_capabilities.initialize()
                logger.info("System capabilities initialized")
            
            # Initialize AI engine
            if hasattr(self, 'ai_engine'):
                ai_success = await self.ai_engine.initialize()
                if not ai_success:
                    logger.warning("AI engine initialization failed, continuing...")
                else:
                    logger.info("AI engine initialized successfully")
            
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
            default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
            self.llm_engine = LLMEngine(ollama_host, default_model)
            
            # Initialize LLM conversation handler with asset client
            if self.llm_conversation_enabled:
                self.llm_conversation_handler = LLMConversationHandler(self.llm_engine, self.asset_client)
                logger.info("LLM conversation handler initialized successfully with asset client access")
            
            # Initialize LLM job creator (replaces NLM intent engine)
            if self.job_creation_enabled:
                self.llm_job_creator = LLMJobCreator(self.llm_engine, self.automation_client)
                logger.info("LLM job creator initialized successfully with automation client integration")
            
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
        
        # NLM Intent Engine REMOVED - Using pure LLM approach
        logger.info("🚫 NLM Intent Engine permanently disabled - using pure LLM pipeline")
        
        if self.job_creation_enabled:
            # Old job engine components removed - using LLM-based job creator
            logger.info("🚀 Job creation using pure LLM pipeline (initialized in integration clients)")
    
    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user query using PURE LLM - NO INTENT MATCHING, NO TEMPLATES, NO BULLSHIT!
        
        Args:
            query: The user's natural language query
            user_context: Optional user context information
            
        Returns:
            Dict containing the AI response and metadata
        """
        try:
            # Use LLM conversation handler - PURE AI, NO HARDCODED SHIT
            if self.llm_conversation_enabled and hasattr(self, 'llm_conversation_handler'):
                logger.info(f"Processing query via PURE LLM: {query[:50]}...")
                
                # Handle case where user_context might be passed as string instead of dict
                if isinstance(user_context, str):
                    logger.warning(f"user_context passed as string: {user_context}, converting to dict")
                    user_id = user_context
                    conversation_id = None
                elif user_context and isinstance(user_context, dict):
                    user_id = user_context.get('user_id', 'default')
                    conversation_id = user_context.get('conversation_id')
                else:
                    user_id = 'default'
                    conversation_id = None
                
                result = await self.llm_conversation_handler.process_message(query, user_id, conversation_id)
                
                return {
                    'response': result['response'],
                    'conversation_id': result['conversation_id'],
                    'conversation_state': result['conversation_state'],
                    'success': result['success'],
                    'metadata': result['metadata']
                }
            
            else:
                # Basic fallback response if LLM is not available
                return {
                    'response': "I'm currently initializing my AI capabilities. Please try again in a moment.",
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
                "success": False,
                "metadata": {
                    "engine": "ai_brain_error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
            }
    
    async def get_system_capabilities(self) -> Dict[str, Any]:
        """
        Get comprehensive system capabilities information.
        
        Returns:
            Dict containing complete system capabilities
        """
        try:
            # Use modern system capabilities
            if hasattr(self, 'system_capabilities'):
                return await self.system_capabilities.get_system_capabilities()
            
            # Fallback system information
            return {
                "ai_brain": {
                    "status": "active",
                    "components": {
                        "system_model": self.system_model_enabled,
                        "knowledge_engine": self.knowledge_graph_enabled,
                        "intent_engine": self.intent_engine_enabled,
                        "job_creation_engine": self.job_creation_enabled,
                        "modern_ai": True
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
        Create an executable job from natural language description using pure LLM analysis.
        
        This method replaces the old NLM intent engine with a multi-stage LLM pipeline:
        1. ANALYZE: Understand the request and extract requirements
        2. PLAN: Generate workflow steps and structure  
        3. VALIDATE: Check feasibility and safety
        4. CREATE: Build the final executable job
        
        Args:
            description: Natural language description of the desired job
            user_context: Optional user context information
            
        Returns:
            Dict containing the created job or error information
        """
        try:
            logger.info(f"🚀 LLM Job creation requested: {description[:50]}...")
            
            if not self.job_creation_enabled:
                return {
                    "success": False,
                    "error": "Job creation engine is not available",
                    "fallback_message": "Please use the legacy automation interface"
                }
            
            if not hasattr(self, 'llm_job_creator'):
                return {
                    "success": False,
                    "error": "LLM job creator not initialized",
                    "fallback_message": "Please restart the AI Brain service"
                }
            
            # Use the new LLM-based job creation pipeline
            logger.info("🧠 Using pure LLM job creation pipeline (NO NLM)")
            result = await self.llm_job_creator.create_job_from_natural_language(description, user_context)
            
            if result.get("success"):
                logger.info(f"✅ LLM job created successfully: {result.get('job_id')}")
            else:
                logger.warning(f"❌ LLM job creation failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM job creation: {e}")
            return {
                "success": False,
                "error": f"Failed to create job: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    # NLM conversation methods removed - using pure LLM approach
    # All conversation handling is now done through LLMConversationHandler
    
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
                "modern_ai_components": True,
                "integration_clients": True,
                "system_model": self.system_model_enabled,
                "knowledge_engine": self.knowledge_graph_enabled,
                "llm_conversation_handler": self.llm_conversation_enabled and hasattr(self, 'llm_conversation_handler'),
                "llm_job_creator": self.job_creation_enabled and hasattr(self, 'llm_job_creator'),
                "system_analytics": hasattr(self, 'system_analytics'),
                "intent_processor": hasattr(self, 'intent_processor'),
                "system_capabilities": hasattr(self, 'system_capabilities'),
                "ai_engine": hasattr(self, 'ai_engine')
            },
            "architecture": "pure_llm",
            "nlm_status": "completely_removed",
            "timestamp": datetime.utcnow().isoformat()
        }
    

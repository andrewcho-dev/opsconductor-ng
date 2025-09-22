"""
Modern AI Engine

This module provides the modern replacement for the legacy AI engine,
using the AI Brain Engine with LLM-powered capabilities and vector-based knowledge.
"""

import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import modern AI Brain components
from brain_engine import AIBrainEngine
from integrations.llm_client import LLMEngine
from integrations.vector_client import OpsConductorVectorStore
from capabilities.system_capabilities import system_capabilities

logger = structlog.get_logger()

class ModernAIEngine:
    """
    Modern AI Engine that provides the same interface as the legacy AI engine
    but uses the AI Brain Engine with modern LLM and vector capabilities.
    """
    
    def __init__(self):
        self.brain_engine = AIBrainEngine()
        self.initialized = False
        self.system_capabilities = system_capabilities
        
        # Legacy-compatible attributes
        self.nlp = None  # Replaced by LLM-based processing
        self.vector_store = None
        self.llm_client = None
        
    async def initialize(self) -> bool:
        """Initialize the modern AI engine"""
        try:
            logger.info("Initializing modern AI engine...")
            
            # Initialize the AI Brain Engine
            success = await self.brain_engine.initialize()
            if not success:
                logger.error("Failed to initialize AI Brain Engine")
                return False
            
            # Initialize system capabilities
            await self.system_capabilities.initialize()
            
            # Set up legacy-compatible references
            self.vector_store = getattr(self.brain_engine, 'vector_store', None)
            self.llm_client = getattr(self.brain_engine, 'llm_engine', None)
            
            self.initialized = True
            logger.info("Modern AI engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Modern AI engine initialization failed: {e}")
            self.initialized = False
            return False
    
    async def process_message(self, message: str, context: List[Dict] = None) -> Dict[str, Any]:
        """
        Process a message using modern AI capabilities.
        
        This method provides the same interface as the legacy AI engine
        but uses LLM-powered processing instead of rule-based systems.
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"Processing message with modern AI engine: {message[:100]}...")
            
            # Use AI Brain's LLM conversation handler for processing
            if hasattr(self.brain_engine, 'llm_conversation_handler'):
                response = await self.brain_engine.llm_conversation_handler.process_message(
                    message, context or []
                )
                
                # Ensure legacy-compatible response format
                return {
                    "response": response.get("response", ""),
                    "intent": response.get("intent", "conversation"),
                    "confidence": response.get("confidence", 0.8),
                    "method": "modern_llm_processing",
                    "timestamp": datetime.now().isoformat(),
                    "context": response.get("context", {}),
                    "suggestions": response.get("suggestions", [])
                }
            
            # Fallback to basic LLM processing
            if self.llm_client:
                llm_response = await self.llm_client.generate(
                    f"Process this IT operations request: {message}"
                )
                
                return {
                    "response": llm_response,
                    "intent": "general_query",
                    "confidence": 0.7,
                    "method": "direct_llm",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Final fallback
            return {
                "response": "I understand your request. The modern AI engine is processing your message.",
                "intent": "acknowledgment",
                "confidence": 0.5,
                "method": "fallback",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "intent": "error",
                "confidence": 0.0,
                "method": "error_handling",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """
        Classify intent using modern LLM-based analysis.
        
        Replaces the legacy rule-based intent classification with
        LLM-powered understanding.
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            if self.llm_client:
                intent_prompt = f"""
                Analyze this IT operations message and classify its intent:
                Message: "{message}"
                
                Classify into one of these categories:
                - infrastructure_query: Questions about servers, networks, systems
                - automation_request: Requests to automate tasks or create jobs
                - system_status: Questions about system health or status
                - troubleshooting: Help with problems or errors
                - general_conversation: General chat or unclear requests
                
                Respond with JSON: {{"intent": "category", "confidence": 0.0-1.0, "reasoning": "explanation"}}
                """
                
                response = await self.llm_client.generate(intent_prompt)
                
                # Parse LLM response (simplified)
                try:
                    import json
                    result = json.loads(response)
                    result["method"] = "modern_llm_classification"
                    return result
                except:
                    # Fallback parsing
                    return {
                        "intent": "general_conversation",
                        "confidence": 0.6,
                        "reasoning": "LLM response parsing failed, using fallback",
                        "method": "fallback_classification"
                    }
            
            # Basic keyword-based fallback
            message_lower = message.lower()
            if any(word in message_lower for word in ["restart", "update", "install", "execute"]):
                return {
                    "intent": "automation_request",
                    "confidence": 0.7,
                    "reasoning": "Contains automation keywords",
                    "method": "keyword_fallback"
                }
            elif any(word in message_lower for word in ["status", "health", "check"]):
                return {
                    "intent": "system_status", 
                    "confidence": 0.7,
                    "reasoning": "Contains status keywords",
                    "method": "keyword_fallback"
                }
            else:
                return {
                    "intent": "general_conversation",
                    "confidence": 0.5,
                    "reasoning": "No specific keywords detected",
                    "method": "default_fallback"
                }
                
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "error",
                "confidence": 0.0,
                "reasoning": f"Classification error: {str(e)}",
                "method": "error_handling"
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        if not self.initialized:
            await self.initialize()
        
        try:
            capabilities = await self.system_capabilities.get_system_capabilities()
            
            return {
                "engine_type": "modern_ai_engine",
                "brain_engine_status": "active" if self.brain_engine else "inactive",
                "llm_available": self.llm_client is not None,
                "vector_store_available": self.vector_store is not None,
                "system_capabilities": capabilities,
                "features": [
                    "LLM-powered natural language processing",
                    "Vector-based knowledge management",
                    "Intelligent intent classification", 
                    "Modern system capabilities",
                    "Legacy API compatibility"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {
                "engine_type": "modern_ai_engine",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def store_interaction(self, message: str, response: Dict[str, Any], context: List[Dict] = None):
        """Store interaction for learning (modern vector-based storage)"""
        try:
            if self.vector_store:
                interaction_data = {
                    "message": message,
                    "response": response.get("response", ""),
                    "intent": response.get("intent", "unknown"),
                    "confidence": response.get("confidence", 0.0),
                    "timestamp": datetime.now().isoformat(),
                    "context": context or []
                }
                
                await self.vector_store.store_document(
                    content=f"User: {message}\nAI: {response.get('response', '')}",
                    metadata=interaction_data,
                    collection_name="ai_interactions"
                )
                
                logger.debug("Interaction stored in vector database")
                
        except Exception as e:
            logger.warning(f"Failed to store interaction: {e}")

# Create global instance
ai_engine = ModernAIEngine()
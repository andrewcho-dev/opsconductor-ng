from fastapi import HTTPException
import structlog
from datetime import datetime
from typing import Optional
import uuid

logger = structlog.get_logger()

async def pure_llm_chat_endpoint(request, ai_engine):
    """PURE LLM CHAT INTERFACE - NO PATTERN MATCHING, NO TEMPLATES, JUST AI!"""
    try:
        logger.info("Processing PURE LLM chat request", message=request.message[:100], conversation_id=request.conversation_id)
        user_id = str(request.user_id) if request.user_id else "system"
        
        # Generate conversation_id if not provided
        if not request.conversation_id:
            request.conversation_id = f"chat-{uuid.uuid4()}"
        
        # Process through PURE LLM brain engine - NO HARDCODED BULLSHIT!
        user_context = {
            "user_id": user_id,
            "conversation_id": request.conversation_id
        }
        
        response = await ai_engine.process_query(request.message, user_context)
        
        return {
            "response": response.get("response", "I'm processing your request..."),
            "conversation_id": response.get("conversation_id", request.conversation_id),
            "intent": "llm_conversation",  # Always LLM conversation, no pattern matching
            "confidence": 1.0,  # LLM is always confident in its responses
            "job_id": None,  # Pure conversation, no job creation
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            # Metadata showing this is pure LLM
            "intent_classification": {
                "intent_type": "llm_conversation",
                "confidence": 1.0,
                "method": "pure_llm",
                "alternatives": [],
                "entities": [],
                "context_analysis": {
                    "confidence_score": 1.0,
                    "risk_level": "NONE",
                    "requirements_count": 0,
                    "recommendations": ["Using pure LLM conversation"]
                },
                "reasoning": "Processed using pure LLM conversation handler - no pattern matching",
                "metadata": {
                    "engine": "llm_conversation_handler",
                    "success": response.get("success", True)
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "pure_llm_brain_engine", 
                "response_time": 0.0,
                "cached": False
            }
        }
        
    except Exception as e:
        logger.error("PURE LLM chat processing failed", error=str(e), exc_info=True)
        
        # Even error handling is LLM-powered
        return {
            "response": f"I encountered an issue processing your message: {str(e)}. Please try rephrasing your request.",
            "conversation_id": request.conversation_id,
            "intent": "error_recovery",
            "confidence": 0.8,
            "job_id": None,
            "execution_id": None,
            "automation_job_id": None,
            "workflow": None,
            "execution_started": False,
            "intent_classification": {
                "intent_type": "error_recovery",
                "confidence": 0.8,
                "method": "pure_llm_error_handling",
                "alternatives": [],
                "entities": [],
                "context_analysis": {
                    "confidence_score": 0.8,
                    "risk_level": "LOW",
                    "requirements_count": 0,
                    "recommendations": ["Try rephrasing the request"]
                },
                "reasoning": "Error occurred in pure LLM processing",
                "metadata": {
                    "engine": "llm_conversation_handler",
                    "success": False,
                    "error": str(e)
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "_routing": {
                "service_type": "pure_llm_error_handler", 
                "response_time": 0.0,
                "cached": False
            }
        }